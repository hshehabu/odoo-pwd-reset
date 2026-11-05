@echo off
title Odoo Password Reset Service
cd /d "%~dp0"

echo =======================================================
echo    Starting Odoo Password Reset Local Service (v16-v19)
echo =======================================================

if not exist "venv\Scripts\python.exe" (
    echo Error: Python virtual environment not found in .\venv
    echo Please ensure venv is installed.
    pause
    exit /b 1
)

"venv\Scripts\python.exe" server.py
pause

