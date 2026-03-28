@echo off
title Remote Monitoring Tool - CyberSec Suite
color 0F

:menu
cls
echo ============================================================
echo         CYBERSEC REMOTE MONITORING TOOL SUITE
echo ============================================================
echo.
echo Main Menu:
echo ============================================================
echo [1] Start Server
echo [2] Connect Client
echo [3] Start Both (Server + Client)
echo [4] Check Python Installation
echo [5] Test Windows Authentication
echo [6] View Server Logs
echo [7] Exit
echo ============================================================
echo.
set /p choice="Select option (1-7): "

if "%choice%"=="1" goto start_server
if "%choice%"=="2" goto start_client
if "%choice%"=="3" goto start_both
if "%choice%"=="4" goto check_python
if "%choice%"=="5" goto test_auth
if "%choice%"=="6" goto view_logs
if "%choice%"=="7" goto exit
goto menu

:start_server
cls
echo Starting Server...
start "Remote Server" cmd /k "cd server && Start_Server.bat"
echo Server started in new window!
echo.
pause
goto menu

:start_client
cls
echo Starting Client...
start "Remote Client" cmd /k "cd client && Connect_Client.bat"
echo Client started in new window!
echo.
pause
goto menu

:start_both
cls
echo Starting both Server and Client...
echo.
start "Remote Server" cmd /k "cd server && Start_Server.bat"
timeout /t 2 >nul
start "Remote Client" cmd /k "cd client && Connect_Client.bat"
echo Both started in separate windows!
echo.
pause
goto menu

:check_python
cls
echo ============================================================
echo           CHECKING PYTHON INSTALLATION
echo ============================================================
echo.
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo [✓] Python is installed:
    python --version
    echo.
    echo Python Path:
    where python
) else (
    echo [✗] Python is NOT installed!
    echo.
    echo Please download and install Python from:
    echo https://www.python.org/downloads/
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
echo This will test if your Windows credentials work with the system.
echo.
for /f "tokens=2 delims=\" %%i in ('whoami') do set current_user=%%i
echo Current Windows User: %current_user%
echo.
set /p test_user="Enter username to test (press Enter for %current_user%): "
if "%test_user%"=="" set test_user=%current_user%
echo.
python -c "from server.windows_auth import authenticate_windows; import getpass; pwd=getpass.getpass('Password: '); print('\n✓ SUCCESS! You can login with this username!' if authenticate_windows('%test_user%', pwd) else '\n✗ FAILED! Check your username and password.')"
echo.
pause
goto menu

:view_logs
cls
echo ============================================================
echo           SERVER LOGS
echo ============================================================
echo.
if exist "server\logs.txt" (
    type server\logs.txt
) else (
    echo No logs found yet. Start the server first.
)
echo.
pause
goto menu

:exit
cls
echo.
echo Thank you for using Remote Monitoring Tool!
echo.
timeout /t 2 >nul
exit /b 0