param(
  [string]$ProjectRoot
)

$ErrorActionPreference = "Stop"
if (-not $ProjectRoot) {
  $ProjectRoot = Split-Path -Parent $PSCommandPath
}
$ProjectRoot = (Resolve-Path $ProjectRoot).Path
Write-Host "[1/8] Project root: $ProjectRoot"
Set-Location $ProjectRoot

if (-not (Test-Path .venv)) {
  Write-Host "[2/8] Creating virtual environment"
  python -m venv .venv
}

Write-Host "[3/8] Activating virtual environment"
& .\.venv\Scripts\Activate.ps1

Write-Host "[4/8] Installing dependencies"
python -m pip install --upgrade pip
pip install -e .[dev]

if (-not (Test-Path .env)) {
  Write-Host "[5/8] Creating .env from .env.example"
  Copy-Item .env.example .env
}

Write-Host "[6/8] Ensuring project Cursor MCP config exists"
if (-not (Test-Path ".cursor\mcp.json")) {
  Copy-Item ".cursor\mcp.sample.json" ".cursor\mcp.json"
}

Write-Host "[7/8] Ensuring git repository exists"
if (-not (Test-Path .git)) {
  git init -b main
}

Write-Host "[8/8] Installing pre-commit hooks"
python -m pre_commit install

Write-Host "Setup complete. Open this folder in Cursor and start with plan mode for contract-sensitive edits."
Write-Host "Cursor MCP: this repo now seeds .cursor\\mcp.json from .cursor\\mcp.sample.json."
Write-Host "Set MCP_API_TOKEN and MCP_PRODUCTION_BEARER_TOKEN in your user/shell environment, then restart Cursor."
