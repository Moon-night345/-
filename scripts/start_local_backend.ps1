$ErrorActionPreference = "Stop"
$packageRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $packageRoot "project\app\backend"
$pythonExe = Join-Path $backendDir ".venv-local\Scripts\python.exe"
$modelDir = Join-Path $packageRoot "models\Qwen3-VL-4B-Instruct"
$adapterDir = Join-Path $packageRoot "model_adapter"

if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw "Local environment not found. Run scripts\setup_local.ps1 first."
}
if (-not (Test-Path -LiteralPath (Join-Path $modelDir "config.json"))) {
    throw "Base model not found. Run scripts\download_base_model.ps1 first."
}

$env:CHEM_BACKEND = "local"
$env:CHEM_MODEL_PATH = $modelDir
$env:CHEM_ADAPTER = $adapterDir
$env:CHEM_QUANT = "4bit"

Push-Location $backendDir
try {
    & $pythonExe -m uvicorn src.web.app:app --host 127.0.0.1 --port 8001
} finally {
    Pop-Location
}

