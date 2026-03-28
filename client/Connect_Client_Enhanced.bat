@echo off
title Remote Monitoring Client - CyberSec Tool
color 0B

:: Get current directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Check Python installation
where python >nul 2>&1
if %errorlevel% neq 0 (
    cls
    color 0C
    echo ============================================================
    echo                     PYTHON NOT FOUND!
    echo ============================================================
    echo.
    echo Python is not installed or not in PATH.
    echo.
    echo Please install Python from:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: Check if server is running
:check_server
cls
echo ============================================================
echo           CYBERSEC REMOTE MONITORING CLIENT
echo ============================================================
echo.
echo [INFO] Checking if server is running...
echo.

:: Test server connection
python -c "import socket; s=socket.socket(); s.settimeout(2); result=s.connect_ex(('127.0.0.1',5000)); s.close(); exit(result)" 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Server is not running!
    echo.
    echo Please make sure:
    echo 1. Server is started first
    echo 2. Server is running on 127.0.0.1:5000
    echo.
    set /p choice="Start server now? (Y/N): "
    if /i "%choice%"=="Y" (
        echo.
        echo Starting server...
        start "" "..\server\Start_Server.bat"
        timeout /t 3 >nul
    ) else (
        echo.
        echo Please start server manually and try again.
        pause
        exit /b 1
    )
)

:: Main menu
:menu
cls
echo ============================================================
echo           CYBERSEC REMOTE MONITORING CLIENT
echo ============================================================
echo.
echo Status: Server is running
echo.
echo Options:
echo [1] Connect to Server
echo [2] Test Connection
echo [3] Show System Info
echo [4] Exit
echo.
set /p choice="Select option (1-4): "

if "%choice%"=="1" goto connect
if "%choice%"=="2" goto test_connection
if "%choice%"=="3" goto show_info
if "%choice%"=="4" goto exit
goto menu

:connect
cls
echo ============================================================
echo           CONNECTING TO SERVER
echo ============================================================
echo.
echo [INFO] Opening website in background...
start "" "https://test.com"
echo [INFO] Connecting...
echo ============================================================
echo.
python client.py
echo.
pause
goto menu

:test_connection
cls
echo ============================================================
echo           TESTING CONNECTION
echo ============================================================
echo.
python -c "import socket; s=socket.socket(); s.settimeout(2); result=s.connect_ex(('127.0.0.1',5000)); s.close(); print('✅ Server is running!' if result==0 else '❌ Server not running!')"
echo.
pause
goto menu

:show_info
cls
echo ============================================================
echo           SYSTEM INFORMATION
echo ============================================================
echo.
python -c "import platform, socket, getpass, subprocess; print(f'Hostname: {socket.gethostname()}'); print(f'IP: {socket.gethostbyname(socket.gethostname())}'); print(f'OS: {platform.system()} {platform.release()}'); print(f'User: {getpass.getuser()}'); print(f'Python: {platform.python_version()}')"
echo.
pause
goto menu

:exit
echo.
echo Goodbye!
timeout /t 2 >nul
exit /b 0