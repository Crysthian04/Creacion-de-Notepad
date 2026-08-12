"""Assembly of the openpyxl workbook: stage 1 of the build.

This stage is fully cross platform. It produces a macro-free `.xlsx` holding
every sheet, format, defined name, validation and formula. Stage 2 (Windows
only, `build/excel_com.py`) converts that file to `.xlsm` and injects the VBA.
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from src.common.config import BuildConfig
from src.sheets import REGISTRY
from src.sheets.base import SheetBuilder, SheetSpec, build_all


def build_workbook(
    config: BuildConfig,
    seed_demo: bool = False,
    builders: list[SheetBuilder] | None = None,
) -> tuple[Workbook, list[SheetSpec]]:
    """Create the workbook in memory and return it with the specs that were built.

    `seed_demo` is accepted from phase 1 so the CLI contract is stable, but the
    demo dataset itself is loaded from `seed/` starting in phase 2.
    """
    workbook = Workbook()
    # openpyxl always starts with one default sheet; builders append their own.
    workbook.remove(workbook.active)

    specs = build_all(workbook, builders if builders is not None else REGISTRY)
    if not workbook.sheetnames:
        raise ValueError("The workbook has no sheets; at least one builder must be registered.")

    _apply_properties(workbook, config)
    workbook.active = 0
    return workbook, specs


def _apply_properties(workbook: Workbook, config: BuildConfig) -> None:
    properties = config.workbook.properties
    workbook.properties.title = properties.get("title")
    workbook.properties.subject = properties.get("subject")
    workbook.properties.creator = properties.get("creator")
    workbook.properties.version = config.version


def write_workbook(workbook: Workbook, destination: Path) -> Path:
    """Save `workbook` to `destination`, creating parent directories."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(destination)
    return destination
