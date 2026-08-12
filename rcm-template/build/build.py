"""Build orchestrator for the RCM template generator.

Usage:
    python build/build.py --output dist/RCM_Template_v0.1.0.xlsm [--sign] [--seed-demo]

The build runs in two stages:

  1. Cross platform. openpyxl assembles the whole workbook structure into a
     temporary `.xlsx`. Runs anywhere, and is what the test suite exercises.
  2. Windows only. Excel is driven over COM to produce the `.xlsm`, import the
     VBA components, apply protection, sign and recalculate.

On a machine without Excel, stage 2 is skipped with an explicit warning and the
`.xlsx` is kept as the build output. Pass --require-com to turn that skip into a
failure (use it in CI on Windows).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from build import excel_com, preflight, sign  # noqa: E402
from src.common.config import BuildConfig, ConfigError, load_config  # noqa: E402
from src.common.workbook import build_workbook, write_workbook  # noqa: E402

MANIFEST_NAME = "manifest.json"
_HASH_CHUNK_BYTES = 1 << 20


class BuildError(RuntimeError):
    """Raised when the build cannot produce its declared output."""


@dataclass
class BuildResult:
    version: str
    output_path: Path
    sheet_count: int
    sheet_titles: list[str]
    com_stage: str
    imported_components: list[str] = field(default_factory=list)
    protected_sheets: int = 0
    signed: bool = False
    signing_note: str = "No solicitada."

    @property
    def is_macro_enabled(self) -> bool:
        return self.output_path.suffix.lower() == ".xlsm"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="build.py",
        description="Compila la plantilla RCM2 / MSG-3.",
    )
    parser.add_argument(
        "--output",
        help="Ruta del archivo de salida. Por defecto, la de build.config.yaml.",
    )
    parser.add_argument(
        "--config",
        help="Ruta de build.config.yaml. Por defecto, build/build.config.yaml.",
    )
    parser.add_argument(
        "--sign",
        action="store_true",
        help="Firma el proyecto VBA (requiere RCM_CERT_THUMBPRINT).",
    )
    parser.add_argument(
        "--seed-demo",
        action="store_true",
        help="Incluye el análisis de ejemplo de seed/ (disponible desde la fase 2).",
    )
    parser.add_argument(
        "--no-com",
        action="store_true",
        help="Omite la etapa de Excel y produce solo el .xlsx sin macros.",
    )
    parser.add_argument(
        "--require-com",
        action="store_true",
        help="Falla si la etapa de Excel no puede ejecutarse, en vez de omitirla.",
    )
    parser.add_argument(
        "--keep-intermediate",
        action="store_true",
        help="Conserva el .xlsx intermedio junto al archivo de salida.",
    )
    return parser.parse_args(argv)


def resolve_output_path(config: BuildConfig, requested: str | None) -> Path:
    if not requested:
        return config.default_output_path()
    path = Path(requested.format(version=config.version))
    return path if path.is_absolute() else config.project_root / path


def run_build(
    config: BuildConfig,
    output_path: Path,
    *,
    seed_demo: bool = False,
    sign_project: bool = False,
    use_com: bool = True,
    require_com: bool = False,
    keep_intermediate: bool = False,
    log=print,
) -> BuildResult:
    """Execute the build and return what was produced."""
    # Fail on a bad VBA component list before doing any work.
    component_paths = config.vba_component_paths()

    log(f"[1/4] Construyendo la estructura del libro (versión {config.version})...")
    workbook, specs = build_workbook(config, seed_demo=seed_demo)
    sheet_titles = [spec.title for spec in specs]

    intermediate_path = output_path.with_suffix(".xlsx")
    write_workbook(workbook, intermediate_path)
    log(f"      {len(sheet_titles)} hoja(s): {', '.join(sheet_titles)}")
    log(f"      Intermedio: {_relative(intermediate_path, config.project_root)}")

    result = BuildResult(
        version=config.version,
        output_path=intermediate_path,
        sheet_count=len(sheet_titles),
        sheet_titles=sheet_titles,
        com_stage="omitida",
    )

    log("[2/4] Comprobando el entorno de Excel...")
    report = preflight.check_environment()
    log(preflight.format_report(report))

    if not use_com:
        result.com_stage = "omitida (--no-com)"
    elif not report.can_run_com:
        if require_com:
            raise BuildError(
                "La etapa COM es obligatoria (--require-com) pero el entorno no la permite."
            )
        result.com_stage = "omitida (entorno sin Excel)"
    else:
        _run_com_stage(
            config,
            component_paths,
            intermediate_path,
            output_path,
            result,
            sign_project=sign_project,
            keep_intermediate=keep_intermediate,
            log=log,
        )

    if result.com_stage.startswith("omitida"):
        log(f"[3/4] Etapa de Excel {result.com_stage}. Salida sin macros.")
        if sign_project:
            raise BuildError(
                "No se puede firmar un libro sin macros: la etapa de Excel no se ejecutó."
            )
        result.signing_note = "No aplicable: libro sin macros."

    log("[4/4] Escribiendo el manifiesto...")
    manifest_path = write_manifest(config, result, component_paths)
    log(f"      {_relative(manifest_path, config.project_root)}")
    return result


def _run_com_stage(
    config: BuildConfig,
    component_paths: list[Path],
    intermediate_path: Path,
    output_path: Path,
    result: BuildResult,
    *,
    sign_project: bool,
    keep_intermediate: bool,
    log,
) -> None:
    log("[3/4] Etapa de Excel: convirtiendo a .xlsm e importando VBA...")
    macro_path = output_path.with_suffix(".xlsm")

    with excel_com.excel_session() as application:
        workbook = excel_com.convert_to_xlsm(application, intermediate_path, macro_path)
        result.imported_components = excel_com.import_vba_components(workbook, component_paths)
        log(f"      Módulos importados: {', '.join(result.imported_components) or 'ninguno'}")

        password = excel_com.password_from_env(config.protection.worksheet_password_env)
        result.protected_sheets = excel_com.protect_worksheets(workbook, password)
        if result.protected_sheets:
            log(f"      Hojas protegidas: {result.protected_sheets}")
        else:
            log(
                f"      Sin protección de hojas ({config.protection.worksheet_password_env} "
                "no definida)."
            )

        excel_com.save_and_close(workbook)

    result.output_path = macro_path
    result.com_stage = "completada"

    if sign_project:
        signing = sign.sign_workbook(macro_path, config)
        result.signed = signing.signed
        result.signing_note = signing.reason
        log(f"      Firma: {signing.reason}")
    else:
        result.signing_note = "No solicitada (--sign ausente)."

    if not keep_intermediate and intermediate_path.exists():
        intermediate_path.unlink()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_HASH_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(config: BuildConfig, result: BuildResult, component_paths: list[Path]) -> Path:
    """Emit dist/manifest.json as required by section 8 of the specification."""
    manifest = {
        "version": result.version,
        "built_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "output": {
            "file": _relative(result.output_path, config.project_root).as_posix(),
            "sha256": file_sha256(result.output_path),
            "macro_enabled": result.is_macro_enabled,
        },
        "sheets": {"count": result.sheet_count, "titles": result.sheet_titles},
        "vba_modules": [
            {
                "file": path.name,
                "sha256": file_sha256(path),
            }
            for path in component_paths
        ],
        "com_stage": result.com_stage,
        "imported_components": result.imported_components,
        "protected_sheets": result.protected_sheets,
        "signature": {"signed": result.signed, "note": result.signing_note},
    }
    manifest_path = result.output_path.parent / MANIFEST_NAME
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest_path


def _relative(path: Path, root: Path) -> Path:
    try:
        return path.resolve().relative_to(root.resolve())
    except ValueError:
        return path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        config = load_config(args.config)
        output_path = resolve_output_path(config, args.output)
        result = run_build(
            config,
            output_path,
            seed_demo=args.seed_demo,
            sign_project=args.sign,
            use_com=not args.no_com,
            require_com=args.require_com,
            keep_intermediate=args.keep_intermediate,
        )
    except (BuildError, ConfigError, excel_com.ExcelComError, sign.SigningError) as exc:
        print(f"\nBuild fallido: {exc}", file=sys.stderr)
        return 1

    print(f"\nOK  {_relative(result.output_path, config.project_root)}")
    if not result.is_macro_enabled:
        print("    Advertencia: la salida no contiene macros (etapa de Excel no ejecutada).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
