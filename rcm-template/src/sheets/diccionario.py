"""`Diccionario`: the label translation table.

Three columns -- `clave`, `es`, `en`. Every caption the workbook displays comes
from a key in this sheet, so translating the template means filling in the `en`
column and switching one parameter. No logic is touched.

The sheet is very hidden: it is infrastructure, not content.
"""

from __future__ import annotations

from openpyxl.worksheet.worksheet import Worksheet

from src.common import names, styles
from src.common.layout import Column, SheetLayout
from src.sheets.base import VERY_HIDDEN, BuildContext, SheetSpec

SPEC = SheetSpec(key="diccionario", title="Diccionario", visibility=VERY_HIDDEN, role="APROBADOR")

# Room for keys added by hand between builds.
SPARE_ROWS = 40


class DiccionarioSheetBuilder:
    """Builds the label dictionary."""

    spec = SPEC

    def build(self, worksheet: Worksheet, context: BuildContext) -> None:
        layout = SheetLayout(worksheet, first_column=2)
        layout.title(
            "Diccionario de etiquetas",
            "Traducir el libro = completar la columna 'en'. No se toca ninguna fórmula.",
        )

        columns = [
            Column("clave", "Clave", 34, styles.CODE),
            Column("es", "Español", 60, styles.READONLY),
            Column("en", "English", 60, styles.INPUT_TEXT),
        ]
        rows = [dict(row) for row in context.seed.diccionario]
        region = layout.table(columns, rows, blank_rows=SPARE_ROWS, autofilter=True, freeze=True)

        names.define(
            context.workbook,
            names.range_name("Diccionario"),
            names.range_ref(
                self.spec.title,
                region.first_column,
                region.first_data_row,
                region.last_column,
                region.last_data_row,
            ),
        )
        names.define(
            context.workbook,
            names.range_name("DiccionarioClaves"),
            names.range_ref(
                self.spec.title,
                region.first_column,
                region.first_data_row,
                region.first_column,
                region.last_data_row,
            ),
        )
