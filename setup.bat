@echo off
echo ============================================
echo    UFI SMS Commander - Windows Installer
echo ============================================
echo.

echo Checking for Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ============================================
echo    Installation Complete!
echo ============================================
echo.
echo To run:
echo   python sms_manager.py
echo.
echo Or create a shortcut to sms_manager.py
echo.
pause
