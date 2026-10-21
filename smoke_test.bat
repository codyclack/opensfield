@echo off
rem Double-click: runs the fast modules once each on Comfy Cloud and saves outputs\smoke_summary.txt
cd /d "%~dp0"
powershell -NoLogo -NoExit -ExecutionPolicy Bypass -File "%~dp0scripts\smoke_live.ps1"

