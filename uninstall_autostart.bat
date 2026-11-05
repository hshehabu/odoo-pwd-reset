@echo off
title Uninstall Odoo Reset Service Autostart
set "TARGET_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%TARGET_DIR%\OdooPasswordResetService.lnk"

if exist "%SHORTCUT_PATH%" (
    del "%SHORTCUT_PATH%"
    echo [OK] Removed startup shortcut from Windows Startup.
) else (
    echo [INFO] Startup shortcut does not exist.
)

call "%~dp0stop_server.bat"
pause

