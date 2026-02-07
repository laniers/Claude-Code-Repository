@echo off
title Street View Scraper - Setup
echo.
echo  ================================
echo   Street View Scraper - Starting
echo  ================================
echo.

:: Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  Python is not installed!
    echo  Download it from: https://www.python.org/downloads/
    echo  IMPORTANT: Check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

:: Install dependencies
echo  Installing dependencies...
python -m pip install -q -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo  Failed to install dependencies.
    pause
    exit /b 1
)

echo  Starting...
echo.

:: Launch the GUI
python -m streetview_scraper.launcher

pause
