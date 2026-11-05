@echo off
title Install Odoo Reset Service Autostart
cd /d "%~dp0"

set "TARGET_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%TARGET_DIR%\OdooPasswordResetService.lnk"
set "SCRIPT_PATH=%~dp0start_background.vbs"

echo Creating startup shortcut...
powershell -NoProfile -Command ^
    "$w=New-Object -ComObject WScript.Shell; " ^
    "$s=$w.CreateShortcut('%SHORTCUT_PATH%'); " ^
    "$s.TargetPath='wscript.exe'; " ^
    "$s.Arguments='\"%SCRIPT_PATH%\"'; " ^
    "$s.WorkingDirectory='%~dp0'; " ^
    "$s.Save()"

if exist "%SHORTCUT_PATH%" (
    echo [OK] Odoo Reset Service has been added to Windows Startup.
    echo The service will start silently in the background whenever Windows boots.
    echo Starting the service now...
    wscript.exe "%SCRIPT_PATH%"
) else (
    echo [ERROR] Failed to create shortcut in %TARGET_DIR%
)

pause
