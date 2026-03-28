param(
  [string]$ProjectRoot
)

$ErrorActionPreference = "Stop"
if (-not $ProjectRoot) {
  $ProjectRoot = Split-Path -Parent $PSCommandPath
}
$ProjectRoot = (Resolve-Path $ProjectRoot).Path
Write-Host "[1/7] Project root: $ProjectRoot"
Set-Location $ProjectRoot

if (-not (Test-Path .venv)) {
  Write-Host "[2/7] Creating virtual environment"
  python -m venv .venv
}

Write-Host "[3/7] Activating virtual environment"
& .\.venv\Scripts\Activate.ps1

Write-Host "[4/7] Installing dependencies"
python -m pip install --upgrade pip
pip install -e .[dev]

if (-not (Test-Path .env)) {
  Write-Host "[5/7] Creating .env from .env.example"
  Copy-Item .env.example .env
}

Write-Host "[6/7] Ensuring git repository exists"
if (-not (Test-Path .git)) {
  git init -b main
}

Write-Host "[7/7] Installing pre-commit hooks"
python -m pre_commit install

Write-Host "Setup complete. Open the folder in Cursor and start with plan mode for contract-sensitive edits."
Write-Host "Cursor MCP: set Windows user/shell env var MCP_API_TOKEN to match .env, then restart Cursor. See README.md (Cursor MCP)."
