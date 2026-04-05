#!/usr/bin/env python3
"""
Print the hardware fingerprint used for Windows runtime licensing.

Run on the target Windows PC (inside the OpenPLC MSYS2 environment or any Python
with access to the Windows registry). Copy the printed line to the vendor to
obtain openplc.license.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running before editable install: repo root on path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from webserver.windows_license import compute_hardware_fingerprint, is_windows_runtime  # noqa: E402


def main() -> int:
    if not is_windows_runtime():
        print(
            "This script only applies to Windows (win32, MSYS, or Cygwin).",
            file=sys.stderr,
        )
        return 1
    print(compute_hardware_fingerprint())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
