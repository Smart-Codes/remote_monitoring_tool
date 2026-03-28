@echo off
title Remote Monitoring Tool - Setup
color 0A

cls
echo ============================================================
echo         REMOTE MONITORING TOOL - SETUP
echo ============================================================
echo.
echo This will prepare your system to run the tool.
echo.
echo Checking Python installation...
echo.

:: Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [✗] Python is not installed!
    echo.
    echo Please install Python first:
    echo 1. Go to https://www.python.org/downloads/
    echo 2. Download Python 3.7 or higher
    echo 3. During installation, CHECK "Add Python to PATH"
    echo 4. Restart your computer after installation
    echo.
    pause
    exit /b 1
) else (
    echo [✓] Python is installed
    python --version
)

:: Install required packages
echo.
echo Installing required Python packages...
pip install --upgrade pip
echo.
echo [✓] Setup complete!
echo.
echo You can now run the tool using:
echo   - Run_Tool.bat (Main menu)
echo   - server\Start_Server.bat (Start server only)
echo   - client\Connect_Client.bat (Connect client only)
echo.
pause