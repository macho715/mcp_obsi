param(
    [string]$ProjectRoot
)

$ErrorActionPreference = "Stop"

if (-not $ProjectRoot) {
    $ProjectRoot = Split-Path -Parent $PSScriptRoot
}

$ProjectRoot = (Resolve-Path $ProjectRoot).Path
$projectMcp = Join-Path $ProjectRoot ".cursor\mcp.json"
$sampleMcp = Join-Path $ProjectRoot ".cursor\mcp.sample.json"

function Get-JsonState {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return [ordered]@{
            status = "missing"
        }
    }

    try {
        $raw = Get-Content $Path -Raw -Encoding UTF8
        $parsed = $raw | ConvertFrom-Json
        $hasServers = $null -ne $parsed.mcpServers
        return [ordered]@{
            status = if ($hasServers) { "valid" } else { "invalid" }
            has_mcpServers = $hasServers
        }
    } catch {
        return [ordered]@{
            status = "invalid"
            error = $_.Exception.Message
        }
    }
}

function Get-EnvState {
    param([string]$Name)

    $value = [Environment]::GetEnvironmentVariable($Name, "User")
    if ([string]::IsNullOrWhiteSpace($value)) {
        $value = [Environment]::GetEnvironmentVariable($Name, "Process")
    }

    if ([string]::IsNullOrWhiteSpace($value)) {
        return "missing"
    }

    return "set"
}

function Get-HttpState {
    param([string]$Url)

    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
        return "ok:$($response.StatusCode)"
    } catch {
        $resp = $_.Exception.Response
        if ($resp) {
            return "http:$($resp.StatusCode.value__)"
        }
        return "connection_error"
    }
}

$result = [ordered]@{
    project_root = $ProjectRoot
    project_mcp_json = Get-JsonState -Path $projectMcp
    sample_mcp_json = Get-JsonState -Path $sampleMcp
    env = [ordered]@{
        MCP_API_TOKEN = Get-EnvState -Name "MCP_API_TOKEN"
        MCP_PRODUCTION_BEARER_TOKEN = Get-EnvState -Name "MCP_PRODUCTION_BEARER_TOKEN"
        OBSIDIAN_LOCAL_VAULT_PATH = Get-EnvState -Name "OBSIDIAN_LOCAL_VAULT_PATH"
    }
    health = [ordered]@{
        local = Get-HttpState -Url "http://127.0.0.1:8000/healthz"
        production = Get-HttpState -Url "https://mcp-server-production-90cb.up.railway.app/healthz"
    }
}

$next = New-Object System.Collections.Generic.List[string]

if ($result.project_mcp_json.status -eq "missing") {
    $next.Add("Create .cursor/mcp.json (copy from .cursor/mcp.sample.json or rerun install_cursor_fullsetup.ps1).")
} elseif ($result.project_mcp_json.status -ne "valid") {
    $next.Add("Fix .cursor/mcp.json so it is valid JSON and contains mcpServers.")
}
if ($result.sample_mcp_json.status -eq "invalid") {
    $next.Add("Fix .cursor/mcp.sample.json so the installer has a valid fallback template.")
}
if ($result.env.MCP_API_TOKEN -eq "missing") {
    $next.Add("Set MCP_API_TOKEN in user or shell environment, then restart Cursor.")
}
if ($result.env.MCP_PRODUCTION_BEARER_TOKEN -eq "missing") {
    $next.Add("Set MCP_PRODUCTION_BEARER_TOKEN in user or shell environment, then restart Cursor.")
}
if (-not $result.health.local.StartsWith("ok:")) {
    $next.Add("Start the local MCP app with scripts/start-mcp-dev.ps1 if Cursor local MCP should connect.")
}
if ($next.Count -eq 0) {
    $next.Add("Config, env, and health probes look ready; if Cursor still fails, reload Cursor and inspect Settings -> MCP / MCP Logs.")
}

$result.next_steps = $next

$result | ConvertTo-Json -Depth 5
