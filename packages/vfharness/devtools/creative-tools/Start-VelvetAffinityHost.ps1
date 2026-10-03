[CmdletBinding()]
param([int]$StartupTimeoutSeconds = 90)

$ErrorActionPreference='Stop'
$Shortcut='D:\Velvet\Runtime\Autostart\Affinity - VelvetOS.lnk'
$Python='C:\Python314\python.exe'
$Adapter='D:\Velvet\Runtime\CreativeTools\Affinity\AffinitySafeAdapter.py'
$LogDir='D:\Velvet\Logs\CreativeTools\Affinity'
$Log=Join-Path $LogDir ('affinity-host-'+(Get-Date -Format 'yyyyMMdd')+'.log')
New-Item -ItemType Directory -Force -Path $LogDir|Out-Null

Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class VelvetAffinityWin32 {
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
}
'@

function Log([string]$m){
  Add-Content -LiteralPath $Log -Encoding UTF8 -Value ('{0:o} {1}' -f (Get-Date),$m)
}

$identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name
$session=(Get-Process -Id $PID).SessionId
Log "CONTEXT wrapper_pid=$PID identity=$identity session=$session"

if(-not (Test-Path -LiteralPath $Shortcut)){throw "Managed Affinity shortcut missing: $Shortcut"}
if(-not (Test-Path -LiteralPath $Python)){throw "Python runtime missing: $Python"}
if(-not (Test-Path -LiteralPath $Adapter)){throw "Affinity safe adapter missing: $Adapter"}

$p=Get-Process Affinity -ErrorAction SilentlyContinue |
  Where-Object {$_.SessionId -eq $session} | Select-Object -First 1
if(-not $p){
  Start-Process -FilePath 'explorer.exe' -ArgumentList ('"'+$Shortcut+'"')|Out-Null
  Log "LAUNCH shortcut=$Shortcut"
} else {
  Log "SKIP running pid=$($p.Id)"
}

$deadline=(Get-Date).AddSeconds($StartupTimeoutSeconds)
$listener=$null
do {
  $p=Get-Process Affinity -ErrorAction SilentlyContinue |
    Where-Object {$_.SessionId -eq $session} | Select-Object -First 1
  if($p){
    $p.Refresh()
    if($p.MainWindowHandle -ne 0){
      [VelvetAffinityWin32]::ShowWindow($p.MainWindowHandle,0)|Out-Null
    }
    $listener=Get-NetTCPConnection -State Listen -LocalPort 6767 -ErrorAction SilentlyContinue |
      Where-Object {$_.OwningProcess -eq $p.Id -and $_.LocalAddress -eq '127.0.0.1'} |
      Select-Object -First 1
  }
  if($p -and $p.Responding -and $listener){break}
  Start-Sleep -Milliseconds 400
} while((Get-Date)-lt $deadline)

if(-not $p){throw 'Affinity process did not appear before timeout'}
if(-not $p.Responding){throw 'Affinity did not become responsive'}
if(-not $listener){throw 'Affinity MCP listener 127.0.0.1:6767 did not become ready'}

for($i=0;$i -lt 12;$i++){
  $p.Refresh()
  if($p.MainWindowHandle -ne 0){
    [VelvetAffinityWin32]::ShowWindow($p.MainWindowHandle,0)|Out-Null
  }
  Start-Sleep -Milliseconds 150
}
$p.Refresh()
$visible=$false
if($p.MainWindowHandle -ne 0){
  $visible=[VelvetAffinityWin32]::IsWindowVisible($p.MainWindowHandle)
}
if($visible){throw 'Affinity window is still visible after hidden launch'}

$raw=& $Python $Adapter probe 2>&1
$code=$LASTEXITCODE
try {$j=($raw -join [Environment]::NewLine)|ConvertFrom-Json} catch {$j=$null}
if($code -ne 0 -or -not $j -or $j.status -ne 'PASS'){
  Log "FAIL safe_adapter_probe exit=$code"
  throw 'Affinity safe adapter probe failed'
}

$statusRaw=& $Python $Adapter status 2>&1
$statusCode=$LASTEXITCODE
try {$s=($statusRaw -join [Environment]::NewLine)|ConvertFrom-Json} catch {$s=$null}
if($statusCode -ne 0 -or -not $s -or $s.ok -ne $true -or $s.status.shortVersion -ne '3.3.0.4850'){
  Log "FAIL safe_adapter_status exit=$statusCode"
  throw 'Affinity safe adapter status/version check failed'
}

Log "READY pid=$($p.Id) mcp=127.0.0.1:6767 version=$($s.status.shortVersion) visible=$visible"
[pscustomobject]@{
  status='READY'
  pid=$p.Id
  session=$p.SessionId
  mcp_host='127.0.0.1'
  mcp_port=6767
  protocol=$j.protocol
  version=$s.status.shortVersion
  visible=$visible
} | ConvertTo-Json