param(
    [string]$LocalVaultPath,
    [switch]$SkipSystem
)

$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

function Resolve-LocalVaultPath {
    param([string]$ExplicitPath)

    if ($ExplicitPath) {
        return (Resolve-Path -LiteralPath $ExplicitPath).Path
    }

    if ($env:OBSIDIAN_LOCAL_VAULT_PATH) {
        return (Resolve-Path -LiteralPath $env:OBSIDIAN_LOCAL_VAULT_PATH).Path
    }

    if ($env:VAULT_PATH -and [IO.Path]::IsPathRooted($env:VAULT_PATH)) {
        return (Resolve-Path -LiteralPath $env:VAULT_PATH).Path
    }

    throw "Local vault path not provided. Use -LocalVaultPath or set OBSIDIAN_LOCAL_VAULT_PATH."
}

function Copy-Tree {
    param(
        [string]$SourceDir,
        [string]$TargetDir
    )

    if (-not (Test-Path -LiteralPath $SourceDir)) {
        return
    }

    New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
    Copy-Item -Path (Join-Path $SourceDir "*") -Destination $TargetDir -Recurse -Force
}

$resolvedVault = Resolve-LocalVaultPath -ExplicitPath $LocalVaultPath

$backup = railway ssh python /app/scripts/backup_restore_drill.py | ConvertFrom-Json
$archivePath = $backup.archive

$archiveBase64 = (
    railway ssh python /app/scripts/export_file_base64.py --path $archivePath
) -join ""
$archiveBase64 = $archiveBase64.Trim()

$tempRoot = Join-Path $env:TEMP ("mcp-railway-sync-" + [guid]::NewGuid().ToString("N"))
$tempArchive = Join-Path $tempRoot "production-sync.tar.gz"
$extractRoot = Join-Path $tempRoot "extract"

New-Item -ItemType Directory -Force -Path $extractRoot | Out-Null
[IO.File]::WriteAllBytes($tempArchive, [Convert]::FromBase64String($archiveBase64))

tar -xzf $tempArchive -C $extractRoot

$sourceVault = Join-Path $extractRoot "vault"
$synced = @()

foreach ($name in @("10_Daily", "20_AI_Memory", "mcp_raw")) {
    $src = Join-Path $sourceVault $name
    $dst = Join-Path $resolvedVault $name
    if (Test-Path -LiteralPath $src) {
        Copy-Tree -SourceDir $src -TargetDir $dst
        $synced += $name
    }
}

if (-not $SkipSystem) {
    $src = Join-Path $sourceVault "90_System"
    $dst = Join-Path $resolvedVault "90_System"
    if (Test-Path -LiteralPath $src) {
        Copy-Tree -SourceDir $src -TargetDir $dst
        $synced += "90_System"
    }
}

@{
    archive = $archivePath
    local_vault = $resolvedVault
    synced_folders = $synced
    extracted_from = $tempArchive
} | ConvertTo-Json -Depth 4
