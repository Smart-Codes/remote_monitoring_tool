@echo off
title Remote Monitoring Client - CyberSec Tool
color 0B

:: Clear screen and show banner
cls
echo ============================================================
echo           CYBERSEC REMOTE MONITORING CLIENT
echo ============================================================
echo.
echo [INFO] Connecting to server...
echo [INFO] Opening website in background...
echo ============================================================
echo.

:: Open website in background
start "" "https://test.com"

:: Change to client directory
cd /d "%~dp0"

:: Check if Python is installed
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed!
    echo.
    echo Please install Python from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: Display Python version
echo [OK] Python found:
python --version
echo.

:: Run the client
echo [RUNNING] Connecting to server...
echo.
python client.py

:: If client stops, pause to show error
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Client stopped with error code: %errorlevel%
    echo.
    pause
)