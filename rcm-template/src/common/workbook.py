"""Assembly of the openpyxl workbook: stage 1 of the build.

This stage is fully cross platform. It produces a macro-free `.xlsx` holding
every sheet, format, defined name, validation and formula. Stage 2 (Windows
only, `build/excel_com.py`) converts that file to `.xlsm` and injects the VBA.
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from src.common import styles
from src.common.config import BuildConfig
from src.seedloader import SeedData, load_seed
from src.sheets import registry
from src.sheets.base import BuildContext, SheetBuilder, SheetSpec, build_all

SEED_DIRNAME = "seed"


def build_workbook(
    config: BuildConfig,
    seed_demo: bool = False,
    builders: list[SheetBuilder] | None = None,
    seed: SeedData | None = None,
) -> tuple[Workbook, list[SheetSpec]]:
    """Create the workbook in memory and return it with the specs that were built.

    `seed_demo` is accepted so the CLI contract is stable; the demo analysis it
    loads arrives with the working sheets in later phases.
    """
    workbook = Workbook()
    # openpyxl always starts with one default sheet; builders append their own.
    workbook.remove(workbook.active)
    styles.register_styles(workbook)

    context = BuildContext(
        workbook=workbook,
        config=config,
        seed=seed if seed is not None else load_seed(config.project_root / SEED_DIRNAME),
    )
    context.regions["build.seed_demo"] = "S" if seed_demo else "N"

    specs = build_all(workbook, builders if builders is not None else registry(), context)
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
