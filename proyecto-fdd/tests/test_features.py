"""Pruebas de la lista blanca de características y del cálculo de residuos.

Verifican la Regla 1 de la auditoría: la matriz X se construye SELECCIONANDO las
columnas `res_*`, nunca eliminando las no deseadas. La lista blanca ahora se
deriva de la topología, pero sigue siendo lista blanca.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.ciclo import CondicionContorno, resolver_ciclo
from src.features import (EXCLUIDAS_Y_MOTIVO, ColumnasFaltantes, calcular_residuos,
                          columnas_derivadas, columnas_residuos, construir_matriz_X,
                          derivada_a_residuo, derivadas_desde_medicion)
from src.topologia import variables_medibles

from .conftest import TOPOLOGIAS_PROBADAS, params_de


def _df_con_trampas(topo, n: int = 25) -> pd.DataFrame:
    """DataFrame con los residuos y, además, todo lo que NO debe entrar al modelo."""
    rng = np.random.default_rng(0)
    datos = {c: rng.normal(size=n) for c in columnas_residuos(topo)}
    datos.update({
        "T_amb": rng.uniform(24, 36, n), "HR_amb": rng.uniform(60, 95, n),
        "Q_load_frac": rng.uniform(0.4, 1.0, n),
        "P_suc": rng.normal(40, 3, n), "P_des": rng.normal(130, 8, n),
        "clase": ["sano"] * n, "clase_id": np.zeros(n, dtype=int),
        "severidad_f": rng.uniform(0, 1, n), "nivel": ["sano"] * n,
        "cond_id": [f"A{i:05d}" for i in range(n)], "muestra_id": [f"m{i}" for i in range(n)],
        "capacidad_saturada": np.zeros(n, dtype=bool), "ciclado": np.zeros(n, dtype=bool),
        "retorno_liquido": np.zeros(n, dtype=bool),
        "desviacion_setpoint": rng.normal(0, 0.1, n), "y_capacidad": rng.uniform(0.3, 1, n),
        "fuga_artificial": np.zeros(n),   # copia directa de la etiqueta
    })
    return pd.DataFrame(datos)


@pytest.mark.parametrize("topo_nombre", TOPOLOGIAS_PROBADAS)
def test_la_matriz_X_solo_contiene_residuos(topo_nombre):
    topo = params_de(topo_nombre).topologia
    X = construir_matriz_X(_df_con_trampas(topo), topo)
    assert tuple(X.columns) == columnas_residuos(topo)
    assert X.shape[1] == len(columnas_residuos(topo))


@pytest.mark.parametrize("topo_nombre", TOPOLOGIAS_PROBADAS)
def test_ninguna_columna_prohibida_entra_a_X(topo_nombre):
    topo = params_de(topo_nombre).topologia
    X = construir_matriz_X(_df_con_trampas(topo), topo)
    for prohibida in EXCLUIDAS_Y_MOTIVO:
        assert prohibida not in X.columns, (
            f"`{prohibida}` entró a la matriz de características. "
            f"Motivo declarado de su exclusión: {EXCLUIDAS_Y_MOTIVO[prohibida]}")
    assert "fuga_artificial" not in X.columns


@pytest.mark.parametrize("topo_nombre", TOPOLOGIAS_PROBADAS)
def test_las_banderas_del_control_no_entran_al_modelo(topo_nombre):
    """`capacidad_saturada` y `ciclado` correlacionan con la severidad.

    Son metadatos valiosos para el análisis y fuga si se usan para entrenar.
    """
    topo = params_de(topo_nombre).topologia
    X = construir_matriz_X(_df_con_trampas(topo), topo)
    for bandera in ("capacidad_saturada", "ciclado", "retorno_liquido",
                    "desviacion_setpoint", "y_capacidad"):
        assert bandera not in X.columns
        assert bandera in EXCLUIDAS_Y_MOTIVO


def test_una_columna_nueva_no_se_cuela_sola():
    """El punto de la lista blanca: lo desconocido se queda fuera por defecto."""
    topo = params_de("chiller_cond_aire").topologia
    df = _df_con_trampas(topo)
    df["variable_nueva_no_prevista"] = df["severidad_f"] * 3.0
    assert "variable_nueva_no_prevista" not in construir_matriz_X(df, topo).columns


def test_falla_ruidosamente_si_falta_un_residuo():
    topo = params_de("chiller_cond_aire").topologia
    df = _df_con_trampas(topo).drop(columns=["res_SC"])
    with pytest.raises(ColumnasFaltantes) as exc:
        construir_matriz_X(df, topo)
    assert "res_SC" in str(exc.value)


@pytest.mark.parametrize("topo_nombre", TOPOLOGIAS_PROBADAS)
def test_correspondencia_derivada_residuo_es_completa(topo_nombre):
    topo = params_de(topo_nombre).topologia
    mapa = derivada_a_residuo(topo)
    assert set(mapa) == set(columnas_derivadas(topo))
    assert tuple(mapa[d] for d in columnas_derivadas(topo)) == columnas_residuos(topo)
    assert len(set(columnas_residuos(topo))) == len(columnas_residuos(topo))


@pytest.mark.parametrize("topo_nombre", TOPOLOGIAS_PROBADAS)
def test_derivadas_solo_usan_variables_medibles_en_campo(topo_nombre):
    """Si el cálculo necesitara algo no medible, el sistema no sería implementable."""
    p = params_de(topo_nombre)
    estado = resolver_ciclo(CondicionContorno(30.0, 80.0, 0.85), p)
    assert estado.convergio
    medible = estado.dict_medible()
    assert set(medible) == set(variables_medibles(p.topologia))
    d = derivadas_desde_medicion(medible, p)
    assert set(d) == set(columnas_derivadas(p.topologia))
    assert all(np.isfinite(v) for v in d.values())


@pytest.mark.parametrize("topo_nombre", TOPOLOGIAS_PROBADAS)
def test_los_residuos_de_un_estado_contra_si_mismo_son_nulos(topo_nombre):
    p = params_de(topo_nombre)
    d = derivadas_desde_medicion(
        resolver_ciclo(CondicionContorno(28.0, 75.0, 0.70), p).dict_medible(), p)
    r = calcular_residuos(d, d, p.topologia)
    assert set(r) == set(columnas_residuos(p.topologia))
    assert all(abs(v) < 1e-12 for v in r.values())


def test_valores_derivados_del_chiller_son_fisicamente_razonables():
    p = params_de("chiller_cond_aire")
    d = derivadas_desde_medicion(
        resolver_ciclo(CondicionContorno(35.0, 80.0, 1.0), p).dict_medible(), p)
    assert 1.0 < d["SH_evap"] < 20.0
    assert 0.0 < d["SC"] < 20.0
    assert 5.0 < d["split_cond"] < 30.0
    assert 0.0 < d["approach_ev"] < 12.0
    assert d["rp"] > 1.0
    assert 3.0 < d["dT_agua_ev"] < 8.0        # salto nominal del agua helada
    assert d["dT_air_cd"] > 0
    assert 1.5 < d["COP_sist"] < 8.0
    assert 0.4 < d["kW_TR"] < 2.5
