$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$root = Get-Location

$activate = Join-Path $root ".venv\Scripts\Activate.ps1"
if (Test-Path $activate) {
    . $activate
}

if ($env:OBSIDIAN_LOCAL_VAULT_PATH) {
    $env:VAULT_PATH = $env:OBSIDIAN_LOCAL_VAULT_PATH
}

uvicorn app.chatgpt_main:app --host 127.0.0.1 --port 8001 --reload
