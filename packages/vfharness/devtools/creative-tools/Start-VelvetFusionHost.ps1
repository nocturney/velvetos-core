[CmdletBinding()]
param([int]$StartupTimeoutSeconds = 120)

$ErrorActionPreference = 'Stop'
$ShortcutPath = 'D:\Velvet\Runtime\Autostart\Autodesk Fusion - VelvetOS.lnk'
$LogDir = 'D:\Velvet\Logs\CreativeTools\Fusion'
$LogPath = Join-Path $LogDir ('fusion-host-' + (Get-Date -Format 'yyyyMMdd') + '.log')
$FusionLogRoot = Join-Path $env:LOCALAPPDATA 'Autodesk\Autodesk Fusion 360'
$NativeMcpPort = 27182

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$runtimeIdentity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$runtimeSession = [Diagnostics.Process]::GetCurrentProcess().SessionId

function Write-FusionLog([string]$Message) {
    Add-Content -LiteralPath $LogPath -Encoding UTF8 -Value ('{0:o} {1}' -f (Get-Date), $Message)
}

Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class VelvetFusionWindow {
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}
'@ -ErrorAction SilentlyContinue

function Hide-FusionWindows {
    foreach ($proc in @(Get-Process -Name 'Fusion360' -ErrorAction SilentlyContinue)) {
        try {
            $proc.Refresh()
            if ($proc.MainWindowHandle -ne 0) {
                [VelvetFusionWindow]::ShowWindow($proc.MainWindowHandle, 0) | Out-Null
            }
        } catch {}
    }
}

function Find-FusionAppLog($FusionProc) {
    Get-ChildItem -LiteralPath $FusionLogRoot -Directory -ErrorAction SilentlyContinue |
        ForEach-Object {
            $logs = Join-Path $_.FullName 'logs'
            if (Test-Path -LiteralPath $logs) {
                Get-ChildItem -LiteralPath $logs -Filter 'AppLogFile*.log' -File -ErrorAction SilentlyContinue
            }
        } |
        Where-Object { $_.CreationTime -ge $FusionProc.StartTime.AddSeconds(-5) } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -ExpandProperty FullName -First 1
}

Write-FusionLog "CONTEXT wrapper_pid=$PID identity=$runtimeIdentity session=$runtimeSession"

if (-not (Test-Path -LiteralPath $ShortcutPath)) {
    throw "Managed Fusion shortcut missing: $ShortcutPath"
}
$wsh = New-Object -ComObject WScript.Shell
$link = $wsh.CreateShortcut($ShortcutPath)
$launcher = [string]$link.TargetPath
if (-not (Test-Path -LiteralPath $launcher)) {
    throw "Fusion launcher missing: $launcher"
}

$existing = @(Get-Process -Name 'Fusion360' -ErrorAction SilentlyContinue)
if ($existing.Count -eq 0) {
    Start-Process -FilePath 'explorer.exe' -ArgumentList ('"' + $ShortcutPath + '"') | Out-Null
    Write-FusionLog "LAUNCH shell=explorer shortcut=$ShortcutPath target=$launcher"
} else {
    Write-FusionLog "SKIP running fusion_pid=$($existing[0].Id)"
}

$deadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
$fusionSeen = $false
$applicationUiReadyObserved = $false
$nativeMcpReady = $false
$fusionAppLog = $null
$fusionProc = $null

do {
    $fusion = @(Get-Process -Name 'Fusion360' -ErrorAction SilentlyContinue)
    if ($fusion.Count -gt 0) {
        $fusionSeen = $true
        $fusionProc = $fusion[0]
        Hide-FusionWindows

        if (-not $fusionAppLog -or -not (Test-Path -LiteralPath $fusionAppLog)) {
            $fusionAppLog = Find-FusionAppLog $fusionProc
        }

        if (-not $applicationUiReadyObserved -and $fusionAppLog -and (Test-Path -LiteralPath $fusionAppLog)) {
            try {
                $tail = Get-Content -LiteralPath $fusionAppLog -Tail 240 -ErrorAction Stop
                if ($tail | Select-String -SimpleMatch 'PERF: ApplicationUIReady') {
                    $applicationUiReadyObserved = $true
                    Write-FusionLog "APPLICATION_UI_READY_OBSERVED fusion_pid=$($fusionProc.Id) log=$fusionAppLog"
                } elseif ($tail | Select-String -SimpleMatch 'PERF: ModelingReady') {
                    $applicationUiReadyObserved = $true
                    Write-FusionLog "MODELING_READY_FALLBACK fusion_pid=$($fusionProc.Id) log=$fusionAppLog"
                } elseif ($tail | Select-String -SimpleMatch 'PERF: ApplicationReady') {
                    $applicationUiReadyObserved = $true
                    Write-FusionLog "APPLICATION_READY_FALLBACK fusion_pid=$($fusionProc.Id) log=$fusionAppLog"
                }
            } catch {}
        }

        try {
            $nativeMcpReady = [bool](Get-NetTCPConnection -State Listen -LocalAddress '127.0.0.1' -LocalPort $NativeMcpPort -ErrorAction Stop |
                Where-Object { $_.OwningProcess -eq $fusionProc.Id } |
                Select-Object -First 1)
        } catch {
            $nativeMcpReady = $false
        }
    }

    if ($fusionSeen -and $applicationUiReadyObserved -and $nativeMcpReady) {
        break
    }
    Start-Sleep -Milliseconds 500
} while ((Get-Date) -lt $deadline)

if (-not $fusionSeen) {
    Write-FusionLog 'FAIL Fusion360 process did not appear before timeout'
    throw 'Fusion360 process did not appear before timeout.'
}
if (-not $applicationUiReadyObserved) {
    Write-FusionLog 'FAIL Fusion ApplicationUIReady evidence was not observed before timeout'
    throw 'Fusion ApplicationUIReady evidence was not observed before timeout.'
}
if (-not $nativeMcpReady) {
    Write-FusionLog "FAIL Autodesk native MCP listener 127.0.0.1:$NativeMcpPort was not owned by Fusion before timeout"
    throw 'Autodesk native Fusion MCP did not become ready before timeout.'
}

$fusionProc.Refresh()
Hide-FusionWindows
$fusionProc.Refresh()
$hidden = ($fusionProc.MainWindowHandle -eq 0)
Write-FusionLog "READY fusion_pid=$($fusionProc.Id) native_mcp=127.0.0.1:$NativeMcpPort app_ui_ready=True hidden=$hidden"

[pscustomobject]@{
    status = 'READY'
    fusion_pid = $fusionProc.Id
    native_mcp = "http://127.0.0.1:$NativeMcpPort/mcp"
    app_ui_ready = $true
    hidden = $hidden
} | ConvertTo-Json
