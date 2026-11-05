@echo off
title Stop Odoo Password Reset Service
echo Stopping Odoo Password Reset Service on port 1111...

powershell -Command "Get-NetTCPConnection -LocalPort 1111 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host 'Stopped PID:' $_.OwningProcess }"

echo Done. Odoo Reset Service stopped.
timeout /t 2 >nul
