@echo off
title Remote Monitoring Server - CyberSec Tool
color 0A

:: Check if running as administrator (optional)
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] Running without administrator privileges
    echo Some features may be limited
    echo.
)

:: Clear screen and show banner
cls
echo ============================================================
echo           CYBERSEC REMOTE MONITORING SERVER
echo ============================================================
echo.
echo [INFO] Starting server...
echo [INFO] Opening website in background...
echo [INFO] Press Ctrl+C to stop the server
echo ============================================================
echo.

:: Open website in background
start "" "https://test.com"

:: Change to server directory
cd /d "%~dp0"

:: Check if Python is installed
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed!
    echo.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

:: Display Python version
echo [OK] Python found: 
python --version
echo.

:: Run the server
echo [RUNNING] Starting server...
echo.
python server.py

:: If server stops, pause to show error
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Server stopped with error code: %errorlevel%
    echo.
    pause
)