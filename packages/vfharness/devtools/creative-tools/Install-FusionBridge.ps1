[CmdletBinding()]
param([switch]$Rollback)

$ErrorActionPreference = 'Stop'
$SourceRoot = 'D:\Velvet\Tools\CreativeTools\FusionMCPSample'
$AddinSource = Join-Path $SourceRoot 'Fusion MCP Addin'
$AddinRoot = Join-Path $env:APPDATA 'Autodesk\FusionAddins'
$AddinTarget = Join-Path $AddinRoot 'Fusion MCP Addin'
$LegacyAddinTarget = Join-Path $env:APPDATA 'Autodesk\Autodesk Fusion\API\AddIns\Fusion MCP Addin'
$StateRoot = 'D:\Velvet\State\CreativeTools\Fusion'
$BackupRoot = Join-Path $StateRoot 'backups'
$StatePath = Join-Path $StateRoot 'deployment-state.json'
$ManifestPath = 'D:\Velvet\Runtime\Autostart\dcc-desktop-hosts.json'
$ShortcutPath = 'D:\Velvet\Runtime\Autostart\Autodesk Fusion - VelvetOS.lnk'
$TaskName = 'VelvetOS DCC OnDemand fusion'
$ExpectedUpstream = '1d49ee8f7744b2e7aaec91f9c660c65963fccd71'
$ExpectedPatch = '4285B99F0BA9D506562B96622E9A13B40AD60A82867A068E3025751386956CFF'
$PatchPath = Join-Path $PSScriptRoot 'fusion-mcp-0.1.0-hardening.patch'
$HostWrapperSource = Join-Path $PSScriptRoot 'Start-VelvetFusionHost.ps1'
$HostWrapperRuntime = 'D:\Velvet\Runtime\Autostart\Start-VelvetFusionHost.ps1'
$SafeWrapperSource = Join-Path $PSScriptRoot 'Invoke-FusionNativeSafe.mjs'
$SafeRuntimeDir = 'D:\Velvet\Runtime\CreativeTools\Fusion'
$SafeWrapperRuntime = Join-Path $SafeRuntimeDir 'Invoke-FusionNativeSafe.mjs'

New-Item -ItemType Directory -Force -Path $StateRoot,$BackupRoot | Out-Null

function Write-JsonAtomic([string]$Path, $Value) {
    $tmp = "$Path.tmp.$PID"
    $Value | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $tmp -Encoding UTF8
    Move-Item -Force -LiteralPath $tmp -Destination $Path
}

$runtimeUser = [string](Get-Content -Raw -LiteralPath $ManifestPath | ConvertFrom-Json).user
if (-not $runtimeUser) { throw 'DCC host manifest has no runtime user.' }
$runtimeSid = (New-Object System.Security.Principal.NTAccount($runtimeUser)).Translate([System.Security.Principal.SecurityIdentifier]).Value
$profileKey = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\$runtimeSid"
$runtimeProfile = [Environment]::ExpandEnvironmentVariables([string](Get-ItemProperty -LiteralPath $profileKey -Name ProfileImagePath).ProfileImagePath)
if (-not $runtimeProfile -or -not (Test-Path -LiteralPath $runtimeProfile)) {
    throw "Runtime user profile not found for $runtimeUser"
}
$runtimeRoaming = Join-Path $runtimeProfile 'AppData\Roaming'
$runtimeLocal = Join-Path $runtimeProfile 'AppData\Local'
$AddinRoot = Join-Path $runtimeRoaming 'Autodesk\FusionAddins'
$AddinTarget = Join-Path $AddinRoot 'Fusion MCP Addin'
$LegacyAddinTarget = Join-Path $runtimeRoaming 'Autodesk\Autodesk Fusion\API\AddIns\Fusion MCP Addin'
$productionRoot = Join-Path $runtimeLocal 'Autodesk\webdeploy\production'
$vendorShortcut = Join-Path $runtimeRoaming 'Microsoft\Windows\Start Menu\Programs\Autodesk\Autodesk Fusion.lnk'

if ($Rollback) {
    if (Get-Process -Name 'Fusion360' -ErrorAction SilentlyContinue) {
        throw 'Rollback blocked while Fusion is running.'
    }
    if (-not (Test-Path -LiteralPath $StatePath)) { throw 'No Fusion deployment state exists.' }
    $state = Get-Content -Raw -LiteralPath $StatePath | ConvertFrom-Json
    if ($state.manifest_backup -and (Test-Path -LiteralPath $state.manifest_backup)) {
        Copy-Item -Force -LiteralPath $state.manifest_backup -Destination $ManifestPath
    }
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Remove-Item -Force -LiteralPath $ShortcutPath -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $AddinTarget) { Remove-Item -Recurse -Force -LiteralPath $AddinTarget }
    if ($state.addin_backup -and (Test-Path -LiteralPath $state.addin_backup)) {
        Move-Item -LiteralPath $state.addin_backup -Destination $AddinTarget
    }
    if ($state.legacy_addin_backup -and (Test-Path -LiteralPath $state.legacy_addin_backup)) {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $LegacyAddinTarget) | Out-Null
        Move-Item -LiteralPath $state.legacy_addin_backup -Destination $LegacyAddinTarget
    }
    [pscustomobject]@{status='ROLLED_BACK';manifest=$ManifestPath;task=$TaskName} | ConvertTo-Json
    exit 0
}

if ((git -C $SourceRoot rev-parse HEAD).Trim() -ne $ExpectedUpstream) {
    throw 'Fusion upstream checkout is not at the pinned commit.'
}
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $PatchPath).Hash -ne $ExpectedPatch) {
    throw 'Fusion hardening patch checksum mismatch.'
}
if (Select-String -LiteralPath (Join-Path $AddinSource 'tools\__init__.py') -Pattern 'execute_api_script') {
    throw 'Raw execute_api_script is still exposed.'
}

if (-not (Test-Path -LiteralPath $SafeWrapperSource)) {
    throw 'Fusion safe native MCP wrapper is missing.'
}


$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$addinBackup = $null
$legacyBackup = $null
New-Item -ItemType Directory -Force -Path $AddinRoot | Out-Null
if (Test-Path -LiteralPath $AddinTarget) {
    $addinBackup = Join-Path $BackupRoot "addin-$stamp"
    Move-Item -LiteralPath $AddinTarget -Destination $addinBackup
}
if (Test-Path -LiteralPath $LegacyAddinTarget) {
    $legacyManifest = Join-Path $LegacyAddinTarget 'Fusion MCP Addin.manifest'
    $legacyOwned = $false
    if (Test-Path -LiteralPath $legacyManifest) {
        try { $legacyOwned = ((Get-Content -Raw -LiteralPath $legacyManifest | ConvertFrom-Json).id -eq '183cc1d9-c94d-411f-be15-5a4790658d52') } catch {}
    }
    if ($legacyOwned) {
        $legacyBackup = Join-Path $BackupRoot "legacy-addin-$stamp"
        Move-Item -LiteralPath $LegacyAddinTarget -Destination $legacyBackup
    }
}
Copy-Item -Recurse -Force -LiteralPath $AddinSource -Destination $AddinTarget
Get-ChildItem -LiteralPath $AddinTarget -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
$exeCandidates = @()
foreach ($dir in @(Get-ChildItem -LiteralPath $productionRoot -Directory -ErrorAction SilentlyContinue)) {
    $exe = Join-Path $dir.FullName 'Fusion360.exe'
    if (Test-Path -LiteralPath $exe) {
        $item = Get-Item -LiteralPath $exe
        $exeCandidates += [pscustomobject]@{exe=$exe;version=$item.VersionInfo.ProductVersion;written=$item.LastWriteTimeUtc}
    }
}
$fusionExe = $exeCandidates | Sort-Object written -Descending | Select-Object -First 1
if (-not $fusionExe) { throw 'No live Fusion360.exe installation was found.' }

$wsh = New-Object -ComObject WScript.Shell
$launcher = $null
if (Test-Path -LiteralPath $vendorShortcut) {
    $vendorLink = $wsh.CreateShortcut($vendorShortcut)
    $rawTarget = [string]$vendorLink.TargetPath
    if ($rawTarget) {
        $needle = '\Autodesk\webdeploy\production\'
        $idx = $rawTarget.IndexOf($needle, [StringComparison]::OrdinalIgnoreCase)
        if ($idx -ge 0) {
            $relative = $rawTarget.Substring($idx + $needle.Length)
            $mappedTarget = Join-Path $productionRoot $relative
            if (Test-Path -LiteralPath $mappedTarget) { $launcher = $mappedTarget }
        }
        if (-not $launcher -and (Test-Path -LiteralPath $rawTarget)) {
            $launcher = $rawTarget
        }
    }
}
if (-not $launcher) {
    $siblingLauncher = Join-Path (Split-Path -Parent $fusionExe.exe) 'FusionLauncher.exe'
    if (Test-Path -LiteralPath $siblingLauncher) { $launcher = $siblingLauncher }
}
if (-not $launcher) {
    $launcher = Get-ChildItem -LiteralPath $productionRoot -Recurse -Filter 'FusionLauncher.exe' -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTimeUtc -Descending | Select-Object -ExpandProperty FullName -First 1
}
if (-not $launcher) { throw 'No FusionLauncher.exe was found.' }
$fusion = [pscustomobject]@{exe=$fusionExe.exe;version=$fusionExe.version;launcher=$launcher}

$link = $wsh.CreateShortcut($ShortcutPath)
$link.TargetPath = $fusion.launcher
$link.WorkingDirectory = Split-Path -Parent $fusion.launcher
$link.Description = 'VelvetOS managed hidden on-demand launcher for Autodesk Fusion'
$link.Save()
Copy-Item -Force -LiteralPath $HostWrapperSource -Destination $HostWrapperRuntime
New-Item -ItemType Directory -Force -Path $SafeRuntimeDir | Out-Null
Copy-Item -Force -LiteralPath $SafeWrapperSource -Destination $SafeWrapperRuntime

$manifestBackup = Join-Path $BackupRoot "dcc-desktop-hosts-$stamp.json"
Copy-Item -Force -LiteralPath $ManifestPath -Destination $manifestBackup
$manifest = Get-Content -Raw -LiteralPath $ManifestPath | ConvertFrom-Json
$app = $manifest.apps | Where-Object {$_.id -eq 'fusion'} | Select-Object -First 1
if (-not $app) {
    $app = [pscustomobject]@{id='fusion';enabled=$true;process='Fusion360';path=$ShortcutPath}
    $manifest.apps += $app
} else {
    $app.enabled = $true
    $app.process = 'Fusion360'
    $app.path = $ShortcutPath
    if ($app.PSObject.Properties['reason']) { $app.PSObject.Properties.Remove('reason') }
}
Write-JsonAtomic $ManifestPath $manifest

$taskArgs = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "D:\Velvet\Runtime\Autostart\Start-VelvetFusionHost.ps1"'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $taskArgs
$principal = New-ScheduledTaskPrincipal -UserId $runtimeUser -LogonType Interactive -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName $TaskName -Action $action -Principal $principal -Settings $settings -Force -ErrorAction Stop | Out-Null
$validate = & 'D:\Velvet\Runtime\Autostart\Start-VelvetDccDesktopHosts.ps1' -ValidateOnly
if ($LASTEXITCODE -ne 0) { throw 'DCC host manifest validation failed after Fusion merge.' }

$state = [ordered]@{
    schema = 'velvetos.creative-tools.fusion-deployment-state.v1'
    deployed_at = (Get-Date).ToString('o')
    upstream_commit = $ExpectedUpstream
    adapter_version = 'fusion-native-1.0.0+velvet-safe-0.1.0'
    manifest_backup = $manifestBackup
    addin_backup = $addinBackup
    legacy_addin_backup = $legacyBackup
    addin_target = $AddinTarget
    shortcut = $ShortcutPath
    shortcut_target = $fusion.launcher
    fusion_executable = $fusion.exe
    fusion_executable_version = $fusion.version
    task = $TaskName
    host_wrapper = $HostWrapperRuntime
    safe_wrapper = $SafeWrapperRuntime
}
Write-JsonAtomic $StatePath $state

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
[pscustomobject]@{
    status = 'INSTALLED'
    adapter_version = 'fusion-native-1.0.0+velvet-safe-0.1.0'
    fusion_version = $fusion.version
    addin = $AddinTarget
    shortcut = $ShortcutPath
    task = $TaskName
    task_triggers = $task.Triggers.Count
    launch_mode = 'hidden_on_demand'
    safe_wrapper = $SafeWrapperRuntime
    manifest_validation = $validate
} | ConvertTo-Json -Depth 6
