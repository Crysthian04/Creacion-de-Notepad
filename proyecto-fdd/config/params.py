"""Parámetros del equipo y del pipeline FDD.

TODOS los valores de equipo de este archivo son PROVISIONALES hasta que se
confirme la placa del equipo y se llene la hoja `Ficha Tecnica` (sección 9 de la
especificación). La procedencia de cada uno se declara en `FUENTE_PARAMETROS` y
`advertir_provisionales()` los lista al arrancar cualquier ejecución.

SISTEMA DE ESTUDIO
------------------
Enfriadora de agua (chiller) de 100 TR que da servicio a un edificio de
oficinas, con distribución hidrónica hacia manejadoras y fan-coils. El tipo de
condensador —aire o agua con torre— se resuelve en el levantamiento de campo;
hasta entonces el caso base es condensador enfriado por AIRE, que es el que
exige menos supuestos inventados.

El modelo de expansión directa se conserva como topología seleccionable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import NamedTuple

from src.topologia import TOPOLOGIAS, Topologia

# ---------------------------------------------------------------------------
# Selección del sistema
# ---------------------------------------------------------------------------
TIPO_SISTEMA = "chiller_cond_aire"


# ---------------------------------------------------------------------------
# Semilla maestra
# ---------------------------------------------------------------------------
SEMILLA_MAESTRA = 20260902

FLUJOS_ALEATORIOS = (
    "lhs_entrenamiento",   # barrido LHS del pool A (conjunto balanceado)
    "lhs_prevalencia",     # barrido LHS del pool B (conjunto de prevalencia)
    "ruido",               # ruido de sensor
    "particion",           # partición train/val/test
    "modelo",              # RandomForest, GridSearchCV, permutation importance
    "severidad",           # asignación de f dentro de cada nivel
    "discrepancia",        # error de calibración del gemelo digital
)


# ---------------------------------------------------------------------------
# Procedencia de los parámetros
# ---------------------------------------------------------------------------
class FuenteParametro(NamedTuple):
    fuente: str
    provisional: bool


FUENTE_PARAMETROS: dict[str, FuenteParametro] = {
    "refrigerante":    FuenteParametro("Placa del equipo", True),
    "Q_nom":           FuenteParametro("Placa / catálogo", True),
    "V_disp":          FuenteParametro("Catálogo del compresor de tornillo", True),
    "N_rev":           FuenteParametro("Placa (60 Hz)", True),
    "eta_v0":          FuenteParametro("Curvas del fabricante", True),
    "k_v":             FuenteParametro("Curvas del fabricante", True),
    "eta_s":           FuenteParametro("Catálogo o estimada en campo", True),
    "k_carga_parcial": FuenteParametro("Curva IPLV del fabricante", True),
    "y_min":           FuenteParametro("Capacidad mínima de la válvula deslizante", True),
    "eta_motor":       FuenteParametro("Catálogo del motor", True),
    "UA_ev":           FuenteParametro("CALIBRADA con datos de campo (src.calibracion)", True),
    "UA_cd":           FuenteParametro("CALIBRADA con datos de campo (src.calibracion)", True),
    "m_w_ev":          FuenteParametro("Placa de la bomba / balance térmico", True),
    "m_w_cd":          FuenteParametro("Placa de la bomba de condensación", True),
    "m_a_ev":          FuenteParametro("Solo expansión directa: placa / balómetro", True),
    "m_a_cd":          FuenteParametro("Placa / anemómetro", True),
    "T_agua_sup_sp":   FuenteParametro("Panel de control de la enfriadora", True),
    "dT_agua_nom":     FuenteParametro("Diseño de la red hidrónica", True),
    "approach_torre":  FuenteParametro("Catálogo de la torre (solo cond. de agua)", True),
    "K_v_valvula":     FuenteParametro("Catálogo de la válvula de expansión", True),
    "K_ctrl_valvula":  FuenteParametro("Ganancia del lazo de sobrecalentamiento", True),
    "beta_sh_UA":      FuenteParametro("Acoplamiento empírico zona seca (ver src/ciclo.py)", True),
    "SH_objetivo":     FuenteParametro("Ajuste de la válvula / manual de servicio", True),
    "SC_nom":          FuenteParametro("Manual de servicio", True),
    "k_SC_Tcond":      FuenteParametro("Acoplamiento empírico (ver src/ciclo.py)", True),
    "dSH_linea":       FuenteParametro("Estimado (ganancia en línea de succión)", True),
    "W_aux":           FuenteParametro("Placa de ventiladores / auxiliares", True),
    "tension_linea":   FuenteParametro("Medición en campo", True),
    "fp":              FuenteParametro("Analizador de redes", True),
    "cp_agua":         FuenteParametro("Propiedad física (Çengel), no provisional", False),
    "cp_aire":         FuenteParametro("Propiedad física (Çengel), no provisional", False),
    "P_atm":           FuenteParametro("Presión atmosférica estándar, no provisional", False),
}


@dataclass(frozen=True)
class ParametrosEquipo:
    """Parámetros físicos del activo. Unidades del SI salvo donde se indique.

    Un solo dataclass cubre las tres topologías; cada una usa los campos que le
    corresponden (`m_w_ev` en enfriadora, `m_a_ev` en expansión directa).
    """

    topologia: Topologia = field(default_factory=lambda: TOPOLOGIAS[TIPO_SISTEMA])

    # --- Refrigerante y capacidad -----------------------------------------
    refrigerante: str = "R134a"
    Q_nom: float = 351685.0          # W  (100 TR)

    # --- Compresor de tornillo ---------------------------------------------
    V_disp: float = 3.80e-3          # m3/rev
    N_rev: float = 49.2              # rev/s (~2950 rpm)
    eta_v0: float = 0.92
    k_v: float = 0.030               # pendiente eta_v vs relación de presiones
    eta_s: float = 0.72
    k_carga_parcial: float = 0.30    # penalización de eta_s a carga parcial
    y_min: float = 0.25              # capacidad mínima (válvula deslizante)
    eta_motor: float = 0.94

    # --- Intercambiadores ---------------------------------------------------
    UA_ev: float = 77000.0           # W/K  -- valor inicial del ajuste
    UA_cd: float = 63000.0           # W/K  -- valor inicial del ajuste
    m_w_ev: float = 16.80            # kg/s  agua helada
    m_w_cd: float = 22.60            # kg/s  agua de condensación (cond. de agua)
    m_a_ev: float = 1.45             # kg/s  solo expansión directa
    m_a_cd: float = 39.20            # kg/s  aire del condensador

    # --- Circuito hidrónico -------------------------------------------------
    T_agua_sup_sp: float = 7.0       # °C  setpoint de agua helada de suministro
    dT_agua_nom: float = 5.0         # K   salto nominal (12 -> 7 °C)
    approach_torre: float = 4.0      # K   sobre bulbo húmedo (cond. de agua)

    # --- Válvula de expansión (elemento de flujo) ---------------------------
    K_v_valvula: float = 9.65e-5     # coeficiente de flujo [kg/s / sqrt(Pa·kg/m3)]
    K_ctrl_valvula: float = 0.16     # ganancia del lazo proporcional [1/K]
    a_nom: float = 0.75              # apertura nominal (reserva del 33 %)
    a_min: float = 0.02
    SH_objetivo: float = 5.0         # K  sobrecalentamiento objetivo de la válvula
    dSH_linea: float = 3.0           # K  ganancia en la línea de succión
    beta_sh_UA: float = 0.45         # fracción de UA_ev que pierde la zona seca
    SH_ref_area: float = 15.0        # K  sobrecalentamiento que satura esa pérdida

    # --- Subenfriamiento ----------------------------------------------------
    SC_nom: float = 6.0              # K
    k_SC_Tcond: float = 0.15         # K/K  acoplamiento SC-presión de condensación
    T_cond_ref_SC: float = 45.0      # °C  referencia del acoplamiento

    # --- Eléctrico y auxiliares --------------------------------------------
    W_aux: float = 8000.0            # W  ventiladores del condensador / auxiliares
    tension_linea: float = 480.0     # V
    fp: float = 0.88

    # --- Constantes físicas -------------------------------------------------
    cp_agua: float = 4186.0          # J/(kg·K)
    cp_aire: float = 1005.0          # J/(kg·K)
    P_atm: float = 101325.0          # Pa

    # --- Expansión directa: setpoint del espacio ---------------------------
    T_space_sp: float = 24.0         # °C  (solo topología expansión_directa)

    def con(self, **cambios) -> "ParametrosEquipo":
        """Copia con los cambios indicados (para inyectar fallas o discrepancia)."""
        return replace(self, **cambios)

    @property
    def cp_secundario_ev(self) -> float:
        return self.cp_agua if self.topologia.evap_es_agua else self.cp_aire

    @property
    def cp_secundario_cd(self) -> float:
        return self.cp_agua if self.topologia.cond_es_agua else self.cp_aire

    @property
    def m_secundario_ev(self) -> float:
        return self.m_w_ev if self.topologia.evap_es_agua else self.m_a_ev

    @property
    def m_secundario_cd(self) -> float:
        return self.m_w_cd if self.topologia.cond_es_agua else self.m_a_cd

    @property
    def nombre_caudal_ev(self) -> str:
        return "m_w_ev" if self.topologia.evap_es_agua else "m_a_ev"

    @property
    def nombre_caudal_cd(self) -> str:
        return "m_w_cd" if self.topologia.cond_es_agua else "m_a_cd"


def parametros_expansion_directa() -> ParametrosEquipo:
    """Preset de respaldo: reproduce el equipo de expansión directa de 5 TR."""
    return ParametrosEquipo(
        topologia=TOPOLOGIAS["expansion_directa"],
        refrigerante="R410A", Q_nom=17584.0,
        V_disp=7.90e-5, N_rev=48.3, eta_v0=0.92, k_v=0.055, eta_s=0.70,
        k_carga_parcial=0.0, y_min=1.0, eta_motor=0.90,
        UA_ev=2222.4, UA_cd=2897.5, m_a_ev=1.45, m_a_cd=2.05,
        K_v_valvula=2.95e-6, K_ctrl_valvula=0.16, SH_objetivo=5.0, dSH_linea=3.0,
        SC_nom=8.0, k_SC_Tcond=0.15, T_cond_ref_SC=45.0, beta_sh_UA=0.45, SH_ref_area=15.0,
        W_aux=1200.0, tension_linea=208.0, fp=0.88, T_space_sp=24.0)


# ---------------------------------------------------------------------------
# Condiciones de contorno: rangos de barrido (sección 2.1)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class RangosContorno:
    T_amb_min: float = 24.0
    T_amb_max: float = 36.0
    HR_amb_min: float = 60.0
    HR_amb_max: float = 95.0
    Q_load_frac_min: float = 0.40
    Q_load_frac_max: float = 1.00


# ---------------------------------------------------------------------------
# Punto de diseño para calibrar los UA (sección 9)
# ---------------------------------------------------------------------------
PUNTO_DISENO = {"T_amb": 35.0, "HR_amb": 80.0, "Q_load_frac": 1.00}
OBJETIVO_CALIBRACION = {"T_evap": 4.5, "T_cond": 50.0}   # °C, provisional (catálogo)

PUNTO_DISENO_DX = {"T_amb": 35.0, "HR_amb": 80.0, "Q_load_frac": 1.00}
OBJETIVO_CALIBRACION_DX = {"T_evap": 7.0, "T_cond": 50.0}


# ---------------------------------------------------------------------------
# Ruido de sensor (sección 5) — trazado a la hoja `Instrumentos`
# ---------------------------------------------------------------------------
# sigma = exactitud / 2, asumiendo que la exactitud declarada es un intervalo de
# confianza del 95 %.
FONDO_ESCALA_P_SUC = 300.0   # psig -- manifold digital, provisional
FONDO_ESCALA_P_DES = 500.0   # psig

SIGMA_RUIDO = {
    "P_suc":         (0.0025 * FONDO_ESCALA_P_SUC, "absoluto"),   # 0,25 % del FS
    "P_des":         (0.0025 * FONDO_ESCALA_P_DES, "absoluto"),
    "T_ev_out":      (0.25, "absoluto"),    # K, termopar tipo K
    "T_suc":         (0.25, "absoluto"),
    "T_des":         (0.25, "absoluto"),
    "T_liq":         (0.25, "absoluto"),
    # Agua: RTD Pt100 en pozo termométrico, ± 0,2 K
    "T_agua_in_ev":  (0.10, "absoluto"),
    "T_agua_out_ev": (0.10, "absoluto"),
    "T_agua_in_cd":  (0.10, "absoluto"),
    "T_agua_out_cd": (0.10, "absoluto"),
    # Aire: sonda T-HR, ± 0,3 K
    "T_air_in_ev":   (0.15, "absoluto"),
    "T_air_out_ev":  (0.15, "absoluto"),
    "T_air_in_cd":   (0.15, "absoluto"),
    "T_air_out_cd":  (0.15, "absoluto"),
    "HR_amb":        (1.0, "absoluto"),     # % HR
    "I_avg":         (0.0075, "relativo"),  # pinza True RMS, 1,5 % de la lectura
    "W_elec":        (0.005, "relativo"),   # analizador de redes, 1 %
    # Caudalímetro ultrasónico de abrazadera, ± 2 % de la lectura
    "V_agua_ev":     (0.010, "relativo"),
    "V_agua_cd":     (0.010, "relativo"),
    "V_air_ev":      (0.015, "relativo"),   # balómetro, 3 %
}


# ---------------------------------------------------------------------------
# Discrepancia entre modelo y planta (corrección C1)
# ---------------------------------------------------------------------------
# Los datos se generan con theta_planta; la referencia sana que se resta se
# calcula con theta_modelo = theta_planta·(1 + epsilon). Representa el error de
# calibración del gemelo digital, que en campo es la fuente de error dominante,
# por encima del ruido de los instrumentos.
NIVEL_DISCREPANCIA = 0.05          # delta: |epsilon| <= 5 % en el caso base
DISTRIBUCION_DISCREPANCIA = "uniforme"   # epsilon ~ U(-delta, +delta): error acotado
MODO_DISCREPANCIA = "por_condicion"      # "por_condicion" | "por_corrida"
NIVELES_DISCREPANCIA_BARRIDO = (0.0, 0.03, 0.05, 0.08, 0.15)
N_REPETICIONES_POR_CORRIDA = 5     # repeticiones con epsilon por corrida en el nivel base


def parametros_con_discrepancia(p: ParametrosEquipo) -> tuple[str, ...]:
    """Parámetros afectados por el error de calibración, según la topología."""
    return ("UA_ev", "UA_cd", "eta_v0", "eta_s", p.nombre_caudal_ev, p.nombre_caudal_cd)


# ---------------------------------------------------------------------------
# Generación del dataset (sección 6)
# ---------------------------------------------------------------------------
N_COND_ENTRENAMIENTO = 400
N_MUESTRAS_PREVALENCIA = 10000     # subido de 3000: con 0,3 % de txv_sobrealimenta,
                                   # 3000 muestras dejaban 9 casos y la precisión de
                                   # esa clase era ruido estadístico
TOL_BALANCE = 1e-4
MAX_DESCARTE_ADMISIBLE = 0.05
SOPORTE_MINIMO_SIN_INTERVALO = 50  # por debajo, se reportan intervalos de Wilson


# ---------------------------------------------------------------------------
# Utilidades de trazabilidad
# ---------------------------------------------------------------------------
def parametros_provisionales() -> list[str]:
    return sorted(k for k, v in FUENTE_PARAMETROS.items() if v.provisional)


def advertir_provisionales(silencioso: bool = False) -> list[str]:
    provisionales = parametros_provisionales()
    if not silencioso:
        print("=" * 78)
        print(f"AVISO: parámetros PROVISIONALES en uso "
              f"({len(provisionales)} de {len(FUENTE_PARAMETROS)})")
        print("Los resultados NO corresponden todavía a un equipo real.")
        print("-" * 78)
        for nombre in provisionales:
            print(f"  {nombre:16s} <- {FUENTE_PARAMETROS[nombre].fuente}")
        print("=" * 78)
    return provisionales


def resumen_parametros(p: ParametrosEquipo) -> dict:
    valores = {k: v for k, v in asdict(p).items() if k != "topologia"}
    salida = {
        nombre: {
            "valor": valor,
            "fuente": FUENTE_PARAMETROS.get(nombre, FuenteParametro("no declarada", True)).fuente,
            "provisional": FUENTE_PARAMETROS.get(nombre, FuenteParametro("", True)).provisional,
        }
        for nombre, valor in valores.items()
    }
    salida["topologia"] = {"valor": p.topologia.nombre, "fuente": "Levantamiento de campo",
                           "provisional": True}
    return salida
