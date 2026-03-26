@echo off
echo ============================================
echo   Building Quietum — Calm Daily Planner
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Download from https://python.org
    pause
    exit /b 1
)

:: Install dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet

:: Build with PyInstaller
echo.
echo Building executable...
pyinstaller --onefile --windowed --name Quietum --clean main.py

echo.
echo ============================================
echo   Build complete!
echo   Executable: dist\Quietum.exe
echo ============================================
pause
