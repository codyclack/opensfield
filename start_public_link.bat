@echo off
rem Double-click AFTER start_opensfield.bat is running. Makes a public https address for judges.
rem Needs cloudflared (installs it with winget if missing). Keep this window open.
where cloudflared >nul 2>nul
if errorlevel 1 (
  echo Installing cloudflared...
  winget install --id Cloudflare.cloudflared -e --accept-source-agreements --accept-package-agreements
  echo Close this window and double-click start_public_link.bat again.
  pause
  exit /b
)
echo.
echo Look for the line with https://....trycloudflare.com below.
echo Your live link is that address followed by  /?key=  and the phrase in the file .opensfield_access
echo (the phrase is also printed in the OpenSfield window).
echo.
cloudflared tunnel --url http://127.0.0.1:8765
pause
