@echo off
REM Prints the machine hardware fingerprint (SHA-256 hex) for OpenPLC Runtime licensing.
REM Send this single line to your vendor; they return an openplc.license file for this PC.

setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "MSYS2_ROOT=%SCRIPT_DIR%\msys64"

if not exist "%MSYS2_ROOT%\usr\bin\bash.exe" (
    echo ERROR: MSYS2 not found at %MSYS2_ROOT%
    echo Reinstall OpenPLC Runtime or run this batch from the install folder (next to msys64).
    pause
    exit /b 1
)

set "CHERE_INVOKING=1"
set "MSYSTEM=MSYS"
set "HOME=/home/openplc"

set "OPENPLC_WIN_PATH=%SCRIPT_DIR%\openplc-runtime"
set "OPENPLC_MSYS_PATH=%OPENPLC_WIN_PATH:\=/%"
set "OPENPLC_MSYS_PATH=%OPENPLC_MSYS_PATH:C:=/c%"
set "OPENPLC_MSYS_PATH=%OPENPLC_MSYS_PATH:D:=/d%"
set "OPENPLC_MSYS_PATH=%OPENPLC_MSYS_PATH:E:=/e%"

echo.
echo ==========================================
echo OpenPLC Runtime - License hardware ID
echo ==========================================
echo.
echo Copy the line below (64 hex characters) and send it to your vendor.
echo They will send you an openplc.license file. Place it in:
echo   %OPENPLC_WIN_PATH%
echo (same folder as core, webserver, venvs).
echo.

"%MSYS2_ROOT%\usr\bin\bash.exe" -lc "cd '%OPENPLC_MSYS_PATH%' && ./venvs/runtime/bin/python3 scripts/print_windows_fingerprint.py"
set "FP_ERR=%ERRORLEVEL%"

echo.
if %FP_ERR% neq 0 (
    echo ERROR: Could not read fingerprint (code %FP_ERR%).
) else (
    echo ---
    echo Done.
)
pause
endlocal
