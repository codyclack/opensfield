# Starts OpenSfield in real (Comfy Cloud) mode. Double-click start_opensfield.bat instead of running this by hand.
#   - frees port 8765 if an old copy is still running
#   - asks for your Comfy API key the first time, then remembers it ENCRYPTED for your Windows user (.opensfield_key.enc, git-ignored)
#   - makes (and remembers) a random access phrase for the live link (.opensfield_access, git-ignored)
#   - starts the app and opens your browser
param([switch]$NoBrowser, [int]$Port = 8765)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | ForEach-Object {
    try { Stop-Process -Id $_.OwningProcess -Force; Write-Host "Stopped an old copy that was using port $Port." } catch { Write-Host "Could not stop the old copy: $($_.Exception.Message)" -ForegroundColor Yellow }
}

if (-not $env:COMFY_API_KEY) {
    $enc = ".opensfield_key.enc"
    if (Test-Path $enc) {
        $sec = Get-Content $enc | ConvertTo-SecureString
    } else {
        Write-Host "Paste your Comfy API key (it stays hidden) and press Enter. It is saved encrypted on this computer only." -ForegroundColor Cyan
        $sec = Read-Host "Comfy API key" -AsSecureString
        $sec | ConvertFrom-SecureString | Set-Content $enc
    }
    $env:COMFY_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
}

$accessFile = ".opensfield_access"
if (-not (Test-Path $accessFile)) {
    (-join ((48..57) + (97..122) | Get-Random -Count 28 | ForEach-Object { [char]$_ })) | Set-Content $accessFile
}
$phrase = (Get-Content $accessFile -Raw).Trim()

$env:OPENSFIELD_MODE = "comfy"
$env:OPENSFIELD_ACCESS_KEY = $phrase
if (-not $env:OPENSFIELD_MAX_JOBS) { $env:OPENSFIELD_MAX_JOBS = "60" }
$url = "http://127.0.0.1:$Port/?key=$phrase"
Write-Host ""
Write-Host "OpenSfield is starting. Your local link (also the access phrase for the public link):" -ForegroundColor Green
Write-Host $url
Write-Host "Keep this window open while you use it. Close it (or press Ctrl+C) to stop."
Write-Host ""
if (-not $NoBrowser) {
    Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoProfile", "-Command", "Start-Sleep 12; Start-Process '$url'"
}
uv run --extra comfy --extra fx uvicorn app.main:app --port $Port
