param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('start','stop','status')]
    [string]$Action,
    [Parameter(Mandatory=$true)]
    [string]$AppId,
    [switch]$CompatibilityProbe
)

$ErrorActionPreference = 'Stop'
$ManifestPath = 'D:\Velvet\Runtime\Autostart\dcc-desktop-hosts.json'
$manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$app = $manifest.apps | Where-Object { $_.id -eq $AppId } | Select-Object -First 1
if (-not $app) { throw "Unknown DCC app id: $AppId" }
if (-not $app.enabled) { throw "DCC app is disabled: $AppId ($($app.reason))" }

function Get-AppProcesses {
    if (($app.PSObject.Properties.Name -contains 'managed_pid_file') -and -not [string]::IsNullOrWhiteSpace([string]$app.managed_pid_file)) {
        $statePath = [string]$app.managed_pid_file
        if (-not (Test-Path -LiteralPath $statePath)) { return @() }
        try {
            $state = Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json
            if (-not $state.pid) { return @() }
            $cim = Get-CimInstance Win32_Process -Filter ("ProcessId=" + [int]$state.pid) -ErrorAction SilentlyContinue
            if (-not $cim) { return @() }
            $expectedBase = if (($app.PSObject.Properties.Name -contains 'automation_process') -and $app.automation_process) { [string]$app.automation_process } else { [string]$app.process }
            $expectedName = (($expectedBase -replace '(?i)\.exe$','') + '.exe')
            if ($cim.Name -ine $expectedName) { return @() }
            if (($state.PSObject.Properties.Name -contains 'command_marker') -and $state.command_marker -and ([string]$cim.CommandLine -notlike ('*' + [string]$state.command_marker + '*'))) { return @() }
            $proc = Get-Process -Id ([int]$state.pid) -ErrorAction SilentlyContinue
            if ($proc) {
                try { if (-not $proc.HasExited) { return @($proc) } } catch {}
            }
        } catch { return @() }
        return @()
    }
    @(
        Get-Process -Name $app.process -ErrorAction SilentlyContinue |
            Where-Object {
                try { -not $_.HasExited } catch { $false }
            }
    )
}

if ($Action -eq 'start' -and -not $CompatibilityProbe) {
    $routingPath = 'D:\Velvet\State\DCC-Adobe-Update-Sentinel\routing-state.json'
    if (Test-Path -LiteralPath $routingPath) {
        $routing = Get-Content -Raw -LiteralPath $routingPath | ConvertFrom-Json
        $route = $routing.hosts.PSObject.Properties[$AppId]
        if ($route -and $route.Value.status -in @('pending_validation','needs_compatibility_repair','blocked_host_update')) {
            throw "VelvetOS compatibility gate blocks automatic routing to ${AppId}: $($route.Value.status)"
        }
    }
}

if ($Action -eq 'start') {
    $taskName = "VelvetOS DCC OnDemand $AppId"
    if (-not (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue)) {
        throw "Missing on-demand task: $taskName"
    }
    Start-ScheduledTask -TaskName $taskName
    [pscustomobject]@{ action='start'; app=$AppId; task=$taskName; mode='hidden_on_demand' } | ConvertTo-Json
    exit 0
}
if ($Action -eq 'stop') {
    $preStopInvoked = $false
    $preStopExit = $null
    if (($app.PSObject.Properties.Name -contains 'pre_stop') -and $null -ne $app.pre_stop) {
        try {
            $prePath = [string]$app.pre_stop.path
            if (-not (Test-Path -LiteralPath $prePath)) { throw "pre_stop helper missing: $prePath" }
            $preArgs = @()
            if ($app.pre_stop.PSObject.Properties.Name -contains 'arguments') { $preArgs = @($app.pre_stop.arguments) }
            $preStopInvoked = $true
            if ([IO.Path]::GetExtension($prePath) -ieq '.ps1') {
                & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $prePath @preArgs | Out-Null
            } else {
                & $prePath @preArgs | Out-Null
            }
            $preStopExit = $LASTEXITCODE
        } catch { $preStopExit = -1 }
    }
    $procs = Get-AppProcesses
    foreach ($proc in $procs) {
        try { $null = $proc.CloseMainWindow() } catch {}
    }
    if ($procs.Count -gt 0) { Start-Sleep -Seconds 3 }
    Get-AppProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
    if (($app.PSObject.Properties.Name -contains 'managed_pid_file') -and -not [string]::IsNullOrWhiteSpace([string]$app.managed_pid_file)) {
        Remove-Item -LiteralPath ([string]$app.managed_pid_file) -Force -ErrorAction SilentlyContinue
    }
    if (($app.PSObject.Properties.Name -contains 'post_launch') -and $null -ne $app.post_launch) {
        Get-Process -Name $app.post_launch.process -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    }
    [pscustomobject]@{ action='stop'; app=$AppId; running=@(Get-AppProcesses).Count; pre_stop_invoked=$preStopInvoked; pre_stop_exit=$preStopExit } | ConvertTo-Json
    exit 0
}

$procs = Get-AppProcesses
$postRunning = $false
if (($app.PSObject.Properties.Name -contains 'post_launch') -and $null -ne $app.post_launch) {
    $postRunning = [bool](Get-Process -Name $app.post_launch.process -ErrorAction SilentlyContinue)
}
[pscustomobject]@{
    action='status'
    app=$AppId
    process=$(if (($app.PSObject.Properties.Name -contains 'automation_process') -and $app.automation_process) { [string]$app.automation_process } else { [string]$app.process })
    running=$procs.Count
    pids=@($procs | ForEach-Object Id)
    post_launch_running=$postRunning
    mode=$manifest.policy.launch_mode
} | ConvertTo-Json -Depth 4
