$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
    Write-Host "가상환경이 없습니다. 먼저 py -3.11 -m venv .venv 를 실행하세요." -ForegroundColor Yellow
    exit 1
}

.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = (Get-Location).Path

python -m uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload
