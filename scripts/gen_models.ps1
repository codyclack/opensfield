# Generates the partner-model tools (see scripts/gen_models.py). Uses the saved Comfy key; reads Cloud's node catalog.
param([string]$Only = "")
. "$PSScriptRoot\_key.ps1"
Set-Location (Split-Path $PSScriptRoot -Parent)
Set-ComfyKey
New-Item -ItemType Directory -Force outputs | Out-Null
$extra = @(); if ($Only) { $extra = @("--only", $Only) }
uv run --with comfy-cli scripts/gen_models.py @extra 2>&1 | Tee-Object -FilePath outputs\gen_models.txt
