$ErrorActionPreference = "Stop"
$packageRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $packageRoot "project\app\backend"
$venvDir = Join-Path $backendDir ".venv-local"
$pythonExe = Join-Path $venvDir "Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonExe)) {
    python -m venv $venvDir
}
& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install -r (Join-Path $backendDir "requirements.txt")
& $pythonExe -m pip install modelscope

Write-Host "Local environment setup completed."
Write-Host "Next run scripts\download_base_model.ps1, then scripts\start_local_backend.ps1"

