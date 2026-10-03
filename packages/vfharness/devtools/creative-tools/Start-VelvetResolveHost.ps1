[CmdletBinding()]
param([int]$StartupTimeoutSeconds = 120)

$ErrorActionPreference='Stop'
$Shortcut='D:\Velvet\Runtime\Autostart\DaVinci Resolve Studio - VelvetOS.lnk'
$ResolvePython='C:\Program Files\Blackmagic Design\DaVinci Resolve\ResolvePython\ResolvePython.exe'
$Probe='D:\Velvet\Runtime\CreativeTools\Resolve\Probe-VelvetResolve.py'
$Config='C:\Users\Chris\AppData\Roaming\Blackmagic Design\DaVinci Resolve\Preferences\config.dat'
$LogDir='D:\Velvet\Logs\CreativeTools\Resolve'
$Log=Join-Path $LogDir ('resolve-host-'+(Get-Date -Format 'yyyyMMdd')+'.log')
New-Item -ItemType Directory -Force -Path $LogDir|Out-Null

function Log([string]$m){
  Add-Content -LiteralPath $Log -Encoding UTF8 -Value ('{0:o} {1}' -f (Get-Date),$m)
}

$identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name
$session=(Get-Process -Id $PID).SessionId
Log "CONTEXT wrapper_pid=$PID identity=$identity session=$session"

if(-not (Test-Path $Shortcut)){throw "Managed Resolve shortcut missing: $Shortcut"}
if(-not (Test-Path $ResolvePython)){throw "ResolvePython missing: $ResolvePython"}
if(-not (Test-Path $Probe)){throw "Resolve probe missing: $Probe"}
if(-not (Select-String -Path $Config -Pattern '^System\.Scripting\.Mode\s*=\s*1\s*$' -Quiet)){
  throw 'Resolve external scripting is not configured for Local mode'
}
$p=Get-Process Resolve -ErrorAction SilentlyContinue |
  Where-Object {$_.SessionId -eq $session} | Select-Object -First 1
if(-not $p){
  Start-Process -FilePath 'explorer.exe' -ArgumentList ('"'+$Shortcut+'"')|Out-Null
  Log "LAUNCH shortcut=$Shortcut mode=nogui"
} else {
  Log "SKIP running pid=$($p.Id)"
}

$deadline=(Get-Date).AddSeconds($StartupTimeoutSeconds)
$listener=$null
do {
  $p=Get-Process Resolve -ErrorAction SilentlyContinue |
    Where-Object {$_.SessionId -eq $session} | Select-Object -First 1
  if($p){
    $fuscripts=Get-CimInstance Win32_Process -Filter "Name='fuscript.exe'" -ErrorAction SilentlyContinue |
      Where-Object {$_.ParentProcessId -eq $p.Id}
    foreach($fu in $fuscripts){
      $candidate=Get-NetTCPConnection -State Listen -LocalPort 1144 -ErrorAction SilentlyContinue |
        Where-Object {$_.OwningProcess -eq $fu.ProcessId} | Select-Object -First 1
      if($candidate){$listener=$candidate;break}
    }
  }
  if($p -and $p.Responding -and $listener){break}
  Start-Sleep -Milliseconds 500
} while((Get-Date)-lt $deadline)

if(-not $p){throw 'Resolve process did not appear before timeout'}
if(-not $p.Responding){throw 'Resolve did not become responsive'}
if(-not $listener){throw 'Resolve scripting listener 1144 did not become ready under Resolve child fuscript'}
$probeDeadline=(Get-Date).AddSeconds(45)
$raw=$null
$code=1
do {
  $raw=& $ResolvePython $Probe 2>&1
  $code=$LASTEXITCODE
  if($code -eq 0){
    try {$j=$raw|ConvertFrom-Json} catch {$j=$null}
    if($j -and $j.ok -eq $true -and $j.version -eq '21.1.0.17'){break}
  }
  Start-Sleep -Milliseconds 750
} while((Get-Date)-lt $probeDeadline)

if($code -ne 0 -or -not $j -or $j.ok -ne $true){
  Log "FAIL official_probe exit=$code"
  throw 'Resolve official scripting probe failed'
}
$p.Refresh()
$hidden=($p.MainWindowHandle -eq 0)
if(-not $hidden){throw 'Resolve headless launch unexpectedly exposed a window'}

Log "READY pid=$($p.Id) fuscript_pid=$($listener.OwningProcess) api=1144 version=$($j.version) hidden=$hidden"
[pscustomobject]@{
  status='READY'
  pid=$p.Id
  fuscript_pid=$listener.OwningProcess
  scripting_port=1144
  version=$j.version
  product=$j.product
  hidden=$hidden
} | ConvertTo-Json
