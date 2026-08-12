"""Named styles shared by every sheet.

Styles are registered once per workbook and referenced by name, so the file
stays small and a palette change happens in exactly one place.

The visual grammar the analyst learns to read:

  amber cell  -> you may type here
  grey cell   -> calculated or inherited; do not type
  dark header -> column heading
  light band  -> section heading
"""

from __future__ import annotations

from openpyxl.styles import Alignment, Border, Font, NamedStyle, PatternFill, Side
from openpyxl.workbook.workbook import Workbook

# Palette.
INK = "1F2933"
ACCENT = "1F3B54"
ACCENT_LIGHT = "DCE6EF"
INPUT_BG = "FFF8E1"
READONLY_BG = "F1F3F5"
BORDER = "B8C2CC"
MUTED = "6B7681"
WHITE = "FFFFFF"

# Criticality class colours, indexed by the CLASE_CRITICIDAD catalogue code.
CRITICALITY_FILLS = {
    "A": "E06B5B",
    "B": "E8A33D",
    "C": "F2D06B",
    "D": "9FC4A0",
}

# Style names.
TITLE = "rcm_title"
SUBTITLE = "rcm_subtitle"
SECTION = "rcm_section"
HEADER = "rcm_header"
INPUT_TEXT = "rcm_input_text"
INPUT_NUMBER = "rcm_input_number"
INPUT_DECIMAL = "rcm_input_decimal"
INPUT_DATE = "rcm_input_date"
READONLY = "rcm_readonly"
READONLY_NUMBER = "rcm_readonly_number"
LABEL = "rcm_label"
NOTE = "rcm_note"
CODE = "rcm_code"

_FONT = "Calibri"
_THIN = Side(style="thin", color=BORDER)
_BOX = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)


def _style(
    name: str,
    *,
    size: int = 10,
    bold: bool = False,
    italic: bool = False,
    color: str = INK,
    fill: str | None = None,
    horizontal: str = "left",
    vertical: str = "center",
    wrap: bool = False,
    border: bool = True,
    locked: bool = True,
    number_format: str | None = None,
) -> NamedStyle:
    from openpyxl.styles import Protection

    style = NamedStyle(name=name)
    style.font = Font(name=_FONT, size=size, bold=bold, italic=italic, color=color)
    style.alignment = Alignment(horizontal=horizontal, vertical=vertical, wrap_text=wrap)
    style.protection = Protection(locked=locked)
    if fill:
        style.fill = PatternFill("solid", fgColor=fill)
    if border:
        style.border = _BOX
    if number_format:
        style.number_format = number_format
    return style


def build_styles() -> list[NamedStyle]:
    """Every named style, built fresh (NamedStyle objects bind to one workbook)."""
    return [
        _style(TITLE, size=18, bold=True, color=ACCENT, border=False),
        _style(SUBTITLE, size=11, italic=True, color=MUTED, border=False),
        _style(SECTION, size=11, bold=True, color=ACCENT, fill=ACCENT_LIGHT),
        _style(
            HEADER, size=10, bold=True, color=WHITE, fill=ACCENT, horizontal="center", wrap=True
        ),
        _style(LABEL, size=10, bold=True, fill=READONLY_BG),
        _style(INPUT_TEXT, fill=INPUT_BG, locked=False, wrap=True),
        _style(
            INPUT_NUMBER,
            fill=INPUT_BG,
            locked=False,
            horizontal="center",
            number_format="0",
        ),
        _style(
            INPUT_DECIMAL,
            fill=INPUT_BG,
            locked=False,
            horizontal="center",
            number_format="0.00",
        ),
        _style(
            INPUT_DATE,
            fill=INPUT_BG,
            locked=False,
            horizontal="center",
            number_format="dd/mm/yyyy",
        ),
        _style(READONLY, fill=READONLY_BG, color=MUTED, wrap=True),
        _style(
            READONLY_NUMBER,
            fill=READONLY_BG,
            color=MUTED,
            horizontal="center",
            number_format="0.00",
        ),
        _style(NOTE, size=9, italic=True, color=MUTED, border=False, wrap=True),
        _style(CODE, size=10, horizontal="center", fill=READONLY_BG, color=MUTED),
    ]


def register_styles(workbook: Workbook) -> None:
    """Add every named style to `workbook`, ignoring ones already present."""
    existing = set(workbook.named_styles)
    for style in build_styles():
        if style.name not in existing:
            workbook.add_named_style(style)
