# Build environment

The build has two stages with different platform requirements. Knowing which
stage runs where explains every "the output has no macros" message.

## Stage 1 — workbook assembly (any platform)

`openpyxl` writes the whole workbook structure — sheets, formats, defined names,
data validations, conditional formatting, formulas and seed data — into a
temporary `.xlsx`. This stage has no Excel dependency, so it runs on Linux, macOS
and Windows, and it is what the test suite exercises.

## Stage 2 — Excel automation (Windows + desktop Excel)

Excel is driven over COM to:

1. save the `.xlsx` as `.xlsm` (`FileFormat=52`);
2. import every component listed in `vba.components`;
3. apply worksheet protection and initial visibility;
4. sign the VBA project when `--sign` is passed;
5. recalculate, save and close Excel cleanly.

Requirements:

| Requirement | How to check |
|---|---|
| Windows | `sys.platform == "win32"` |
| Desktop Excel (not Store, not Online) | `Excel.Application` registered in `HKCR` |
| `pywin32` | `pip install -r requirements.txt` |
| Trust access to the VBA project object model | see below |

### Trust access to the VBA project object model

Without this setting, step 2 fails with COM error 1004 and no useful message.
`build/preflight.py` detects the condition before Excel is launched and prints
the exact path of the option:

> Excel > Archivo > Opciones > Centro de confianza > Configuración del Centro de
> confianza > Configuración de macros > *Confiar en el acceso al modelo de objetos
> de proyectos de VBA*

The equivalent registry value is
`HKCU\Software\Microsoft\Office\<version>\Excel\Security\AccessVBOM = 1`.

## Running the build off Windows

Stage 2 is skipped with an explicit warning and the `.xlsx` is kept as the build
output. This is a valid way to review structure, formulas and formats; it is not
a deliverable, because none of the buttons work.

```bash
python build/build.py --no-com          # explicit skip, no warning noise
python build/build.py --require-com     # fail instead of skipping (use in CI)
```

## Known limitations of the COM stage

- **VBA project protection cannot be automated.** `VBProject.Protection` is
  read-only in the object model, and the only documented workaround is driving
  the VBE dialog with `SendKeys`, which is unreliable and silently corrupts the
  project when it mistimes. The build therefore does *not* lock the VBA project;
  it is a manual step performed once on the released file. See `docs/seguridad.md`
  for why this matters less than it appears.
- **Signing needs more than a certificate.** `signtool` signs an Office file in a
  format Excel recognises only when the Office Subject Interface Packages
  (`msosipx.dll`) are registered on the build machine. `build/sign.py` verifies
  this and refuses to produce a signature Excel would ignore.

## Command reference

```
python build/build.py [--output PATH] [--config PATH] [--sign] [--seed-demo]
                      [--no-com] [--require-com] [--keep-intermediate]
```

| Flag | Effect |
|---|---|
| `--output` | Output path. `{version}` is expanded. Defaults to `workbook.default_output`. |
| `--config` | Alternate `build.config.yaml`. |
| `--sign` | Sign the VBA project. Requires `RCM_CERT_THUMBPRINT`; fails if the COM stage did not run. |
| `--seed-demo` | Include the sample analysis from `seed/` (available from phase 2). |
| `--no-com` | Skip stage 2 deliberately. |
| `--require-com` | Turn an unavailable stage 2 into a build failure. |
| `--keep-intermediate` | Keep the intermediate `.xlsx` next to the output. |

## Environment variables

| Variable | Used by | Effect when unset |
|---|---|---|
| `RCM_CERT_THUMBPRINT` | `--sign` | Signing fails with an explicit message. |
| `RCM_SHEET_PASSWORD` | stage 2 | Worksheets are left unprotected. |
| `RCM_VBA_PROJECT_PASSWORD` | reserved | Not used yet (see limitations above). |

None of these are ever written to the repository or to `manifest.json`.

## Build manifest

Every build emits `dist/manifest.json`: version, UTC timestamp, output file with
its SHA-256, sheet count and titles, the SHA-256 of every imported VBA module,
whether the COM stage ran, and the signature status. It is the audit record that
answers "which exact template is this file?".
