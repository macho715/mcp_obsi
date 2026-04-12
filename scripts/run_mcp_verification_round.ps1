# Single verification round: live MCP tool calls + pytest MCP-focused.
# Usage (from repo root): powershell -File scripts/run_mcp_verification_round.ps1 -Round 1
param(
    [int]$Round = 1,
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path $ProjectRoot).Path
Set-Location $ProjectRoot

$py = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Error "Missing venv python: $py"
    exit 1
}

function Resolve-EnvValue {
    param([string]$Name)
    $value = [Environment]::GetEnvironmentVariable($Name, "Process")
    if ([string]::IsNullOrWhiteSpace($value)) {
        $value = [Environment]::GetEnvironmentVariable($Name, "User")
    }
    return $value
}

$prodBase = "https://mcp-server-production-90cb.up.railway.app"
$prodUrl = "$prodBase/mcp/"
$prodTok = Resolve-EnvValue "MCP_PRODUCTION_BEARER_TOKEN"
if ([string]::IsNullOrWhiteSpace($prodTok)) {
    Write-Error "MCP_PRODUCTION_BEARER_TOKEN is missing (User or Process)."
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

function Step {
    param([string]$Name, [string[]]$CommandArgs)
    Write-Host ""
    Write-Host "[Round $Round] $Name"
    & $py @CommandArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $Name (exit $LASTEXITCODE)"
    }
}

Write-Host "======================================== Round $Round start ========================================"

try {
    Step "local_all_mounts_observe" @(
        "scripts\mcp_local_tool_smoke.py", "--all-mounts",
        "--base-url", "http://127.0.0.1:8000"
    )
    Step "production_all_mounts_observe" @(
        "scripts\mcp_local_tool_smoke.py", "--all-mounts",
        "--base-url", $prodBase,
        "--main-token", $prodTok
    )
    Step "verify_main_mcp_readonly" @(
        "scripts\verify_mcp_readonly.py",
        "--server-url", $prodUrl,
        "--token", $prodTok
    )
    Step "verify_chatgpt_mcp_readonly" @(
        "scripts\verify_chatgpt_mcp_readonly.py",
        "--server-url", "$prodBase/chatgpt-mcp/",
        "--token", $prodTok
    )
    Step "verify_claude_mcp_readonly" @(
        "scripts\verify_claude_mcp_readonly.py",
        "--server-url", "$prodBase/claude-mcp/",
        "--token", $prodTok
    )
    Step "verify_mcp_write_once" @(
        "scripts\verify_mcp_write_once.py",
        "--server-url", $prodUrl,
        "--token", $prodTok,
        "--confirm", "production-write-once"
    )
    Step "verify_mcp_secret_paths" @(
        "scripts\verify_mcp_secret_paths.py",
        "--server-url", $prodUrl,
        "--token", $prodTok,
        "--confirm", "production-secret-paths"
    )
    Step "verify_chatgpt_specialist_write" @(
        "scripts\verify_specialist_mcp_write.py",
        "--server-url", "$prodBase/chatgpt-mcp-write/",
        "--token", $chatgptWriteTok,
        "--profile", "chatgpt"
    )
    Step "verify_claude_specialist_write" @(
        "scripts\verify_specialist_mcp_write.py",
        "--server-url", "$prodBase/claude-mcp-write/",
        "--token", $claudeWriteTok,
        "--profile", "claude"
    )
    Step "pytest_mcp_focus" @(
        "-m", "pytest", "-q",
        "tests/test_auth.py",
        "tests/test_mcp_server_archive_raw.py",
        "tests/test_chatgpt_mcp_server.py",
        "tests/test_claude_mcp_server.py",
        "tests/test_wiki_overlay_surface.py",
        "tests/test_wiki_write_surface.py",
        "tests/test_search_v2.py"
    )
}
catch {
    Write-Error $_
    exit 1
}

Write-Host "======================================== Round $Round OK ========================================"
