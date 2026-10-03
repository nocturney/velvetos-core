[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ToolName,
    [string]$ArgumentsJson = '{}',
    [string]$ArgumentsPath,
    [int]$TimeoutSeconds = 30,
    [switch]$TerminateSession
)

$ErrorActionPreference = 'Stop'
$Uri = 'http://127.0.0.1:27182/mcp'
$Protocol = '2025-11-25'
$base = @{ Accept='application/json, text/event-stream' }

if ($ArgumentsPath) {
    $ArgumentsJson = Get-Content -Raw -LiteralPath $ArgumentsPath
}
$arguments = $ArgumentsJson | ConvertFrom-Json
$initBody = @{
    jsonrpc='2.0'; id=1; method='initialize'
    params=@{protocolVersion=$Protocol;capabilities=@{};clientInfo=@{name='VelvetOS';version='0.1.0'}}
} | ConvertTo-Json -Depth 10 -Compress
$sid = $null
try {
    $init = Invoke-WebRequest -UseBasicParsing -Method Post -Uri $Uri -Headers $base -ContentType 'application/json' -Body $initBody -TimeoutSec 15
    $sid = [string]$init.Headers['MCP-Session-Id']
    if (-not $sid) { throw 'Fusion native MCP did not return MCP-Session-Id.' }
    $headers = @{Accept='application/json, text/event-stream';'MCP-Protocol-Version'=$Protocol;'MCP-Session-Id'=$sid}
    $note = @{jsonrpc='2.0';method='notifications/initialized';params=@{}} | ConvertTo-Json -Depth 5 -Compress
    Invoke-WebRequest -UseBasicParsing -Method Post -Uri $Uri -Headers $headers -ContentType 'application/json' -Body $note -TimeoutSec 10 | Out-Null
    $call = @{jsonrpc='2.0';id=2;method='tools/call';params=@{name=$ToolName;arguments=$arguments}} | ConvertTo-Json -Depth 30 -Compress
    $resp = Invoke-WebRequest -UseBasicParsing -Method Post -Uri $Uri -Headers $headers -ContentType 'application/json' -Body $call -TimeoutSec $TimeoutSeconds
    [pscustomobject]@{http_status=[int]$resp.StatusCode;session_created=$true;result=($resp.Content|ConvertFrom-Json)} | ConvertTo-Json -Depth 30
} finally {
    if ($TerminateSession -and $sid) {
        try { Invoke-WebRequest -UseBasicParsing -Method Delete -Uri $Uri -Headers $headers -TimeoutSec 5 | Out-Null } catch {}
    }
}
