param(
  [string]$Host = "127.0.0.1",
  [int]$Port = 8010
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
  throw ".venv is missing. Run: python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -e `"".[dev]`""
}

if (-not $env:LOCAL_RAG_MODEL) {
  $env:LOCAL_RAG_MODEL = "gemma4:e4b"
}

if (-not $env:LOCAL_RAG_DOCS_DIR) {
  $env:LOCAL_RAG_DOCS_DIR = "C:\Users\jichu\Downloads\valut\wiki"
}

if (-not $env:LOCAL_RAG_CACHE_PATH) {
  $env:LOCAL_RAG_CACHE_PATH = ".cache\retrieval-cache.json"
}

if (($Host -ne "127.0.0.1") -and ($Host -ne "localhost") -and (-not $env:LOCAL_RAG_SHARED_SECRET)) {
  throw "LOCAL_RAG_SHARED_SECRET is required when binding beyond loopback."
}

Write-Host "Starting local-rag on $Host`:$Port"
Write-Host "Model    : $env:LOCAL_RAG_MODEL"
Write-Host "Docs dir  : $env:LOCAL_RAG_DOCS_DIR"
Write-Host "Cache path: $env:LOCAL_RAG_CACHE_PATH"
if ($env:LOCAL_RAG_SHARED_SECRET) {
  Write-Host "Guard    : enabled"
} else {
  Write-Host "Guard    : disabled"
}

& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --host $Host --port $Port
