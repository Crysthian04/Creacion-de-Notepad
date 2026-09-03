"""Capa 1 — Modelo físico del ciclo de compresión de vapor (gemelo digital).

Módulo AISLADO: no importa nada de `fallas`, `generador`, `features` ni
`modelo`. Recibe condiciones de contorno, parámetros del equipo y un objeto de
ajustes multiplicativos, y devuelve el estado del ciclo junto con el diagnóstico
de convergencia del solver. Se puede probar por completo sin que exista el resto
del pipeline (ver `tests/test_ciclo.py`).

Ecuaciones: efectividad-NTU para los intercambiadores (Çengel y Ghajar, cap. 11)
y compresor con eficiencias volumétrica e isentrópica (Çengel y Boles). Todas
las propiedades termodinámicas provienen de CoolProp (Bell et al., 2014): no se
usa ninguna correlación aproximada ni tabla embebida.

SIMPLIFICACIONES DECLARADAS
---------------------------
1. Los intercambiadores se modelan como intercambio SENSIBLE puro
   (`m_a·cp_a·eps·ΔT`), tal como fija la sección 3.1 de la especificación. La
   deshumidificación en el evaporador no se modela; por eso `HR_amb` se registra
   como medición pero no interviene en el cierre del ciclo.
2. `Q_load_frac` se implementa como fracción del caudal de aire nominal del
   evaporador. Es un proxy de la operación a carga parcial de un equipo de
   velocidad fija con control on/off: el modelo describe el estado
   cuasi-estacionario durante el periodo de marcha, no el ciclado.
3. El `UA` de cada intercambiador escala con el caudal de aire según
   `UA ∝ m_a^0.8` (analogía de Dittus-Boelter del lado aire).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict, field
from functools import lru_cache

import numpy as np
from scipy.optimize import fsolve

import CoolProp.CoolProp as CP

# ---------------------------------------------------------------------------
# Conversión de unidades — probada en tests/test_ciclo.py::test_unidades
# ---------------------------------------------------------------------------
PSI_A_PA = 6894.757293168361
CERO_C_EN_K = 273.15


def pa_abs_a_psig(p_pa: float, p_atm: float) -> float:
    """Presión absoluta en Pa -> presión manométrica en psig."""
    return (p_pa - p_atm) / PSI_A_PA


def psig_a_pa_abs(p_psig: float, p_atm: float) -> float:
    """Presión manométrica en psig -> presión absoluta en Pa."""
    return p_psig * PSI_A_PA + p_atm


def c_a_k(t_c: float) -> float:
    return t_c + CERO_C_EN_K


def k_a_c(t_k: float) -> float:
    return t_k - CERO_C_EN_K


# ---------------------------------------------------------------------------
# Propiedades de saturación (con caché: el solver las pide miles de veces)
# ---------------------------------------------------------------------------
@lru_cache(maxsize=200_000)
def p_rocio(t_c: float, refrigerante: str) -> float:
    """Presión de saturación en el punto de ROCÍO (Q=1), en Pa absolutos."""
    return CP.PropsSI("P", "T", c_a_k(t_c), "Q", 1, refrigerante)


@lru_cache(maxsize=200_000)
def p_burbuja(t_c: float, refrigerante: str) -> float:
    """Presión de saturación en el punto de BURBUJA (Q=0), en Pa absolutos."""
    return CP.PropsSI("P", "T", c_a_k(t_c), "Q", 0, refrigerante)


@lru_cache(maxsize=200_000)
def t_rocio(p_pa: float, refrigerante: str) -> float:
    """Temperatura de ROCÍO a la presión dada, en °C. Para sobrecalentamiento."""
    return k_a_c(CP.PropsSI("T", "P", p_pa, "Q", 1, refrigerante))


@lru_cache(maxsize=200_000)
def t_burbuja(p_pa: float, refrigerante: str) -> float:
    """Temperatura de BURBUJA a la presión dada, en °C. Para subenfriamiento."""
    return k_a_c(CP.PropsSI("T", "P", p_pa, "Q", 0, refrigerante))


@lru_cache(maxsize=8)
def t_critica(refrigerante: str) -> float:
    return k_a_c(CP.PropsSI("Tcrit", refrigerante))


@lru_cache(maxsize=8)
def t_triple(refrigerante: str) -> float:
    return k_a_c(CP.PropsSI("Ttriple", refrigerante))


# ---------------------------------------------------------------------------
# Entradas del modelo
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CondicionContorno:
    """Condiciones de contorno del barrido (sección 2.1)."""

    T_amb: float         # °C, bulbo seco exterior
    HR_amb: float        # %, humedad relativa exterior
    T_space: float       # °C, temperatura del espacio acondicionado
    Q_load_frac: float   # -, fracción de carga térmica


@dataclass(frozen=True)
class AjustesCiclo:
    """Degradaciones aplicadas al modelo (Capa 2).

    Neutro por defecto: `AjustesCiclo()` describe el equipo SANO. `src.fallas`
    es quien construye los ajustes de cada modo de falla; este módulo solo los
    aplica, para que la física y la inyección de fallas queden separadas.
    """

    f_UA_ev: float = 1.0        # multiplicador del UA del evaporador
    f_UA_cd: float = 1.0        # multiplicador del UA del condensador
    f_m_a_ev: float = 1.0       # multiplicador del caudal de aire del evaporador
    f_m_a_cd: float = 1.0       # multiplicador del caudal de aire del condensador
    f_eta_v: float = 1.0        # multiplicador de la eficiencia volumétrica
    f_eta_s: float = 1.0        # multiplicador de la eficiencia isentrópica
    f_m_r: float = 1.0          # multiplicador del flujo másico de refrigerante
    d_SH: float = 0.0           # K sumados al sobrecalentamiento objetivo
    d_SC: float = 0.0           # K sumados al subenfriamiento objetivo
    frac_P_des_extra: float = 0.0  # fracción de presión de descarga adicional
                                   # (incondensables) SIN alterar T_cond


# ---------------------------------------------------------------------------
# Salida del modelo
# ---------------------------------------------------------------------------
@dataclass
class EstadoCiclo:
    """Estado completo del ciclo. Las 12 variables medibles van marcadas."""

    # --- variables medibles en campo (sección 2.2) -------------------------
    P_suc: float          # psig      [medible]
    P_des: float          # psig      [medible]
    T_ev_out: float       # °C        [medible]
    T_suc: float          # °C        [medible]
    T_des: float          # °C        [medible]
    T_liq: float          # °C        [medible]
    T_air_in_ev: float    # °C        [medible]
    T_air_out_ev: float   # °C        [medible]
    T_air_in_cd: float    # °C        [medible]
    T_air_out_cd: float   # °C        [medible]
    I_avg: float          # A         [medible]
    W_elec: float         # W         [medible]
    V_air_ev: float       # kg/s      [medible, balómetro]

    # --- estado interno (NO medible: solo para verificación y figuras) -----
    T_evap: float         # °C
    T_cond: float         # °C
    m_r: float            # kg/s
    Q_L: float            # W
    Q_H: float            # W
    W_comp: float         # W
    Q_linea: float        # W  (ganancia de calor en la línea de succión)
    eta_v: float
    rp: float
    h1: float             # J/kg  entrada al compresor
    h2a: float            # J/kg  descarga real
    h3: float             # J/kg  salida del condensador
    h4: float             # J/kg  entrada al evaporador
    P_suc_pa: float       # Pa absolutos
    P_des_pa: float       # Pa absolutos

    # --- diagnóstico del solver -------------------------------------------
    convergio: bool
    residuo: float
    n_evaluaciones: int
    motivo: str = ""

    def dict_medible(self) -> dict[str, float]:
        """Solo las variables que el equipo puede medir en campo."""
        return {k: getattr(self, k) for k in VARIABLES_MEDIBLES}


VARIABLES_MEDIBLES = (
    "P_suc", "P_des", "T_ev_out", "T_suc", "T_des", "T_liq",
    "T_air_in_ev", "T_air_out_ev", "T_air_in_cd", "T_air_out_cd",
    "I_avg", "W_elec", "V_air_ev",
)

# Márgenes numéricos mínimos para no pedir propiedades dentro de la campana.
_SH_MIN = 0.10   # K
_SC_MIN = 0.10   # K


class ErrorCiclo(RuntimeError):
    """El estado pedido está fuera del dominio físico o de CoolProp."""


# ---------------------------------------------------------------------------
# Núcleo: estado del ciclo dadas T_evap y T_cond
# ---------------------------------------------------------------------------
def _estado_dado_te_tc(t_evap: float, t_cond: float, cond: CondicionContorno,
                       p, aj: AjustesCiclo) -> dict:
    """Evalúa todo el ciclo para un par (T_evap, T_cond) tentativo.

    Devuelve un diccionario con los flujos de calor por el lado refrigerante y
    por el lado aire. El solver anula la diferencia entre ambos.
    """
    ref = p.refrigerante

    # --- presiones de saturación ------------------------------------------
    p_suc_pa = p_rocio(round(t_evap, 6), ref)
    p_cond_pa = p_burbuja(round(t_cond, 6), ref)
    # Incondensables: la presión de descarga sube sin que suba T_cond.
    p_des_pa = p_cond_pa * (1.0 + aj.frac_P_des_extra)

    # --- lado refrigerante: succión ---------------------------------------
    sh_evap = max(p.SH_nom + aj.d_SH, _SH_MIN)
    sh_total = sh_evap + p.dSH_linea
    t_ev_out = t_evap + sh_evap
    t_suc = t_evap + sh_total

    h_ev_out = CP.PropsSI("H", "P", p_suc_pa, "T", c_a_k(t_ev_out), ref)
    h1 = CP.PropsSI("H", "P", p_suc_pa, "T", c_a_k(t_suc), ref)
    s1 = CP.PropsSI("S", "P", p_suc_pa, "T", c_a_k(t_suc), ref)
    rho1 = CP.PropsSI("D", "P", p_suc_pa, "T", c_a_k(t_suc), ref)
    v_suc = 1.0 / rho1

    # --- compresor ---------------------------------------------------------
    rp = p_des_pa / p_suc_pa
    eta_v = (p.eta_v0 - p.k_v * (rp - 1.0)) * aj.f_eta_v
    eta_v = float(np.clip(eta_v, 0.05, 1.0))
    eta_s = float(np.clip(p.eta_s * aj.f_eta_s, 0.05, 1.0))

    m_r = p.V_disp * p.N_rev * eta_v / v_suc * aj.f_m_r

    h2s = CP.PropsSI("H", "P", p_des_pa, "S", s1, ref)
    h2a = h1 + (h2s - h1) / eta_s
    t_des = k_a_c(CP.PropsSI("T", "P", p_des_pa, "H", h2a, ref))
    w_comp = m_r * (h2a - h1)

    # --- condensador: salida de líquido ------------------------------------
    sc = max(p.SC_nom + aj.d_SC, _SC_MIN)
    t_liq = t_cond - sc
    h3 = CP.PropsSI("H", "P", p_cond_pa, "T", c_a_k(t_liq), ref)
    h4 = h3  # expansión isentálpica

    # --- calores por el lado refrigerante ----------------------------------
    q_l_ref = m_r * (h_ev_out - h4)
    q_h_ref = m_r * (h2a - h3)
    q_linea = m_r * (h1 - h_ev_out)   # ganancia en la línea de succión

    # --- lado aire (efectividad-NTU) ---------------------------------------
    m_a_ev = p.m_a_ev * aj.f_m_a_ev * cond.Q_load_frac
    m_a_cd = p.m_a_cd * aj.f_m_a_cd
    c_ev = m_a_ev * p.cp_aire
    c_cd = m_a_cd * p.cp_aire

    ua_ev = p.UA_ev * aj.f_UA_ev * (aj.f_m_a_ev * cond.Q_load_frac) ** 0.8
    ua_cd = p.UA_cd * aj.f_UA_cd * (aj.f_m_a_cd) ** 0.8

    ntu_ev = ua_ev / c_ev
    ntu_cd = ua_cd / c_cd
    eps_ev = 1.0 - math.exp(-ntu_ev)
    eps_cd = 1.0 - math.exp(-ntu_cd)

    q_l_air = c_ev * eps_ev * (cond.T_space - t_evap)
    q_h_air = c_cd * eps_cd * (t_cond - cond.T_amb)

    t_air_out_ev = cond.T_space - q_l_air / c_ev
    t_air_out_cd = cond.T_amb + q_h_air / c_cd

    # --- eléctrico ---------------------------------------------------------
    w_elec = w_comp / p.eta_motor + p.W_vent_ev + p.W_vent_cd
    i_avg = w_elec / (math.sqrt(3.0) * p.tension_linea * p.fp)

    return {
        "q_l_ref": q_l_ref, "q_h_ref": q_h_ref, "q_l_air": q_l_air, "q_h_air": q_h_air,
        "p_suc_pa": p_suc_pa, "p_des_pa": p_des_pa, "p_cond_pa": p_cond_pa,
        "t_ev_out": t_ev_out, "t_suc": t_suc, "t_des": t_des, "t_liq": t_liq,
        "t_air_out_ev": t_air_out_ev, "t_air_out_cd": t_air_out_cd,
        "m_r": m_r, "eta_v": eta_v, "rp": rp, "w_comp": w_comp, "w_elec": w_elec,
        "i_avg": i_avg, "q_linea": q_linea,
        "h1": h1, "h2a": h2a, "h3": h3, "h4": h4, "h_ev_out": h_ev_out,
        "m_a_ev": m_a_ev,
    }


def resolver_ciclo(cond: CondicionContorno, p, aj: AjustesCiclo | None = None,
                   tol: float = 1e-4, x0: tuple[float, float] | None = None) -> EstadoCiclo:
    """Resuelve el ciclo para (T_evap, T_cond) cerrando el balance de energía.

    La convergencia SIEMPRE se devuelve como dato (`EstadoCiclo.convergio`);
    nunca se asume. El generador descarta y contabiliza los puntos no
    convergidos (sección 3.2 de la especificación).
    """
    aj = aj or AjustesCiclo()
    ref = p.refrigerante

    # Dominio admisible de las temperaturas de saturación.
    te_min = max(t_triple(ref) + 5.0, -30.0)
    te_max = cond.T_space - 0.5           # el evaporador debe estar por debajo del aire
    tc_min = cond.T_amb + 0.5             # el condensador por encima del aire
    tc_max = t_critica(ref) - 5.0

    contador = {"n": 0}

    def residuos(x):
        contador["n"] += 1
        t_evap = float(np.clip(x[0], te_min, te_max))
        t_cond = float(np.clip(x[1], tc_min, tc_max))
        try:
            e = _estado_dado_te_tc(t_evap, t_cond, cond, p, aj)
        except Exception:
            return [1e3, 1e3]
        r1 = (e["q_l_ref"] - e["q_l_air"]) / p.Q_nom
        r2 = (e["q_h_ref"] - e["q_h_air"]) / p.Q_nom
        # Penalización si el solver empuja fuera del dominio admisible.
        pen1 = 10.0 * (abs(x[0] - t_evap) + abs(x[1] - t_cond))
        return [r1 + pen1, r2 + pen1]

    # Arranques deterministas. fsolve se estanca en puntos aislados del dominio
    # ("the iteration is not making good progress"); reintentar desde otro punto
    # de partida recupera la mayoría sin tocar la física. La lista es fija y
    # ordenada: el resultado no depende de nada aleatorio.
    if x0 is not None:
        arranques = [tuple(x0)]
    else:
        arranques = [
            (cond.T_space - 15.0, cond.T_amb + 14.0),
            (cond.T_space - 8.0, cond.T_amb + 10.0),
            (cond.T_space - 22.0, cond.T_amb + 20.0),
            (max(te_min + 2.0, cond.T_space - 30.0), cond.T_amb + 6.0),
            (cond.T_space - 4.0, cond.T_amb + 25.0),
        ]

    sol, ier, msg = None, 5, "sin intentos"
    for arranque in arranques:
        sol_i, info, ier_i, msg_i = fsolve(residuos, np.array(arranque, dtype=float),
                                           full_output=True, xtol=1e-10, maxfev=400)
        te_i = float(np.clip(sol_i[0], te_min, te_max))
        tc_i = float(np.clip(sol_i[1], tc_min, tc_max))
        dentro = (abs(sol_i[0] - te_i) < 1e-6) and (abs(sol_i[1] - tc_i) < 1e-6)
        if sol is None:
            sol, ier, msg = sol_i, ier_i, msg_i
        if ier_i == 1 and dentro:
            sol, ier, msg = sol_i, ier_i, msg_i
            break

    t_evap = float(np.clip(sol[0], te_min, te_max))
    t_cond = float(np.clip(sol[1], tc_min, tc_max))
    en_dominio = (abs(sol[0] - t_evap) < 1e-6) and (abs(sol[1] - t_cond) < 1e-6)

    motivo = ""
    try:
        e = _estado_dado_te_tc(t_evap, t_cond, cond, p, aj)
    except Exception as exc:                                  # pragma: no cover
        raise ErrorCiclo(f"CoolProp falló en el punto solución: {exc}") from exc

    residuo = max(abs(e["q_l_ref"] - e["q_l_air"]),
                  abs(e["q_h_ref"] - e["q_h_air"])) / p.Q_nom

    convergio = bool(ier == 1 and residuo < tol and en_dominio)
    if not convergio:
        if not en_dominio:
            motivo = "solución fuera del dominio físico admisible"
        elif ier != 1:
            motivo = f"fsolve no convergió: {str(msg).strip()[:80]}"
        else:
            motivo = f"residuo {residuo:.2e} por encima de la tolerancia {tol:.0e}"

    return EstadoCiclo(
        P_suc=pa_abs_a_psig(e["p_suc_pa"], p.P_atm),
        P_des=pa_abs_a_psig(e["p_des_pa"], p.P_atm),
        T_ev_out=e["t_ev_out"], T_suc=e["t_suc"], T_des=e["t_des"], T_liq=e["t_liq"],
        T_air_in_ev=cond.T_space, T_air_out_ev=e["t_air_out_ev"],
        T_air_in_cd=cond.T_amb, T_air_out_cd=e["t_air_out_cd"],
        I_avg=e["i_avg"], W_elec=e["w_elec"], V_air_ev=e["m_a_ev"],
        T_evap=t_evap, T_cond=t_cond, m_r=e["m_r"],
        Q_L=e["q_l_air"], Q_H=e["q_h_air"], W_comp=e["w_comp"], Q_linea=e["q_linea"],
        eta_v=e["eta_v"], rp=e["rp"],
        h1=e["h1"], h2a=e["h2a"], h3=e["h3"], h4=e["h4"],
        P_suc_pa=e["p_suc_pa"], P_des_pa=e["p_des_pa"],
        convergio=convergio, residuo=residuo, n_evaluaciones=contador["n"], motivo=motivo,
    )


def cop_carnot(t_evap: float, t_cond: float) -> float:
    """COP de Carnot entre las dos temperaturas de saturación, en °C."""
    return c_a_k(t_evap) / (t_cond - t_evap)


if __name__ == "__main__":  # diagnóstico rápido del módulo
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
    from config.params import ParametrosEquipo, PUNTO_DISENO

    p = ParametrosEquipo()
    c = CondicionContorno(**PUNTO_DISENO)
    e = resolver_ciclo(c, p)
    print(f"convergio={e.convergio} residuo={e.residuo:.2e} n_eval={e.n_evaluaciones}")
    print(f"T_evap={e.T_evap:6.2f} °C   T_cond={e.T_cond:6.2f} °C   rp={e.rp:5.2f}")
    print(f"P_suc ={e.P_suc:6.1f} psig  P_des ={e.P_des:6.1f} psig")
    print(f"Q_L   ={e.Q_L:8.1f} W  ({e.Q_L/3516.85:.2f} TR)   W_elec={e.W_elec:7.1f} W")
    print(f"COP   ={e.Q_L/e.W_elec:5.2f}   (Carnot {cop_carnot(e.T_evap, e.T_cond):5.2f})")
    print(f"T_des ={e.T_des:6.2f} °C   T_liq={e.T_liq:6.2f} °C   m_r={e.m_r:.4f} kg/s")
    print(f"dT_air_ev={e.T_air_in_ev - e.T_air_out_ev:5.2f} K  "
          f"dT_air_cd={e.T_air_out_cd - e.T_air_in_cd:5.2f} K  "
          f"split_cd={e.T_cond - e.T_air_in_cd:5.2f} K")
