@echo off
title Odoo Reset Hub - Install
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Python venv not found at %~dp0venv
    pause
    exit /b 1
)
"venv\Scripts\python.exe" setup_host.py install
echo.
echo Done. Now load the "extension" folder in chrome://extensions (Developer mode ^> Load unpacked).
echo You never need to run anything again - the extension starts the helper by itself.
pause
