param([switch]$KeepEvidence)
$ErrorActionPreference='Stop'
$runtime='D:\Velvet\Runtime\CreativeTools\MissingIntegrationsPhase2'
$state='D:\Velvet\State\MissingIntegrationsPhase2'
$launcher='D:\Velvet\Runtime\Autostart\Start-Phase2CandidateHost.ps1'
$tasks=@(
 'VelvetOS Phase2 Candidate indesign','VelvetOS Phase2 Candidate photopaint',
 'VelvetOS Phase2 Candidate fusion','VelvetOS Phase2 Candidate openscad',
 'VelvetOS Phase2 Candidate acrobat','VelvetOS Phase2 Candidate sketchup-capi','VelvetOS Phase2 Candidate office-adapter',
 'VelvetOS Phase2 Candidate office-word','VelvetOS Phase2 Candidate office-excel',
 'VelvetOS Phase2 Candidate office-powerpoint',
 'VelvetOS Phase2 Candidate media-encoder','VelvetOS Phase2 Candidate xvl-studio-corel','VelvetOS Phase2 Candidate xvl-html5','VelvetOS Phase2 Candidate media-encoder-adapter',
 'VelvetOS Phase2 Candidate sketchup','VelvetOS Phase2 Candidate office-word-worker',
 'VelvetOS Phase2 Candidate fusion-adapter','VelvetOS Phase2 Candidate openscad-adapter',
 'VelvetOS Phase2 Candidate acrobat-adapter'
)
$probes=@(Get-ScheduledTask -TaskName 'VelvetOS Phase2 Probe *' -ErrorAction SilentlyContinue|
 Select-Object -ExpandProperty TaskName)
$configs=@(Get-ScheduledTask -TaskName 'VelvetOS Phase2 Configure AME *' -ErrorAction SilentlyContinue|
 Select-Object -ExpandProperty TaskName)
foreach($name in @($tasks)+@($probes)+@($configs)){
 Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
 Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
}
function Stop-OwnedPort([int]$Port){
 $listeners=@(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
 foreach($listener in $listeners){
  $proc=Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)" -ErrorAction SilentlyContinue
  if($proc -and $proc.CommandLine -like '*D:\Velvet\Runtime\CreativeTools\MissingIntegrationsPhase2*'){
   Stop-Process -Id $listener.OwningProcess -Force -ErrorAction SilentlyContinue
  }
 }
}
foreach($port in @(6781,6782,6783,6784,6785,6786,6787,6788,6789,6790)){Stop-OwnedPort $port}
$baseline=Join-Path $state 'office-service-baseline.json'
if(Test-Path -LiteralPath $baseline){
 $b=Get-Content -LiteralPath $baseline -Raw -Encoding UTF8|ConvertFrom-Json
 $svc=Get-CimInstance Win32_Service -Filter "Name='ClickToRunSvc'"
 if([string]$b.State -ne 'Running' -and $svc.State -ne 'Stopped'){
  Stop-Service -Name ClickToRunSvc -Force -ErrorAction SilentlyContinue
 }
 switch([string]$b.StartMode){
  'Disabled' {Set-Service -Name ClickToRunSvc -StartupType Disabled}
  'Auto' {Set-Service -Name ClickToRunSvc -StartupType Automatic}
  default {Set-Service -Name ClickToRunSvc -StartupType Manual}
 }
 if([string]$b.State -eq 'Running'){Start-Service -Name ClickToRunSvc}
}
Remove-Item -LiteralPath $runtime -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $launcher -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $state -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath 'D:\Velvet\Runtime\Autostart\Start-SketchUpPhase2.ps1' -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath 'D:\Velvet\Runtime\Autostart\Start-MediaEncoderPhase2.ps1' -Force -ErrorAction SilentlyContinue
if(-not $KeepEvidence){
 Remove-Item -LiteralPath 'D:\Velvet\Tmp\creative-tools\missing-integrations-phase2' -Recurse -Force -ErrorAction SilentlyContinue
}
[pscustomobject]@{
 status='ROLLED_BACK'
 stopped_owned_ports=@(6781,6782,6783,6784,6785,6786,6787,6788,6789,6790)
 shared_router_untouched=$true
}|ConvertTo-Json
