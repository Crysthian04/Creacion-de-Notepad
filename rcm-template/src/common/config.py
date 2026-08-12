"""Typed access to `build/build.config.yaml`.

The build must fail loudly on a malformed or incomplete configuration rather
than silently falling back to a default, so every accessor validates its input.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_RELPATH = Path("build") / "build.config.yaml"


class ConfigError(ValueError):
    """Raised when the build configuration is missing or malformed."""


@dataclass(frozen=True)
class WorkbookConfig:
    default_output: str
    properties: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class VbaConfig:
    source_dir: str
    components: tuple[str, ...]


@dataclass(frozen=True)
class ProtectionConfig:
    vba_project_password_env: str
    worksheet_password_env: str


@dataclass(frozen=True)
class SigningConfig:
    thumbprint_env: str
    timestamp_url: str
    digest_algorithm: str


@dataclass(frozen=True)
class BuildConfig:
    """The whole build configuration, resolved against a project root."""

    project_root: Path
    version: str
    workbook: WorkbookConfig
    vba: VbaConfig
    protection: ProtectionConfig
    signing: SigningConfig

    @property
    def vba_dir(self) -> Path:
        return self.project_root / self.vba.source_dir

    def vba_component_paths(self) -> list[Path]:
        """Absolute paths of the VBA components, in import order.

        Raises ConfigError if a declared component is missing, so that a typo in
        the configuration surfaces before Excel is ever opened.
        """
        paths: list[Path] = []
        for name in self.vba.components:
            path = self.vba_dir / name
            if not path.is_file():
                raise ConfigError(
                    f"VBA component declared in the configuration does not exist: {path}"
                )
            paths.append(path)
        return paths

    def default_output_path(self) -> Path:
        return self.project_root / self.workbook.default_output.format(version=self.version)


def _require(mapping: Any, key: str, context: str) -> Any:
    if not isinstance(mapping, dict):
        raise ConfigError(f"Expected a mapping at '{context}', got {type(mapping).__name__}.")
    if key not in mapping:
        raise ConfigError(f"Missing required key '{key}' in '{context}'.")
    return mapping[key]


def _require_str(mapping: Any, key: str, context: str) -> str:
    value = _require(mapping, key, context)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"Key '{key}' in '{context}' must be a non-empty string.")
    return value


def load_config(path: Path | str | None = None, project_root: Path | None = None) -> BuildConfig:
    """Load and validate the build configuration.

    `path` defaults to `<project_root>/build/build.config.yaml`; `project_root`
    defaults to the directory two levels above this module.
    """
    root = Path(project_root).resolve() if project_root else Path(__file__).resolve().parents[2]
    config_path = Path(path).resolve() if path else root / DEFAULT_CONFIG_RELPATH

    if not config_path.is_file():
        raise ConfigError(f"Build configuration not found: {config_path}")

    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Build configuration is not valid YAML: {config_path}\n{exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError(f"Build configuration must be a YAML mapping: {config_path}")

    workbook_raw = _require(raw, "workbook", "root")
    vba_raw = _require(raw, "vba", "root")
    protection_raw = _require(raw, "protection", "root")
    signing_raw = _require(raw, "signing", "root")

    components = _require(vba_raw, "components", "vba")
    if not isinstance(components, list) or not all(isinstance(item, str) for item in components):
        raise ConfigError("'vba.components' must be a list of file names.")

    properties = workbook_raw.get("properties", {}) or {}
    if not isinstance(properties, dict):
        raise ConfigError("'workbook.properties' must be a mapping.")

    return BuildConfig(
        project_root=root,
        version=_require_str(raw, "version", "root"),
        workbook=WorkbookConfig(
            default_output=_require_str(workbook_raw, "default_output", "workbook"),
            properties={str(k): str(v) for k, v in properties.items()},
        ),
        vba=VbaConfig(
            source_dir=_require_str(vba_raw, "source_dir", "vba"),
            components=tuple(components),
        ),
        protection=ProtectionConfig(
            vba_project_password_env=_require_str(
                protection_raw, "vba_project_password_env", "protection"
            ),
            worksheet_password_env=_require_str(
                protection_raw, "worksheet_password_env", "protection"
            ),
        ),
        signing=SigningConfig(
            thumbprint_env=_require_str(signing_raw, "thumbprint_env", "signing"),
            timestamp_url=_require_str(signing_raw, "timestamp_url", "signing"),
            digest_algorithm=_require_str(signing_raw, "digest_algorithm", "signing"),
        ),
    )
