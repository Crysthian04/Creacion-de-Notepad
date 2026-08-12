"""The asset identification header replicated across every working sheet.

Specification 4.4: the analyst types the identification once, in `Contexto
Operacional`, and every other working sheet shows it by formula. This module owns
both halves of that contract -- the editable original and the read-only echo --
so the two can never drift apart.
"""

from __future__ import annotations

from dataclasses import dataclass

from openpyxl.worksheet.worksheet import Worksheet

from src.common import names, styles
from src.common.layout import SheetLayout


@dataclass(frozen=True)
class HeaderField:
    key: str
    label: str
    catalog: str | None = None


# Order is the reading order of the header, not a data model.
FIELDS: tuple[HeaderField, ...] = (
    HeaderField("area_sistema", "Área / sistema"),
    HeaderField("equipo", "Equipo"),
    HeaderField("fabricante", "Fabricante"),
    HeaderField("modelo", "Modelo"),
    HeaderField("serial", "Número de serie"),
    HeaderField("numero_cmms", "Número en el CMMS"),
    HeaderField("ubicacion", "Ubicación técnica"),
    HeaderField("fecha", "Fecha del análisis"),
    HeaderField("revisor", "Revisor"),
)

# Fields echoed on every working sheet; the rest stay on the context sheet only.
ECHO_KEYS = ("area_sistema", "equipo", "numero_cmms", "ubicacion")

PREFIX = "CAB_"


def header_name(key: str) -> str:
    """Defined name of one identification field."""
    return names.range_name(PREFIX + key)


def build_master(worksheet: Worksheet, layout: SheetLayout, context) -> None:
    """Write the editable header on `Contexto Operacional` and name every cell."""
    first_row = layout.row
    label_col = layout.first_column
    value_col = label_col + 1

    entries = [(field.label, None, "") for field in FIELDS]
    region = layout.key_values(entries)

    for index, field in enumerate(FIELDS):
        row = first_row + index
        if field.key == "fecha":
            worksheet.cell(row=row, column=value_col).style = styles.INPUT_DATE
        names.define(
            context.workbook,
            header_name(field.key),
            names.cell_ref(worksheet.title, value_col, row),
        )
    assert region.last_data_row == first_row + len(FIELDS) - 1


def build_echo(worksheet: Worksheet, layout: SheetLayout) -> None:
    """Write the read-only echo of the header used by every other working sheet.

    One row, label above value, so it costs little vertical space on sheets whose
    real content is a wide table.
    """
    row = layout.row
    first_column = layout.first_column

    for offset, key in enumerate(ECHO_KEYS):
        field = next(item for item in FIELDS if item.key == key)
        label_cell = worksheet.cell(row=row, column=first_column + offset, value=field.label)
        label_cell.style = styles.LABEL
        value_cell = worksheet.cell(
            row=row + 1, column=first_column + offset, value=f"={header_name(key)}"
        )
        value_cell.style = styles.READONLY

    layout.row = row + 3
