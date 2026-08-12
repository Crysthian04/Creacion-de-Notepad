"""Worksheet builders, one module per sheet.

`REGISTRY` is the single source of truth for which sheets exist and in what tab
order. Phase 1 registers only the cover sheet placeholder.
"""

from __future__ import annotations

from src.sheets.base import SheetBuilder
from src.sheets.inicio import InicioSheetBuilder

REGISTRY: list[SheetBuilder] = [
    InicioSheetBuilder(),
]

__all__ = ["REGISTRY", "SheetBuilder"]
