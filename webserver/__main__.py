"""
Entry point for ``python -m webserver``.

When ``webserver.app`` is a C extension (Cython), ``python -m webserver.app`` cannot be
used: extension modules have no code object for ``runpy``. This module stays as plain
Python and is not removed by ``strip_webserver_py_after_cython.py``.
"""

from __future__ import annotations

from webserver.app import run_https

if __name__ == "__main__":
    run_https()
