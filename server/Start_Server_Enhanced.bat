@echo off
title Remote Monitoring Server - CyberSec Tool
color 0A

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
    echo IMPORTANT: During installation, check:
    echo "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

:: Main menu
:menu
cls
echo ============================================================
echo           CYBERSEC REMOTE MONITORING SERVER
echo ============================================================
echo.
echo Server Configuration:
echo --------------------
echo Host: 127.0.0.1
echo Port: 5000
echo Auth: Windows Credentials
echo.
echo Options:
echo [1] Start Server (Normal Mode)
echo [2] Start Server (Debug Mode)
echo [3] View Logs
echo [4] Clear Logs
echo [5] Test Windows Authentication
echo [6] Exit
echo.
set /p choice="Select option (1-6): "

if "%choice%"=="1" goto start_normal
if "%choice%"=="2" goto start_debug
if "%choice%"=="3" goto view_logs
if "%choice%"=="4" goto clear_logs
if "%choice%"=="5" goto test_auth
if "%choice%"=="6" goto exit
goto menu

:start_normal
cls
echo ============================================================
echo           STARTING SERVER (NORMAL MODE)
echo ============================================================
echo.
echo [INFO] Opening website in background...
start "" "https://test.com"
echo [INFO] Server will run in this window
echo [INFO] Press Ctrl+C to stop
echo ============================================================
echo.
python server.py
pause
goto menu

:start_debug
cls
echo ============================================================
echo           STARTING SERVER (DEBUG MODE)
echo ============================================================
echo.
echo [INFO] Opening website in background...
start "" "https://test.com"
echo [INFO] Debug mode enabled - showing detailed logs
echo ============================================================
echo.
python -c "import sys; sys.argv=['server.py']; exec(open('server.py').read())"
pause
goto menu

:view_logs
cls
echo ============================================================
echo                  SERVER LOGS
echo ============================================================
echo.
if exist "logs.txt" (
    type logs.txt
    echo.
    echo ============================================================
    echo End of logs
) else (
    echo No logs found yet.
)
echo.
pause
goto menu

:clear_logs
cls
echo ============================================================
echo                  CLEAR LOGS
echo ============================================================
echo.
if exist "logs.txt" (
    del logs.txt
    echo [OK] Logs cleared successfully!
) else (
    echo No logs to clear.
)
echo.
pause
goto menu

:test_auth
cls
echo ============================================================
echo           TEST WINDOWS AUTHENTICATION
echo ============================================================
echo.
echo This will test if your Windows credentials work.
echo.
set /p test_user="Enter username to test (or press Enter for current user): "
if "%test_user%"=="" (
    for /f "tokens=2 delims=\" %%i in ('whoami') do set test_user=%%i
    echo Using current user: %test_user%
)
echo.
python -c "from windows_auth import authenticate_windows; import getpass; user='%test_user%'; pwd=getpass.getpass('Enter password: '); result=authenticate_windows(user, pwd); print('\n✅ SUCCESS!' if result else '\n❌ FAILED!')"
echo.
pause
goto menu

:exit
echo.
echo Goodbye!
timeout /t 2 >nul
exit /b 0