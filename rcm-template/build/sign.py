"""Digital signature of the VBA project.

Excel's object model exposes no way to sign a VBA project, so this is a wrapper
around Microsoft's `signtool`. Signing an Office file additionally requires the
Office Subject Interface Packages to be registered on the machine; without them
`signtool` signs the file as a plain binary and Excel does not recognise the
macro signature.

The rule of this module: if signing was requested and cannot be done correctly,
fail. Never leave the caller believing a workbook is signed when it is not.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from src.common.config import BuildConfig

# Registered by the Office SIP installer; its absence means signatures would be
# written in a format Excel ignores.
_OFFICE_SIP_DLL = "msosipx.dll"
_SIP_DOC_URL = "https://learn.microsoft.com/en-us/deployoffice/security/designate-trusted-publisher"


class SigningError(RuntimeError):
    """Raised when signing was requested but cannot be completed."""


@dataclass(frozen=True)
class SigningResult:
    signed: bool
    reason: str
    thumbprint: str | None = None


def thumbprint_from_env(config: BuildConfig) -> str | None:
    value = os.environ.get(config.signing.thumbprint_env, "").strip()
    return value or None


def sign_workbook(path: Path, config: BuildConfig) -> SigningResult:
    """Sign `path` with the certificate named by the configured thumbprint."""
    thumbprint = thumbprint_from_env(config)
    if not thumbprint:
        raise SigningError(
            f"Se solicitó --sign pero la variable {config.signing.thumbprint_env} "
            "no está definida. Defina la huella digital del certificado de firma."
        )

    signtool = _find_signtool()
    if signtool is None:
        raise SigningError(
            "No se encontró 'signtool.exe'. Instale el Windows SDK o agregue signtool al PATH."
        )

    if not _office_sip_registered():
        raise SigningError(
            "Los Subject Interface Packages de Office no están registrados; la firma se "
            f"escribiría en un formato que Excel ignora. Referencia: {_SIP_DOC_URL}"
        )

    command = [
        str(signtool),
        "sign",
        "/sha1",
        thumbprint,
        "/fd",
        config.signing.digest_algorithm,
        "/tr",
        config.signing.timestamp_url,
        "/td",
        config.signing.digest_algorithm,
        str(path.resolve()),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise SigningError(f"signtool falló con código {completed.returncode}: {detail}")

    return SigningResult(signed=True, reason="Firmado con signtool.", thumbprint=thumbprint)


def _find_signtool() -> Path | None:
    found = shutil.which("signtool")
    if found:
        return Path(found)

    # signtool ships with the Windows SDK and is usually not on PATH; probe the
    # standard install location, newest SDK first.
    for program_files in ("ProgramFiles(x86)", "ProgramFiles"):
        base = os.environ.get(program_files)
        if not base:
            continue
        sdk_bin = Path(base) / "Windows Kits" / "10" / "bin"
        if not sdk_bin.is_dir():
            continue
        candidates = sorted(sdk_bin.glob("*/x64/signtool.exe"), reverse=True)
        if candidates:
            return candidates[0]
    return None


def _office_sip_registered() -> bool:
    """Check whether the Office SIP DLL is registered for Authenticode."""
    if os.name != "nt":
        return False
    try:
        import winreg
    except ImportError:  # pragma: no cover - Windows only.
        return False

    subkey = r"SOFTWARE\Microsoft\Cryptography\OID\EncodingType 0\CryptSIPDllCreateIndirectData"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey) as key:
            index = 0
            while True:
                try:
                    guid = winreg.EnumKey(key, index)
                except OSError:
                    return False
                index += 1
                with winreg.OpenKey(key, guid) as entry:
                    try:
                        dll, _ = winreg.QueryValueEx(entry, "Dll")
                    except OSError:
                        continue
                    if _OFFICE_SIP_DLL.lower() in str(dll).lower():
                        return True
    except OSError:
        return False
