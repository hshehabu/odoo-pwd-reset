@echo off
title Odoo Reset Hub - Uninstall
cd /d "%~dp0"
"venv\Scripts\python.exe" setup_host.py uninstall
pause
