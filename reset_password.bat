@echo off
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
    echo Error: Virtual environment not found in .\venv
    pause
    exit /b 1
)

start "" http://127.0.0.1:1111
"venv\Scripts\python.exe" server.py
pause
