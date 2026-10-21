param([string]$Only)
. "$PSScriptRoot\_key.ps1"
Set-Location (Split-Path $PSScriptRoot -Parent)
Set-ComfyKey
uv run --extra comfy scripts/smoke_cloud.py --only $Only 2>&1 | Tee-Object -FilePath outputs\only_summary.txt
