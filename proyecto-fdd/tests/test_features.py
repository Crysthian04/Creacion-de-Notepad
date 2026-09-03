"""Pruebas de la lista blanca de características y del cálculo de residuos.

Verifican la Regla 1 de la auditoría: la matriz X se construye SELECCIONANDO las
columnas `res_*`, nunca eliminando las no deseadas.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from config.params import ParametrosEquipo
from src.calibracion import aplicar_calibracion
from src.ciclo import CondicionContorno, resolver_ciclo
from src.features import (COLUMNAS_DERIVADAS, COLUMNAS_RESIDUOS, DERIVADA_A_RESIDUO,
                          EXCLUIDAS_Y_MOTIVO, ColumnasFaltantes, calcular_residuos,
                          construir_matriz_X, derivadas_desde_medicion)

P = aplicar_calibracion(ParametrosEquipo())


def _df_con_trampas() -> pd.DataFrame:
    """DataFrame con los residuos y, además, todo lo que NO debe entrar al modelo."""
    n = 25
    rng = np.random.default_rng(0)
    datos = {c: rng.normal(size=n) for c in COLUMNAS_RESIDUOS}
    # Trampas: condiciones de contorno, mediciones crudas, identificadores y
    # —la peor— una columna derivada de la etiqueta.
    datos.update({
        "T_amb": rng.uniform(24, 36, n), "HR_amb": rng.uniform(60, 95, n),
        "T_space": np.full(n, 24.0), "Q_load_frac": rng.uniform(0.4, 1.0, n),
        "P_suc": rng.normal(130, 5, n), "P_des": rng.normal(400, 15, n),
        "clase": ["sano"] * n, "clase_id": np.zeros(n, dtype=int),
        "severidad_f": rng.uniform(0, 1, n), "nivel": ["sano"] * n,
        "cond_id": [f"A{i:05d}" for i in range(n)],
        "muestra_id": [f"m{i}" for i in range(n)],
        "fuga_artificial": np.zeros(n),  # copia directa de la etiqueta
    })
    return pd.DataFrame(datos)


def test_la_matriz_X_solo_contiene_residuos():
    X = construir_matriz_X(_df_con_trampas())
    assert tuple(X.columns) == COLUMNAS_RESIDUOS
    assert X.shape[1] == 11


def test_ninguna_columna_prohibida_entra_a_X():
    X = construir_matriz_X(_df_con_trampas())
    for prohibida in EXCLUIDAS_Y_MOTIVO:
        assert prohibida not in X.columns, (
            f"`{prohibida}` entró a la matriz de características. "
            f"Motivo por el que está excluida: {EXCLUIDAS_Y_MOTIVO[prohibida]}")
    assert "fuga_artificial" not in X.columns


def test_una_columna_nueva_no_se_cuela_sola():
    """El punto de la lista blanca: lo desconocido se queda fuera por defecto.

    Con un `drop` de columnas no deseadas, esta columna habría entrado al modelo
    sin que nadie lo notara (defecto D1/D2 de la auditoría).
    """
    df = _df_con_trampas()
    df["variable_nueva_no_prevista"] = df["severidad_f"] * 3.0
    X = construir_matriz_X(df)
    assert "variable_nueva_no_prevista" not in X.columns


def test_falla_ruidosamente_si_falta_un_residuo():
    df = _df_con_trampas().drop(columns=["res_SC"])
    with pytest.raises(ColumnasFaltantes) as exc:
        construir_matriz_X(df)
    assert "res_SC" in str(exc.value)


def test_correspondencia_derivada_residuo_es_completa():
    assert set(DERIVADA_A_RESIDUO) == set(COLUMNAS_DERIVADAS)
    assert tuple(DERIVADA_A_RESIDUO[d] for d in COLUMNAS_DERIVADAS) == COLUMNAS_RESIDUOS
    assert len(set(COLUMNAS_RESIDUOS)) == 11


def test_derivadas_solo_usan_variables_medibles_en_campo():
    """Si el cálculo necesitara algo no medible, el sistema no sería implementable."""
    cond = CondicionContorno(30.0, 80.0, 24.0, 0.85)
    estado = resolver_ciclo(cond, P)
    medible = estado.dict_medible()
    d = derivadas_desde_medicion(medible, P)          # no recibe nada más
    assert set(d) == set(COLUMNAS_DERIVADAS)
    assert all(np.isfinite(v) for v in d.values())


def test_los_residuos_de_un_estado_contra_si_mismo_son_nulos():
    cond = CondicionContorno(28.0, 75.0, 24.0, 0.70)
    d = derivadas_desde_medicion(resolver_ciclo(cond, P).dict_medible(), P)
    r = calcular_residuos(d, d)
    assert set(r) == set(COLUMNAS_RESIDUOS)
    assert all(abs(v) < 1e-12 for v in r.values())


def test_valores_derivados_son_fisicamente_razonables():
    cond = CondicionContorno(**{"T_amb": 35.0, "HR_amb": 80.0,
                                "T_space": 24.0, "Q_load_frac": 1.0})
    d = derivadas_desde_medicion(resolver_ciclo(cond, P).dict_medible(), P)
    assert 1.0 < d["SH_evap"] < 20.0
    assert 0.0 < d["SC"] < 20.0
    assert 5.0 < d["split_cond"] < 30.0
    assert d["rp"] > 1.0
    assert d["dT_air_ev"] > 0 and d["dT_air_cd"] > 0
    assert 1.0 < d["COP_sist"] < 8.0
    assert 0.5 < d["kW_TR"] < 3.0
