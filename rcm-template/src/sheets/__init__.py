"""Worksheet builders, one module per sheet.

`registry()` is the single source of truth for which sheets exist and in what
tab order: visible working sheets first, in the order the analysis follows, then
configuration, then the hidden libraries.
"""

from __future__ import annotations

from src.sheets.amfe import AmfeSheetBuilder
from src.sheets.base import BuildContext, SheetBuilder, SheetSpec
from src.sheets.contexto import ContextoSheetBuilder
from src.sheets.criticidad import CriticidadSheetBuilder
from src.sheets.diccionario import DiccionarioSheetBuilder
from src.sheets.inicio import InicioSheetBuilder
from src.sheets.librerias import library_builders
from src.sheets.parametros import ParametrosSheetBuilder
from src.sheets.particion import ParticionSheetBuilder


def registry() -> list[SheetBuilder]:
    """The builders of every sheet, in tab order.

    Order matters twice: it is the tab order the analyst sees, and it is the
    build order, so a builder that publishes a region must come before the one
    that reads it. `Particion` before `AMFE` is the current instance of that.
    """
    return [
        InicioSheetBuilder(),
        ContextoSheetBuilder(),
        CriticidadSheetBuilder(),
        ParticionSheetBuilder(),
        AmfeSheetBuilder(),
        ParametrosSheetBuilder(),
        DiccionarioSheetBuilder(),
        *library_builders(),
    ]


__all__ = ["BuildContext", "SheetBuilder", "SheetSpec", "registry"]
