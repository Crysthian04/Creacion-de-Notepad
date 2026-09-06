"""Independencia entre barridos y partición sin fuga.

Cubren dos exigencias de la especificación:
  * Sección 6.2 — el conjunto de prevalencia se genera con condiciones propias.
  * Sección 7.1 — ninguna condición de contorno aparece en más de una partición.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from config.params import SEMILLA_MAESTRA, RangosContorno
from src.fallas import clases
from src.features import columnas_residuos
from src.generador import (aplicar_discrepancia, muestrear_condiciones,
                           muestrear_discrepancia, prevalencia_campo, semillas_derivadas)
from src.modelo import ConjuntoSellado, intervalo_wilson, particionar

from .conftest import TOPOLOGIAS_PROBADAS, params_de

SEM = semillas_derivadas(SEMILLA_MAESTRA)
R = RangosContorno()


def _normalizar(df: pd.DataFrame) -> np.ndarray:
    lo = np.array([R.T_amb_min, R.HR_amb_min, R.Q_load_frac_min])
    hi = np.array([R.T_amb_max, R.HR_amb_max, R.Q_load_frac_max])
    return (df[["T_amb", "HR_amb", "Q_load_frac"]].to_numpy() - lo) / (hi - lo)


def _distancia_minima(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(axis=2)).min())


# ---------------------------------------------------------------------------
# 1. Los dos barridos son independientes
# ---------------------------------------------------------------------------
def test_los_pools_no_comparten_identificadores(parametros_base):
    a = muestrear_condiciones(200, SEM["lhs_entrenamiento"], parametros_base, prefijo="A")
    b = muestrear_condiciones(200, SEM["lhs_prevalencia"], parametros_base, prefijo="B")
    assert set(a["cond_id"]).isdisjoint(set(b["cond_id"]))


def test_los_pools_no_comparten_ningun_punto(parametros_base):
    a = _normalizar(muestrear_condiciones(400, SEM["lhs_entrenamiento"], parametros_base,
                                          prefijo="A"))
    b = _normalizar(muestrear_condiciones(400, SEM["lhs_prevalencia"], parametros_base,
                                          prefijo="B"))
    assert _distancia_minima(a, b) > 1e-9


def test_la_prueba_de_independencia_puede_fallar(parametros_base):
    """Control: con la MISMA semilla los dos barridos serían idénticos."""
    a = _normalizar(muestrear_condiciones(120, SEM["lhs_entrenamiento"], parametros_base,
                                          prefijo="A"))
    a2 = _normalizar(muestrear_condiciones(120, SEM["lhs_entrenamiento"], parametros_base,
                                           prefijo="B"))
    assert _distancia_minima(a, a2) < 1e-12


def test_los_barridos_cubren_el_rango_declarado(parametros_base):
    for flujo, prefijo in (("lhs_entrenamiento", "A"), ("lhs_prevalencia", "B")):
        c = muestrear_condiciones(300, SEM[flujo], parametros_base, prefijo=prefijo)
        assert c["T_amb"].between(R.T_amb_min, R.T_amb_max).all()
        assert c["HR_amb"].between(R.HR_amb_min, R.HR_amb_max).all()
        assert c["Q_load_frac"].between(R.Q_load_frac_min, R.Q_load_frac_max).all()
        assert c["T_amb"].min() < R.T_amb_min + 1.0
        assert c["T_amb"].max() > R.T_amb_max - 1.0


def test_muestreo_reproducible_con_la_misma_semilla(parametros_base):
    a1 = muestrear_condiciones(50, SEM["lhs_entrenamiento"], parametros_base, prefijo="A")
    a2 = muestrear_condiciones(50, SEM["lhs_entrenamiento"], parametros_base, prefijo="A")
    pd.testing.assert_frame_equal(a1, a2)


# ---------------------------------------------------------------------------
# 2. Discrepancia entre modelo y planta
# ---------------------------------------------------------------------------
def test_la_discrepancia_respeta_su_cota(parametros_base):
    eps = muestrear_discrepancia(parametros_base, SEM["discrepancia"], 200, nivel=0.05,
                                 modo="por_condicion")
    assert len(eps) == 200
    for e in eps:
        assert all(abs(v) <= 0.05 + 1e-12 for v in e.values())


def test_por_corrida_da_el_mismo_error_a_todas_las_condiciones(parametros_base):
    eps = muestrear_discrepancia(parametros_base, SEM["discrepancia"], 50, nivel=0.05,
                                 modo="por_corrida")
    assert all(e == eps[0] for e in eps)
    eps_cond = muestrear_discrepancia(parametros_base, SEM["discrepancia"], 50, nivel=0.05,
                                      modo="por_condicion")
    assert not all(e == eps_cond[0] for e in eps_cond)


def test_discrepancia_cero_no_altera_los_parametros(parametros_base):
    eps = muestrear_discrepancia(parametros_base, SEM["discrepancia"], 5, nivel=0.0)
    assert aplicar_discrepancia(parametros_base, eps[0]) is parametros_base


def test_la_discrepancia_modifica_los_parametros_declarados(parametros_base):
    from config.params import parametros_con_discrepancia
    eps = muestrear_discrepancia(parametros_base, SEM["discrepancia"], 1, nivel=0.05)[0]
    p2 = aplicar_discrepancia(parametros_base, eps)
    afectados = set(parametros_con_discrepancia(parametros_base))
    for nombre in afectados:
        assert getattr(p2, nombre) != getattr(parametros_base, nombre)
    assert p2.Q_nom == parametros_base.Q_nom       # la capacidad de placa no se desvía
    assert p2.V_disp == parametros_base.V_disp


# ---------------------------------------------------------------------------
# 3. Partición por grupos, sin fuga de condiciones
# ---------------------------------------------------------------------------
def _dataset_sintetico(topo, n_cond: int = 60) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    filas = []
    for i in range(n_cond):
        for clase_id, clase in enumerate(clases(topo)):
            for nivel in ("incipiente", "moderada", "severa"):
                fila = {c: rng.normal() for c in columnas_residuos(topo)}
                fila.update({"clase": clase, "clase_id": clase_id,
                             "severidad_f": 0.0 if clase == "sano" else rng.uniform(0.15, 0.95),
                             "nivel": "sano" if clase == "sano" else nivel,
                             "cond_id": f"A{i:05d}"})
                filas.append(fila)
    return pd.DataFrame(filas)


@pytest.mark.parametrize("topo_nombre", TOPOLOGIAS_PROBADAS)
def test_ninguna_condicion_aparece_en_dos_particiones(topo_nombre):
    topo = params_de(topo_nombre).topologia
    part = particionar(_dataset_sintetico(topo), topo, SEMILLA_MAESTRA)
    tr, val, te = part.conds["train"], part.conds["val"], part.conds["test"]
    assert tr.isdisjoint(val) and tr.isdisjoint(te) and val.isdisjoint(te)
    assert len(tr | val | te) == 60


def test_la_particion_respeta_las_proporciones_pedidas(parametros_base):
    topo = parametros_base.topologia
    part = particionar(_dataset_sintetico(topo, 200), topo, SEMILLA_MAESTRA)
    total = sum(len(v) for v in part.conds.values())
    assert len(part.conds["train"]) / total == pytest.approx(0.70, abs=0.03)
    assert len(part.conds["val"]) / total == pytest.approx(0.15, abs=0.03)
    assert len(part.conds["test"]) / total == pytest.approx(0.15, abs=0.03)


def test_el_balance_de_clases_sobrevive_a_la_particion(parametros_base):
    """El corte por condiciones preserva el balance sin estratificar a mano."""
    topo = parametros_base.topologia
    part = particionar(_dataset_sintetico(topo, 120), topo, SEMILLA_MAESTRA)
    esperado = 1.0 / len(clases(topo))
    for y in (part.y_tr, part.y_val):
        proporciones = y.value_counts(normalize=True)
        assert proporciones.min() == pytest.approx(esperado, abs=1e-9)
        assert proporciones.max() == pytest.approx(esperado, abs=1e-9)


def test_la_particion_es_reproducible(parametros_base):
    topo = parametros_base.topologia
    a = particionar(_dataset_sintetico(topo), topo, SEMILLA_MAESTRA)
    b = particionar(_dataset_sintetico(topo), topo, SEMILLA_MAESTRA)
    assert a.conds == b.conds


def test_el_conjunto_de_prueba_nace_sellado(parametros_base):
    topo = parametros_base.topologia
    part = particionar(_dataset_sintetico(topo), topo, SEMILLA_MAESTRA)
    assert part.sellado.n_aperturas == 0
    part.sellado.abrir("prueba unitaria")
    assert part.sellado.n_aperturas == 1


def test_abrir_dos_veces_el_conjunto_sellado_avisa(parametros_base):
    topo = parametros_base.topologia
    part = particionar(_dataset_sintetico(topo), topo, SEMILLA_MAESTRA)
    part.sellado.abrir("primera")
    with pytest.warns(UserWarning, match="NO VÁLIDA"):
        part.sellado.abrir("segunda")
    assert part.sellado.n_aperturas == 2


# ---------------------------------------------------------------------------
# 4. Prevalencia declarada e intervalos de Wilson
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("topo_nombre", TOPOLOGIAS_PROBADAS)
def test_la_prevalencia_declarada_suma_uno_y_cubre_las_clases(topo_nombre):
    topo = params_de(topo_nombre).topologia
    prev = prevalencia_campo(topo)
    assert sum(prev.values()) == pytest.approx(1.0, abs=1e-9)
    assert set(prev) == set(clases(topo))
    assert prev["sano"] > 0.5, "la condición sana debe dominar la prevalencia de campo"


def test_intervalo_wilson_contra_valores_conocidos():
    """Con soporte pequeño el intervalo debe ser ancho; con soporte grande, estrecho."""
    lo, hi = intervalo_wilson(9, 13)          # precisión 0,69 sobre 13 casos
    assert lo < 0.45 and hi > 0.85, (lo, hi)
    assert hi - lo > 0.35, "con 13 casos el intervalo no puede ser estrecho"
    lo2, hi2 = intervalo_wilson(690, 1000)    # misma proporción, mucho más soporte
    assert hi2 - lo2 < 0.07
    assert intervalo_wilson(0, 0) != intervalo_wilson(0, 0) or True   # no lanza
    lo3, hi3 = intervalo_wilson(20, 20)
    assert hi3 == pytest.approx(1.0) and lo3 > 0.8
