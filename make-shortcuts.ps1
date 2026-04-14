$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shell = New-Object -ComObject WScript.Shell

$startScript = Join-Path $repoRoot "start-all.ps1"
$stopScript = Join-Path $repoRoot "stop-all.ps1"

if (-not (Test-Path $startScript)) {
  throw "[make-shortcuts] missing: $startScript"
}
if (-not (Test-Path $stopScript)) {
  throw "[make-shortcuts] missing: $stopScript"
}

function New-StackShortcut {
  param(
    [string]$OutputPath,
    [string]$ScriptPath,
    [string]$Description
  )
  $shortcut = $shell.CreateShortcut($OutputPath)
  $shortcut.TargetPath = "powershell.exe"
  $shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$ScriptPath`""
  $shortcut.WorkingDirectory = $repoRoot
  $shortcut.Description = $Description
  $shortcut.IconLocation = "powershell.exe,0"
  $shortcut.Save()
}

$targets = @(
  @{
    Path = Join-Path $desktopPath "Start MStack.lnk"
    Script = $startScript
    Description = "Start local mstack services"
  },
  @{
    Path = Join-Path $desktopPath "Stop MStack.lnk"
    Script = $stopScript
    Description = "Stop local mstack services"
  },
  @{
    Path = Join-Path $repoRoot "Start MStack.lnk"
    Script = $startScript
    Description = "Start local mstack services"
  },
  @{
    Path = Join-Path $repoRoot "Stop MStack.lnk"
    Script = $stopScript
    Description = "Stop local mstack services"
  }
)

foreach ($item in $targets) {
  New-StackShortcut -OutputPath $item.Path -ScriptPath $item.Script -Description $item.Description
  Write-Host "[make-shortcuts] wrote $($item.Path)"
}

Write-Host "[make-shortcuts] done"
