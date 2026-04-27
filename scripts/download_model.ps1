\
param(
    [string]$ModelName = $(if ($env:MODEL_NAME) { $env:MODEL_NAME } else { "Qwen/Qwen3.5-0.8B" }),
    [string]$ModelDir = $(if ($env:MODEL_DIR) { $env:MODEL_DIR } else { "./models/qwen3.5-0.8b" })
)

$ErrorActionPreference = "Stop"

function Find-Python {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) { return "python" }

    $python3 = Get-Command python3 -ErrorAction SilentlyContinue
    if ($python3) { return "python3" }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { return "py -3" }

    return $null
}

$PythonCmd = Find-Python

if (-not $PythonCmd) {
    Write-Host "Could not find Python."
    Write-Host ""
    Write-Host "Install Python 3.10+ from https://www.python.org/downloads/"
    Write-Host "During installation, enable: Add python.exe to PATH"
    Write-Host ""
    Write-Host "Then reopen PowerShell and verify:"
    Write-Host "  python --version"
    Write-Host "or:"
    Write-Host "  py -3 --version"
    exit 1
}

$hf = Get-Command huggingface-cli -ErrorAction SilentlyContinue
if (-not $hf) {
    Write-Host "huggingface-cli not found. Installing huggingface_hub..."
    Invoke-Expression "$PythonCmd -m pip install --upgrade huggingface_hub"
}

New-Item -ItemType Directory -Force -Path $ModelDir | Out-Null

Write-Host "Downloading $ModelName to $ModelDir..."
huggingface-cli download $ModelName `
  --local-dir $ModelDir `
  --local-dir-use-symlinks False

Write-Host "Model downloaded successfully."
