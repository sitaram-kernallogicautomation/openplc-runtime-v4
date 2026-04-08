@echo off
REM Prints the machine hardware fingerprint (SHA-256 hex) for OpenPLC Runtime licensing.

setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "MSYS2_ROOT=%SCRIPT_DIR%\msys64"
set "OPENPLC_WIN_PATH=%SCRIPT_DIR%\openplc-runtime"
set "HELPER_SH=%OPENPLC_WIN_PATH%\scripts\print_fingerprint_msys.sh"

if not exist "%MSYS2_ROOT%\usr\bin\bash.exe" (
    echo ERROR: MSYS2 not found at %MSYS2_ROOT%
    echo Run this from the OpenPLC install folder (next to msys64).
    goto :end_pause
)

if not exist "%HELPER_SH%" (
    echo ERROR: Missing %HELPER_SH%
    echo Reinstall or copy scripts\print_fingerprint_msys.sh into openplc-runtime\scripts\
    goto :end_pause
)

echo.
echo ==========================================
echo OpenPLC Runtime - License hardware ID
echo ==========================================
echo Copy the one line below (64 hex chars) to your vendor for openplc.license
echo.
echo ----- fingerprint -----

REM No "login" shell: some profiles exit immediately and close the window.
"%MSYS2_ROOT%\usr\bin\bash.exe" "%HELPER_SH%"
set "FP_ERR=!ERRORLEVEL!"

echo ----- end -----
echo.

if not "!FP_ERR!"=="0" (
    echo ERROR: exit code !FP_ERR!
    echo Check that venvs\runtime exists and scripts\print_windows_fingerprint.py is present.
)

:end_pause
pause
endlocal
