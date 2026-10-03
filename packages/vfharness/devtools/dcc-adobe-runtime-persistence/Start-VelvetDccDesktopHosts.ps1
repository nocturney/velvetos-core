param(
    [switch]$ValidateOnly,
    [string]$OnlyAppId,
    [switch]$HideAfterLaunch
)

$ErrorActionPreference = 'Stop'
$ManifestPath = 'D:\Velvet\Runtime\Autostart\dcc-desktop-hosts.json'
$LogDir = 'D:\Velvet\Logs\Autostart'
$LogPath = Join-Path $LogDir ('dcc-desktop-hosts-' + (Get-Date -Format 'yyyyMMdd') + '.log')

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
. 'D:\Velvet\Runtime\Autostart\Set-VelvetDccEnvironment.ps1'

function Write-HostLog {
    param([string]$Message)
    $line = ('{0:o} {1}' -f (Get-Date), $Message)
    Add-Content -Path $LogPath -Value $line -Encoding UTF8
}

Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class VelvetWindow {
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}
'@ -ErrorAction SilentlyContinue

function Get-AppProcess {
    param([string]$Name)
    @(Get-Process -Name $Name -ErrorAction SilentlyContinue)
}

function Minimize-App {
    param([string]$Name)
    $deadline = (Get-Date).AddSeconds(30)
    do {
        $procs = Get-AppProcess -Name $Name
        foreach ($proc in $procs) {
            try {
                $proc.Refresh()
                if ($proc.MainWindowHandle -ne 0) {
                    [VelvetWindow]::ShowWindow($proc.MainWindowHandle, 6) | Out-Null
                    return $true
                }
            } catch {}
        }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    return $false
}

function Hide-App {
    param([string]$Name)
    $deadline = (Get-Date).AddSeconds(30)
    do {
        $hidden = $false
        foreach ($proc in (Get-AppProcess -Name $Name)) {
            try { $proc.Refresh(); if ($proc.MainWindowHandle -ne 0) { [VelvetWindow]::ShowWindow($proc.MainWindowHandle, 0) | Out-Null; $hidden = $true } } catch {}
        }
        if ($hidden) { return $true }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    return $false
}

function Start-InteractiveApp {
    param($App)
    $extension = [IO.Path]::GetExtension([string]$App.path).ToLowerInvariant()
    if ($extension -eq '.lnk') {
        # Route shortcuts through the existing interactive Windows shell. This
        # reproduces a normal user click and avoids the alternate startup
        # context that caused host-specific GUI errors during remote launches.
        Start-Process -FilePath 'explorer.exe' -ArgumentList ('"' + [string]$App.path + '"') | Out-Null
        $deadline = (Get-Date).AddSeconds(45)
        do {
            $procs = Get-AppProcess -Name $App.process
            if ($procs.Count -gt 0) { return $procs[0] }
            Start-Sleep -Milliseconds 500
        } while ((Get-Date) -lt $deadline)
        throw "interactive shell launch did not produce process $($App.process)"
    }
    return Start-Process -FilePath $App.path -WindowStyle Minimized -PassThru
}

function Start-PostLaunch {
    param($App)
    if (-not ($App.PSObject.Properties.Name -contains 'post_launch') -or $null -eq $App.post_launch) {
        return
    }
    $post = $App.post_launch
    $existing = Get-AppProcess -Name $post.process
    if ($existing.Count -gt 0) {
        Write-HostLog "POST SKIP running $($App.id) process=$($post.process) pid=$($existing[0].Id)"
        return
    }
    $delay = [int]$post.delay_seconds
    if ($delay -gt 0) { Start-Sleep -Seconds $delay }
    try {
        $args = @($post.arguments)
        $style = if ([string]::IsNullOrWhiteSpace([string]$post.window_style)) { 'Hidden' } else { [string]$post.window_style }
        $proc = Start-Process -FilePath $post.path -ArgumentList $args -WindowStyle $style -PassThru
        Write-HostLog "POST LAUNCH $($App.id) pid=$($proc.Id) path=$($post.path)"
    } catch {
        Write-HostLog "POST ERROR $($App.id): $($_.Exception.Message)"
    }
}

if (-not (Test-Path $ManifestPath)) {
    Write-HostLog "BLOCKED manifest missing: $ManifestPath"
    exit 2
}

$manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$errors = @()
foreach ($app in $manifest.apps) {
    if (-not $app.enabled) { continue }
    if (-not [string]::IsNullOrWhiteSpace($OnlyAppId) -and $app.id -ne $OnlyAppId) { continue }
    if ([string]::IsNullOrWhiteSpace([string]$app.path) -or -not (Test-Path $app.path)) {
        $errors += "missing executable for $($app.id): $($app.path)"
    }
    if (($app.PSObject.Properties.Name -contains 'post_launch') -and $null -ne $app.post_launch) {
        if ([string]::IsNullOrWhiteSpace([string]$app.post_launch.path) -or -not (Test-Path $app.post_launch.path)) {
            $errors += "missing post-launch executable for $($app.id): $($app.post_launch.path)"
        }
    }
    if (($app.PSObject.Properties.Name -contains 'automation_mode') -and [string]$app.automation_mode -eq 'headless_mayapy') {
        if (-not ($app.PSObject.Properties.Name -contains 'on_demand_launcher') -or
            [string]::IsNullOrWhiteSpace([string]$app.on_demand_launcher) -or
            -not (Test-Path -LiteralPath ([string]$app.on_demand_launcher))) {
            $errors += "missing headless launcher for $($app.id): $($app.on_demand_launcher)"
        }
    }
}

if ($errors.Count -gt 0) {
    foreach ($err in $errors) { Write-HostLog "BLOCKED $err" }
    $errors | ForEach-Object { Write-Output $_ }
    exit 2
}

if ($ValidateOnly) {
    Write-HostLog "PASS validate-only: $(@($manifest.apps | Where-Object enabled).Count) enabled apps"
    [pscustomobject]@{
        status = 'PASS'
        manifest = $ManifestPath
        enabled_apps = @($manifest.apps | Where-Object enabled).Count
        disabled_apps = @($manifest.apps | Where-Object { -not $_.enabled }).Count
        stagger_seconds = [int]$manifest.policy.stagger_seconds
    } | ConvertTo-Json -Depth 4
    exit 0
}

Write-HostLog "START desktop DCC launcher app=$OnlyAppId hidden=$HideAfterLaunch"
if ([string]::IsNullOrWhiteSpace($OnlyAppId)) { Start-Sleep -Seconds 20 }

foreach ($app in $manifest.apps) {
    if (-not $app.enabled) {
        Write-HostLog "SKIP disabled $($app.id): $($app.reason)"
        continue
    }
    if (-not [string]::IsNullOrWhiteSpace($OnlyAppId) -and $app.id -ne $OnlyAppId) {
        continue
    }

    if (($app.PSObject.Properties.Name -contains 'automation_mode') -and [string]$app.automation_mode -eq 'headless_mayapy') {
        try {
            $launcher = [string]$app.on_demand_launcher
            $result = & powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File $launcher
            Write-HostLog "HEADLESS $($app.id) launcher=$launcher result=$result"
        } catch {
            Write-HostLog "ERROR $($app.id) headless launch: $($_.Exception.Message)"
        }
        continue
    }

    $running = Get-AppProcess -Name $app.process
    if ($running.Count -gt 0) {
        $min = if ($HideAfterLaunch) { Hide-App -Name $app.process } else { Minimize-App -Name $app.process }
        Write-HostLog "SKIP running $($app.id) pid=$($running[0].Id) hidden=$HideAfterLaunch window_action=$min"
        Start-PostLaunch -App $app
        continue
    }

    try {
        $proc = $null
        if ($app.id -eq 'illustrator') {
            $bootstrapPython = 'D:\Velvet\Tools\DCC-MCP\illustrator-0.3.1\venv\Scripts\python.exe'
            $bootstrapScript = 'D:\Velvet\Runtime\Autostart\Bootstrap-VelvetIllustrator.py'
            if (-not (Test-Path -LiteralPath $bootstrapPython)) { throw "Illustrator bootstrap Python missing: $bootstrapPython" }
            if (-not (Test-Path -LiteralPath $bootstrapScript)) { throw "Illustrator bootstrap script missing: $bootstrapScript" }
            $bootstrapOut = Join-Path $LogDir ('illustrator-bootstrap-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.stdout.log')
            $bootstrapErr = Join-Path $LogDir ('illustrator-bootstrap-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.stderr.log')
            $bootstrapProc = Start-Process -FilePath $bootstrapPython -ArgumentList @($bootstrapScript) -RedirectStandardOutput $bootstrapOut -RedirectStandardError $bootstrapErr -WindowStyle Hidden -PassThru
            Write-HostLog "BOOTSTRAP illustrator pid=$($bootstrapProc.Id) stdout=$bootstrapOut stderr=$bootstrapErr"

            $bootstrapHost = $null
            $hostDeadline = (Get-Date).AddSeconds(6)
            do {
                $candidateHosts = @(Get-AppProcess -Name $app.process)
                if ($candidateHosts.Count -gt 0) {
                    $bootstrapHost = $candidateHosts[0]
                    Write-HostLog "BOOTSTRAP_HOST_DISCOVERED illustrator pid=$($bootstrapHost.Id)"
                    break
                }
                if ($bootstrapProc.HasExited) { break }
                Start-Sleep -Milliseconds 250
                $bootstrapProc.Refresh()
            } while ((Get-Date) -lt $hostDeadline)

            if (-not $bootstrapHost -and -not $bootstrapProc.HasExited) {
                Write-HostLog "BOOTSTRAP_HOST_PENDING illustrator owner=broker"
            }

            $bootstrapFinished = $bootstrapProc.WaitForExit(40000)
            if (-not $bootstrapFinished) {
                Stop-Process -Id $bootstrapProc.Id -Force -ErrorAction SilentlyContinue
                @(Get-AppProcess -Name $app.process) | Stop-Process -Force -ErrorAction SilentlyContinue
                Write-HostLog "BOOTSTRAP_TIMEOUT illustrator pid=$($bootstrapProc.Id)"
                throw "Illustrator bounded bootstrap timed out"
            }

            if (-not (Test-Path -LiteralPath $bootstrapOut)) {
                @(Get-AppProcess -Name $app.process) | Stop-Process -Force -ErrorAction SilentlyContinue
                throw "Illustrator bootstrap produced no structured output"
            }

            $bootstrapRaw = (Get-Content -Raw -LiteralPath $bootstrapOut).Trim()
            try {
                $bootstrapResult = $bootstrapRaw | ConvertFrom-Json
            } catch {
                @(Get-AppProcess -Name $app.process) | Stop-Process -Force -ErrorAction SilentlyContinue
                Write-HostLog "BOOTSTRAP_PARSE_ERROR illustrator: $($_.Exception.Message)"
                throw "Illustrator bootstrap output was not valid JSON"
            }

            if ($bootstrapResult.ok -ne $true -or -not $bootstrapResult.host.pid) {
                @(Get-AppProcess -Name $app.process) | Stop-Process -Force -ErrorAction SilentlyContinue
                Write-HostLog "BOOTSTRAP_FAIL illustrator result=$bootstrapRaw"
                throw "Illustrator bounded bootstrap failed"
            }

            $verifiedPid = [int]$bootstrapResult.host.pid
            if ($bootstrapHost -and [int]$bootstrapHost.Id -ne $verifiedPid) {
                @(Get-AppProcess -Name $app.process) | Stop-Process -Force -ErrorAction SilentlyContinue
                Write-HostLog "BOOTSTRAP_IDENTITY_MISMATCH illustrator launched_pid=$($bootstrapHost.Id) verified_pid=$verifiedPid"
                throw "Illustrator bootstrap verified a different host PID"
            }

            Start-Sleep -Milliseconds 750
            $candidate = Get-Process -Id $verifiedPid -ErrorAction SilentlyContinue
            if (-not $candidate) {
                throw "Illustrator verified bootstrap host exited before handoff"
            }
            $proc = $candidate
            Write-HostLog "BOOTSTRAP_READY illustrator host_pid=$($proc.Id) status=$($bootstrapResult.bootstrap_status)"
        }
        if (-not $proc) {
            $proc = Start-InteractiveApp -App $app
            Write-HostLog "LAUNCH $($app.id) pid=$($proc.Id) path=$($app.path) shell=$([IO.Path]::GetExtension([string]$app.path).ToLowerInvariant() -eq '.lnk')"
        } else {
            Write-HostLog "LAUNCH $($app.id) pid=$($proc.Id) mode=verified-bootstrap"
        }
        $min = if ($HideAfterLaunch) { Hide-App -Name $app.process } else { Minimize-App -Name $app.process }
        Write-HostLog "WINDOW $($app.id) hidden=$HideAfterLaunch result=$min"
        Start-PostLaunch -App $app
    } catch {
        Write-HostLog "ERROR $($app.id): $($_.Exception.Message)"
    }

    if ([string]::IsNullOrWhiteSpace($OnlyAppId)) { Start-Sleep -Seconds ([int]$manifest.policy.stagger_seconds) }
}

Write-HostLog "DONE desktop DCC autostart"
