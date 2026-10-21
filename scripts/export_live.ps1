# Converts the two blocked templates (video outpaint, text-to-speech) to API format against Comfy Cloud's node catalog.
. "$PSScriptRoot\_key.ps1"
Set-Location (Split-Path $PSScriptRoot -Parent)
Set-ComfyKey
New-Item -ItemType Directory -Force outputs | Out-Null
uv run --with comfy-cli scripts/export_api.py --base https://cloud.comfy.org video.reframe audio.tts 2>&1 | Tee-Object -FilePath outputs\export_summary.txt
Write-Host ""
Write-Host "Finished. You can close this window and tell Claude 'export done'." -ForegroundColor Green
