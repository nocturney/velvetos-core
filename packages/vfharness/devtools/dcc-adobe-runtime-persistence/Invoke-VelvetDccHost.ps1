param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('start','stop','status')]
    [string]$Action,
    [Parameter(Mandatory=$true)]
    [string]$AppId
)

$ErrorActionPreference = 'Stop'
$ManifestPath = 'D:\Velvet\Runtime\Autostart\dcc-desktop-hosts.json'
$manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$app = $manifest.apps | Where-Object { $_.id -eq $AppId } | Select-Object -First 1
if (-not $app) { throw "Unknown DCC app id: $AppId" }
if (-not $app.enabled) { throw "DCC app is disabled: $AppId ($($app.reason))" }

function Get-AppProcesses {
    @(Get-Process -Name $app.process -ErrorAction SilentlyContinue)
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
    $procs = Get-AppProcesses
    foreach ($proc in $procs) {
        try { $null = $proc.CloseMainWindow() } catch {}
    }
    if ($procs.Count -gt 0) { Start-Sleep -Seconds 3 }
    Get-AppProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
    if (($app.PSObject.Properties.Name -contains 'post_launch') -and $null -ne $app.post_launch) {
        Get-Process -Name $app.post_launch.process -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    }
    [pscustomobject]@{ action='stop'; app=$AppId; running=@(Get-AppProcesses).Count } | ConvertTo-Json
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
    process=$app.process
    running=$procs.Count
    pids=@($procs | ForEach-Object Id)
    post_launch_running=$postRunning
    mode=$manifest.policy.launch_mode
} | ConvertTo-Json -Depth 4
