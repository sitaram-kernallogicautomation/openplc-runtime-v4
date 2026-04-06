#!/usr/bin/env python3
"""
Compile webserver/*.py to native extensions with Cython (release / IP-hardening).

Usage (from repository root, with a venv that has runtime deps + Cython):

    pip install Cython
    python setup_cython.py build_ext --inplace

Then remove plain Python sources so only .so / .pyd remain:

    python scripts/strip_webserver_py_after_cython.py

Development: do not run this; use normal ``pip install -e .`` and plain .py files.

This file is intentionally separate from the default ``pyproject.toml`` install so
``pip install .`` does not require a C compiler or Cython for day-to-day work.
"""

from __future__ import annotations

from pathlib import Path

from setuptools import Extension, find_packages, setup

try:
    from Cython.Build import cythonize
except ImportError as e:
    raise SystemExit("Install Cython first: pip install Cython") from e


def _collect_extensions() -> list[Extension]:
    exts: list[Extension] = []
    root = Path("webserver")
    if not root.is_dir():
        raise SystemExit("webserver/ not found (run from repository root)")
    for py in sorted(root.rglob("*.py")):
        if "__pycache__" in py.parts:
            continue
        mod = ".".join(py.with_suffix("").parts)
        exts.append(Extension(mod, [str(py)]))
    if not exts:
        raise SystemExit("No Python files found under webserver/")
    return exts


setup(
    name="openplc-runtime",
    version="0.1.0",
    packages=find_packages(include=["webserver", "webserver.logger"]),
    ext_modules=cythonize(
        _collect_extensions(),
        compiler_directives={
            "language_level": "3",
            "binding": True,
        },
        nthreads=4,
    ),
    zip_safe=False,
)
