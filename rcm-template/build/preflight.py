"""Environment checks run before the COM stage.

Section 8 of the specification requires the build to detect a missing "Trust
access to the VBA project object model" setting and print the exact path of the
option, instead of failing opaquely with COM error 1004. Every check therefore
returns a remedy in the user's language, not just a diagnosis.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum

# Office major versions that still ship a supported Excel, newest first.
_OFFICE_VERSIONS = ("16.0", "15.0", "14.0")

_VBOM_REGISTRY_PATH = r"HKEY_CURRENT_USER\Software\Microsoft\Office\{version}\Excel\Security"
_VBOM_UI_PATH = (
    "Excel > Archivo > Opciones > Centro de confianza > Configuración del Centro de "
    "confianza > Configuración de macros > 'Confiar en el acceso al modelo de objetos "
    "de proyectos de VBA'"
)


class Severity(Enum):
    """BLOCKER stops the COM stage; WARNING lets it proceed."""

    BLOCKER = "blocker"
    WARNING = "warning"


@dataclass(frozen=True)
class PreflightIssue:
    code: str
    severity: Severity
    message: str
    remedy: str

    @property
    def is_blocker(self) -> bool:
        return self.severity is Severity.BLOCKER


@dataclass(frozen=True)
class PreflightReport:
    issues: tuple[PreflightIssue, ...]

    @property
    def blockers(self) -> tuple[PreflightIssue, ...]:
        return tuple(issue for issue in self.issues if issue.is_blocker)

    @property
    def can_run_com(self) -> bool:
        return not self.blockers


def is_windows() -> bool:
    return sys.platform == "win32"


def check_environment() -> PreflightReport:
    """Run every check and collect the issues found."""
    issues: list[PreflightIssue] = []

    if not is_windows():
        issues.append(
            PreflightIssue(
                code="not-windows",
                severity=Severity.BLOCKER,
                message=(
                    f"La etapa COM requiere Windows con Excel instalado; "
                    f"esta máquina es '{sys.platform}'."
                ),
                remedy=(
                    "Ejecute el build en Windows, o use --no-com para generar sólo el "
                    ".xlsx sin macros."
                ),
            )
        )
        # The remaining checks are Windows-only APIs; stop here.
        return PreflightReport(tuple(issues))

    issues.extend(_check_pywin32())
    if any(issue.code == "pywin32-missing" for issue in issues):
        return PreflightReport(tuple(issues))

    issues.extend(_check_excel_registered())
    issues.extend(_check_vbom_trust())
    return PreflightReport(tuple(issues))


def _check_pywin32() -> list[PreflightIssue]:
    try:
        import win32com.client  # noqa: F401
    except ImportError:
        return [
            PreflightIssue(
                code="pywin32-missing",
                severity=Severity.BLOCKER,
                message="El paquete 'pywin32' no está instalado.",
                remedy="Ejecute: pip install -r requirements.txt",
            )
        ]
    return []


def _check_excel_registered() -> list[PreflightIssue]:
    import winreg

    try:
        winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "Excel.Application").Close()
    except OSError:
        return [
            PreflightIssue(
                code="excel-missing",
                severity=Severity.BLOCKER,
                message="No se encontró Excel de escritorio registrado en este equipo.",
                remedy=(
                    "Instale Microsoft Excel para escritorio. Excel Online y las "
                    "versiones de la Microsoft Store no exponen la automatización COM."
                ),
            )
        ]
    return []


def _check_vbom_trust() -> list[PreflightIssue]:
    """Check the AccessVBOM flag for every installed Office version.

    A value of 1 in any installed version is enough: the build only needs the
    Excel instance it actually launches to allow it, and we cannot know which
    version that will be until Excel starts.
    """
    import winreg

    found_versions: list[str] = []
    for version in _OFFICE_VERSIONS:
        subkey = rf"Software\Microsoft\Office\{version}\Excel\Security"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey) as key:
                value, _ = winreg.QueryValueEx(key, "AccessVBOM")
        except OSError:
            continue
        found_versions.append(version)
        if int(value) == 1:
            return []

    if not found_versions:
        # The key is created the first time the option is toggled, so its
        # absence is inconclusive rather than a failure.
        return [
            PreflightIssue(
                code="vbom-unknown",
                severity=Severity.WARNING,
                message=(
                    "No se pudo confirmar el ajuste 'Confiar en el acceso al modelo de "
                    "objetos de proyectos de VBA'."
                ),
                remedy=f"Si el build falla con error 1004, habilítelo en: {_VBOM_UI_PATH}",
            )
        ]

    registry_paths = ", ".join(
        _VBOM_REGISTRY_PATH.format(version=version) for version in found_versions
    )
    return [
        PreflightIssue(
            code="vbom-disabled",
            severity=Severity.BLOCKER,
            message=(
                "El acceso al modelo de objetos de proyectos de VBA está deshabilitado; "
                "la importación de módulos fallaría con error 1004."
            ),
            remedy=(f"Habilítelo en: {_VBOM_UI_PATH}. Equivale a AccessVBOM=1 en {registry_paths}"),
        )
    ]


def format_report(report: PreflightReport) -> str:
    """Render a report as indented text for the build log."""
    if not report.issues:
        return "Preflight: OK"
    lines = ["Preflight:"]
    for issue in report.issues:
        marker = "ERROR" if issue.is_blocker else "AVISO"
        lines.append(f"  [{marker}] {issue.message}")
        lines.append(f"          {issue.remedy}")
    return "\n".join(lines)
