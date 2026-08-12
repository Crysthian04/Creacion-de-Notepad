"""Reading of the `seed/` datasets.

Seed files are the source of truth for every business constant. They are read
once per build into plain dictionaries, validated for the columns each consumer
needs, and handed to the sheet builders.

Validation is deliberately strict: a missing column or an unknown catalogue
reference must break the build, not produce a workbook with silent gaps.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

TRUE_VALUES = {"S", "SI", "SÍ", "Y", "YES", "1", "TRUE"}

# Seed file names, so a rename happens in one place.
FILE_CATALOGOS = "catalogos.csv"
FILE_PARAMETROS = "parametros.csv"
FILE_TIPOS_TAREA = "tipos_tarea.csv"
FILE_DICCIONARIO = "diccionario_etiquetas.csv"
FILE_TAXONOMIA = "taxonomia_iso14224.csv"
FILE_LIB_PARTICIONES = "lib_particiones.csv"
FILE_LIB_MODOS = "lib_modos_falla.csv"
FILE_LIB_TAREAS = "lib_tareas.csv"

Row = dict[str, str]


class SeedError(ValueError):
    """Raised when a seed file is missing, malformed or internally inconsistent."""


def read_csv(path: Path, required_columns: tuple[str, ...] = ()) -> list[Row]:
    """Read a UTF-8 CSV into a list of dictionaries, stripping whitespace."""
    if not path.is_file():
        raise SeedError(f"Seed file not found: {path}")

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise SeedError(f"Seed file has no header row: {path}")

        columns = tuple(name.strip() for name in reader.fieldnames)
        missing = [name for name in required_columns if name not in columns]
        if missing:
            raise SeedError(f"Seed file {path.name} is missing column(s): {', '.join(missing)}")

        rows: list[Row] = []
        for number, raw in enumerate(reader, start=2):
            # DictReader pads a short row with None values and collects the
            # surplus of a long row under the None key.
            if None in raw:
                raise SeedError(f"{path.name} line {number}: row is longer than the header.")
            if any(value is None for value in raw.values()):
                raise SeedError(f"{path.name} line {number}: row is shorter than the header.")
            row = {key.strip(): (value or "").strip() for key, value in raw.items()}
            if not any(row.values()):
                continue  # tolerate blank separator lines
            rows.append(row)
    return rows


def is_true(value: str) -> bool:
    return value.strip().upper() in TRUE_VALUES


@dataclass(frozen=True)
class SeedData:
    """Every seed dataset, loaded and cross validated."""

    root: Path
    catalogos: list[Row]
    parametros: list[Row]
    tipos_tarea: list[Row]
    diccionario: list[Row]
    taxonomia: list[Row]
    lib_particiones: list[Row]
    lib_modos: list[Row]
    lib_tareas: list[Row]

    @cached_property
    def catalogos_por_nombre(self) -> dict[str, list[Row]]:
        """Active catalogue entries grouped by catalogue name, in `orden` order."""
        grouped: dict[str, list[Row]] = defaultdict(list)
        for row in self.catalogos:
            if is_true(row["activo"]):
                grouped[row["catalogo"]].append(row)
        for entries in grouped.values():
            entries.sort(key=lambda item: (_as_int(item["orden"]), item["codigo"]))
        return dict(grouped)

    @cached_property
    def parametros_por_bloque(self) -> dict[str, list[Row]]:
        """Parameters grouped by block, preserving file order within a block."""
        grouped: dict[str, list[Row]] = defaultdict(list)
        for row in self.parametros:
            grouped[row["bloque"]].append(row)
        return dict(grouped)

    @cached_property
    def taxonomia_por_codigo(self) -> dict[str, Row]:
        return {row["codigo"]: row for row in self.taxonomia}

    def catalogo(self, nombre: str) -> list[Row]:
        try:
            return self.catalogos_por_nombre[nombre]
        except KeyError:
            raise SeedError(f"Unknown catalogue '{nombre}'.") from None

    def codigos(self, catalogo: str) -> list[str]:
        return [row["codigo"] for row in self.catalogo(catalogo)]


def load_seed(root: Path) -> SeedData:
    """Load every seed file under `root` and cross validate the datasets."""
    if not root.is_dir():
        raise SeedError(f"Seed directory not found: {root}")

    data = SeedData(
        root=root,
        catalogos=read_csv(
            root / FILE_CATALOGOS, ("catalogo", "codigo", "etiqueta", "orden", "activo")
        ),
        parametros=read_csv(
            root / FILE_PARAMETROS,
            ("bloque", "clave", "etiqueta", "valor", "tipo", "catalogo", "notas"),
        ),
        tipos_tarea=read_csv(
            root / FILE_TIPOS_TAREA,
            (
                "codigo",
                "etiqueta",
                "categoria_msg3",
                "requiere_intervalo",
                "requiere_justificacion",
                "frecuencia_min_dias",
                "frecuencia_max_dias",
                "activo",
            ),
        ),
        diccionario=read_csv(root / FILE_DICCIONARIO, ("clave", "es", "en")),
        taxonomia=read_csv(root / FILE_TAXONOMIA, ("nivel", "codigo", "codigo_padre", "etiqueta")),
        lib_particiones=read_csv(
            root / FILE_LIB_PARTICIONES,
            ("plantilla", "orden", "nivel", "codigo_taxonomia", "descripcion"),
        ),
        lib_modos=read_csv(
            root / FILE_LIB_MODOS,
            (
                "codigo_taxonomia",
                "codigo_modo_iso",
                "funcion",
                "falla_funcional",
                "modo_falla",
                "causa",
                "efecto",
                "evidente",
                "seguridad",
                "ambiental",
                "operacional",
            ),
        ),
        lib_tareas=read_csv(
            root / FILE_LIB_TAREAS,
            (
                "codigo_taxonomia",
                "codigo_modo_iso",
                "tipo_tarea",
                "descripcion_tarea",
                "oficio",
                "frecuencia_valor",
                "frecuencia_unidad",
                "base_frecuencia",
                "duracion_valor",
                "duracion_unidad",
                "estado_equipo",
                "requiere_permiso",
                "codigo_actividad",
            ),
        ),
    )
    _validate(data)
    return data


def _validate(data: SeedData) -> None:
    """Cross file consistency checks."""
    _validate_unique(data.catalogos, ("catalogo", "codigo"), FILE_CATALOGOS)
    _validate_unique(data.parametros, ("clave",), FILE_PARAMETROS)
    _validate_unique(data.tipos_tarea, ("codigo",), FILE_TIPOS_TAREA)
    _validate_unique(data.diccionario, ("clave",), FILE_DICCIONARIO)
    _validate_unique(data.taxonomia, ("codigo",), FILE_TAXONOMIA)

    known_codes = set(data.taxonomia_por_codigo)
    for row in data.taxonomia:
        parent = row["codigo_padre"]
        if parent and parent not in known_codes:
            raise SeedError(
                f"{FILE_TAXONOMIA}: '{row['codigo']}' references unknown parent '{parent}'."
            )

    _validate_references(
        data.lib_particiones, "codigo_taxonomia", known_codes, FILE_LIB_PARTICIONES
    )
    _validate_references(data.lib_modos, "codigo_taxonomia", known_codes, FILE_LIB_MODOS)
    _validate_references(data.lib_tareas, "codigo_taxonomia", known_codes, FILE_LIB_TAREAS)

    task_types = {row["codigo"] for row in data.tipos_tarea}
    _validate_references(data.lib_tareas, "tipo_tarea", task_types, FILE_LIB_TAREAS)

    # Catalogue driven columns of the task library.
    for column, catalogue in (
        ("oficio", "OFICIO"),
        ("frecuencia_unidad", "FRECUENCIA_UNIDAD"),
        ("base_frecuencia", "BASE_FRECUENCIA"),
        ("duracion_unidad", "DURACION_UNIDAD"),
        ("estado_equipo", "ESTADO_EQUIPO"),
        ("requiere_permiso", "PERMISO"),
        ("codigo_actividad", "CODIGO_ACTIVIDAD"),
    ):
        _validate_references(data.lib_tareas, column, set(data.codigos(catalogue)), FILE_LIB_TAREAS)

    # Every parameter that declares a catalogue must reference an existing one.
    for row in data.parametros:
        catalogue = row["catalogo"]
        if catalogue and catalogue not in data.catalogos_por_nombre:
            raise SeedError(
                f"{FILE_PARAMETROS}: parameter '{row['clave']}' references unknown "
                f"catalogue '{catalogue}'."
            )

    for row in data.tipos_tarea:
        if row["categoria_msg3"] not in set(data.codigos("CATEGORIA_MSG3")):
            raise SeedError(
                f"{FILE_TIPOS_TAREA}: task type '{row['codigo']}' references unknown "
                f"MSG-3 category '{row['categoria_msg3']}'."
            )


def _validate_unique(rows: list[Row], keys: tuple[str, ...], file_name: str) -> None:
    seen: set[tuple[str, ...]] = set()
    for row in rows:
        key = tuple(row[name] for name in keys)
        if key in seen:
            raise SeedError(f"{file_name}: duplicate entry for {'/'.join(key)}.")
        seen.add(key)


def _validate_references(rows: list[Row], column: str, allowed: set[str], file_name: str) -> None:
    for row in rows:
        value = row.get(column, "")
        if value and value not in allowed:
            raise SeedError(f"{file_name}: unknown value '{value}' in column '{column}'.")


def _as_int(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
