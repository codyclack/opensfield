# Shared helper: sets $env:COMFY_API_KEY from the encrypted copy saved by start_opensfield.bat (prompts once if there is none).
function Set-ComfyKey {
    if ($env:COMFY_API_KEY) { return }
    $enc = Join-Path (Split-Path $PSScriptRoot -Parent) ".opensfield_key.enc"
    if (Test-Path $enc) {
        $sec = Get-Content $enc | ConvertTo-SecureString
    } else {
        Write-Host "Paste your Comfy API key (it stays hidden) and press Enter. It is saved encrypted on this computer only." -ForegroundColor Cyan
        $sec = Read-Host "Comfy API key" -AsSecureString
        $sec | ConvertFrom-SecureString | Set-Content $enc
    }
    $env:COMFY_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
}
