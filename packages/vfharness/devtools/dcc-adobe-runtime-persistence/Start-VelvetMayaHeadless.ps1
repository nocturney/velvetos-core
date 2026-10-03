$ErrorActionPreference = 'Stop'
. 'D:\Velvet\Runtime\Autostart\Set-VelvetDccEnvironment.ps1'

$Mayapy = 'C:\Program Files\Autodesk\Maya2027\bin\mayapy.exe'
$ModuleRoot = 'C:\Users\Chris\Documents\maya\modules\dcc-mcp-maya\python'
$VenvSite = 'D:\Velvet\Tools\DCC-MCP\maya-0.9.31\venv\Lib\site-packages'
$CleanAppDir = 'D:\Velvet\Runtime\MayaHeadlessApp'
$StatePath = 'D:\Velvet\State\DCC-MCP\maya-headless-host.json'
$RegistryDir = 'D:\Velvet\State\DCC-MCP\maya-0.9.31-shadow\registry'
$ServicesPath = Join-Path $RegistryDir 'services.json'
$LogDir = 'D:\Velvet\Logs\Autostart'

New-Item -ItemType Directory -Force -Path $CleanAppDir,$RegistryDir,$LogDir,(Split-Path -Parent $StatePath) | Out-Null

function Get-ManagedHost {
    if (-not (Test-Path -LiteralPath $StatePath)) { return $null }
    try {
        $state = Get-Content -Raw -LiteralPath $StatePath | ConvertFrom-Json
        if (-not $state.pid) { return $null }
        $cim = Get-CimInstance Win32_Process -Filter ("ProcessId=" + [int]$state.pid) -ErrorAction SilentlyContinue
        if (-not $cim -or $cim.Name -ine 'mayapy.exe') { return $null }
        return Get-Process -Id ([int]$state.pid) -ErrorAction SilentlyContinue
    } catch { return $null }
}
function Get-RegistryEntry([int]$HostPid) {
    if (-not (Test-Path -LiteralPath $ServicesPath)) { return $null }
    try {
        $rows = @(Get-Content -Raw -LiteralPath $ServicesPath | ConvertFrom-Json)
        foreach ($row in $rows) {
            if ($row.dcc_type -ne 'maya' -or $row.status -ne 'available') { continue }
            $ownerPid = if (($row.PSObject.Properties.Name -contains 'host_pid') -and $row.host_pid) { [int]$row.host_pid } else { [int]$row.pid }
            if ($ownerPid -eq $HostPid) { return $row }
        }
    } catch {}
    return $null
}

$existing = Get-ManagedHost
if ($existing) {
    $entry = Get-RegistryEntry -HostPid $existing.Id
    [pscustomobject]@{
        status = $(if ($entry) { 'ALREADY_RUNNING' } else { 'RUNNING_WAITING_REGISTRY' })
        pid = $existing.Id
        endpoint = $(if ($entry) { "http://127.0.0.1:$($entry.port)/mcp" } else { $null })
        mode = 'official_mayapy_entrypoint'
        state = $StatePath
    } | ConvertTo-Json -Compress
    exit 0
}

Remove-Item -LiteralPath $StatePath -Force -ErrorAction SilentlyContinue

$env:MAYA_APP_DIR = $CleanAppDir
$env:PYTHONPATH = "$ModuleRoot;$VenvSite"
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:DCC_MCP_REGISTRY_DIR = $RegistryDir
$env:DCC_MCP_GATEWAY_PORT = '9765'
$env:DCC_MCP_GATEWAY_REMOTE_PORT = '0'
$env:DCC_MCP_NO_ADMIN = 'true'
$env:DCC_MCP_LOG_DIR = 'D:\Velvet\Logs\DCC-MCP\maya-0.9.31-shadow'
$env:DCC_MCP_MAYA_DISABLE_EXECUTE_PYTHON = '1'
$env:DCC_MCP_MAYA_DISABLE_EXECUTE_MEL = '1'
$env:DCC_MCP_MAYA_DISABLE_ARBITRARY_SCRIPT = '1'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$stdout = Join-Path $LogDir "maya-headless-$stamp.stdout.log"
$stderr = Join-Path $LogDir "maya-headless-$stamp.stderr.log"

$args = @(
    '-m','dcc_mcp_maya',
    '--port','0',
    '--gateway-port','9765',
    '--registry-dir',$RegistryDir,
    '--json'
)
$proc = Start-Process -FilePath $Mayapy -ArgumentList $args -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru

[ordered]@{
    schema = 'velvetos.maya-headless-host.v2'
    pid = [int]$proc.Id
    process = 'mayapy'
    executable = $Mayapy
    adapter_expected = '0.9.33'
    started_at = (Get-Date).ToString('o')
    command_marker = '-m dcc_mcp_maya'
    stdout = $stdout
    stderr = $stderr
    registry = $RegistryDir
    maya_app_dir = $CleanAppDir
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $StatePath -Encoding UTF8

$deadline = (Get-Date).AddSeconds(20)
$announce = $null
do {
    if ($proc.HasExited) { break }
    if (Test-Path -LiteralPath $stdout) {
        $line = Get-Content -LiteralPath $stdout -First 1 -ErrorAction SilentlyContinue
        if (-not [string]::IsNullOrWhiteSpace([string]$line)) {
            try { $announce = [string]$line | ConvertFrom-Json } catch {}
            if ($announce -and $announce.mcp_url) { break }
        }
    }
    Start-Sleep -Milliseconds 250
    $proc.Refresh()
} while ((Get-Date) -lt $deadline)

if (-not $announce -or [string]$announce.adapter_version -ne '0.9.33' -or -not $announce.mcp_url) {
    if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
    Remove-Item -LiteralPath $StatePath -Force -ErrorAction SilentlyContinue
    $errTail = if (Test-Path -LiteralPath $stderr) { (Get-Content -LiteralPath $stderr -Tail 30 -ErrorAction SilentlyContinue) -join ' | ' } else { '' }
    throw "Official Maya Mayapy MCP host failed startup verification. stderr=$errTail"
}

[pscustomobject]@{
    status = 'STARTED'
    pid = [int]$proc.Id
    adapter_version = [string]$announce.adapter_version
    endpoint = [string]$announce.mcp_url
    mode = 'official_mayapy_entrypoint'
    state = $StatePath
} | ConvertTo-Json -Compress
