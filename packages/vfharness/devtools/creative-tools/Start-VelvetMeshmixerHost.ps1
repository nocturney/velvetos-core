[CmdletBinding()]
param([int]$StartupTimeoutSeconds = 60)

$ErrorActionPreference = 'Stop'
$ShortcutPath = 'D:\Velvet\Runtime\Autostart\Autodesk Meshmixer - VelvetOS.lnk'
$Adapter = 'D:\Velvet\Tools\CreativeTools\Meshmixer\adapter-0.1.0\VelvetMeshmixerAdapter.exe'
$LogDir = 'D:\Velvet\Logs\CreativeTools\Meshmixer'
$LogPath = Join-Path $LogDir ('meshmixer-host-' + (Get-Date -Format 'yyyyMMdd') + '.log')
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Log([string]$m) {
    Add-Content -LiteralPath $LogPath -Encoding UTF8 -Value ('{0:o} {1}' -f (Get-Date), $m)
}

Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class VelvetMeshmixerWindow {
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}
'@ -ErrorAction SilentlyContinue

function Hide-Meshmixer {
    foreach ($proc in @(Get-Process meshmixer -ErrorAction SilentlyContinue)) {
        try {
            $proc.Refresh()
            if ($proc.MainWindowHandle -ne 0) {
                [VelvetMeshmixerWindow]::ShowWindow($proc.MainWindowHandle, 0) | Out-Null
            }
        } catch {}
    }
}

$identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name
$session=[Diagnostics.Process]::GetCurrentProcess().SessionId
Log "CONTEXT wrapper_pid=$PID identity=$identity session=$session"

if (-not (Test-Path -LiteralPath $ShortcutPath)) { throw "Managed Meshmixer shortcut missing: $ShortcutPath" }
if (-not (Test-Path -LiteralPath $Adapter)) { throw "Meshmixer adapter missing: $Adapter" }

$p=Get-Process meshmixer -ErrorAction SilentlyContinue | Select-Object -First 1
if(-not $p) {
    Start-Process -FilePath 'explorer.exe' -ArgumentList ('"' + $ShortcutPath + '"') | Out-Null
    Log "LAUNCH shortcut=$ShortcutPath"
} else {
    Log "SKIP running pid=$($p.Id)"
}

$deadline=(Get-Date).AddSeconds($StartupTimeoutSeconds)
$udpReady=$false
$probeReady=$false
do {
    $p=Get-Process meshmixer -ErrorAction SilentlyContinue | Select-Object -First 1
    if($p) {
        Hide-Meshmixer
        try { $p.Refresh() } catch {}
        try {
            $udpReady=[bool](Get-NetUDPEndpoint -LocalPort 45007 -ErrorAction Stop |
                Where-Object {$_.LocalAddress -eq '127.0.0.1' -and $_.OwningProcess -eq $p.Id} |
                Select-Object -First 1)
        } catch { $udpReady=$false }

        if($p.Responding -and $udpReady) {
            try {
                $raw=& $Adapter probe
                $code=$LASTEXITCODE
                $j=$raw | ConvertFrom-Json
                $probeReady=($code -eq 0 -and $j.ok -eq $true)
            } catch { $probeReady=$false }
        }
    }
    if($p -and $p.Responding -and $udpReady -and $probeReady) { break }
    Start-Sleep -Milliseconds 500
} while((Get-Date)-lt $deadline)

if(-not $p) { Log 'FAIL process missing'; throw 'Meshmixer process did not appear before timeout.' }
if(-not $p.Responding) { Log "FAIL not responding pid=$($p.Id)"; throw 'Meshmixer did not become responsive.' }
if(-not $udpReady) { Log "FAIL udp45007 pid=$($p.Id)"; throw 'Meshmixer mm-api UDP listener did not become ready.' }
if(-not $probeReady) { Log "FAIL adapter_probe pid=$($p.Id)"; throw 'Meshmixer read-only adapter probe failed.' }

Hide-Meshmixer
$p.Refresh()
$hidden=($p.MainWindowHandle -eq 0)
Log "READY pid=$($p.Id) udp=127.0.0.1:45007 adapter_probe=True hidden=$hidden"
[pscustomobject]@{status='READY';pid=$p.Id;udp='127.0.0.1:45007';adapter_probe=$true;hidden=$hidden} | ConvertTo-Json
