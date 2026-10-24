param(
    [string]$InteractiveUser = 'CHRIS\Chris',
    [string]$RuntimeRoot = 'D:\Velvet\Runtime\Autostart',
    [switch]$ValidateOnly
)

$ErrorActionPreference = 'Stop'
$SourceRoot = $PSScriptRoot
$GatewaySource = Join-Path $SourceRoot 'Start-VelvetDccGateway.ps1'
$DesktopSource = Join-Path $SourceRoot 'Start-VelvetDccDesktopHosts.ps1'
$ManagerSource = Join-Path $SourceRoot 'Invoke-VelvetDccHost.ps1'
$ManifestSource = Join-Path $SourceRoot 'dcc-desktop-hosts.json'
$GatewayTarget = Join-Path $RuntimeRoot 'Start-VelvetDccGateway.ps1'
$DesktopTarget = Join-Path $RuntimeRoot 'Start-VelvetDccDesktopHosts.ps1'
$ManagerTarget = Join-Path $RuntimeRoot 'Invoke-VelvetDccHost.ps1'
$ManifestTarget = Join-Path $RuntimeRoot 'dcc-desktop-hosts.json'

$ObsoleteTasks = @(
    'VelvetOS Acceptance Launch Illustrator',
    'VelvetOS DCC Launch AutoCAD Once',
    'VelvetOS DCC Launch Cinema4D Once',
    'VelvetOS Temp AfterEffects Acceptance Launch',
    'VelvetOS Temp Illustrator Acceptance Launch',
    'VelvetOS Temp Photoshop Reconnect',
    'VelvetOS Temp ZBrush Reconnect',
    'VelvetOS DCC OnDemand 3dsmax',
    'VelvetOS DCC OnDemand autocad',
    'VelvetOS DCC OnDemand inventor',
    'VelvetOS DCC OnDemand maya',
    'VelvetOS DCC OnDemand photoshop',
    'VelvetOS DCC OnDemand illustrator',
    'VelvetOS DCC OnDemand aftereffects',
    'VelvetOS DCC OnDemand premiere',
    'VelvetOS DCC OnDemand substance-painter',
    'VelvetOS DCC OnDemand substance-designer',
    'VelvetOS DCC OnDemand substance-modeler',
    'VelvetOS DCC OnDemand substance-sampler',
    'VelvetOS DCC OnDemand substance-stager',
    'VelvetOS AdobePy Broker Photoshop',
    'VelvetOS AdobePy Broker Illustrator',
    'VelvetOS AdobePy Broker AfterEffects',
    'VelvetOS AfterEffects Readonly Surface',
    'VelvetOS Illustrator Readonly Agent',
    'VelvetOS DCC Update Sentinel'
)

function Get-TaskSummary {
    param([string]$Name)
    $task = Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
    if (-not $task) { return [pscustomobject]@{ name=$Name; exists=$false } }
    $info = $task | Get-ScheduledTaskInfo
    $triggerTypes = @($task.Triggers | ForEach-Object { $_.CimClass.CimClassName } | Where-Object { $_ })
    [pscustomobject]@{
        name = $Name
        exists = $true
        state = [string]$task.State
        last_task_result = $info.LastTaskResult
        principal = [string]$task.Principal.UserId
        logon_type = [string]$task.Principal.LogonType
        action = (($task.Actions | ForEach-Object { ($_.Execute + ' ' + $_.Arguments).Trim() }) -join ' || ')
        trigger_types = $triggerTypes
    }
}

function Get-OnDemandTaskName {
    param([string]$Id)
    "VelvetOS DCC OnDemand $Id"
}

$ExternalOnDemandContracts = @{
    'fusion' = @('Start-VelvetFusionHost.ps1')
    'meshmixer' = @('Start-VelvetMeshmixerHost.ps1')
    'resolve' = @('Start-VelvetResolveHost.ps1')
    'affinity' = @('Start-VelvetAffinityHost.ps1')
    'coreldraw' = @('Start-VelvetCorelHost.ps1', '-AppId coreldraw')
    'corel-designer' = @('Start-VelvetCorelHost.ps1', '-AppId corel-designer')
}

function Test-OnDemandActionContract {
    param($App, $Summary)
    if (-not $Summary.exists) { return $false }
    $id = [string]$App.id
    if ($ExternalOnDemandContracts.ContainsKey($id)) {
        foreach ($token in @($ExternalOnDemandContracts[$id])) {
            if (-not $Summary.action.Contains([string]$token)) { return $false }
        }
        return $true
    }
    return $Summary.action.Contains("-OnlyAppId $id -HideAfterLaunch")
}

$requiredSources = @($GatewaySource,$DesktopSource,$ManagerSource,$ManifestSource)
foreach ($required in $requiredSources) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Missing deployment source: $required" }
}

if ($ValidateOnly) {
    $pairs = @(
        @($GatewaySource,$GatewayTarget),
        @($DesktopSource,$DesktopTarget),
        @($ManagerSource,$ManagerTarget),
        @($ManifestSource,$ManifestTarget)
    )
    $fileChecks = foreach ($pair in $pairs) {
        $source = $pair[0]; $target = $pair[1]
        $exists = Test-Path -LiteralPath $target
        $sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $source).Hash
        $targetHash = if ($exists) { (Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash } else { $null }
        [pscustomobject]@{ source=$source; target=$target; exists=$exists; source_sha256=$sourceHash; target_sha256=$targetHash; match=($exists -and $sourceHash -eq $targetHash) }
    }
    $manifest = Get-Content $ManifestSource -Raw | ConvertFrom-Json
    $enabledApps = @($manifest.apps | Where-Object enabled)
    $desktop = Get-TaskSummary -Name 'VelvetOS DCC Desktop Hosts'
    $onDemand = foreach ($app in $enabledApps) {
        $summary = Get-TaskSummary -Name (Get-OnDemandTaskName -Id $app.id)
        [pscustomobject]@{
            id=$app.id
            task=$summary
            no_triggers=($summary.exists -and @($summary.trigger_types).Count -eq 0)
            action_contract_ok=(Test-OnDemandActionContract -App $app -Summary $summary)
            owner=$(if ($ExternalOnDemandContracts.ContainsKey([string]$app.id)) { 'creative-tools' } else { 'dcc-runtime' })
        }
    }

    $oldRemaining = @($ObsoleteTasks | Where-Object { Get-ScheduledTask -TaskName $_ -ErrorAction SilentlyContinue })
    $policyOk = ($manifest.policy.launch_mode -eq 'on_demand_hidden' -and
                 $manifest.policy.launch_at_logon -eq $false -and
                 $manifest.policy.agent_hidden_launch -eq $true)
    $desktopOk = ($desktop.exists -and @($desktop.trigger_types).Count -eq 0 -and $desktop.action.Contains('-HideAfterLaunch'))
    $onDemandOk = (@($onDemand | Where-Object { -not $_.no_triggers -or -not $_.action_contract_ok }).Count -eq 0)
    $filesOk = (@($fileChecks | Where-Object { -not $_.match }).Count -eq 0)
    $status = if ($filesOk -and $policyOk -and $desktopOk -and $onDemandOk -and $oldRemaining.Count -eq 0) { 'PASS' } else { 'BLOCKED' }

    [pscustomobject]@{
        status=$status
        runtime_root=$RuntimeRoot
        interactive_user=$InteractiveUser
        files=$fileChecks
        policy_ok=$policyOk
        desktop_hosts=$desktop
        on_demand=$onDemand
        obsolete_tasks_remaining=$oldRemaining
        gateway=(Get-TaskSummary -Name 'VelvetOS DCC Gateway')
    } | ConvertTo-Json -Depth 8
    if ($status -ne 'PASS') { exit 2 }
    exit 0
}

New-Item -ItemType Directory -Force -Path $RuntimeRoot | Out-Null

Copy-Item -LiteralPath $GatewaySource -Destination $GatewayTarget -Force
Copy-Item -LiteralPath $DesktopSource -Destination $DesktopTarget -Force
Copy-Item -LiteralPath $ManagerSource -Destination $ManagerTarget -Force
Copy-Item -LiteralPath $ManifestSource -Destination $ManifestTarget -Force

$gatewayAction = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $GatewayTarget + '"')
$gatewayTrigger = New-ScheduledTaskTrigger -AtStartup
$gatewayPrincipal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
$gatewaySettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName 'VelvetOS DCC Gateway' -Action $gatewayAction -Trigger $gatewayTrigger -Principal $gatewayPrincipal -Settings $gatewaySettings -Description 'Starts the VelvetOS DCC-MCP loopback gateway at Windows boot before user login.' -Force | Out-Null

$desktopPrincipal = New-ScheduledTaskPrincipal -UserId $InteractiveUser -LogonType Interactive -RunLevel Highest
$desktopSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
$desktopAction = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $DesktopTarget + '" -HideAfterLaunch')
$desktopDefinition = New-ScheduledTask -Action $desktopAction -Principal $desktopPrincipal -Settings $desktopSettings -Description 'VelvetOS DCC GUI hosts manual-only hidden launcher. No automatic trigger.'
Register-ScheduledTask -TaskName 'VelvetOS DCC Desktop Hosts' -InputObject $desktopDefinition -Force | Out-Null

$runtimeManifest = Get-Content $ManifestTarget -Raw | ConvertFrom-Json
foreach ($app in @($runtimeManifest.apps | Where-Object enabled)) {
    $taskName = Get-OnDemandTaskName -Id $app.id
    $id = [string]$app.id
    if ($ExternalOnDemandContracts.ContainsKey($id)) {
        $existing = Get-TaskSummary -Name $taskName
        $existingValid = ($existing.exists -and @($existing.trigger_types).Count -eq 0 -and (Test-OnDemandActionContract -App $app -Summary $existing))
        if (-not $existingValid) {
            Write-Warning "External Creative Tools task is missing or invalid and was left untouched: $taskName"
        }
        continue
    }
    $args = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $DesktopTarget + '" -OnlyAppId ' + $app.id + ' -HideAfterLaunch'
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $args
    $description = "VelvetOS hidden on-demand DCC host: $($app.id)"
    $definition = New-ScheduledTask -Action $action -Principal $desktopPrincipal -Settings $desktopSettings -Description $description
    Register-ScheduledTask -TaskName $taskName -InputObject $definition -Force | Out-Null
}

foreach ($name in $ObsoleteTasks) {
    if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $name -Confirm:$false
    }
}

& $PSCommandPath -InteractiveUser $InteractiveUser -RuntimeRoot $RuntimeRoot -ValidateOnly
