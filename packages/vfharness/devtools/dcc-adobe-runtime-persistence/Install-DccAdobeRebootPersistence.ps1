param(
    [string]$InteractiveUser = 'CHRIS\Chris',
    [string]$RuntimeRoot = 'D:\Velvet\Runtime\Autostart',
    [switch]$ValidateOnly
)

$ErrorActionPreference = 'Stop'
$SourceRoot = $PSScriptRoot
$GatewaySource = Join-Path $SourceRoot 'Start-VelvetDccGateway.ps1'
$PhotoshopSource = Join-Path $SourceRoot 'Start-AdobePyBroker-Photoshop.ps1'
$GatewayTarget = Join-Path $RuntimeRoot 'Start-VelvetDccGateway.ps1'
$PhotoshopTarget = Join-Path $RuntimeRoot 'Start-AdobePyBroker-Photoshop.ps1'

function Get-TaskSummary {
    param([string]$Name)
    $task = Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
    if (-not $task) {
        return [pscustomobject]@{ name = $Name; exists = $false }
    }
    $info = $task | Get-ScheduledTaskInfo
    [pscustomobject]@{
        name = $Name
        exists = $true
        state = [string]$task.State
        last_task_result = $info.LastTaskResult
        principal = [string]$task.Principal.UserId
        logon_type = [string]$task.Principal.LogonType
        action = (($task.Actions | ForEach-Object { ($_.Execute + ' ' + $_.Arguments).Trim() }) -join ' || ')
        trigger_types = @($task.Triggers | ForEach-Object { $_.CimClass.CimClassName })
    }
}

foreach ($required in @($GatewaySource, $PhotoshopSource)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Missing deployment source: $required"
    }
}

if ($ValidateOnly) {
    $gatewayLive = Test-Path -LiteralPath $GatewayTarget
    $photoshopLive = Test-Path -LiteralPath $PhotoshopTarget
    [pscustomobject]@{
        status = if ($gatewayLive -and $photoshopLive) { 'PASS' } else { 'BLOCKED' }
        runtime_root = $RuntimeRoot
        interactive_user = $InteractiveUser
        gateway = [pscustomobject]@{
            source_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $GatewaySource).Hash
            target_exists = $gatewayLive
            target_sha256 = if ($gatewayLive) { (Get-FileHash -Algorithm SHA256 -LiteralPath $GatewayTarget).Hash } else { $null }
            task = Get-TaskSummary -Name 'VelvetOS DCC Gateway'
        }
        photoshop_broker = [pscustomobject]@{
            source_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $PhotoshopSource).Hash
            target_exists = $photoshopLive
            target_sha256 = if ($photoshopLive) { (Get-FileHash -Algorithm SHA256 -LiteralPath $PhotoshopTarget).Hash } else { $null }
            task = Get-TaskSummary -Name 'VelvetOS AdobePy Broker Photoshop'
        }
    } | ConvertTo-Json -Depth 7
    exit 0
}

New-Item -ItemType Directory -Force -Path $RuntimeRoot | Out-Null
Copy-Item -LiteralPath $GatewaySource -Destination $GatewayTarget -Force
Copy-Item -LiteralPath $PhotoshopSource -Destination $PhotoshopTarget -Force

$gatewayAction = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $GatewayTarget + '"')
$gatewayTrigger = New-ScheduledTaskTrigger -AtStartup
$gatewayPrincipal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
$gatewaySettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName 'VelvetOS DCC Gateway' -Action $gatewayAction -Trigger $gatewayTrigger -Principal $gatewayPrincipal -Settings $gatewaySettings -Description 'Starts the VelvetOS DCC-MCP loopback gateway at Windows boot before user login.' -Force | Out-Null

$photoshopAction = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $PhotoshopTarget + '"')
$photoshopTrigger = New-ScheduledTaskTrigger -AtLogOn -User $InteractiveUser
$photoshopPrincipal = New-ScheduledTaskPrincipal -UserId $InteractiveUser -LogonType Interactive -RunLevel Highest
$photoshopSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName 'VelvetOS AdobePy Broker Photoshop' -Action $photoshopAction -Trigger $photoshopTrigger -Principal $photoshopPrincipal -Settings $photoshopSettings -Description 'VelvetOS AdobePy 0.6.2 broker for Photoshop first-party UXP bridge, interactive user session, loopback only.' -Force | Out-Null

& $PSCommandPath -InteractiveUser $InteractiveUser -RuntimeRoot $RuntimeRoot -ValidateOnly