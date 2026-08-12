"""Stage 2 of the build: Excel automation over COM (Windows only).

Responsibilities: convert the openpyxl `.xlsx` into a macro enabled `.xlsm`,
import the VBA components, apply protection and visibility, recalculate and
save. Excel is a process that outlives a crashed script, so every path out of
this module -- success, exception, or KeyboardInterrupt -- must close or kill
the instance it started. That is what `ExcelSession` guarantees.

Nothing here is imported at module load time on non-Windows platforms: the COM
imports happen inside the functions that need them.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import Any

# Excel FileFormat constants (XlFileFormat enumeration).
XL_OPEN_XML_WORKBOOK_MACRO_ENABLED = 52  # .xlsm

# VBComponent type constants (vbext_ComponentType enumeration).
_COMPONENT_TYPE_NAMES = {
    1: "módulo estándar",
    2: "módulo de clase",
    3: "formulario",
    100: "módulo de documento",
}

# Excel raises this HRESULT when the VBA project object model is not trusted.
_ERROR_ACCESS_DENIED_HRESULT = -2147352567  # 0x800A03EC ("1004")


class ExcelComError(RuntimeError):
    """Raised when the COM stage cannot complete."""


def is_available() -> bool:
    """True when this machine can run the COM stage at all."""
    from build import preflight

    return preflight.check_environment().can_run_com


@contextmanager
def excel_session(visible: bool = False) -> Iterator[Any]:
    """Start Excel, yield the Application object, and always shut it down.

    On a clean exit Excel is quit politely. On any error the process is killed,
    because a half-configured hidden Excel with a locked workbook is worse than
    no Excel at all.
    """
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    application = None
    process_id = None
    try:
        application = win32com.client.DispatchEx("Excel.Application")
        application.Visible = visible
        application.DisplayAlerts = False
        application.ScreenUpdating = False
        application.EnableEvents = False
        application.AskToUpdateLinks = False
        process_id = _process_id(application)
        yield application
    except BaseException:
        _kill(application, process_id)
        application = None
        raise
    finally:
        if application is not None:
            try:
                application.DisplayAlerts = True
                application.Quit()
            except Exception:  # noqa: BLE001 - Excel may already be gone; killing is the fallback.
                _kill(application, process_id)
        pythoncom.CoUninitialize()


def _process_id(application: Any) -> int | None:
    """Resolve the PID of an Excel instance from its main window handle."""
    try:
        import win32process

        _, pid = win32process.GetWindowThreadProcessId(application.Hwnd)
        return int(pid)
    except Exception:  # noqa: BLE001 - the PID is a best-effort fallback only.
        return None


def _kill(application: Any, process_id: int | None) -> None:
    if application is not None:
        # An unresponsive Excel is exactly the case this function exists for, so
        # a failed Quit() is expected and the PID path below takes over.
        with suppress(Exception):
            application.Quit()
    if process_id is None:
        return
    try:
        import win32api
        import win32con

        handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, False, process_id)
        win32api.TerminateProcess(handle, 1)
        win32api.CloseHandle(handle)
    except Exception:  # noqa: BLE001 - the process may have exited on its own.
        pass


def convert_to_xlsm(application: Any, source: Path, destination: Path) -> Any:
    """Open the `.xlsx` and save it as a macro enabled `.xlsm`.

    Returns the open Workbook object; the caller keeps working on it.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()

    workbook = application.Workbooks.Open(str(source.resolve()))
    workbook.SaveAs(str(destination.resolve()), FileFormat=XL_OPEN_XML_WORKBOOK_MACRO_ENABLED)
    return workbook


def import_vba_components(workbook: Any, components: list[Path]) -> list[str]:
    """Import each VBA file into the workbook project, in order.

    Returns the resulting component names. A component whose name already
    exists is removed first, so re-running the build is idempotent.
    """
    try:
        project = workbook.VBProject
    except Exception as exc:  # noqa: BLE001 - translated into an actionable message below.
        raise ExcelComError(
            "Excel no permitió el acceso al proyecto VBA. Habilite 'Confiar en el acceso "
            "al modelo de objetos de proyectos de VBA' en el Centro de confianza."
        ) from exc

    imported: list[str] = []
    for path in components:
        _remove_existing_component(project, path.stem)
        try:
            component = project.VBComponents.Import(str(path.resolve()))
        except Exception as exc:  # noqa: BLE001 - COM errors carry no useful type.
            if getattr(exc, "hresult", None) == _ERROR_ACCESS_DENIED_HRESULT:
                raise ExcelComError(
                    f"Error 1004 al importar '{path.name}': el acceso al modelo de objetos "
                    "de VBA sigue bloqueado."
                ) from exc
            raise ExcelComError(f"Falló la importación de '{path.name}': {exc}") from exc
        imported.append(str(component.Name))
    return imported


def _remove_existing_component(project: Any, name: str) -> None:
    for component in project.VBComponents:
        if str(component.Name) != name:
            continue
        # Document modules (ThisWorkbook, sheet modules) cannot be removed; their
        # code is replaced instead.
        if int(component.Type) == 100:
            module = component.CodeModule
            if module.CountOfLines > 0:
                module.DeleteLines(1, module.CountOfLines)
        else:
            project.VBComponents.Remove(component)
        return


def describe_components(workbook: Any) -> list[str]:
    """List the VBA components of a workbook as 'name (kind)' strings."""
    project = workbook.VBProject
    return [
        f"{component.Name} ({_COMPONENT_TYPE_NAMES.get(int(component.Type), 'desconocido')})"
        for component in project.VBComponents
    ]


def run_macro(application: Any, macro: str, *args: Any) -> Any:
    """Run a macro inside the built workbook (used by the VBA smoke tests)."""
    try:
        return application.Run(macro, *args)
    except Exception as exc:  # noqa: BLE001 - COM errors carry no useful type.
        raise ExcelComError(f"Falló la ejecución de la macro '{macro}': {exc}") from exc


def protect_worksheets(workbook: Any, password: str | None) -> int:
    """Protect every worksheet. Returns how many were protected.

    Phase 1 applies a uniform protection; per-role visibility and the finer
    grained locking of specific ranges arrive with `modUI` in phase 9.
    """
    if not password:
        return 0
    count = 0
    for worksheet in workbook.Worksheets:
        worksheet.Protect(Password=password, DrawingObjects=True, Contents=True, Scenarios=True)
        count += 1
    return count


def password_from_env(variable: str) -> str | None:
    value = os.environ.get(variable, "").strip()
    return value or None


def save_and_close(workbook: Any) -> None:
    """Recalculate, save and close the workbook."""
    workbook.Application.CalculateFullRebuild()
    workbook.Save()
    workbook.Close(SaveChanges=False)
