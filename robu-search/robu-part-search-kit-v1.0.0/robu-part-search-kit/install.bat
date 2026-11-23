@echo off
setlocal
cd /d "%~dp0"
rem Use a clean Windows PowerShell module path so a PowerShell 7 parent
rem session cannot break 5.1 module auto-loading.
set "PSModulePath=%ProgramFiles%\WindowsPowerShell\Modules;%SystemRoot%\System32\WindowsPowerShell\v1.0\Modules"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" (
    echo Installation finished with errors ^(exit code %RC%^).
    echo See README.md for troubleshooting.
) else (
    echo Installation complete.
)
if "%~1"=="" pause
exit /b %RC%
