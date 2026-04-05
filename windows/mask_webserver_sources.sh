#!/usr/bin/env bash
# Remove plain-text Python under webserver/ from a *distribution copy* only.
#
# Run against the installer payload tree (e.g. windows/payload/openplc-runtime),
# never against your main git checkout without a backup.
#
# Steps:
# 1. Byte-compile all webserver modules into __pycache__/
# 2. Delete *.py and *.pyi (imports still resolve from .pyc for the same Python)
# 3. Remove markdown docs shipped under webserver/

set -euo pipefail

usage() {
    echo "Usage: $0 <openplc-runtime-root>" >&2
    echo "  openplc-runtime-root must contain venvs/runtime/bin/python3 and webserver/" >&2
    exit 2
}

if [[ "${1:-}" == "" ]]; then
    usage
fi

ROOT="$(cd "$1" && pwd)"
PY="${ROOT}/venvs/runtime/bin/python3"
WEB="${ROOT}/webserver"

if [[ ! -x "$PY" ]]; then
    echo "ERROR: Python not found at $PY" >&2
    exit 1
fi

if [[ ! -d "$WEB" ]]; then
    echo "ERROR: webserver directory not found at $WEB" >&2
    exit 1
fi

echo "Masking webserver sources under: $WEB"
"$PY" -m compileall -q -f "$WEB"
find "$WEB" -type f -name '*.py' -delete
find "$WEB" -type f -name '*.pyi' -delete
find "$WEB" -type f -name '*.md' -delete
echo "Done. webserver/ now contains bytecode and resources only (no .py)."
