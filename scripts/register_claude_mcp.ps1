param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)
$root = Get-Location

function Require-Command {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

Require-Command -Name "railway"
Require-Command -Name "claude"

$vars = railway variables --json | ConvertFrom-Json
if (-not $vars) {
    throw "Failed to read Railway variables."
}

$writeTokenProp = $vars.PSObject.Properties["CLAUDE_MCP_WRITE_TOKEN"]
$writeToken = ""
if ($writeTokenProp -and -not [string]::IsNullOrWhiteSpace([string]$writeTokenProp.Value)) {
    $writeToken = [string]$writeTokenProp.Value
} else {
    $writeToken = [string]$vars.MCP_API_TOKEN
}

if ([string]::IsNullOrWhiteSpace($writeToken)) {
    throw "Neither CLAUDE_MCP_WRITE_TOKEN nor MCP_API_TOKEN is set in Railway variables."
}

$readUrl = "https://mcp-server-production-90cb.up.railway.app/claude-mcp"
$writeUrl = "https://mcp-server-production-90cb.up.railway.app/claude-mcp-write"
$cfgPath = Join-Path $HOME ".claude.json"

if (Test-Path $cfgPath) {
    $cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
} else {
    $cfg = [pscustomobject]@{}
}

if (-not $cfg.PSObject.Properties["mcpServers"]) {
    $cfg | Add-Member -NotePropertyName mcpServers -NotePropertyValue ([pscustomobject]@{})
}

$mcpServers = [ordered]@{}
if ($cfg.mcpServers) {
    $cfg.mcpServers.PSObject.Properties | ForEach-Object {
        $mcpServers[$_.Name] = $_.Value
    }
}

$mcpServers["obsidian-memory-claude"] = [pscustomobject]@{
    type = "http"
    url = $readUrl
}

$mcpServers["obsidian-memory-claude-write"] = [pscustomobject]@{
    type = "http"
    url = $writeUrl
    headers = [pscustomobject]@{
        Authorization = "Bearer $writeToken"
    }
}

$cfg.mcpServers = [pscustomobject]$mcpServers

if ($DryRun) {
    Write-Output "Dry run only. No files changed."
    Write-Output "Config path: $cfgPath"
    Write-Output "Read route: $readUrl"
    Write-Output "Write route: $writeUrl"
    Write-Output "Write token source: $(if ($writeTokenProp -and -not [string]::IsNullOrWhiteSpace([string]$writeTokenProp.Value)) { 'CLAUDE_MCP_WRITE_TOKEN' } else { 'MCP_API_TOKEN' })"
    exit 0
}

$cfg | ConvertTo-Json -Depth 100 | Set-Content $cfgPath -Encoding UTF8

Write-Output "Updated: $cfgPath"
claude mcp list
