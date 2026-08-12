"""Tests of the seed datasets and their loader.

The seed is the source of truth for every business constant, so a malformed or
internally inconsistent seed must fail here rather than in a delivered workbook.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.seedloader import SeedError, is_true, load_seed, read_csv


@pytest.fixture(scope="module")
def seed():
    root = Path(__file__).resolve().parents[1] / "seed"
    return load_seed(root)


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------


def test_seed_loads_without_error(seed):
    assert seed.catalogos
    assert seed.parametros
    assert seed.taxonomia


def test_catalogues_are_grouped_and_ordered(seed):
    oficios = seed.catalogo("OFICIO")
    assert [row["codigo"] for row in oficios][0] == "MEC"
    assert all(is_true(row["activo"]) for row in oficios)


def test_every_catalogue_referenced_by_a_parameter_exists(seed):
    for row in seed.parametros:
        if row["catalogo"]:
            assert row["catalogo"] in seed.catalogos_por_nombre


def test_taxonomy_levels_are_consistent(seed):
    by_code = seed.taxonomia_por_codigo
    for row in seed.taxonomia:
        level = int(row["nivel"])
        parent = row["codigo_padre"]
        if level == 1:
            assert parent == "", row["codigo"]
        else:
            assert parent, row["codigo"]
            assert int(by_code[parent]["nivel"]) == level - 1, row["codigo"]


def test_library_rows_reference_existing_taxonomy_codes(seed):
    known = set(seed.taxonomia_por_codigo)
    for dataset in (seed.lib_particiones, seed.lib_modos, seed.lib_tareas):
        for row in dataset:
            assert row["codigo_taxonomia"] in known


def test_task_library_only_uses_declared_task_types(seed):
    declared = {row["codigo"] for row in seed.tipos_tarea}
    for row in seed.lib_tareas:
        assert row["tipo_tarea"] in declared


# Task types that constitute a proactive answer to a failure mode. `OF` and `RD`
# are answers too, but not ones a seeded library should ever ship as a default.
PROACTIVE_TASK_TYPES = frozenset(
    {"VO", "IVF", "IO", "RE", "DS", "LI", "LB", "SE"}
    | {"CBM-TER", "CBM-VIB", "CBM-US", "CBM-AL", "CBM-ACM", "CBM-AMV"}
)


def test_hidden_failure_modes_with_safety_consequence_are_treated(seed):
    """A hidden failure that can hurt someone must carry a proactive task.

    RCM2 allows any of on-condition, restoration, discard or failure-finding
    here -- failure-finding is the last resort, not the only answer -- so the
    check is that *some* proactive task exists, not that it is a `VO`. Shipping a
    library where such a mode has no task at all would teach the wrong method.
    """
    hidden_unsafe = {
        (row["codigo_taxonomia"], row["codigo_modo_iso"])
        for row in seed.lib_modos
        if row["evidente"] == "N" and row["seguridad"] == "S"
    }
    treated = {
        (row["codigo_taxonomia"], row["codigo_modo_iso"])
        for row in seed.lib_tareas
        if row["tipo_tarea"] in PROACTIVE_TASK_TYPES
    }
    assert hidden_unsafe <= treated, sorted(hidden_unsafe - treated)


def test_every_seeded_failure_mode_has_at_least_one_task(seed):
    modes = {(row["codigo_taxonomia"], row["codigo_modo_iso"]) for row in seed.lib_modos}
    with_task = {(row["codigo_taxonomia"], row["codigo_modo_iso"]) for row in seed.lib_tareas}
    assert modes <= with_task, sorted(modes - with_task)


def test_task_types_declare_a_usable_frequency_range(seed):
    for row in seed.tipos_tarea:
        minimum = int(row["frecuencia_min_dias"])
        maximum = int(row["frecuencia_max_dias"])
        assert minimum <= maximum, row["codigo"]
        if row["requiere_intervalo"] == "S":
            assert maximum > 0, row["codigo"]


def test_criticality_weights_sum_to_one(seed):
    weights = [
        float(row["valor"])
        for row in seed.parametros
        if row["bloque"] == "CRITICIDAD_PESOS" and row["clave"].startswith("peso_")
    ]
    assert len(weights) == 4
    assert abs(sum(weights) - 1.0) < 1e-9


def test_criticality_thresholds_descend(seed):
    values = {
        row["clave"]: float(row["valor"])
        for row in seed.parametros
        if row["bloque"] == "CRITICIDAD_UMBRALES"
    }
    assert values["umbral_clase_a"] > values["umbral_clase_b"] > values["umbral_clase_c"] > 0


# --------------------------------------------------------------------------
# Failure handling
# --------------------------------------------------------------------------


def test_missing_file_is_reported(tmp_path: Path):
    with pytest.raises(SeedError, match="not found"):
        load_seed(tmp_path / "nope")


def test_missing_column_is_reported(tmp_path: Path):
    path = tmp_path / "catalogos.csv"
    path.write_text("catalogo,codigo\nOFICIO,MEC\n", encoding="utf-8")
    with pytest.raises(SeedError, match="missing column"):
        read_csv(path, ("catalogo", "codigo", "etiqueta"))


def test_short_row_is_reported(tmp_path: Path):
    path = tmp_path / "corta.csv"
    path.write_text("a,b,c\n1,2\n", encoding="utf-8")
    with pytest.raises(SeedError, match="shorter"):
        read_csv(path)


def test_long_row_is_reported(tmp_path: Path):
    path = tmp_path / "larga.csv"
    path.write_text("a,b\n1,2,3\n", encoding="utf-8")
    with pytest.raises(SeedError, match="longer"):
        read_csv(path)


def test_unknown_catalogue_is_reported(seed):
    with pytest.raises(SeedError, match="Unknown catalogue"):
        seed.catalogo("NO_EXISTE")
