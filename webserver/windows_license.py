"""
Windows distribution license verification.

The Windows installer build runs this runtime under MSYS2. A license file (JWT,
RS256) must be present and must match the host hardware fingerprint derived
from the Windows MachineGuid and computer name.

Linux and other non-Windows platforms are not gated by this module.
"""

from __future__ import annotations

import hashlib
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Final

import jwt

DEFAULT_LICENSE_BASENAME: Final[str] = "openplc.license"
PUBLIC_KEY_RELPATH: Final[str] = "webserver/keys/license_public.pem"


def is_windows_runtime() -> bool:
    """True when running the Windows-oriented build (win32, MSYS2, or Cygwin)."""
    plat = sys.platform
    if plat == "win32":
        return True
    if plat == "msys":
        return True
    if plat.startswith("cygwin"):
        return True
    return False


def license_enforcement_enabled() -> bool:
    if os.environ.get("OPENPLC_SKIP_LICENSE_CHECK", "").strip().lower() in (
        "1",
        "true",
        "yes",
    ):
        return False
    return is_windows_runtime()


def _machine_guid_winreg() -> str:
    import winreg

    key = winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\Microsoft\Cryptography",
        0,
        winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
    )
    try:
        value, _ = winreg.QueryValueEx(key, "MachineGuid")
        return str(value).strip().lower()
    finally:
        winreg.CloseKey(key)


def _machine_guid_subprocess() -> str:
    commands: list[list[str]] = [
        [
            "reg.exe",
            "QUERY",
            r"HKLM\SOFTWARE\Microsoft\Cryptography",
            "/v",
            "MachineGuid",
        ],
        [
            "reg",
            "QUERY",
            r"HKLM\SOFTWARE\Microsoft\Cryptography",
            "/v",
            "MachineGuid",
        ],
    ]
    uuid_re = re.compile(
        r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
        re.IGNORECASE,
    )
    for cmd in commands:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode != 0:
            continue
        m = uuid_re.search(result.stdout or "")
        if m:
            return m.group(1).strip().lower()
    raise OSError("Could not read Windows MachineGuid from registry")


def get_windows_machine_guid() -> str:
    if sys.platform == "win32":
        try:
            return _machine_guid_winreg()
        except ImportError:
            pass
        except OSError:
            pass
    return _machine_guid_subprocess()


def compute_hardware_fingerprint() -> str:
    """
    Stable fingerprint for the current Windows host.

    Uses HKLM MachineGuid and the computer name. If MachineGuid cannot be read,
    falls back to an opaque error-oriented sentinel so verification fails closed.
    """
    try:
        guid = get_windows_machine_guid()
    except OSError:
        guid = "unknown-machine-guid"
    node = (platform.node() or "unknown-node").strip().lower()
    raw = f"{guid}|{node}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def default_license_path(repo_root: Path) -> Path:
    env_path = os.environ.get("OPENPLC_LICENSE_FILE", "").strip()
    if env_path:
        return Path(env_path).expanduser().resolve()
    return (repo_root / DEFAULT_LICENSE_BASENAME).resolve()


def default_public_key_path(repo_root: Path) -> Path:
    env_path = os.environ.get("OPENPLC_LICENSE_PUBLIC_KEY", "").strip()
    if env_path:
        return Path(env_path).expanduser().resolve()
    return (repo_root / PUBLIC_KEY_RELPATH).resolve()


def verify_license(repo_root: Path | None = None) -> tuple[bool, str]:
    """
    Verify license file for this machine.

    Returns (True, message) on success, (False, error_message) on failure.
    """
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent

    lic_path = default_license_path(repo_root)
    pub_path = default_public_key_path(repo_root)

    if not lic_path.is_file():
        return (
            False,
            f"OpenPLC Runtime (Windows): license file not found.\n"
            f"Expected: {lic_path}\n"
            f"Or set OPENPLC_LICENSE_FILE to the license file path.",
        )

    if not pub_path.is_file():
        return (
            False,
            f"OpenPLC Runtime (Windows): public key missing at {pub_path}.",
        )

    try:
        token = lic_path.read_text(encoding="utf-8").strip()
        pub_pem = pub_path.read_text(encoding="utf-8")
    except OSError as e:
        return False, f"OpenPLC Runtime (Windows): cannot read license or key: {e}"

    try:
        payload = jwt.decode(
            token,
            pub_pem,
            algorithms=["RS256"],
            options={"require": ["fp"]},
        )
    except jwt.ExpiredSignatureError:
        return False, "OpenPLC Runtime (Windows): license has expired."
    except jwt.InvalidTokenError as e:
        return False, f"OpenPLC Runtime (Windows): invalid license: {e}"

    expected_fp = str(payload.get("fp", "")).strip().lower()
    actual_fp = compute_hardware_fingerprint().lower()
    if expected_fp != actual_fp:
        return (
            False,
            "OpenPLC Runtime (Windows): license does not match this computer.\n"
            f"Expected fingerprint (in license): {expected_fp}\n"
            f"This machine fingerprint: {actual_fp}\n"
            "Request a license for this machine fingerprint from your vendor.",
        )

    return True, "License valid."


def ensure_licensed_or_exit(repo_root: Path | None = None) -> None:
    if not license_enforcement_enabled():
        return
    ok, msg = verify_license(repo_root)
    if not ok:
        print(msg, file=sys.stderr)
        raise SystemExit(2)
