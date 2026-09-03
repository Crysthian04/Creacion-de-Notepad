"""Pruebas de independencia entre barridos y de partición sin fuga.

Cubren dos exigencias de la especificación:
  * Sección 6.2 — el conjunto de prevalencia realista se genera con condiciones
    de contorno propias, no submuestreando el barrido de entrenamiento.
  * Sección 7.1 — ninguna condición de contorno aparece en más de una partición.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from config.params import (N_COND_ENTRENAMIENTO, SEMILLA_MAESTRA, ParametrosEquipo,
                           RangosContorno)
from src.fallas import CLASES
from src.generador import PREVALENCIA_CAMPO, muestrear_condiciones, semillas_derivadas
from src.modelo import particionar

P = ParametrosEquipo()
SEM = semillas_derivadas(SEMILLA_MAESTRA)
R = RangosContorno()


def _normalizar(df: pd.DataFrame) -> np.ndarray:
    """Condiciones a [0,1]^3 para poder medir distancias entre pools."""
    lo = np.array([R.T_amb_min, R.HR_amb_min, R.Q_load_frac_min])
    hi = np.array([R.T_amb_max, R.HR_amb_max, R.Q_load_frac_max])
    return (df[["T_amb", "HR_amb", "Q_load_frac"]].to_numpy() - lo) / (hi - lo)


def _distancia_minima(a: np.ndarray, b: np.ndarray) -> float:
    d = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(axis=2))
    return float(d.min())


# ---------------------------------------------------------------------------
# 1. Los dos barridos son independientes
# ---------------------------------------------------------------------------
def test_los_pools_no_comparten_identificadores():
    a = muestrear_condiciones(200, SEM["lhs_entrenamiento"], P, prefijo="A")
    b = muestrear_condiciones(200, SEM["lhs_prevalencia"], P, prefijo="B")
    assert set(a["cond_id"]).isdisjoint(set(b["cond_id"]))


def test_los_pools_no_comparten_ningun_punto():
    """El pool B no es un submuestreo del pool A: ningún punto se repite."""
    a = _normalizar(muestrear_condiciones(400, SEM["lhs_entrenamiento"], P, prefijo="A"))
    b = _normalizar(muestrear_condiciones(400, SEM["lhs_prevalencia"], P, prefijo="B"))
    assert _distancia_minima(a, b) > 1e-9


def test_la_prueba_de_independencia_puede_fallar():
    """Control: con la MISMA semilla los dos barridos serían idénticos.

    Sin esta comprobación, la prueba anterior podría estar pasando por
    construcción y no por independencia real.
    """
    a = _normalizar(muestrear_condiciones(120, SEM["lhs_entrenamiento"], P, prefijo="A"))
    a_repetido = _normalizar(muestrear_condiciones(120, SEM["lhs_entrenamiento"], P, prefijo="B"))
    assert _distancia_minima(a, a_repetido) < 1e-12, (
        "Reutilizar la misma semilla debería producir los mismos puntos; "
        "si no lo hace, la prueba de independencia no está midiendo lo que cree")


def test_los_barridos_cubren_el_rango_declarado():
    for flujo, prefijo in (("lhs_entrenamiento", "A"), ("lhs_prevalencia", "B")):
        c = muestrear_condiciones(300, SEM[flujo], P, prefijo=prefijo)
        assert c["T_amb"].between(R.T_amb_min, R.T_amb_max).all()
        assert c["HR_amb"].between(R.HR_amb_min, R.HR_amb_max).all()
        assert c["Q_load_frac"].between(R.Q_load_frac_min, R.Q_load_frac_max).all()
        # El hipercubo latino debe cubrir el rango, no concentrarse en el centro.
        assert c["T_amb"].min() < R.T_amb_min + 1.0
        assert c["T_amb"].max() > R.T_amb_max - 1.0


def test_muestreo_reproducible_con_la_misma_semilla():
    a1 = muestrear_condiciones(50, SEM["lhs_entrenamiento"], P, prefijo="A")
    a2 = muestrear_condiciones(50, SEM["lhs_entrenamiento"], P, prefijo="A")
    pd.testing.assert_frame_equal(a1, a2)


# ---------------------------------------------------------------------------
# 2. Partición por grupos, sin fuga de condiciones
# ---------------------------------------------------------------------------
def _dataset_sintetico(n_cond: int = 60) -> pd.DataFrame:
    """Dataset mínimo con la estructura real: 30 filas por condición."""
    rng = np.random.default_rng(7)
    filas = []
    from src.features import COLUMNAS_RESIDUOS
    for i in range(n_cond):
        for clase_id, clase in enumerate(CLASES):
            for nivel in ("incipiente", "moderada", "severa"):
                fila = {c: rng.normal() for c in COLUMNAS_RESIDUOS}
                fila.update({"clase": clase, "clase_id": clase_id,
                             "severidad_f": 0.0 if clase == "sano" else rng.uniform(0.15, 0.95),
                             "nivel": "sano" if clase == "sano" else nivel,
                             "cond_id": f"A{i:05d}"})
                filas.append(fila)
    return pd.DataFrame(filas)


def test_ninguna_condicion_aparece_en_dos_particiones():
    part = particionar(_dataset_sintetico(), SEMILLA_MAESTRA)
    tr, val, te = part.conds["train"], part.conds["val"], part.conds["test"]
    assert tr.isdisjoint(val)
    assert tr.isdisjoint(te)
    assert val.isdisjoint(te)
    assert len(tr | val | te) == 60


def test_la_particion_respeta_las_proporciones_pedidas():
    part = particionar(_dataset_sintetico(200), SEMILLA_MAESTRA)
    total = sum(len(v) for v in part.conds.values())
    assert len(part.conds["train"]) / total == pytest.approx(0.70, abs=0.03)
    assert len(part.conds["val"]) / total == pytest.approx(0.15, abs=0.03)
    assert len(part.conds["test"]) / total == pytest.approx(0.15, abs=0.03)


def test_el_balance_de_clases_sobrevive_a_la_particion():
    """El corte por condiciones preserva el balance sin estratificar a mano.

    Cada condición aporta el mismo número de filas de cada clase, así que la
    estratificación sale sola. Se verifica en lugar de suponerse.
    """
    part = particionar(_dataset_sintetico(120), SEMILLA_MAESTRA)
    for y in (part.y_tr, part.y_val):
        proporciones = y.value_counts(normalize=True)
        assert proporciones.min() == pytest.approx(0.10, abs=1e-9)
        assert proporciones.max() == pytest.approx(0.10, abs=1e-9)


def test_la_particion_es_reproducible():
    a = particionar(_dataset_sintetico(), SEMILLA_MAESTRA)
    b = particionar(_dataset_sintetico(), SEMILLA_MAESTRA)
    assert a.conds == b.conds


def test_el_conjunto_de_prueba_nace_sellado():
    part = particionar(_dataset_sintetico(), SEMILLA_MAESTRA)
    assert part.sellado.n_aperturas == 0
    part.sellado.abrir("prueba unitaria")
    assert part.sellado.n_aperturas == 1


def test_abrir_dos_veces_el_conjunto_sellado_avisa():
    part = particionar(_dataset_sintetico(), SEMILLA_MAESTRA)
    part.sellado.abrir("primera")
    with pytest.warns(UserWarning, match="NO VÁLIDA"):
        part.sellado.abrir("segunda")
    assert part.sellado.n_aperturas == 2


# ---------------------------------------------------------------------------
# 3. Prevalencia declarada
# ---------------------------------------------------------------------------
def test_la_prevalencia_declarada_suma_uno_y_cubre_las_clases():
    assert sum(PREVALENCIA_CAMPO.values()) == pytest.approx(1.0, abs=1e-12)
    assert set(PREVALENCIA_CAMPO) == set(CLASES)
    assert PREVALENCIA_CAMPO["sano"] == 0.70
