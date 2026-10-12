$ErrorActionPreference = "Stop"
$packageRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $packageRoot "project\app\backend"
$pythonExe = Join-Path $backendDir ".venv-submission\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw "API environment not found. Run scripts\setup_api.ps1 first."
}
if (-not $env:CHEM_API_KEY) {
    throw "CHEM_API_KEY is not set. Configure it in the current terminal without writing it into the project."
}

$env:CHEM_BACKEND = "api"
if (-not $env:CHEM_API_BASE) {
    $env:CHEM_API_BASE = "https://api-inference.modelscope.cn/v1/chat/completions"
}
if (-not $env:CHEM_API_MODEL) {
    $env:CHEM_API_MODEL = "Qwen/Qwen3-VL-4B-Instruct"
}

Push-Location $backendDir
try {
    & $pythonExe -m uvicorn src.web.app:app --host 127.0.0.1 --port 8001
} finally {
    Pop-Location
}

