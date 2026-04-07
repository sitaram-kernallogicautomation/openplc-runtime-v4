#!/usr/bin/env python3
"""
Remove webserver/*.py after Cython build_ext --inplace, only if a matching extension exists.

Run from repository root:

    python scripts/strip_webserver_py_after_cython.py

Dry-run:

    python scripts/strip_webserver_py_after_cython.py --dry-run

Do not run on your main git tree without a backup; use on a release copy or CI artifact.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _has_compiled_module(py_file: Path) -> bool:
    d = py_file.parent
    stem = py_file.stem
    patterns = (
        f"{stem}.*.so",
        f"{stem}.*.pyd",
        f"{stem}.so",
        f"{stem}.pyd",
        f"{stem}.cpython-312-x86_64-linux-gnu.so",
        f"{stem}.cpython-312-x86_64-cygwin.dll",
    )
    for pat in patterns:
        if list(d.glob(pat)):
            return True
    return False


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--root",
        type=Path,
        default=Path("webserver"),
        help="Package root (default: webserver/)",
    )
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    root: Path = args.root
    if not root.is_dir():
        print(f"ERROR: {root} is not a directory", file=sys.stderr)
        return 1

    removed = 0
    skipped = 0
    for py in sorted(root.rglob("*.py")):
        if "__pycache__" in py.parts:
            continue
        # Entry point for `python -m webserver`; must stay as .py (not Cythonized).
        if py.name == "__main__.py":
            continue
        if not _has_compiled_module(py):
            print(f"SKIP (no extension next to source): {py}")
            skipped += 1
            continue
        if args.dry_run:
            print(f"WOULD REMOVE {py}")
        else:
            py.unlink()
            print(f"removed {py}")
        removed += 1

    if skipped:
        print(
            f"\nERROR: {skipped} file(s) have no compiled extension next to them.\n"
            "Run: python setup_cython.py build_ext --inplace",
            file=sys.stderr,
        )
        return 1

    print(f"Done. Removed {removed} .py file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
