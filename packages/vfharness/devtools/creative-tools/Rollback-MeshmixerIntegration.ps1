[CmdletBinding()]
param([switch]$KeepAdapter)

$ErrorActionPreference = 'Stop'
$StatePath = 'D:\Velvet\State\CreativeTools\Meshmixer\deployment-state.json'
$HostManager = 'D:\Velvet\Runtime\Autostart\Invoke-VelvetDccHost.ps1'

if (-not (Test-Path -LiteralPath $StatePath)) {
    throw 'Meshmixer deployment state is missing.'
}
$state = Get-Content -Raw -LiteralPath $StatePath | ConvertFrom-Json

if (Get-Process meshmixer -ErrorAction SilentlyContinue) {
    & $HostManager -Action stop -AppId meshmixer | Out-Null
    $deadline = (Get-Date).AddSeconds(15)
    do {
        if (-not (Get-Process meshmixer -ErrorAction SilentlyContinue)) { break }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
}
if (Get-Process meshmixer -ErrorAction SilentlyContinue) {
    throw 'Rollback blocked because Meshmixer is still running.'
}

Unregister-ScheduledTask -TaskName ([string]$state.task) -Confirm:$false -ErrorAction SilentlyContinue
Remove-Item -Force -LiteralPath ([string]$state.shortcut) -ErrorAction SilentlyContinue
Remove-Item -Force -LiteralPath ([string]$state.host_wrapper) -ErrorAction SilentlyContinue

if ($state.manifest_backup -and (Test-Path -LiteralPath $state.manifest_backup)) {
    Copy-Item -Force -LiteralPath $state.manifest_backup -Destination 'D:\Velvet\Runtime\Autostart\dcc-desktop-hosts.json'
}
if ($state.sentinel_config_backup -and (Test-Path -LiteralPath $state.sentinel_config_backup)) {
    Copy-Item -Force -LiteralPath $state.sentinel_config_backup -Destination 'D:\Velvet\Runtime\UpdateSentinel\dcc-adobe-update-sentinel.json'
}
if ($state.sentinel_script_backup -and (Test-Path -LiteralPath $state.sentinel_script_backup)) {
    Copy-Item -Force -LiteralPath $state.sentinel_script_backup -Destination 'D:\Velvet\Runtime\UpdateSentinel\Invoke-DccAdobeUpdateSentinel.ps1'
}

function Remove-HostState([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return }
    $obj = Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json
    if ($obj.hosts -and $obj.hosts.PSObject.Properties['meshmixer']) {
        $obj.hosts.PSObject.Properties.Remove('meshmixer')
        $tmp = "$Path.tmp.$PID"
        $obj | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $tmp -Encoding UTF8
        Move-Item -Force -LiteralPath $tmp -Destination $Path
    }
}

Remove-HostState 'D:\Velvet\State\DCC-Adobe-Update-Sentinel\accepted-baseline.json'
Remove-HostState 'D:\Velvet\State\DCC-Adobe-Update-Sentinel\routing-state.json'

if (-not $KeepAdapter -and $state.adapter_dir -and (Test-Path -LiteralPath $state.adapter_dir)) {
    Remove-Item -Recurse -Force -LiteralPath $state.adapter_dir
}

[pscustomobject]@{
    status = 'ROLLED_BACK'
    app = 'meshmixer'
    adapter_kept = [bool]$KeepAdapter
    restored_manifest = [bool](Test-Path -LiteralPath $state.manifest_backup)
    restored_sentinel = [bool](Test-Path -LiteralPath $state.sentinel_config_backup)
} | ConvertTo-Json
