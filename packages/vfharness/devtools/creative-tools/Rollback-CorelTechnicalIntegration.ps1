[CmdletBinding()]
param([switch]$KeepEvidence)

$ErrorActionPreference='Stop'
$ids=@('coreldraw','corel-designer')
$runtimeManifest='D:\Velvet\Runtime\Autostart\dcc-desktop-hosts.json'
$devtoolsRoot=Split-Path -Parent $PSScriptRoot
$sourceManifest=Join-Path $devtoolsRoot 'dcc-adobe-runtime-persistence\dcc-desktop-hosts.json'
$sentinelRuntime='D:\Velvet\Runtime\UpdateSentinel\dcc-adobe-update-sentinel.json'
$sentinelSource=Join-Path $PSScriptRoot 'update-sentinel\dcc-adobe-update-sentinel.json'
$hostManager='D:\Velvet\Runtime\Autostart\Invoke-VelvetDccHost.ps1'

foreach($id in $ids){
  try { & $hostManager -Action stop -AppId $id | Out-Null } catch {}
}
foreach($task in @('VelvetOS DCC OnDemand coreldraw','VelvetOS DCC OnDemand corel-designer')){
  if(Get-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue){
    Unregister-ScheduledTask -TaskName $task -Confirm:$false
  }
}

function Remove-JsonRows([string]$Path,[string]$Property){
  if(-not (Test-Path -LiteralPath $Path)){return}
  $obj=Get-Content -Raw -LiteralPath $Path|ConvertFrom-Json
  $rows=@($obj.$Property|Where-Object {$_.id -notin $ids})
  $obj.$Property=$rows
  $tmp=$Path+'.rollback-'+[guid]::NewGuid().ToString('N')
  $obj|ConvertTo-Json -Depth 30|Set-Content -LiteralPath $tmp -Encoding UTF8
  Move-Item -LiteralPath $tmp -Destination $Path -Force
}

Remove-JsonRows $runtimeManifest 'apps'
Remove-JsonRows $sourceManifest 'apps'
Remove-JsonRows $sentinelRuntime 'hosts'
Remove-JsonRows $sentinelSource 'hosts'

foreach($statePath in @(
  'D:\Velvet\State\DCC-Adobe-Update-Sentinel\routing-state.json',
  'D:\Velvet\State\DCC-Adobe-Update-Sentinel\accepted-baseline.json'
)){
  if(Test-Path -LiteralPath $statePath){
    $obj=Get-Content -Raw -LiteralPath $statePath|ConvertFrom-Json
    foreach($id in $ids){
      if($obj.hosts.PSObject.Properties[$id]){
        $obj.hosts.PSObject.Properties.Remove($id)
      }
    }
    $tmp=$statePath+'.rollback-'+[guid]::NewGuid().ToString('N')
    $obj|ConvertTo-Json -Depth 30|Set-Content -LiteralPath $tmp -Encoding UTF8
    Move-Item -LiteralPath $tmp -Destination $statePath -Force
  }
}

$remove=@(
  'D:\Velvet\Runtime\Autostart\CorelDRAW 2026 - VelvetOS.lnk',
  'D:\Velvet\Runtime\Autostart\Corel DESIGNER 2026 - VelvetOS.lnk',
  'D:\Velvet\Runtime\Autostart\Start-VelvetCorelHost.ps1',
  'D:\Velvet\Runtime\Autostart\Stop-VelvetCorelHost.ps1',
  'D:\Velvet\Runtime\CreativeTools\Corel\CorelTechnicalSafeAdapter.py',
  'D:\Velvet\State\Corel\corel-adapter-token.txt',
  'D:\Velvet\State\Corel\acceptance-gate.json'
)
foreach($p in $remove){Remove-Item -LiteralPath $p -Force -ErrorAction SilentlyContinue}

if(-not $KeepEvidence){
  Remove-Item -LiteralPath 'D:\Velvet\Tmp\creative-tools\corel\coreldraw-acceptance.pdf' -Force -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath 'D:\Velvet\Tmp\creative-tools\corel\corel-designer-acceptance.pdf' -Force -ErrorAction SilentlyContinue
}

[pscustomobject]@{
  status='ROLLED_BACK'
  removed_ids=$ids
  note='The generic corel_com Sentinel code path may remain inert; no Corel hosts remain configured.'
}|ConvertTo-Json -Depth 5
