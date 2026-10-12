$ErrorActionPreference = "Stop"
$packageRoot = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $packageRoot "project\app\frontend"

Push-Location $frontendDir
try {
    npm run dev
} finally {
    Pop-Location
}

