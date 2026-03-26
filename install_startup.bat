@echo off
echo ============================================
echo   Quietum — Enable Startup on Boot
echo ============================================
echo.

:: Determine the path to the executable or script
set "APP_PATH=%~dp0dist\Quietum.exe"

if not exist "%APP_PATH%" (
    echo [INFO] Quietum.exe not found in dist\
    echo        Using Python script fallback...
    set "APP_PATH=pythonw %~dp0main.py --minimized"
)

:: Add to registry
echo Adding Quietum to Windows startup...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v Quietum /t REG_SZ /d "\"%APP_PATH%\" --minimized" /f

if errorlevel 1 (
    echo [ERROR] Failed to add to startup.
) else (
    echo [OK] Quietum will now start with Windows.
    echo      It will launch minimized in the background.
)

echo.
pause
