"""Hidden seed libraries: `Lib_Particiones`, `Lib_ModosFalla`, `Lib_Tareas`.

These are read-only reference data structured against ISO 14224. `modLibrary`
filters them by taxonomy code and inserts the chosen rows into the working
sheets; the analyst never edits them directly, which is why they are very hidden.

The taxonomy itself lives in a fourth library sheet, because the partition sheet
validates its codes against it.

The seeded content is a starter set covering pumps, electric motors, valves and
screw compressors. The team extends it by editing `seed/` and rebuilding -- never
by typing into the workbook, which the next build would overwrite.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from openpyxl.worksheet.worksheet import Worksheet

from src.common import names, styles
from src.common.layout import Column, SheetLayout
from src.sheets.base import VERY_HIDDEN, BuildContext, SheetSpec


@dataclass(frozen=True)
class _LibrarySheet:
    """A library sheet described entirely by data."""

    spec: SheetSpec
    title: str
    subtitle: str
    columns: list[Column]
    range_key: str
    source: str

    def rows(self, context: BuildContext) -> list[dict[str, Any]]:
        return [dict(row) for row in getattr(context.seed, self.source)]


_CODE = styles.CODE
_READ = styles.READONLY

TAXONOMIA = _LibrarySheet(
    spec=SheetSpec(
        key="lib_taxonomia", title="Lib_Taxonomia", visibility=VERY_HIDDEN, role="APROBADOR"
    ),
    title="Taxonomía ISO 14224",
    subtitle="Clase de equipo (nivel 1) → subunidad (nivel 2) → ítem mantenible (nivel 3).",
    columns=[
        Column("nivel", "Nivel", 8, _CODE),
        Column("codigo", "Código", 18, _CODE),
        Column("codigo_padre", "Código padre", 18, _CODE),
        Column("etiqueta", "Descripción", 46, _READ),
        Column("notas", "Notas", 36, _READ),
    ],
    range_key="Taxonomia",
    source="taxonomia",
)

PARTICIONES = _LibrarySheet(
    spec=SheetSpec(
        key="lib_particiones", title="Lib_Particiones", visibility=VERY_HIDDEN, role="APROBADOR"
    ),
    title="Librería de particiones",
    subtitle="Plantillas de desglose por tipo de máquina, insertables desde la hoja Particion.",
    columns=[
        Column("plantilla", "Plantilla", 26, _CODE),
        Column("orden", "Orden", 8, _CODE),
        Column("nivel", "Nivel", 8, _CODE),
        Column("codigo_taxonomia", "Código ISO 14224", 20, _CODE),
        Column("descripcion", "Descripción", 46, _READ),
    ],
    range_key="LibParticiones",
    source="lib_particiones",
)

MODOS_FALLA = _LibrarySheet(
    spec=SheetSpec(
        key="lib_modos_falla", title="Lib_ModosFalla", visibility=VERY_HIDDEN, role="APROBADOR"
    ),
    title="Librería de modos de falla",
    subtitle=(
        "Modos genéricos por ítem de taxonomía, con las respuestas de consecuencia "
        "que alimentan el árbol de decisión."
    ),
    columns=[
        Column("codigo_taxonomia", "Código ISO 14224", 20, _CODE),
        Column("codigo_modo_iso", "Modo ISO 14224", 14, _CODE),
        Column("funcion", "Función", 46, _READ),
        Column("falla_funcional", "Falla funcional", 40, _READ),
        Column("modo_falla", "Modo de falla", 40, _READ),
        Column("causa", "Causa", 40, _READ),
        Column("efecto", "Efecto", 52, _READ),
        Column("evidente", "¿Evidente?", 12, _CODE),
        Column("seguridad", "¿Seguridad?", 12, _CODE),
        Column("ambiental", "¿Ambiental?", 12, _CODE),
        Column("operacional", "¿Operacional?", 12, _CODE),
    ],
    range_key="LibModosFalla",
    source="lib_modos",
)

TAREAS = _LibrarySheet(
    spec=SheetSpec(key="lib_tareas", title="Lib_Tareas", visibility=VERY_HIDDEN, role="APROBADOR"),
    title="Librería de tareas",
    subtitle="Tareas tipo por modo de falla, con oficio, frecuencia y duración de referencia.",
    columns=[
        Column("codigo_taxonomia", "Código ISO 14224", 20, _CODE),
        Column("codigo_modo_iso", "Modo ISO 14224", 14, _CODE),
        Column("tipo_tarea", "Tipo de tarea", 14, _CODE),
        Column("descripcion_tarea", "Descripción de la tarea", 70, _READ),
        Column("oficio", "Oficio", 12, _CODE),
        Column("cantidad_personas", "Personas", 10, _CODE),
        Column("frecuencia_valor", "Frecuencia", 12, _CODE),
        Column("frecuencia_unidad", "Unidad", 10, _CODE),
        Column("base_frecuencia", "Base", 14, _CODE),
        Column("duracion_valor", "Duración", 10, _CODE),
        Column("duracion_unidad", "Unidad", 10, _CODE),
        Column("estado_equipo", "Estado del equipo", 16, _CODE),
        Column("requiere_permiso", "Permiso", 14, _CODE),
        Column("codigo_actividad", "Código de actividad", 16, _CODE),
    ],
    range_key="LibTareas",
    source="lib_tareas",
)

LIBRARIES = (TAXONOMIA, PARTICIONES, MODOS_FALLA, TAREAS)


class LibrarySheetBuilder:
    """Builds one library sheet from its declarative description."""

    def __init__(self, library: _LibrarySheet) -> None:
        self._library = library
        self.spec = library.spec

    def build(self, worksheet: Worksheet, context: BuildContext) -> None:
        library = self._library
        layout = SheetLayout(worksheet, first_column=2)
        layout.title(library.title, library.subtitle)

        region = layout.table(library.columns, library.rows(context), autofilter=True, freeze=True)

        names.define(
            context.workbook,
            names.library_name(library.range_key),
            names.range_ref(
                library.spec.title,
                region.first_column,
                region.first_data_row,
                region.last_column,
                region.last_data_row,
            ),
        )
        # The first column doubles as the lookup key of every library, so it gets
        # its own name for the filtering form of `modLibrary`.
        names.define(
            context.workbook,
            names.library_name(library.range_key + "Clave"),
            names.range_ref(
                library.spec.title,
                region.first_column,
                region.first_data_row,
                region.first_column,
                region.last_data_row,
            ),
        )


def library_builders() -> list[LibrarySheetBuilder]:
    return [LibrarySheetBuilder(library) for library in LIBRARIES]
