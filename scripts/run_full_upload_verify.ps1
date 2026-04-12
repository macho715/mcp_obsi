# Full batch: repo vault → destination Obsidian vault, .env align, layout, Ollama, MCP smoke, pytest, Cursor check.
# Aligns with obsidian-ingest (paths) + AGENTS vault contract. Optional: --IngestFile for new KB file.
param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$DestinationVault = "C:\Users\jichu\Downloads\valut",
    [string]$IngestFile = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path $ProjectRoot).Path
$SrcVault = Join-Path $ProjectRoot "vault"
$SrcDb = Join-Path $ProjectRoot "data\memory_index.sqlite3"
$DstData = Join-Path $DestinationVault "data"
$DstDb = Join-Path $DstData "memory_index.sqlite3"
$Py = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

function Step($name, [scriptblock]$action) {
    Write-Host "`n=== $name ==="
    & $action
}

if (-not (Test-Path -LiteralPath $Py)) {
    Write-Error "Missing venv: $Py"
    exit 1
}

Step "1. Robocopy repo/vault → destination" {
    New-Item -ItemType Directory -Force -Path $DestinationVault | Out-Null
    $null = robocopy $SrcVault $DestinationVault /E /XD .git /NFL /NDL /NJH /NJS
    if ($LASTEXITCODE -ge 8) { throw "robocopy failed: $LASTEXITCODE" }
}

Step "2. SQLite index copy" {
    New-Item -ItemType Directory -Force -Path $DstData | Out-Null
    if (Test-Path -LiteralPath $SrcDb) {
        Copy-Item -LiteralPath $SrcDb -Destination $DstDb -Force
    } else {
        Write-Warning "No source DB at $SrcDb (destination may reindex on first use)"
    }
}

Step "3. Patch .env (VAULT_PATH, INDEX_DB_PATH, OBSIDIAN_LOCAL_VAULT_PATH)" {
    $envPath = Join-Path $ProjectRoot ".env"
    if (-not (Test-Path -LiteralPath $envPath)) {
        Copy-Item (Join-Path $ProjectRoot ".env.example") $envPath
    }
    $utf8 = [System.Text.UTF8Encoding]::new($false)
    $lines = [System.IO.File]::ReadAllLines($envPath, $utf8)
    $out = foreach ($line in $lines) {
        if ($line -match '^\s*VAULT_PATH=') { "VAULT_PATH=$DestinationVault" }
        elseif ($line -match '^\s*INDEX_DB_PATH=') { "INDEX_DB_PATH=$DstDb" }
        elseif ($line -match '^\s*OBSIDIAN_LOCAL_VAULT_PATH=') { "OBSIDIAN_LOCAL_VAULT_PATH=$DestinationVault" }
        else { $line }
    }
    $has = $false
    foreach ($x in $out) { if ($x -match '^\s*VAULT_PATH=') { $has = $true } }
    if (-not $has) { $out += "VAULT_PATH=$DestinationVault" }
    [System.IO.File]::WriteAllLines($envPath, $out, $utf8)
}

Step "4. bootstrap_vault_layout" {
    & $Py (Join-Path $ProjectRoot "scripts\bootstrap_vault_layout.py") --vault $DestinationVault
    if ($LASTEXITCODE -ne 0) { throw "bootstrap failed" }
}

if ($IngestFile -and (Test-Path -LiteralPath $IngestFile)) {
    Step "4b. obsidian-ingest (ingest_kb_file.py)" {
        & $Py (Join-Path $ProjectRoot "scripts\ingest_kb_file.py") --file $IngestFile
        if ($LASTEXITCODE -ne 0) { throw "ingest failed" }
    }
}

Step "5. Python verify (settings + search)" {
    $code = @"
import importlib
import app.config as cfg
importlib.reload(cfg)
from pathlib import Path
from app.config import settings
from app.services.memory_store import MemoryStore

v = Path(settings.vault_path).resolve()
assert v == Path(r'$DestinationVault').resolve(), (v, r'$DestinationVault')
wiki = v / 'wiki' / 'analyses' / 'hvdc-logistics-ontology-guide.md'
print('vault:', v)
print('hvdc_wiki:', wiki.is_file())
store = MemoryStore(vault_path=v, index_db_path=Path(settings.index_db_path), timezone=settings.timezone)
hits = store.search(query='hvdc', limit=10).get('results') or []
print('search_hits:', len(hits))
assert len(hits) >= 1, 'expected at least one hvdc memory hit'
print('VERIFY_OK')
"@
    & $Py -c $code
    if ($LASTEXITCODE -ne 0) { throw "python verify failed" }
}

Step "6. Ollama health" {
    & $Py -c "from scripts.ollama_kb import health_check; import sys; sys.exit(0 if health_check() else 1)"
    if ($LASTEXITCODE -ne 0) { Write-Warning "Ollama not reachable (ingest would fail; sync still OK)" }
}

Step "7. Local MCP health + smoke (optional)" {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/healthz" -UseBasicParsing -TimeoutSec 5
        if ($r.StatusCode -ne 200) { throw "healthz not 200" }
        & $Py (Join-Path $ProjectRoot "scripts\mcp_local_tool_smoke.py") --all-mounts --base-url "http://127.0.0.1:8000"
        if ($LASTEXITCODE -ne 0) { throw "mcp smoke failed" }
    } catch {
        Write-Warning "MCP local skipped or failed: $_"
    }
}

Step "8. pytest (auth, search, mcp archive)" {
    Push-Location $ProjectRoot
    try {
        & $Py -m pytest -q tests/test_auth.py tests/test_search_v2.py tests/test_mcp_server_archive_raw.py --tb=no
        if ($LASTEXITCODE -ne 0) { throw "pytest failed" }
    } finally {
        Pop-Location
    }
}

Step "9. check_cursor_mcp_status" {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\check_cursor_mcp_status.ps1")
}

Write-Host "`n======================================== FULL UPLOAD + VERIFY: PASS ========================================"
