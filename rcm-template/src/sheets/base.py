"""Sheet builder contract and registry.

Every worksheet of the template is produced by one builder object. The registry
below defines the physical tab order of the workbook: builders are applied in
list order, so reordering the list reorders the tabs.

Adding a sheet means writing a builder and registering it here -- no other file
changes. Phases 2 through 9 fill this registry in.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from openpyxl.workbook.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

# Excel sheet visibility states, mirrored here so builders never import the
# raw string literals.
VISIBLE = "visible"
HIDDEN = "hidden"
VERY_HIDDEN = "veryHidden"


@dataclass(frozen=True)
class SheetSpec:
    """Static description of a sheet, independent of its contents.

    `title` is the Spanish tab caption seen by the analyst; `key` is the stable
    English identifier used by code and tests, which never changes even if the
    caption is retitled or translated.
    """

    key: str
    title: str
    visibility: str = VISIBLE

    def __post_init__(self) -> None:
        if self.visibility not in (VISIBLE, HIDDEN, VERY_HIDDEN):
            raise ValueError(f"Unknown visibility '{self.visibility}' for sheet '{self.key}'.")
        # Excel's own limit; catching it here beats a corrupt file later.
        if not self.title or len(self.title) > 31:
            raise ValueError(f"Sheet title must be 1-31 characters: '{self.title}'.")


class SheetBuilder(Protocol):
    """Anything that can materialise one sheet into a workbook."""

    spec: SheetSpec

    def build(self, worksheet: Worksheet) -> None:
        """Populate `worksheet`. The sheet already exists and is correctly named."""


def create_sheet(workbook: Workbook, spec: SheetSpec) -> Worksheet:
    """Append a sheet for `spec` and apply its visibility."""
    worksheet = workbook.create_sheet(title=spec.title)
    worksheet.sheet_state = spec.visibility
    return worksheet


def build_all(workbook: Workbook, builders: list[SheetBuilder]) -> list[SheetSpec]:
    """Apply every builder in order and return the specs that were built."""
    built: list[SheetSpec] = []
    for builder in builders:
        worksheet = create_sheet(workbook, builder.spec)
        builder.build(worksheet)
        built.append(builder.spec)
    return built
