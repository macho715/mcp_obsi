$ErrorActionPreference = "Continue"

function Get-ListeningProcessIds {
  param([int]$Port)
  $result = @()
  $lines = netstat -ano -p tcp | Select-String ":$Port\s"
  foreach ($line in $lines) {
    $parts = ($line -replace "\s+", " ").Trim().Split(" ")
    if ($parts.Length -ge 5 -and $parts[3] -eq "LISTENING") {
      $result += [int]$parts[4]
    }
  }
  return $result | Select-Object -Unique
}

function Stop-ByPort {
  param([int]$Port)
  $procIds = Get-ListeningProcessIds -Port $Port
  if (-not $procIds -or $procIds.Count -eq 0) {
    Write-Host "[stop-all] port $Port already down"
    return
  }
  foreach ($procId in $procIds) {
    try {
      Stop-Process -Id $procId -Force -ErrorAction Stop
      Write-Host "[stop-all] stopped pid $procId on port $Port"
    } catch {
      Write-Host "[stop-all] failed pid $procId on port $Port"
    }
  }
}

Write-Host "[stop-all] stopping stack ports"
Stop-ByPort -Port 3010
Stop-ByPort -Port 8000
Stop-ByPort -Port 8010
Stop-ByPort -Port 11434

Write-Host "[stop-all] stopping ollama processes (if any)"
taskkill /F /T /IM "ollama app.exe" | Out-Null
taskkill /F /T /IM "ollama.exe" | Out-Null

Start-Sleep -Seconds 2

Write-Host "[stop-all] final status"
$ports = @(3010, 8000, 8010, 11434)
foreach ($port in $ports) {
  $up = $false
  try {
    $res = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$port/" -TimeoutSec 2
    if ($res.StatusCode -ge 200) {
      $up = $true
    }
  } catch {
    $up = $false
  }
  if ($up) {
    Write-Host "  UP   $port"
  } else {
    Write-Host "  DOWN $port"
  }
}

Write-Host "[stop-all] done"
