@echo off
rem Double-click: converts video outpaint + text-to-speech templates against Comfy Cloud and saves outputs\export_summary.txt
cd /d "%~dp0"
powershell -NoLogo -NoExit -ExecutionPolicy Bypass -File "%~dp0scripts\export_live.ps1"

