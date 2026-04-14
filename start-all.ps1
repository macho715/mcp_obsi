$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$localRagRoot = Join-Path $repoRoot "local-rag"
$standaloneRoot = Join-Path $repoRoot "myagent-copilot-kit\standalone-package"
$mcpStartScript = Join-Path $repoRoot "scripts\start-mcp-dev.ps1"

function Test-PortListening {
  param([int]$Port)
  $lines = netstat -ano -p tcp | Select-String ":$Port\s"
  foreach ($line in $lines) {
    $parts = ($line -replace "\s+", " ").Trim().Split(" ")
    if ($parts.Length -ge 5 -and $parts[3] -eq "LISTENING") {
      return $true
    }
  }
  return $false
}

function Start-DetachedPowerShell {
  param(
    [string]$WorkingDirectory,
    [string]$Command
  )
  Start-Process -FilePath "powershell.exe" -WorkingDirectory $WorkingDirectory -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command", $Command
  ) | Out-Null
}

Write-Host "[start-all] root: $repoRoot"

if (-not (Test-PortListening -Port 11434)) {
  Write-Host "[start-all] starting ollama (11434)"
  Start-Process -FilePath "ollama" -ArgumentList @("serve") -WorkingDirectory $repoRoot | Out-Null
} else {
  Write-Host "[start-all] ollama already running"
}

if (-not (Test-PortListening -Port 8010)) {
  $localRagPython = Join-Path $localRagRoot ".venv\Scripts\python.exe"
  if (-not (Test-Path $localRagPython)) {
    throw "[start-all] missing local-rag venv: $localRagPython"
  }
  Write-Host "[start-all] starting local-rag (8010)"
  Start-DetachedPowerShell -WorkingDirectory $localRagRoot -Command "& '$localRagPython' -m uvicorn app.main:app --host 127.0.0.1 --port 8010"
} else {
  Write-Host "[start-all] local-rag already running"
}

if (-not (Test-PortListening -Port 8000)) {
  if (-not (Test-Path $mcpStartScript)) {
    throw "[start-all] missing script: $mcpStartScript"
  }
  Write-Host "[start-all] starting mcp_obsidian (8000)"
  Start-DetachedPowerShell -WorkingDirectory $repoRoot -Command "& '$mcpStartScript'"
} else {
  Write-Host "[start-all] mcp_obsidian already running"
}

if (-not (Test-PortListening -Port 3010)) {
  if (-not (Test-Path $standaloneRoot)) {
    throw "[start-all] missing standalone root: $standaloneRoot"
  }
  Write-Host "[start-all] starting standalone (3010)"
  Start-DetachedPowerShell -WorkingDirectory $standaloneRoot -Command '$env:MYAGENT_HVDC_PREDICT_ENABLED="0"; $env:MYAGENT_LOCAL_RAG_TOKEN="dev-local-rag-token"; $env:MYAGENT_MEMORY_TOKEN="dev-memory-token"; node --import tsx src/cli.ts serve --host 127.0.0.1 --port 3010'
} else {
  Write-Host "[start-all] standalone already running"
}

Start-Sleep -Seconds 4

$checks = @(
  "http://127.0.0.1:11434/",
  "http://127.0.0.1:8010/health",
  "http://127.0.0.1:8000/healthz",
  "http://127.0.0.1:3010/api/ai/health"
)

Write-Host "[start-all] health checks:"
$allHealthy = $true
foreach ($url in $checks) {
  try {
    $res = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 5
    Write-Host "  OK  $url ($($res.StatusCode))"
  } catch {
    Write-Host "  FAIL $url"
    $allHealthy = $false
  }
}

if ($allHealthy) {
  Write-Host "[start-all] opening chat UI: http://127.0.0.1:3010/"
  Start-Process "http://127.0.0.1:3010/" | Out-Null
} else {
  Write-Host "[start-all] skipped browser open due to failed health check"
}

Write-Host "[start-all] done"
