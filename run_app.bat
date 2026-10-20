@echo off
title Predictive Maintenance Multi-Agent Suite
echo =========================================================================
echo   STARTING PREDICTIVE MAINTENANCE MULTI-AGENT INTERACTIVE APP
echo =========================================================================
echo.
cd /d "%~dp0"

if exist .venv\Scripts\python.exe (
    echo [*] Launching FastAPI backend and opening browser...
    .venv\Scripts\python.exe app.py
) else (
    echo [*] Virtual environment not found, falling back to system python...
    python app.py
)

pause
