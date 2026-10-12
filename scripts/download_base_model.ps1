$ErrorActionPreference = "Stop"
$packageRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $packageRoot "project\app\backend\.venv-local\Scripts\python.exe"
$modelDir = Join-Path $packageRoot "models\Qwen3-VL-4B-Instruct"

if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw "Local environment not found. Run scripts\setup_local.ps1 first."
}
& $pythonExe (Join-Path $PSScriptRoot "download_base_model.py") --target $modelDir

