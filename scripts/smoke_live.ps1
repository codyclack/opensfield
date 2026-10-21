# Runs scripts/smoke_cloud.py with the saved key and writes outputs\smoke_summary.txt (read by Claude from your folder).
param([switch]$All)
$ErrorActionPreference = "Continue"
. "$PSScriptRoot\_key.ps1"
Set-Location (Split-Path $PSScriptRoot -Parent)
Set-ComfyKey
New-Item -ItemType Directory -Force outputs | Out-Null
[string[]]$extra = if ($All) { @() } else { @("--skip-slow") }
Write-Host "Running every module once through the app on Comfy Cloud. This takes a while; leave the window open." -ForegroundColor Cyan
uv run --extra comfy scripts/smoke_cloud.py @extra 2>&1 | Tee-Object -FilePath outputs\smoke_summary.txt
Write-Host ""
Write-Host "Finished. You can close this window and tell Claude 'smoke test done'." -ForegroundColor Green
