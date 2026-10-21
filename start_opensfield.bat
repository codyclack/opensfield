@echo off
rem Double-click to start OpenSfield (real mode, Comfy Cloud). See scripts\start_live.ps1.
cd /d "%~dp0"
powershell -NoLogo -NoExit -ExecutionPolicy Bypass -File "%~dp0scripts\start_live.ps1"
