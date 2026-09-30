param(
    [switch]$ValidateOnly
)

$ErrorActionPreference = 'Stop'
$LogDir = 'D:\Velvet\Logs\Autostart'
$LogPath = Join-Path $LogDir ('dcc-gateway-' + (Get-Date -Format 'yyyyMMdd') + '.log')
$Server = 'D:\Velvet\Tools\DCC-MCP\core-0.20.37\venv\Scripts\dcc-mcp-server.exe'
$Registry = 'D:\Velvet\State\DCC-MCP\maya-0.9.31-shadow\registry'
$Profiles = 'D:\Velvet\State\DCC-MCP\maya-0.9.31-shadow\gateway-profiles.json'
$Port = 9765

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-GatewayLog {
    param([string]$Message)
    Add-Content -Path $LogPath -Value ('{0:o} {1}' -f (Get-Date), $Message) -Encoding UTF8
}

if ($ValidateOnly) {
    $result = [pscustomobject]@{
        status = if ((Test-Path $Server) -and (Test-Path 'D:\Velvet')) { 'PASS' } else { 'BLOCKED' }
        server = $Server
        server_exists = Test-Path $Server
        velvet_root_exists = Test-Path 'D:\Velvet'
        registry = $Registry
        port = $Port
        run_as = 'SYSTEM'
        pre_login = $true
    }
    $result | ConvertTo-Json -Depth 3
    exit $(if ($result.status -eq 'PASS') { 0 } else { 2 })
}

$deadline = (Get-Date).AddSeconds(90)
while (-not (Test-Path 'D:\Velvet') -and (Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 3
}
if (-not (Test-Path 'D:\Velvet')) {
    Write-GatewayLog 'BLOCKED D:\Velvet unavailable after 90s'
    exit 2
}

New-Item -ItemType Directory -Force -Path $Registry | Out-Null
$env:DCC_MCP_GATEWAY_PROFILES_FILE = $Profiles

try {
    $health = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 2
    if ($health.StatusCode -eq 200) {
        Write-GatewayLog "SKIP gateway already healthy on 127.0.0.1:$Port"
        exit 0
    }
} catch {}

Write-GatewayLog "START gateway on 127.0.0.1:$Port"
$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
try {
    & $Server gateway --host 127.0.0.1 --port $Port --name velvetos-dcc-autostart --remote-host 127.0.0.1 --remote-port 0 --registry-dir $Registry --no-admin --gateway-persist *>> $LogPath
    $code = $LASTEXITCODE
} finally {
    $ErrorActionPreference = $previousErrorActionPreference
}
if ($null -eq $code) { $code = 1 }
Write-GatewayLog "EXIT gateway code=$code"
exit $code
