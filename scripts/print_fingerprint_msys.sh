#!/usr/bin/env bash
# Run from Windows via PrintHardwareFingerprint.bat. Sets cwd to openplc-runtime (parent of scripts/).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE" || exit 1

PY=
for candidate in ./venvs/runtime/bin/python3 ./venvs/runtime/bin/python3.exe ./venvs/runtime/bin/python ./venvs/runtime/bin/python.exe; do
    if [ -e "$candidate" ]; then
        PY="$candidate"
        break
    fi
done

if [ -z "$PY" ]; then
    echo "ERROR: No Python found under $HERE/venvs/runtime/bin/" >&2
    exit 1
fi

exec "$PY" ./scripts/print_windows_fingerprint.py
