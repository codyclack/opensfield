@echo off
rem Double-click: runs ALL modules incl. the slow video ones (takes longer, more credits)
cd /d "%~dp0"
powershell -NoLogo -NoExit -ExecutionPolicy Bypass -File "%~dp0scripts\smoke_live.ps1" -All

