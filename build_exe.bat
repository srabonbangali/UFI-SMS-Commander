@echo off
echo ============================================
echo    Building UFI SMS Commander .exe
echo ============================================
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Install PyInstaller if not installed
echo Installing PyInstaller...
pip install pyinstaller --upgrade

if errorlevel 1 (
    echo [ERROR] Failed to install PyInstaller
    pause
    exit /b 1
)

REM Build the executable
echo.
echo Building executable...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name="UFI-SMS-Commander" ^
    --icon="icon.ico" ^
    --add-data="docs;docs" ^
    --hidden-import=PyQt6 ^
    --hidden-import=requests ^
    --clean ^
    sms_manager.py

if errorlevel 1 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ============================================
echo    Build Complete!
echo ============================================
echo.
echo Executable created at: dist\UFI-SMS-Commander.exe
echo.
echo To run: double-click UFI-SMS-Commander.exe
echo.
pause
