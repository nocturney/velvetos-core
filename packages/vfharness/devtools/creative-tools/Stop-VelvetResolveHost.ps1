[CmdletBinding()]
param([int]$TimeoutSeconds = 25)

$ErrorActionPreference='Stop'
$ResolvePython='C:\Program Files\Blackmagic Design\DaVinci Resolve\ResolvePython\ResolvePython.exe'
$QuitScript='D:\Velvet\Runtime\CreativeTools\Resolve\Quit-VelvetResolve.py'

if(-not (Get-Process Resolve -ErrorAction SilentlyContinue)){
  [pscustomobject]@{status='ALREADY_STOPPED';clean=$true}|ConvertTo-Json
  exit 0
}
if(-not (Test-Path $ResolvePython)){throw "ResolvePython missing: $ResolvePython"}
if(-not (Test-Path $QuitScript)){throw "Resolve quit helper missing: $QuitScript"}

$raw=& $ResolvePython $QuitScript 2>&1
$code=$LASTEXITCODE
$deadline=(Get-Date).AddSeconds($TimeoutSeconds)
do{
  $remaining=@(Get-Process Resolve -ErrorAction SilentlyContinue)
  if($remaining.Count -eq 0){break}
  Start-Sleep -Milliseconds 300
}while((Get-Date)-lt $deadline)

$remaining=@(Get-Process Resolve -ErrorAction SilentlyContinue)
$clean=($remaining.Count -eq 0)
[pscustomobject]@{status=$(if($clean){'STOPPED'}else{'TIMEOUT'});clean=$clean;quit_exit=$code;quit_output=($raw -join [Environment]::NewLine);remaining=@($remaining|ForEach-Object Id)}|ConvertTo-Json -Depth 4
if(-not $clean){exit 3}
