"""Variables derivadas y RESIDUOS (Capa 3, entrada del clasificador).

Regla dura del proyecto (defecto D1 de la auditoría de la Etapa 1):

    La matriz de características se construye por LISTA BLANCA de columnas
    `res_*`. NUNCA por `drop` de columnas no deseadas.

La lista blanca ahora se deriva de la TOPOLOGÍA, pero sigue siendo una lista
blanca: selección explícita, y falla ruidosamente si falta una columna.

Las temperaturas de saturación se obtienen con CoolProp, usando ROCÍO para el
sobrecalentamiento y BURBUJA para el subenfriamiento (sección 2.3).
"""

from __future__ import annotations

import pandas as pd

from .ciclo import psig_a_pa_abs, t_burbuja, t_rocio
from .topologia import (Topologia, nombre_entrada_condensador, nombre_entrada_evaporador,
                        nombre_salida_condensador, nombre_salida_evaporador)

TR_EN_W = 3516.85


class ColumnasFaltantes(KeyError):
    """El DataFrame no trae todas las columnas de la lista blanca."""


# ---------------------------------------------------------------------------
# Variables derivadas por topología (sección 2.3)
# ---------------------------------------------------------------------------
def columnas_derivadas(topo: Topologia) -> tuple[str, ...]:
    comunes = ("SH_evap", "SH_total", "SC", "SH_des", "rp", "COP_sist", "kW_TR")
    if topo.evap_es_agua:
        # `approach_ev` = agua helada de suministro − temperatura de evaporación.
        # Es de las variables más informativas en diagnóstico de enfriadoras y
        # no existe en un equipo de expansión directa.
        evap = ("approach_ev", "dT_agua_ev")
    else:
        evap = ("approach_evap", "dT_air_ev")
    if topo.cond_es_agua:
        cond = ("split_cond", "approach_cd", "dT_agua_cd")
    else:
        cond = ("split_cond", "dT_air_cd")
    return comunes + evap + cond


def derivada_a_residuo(topo: Topologia) -> dict[str, str]:
    """Correspondencia explícita: `COP_sist` -> `res_COP` no sigue el patrón."""
    especiales = {"COP_sist": "res_COP", "kW_TR": "res_kW_TR"}
    return {d: especiales.get(d, f"res_{d}") for d in columnas_derivadas(topo)}


# ===========================================================================
# LISTA BLANCA: las únicas columnas que el clasificador puede ver.
# ===========================================================================
def columnas_residuos(topo: Topologia) -> tuple[str, ...]:
    mapa = derivada_a_residuo(topo)
    return tuple(mapa[d] for d in columnas_derivadas(topo))


# Columnas que jamás deben entrar al modelo, y el motivo. La exclusión es una
# decisión trazable, no un olvido afortunado.
EXCLUIDAS_Y_MOTIVO: dict[str, str] = {
    "T_amb": "condición de contorno: el modelo aprendería clima en lugar de falla",
    "HR_amb": "condición de contorno",
    "Q_load_frac": "condición de contorno; además no es medible en campo",
    "P_suc": "medición cruda: su valor absoluto depende del clima y de la carga",
    "P_des": "medición cruda",
    "clase": "etiqueta",
    "clase_id": "etiqueta",
    "severidad_f": "derivada de la etiqueta: fuga directa del objetivo",
    "nivel": "derivada de la etiqueta: fuga directa del objetivo",
    "cond_id": "identificador sin contenido físico (defecto D2 de la auditoría)",
    "muestra_id": "identificador sin contenido físico",
    "capacidad_saturada": "bandera del control: fuertemente correlacionada con la "
                          "severidad de la falla. Se registra para el análisis, "
                          "no para entrenar",
    "ciclado": "bandera del control: correlacionada con la carga y la severidad",
    "retorno_liquido": "bandera del régimen de la válvula: correlacionada con la "
                       "severidad de la sobrealimentación",
    "regimen": "etiqueta del régimen de operación resuelto por el modelo; no es "
               "una medición de campo",
    "desviacion_setpoint": "consecuencia directa de la saturación de capacidad",
    "y_capacidad": "no es medible con el inventario de instrumentos; si el sistema "
                   "de automatización del edificio expusiera el % de capacidad, "
                   "sería una característica adicional muy informativa",
}


# ---------------------------------------------------------------------------
# Derivadas a partir de las MEDICIONES (con ruido, como en campo)
# ---------------------------------------------------------------------------
def derivadas_desde_medicion(med: dict, p) -> dict[str, float]:
    """Calcula las variables derivadas con lo que el equipo mide, y nada más.

    Si el cálculo necesitara una variable no medible, el sistema no sería
    implementable en campo y la propuesta perdería sentido.
    """
    topo: Topologia = p.topologia
    ref = p.refrigerante
    p_suc_pa = psig_a_pa_abs(med["P_suc"], p.P_atm)
    p_des_pa = psig_a_pa_abs(med["P_des"], p.P_atm)

    t_roc_suc = t_rocio(round(p_suc_pa, 3), ref)
    t_bur_des = t_burbuja(round(p_des_pa, 3), ref)
    t_roc_des = t_rocio(round(p_des_pa, 3), ref)

    ent_ev = med[nombre_entrada_evaporador(topo)]
    sal_ev = med[nombre_salida_evaporador(topo)]
    ent_cd = med[nombre_entrada_condensador(topo)]
    sal_cd = med[nombre_salida_condensador(topo)]

    if topo.evap_es_agua:
        caudal_ev = med["V_agua_ev"]
        cp_ev = p.cp_agua
    else:
        caudal_ev = med["V_air_ev"]
        cp_ev = p.cp_aire

    d_sec_ev = ent_ev - sal_ev                       # salto en el fluido secundario
    q_l = caudal_ev * cp_ev * d_sec_ev               # W, lado secundario
    w_elec = med["W_elec"]

    d = {
        "SH_evap": med["T_ev_out"] - t_roc_suc,
        "SH_total": med["T_suc"] - t_roc_suc,
        "SC": t_bur_des - med["T_liq"],
        "SH_des": med["T_des"] - t_roc_des,
        "rp": p_des_pa / p_suc_pa,
        "COP_sist": q_l / w_elec,
        "kW_TR": (w_elec / 1000.0) / max(q_l / TR_EN_W, 1e-9),
        "split_cond": t_bur_des - ent_cd,
    }
    if topo.evap_es_agua:
        d["approach_ev"] = sal_ev - t_roc_suc
        d["dT_agua_ev"] = d_sec_ev
    else:
        d["approach_evap"] = ent_ev - t_roc_suc
        d["dT_air_ev"] = d_sec_ev
    if topo.cond_es_agua:
        d["approach_cd"] = t_bur_des - sal_cd
        d["dT_agua_cd"] = sal_cd - ent_cd
    else:
        d["dT_air_cd"] = sal_cd - ent_cd

    esperadas = set(columnas_derivadas(topo))
    assert set(d) == esperadas, f"Derivadas inesperadas: {set(d) ^ esperadas}"
    return d


def calcular_residuos(derivadas_med: dict, derivadas_ref: dict, topo: Topologia
                      ) -> dict[str, float]:
    """RESIDUO = (medición degradada) − (predicción sana a igual contorno).

    Al restar la predicción del modelo sano en las mismas condiciones de
    contorno, la variabilidad operacional se cancela y queda solo la firma de la
    degradación. Es lo que impide que el clasificador confunda clima con avería.
    """
    mapa = derivada_a_residuo(topo)
    return {mapa[d]: derivadas_med[d] - derivadas_ref[d] for d in columnas_derivadas(topo)}


# ---------------------------------------------------------------------------
# Construcción de X — LISTA BLANCA
# ---------------------------------------------------------------------------
def construir_matriz_X(df: pd.DataFrame, topo: Topologia) -> pd.DataFrame:
    """Devuelve la matriz de características: SOLO las columnas `res_*`.

    Selección explícita, nunca `drop`. Si falta alguna columna de la lista
    blanca, falla ruidosamente en lugar de devolver una matriz incompleta.
    """
    blanca = columnas_residuos(topo)
    faltantes = [c for c in blanca if c not in df.columns]
    if faltantes:
        raise ColumnasFaltantes(
            f"Faltan columnas de residuo para la topología {topo.nombre}: {faltantes}. "
            f"Se esperaban {len(blanca)}: {blanca}")
    X = df.loc[:, list(blanca)].copy()
    assert tuple(X.columns) == blanca, "La matriz X no respeta la lista blanca"
    return X


def objetivo(df: pd.DataFrame, columna: str = "clase_id") -> pd.Series:
    return df[columna]


def grupos(df: pd.DataFrame) -> pd.Series:
    """Identificador de condición de contorno, para particionar por grupos."""
    return df["cond_id"]
