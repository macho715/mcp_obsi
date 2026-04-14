param(
    [int]$Rounds = 5,
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$LocalVaultPath = "C:\Users\jichu\Downloads\valut"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path $ProjectRoot).Path
$LocalVaultPath = (Resolve-Path $LocalVaultPath).Path
$Py = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$ProdBase = "https://mcp-server-production-90cb.up.railway.app"
$MainUrl = "$ProdBase/mcp/"
$ChatgptWriteUrl = "$ProdBase/chatgpt-mcp-write/"
$ClaudeWriteUrl = "$ProdBase/claude-mcp-write/"

function Resolve-EnvValue {
    param([string]$Name)
    $value = [Environment]::GetEnvironmentVariable($Name, "Process")
    if ([string]::IsNullOrWhiteSpace($value)) {
        $value = [Environment]::GetEnvironmentVariable($Name, "User")
    }
    return $value
}

function New-RunnerSpec {
    param(
        [string]$Name,
        [string[]]$CommandArgs
    )
    return [pscustomobject]@{
        Name = $Name
        CommandArgs = $CommandArgs
    }
}

function Start-Runner {
    param(
        [pscustomobject]$Spec,
        [string]$RoundTemp
    )
    $stdout = Join-Path $RoundTemp "$($Spec.Name).stdout.txt"
    $stderr = Join-Path $RoundTemp "$($Spec.Name).stderr.txt"
    $job = Start-Job -Name $Spec.Name -ScriptBlock {
        param(
            [string]$PyPath,
            [string]$WorkingDir,
            [string[]]$CommandArgs,
            [string]$StdoutPath,
            [string]$StderrPath,
            [string]$RunnerName
        )
        Set-Location $WorkingDir
        & $PyPath @CommandArgs 1> $StdoutPath 2> $StderrPath
        [pscustomobject]@{
            name = $RunnerName
            exit_code = $LASTEXITCODE
            stdout = $StdoutPath
            stderr = $StderrPath
        }
    } -ArgumentList $Py, $ProjectRoot, $Spec.CommandArgs, $stdout, $stderr, $Spec.Name
    return [pscustomobject]@{
        Name = $Spec.Name
        Job = $job
        Stdout = $stdout
        Stderr = $stderr
    }
}

function Read-JsonFile {
    param([string]$Path)
    $raw = Get-Content -LiteralPath $Path -Raw
    if ([string]::IsNullOrWhiteSpace($raw)) {
        throw "empty json output: $Path"
    }
    return $raw | ConvertFrom-Json
}

function Invoke-SyncToLocalVault {
    param([string]$TargetVault)
    $syncScript = Join-Path $ProjectRoot "scripts\sync_railway_production_to_local_vault.ps1"
    powershell -NoProfile -ExecutionPolicy Bypass -File $syncScript -LocalVaultPath $TargetVault | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "sync_railway_production_to_local_vault failed"
    }
}

function Test-LocalVaultShape {
    param([string]$TargetVault)
    $markers = @(
        (Join-Path $TargetVault ".obsidian"),
        (Join-Path $TargetVault "memory"),
        (Join-Path $TargetVault "mcp_raw"),
        (Join-Path $TargetVault "wiki")
    )
    foreach ($marker in $markers) {
        if (Test-Path -LiteralPath $marker) {
            return $true
        }
    }
    return $false
}

if (-not (Test-Path -LiteralPath $Py)) {
    Write-Error "Missing venv: $Py"
    exit 1
}
Set-Location $ProjectRoot
if (-not (Test-LocalVaultShape -TargetVault $LocalVaultPath)) {
    Write-Error "LocalVaultPath does not look like an Obsidian/MCP vault: $LocalVaultPath"
    exit 1
}

$prodTok = Resolve-EnvValue "MCP_PRODUCTION_BEARER_TOKEN"
if ([string]::IsNullOrWhiteSpace($prodTok)) {
    Write-Error "MCP_PRODUCTION_BEARER_TOKEN is missing."
    exit 1
}
$chatgptWriteTok = Resolve-EnvValue "CHATGPT_MCP_WRITE_TOKEN"
if ([string]::IsNullOrWhiteSpace($chatgptWriteTok)) {
    $chatgptWriteTok = $prodTok
}
$claudeWriteTok = Resolve-EnvValue "CLAUDE_MCP_WRITE_TOKEN"
if ([string]::IsNullOrWhiteSpace($claudeWriteTok)) {
    $claudeWriteTok = $prodTok
}

$roundResults = @()

for ($round = 1; $round -le $Rounds; $round++) {
    Write-Host ""
    Write-Host "======================================== Upload simulation round $round start ========================================"

    $roundTemp = Join-Path $env:TEMP ("mcp-upload-sim-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $roundTemp | Out-Null

    $specs = @(
        (New-RunnerSpec -Name "cursor-main" -CommandArgs @(
            "scripts\verify_mcp_write_once.py",
            "--server-url", $MainUrl,
            "--token", $prodTok,
            "--confirm", "production-write-once"
        )),
        (New-RunnerSpec -Name "chatgpt-specialist" -CommandArgs @(
            "scripts\verify_specialist_mcp_write.py",
            "--server-url", $ChatgptWriteUrl,
            "--token", $chatgptWriteTok,
            "--profile", "chatgpt"
        )),
        (New-RunnerSpec -Name "claude-specialist" -CommandArgs @(
            "scripts\verify_specialist_mcp_write.py",
            "--server-url", $ClaudeWriteUrl,
            "--token", $claudeWriteTok,
            "--profile", "claude"
        ))
    )

    $runs = foreach ($spec in $specs) {
        Start-Runner -Spec $spec -RoundTemp $roundTemp
    }

    foreach ($run in $runs) {
        Wait-Job -Job $run.Job | Out-Null
    }

    $stepResults = @()
    foreach ($run in $runs) {
        $jobResult = $null
        $jobErrorText = ""
        try {
            $jobResult = Receive-Job -Job $run.Job -ErrorAction Stop
        }
        catch {
            $jobErrorText = $_.Exception.Message
        }
        Remove-Job -Job $run.Job -Force -ErrorAction SilentlyContinue
        $exitCode = if ($null -ne $jobResult) { $jobResult.exit_code } else { 1 }
        $stderr = if (Test-Path -LiteralPath $run.Stderr) {
            Get-Content -LiteralPath $run.Stderr -Raw
        } else {
            ""
        }
        $result = [ordered]@{
            name = $run.Name
            exit_code = $exitCode
            ok = ($exitCode -eq 0)
            stderr = if ($null -eq $stderr) { "" } else { $stderr.ToString().Trim() }
        }
        if ($jobErrorText) {
            $result["job_error"] = $jobErrorText
        }

        if ($exitCode -eq 0) {
            $payload = Read-JsonFile -Path $run.Stdout
            $saved = $payload.saved
            $result["memory_id"] = $saved.id
            $result["relative_path"] = $saved.path
            $result["rollback_status"] = if ($payload.get_after_rollback) { $payload.get_after_rollback.status } else { $null }
            if ($payload.fetch_after_update) {
                $result["expected_title"] = $payload.fetch_after_update.title
            }
            elseif ($payload.fetch_after_save) {
                $result["expected_title"] = $payload.fetch_after_save.title
            }
            elseif ($payload.get_after_save) {
                $result["expected_title"] = $payload.get_after_save.title
            }
        }

        $stepResults += [pscustomobject]$result
    }

    $syncOk = $true
    $syncError = ""
    try {
        Invoke-SyncToLocalVault -TargetVault $LocalVaultPath
    }
    catch {
        $syncOk = $false
        $syncError = $_.Exception.Message
    }

    foreach ($step in $stepResults) {
        if ($step.relative_path) {
            $localPath = Join-Path $LocalVaultPath $step.relative_path
            Add-Member -InputObject $step -NotePropertyName local_path -NotePropertyValue $localPath
            $localExists = Test-Path -LiteralPath $localPath
            Add-Member -InputObject $step -NotePropertyName local_exists -NotePropertyValue $localExists
            if ($localExists) {
                $localText = Get-Content -LiteralPath $localPath -Raw
                Add-Member -InputObject $step -NotePropertyName local_contains_id -NotePropertyValue ($localText.Contains($step.memory_id))
                Add-Member -InputObject $step -NotePropertyName local_contains_title -NotePropertyValue (
                    -not [string]::IsNullOrWhiteSpace($step.expected_title) -and $localText.Contains($step.expected_title)
                )
                Add-Member -InputObject $step -NotePropertyName local_contains_archived -NotePropertyValue ($localText.Contains("status: archived"))
            }
            else {
                Add-Member -InputObject $step -NotePropertyName local_contains_id -NotePropertyValue $false
                Add-Member -InputObject $step -NotePropertyName local_contains_title -NotePropertyValue $false
                Add-Member -InputObject $step -NotePropertyName local_contains_archived -NotePropertyValue $false
            }
        }
        else {
            Add-Member -InputObject $step -NotePropertyName local_path -NotePropertyValue $null
            Add-Member -InputObject $step -NotePropertyName local_exists -NotePropertyValue $false
            Add-Member -InputObject $step -NotePropertyName local_contains_id -NotePropertyValue $false
            Add-Member -InputObject $step -NotePropertyName local_contains_title -NotePropertyValue $false
            Add-Member -InputObject $step -NotePropertyName local_contains_archived -NotePropertyValue $false
        }
    }

    $roundResults += [pscustomobject]@{
        round = $round
        sync_ok = $syncOk
        sync_error = $syncError
        steps = $stepResults
    }

    Write-Host "======================================== Upload simulation round $round end ========================================"
}

$allOk = $true
foreach ($round in $roundResults) {
    if (-not $round.sync_ok) {
        $allOk = $false
        continue
    }
    foreach ($step in $round.steps) {
        if (
            -not $step.ok -or
            -not $step.local_exists -or
            -not $step.local_contains_id -or
            -not $step.local_contains_title -or
            -not $step.local_contains_archived -or
            $step.rollback_status -ne "archived"
        ) {
            $allOk = $false
        }
    }
}

$summary = [pscustomobject]@{
    rounds = $Rounds
    local_vault = $LocalVaultPath
    all_ok = $allOk
    results = $roundResults
}

$summary | ConvertTo-Json -Depth 8

if (-not $allOk) {
    exit 1
}
