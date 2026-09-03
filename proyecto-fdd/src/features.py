"""Cálculo de variables derivadas y de RESIDUOS (Capa 3, entrada del clasificador).

Regla dura del proyecto (deriva del defecto D1 de la auditoría):

    La matriz de características se construye por LISTA BLANCA de columnas
    `res_*`. NUNCA por `drop` de columnas no deseadas.

La diferencia importa: un `drop` falla en silencio cuando alguien agrega una
columna nueva al dataset, y esa columna entra al modelo sin que nadie lo note.
Una lista blanca falla ruidosamente, que es como debe fallar.

Las temperaturas de saturación se obtienen con CoolProp, usando ROCÍO para el
sobrecalentamiento y BURBUJA para el subenfriamiento (sección 2.3). Esto importa
en refrigerantes zeotrópicos con deslizamiento.
"""

from __future__ import annotations

import pandas as pd

from .ciclo import psig_a_pa_abs, t_burbuja, t_rocio

# ---------------------------------------------------------------------------
# Variables derivadas (sección 2.3)
# ---------------------------------------------------------------------------
COLUMNAS_DERIVADAS: tuple[str, ...] = (
    "SH_evap", "SH_total", "SC", "split_cond", "approach_evap", "SH_des",
    "rp", "dT_air_ev", "dT_air_cd", "COP_sist", "kW_TR",
)

# Correspondencia derivada -> nombre del residuo (sección 6.3). Explícita a
# propósito: `res_COP` y `res_kW_TR` no siguen el patrón mecánico del prefijo.
DERIVADA_A_RESIDUO: dict[str, str] = {
    "SH_evap": "res_SH_evap",
    "SH_total": "res_SH_total",
    "SC": "res_SC",
    "split_cond": "res_split_cond",
    "approach_evap": "res_approach_evap",
    "SH_des": "res_SH_des",
    "rp": "res_rp",
    "dT_air_ev": "res_dT_air_ev",
    "dT_air_cd": "res_dT_air_cd",
    "COP_sist": "res_COP",
    "kW_TR": "res_kW_TR",
}

# ===========================================================================
# LISTA BLANCA: las únicas columnas que el clasificador puede ver.
# ===========================================================================
COLUMNAS_RESIDUOS: tuple[str, ...] = tuple(DERIVADA_A_RESIDUO[d] for d in COLUMNAS_DERIVADAS)

# Columnas que jamás deben entrar al modelo, y el motivo. Se documenta aquí para
# que la exclusión sea una decisión trazable y no un olvido afortunado.
EXCLUIDAS_Y_MOTIVO: dict[str, str] = {
    "T_amb": "condición de contorno: el modelo aprendería clima en lugar de falla",
    "HR_amb": "condición de contorno",
    "T_space": "condición de contorno",
    "Q_load_frac": "condición de contorno; además no es medible en campo",
    "P_suc": "medición cruda: su valor absoluto depende del clima",
    "P_des": "medición cruda",
    "clase": "etiqueta",
    "clase_id": "etiqueta",
    "severidad_f": "derivada de la etiqueta: fuga directa del objetivo",
    "nivel": "derivada de la etiqueta: fuga directa del objetivo",
    "cond_id": "identificador sin contenido físico (defecto D2 de la auditoría)",
    "muestra_id": "identificador sin contenido físico",
}

TR_EN_W = 3516.85  # 1 tonelada de refrigeración en watts


class ColumnasFaltantes(KeyError):
    """El DataFrame no trae todas las columnas de la lista blanca."""


# ---------------------------------------------------------------------------
# Variables derivadas a partir de las MEDICIONES (con ruido, como en campo)
# ---------------------------------------------------------------------------
def derivadas_desde_medicion(med: dict, p) -> dict[str, float]:
    """Calcula las 11 variables derivadas a partir de lo que el equipo mide.

    `med` contiene únicamente variables de la sección 2.2 más el caudal de aire
    del evaporador (hoja `Instrumentos`: balómetro, ±3 %). No accede a ninguna
    variable interna del modelo: si el cálculo necesitara algo no medible, el
    sistema no sería implementable en campo.
    """
    ref = p.refrigerante
    p_suc_pa = psig_a_pa_abs(med["P_suc"], p.P_atm)
    p_des_pa = psig_a_pa_abs(med["P_des"], p.P_atm)

    t_roc_suc = t_rocio(round(p_suc_pa, 3), ref)
    t_bur_des = t_burbuja(round(p_des_pa, 3), ref)
    t_roc_des = t_rocio(round(p_des_pa, 3), ref)

    dt_air_ev = med["T_air_in_ev"] - med["T_air_out_ev"]
    q_l = med["V_air_ev"] * p.cp_aire * dt_air_ev          # W, lado aire
    w_elec = med["W_elec"]

    return {
        "SH_evap": med["T_ev_out"] - t_roc_suc,
        "SH_total": med["T_suc"] - t_roc_suc,
        "SC": t_bur_des - med["T_liq"],
        "split_cond": t_bur_des - med["T_air_in_cd"],
        "approach_evap": med["T_air_in_ev"] - t_roc_suc,
        "SH_des": med["T_des"] - t_roc_des,
        "rp": p_des_pa / p_suc_pa,
        "dT_air_ev": dt_air_ev,
        "dT_air_cd": med["T_air_out_cd"] - med["T_air_in_cd"],
        "COP_sist": q_l / w_elec,
        "kW_TR": (w_elec / 1000.0) / max(q_l / TR_EN_W, 1e-9),
    }


def calcular_residuos(derivadas_med: dict, derivadas_ref: dict) -> dict[str, float]:
    """RESIDUO = (medición degradada) − (predicción sana a igual contorno).

    Al restar la predicción del modelo sano en las mismas condiciones de
    contorno, la variabilidad operacional se cancela y queda solo la firma de la
    degradación. Es lo que impide que el clasificador confunda clima con avería.
    """
    return {DERIVADA_A_RESIDUO[d]: derivadas_med[d] - derivadas_ref[d]
            for d in COLUMNAS_DERIVADAS}


# ---------------------------------------------------------------------------
# Construcción de X — LISTA BLANCA
# ---------------------------------------------------------------------------
def construir_matriz_X(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve la matriz de características: SOLO las columnas `res_*`.

    Selección explícita, nunca `drop`. Si falta alguna columna de la lista
    blanca, falla ruidosamente en lugar de devolver una matriz incompleta.
    """
    faltantes = [c for c in COLUMNAS_RESIDUOS if c not in df.columns]
    if faltantes:
        raise ColumnasFaltantes(
            f"Faltan columnas de residuo en el DataFrame: {faltantes}. "
            f"Se esperaban las {len(COLUMNAS_RESIDUOS)} columnas de COLUMNAS_RESIDUOS."
        )
    X = df.loc[:, list(COLUMNAS_RESIDUOS)].copy()
    # Verificación redundante a propósito: si alguna vez alguien cambia la
    # implementación por un `drop`, esta aserción lo detiene aquí.
    assert tuple(X.columns) == COLUMNAS_RESIDUOS, "La matriz X no respeta la lista blanca"
    return X


def objetivo(df: pd.DataFrame, columna: str = "clase_id") -> pd.Series:
    return df[columna]


def grupos(df: pd.DataFrame) -> pd.Series:
    """Identificador de condición de contorno, para particionar por grupos.

    Una condición genera 30 filas (10 clases × 3 niveles). Partir por fila
    metería la misma condición en entrenamiento y en prueba (sección 7.1).
    """
    return df["cond_id"]
