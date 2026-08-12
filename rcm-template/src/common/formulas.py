"""Static analysis of the formulas the build writes.

Two project constraints are checkable without Excel, so they are checked here
and enforced by the test suite:

  * no formula nests function calls more than three levels deep -- deeper logic
    belongs in a rule table or in VBA;
  * every defined name a formula references actually exists, which is what turns
    a silent `#NAME?` in the delivered workbook into a failing build.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

MAX_NESTING = 3

# Defined names follow the prefixes declared in src/common/names.py.
_NAME_PATTERN = re.compile(r"\b(?:PARAM|CAT|LIB|RNG)_[A-Z0-9_.]+", re.IGNORECASE)
_IDENTIFIER_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.$")


@dataclass(frozen=True)
class FormulaInfo:
    sheet: str
    cell: str
    formula: str
    depth: int
    names: frozenset[str]


def nesting_depth(formula: str) -> int:
    """Maximum depth of nested function calls in `formula`.

    Only parentheses that open a function call count; parentheses used purely to
    group arithmetic do not, since they carry no readability cost.
    """
    depth = 0
    maximum = 0
    in_string = False
    previous = ""
    # One entry per open parenthesis: True when it opened a function call.
    open_parens: list[bool] = []

    for char in formula:
        if char == '"':
            in_string = not in_string
            previous = char
            continue
        if in_string:
            continue

        if char == "(":
            is_call = previous in _IDENTIFIER_CHARS
            open_parens.append(is_call)
            if is_call:
                depth += 1
                maximum = max(maximum, depth)
        elif char == ")":
            if open_parens and open_parens.pop():
                depth -= 1

        if char.strip():
            previous = char

    return maximum


def referenced_names(formula: str) -> frozenset[str]:
    """Defined names a formula refers to, upper cased."""
    return frozenset(match.group(0).upper() for match in _NAME_PATTERN.finditer(formula))


def scan_workbook(workbook) -> list[FormulaInfo]:
    """Collect every formula in `workbook` with its depth and referenced names."""
    found: list[FormulaInfo] = []
    for worksheet in workbook.worksheets:
        for row in worksheet.iter_rows():
            for cell in row:
                value = cell.value
                if not isinstance(value, str) or not value.startswith("="):
                    continue
                found.append(
                    FormulaInfo(
                        sheet=worksheet.title,
                        cell=cell.coordinate,
                        formula=value,
                        depth=nesting_depth(value),
                        names=referenced_names(value),
                    )
                )
    return found


def distinct_formulas(infos: list[FormulaInfo]) -> list[FormulaInfo]:
    """One representative per distinct formula shape.

    A 500 row table repeats the same formula with different row numbers; for
    reporting purposes only the shape matters.
    """
    seen: set[tuple[str, str]] = set()
    unique: list[FormulaInfo] = []
    for info in infos:
        shape = (info.sheet, re.sub(r"\d+", "#", info.formula))
        if shape in seen:
            continue
        seen.add(shape)
        unique.append(info)
    return unique
