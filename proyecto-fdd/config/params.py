"""Parámetros del equipo y del pipeline FDD.

TODOS los valores de equipo de este archivo son PROVISIONALES hasta que se
confirme el sitio de estudio y se llene la hoja `Ficha Tecnica` del cuaderno de
trabajo (sección 9 de la especificación).

La procedencia de cada parámetro se declara en `FUENTE_PARAMETROS`. Al arrancar
cualquier ejecución, `advertir_provisionales()` imprime la lista de parámetros
que siguen sin confirmar, para que ningún resultado se interprete como definitivo
por descuido.

Los `UA` NO se asumen: se calibran con `src.calibracion`. Los valores que
aparecen aquí son solo el punto de partida del ajuste.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, replace
from typing import NamedTuple

# ---------------------------------------------------------------------------
# Semilla maestra
# ---------------------------------------------------------------------------
# Única fuente de aleatoriedad del proyecto. De ella se derivan todos los flujos
# con SeedSequence.spawn() en src.generador y src.modelo. No debe existir ningún
# otro literal de semilla en el código.
SEMILLA_MAESTRA = 20260902

# Nombres de los flujos derivados, en orden fijo. El orden importa: cambiarlo
# cambia todos los resultados.
FLUJOS_ALEATORIOS = (
    "lhs_entrenamiento",   # barrido LHS del pool A (conjunto balanceado)
    "lhs_prevalencia",     # barrido LHS del pool B (conjunto de prevalencia)
    "ruido",               # ruido de sensor
    "particion",           # partición train/val/test
    "modelo",              # RandomForest, GridSearchCV, permutation importance
    "severidad",           # asignación de f dentro de cada nivel
)


# ---------------------------------------------------------------------------
# Procedencia de los parámetros
# ---------------------------------------------------------------------------
class FuenteParametro(NamedTuple):
    fuente: str
    provisional: bool


FUENTE_PARAMETROS: dict[str, FuenteParametro] = {
    "refrigerante":  FuenteParametro("Placa del equipo", True),
    "Q_nom":         FuenteParametro("Placa / catálogo", True),
    "V_disp":        FuenteParametro("Catálogo del compresor", True),
    "N_rev":         FuenteParametro("Placa (60 Hz, 2 polos, deslizamiento típico)", True),
    "eta_v0":        FuenteParametro("Curvas del fabricante", True),
    "k_v":           FuenteParametro("Curvas del fabricante", True),
    "eta_s":         FuenteParametro("Catálogo o estimada en campo", True),
    "eta_motor":     FuenteParametro("Catálogo del motor", True),
    "UA_ev":         FuenteParametro("CALIBRADA con datos de campo (src.calibracion)", True),
    "UA_cd":         FuenteParametro("CALIBRADA con datos de campo (src.calibracion)", True),
    "m_a_ev":        FuenteParametro("Placa / medición con balómetro", True),
    "m_a_cd":        FuenteParametro("Placa / medición con anemómetro", True),
    "SH_nom":        FuenteParametro("Manual de servicio", True),
    "SC_nom":        FuenteParametro("Manual de servicio", True),
    "dSH_linea":     FuenteParametro("Estimado (ganancia de calor en línea de succión)", True),
    "T_space_sp":    FuenteParametro("Panel de control", True),
    "W_vent_ev":     FuenteParametro("Placa del motoventilador", True),
    "W_vent_cd":     FuenteParametro("Placa del motoventilador", True),
    "cp_aire":       FuenteParametro("Propiedad física (Çengel), no provisional", False),
    "P_atm":         FuenteParametro("Presión atmosférica estándar, no provisional", False),
    "tension_linea": FuenteParametro("Medición en campo", True),
    "fp":            FuenteParametro("Analizador de redes", True),
}


@dataclass(frozen=True)
class ParametrosEquipo:
    """Parámetros físicos del activo. Unidades del SI salvo donde se indique."""

    # --- Refrigerante y capacidad -----------------------------------------
    refrigerante: str = "R410A"
    Q_nom: float = 17584.0          # W  (5 TR)

    # --- Compresor ---------------------------------------------------------
    V_disp: float = 7.90e-5         # m3/rev  (desplazamiento por revolución)
    N_rev: float = 48.3             # rev/s   (~2900 rpm)
    eta_v0: float = 0.92            # -       (eficiencia volumétrica a rp=1)
    k_v: float = 0.055              # -       (pendiente eta_v vs rp)
    eta_s: float = 0.70             # -       (eficiencia isentrópica)
    eta_motor: float = 0.90         # -       (eficiencia del motor eléctrico)

    # --- Intercambiadores --------------------------------------------------
    UA_ev: float = 1550.0           # W/K  -- valor inicial del ajuste
    UA_cd: float = 2400.0           # W/K  -- valor inicial del ajuste
    m_a_ev: float = 1.45            # kg/s
    m_a_cd: float = 2.05            # kg/s

    # --- Puntos de operación nominales -------------------------------------
    SH_nom: float = 5.0             # K   (sobrecalentamiento en el evaporador)
    SC_nom: float = 8.0             # K   (subenfriamiento en el condensador)
    dSH_linea: float = 3.0          # K   (ganancia adicional en línea de succión)
    T_space_sp: float = 24.0        # °C  (setpoint del espacio acondicionado)

    # --- Ventiladores y eléctrico ------------------------------------------
    W_vent_ev: float = 700.0        # W
    W_vent_cd: float = 500.0        # W
    tension_linea: float = 208.0    # V   (trifásica)
    fp: float = 0.88                # -   (factor de potencia)

    # --- Constantes físicas ------------------------------------------------
    cp_aire: float = 1005.0         # J/(kg·K)
    P_atm: float = 101325.0         # Pa

    def con(self, **cambios) -> "ParametrosEquipo":
        """Devuelve una copia con los cambios indicados (para inyectar fallas)."""
        return replace(self, **cambios)


# ---------------------------------------------------------------------------
# Condiciones de contorno: rangos de barrido (sección 2.1)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class RangosContorno:
    T_amb_min: float = 24.0         # °C
    T_amb_max: float = 36.0         # °C
    HR_amb_min: float = 60.0        # %
    HR_amb_max: float = 95.0        # %
    Q_load_frac_min: float = 0.40   # -
    Q_load_frac_max: float = 1.00   # -


# ---------------------------------------------------------------------------
# Punto de diseño usado para calibrar los UA (sección 9)
# ---------------------------------------------------------------------------
# Objetivo provisional: mientras no existan las mediciones de campo de la Fase 1,
# la calibración persigue las temperaturas de saturación de catálogo. Cuando
# lleguen los datos reales, se sustituyen por T_evap y T_cond derivadas de las
# presiones medidas (P_suc, P_des de la hoja `Registro Campo`).
PUNTO_DISENO = {
    "T_amb": 35.0,          # °C
    "HR_amb": 80.0,         # %
    "T_space": 24.0,        # °C
    "Q_load_frac": 1.00,    # -
}
OBJETIVO_CALIBRACION = {
    "T_evap": 7.0,          # °C  -- provisional (catálogo)
    "T_cond": 50.0,         # °C  -- provisional (catálogo)
}


# ---------------------------------------------------------------------------
# Ruido de sensor (sección 5) — trazado a la hoja `Instrumentos`
# ---------------------------------------------------------------------------
# sigma = exactitud / 2, asumiendo que la exactitud declarada es un intervalo de
# confianza del 95 %.
FONDO_ESCALA_P_SUC = 500.0   # psig -- manifold digital, provisional
FONDO_ESCALA_P_DES = 800.0   # psig -- manifold digital, provisional

SIGMA_RUIDO = {
    # variable        sigma      tipo
    "P_suc":         (0.0025 * FONDO_ESCALA_P_SUC, "absoluto"),   # 0,25 % del FS
    "P_des":         (0.0025 * FONDO_ESCALA_P_DES, "absoluto"),   # 0,25 % del FS
    "T_ev_out":      (0.25, "absoluto"),    # K, termopar tipo K
    "T_suc":         (0.25, "absoluto"),    # K
    "T_des":         (0.25, "absoluto"),    # K
    "T_liq":         (0.25, "absoluto"),    # K
    "T_air_in_ev":   (0.15, "absoluto"),    # K, sonda T-HR
    "T_air_out_ev":  (0.15, "absoluto"),    # K
    "T_air_in_cd":   (0.15, "absoluto"),    # K
    "T_air_out_cd":  (0.15, "absoluto"),    # K
    "HR_amb":        (1.0, "absoluto"),     # % HR
    "I_avg":         (0.0075, "relativo"),  # 0,75 % de la lectura
    "W_elec":        (0.005, "relativo"),   # 0,5 % de la lectura
    "V_air_ev":      (0.015, "relativo"),   # 1,5 % de la lectura
}


# ---------------------------------------------------------------------------
# Generación del dataset (sección 6)
# ---------------------------------------------------------------------------
N_COND_ENTRENAMIENTO = 400      # condiciones LHS del pool A
N_MUESTRAS_PREVALENCIA = 3000   # muestras del conjunto de prevalencia (pool B)
TOL_BALANCE = 1e-4              # tolerancia del residuo del balance de energía
MAX_DESCARTE_ADMISIBLE = 0.05   # fracción de puntos no convergidos tolerada


# ---------------------------------------------------------------------------
# Utilidades de trazabilidad
# ---------------------------------------------------------------------------
def parametros_provisionales() -> list[str]:
    """Nombres de los parámetros que siguen marcados como provisionales."""
    return sorted(k for k, v in FUENTE_PARAMETROS.items() if v.provisional)


def advertir_provisionales(silencioso: bool = False) -> list[str]:
    """Imprime y devuelve la lista de parámetros provisionales en uso."""
    provisionales = parametros_provisionales()
    if not silencioso:
        print("=" * 78)
        print("AVISO: parámetros PROVISIONALES en uso "
              f"({len(provisionales)} de {len(FUENTE_PARAMETROS)})")
        print("Los resultados NO corresponden todavía a un equipo real.")
        print("-" * 78)
        for nombre in provisionales:
            print(f"  {nombre:15s} <- {FUENTE_PARAMETROS[nombre].fuente}")
        print("=" * 78)
    return provisionales


def resumen_parametros(p: ParametrosEquipo) -> dict:
    """Diccionario serializable con los parámetros y su procedencia."""
    valores = asdict(p)
    return {
        nombre: {
            "valor": valor,
            "fuente": FUENTE_PARAMETROS.get(nombre, FuenteParametro("no declarada", True)).fuente,
            "provisional": FUENTE_PARAMETROS.get(nombre, FuenteParametro("", True)).provisional,
        }
        for nombre, valor in valores.items()
    }
