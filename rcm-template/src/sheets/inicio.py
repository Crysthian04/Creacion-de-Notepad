"""Placeholder builder for the `INICIO` cover sheet.

Phase 1 only needs a structurally valid workbook, so this builder writes the
cover heading and a note stating that the workbook is a pipeline artifact, not
a usable template yet. The real console -- role selector, stage traffic lights
and command buttons -- is built in phase 9.

User facing strings are Spanish by contract; identifiers and comments are
English.
"""

from __future__ import annotations

from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.worksheet import Worksheet

from src.sheets.base import VISIBLE, SheetSpec

SPEC = SheetSpec(key="inicio", title="INICIO", visibility=VISIBLE)

_TITLE = "Plantilla RCM2 / MSG-3"
_SUBTITLE = "Analisis RCM de una maquina individual"
_PLACEHOLDER_NOTE = (
    "Libro de verificacion del proceso de compilacion (Fase 1). "
    "Todavia no contiene hojas de analisis."
)


class InicioSheetBuilder:
    """Builds the cover sheet."""

    spec = SPEC

    def build(self, worksheet: Worksheet) -> None:
        worksheet["B2"] = _TITLE
        worksheet["B2"].font = Font(size=18, bold=True)

        worksheet["B3"] = _SUBTITLE
        worksheet["B3"].font = Font(size=11, italic=True)

        worksheet["B5"] = _PLACEHOLDER_NOTE
        worksheet["B5"].alignment = Alignment(wrap_text=True, vertical="top")

        worksheet.column_dimensions["A"].width = 3
        worksheet.column_dimensions["B"].width = 90
        worksheet.sheet_view.showGridLines = False
