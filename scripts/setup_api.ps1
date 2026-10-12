$ErrorActionPreference = "Stop"
$packageRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $packageRoot "project\app\backend"
$frontendDir = Join-Path $packageRoot "project\app\frontend"
$venvDir = Join-Path $backendDir ".venv-submission"
$pythonExe = Join-Path $venvDir "Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonExe)) {
    python -m venv $venvDir
}
& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install -r (Join-Path $backendDir "requirements-api.txt")

Push-Location $frontendDir
try {
    npm ci
} finally {
    Pop-Location
}

Write-Host "API mode setup completed."
Write-Host "Set CHEM_API_KEY, then run scripts\start_api_backend.ps1 and scripts\start_frontend.ps1"

