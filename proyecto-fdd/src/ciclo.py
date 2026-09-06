"""Capa 1 — Modelo físico del ciclo de compresión de vapor (gemelo digital).

Módulo AISLADO: no importa nada de `fallas`, `generador`, `features` ni
`modelo`. Recibe condiciones de contorno, parámetros del equipo (que llevan
dentro la topología) y un objeto de ajustes, y devuelve el estado del ciclo con
el diagnóstico de convergencia del solver.

Ecuaciones: efectividad-NTU para los intercambiadores (Çengel y Ghajar, cap. 11)
y compresor con eficiencias volumétrica e isentrópica (Çengel y Boles). Todas
las propiedades termodinámicas provienen de CoolProp (Bell et al., 2014).

TRES MECANISMOS QUE ANTES NO ESTABAN
------------------------------------
1. LA VÁLVULA DE EXPANSIÓN ES UN ELEMENTO DE FLUJO, no un setpoint. El
   sobrecalentamiento es RESULTADO de la restricción, no una entrada:

       ṁ_válvula = K_v · a(SH) · sqrt(ρ_líq · ΔP_válvula)
       a(SH)     = clip(a_nom + K_ctrl·(SH − SH_objetivo), a_min, 1)

   Una válvula restringida hambrea el evaporador: cae el flujo, cae la presión
   de succión, cae la capacidad y sube el sobrecalentamiento como consecuencia.

2. LA ENFRIADORA MODULA CAPACIDAD para sostener la temperatura de salida del
   agua en el setpoint. La fracción de capacidad `y` (válvula deslizante o
   variador) es incógnita del solver, acotada entre `y_min` y 1. Cuando satura,
   queda registrado: es exactamente lo que ocurre cuando una falla degrada la
   capacidad en un día caluroso.

   Bajo control de setpoint la carga queda prescrita, así que la ecuación del
   evaporador se vuelve EXPLÍCITA para T_evap y `y` ocupa su lugar como
   incógnita. El sistema sigue siendo de tres ecuaciones, no de cuatro.

3. EL SUBENFRIAMIENTO SE ACOPLA A LA PRESIÓN DE CONDENSACIÓN:

       SC = SC_nom + k_SC·(T_cond − T_cond_ref) + d_SC_falla

   Al subir la presión de condensación se acumula líquido y crece el área
   inundada. Es una aproximación empírica declarada: sin ella, `res_SC` solo
   llevaría información sobre el inventario de refrigerante.

SIMPLIFICACIONES DECLARADAS
---------------------------
a. Intercambio SENSIBLE puro (`m·cp·eps·ΔT`). En el evaporador de agua eso es
   exacto; en el de aire de la topología de expansión directa ignora la
   deshumidificación.
b. CAUDAL PRIMARIO CONSTANTE en el circuito de agua helada. Es un SUPUESTO, no
   un hecho verificado: se confirma en la visita al cuarto de máquinas. Si la
   instalación resultara de caudal primario variable (válvulas de dos vías y
   variador en las bombas), un caudal reducido a carga parcial sería operación
   normal y la clase `caudal_agua_bajo` dejaría de ser válida tal como está
   planteada.
c. La carga del edificio fija la temperatura de retorno mediante
   `T_ret = T_sup_sp + Q_load/(ṁ_w·cp)`. No se modela la reducción de capacidad
   de las serpentinas del edificio al bajar el caudal.
d. `UA` escala con el caudal del fluido secundario según `UA ∝ ṁ^0.8`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np
from scipy.optimize import fsolve

import CoolProp.CoolProp as CP

from .topologia import Topologia, variables_medibles

# ---------------------------------------------------------------------------
# Conversión de unidades — probada en tests/test_ciclo.py::test_unidades
# ---------------------------------------------------------------------------
PSI_A_PA = 6894.757293168361
CERO_C_EN_K = 273.15


def pa_abs_a_psig(p_pa: float, p_atm: float) -> float:
    return (p_pa - p_atm) / PSI_A_PA


def psig_a_pa_abs(p_psig: float, p_atm: float) -> float:
    return p_psig * PSI_A_PA + p_atm


def c_a_k(t_c: float) -> float:
    return t_c + CERO_C_EN_K


def k_a_c(t_k: float) -> float:
    return t_k - CERO_C_EN_K


# ---------------------------------------------------------------------------
# Propiedades (con caché: el solver las pide decenas de miles de veces)
# ---------------------------------------------------------------------------
@lru_cache(maxsize=300_000)
def p_rocio(t_c: float, refrigerante: str) -> float:
    return CP.PropsSI("P", "T", c_a_k(t_c), "Q", 1, refrigerante)


@lru_cache(maxsize=300_000)
def p_burbuja(t_c: float, refrigerante: str) -> float:
    return CP.PropsSI("P", "T", c_a_k(t_c), "Q", 0, refrigerante)


@lru_cache(maxsize=300_000)
def t_rocio(p_pa: float, refrigerante: str) -> float:
    """Temperatura de ROCÍO a la presión dada, en °C. Para sobrecalentamiento."""
    return k_a_c(CP.PropsSI("T", "P", p_pa, "Q", 1, refrigerante))


@lru_cache(maxsize=300_000)
def t_burbuja(p_pa: float, refrigerante: str) -> float:
    """Temperatura de BURBUJA a la presión dada, en °C. Para subenfriamiento."""
    return k_a_c(CP.PropsSI("T", "P", p_pa, "Q", 0, refrigerante))


@lru_cache(maxsize=8)
def t_critica(refrigerante: str) -> float:
    return k_a_c(CP.PropsSI("Tcrit", refrigerante))


@lru_cache(maxsize=8)
def t_triple(refrigerante: str) -> float:
    return k_a_c(CP.PropsSI("Ttriple", refrigerante))


@lru_cache(maxsize=100_000)
def temperatura_bulbo_humedo(t_seco_c: float, hr_pct: float, p_atm: float) -> float:
    """Bulbo húmedo del aire exterior, en °C. Gobierna la torre de enfriamiento."""
    return k_a_c(CP.HAPropsSI("Twb", "T", c_a_k(t_seco_c), "P", p_atm,
                              "R", min(max(hr_pct / 100.0, 0.01), 1.0)))


# ---------------------------------------------------------------------------
# Entradas del modelo
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CondicionContorno:
    """Condiciones de contorno del barrido (sección 2.1)."""

    T_amb: float         # °C, bulbo seco exterior
    HR_amb: float        # %, humedad relativa exterior
    Q_load_frac: float   # -, fracción de carga térmica del edificio


@dataclass(frozen=True)
class AjustesCiclo:
    """Degradaciones aplicadas al modelo (Capa 2). Neutro = equipo sano.

    `src.fallas` construye estos ajustes; este módulo solo los aplica, para que
    la física y la inyección de fallas queden separadas.
    """

    f_UA_ev: float = 1.0            # multiplicador del UA del evaporador
    f_UA_cd: float = 1.0            # multiplicador del UA del condensador
    f_m_sec_ev: float = 1.0         # multiplicador del caudal secundario del evaporador
    f_m_sec_cd: float = 1.0         # multiplicador del caudal secundario del condensador
    f_eta_v: float = 1.0
    f_eta_s: float = 1.0
    f_K_v: float = 1.0              # multiplicador del coeficiente de flujo de la válvula
    d_a_nom: float = 0.0            # apertura base adicional (bulbo descargado)
    f_K_ctrl: float = 1.0           # multiplicador de la ganancia del lazo de SH
    d_SC: float = 0.0               # K sumados al subenfriamiento
    frac_dP_liquido: float = 0.0    # fracción de (P_des − P_suc) perdida en la línea
    frac_P_des_extra: float = 0.0   # incondensables, SIN alterar T_cond


# ---------------------------------------------------------------------------
# Salida del modelo
# ---------------------------------------------------------------------------
@dataclass
class EstadoCiclo:
    medible: dict[str, float]       # solo lo que el equipo mide en campo

    # --- estado interno (NO medible: verificación, figuras y análisis) -----
    T_evap: float
    T_cond: float
    SH_evap: float
    SC: float
    y_capacidad: float
    m_r: float
    Q_L: float
    Q_H: float
    W_comp: float
    Q_linea: float
    eta_v: float
    eta_s_efectiva: float
    apertura_valvula: float
    rp: float
    h1: float
    h2a: float
    h3: float
    h4: float
    P_suc_pa: float
    P_des_pa: float
    T_sec_in_ev: float
    T_sec_out_ev: float
    desviacion_setpoint: float      # K, T_salida_agua − setpoint (0 bajo control)
    capacidad_saturada: bool
    ciclado: bool
    retorno_liquido: bool
    exceso_alimentacion: float      # (ṁ_válvula − ṁ_compresor)/ṁ_compresor

    # --- diagnóstico del solver -------------------------------------------
    convergio: bool
    residuo: float
    n_evaluaciones: int
    regimen: str = ""
    motivo: str = ""

    def __getattr__(self, nombre: str):
        # Permite estado.P_suc, estado.T_agua_out_ev, etc. según la topología.
        try:
            return self.__dict__["medible"][nombre]
        except KeyError as exc:
            raise AttributeError(nombre) from exc

    def dict_medible(self) -> dict[str, float]:
        return dict(self.medible)


_SH_MIN = 0.10
_SC_MIN = 0.10


class ErrorCiclo(RuntimeError):
    """El estado pedido está fuera del dominio físico o de CoolProp."""


# ---------------------------------------------------------------------------
# Lado secundario: temperaturas de entrada y capacidades térmicas
# ---------------------------------------------------------------------------
def _lado_secundario(cond: CondicionContorno, p, aj: AjustesCiclo) -> dict:
    """Caudales, capacidades térmicas y temperaturas de entrada de cada lado."""
    topo: Topologia = p.topologia
    q_load = cond.Q_load_frac * p.Q_nom

    if topo.evap_es_agua:
        m_ev = p.m_w_ev * aj.f_m_sec_ev
        c_ev = m_ev * p.cp_agua
        # Caudal primario constante: la carga del edificio fija el retorno.
        t_in_ev = p.T_agua_sup_sp + q_load / c_ev
    else:
        # Expansión directa: la carga escala el caudal de aire (respaldo).
        m_ev = p.m_a_ev * aj.f_m_sec_ev * cond.Q_load_frac
        c_ev = m_ev * p.cp_aire
        t_in_ev = p.T_space_sp

    if topo.cond_es_agua:
        m_cd = p.m_w_cd * aj.f_m_sec_cd
        c_cd = m_cd * p.cp_agua
        t_wb = temperatura_bulbo_humedo(round(cond.T_amb, 4), round(cond.HR_amb, 4), p.P_atm)
        t_in_cd = t_wb + p.approach_torre
    else:
        m_cd = p.m_a_cd * aj.f_m_sec_cd
        c_cd = m_cd * p.cp_aire
        t_in_cd = cond.T_amb

    ua_ev = p.UA_ev * aj.f_UA_ev * (m_ev / max(p.m_secundario_ev, 1e-9)) ** 0.8
    ua_cd = p.UA_cd * aj.f_UA_cd * (m_cd / max(p.m_secundario_cd, 1e-9)) ** 0.8

    return {"q_load": q_load, "m_ev": m_ev, "c_ev": c_ev, "t_in_ev": t_in_ev,
            "m_cd": m_cd, "c_cd": c_cd, "t_in_cd": t_in_cd,
            "ua_ev": ua_ev, "ua_cd": ua_cd,
            "eps_cd": 1.0 - math.exp(-ua_cd / c_cd)}


def _eps_evaporador(sh: float, sec: dict, p) -> float:
    """Efectividad del evaporador, penalizada por la zona de sobrecalentamiento.

    ACOPLAMIENTO FÍSICO: el refrigerante que ya se evaporó por completo sigue
    recorriendo el evaporador recalentándose, y en esa zona el coeficiente de
    transferencia es muy inferior al de la zona de ebullición. Cuanto mayor es
    el sobrecalentamiento, más superficie queda "seca" y menor es el UA efectivo:

        UA_ev_ef = UA_ev · (1 − beta_sh · min(SH/SH_ref, 1))

    Sin este acoplamiento, el sobrecalentamiento no tendría NINGUNA consecuencia
    sobre la temperatura de evaporación, y una válvula restringida se limitaría a
    subir el SH sin mover la presión de succión, la relación de presiones ni el
    COP. La batería de firmas lo detectó y por eso el modelo lo incorpora.

    Es una aproximación empírica declarada: representa el efecto de un modelo
    distribuido de dos zonas mediante un solo coeficiente.
    """
    penalizacion = 1.0 - p.beta_sh_UA * min(max(sh, 0.0) / p.SH_ref_area, 1.0)
    return 1.0 - math.exp(-sec["ua_ev"] * penalizacion / sec["c_ev"])


# ---------------------------------------------------------------------------
# Núcleo: evalúa el ciclo dado (T_evap, T_cond, SH, y)
# ---------------------------------------------------------------------------
def _evaluar(t_evap: float, t_cond: float, sh: float, y: float,
             sec: dict, p, aj: AjustesCiclo) -> dict:
    ref = p.refrigerante

    p_suc_pa = p_rocio(round(t_evap, 6), ref)
    p_cond_pa = p_burbuja(round(t_cond, 6), ref)
    p_des_pa = p_cond_pa * (1.0 + aj.frac_P_des_extra)

    # --- succión -----------------------------------------------------------
    sh = max(sh, _SH_MIN)
    t_ev_out = t_evap + sh
    t_suc = t_ev_out + p.dSH_linea
    h_ev_out = CP.PropsSI("H", "P", p_suc_pa, "T", c_a_k(t_ev_out), ref)
    h1 = CP.PropsSI("H", "P", p_suc_pa, "T", c_a_k(t_suc), ref)
    s1 = CP.PropsSI("S", "P", p_suc_pa, "T", c_a_k(t_suc), ref)
    v_suc = 1.0 / CP.PropsSI("D", "P", p_suc_pa, "T", c_a_k(t_suc), ref)

    # --- compresor ---------------------------------------------------------
    rp = p_des_pa / p_suc_pa
    eta_v = float(np.clip((p.eta_v0 - p.k_v * (rp - 1.0)) * aj.f_eta_v, 0.05, 1.0))
    # Penalización de eficiencia isentrópica a carga parcial (curva IPLV).
    eta_s = p.eta_s * (1.0 - p.k_carga_parcial * (1.0 - y)) * aj.f_eta_s
    eta_s = float(np.clip(eta_s, 0.05, 1.0))
    m_r = y * p.V_disp * p.N_rev * eta_v / v_suc

    h2s = CP.PropsSI("H", "P", p_des_pa, "S", s1, ref)
    h2a = h1 + (h2s - h1) / eta_s
    t_des = k_a_c(CP.PropsSI("T", "P", p_des_pa, "H", h2a, ref))
    w_comp = m_r * (h2a - h1)

    # --- condensador: subenfriamiento acoplado a la presión ----------------
    sc = p.SC_nom + p.k_SC_Tcond * (t_cond - p.T_cond_ref_SC) + aj.d_SC
    sc = max(sc, _SC_MIN)
    t_liq = t_cond - sc
    h3 = CP.PropsSI("H", "P", p_cond_pa, "T", c_a_k(t_liq), ref)
    rho_liq = CP.PropsSI("D", "P", p_cond_pa, "T", c_a_k(t_liq), ref)
    h4 = h3

    # --- línea de líquido y válvula de expansión ---------------------------
    dp_linea = aj.frac_dP_liquido * max(p_cond_pa - p_suc_pa, 0.0)
    dp_valvula = max(p_cond_pa - dp_linea - p_suc_pa, 1.0)

    # Temperatura de la línea de líquido TAL COMO LA MIDE EL TERMOPAR, que está
    # aguas abajo del filtro deshidratador. Si la caída de presión hace flashear
    # el líquido, este se enfría hasta la saturación a la presión reducida: es
    # el «filtro frío» que el técnico detecta con la mano y que distingue una
    # restricción de línea de líquido de una válvula restringida. Sin esta
    # distinción las dos fallas dejan exactamente la misma firma de signos,
    # porque ambas hambrean el evaporador.
    #
    # La entalpía h3 NO cambia: el paso por la restricción es isentálpico. Lo
    # único que cambia es lo que lee el instrumento.
    t_liq_medido = t_liq
    if dp_linea > 0.0:
        p_aguas_abajo = max(p_cond_pa - dp_linea, 1e4)
        t_sat_abajo = t_burbuja(round(p_aguas_abajo, 3), ref)
        t_liq_medido = min(t_liq, t_sat_abajo)
    # El elemento de potencia pierde sensibilidad de forma progresiva: la
    # apertura base sube y la ganancia del lazo cae. Con f = 0 la válvula modula
    # normalmente; con f = 1 queda abierta y sin control.
    apertura = (p.a_nom + aj.d_a_nom
                + p.K_ctrl_valvula * aj.f_K_ctrl * (sh - p.SH_objetivo))
    apertura = float(np.clip(apertura, p.a_min, 1.0))
    m_valvula = p.K_v_valvula * aj.f_K_v * apertura * math.sqrt(rho_liq * dp_valvula)

    # --- calores -----------------------------------------------------------
    q_l_ref = m_r * (h_ev_out - h4)
    q_h_ref = m_r * (h2a - h3)
    q_linea = m_r * (h1 - h_ev_out)

    eps_ev = _eps_evaporador(sh, sec, p)
    q_l_sec = sec["c_ev"] * eps_ev * (sec["t_in_ev"] - t_evap)
    q_h_sec = sec["c_cd"] * sec["eps_cd"] * (t_cond - sec["t_in_cd"])

    w_elec = w_comp / p.eta_motor + p.W_aux
    i_avg = w_elec / (math.sqrt(3.0) * p.tension_linea * p.fp)

    return {"p_suc_pa": p_suc_pa, "p_cond_pa": p_cond_pa, "p_des_pa": p_des_pa,
            "t_ev_out": t_ev_out, "t_suc": t_suc, "t_des": t_des, "t_liq": t_liq,
            "t_liq_medido": t_liq_medido,
            "sc": sc, "sh": sh, "m_r": m_r, "m_valvula": m_valvula,
            "apertura": apertura, "eta_v": eta_v, "eta_s": eta_s, "rp": rp,
            "w_comp": w_comp, "w_elec": w_elec, "i_avg": i_avg,
            "q_l_ref": q_l_ref, "q_h_ref": q_h_ref, "q_linea": q_linea,
            "q_l_sec": q_l_sec, "q_h_sec": q_h_sec, "eps_ev": eps_ev,
            "h1": h1, "h2a": h2a, "h3": h3, "h4": h4, "h_ev_out": h_ev_out}


# ---------------------------------------------------------------------------
# Solver
# ---------------------------------------------------------------------------
def resolver_ciclo(cond: CondicionContorno, p, aj: AjustesCiclo | None = None,
                   tol: float = 1e-4) -> EstadoCiclo:
    """Resuelve el ciclo cerrando los balances de energía y el flujo de la válvula.

    REGÍMENES DE CAPACIDAD (solo con control de capacidad)
      `controlado` — la enfriadora modula; el agua sale al setpoint.
      `saturado`   — y = 1 y aun así no alcanza el setpoint. Bandera.
      `ciclado`    — la carga cae por debajo de la capacidad mínima. Bandera.

    REGÍMENES DE LA VÁLVULA
      `balance`    — ṁ_válvula = ṁ_compresor. Operación normal.
      `inundado`   — la válvula pasa más de lo que el compresor absorbe incluso
                     con el sobrecalentamiento en su mínimo. El evaporador se
                     inunda y el exceso de líquido llega al compresor.
      `hambriento` — la válvula no alcanza a alimentar ni con el
                     sobrecalentamiento en su MÁXIMO FÍSICO, que es el que deja
                     al refrigerante justo por debajo de la temperatura del
                     fluido que lo calienta. Más allá de ese tope, el modelo
                     estaría calentando el refrigerante por encima de su fuente.

    En los dos regímenes extremos el balance de la válvula se viola A PROPÓSITO
    —exigir que cierre sería exigir que la falla no ocurra— y el desbalance se
    reporta en `exceso_alimentacion` como medida del fenómeno. El modelo
    representa el UMBRAL de la inundación, no la compresión bifásica.

    La convergencia SIEMPRE se devuelve como dato; nunca se asume.
    """
    aj = aj or AjustesCiclo()
    ref = p.refrigerante
    sec = _lado_secundario(cond, p, aj)

    te_min = max(t_triple(ref) + 5.0, -25.0)
    te_max = sec["t_in_ev"] - 0.5
    tc_min = sec["t_in_cd"] + 0.5
    tc_max = t_critica(ref) - 5.0
    contador = {"n": 0}

    def sh_max_fisico(t_evap: float) -> float:
        """Tope del sobrecalentamiento: el refrigerante no puede salir del
        evaporador más caliente que el fluido que lo está calentando."""
        return max(sec["t_in_ev"] - t_evap - 0.5, _SH_MIN + 0.01)

    def t_evap_controlado(sh: float) -> float:
        """Bajo control de setpoint la carga está prescrita, así que la ecuación
        del evaporador da T_evap explícitamente DADO el sobrecalentamiento."""
        eps = _eps_evaporador(sh, sec, p)
        return float(np.clip(sec["t_in_ev"] - sec["q_load"] / (sec["c_ev"] * eps),
                             te_min, te_max))

    def _resolver(y_fijo: float | None, modo: str):
        controlado = y_fijo is None
        controlado_topologia = p.topologia.control_capacidad

        def desempaquetar(x):
            if controlado:
                t_cond = float(np.clip(x[0], tc_min, tc_max))
                sh_bruto, y = x[1], float(np.clip(x[2], 0.02, 3.0))
                sh = float(np.clip(sh_bruto, _SH_MIN, 60.0))
                t_evap = t_evap_controlado(sh)
                sh = float(np.clip(sh, _SH_MIN, sh_max_fisico(t_evap)))
                fuera = abs(x[0] - t_cond) + abs(x[2] - y)
            else:
                t_evap = float(np.clip(x[0], te_min, te_max))
                t_cond = float(np.clip(x[1], tc_min, tc_max))
                sh = float(np.clip(x[2], _SH_MIN, sh_max_fisico(t_evap)))
                y = y_fijo
                fuera = abs(x[0] - t_evap) + abs(x[1] - t_cond)
            return t_evap, t_cond, sh, y, fuera

        def residuos(x):
            contador["n"] += 1
            t_evap, t_cond, sh, y, fuera = desempaquetar(x)
            try:
                e = _evaluar(t_evap, t_cond, sh, y, sec, p, aj)
            except Exception:
                return [1e3, 1e3, 1e3]
            r_cond = (e["q_h_ref"] - e["q_h_sec"]) / p.Q_nom
            r_cap = ((e["q_l_ref"] - sec["q_load"]) / p.Q_nom if controlado
                     else (e["q_l_ref"] - e["q_l_sec"]) / p.Q_nom)
            if modo == "balance":
                r_valv = (e["m_r"] - e["m_valvula"]) / max(e["m_r"], 1e-9)
            elif modo == "inundado":
                r_valv = 10.0 * (sh - _SH_MIN)
            else:  # hambriento
                r_valv = 10.0 * (sh - sh_max_fisico(t_evap))
            pen = 10.0 * fuera
            return [r_cond + pen, r_valv + pen, r_cap + pen]

        if controlado:
            arranques = [(sec["t_in_cd"] + 14.0, p.SH_objetivo, max(cond.Q_load_frac, 0.3)),
                         (sec["t_in_cd"] + 10.0, p.SH_objetivo + 2.0, 0.8),
                         (sec["t_in_cd"] + 20.0, p.SH_objetivo - 1.5, 0.5),
                         (sec["t_in_cd"] + 14.0, 1.5, max(cond.Q_load_frac, 0.3)),
                         (sec["t_in_cd"] + 14.0, 0.5, max(cond.Q_load_frac, 0.3)),
                         (sec["t_in_cd"] + 25.0, p.SH_objetivo + 6.0, 1.0)]
        else:
            base_te = min(sec["t_in_ev"] - 5.0, te_max)
            arranques = [(base_te, sec["t_in_cd"] + 14.0, p.SH_objetivo),
                         (base_te - 4.0, sec["t_in_cd"] + 10.0, p.SH_objetivo + 3.0),
                         (base_te - 10.0, sec["t_in_cd"] + 20.0, p.SH_objetivo + 8.0),
                         (base_te + 2.0, sec["t_in_cd"] + 25.0, max(p.SH_objetivo - 2.0, 0.5))]

        mejor = None
        for arranque in arranques:
            sol, info, ier, msg = fsolve(residuos, np.array(arranque, dtype=float),
                                         full_output=True, xtol=1e-10, maxfev=600)
            t_evap, t_cond, sh, y, fuera = desempaquetar(sol)
            try:
                e = _evaluar(t_evap, t_cond, sh, y, sec, p, aj)
            except Exception:
                continue
            balances = [abs(e["q_h_ref"] - e["q_h_sec"]) / p.Q_nom,
                        abs((e["q_l_ref"] - sec["q_load"]) / p.Q_nom if y_fijo is None
                            else (e["q_l_ref"] - e["q_l_sec"]) / p.Q_nom)]
            if modo == "balance":
                balances.append(abs(e["m_r"] - e["m_valvula"]) / max(e["m_r"], 1e-9))
            residuo = max(balances)

            # CONDICIÓN DE VALIDEZ DEL RÉGIMEN. Los modos extremos sueltan la
            # ecuación de la válvula, así que SIEMPRE encuentran solución: sin
            # esta comprobación, el orden en que se prueban decidiría el
            # resultado en lugar de la física, y una válvula restringida podría
            # salir con firma de válvula inundada. Un régimen extremo solo es
            # admisible si el desbalance apunta en su propio sentido.
            if modo == "inundado" and not (e["m_valvula"] > e["m_r"]):
                residuo = float("inf")     # no sobrealimenta: el régimen no aplica
            elif modo == "hambriento" and not (e["m_valvula"] < e["m_r"]):
                residuo = float("inf")     # no subalimenta: el régimen no aplica

            # Los regímenes de CAPACIDAD necesitan la misma guarda. Fijar y = 1
            # siempre admite solución, así que sin esta comprobación una falla
            # que no tiene nada que ver con la capacidad —una válvula
            # ligeramente sobrealimentada— podía salir declarada como
            # «saturación de capacidad», entregando mucho más frío que la carga.
            # Solo hay saturación si la máquina se queda CORTA a plena
            # capacidad, y solo hay ciclado si sobra frío al mínimo.
            if y_fijo is not None and controlado_topologia:
                margen = 1e-6 * p.Q_nom
                if y_fijo >= 1.0 and e["q_l_ref"] > sec["q_load"] + margen:
                    residuo = float("inf")
                elif y_fijo <= p.y_min and e["q_l_ref"] < sec["q_load"] - margen:
                    residuo = float("inf")
            candidato = (residuo, t_evap, t_cond, sh, y, e, msg)
            if mejor is None or residuo < mejor[0]:
                mejor = candidato
            if residuo < tol and fuera < 1e-6:
                break
        if mejor is not None and not np.isfinite(mejor[0]):
            return None
        return mejor

    # --- secuencia de regímenes -------------------------------------------
    controla = p.topologia.control_capacidad
    if controla:
        # `hambriento` NO se prueba con capacidad controlada: si la válvula no
        # alcanza a alimentar, la enfriadora no puede sostener la carga, así que
        # imponer «capacidad = carga» sería imponer que la falla no ocurra. El
        # régimen hambriento va siempre acompañado de capacidad plena, y el agua
        # sale por encima del setpoint. `inundado` sí puede darse bajo control:
        # una válvula abierta inunda el evaporador sin impedir que la máquina
        # sostenga el setpoint.
        secuencia = [(None, "balance"), (None, "inundado"),
                     (1.0, "balance"), (1.0, "hambriento"), (1.0, "inundado")]
    else:
        secuencia = [(1.0, "balance"), (1.0, "inundado"), (1.0, "hambriento")]

    elegido = None
    for y_fijo, modo in secuencia:
        r = _resolver(y_fijo, modo)
        if r is None:
            continue
        if elegido is None or r[0] < elegido[0][0]:
            elegido = (r, y_fijo, modo)
        if r[0] < tol:
            elegido = (r, y_fijo, modo)
            break

    (residuo, t_evap, t_cond, sh, y, e, msg), y_fijo, modo = elegido

    # --- límites de capacidad ---------------------------------------------
    # Si la solución vino de un candidato con capacidad fija, la máquina ya está
    # contra un tope: plena capacidad (no alcanza el setpoint) o capacidad
    # mínima (sobre-enfría y en el equipo real ciclaría).
    saturada = bool(controla and y_fijo == 1.0)
    ciclado = bool(controla and y_fijo is not None and y_fijo == p.y_min)
    if controla and y_fijo is None:
        if y > 1.0:
            saturada = True
            r2 = _resolver(1.0, modo if modo != "hambriento" else "balance")
            if r2 is not None and r2[0] < max(residuo, tol):
                (residuo, t_evap, t_cond, sh, y, e, msg), y_fijo = r2, 1.0
        elif y < p.y_min:
            ciclado = True
            r2 = _resolver(p.y_min, modo)
            if r2 is not None and r2[0] < max(residuo, tol):
                (residuo, t_evap, t_cond, sh, y, e, msg), y_fijo = r2, p.y_min

    regimen = ("controlado" if (controla and y_fijo is None) else
               "saturado" if (controla and y_fijo == 1.0) else
               "ciclado" if controla else "capacidad_plena")
    if modo != "balance":
        regimen = f"{regimen}_{modo}"

    convergio = bool(residuo < tol)
    motivo = "" if convergio else (
        f"residuo {residuo:.2e} por encima de la tolerancia {tol:.0e} "
        f"(régimen {regimen})")

    q_l = e["q_l_ref"]
    exceso_alimentacion = (e["m_valvula"] - e["m_r"]) / max(e["m_r"], 1e-9)
    t_sec_out_ev = sec["t_in_ev"] - q_l / sec["c_ev"]
    t_sec_out_cd = sec["t_in_cd"] + e["q_h_sec"] / sec["c_cd"]
    desviacion = (t_sec_out_ev - p.T_agua_sup_sp) if p.topologia.evap_es_agua else 0.0

    topo = p.topologia
    medible: dict[str, float] = {
        "P_suc": pa_abs_a_psig(e["p_suc_pa"], p.P_atm),
        "P_des": pa_abs_a_psig(e["p_des_pa"], p.P_atm),
        "T_ev_out": e["t_ev_out"], "T_suc": e["t_suc"],
        "T_des": e["t_des"], "T_liq": e["t_liq_medido"],
        "I_avg": e["i_avg"], "W_elec": e["w_elec"],
    }
    if topo.evap_es_agua:
        medible.update({"T_agua_in_ev": sec["t_in_ev"], "T_agua_out_ev": t_sec_out_ev,
                        "V_agua_ev": sec["m_ev"]})
    else:
        medible.update({"T_air_in_ev": sec["t_in_ev"], "T_air_out_ev": t_sec_out_ev,
                        "V_air_ev": sec["m_ev"]})
    if topo.cond_es_agua:
        medible.update({"T_agua_in_cd": sec["t_in_cd"], "T_agua_out_cd": t_sec_out_cd,
                        "V_agua_cd": sec["m_cd"]})
    else:
        medible.update({"T_air_in_cd": sec["t_in_cd"], "T_air_out_cd": t_sec_out_cd})

    assert set(medible) == set(variables_medibles(topo)), (
        "El estado no expone exactamente las variables medibles de la topología")

    return EstadoCiclo(
        medible=medible,
        T_evap=t_evap, T_cond=t_cond, SH_evap=e["sh"], SC=e["sc"], y_capacidad=y,
        m_r=e["m_r"], Q_L=q_l, Q_H=e["q_h_sec"], W_comp=e["w_comp"], Q_linea=e["q_linea"],
        eta_v=e["eta_v"], eta_s_efectiva=e["eta_s"], apertura_valvula=e["apertura"],
        rp=e["rp"], h1=e["h1"], h2a=e["h2a"], h3=e["h3"], h4=e["h4"],
        P_suc_pa=e["p_suc_pa"], P_des_pa=e["p_des_pa"],
        T_sec_in_ev=sec["t_in_ev"], T_sec_out_ev=t_sec_out_ev,
        desviacion_setpoint=desviacion, capacidad_saturada=saturada, ciclado=ciclado,
        retorno_liquido=(modo == "inundado"), exceso_alimentacion=exceso_alimentacion,
        convergio=convergio, residuo=residuo, n_evaluaciones=contador["n"],
        regimen=regimen, motivo=motivo)


def cop_carnot(t_evap: float, t_cond: float) -> float:
    return c_a_k(t_evap) / (t_cond - t_evap)


if __name__ == "__main__":
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
    from config.params import PUNTO_DISENO, ParametrosEquipo

    p = ParametrosEquipo()
    for carga in (1.00, 0.70, 0.40):
        c = CondicionContorno(T_amb=35.0, HR_amb=80.0, Q_load_frac=carga)
        e = resolver_ciclo(c, p)
        print(f"carga={carga:.0%} regimen={e.regimen:12s} conv={e.convergio} "
              f"res={e.residuo:.1e} n={e.n_evaluaciones}")
        print(f"   T_evap={e.T_evap:6.2f} T_cond={e.T_cond:6.2f} y={e.y_capacidad:5.3f} "
              f"SH={e.SH_evap:5.2f} SC={e.SC:5.2f} a={e.apertura_valvula:5.3f}")
        print(f"   Q_L={e.Q_L/1000:7.1f} kW ({e.Q_L/3516.85:5.1f} TR) "
              f"W={e.W_elec/1000:6.1f} kW COP={e.Q_L/e.W_elec:4.2f} "
              f"agua {e.T_agua_in_ev:.2f}->{e.T_agua_out_ev:.2f} °C "
              f"(desv {e.desviacion_setpoint:+.2f} K)")
