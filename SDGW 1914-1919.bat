@echo off
REM Windows launcher for SDGW 1914-1919.
REM Double-click this file (or a shortcut to it) to open the app window.
REM Closing the window stops the embedded Flask server.

setlocal
cd /d "%~dp0"

where pythonw >nul 2>nul
if errorlevel 1 (
    msg * "Python 3 is required but was not found. Please install Python 3 from python.org and try again."
    exit /b 1
)

start "" pythonw launcher.py
endlocal
