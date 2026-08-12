# Architecture

## The shape of the thing

The workbook is a build artifact. Nothing in `dist/` is edited by hand and
nothing in it is versioned: the sources are this repository and `seed/`.

```
seed/*.csv ──▶ seedloader ──▶ BuildContext ──▶ sheet builders ──▶ .xlsx
                                                                   │
                                              vba/*.bas ──▶ excel_com ──▶ .xlsm
```

## Two build stages

Stage 1 (`src/`) is pure openpyxl and runs anywhere. Stage 2 (`build/excel_com.py`)
needs Windows and desktop Excel. Everything that *can* be decided without Excel is
decided in stage 1, which is why the test suite covers the structure of the
workbook without ever launching Office. See `entorno-build.md`.

## Sheet builders

One module per sheet under `src/sheets/`, each exporting a builder with a `spec`
(key, Spanish tab title, visibility, minimum role) and a `build(worksheet, context)`.
`registry()` lists them in tab order, and that list is the only place the set of
sheets is declared.

Registry order is also build order. A builder that publishes something another
builder consumes must come first: `Particion` publishes the column offset of its
description column, and `AMFE` reads it to build its `VLOOKUP`. That is what
`BuildContext.regions` is for — a builder never reaches into another builder's
layout.

`spec.key` is the stable English identifier used by code and tests. `spec.title`
is the Spanish caption on the tab. Renaming a tab must never break a test.

## Defined names are the API

No formula and no macro may contain a cell address. Every value that crosses a
sheet boundary is reachable through a defined name, built in `src/common/names.py`:

| Prefix | Points at | Example |
|---|---|---|
| `PARAM_` | one parameter value cell | `PARAM_UMBRAL_CLASE_A` |
| `CAT_` | a catalogue code range, used as a validation list | `CAT_OFICIO` |
| `LIB_` | a library data range | `LIB_LIBMODOSFALLA` |
| `RNG_` | anything else | `RNG_PARTICIONIDS` |

Ranges are absolute and sized exactly to their content, so nothing needs `OFFSET`
or `INDIRECT` to resolve. The cost is that a range does not grow when a row is
typed past its end; the button that resizes them arrives with `modUI`.

## Formula rules the build enforces

`tests/test_sheets.py` fails the build on any of these, using the analysis in
`src/common/formulas.py`:

- a formula referencing a defined name that does not exist (a `#NAME?` waiting to
  happen in a delivered file);
- function calls nested more than three deep;
- a volatile function (`OFFSET`, `INDIRECT`, `TODAY`, `NOW`, `RAND`);
- a whole-column reference.

The nesting limit is the one that actually shapes the design. Three places wanted
a fourth level and got a hidden helper column instead: the hierarchical item
number in `Particion`, the consequence category in `AMFE`, and the criticality
class in `Criticidad del Activo`. Each helper is documented where it is written.

## Seed contract

`seed/` holds every business constant. `src/seedloader/loader.py` reads it and
cross validates before a single cell is written:

- required columns present on every file;
- rows neither shorter nor longer than the header;
- unique keys;
- taxonomy parents that exist and sit exactly one level up;
- library rows referencing real taxonomy codes, real task types and real
  catalogue codes;
- parameters referencing real catalogues.

A seed that fails any of these breaks the build. That is deliberate: the
alternative is a workbook with silent gaps that the analyst discovers three weeks
into an analysis.

## Style vocabulary

`src/common/styles.py` registers named styles once per workbook. The analyst
learns four signals and nothing else:

| Look | Meaning |
|---|---|
| amber fill | you may type here (the cell is also unlocked for protection) |
| grey fill | calculated or inherited; do not type |
| dark band | column heading |
| light band | section heading |

Cell locking is set by the style, not by a separate pass, so "grey" and "locked"
cannot drift apart.

## Language split

Spanish is the product surface: sheet names, captions, notes, validation
messages, and the build's own console output. English is the developer surface:
identifiers, comments, commit messages and these documents. The `Diccionario`
sheet makes the split pay off — translating the workbook means filling in one
column.
