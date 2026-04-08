# OpenPLC Runtime - Windows Installer

This directory contains the infrastructure for building a Windows installer for OpenPLC Runtime using MSYS2 and Inno Setup.

## Overview

The Windows installer bundles a complete MSYS2 environment with all required dependencies (GCC, Python, etc.) so users can run OpenPLC Runtime on Windows without needing to install any additional software.

## Files

- `setup.iss` - Inno Setup script that creates the Windows installer
- `StartOpenPLC.bat` - Windows launcher script that starts the runtime inside MSYS2
- `PrintHardwareFingerprint.bat` - Prints the 64-hex machine fingerprint for licensing (clients send this to you)
- `provision-msys2.sh` - Script to install packages and configure MSYS2 (used during CI build)

## Building the Installer

### Automated Build (GitHub Actions)

The installer is automatically built by GitHub Actions when:
- A tag starting with `v` is pushed (e.g., `v4.0.0`)
- The workflow is manually triggered via `workflow_dispatch`

The workflow:
1. Sets up MSYS2 on a Windows runner
2. Installs all required packages (GCC, Python, CMake, etc.)
3. Builds the OpenPLC Runtime
4. Creates a Python virtual environment with all dependencies
5. Packages everything into an Inno Setup installer
6. Uploads the installer to GitHub Releases (for tag pushes)

### Manual Build

To build the installer manually on a Windows machine:

1. Install MSYS2 from https://www.msys2.org/
2. Open MSYS2 MSYS terminal and run:
   ```bash
   pacman -Syu --noconfirm
   pacman -S --noconfirm base-devel gcc make cmake pkg-config python python-pip git sqlite3
   ```
3. Clone and build OpenPLC Runtime:
   ```bash
   git clone https://github.com/Autonomy-Logic/openplc-runtime.git
   cd openplc-runtime
   python3 -m venv venvs/runtime
   ./venvs/runtime/bin/python3 -m pip install -r requirements.txt
   ./venvs/runtime/bin/python3 -m pip install -e .
   mkdir build && cd build && cmake .. && make
   ```
4. Install Inno Setup from https://jrsoftware.org/isinfo.php
5. Create the payload directory structure:
   ```
   windows/
     payload/
       msys64/     <- Copy your MSYS2 installation here
       openplc-runtime/  <- Copy the runtime files here
   ```
6. Optional: strip plain `webserver/*.py` from the payload (see **Masking Python source**):
   ```bash
   ./windows/mask_webserver_sources.sh windows/payload/openplc-runtime
   ```
7. Run Inno Setup compiler:
   ```
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" windows\setup.iss
   ```

## Installation

The installer creates a per-user installation (no admin rights required) at:
```
%LOCALAPPDATA%\OpenPLC Runtime\
```

This includes:
- `msys64/` - Complete MSYS2 environment
- `openplc-runtime/` - OpenPLC Runtime files
- `StartOpenPLC.bat` - Launcher script
- `PrintHardwareFingerprint.bat` - License hardware ID helper

## Usage

After installation, users can:
1. Use the Start Menu shortcut "Start OpenPLC Runtime"
2. Or run `StartOpenPLC.bat` directly

The runtime will start and be accessible at https://localhost:8443

**Licensing:** Use the Start Menu entry **Print hardware fingerprint (license)** or run `PrintHardwareFingerprint.bat` in `%LOCALAPPDATA%\OpenPLC Runtime\`. Copy the printed line to your vendor; they return `openplc.license` to place in `openplc-runtime\`.

## Licensing (fork builds)

On Windows (including the MSYS2-backed installer), the runtime **requires a valid license file** before the web server or PLC manager starts. Linux and Docker builds are not gated.

### What gets tied to the machine

The license contains a SHA-256 fingerprint derived from the Windows registry **MachineGuid** and the computer name (`platform.node()`). The customer generates a fingerprint on the target PC; you issue a signed JWT that embeds that fingerprint.

### Files and layout

- **License file (customer):** `openplc.license` in the OpenPLC repository root next to `webserver/` (for the installed layout: `{install}\openplc-runtime\openplc.license`). Override with environment variable `OPENPLC_LICENSE_FILE` if needed.
- **Public key (shipped in the installer):** `webserver/keys/license_public.pem`. Override with `OPENPLC_LICENSE_PUBLIC_KEY`.
- **Private key (vendor only, never ship):** keep offline; use it only with `scripts/issue_windows_license.py`.

### Workflow

1. On the target PC (MSYS2 shell or any suitable Python on that Windows system), run:
   ```bash
   ./venvs/runtime/bin/python3 scripts/print_windows_fingerprint.py
   ```
   Or from a repo checkout without venv, after `pip install -e .` and dependencies.
2. Sign a license with your private key:
   ```bash
   ./venvs/runtime/bin/python3 scripts/issue_windows_license.py \
     --private-key /secure/path/vendor_private.pem \
     --fingerprint <value from step 1> \
     --days 365 \
     --output openplc.license
   ```
3. Place `openplc.license` in the runtime root (`openplc-runtime\` next to `webserver\`, `core\`, etc.).

### Optional expiry

Pass `--days N` when issuing to set JWT `exp`. Omit `--days` (or use `0`) for no expiry field in the token.

### Development bypass

Set `OPENPLC_SKIP_LICENSE_CHECK=1` in the environment to start the runtime on Windows without a license (for internal development only). **Note:** `StartOpenPLC.bat` clears this variable before starting Python so a stray machine-wide setting cannot disable licensing when customers use the shipped shortcut; for local dev, run `python3 -m webserver` from an MSYS shell yourself with the variable set.

### Replacing keys in your fork

Generate an RSA key pair (2048-bit or stronger), install the **public** PEM as `webserver/keys/license_public.pem` in your tree (update `.gitignore` if you use a different path), and use the **private** PEM only with `issue_windows_license.py`. The file committed upstream is a placeholder; you must use your own key pair for customers.

## Hiding webserver source in the installed app

**Preferred:** compile `webserver/` with **Cython** on the payload copy, then strip `.py` files. See [docs/CYTHON.md](../docs/CYTHON.md) (`setup_cython.py`, `scripts/strip_webserver_py_after_cython.py`). Ship the same Python minor version you used to build.

### Bytecode-only masking (lighter obfuscation)

The installer places files under `%LOCALAPPDATA%\OpenPLC Runtime\openplc-runtime\`, which would normally expose plain `webserver/*.py` files.

**What we do:** the Windows installer workflow runs `windows/mask_webserver_sources.sh` on the **payload copy only** (after `install.sh`, before Inno Setup). That script:

1. Byte-compiles everything under `webserver/` into `__pycache__/`
2. Deletes all `*.py` and `*.pyi` there
3. Deletes `*.md` under `webserver/` (docs shipped with the package)

The runtime starts with `./venvs/runtime/bin/python3 -m webserver` (or `-m webserver.app` only when `app` is still plain Python). After Cython, use `-m webserver` only.

**Manual builds:** after you populate `windows/payload/openplc-runtime`, run from the repository root inside MSYS2:

```bash
./windows/mask_webserver_sources.sh windows/payload/openplc-runtime
```

**Important limits (read this):**

- This is **obfuscation**, not encryption. Bytecode can be **decompiled** (e.g. with public tools). It stops casual reading of source in Notepad, not a determined reverse engineer.
- **`core/`** (C/C++ PLC core, plugins), **`scripts/*.sh`**, **`scripts/*.py`**, **`CMakeLists.txt`**, and the rest of the tree are **unchanged**. Only `webserver/` Python sources in the payload are masked. To hide more, remove or mask those paths from the payload (may break features) or move to stronger packagers below.
- The **Python minor version** in the venv must match the one used when compiling; the payload is built in one shot, so this stays consistent.

**Stronger options (vendor-owned tooling, not in-tree):** pack the web stack with **PyInstaller**, **Nuitka**, or a commercial obfuscator (**PyArmor**, etc.) so logic ships as a native binary or encrypted bytecode. That requires a separate build entry point and more testing with Flask-SocketIO and your plugin paths.

## Size Considerations

The installer is large (~500MB-1GB compressed) because it includes:
- Complete MSYS2 environment
- GCC toolchain (needed for compiling PLC programs)
- Python with all dependencies
- OpenPLC Runtime

To reduce size, the build process:
- Cleans pacman package cache
- Removes unnecessary log files
- Excludes test files and development tools

## Troubleshooting

### Runtime fails to start
- Ensure the installation path does not contain spaces
- Try running as administrator if permission issues occur
- Check that antivirus is not blocking MSYS2 executables

### Compilation errors
- The GCC toolchain is bundled with the installer
- If compilation fails, check that the build directory exists

### Socket errors
- The runtime uses Unix domain sockets via MSYS2
- Ensure no other instance is running
- Check that the `/run/runtime` directory exists in MSYS2
