# Cython build (webserver IP protection)

This is an **optional release** path: compile `webserver/**/*.py` to native extensions (`.so` / `.pyd`) and remove the original `.py` files so the shipped tree does not contain readable Python source.

## When to use it

- You want **stronger obscurity** than bytecode-only stripping (still not DRM; determined attackers can reverse native code).
- You accept a **slower** release build and **per-platform** artifacts (Linux vs Windows vs macOS each need their own compile).

## When not to use it

- **Day-to-day development**: keep plain Python, `pip install -e .`, and normal tests.
- **No C toolchain**: Cython needs a working compiler (GCC/Clang on Linux/MSYS2, MSVC or mingw on Windows).

## Steps

1. Install build deps (in your runtime venv):

   ```bash
   pip install -r requirements.txt
   pip install "Cython>=3,<4"
   ```

2. Compile in place:

   ```bash
   python setup_cython.py build_ext --inplace
   ```

   This generates extension modules next to each `.py` and may emit `.c` files under `webserver/` (ignored by git if listed in `.gitignore`).

3. Remove plain Python **only after** step 2 succeeds:

   ```bash
   python scripts/strip_webserver_py_after_cython.py
   ```

   If some files are skipped, the script lists them; fix the Cython build for those modules first.

4. **Dry-run** strip:

   ```bash
   python scripts/strip_webserver_py_after_cython.py --dry-run
   ```

5. Run the runtime from the same venv:

   ```bash
   python -m webserver.app
   ```

## CI / Windows installer

- Run steps 2–3 on the **payload copy** (e.g. `windows/payload/openplc-runtime`) **after** `install.sh` and **before** Inno Setup, using the **same** Python version as the venv you ship.
- Do not mix Python minor versions between compile and runtime.

## Relationship to `setup_cython.py` vs `pyproject.toml`

- Default **`pip install .`** / **`pip install -e .`** uses **`pyproject.toml`** only and stays **pure Python** (no Cython required).
- **`setup_cython.py`** is **manual** for release builds only.

## Troubleshooting

- **Import errors** after strip: re-run `build_ext --inplace` with the **exact** interpreter you use at runtime.
- **A module fails to Cythonize**: exclude it temporarily in `setup_cython.py` (narrow `_collect_extensions`) or add Cython directives; some dynamic patterns need `binding=True` (already set).

## License checks

Windows license verification in `webserver/windows_license.py` is unchanged; it compiles like any other module.
