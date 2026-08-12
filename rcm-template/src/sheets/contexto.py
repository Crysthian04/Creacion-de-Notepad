"""`Contexto Operacional`: what the machine is and the conditions it works in.

RCM2 starts here. Everything downstream -- the functions in the FMEA, the
performance standards a failure is measured against, the consequence answers --
depends on the operating context being written down first, so this sheet is the
first visible working sheet and the only place the identification is typed.
"""

from __future__ import annotations

from openpyxl.worksheet.worksheet import Worksheet

from src.common import header, names, styles
from src.common.layout import Column, SheetLayout, add_list_validation
from src.sheets.base import VISIBLE, BuildContext, SheetSpec

SPEC = SheetSpec(key="contexto", title="Contexto Operacional", visibility=VISIBLE, role="ANALISTA")

_FUNCTION_ROWS = 6
_STANDARD_ROWS = 10
_FLOW_ROWS = 10

_CONDITION_FIELDS = (
    ("regimen", "Régimen de operación", "REGIMEN_OPERACION"),
    ("turnos", "Turnos por día", None),
    ("horas_dia", "Horas de operación al día", None),
    ("dias_anio", "Días de operación al año", None),
    ("ambiente", "Ambiente predominante", "AMBIENTE"),
    ("redundancia", "Redundancia", "REDUNDANCIA"),
    ("temperatura", "Rango de temperatura ambiente (°C)", None),
    ("accesibilidad", "Accesibilidad para mantenimiento", None),
)


class ContextoSheetBuilder:
    """Builds the operating context sheet."""

    spec = SPEC

    def build(self, worksheet: Worksheet, context: BuildContext) -> None:
        layout = SheetLayout(worksheet, first_column=2)
        layout.title(
            "Contexto operacional",
            "Se completa antes que cualquier otra hoja. El resto del libro lo hereda.",
        )

        layout.section("Identificación del activo", width=3)
        header.build_master(worksheet, layout, context)

        self._conditions(worksheet, layout, context)
        self._function_statement(layout)
        self._performance_standards(worksheet, layout, context)
        self._flows(worksheet, layout, context)

        worksheet.column_dimensions["A"].width = 3

    def _conditions(self, worksheet: Worksheet, layout: SheetLayout, context: BuildContext) -> None:
        layout.section("Condiciones de operación", width=3)
        first_row = layout.row
        value_col = layout.first_column + 1

        layout.key_values([(label, None, "") for _, label, _ in _CONDITION_FIELDS])

        for index, (key, _, catalog) in enumerate(_CONDITION_FIELDS):
            row = first_row + index
            if catalog:
                add_list_validation(
                    worksheet, names.catalog_name(catalog), row, row, value_col, allow_blank=True
                )
            names.define(
                context.workbook,
                names.range_name("CTX_" + key),
                names.cell_ref(self.spec.title, value_col, row),
            )

    def _function_statement(self, layout: SheetLayout) -> None:
        layout.section("Declaración de funcionamiento", width=3)
        layout.note(
            "Qué hace la máquina, para quién, y bajo qué restricciones. "
            "Redactar en prosa; es el marco de todo el análisis."
        )
        layout.table(
            [Column("texto", "Declaración", 120, styles.INPUT_TEXT)],
            [],
            blank_rows=_FUNCTION_ROWS,
        )

    def _performance_standards(
        self, worksheet: Worksheet, layout: SheetLayout, context: BuildContext
    ) -> None:
        layout.section("Estándares de desempeño", width=5)
        layout.note(
            "El estándar es el umbral contra el que se declara una falla funcional. "
            "Sin valor y unidad, la falla funcional no es verificable."
        )
        region = layout.table(
            [
                Column("variable", "Variable", 34, styles.INPUT_TEXT),
                Column("valor_nominal", "Valor nominal", 18, styles.INPUT_DECIMAL),
                Column("limite_inferior", "Límite inferior", 18, styles.INPUT_DECIMAL),
                Column("limite_superior", "Límite superior", 18, styles.INPUT_DECIMAL),
                Column("unidad", "Unidad", 14, styles.INPUT_TEXT),
                Column("fuente", "Fuente del estándar", 40, styles.INPUT_TEXT),
            ],
            [],
            blank_rows=_STANDARD_ROWS,
            freeze=False,
        )
        names.define(
            context.workbook,
            names.range_name("Estandares"),
            names.range_ref(
                self.spec.title,
                region.first_column,
                region.first_data_row,
                region.last_column,
                region.last_data_row,
            ),
        )

    def _flows(self, worksheet: Worksheet, layout: SheetLayout, context: BuildContext) -> None:
        layout.section("Insumos y productos", width=4)
        region = layout.table(
            [
                Column("tipo", "Tipo", 16, styles.INPUT_TEXT),
                Column("descripcion", "Descripción", 46, styles.INPUT_TEXT),
                Column("especificacion", "Especificación", 34, styles.INPUT_TEXT),
                Column("origen_destino", "Origen / destino", 30, styles.INPUT_TEXT),
            ],
            [{"tipo": "INSUMO"}, {"tipo": "PRODUCTO"}],
            blank_rows=_FLOW_ROWS,
        )
        names.define(
            context.workbook,
            names.range_name("Flujos"),
            names.range_ref(
                self.spec.title,
                region.first_column,
                region.first_data_row,
                region.last_column,
                region.last_data_row,
            ),
        )
