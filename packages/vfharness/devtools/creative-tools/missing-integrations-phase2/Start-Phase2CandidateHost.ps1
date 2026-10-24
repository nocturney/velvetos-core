param([Parameter(Mandatory=$true)][ValidateSet('photopaint','fusion','openscad','acrobat','sketchup-capi','xvl-studio-corel','xvl-html5')][string]$AppId)
$ErrorActionPreference='Stop'
$diag='D:\Velvet\State\MissingIntegrationsPhase2\candidate-host-last-error.txt'
Remove-Item -LiteralPath $diag -Force -ErrorAction SilentlyContinue
trap{($_|Out-String)|Set-Content -LiteralPath $diag -Encoding UTF8;exit 1}
if((Get-Process -Id $PID).SessionId -eq 0){throw 'Phase2 candidate host requires an interactive user session'}
$root='D:\Velvet\Runtime\CreativeTools\MissingIntegrationsPhase2'
$python='C:\Python314\python.exe'
$state='D:\Velvet\State\MissingIntegrationsPhase2'
$cfg=@{
  photopaint=@{adapter='PhotoPaintSafeAdapter.py';process='CorelPP'}
  fusion=@{adapter='FusionStudioSafeAdapter.py';process='Fusion'}
  openscad=@{adapter='OpenSCADSafeAdapter.py';process=$null}
  acrobat=@{adapter='AcrobatSafeAdapter.py';process=$null}
  'sketchup-capi'=@{adapter='SketchUpCapiSafeAdapter.py';process=$null}
  'xvl-studio-corel'=@{adapter='XVLCorelSafeAdapter.py';process=$null}
  'xvl-html5'=@{adapter='XvlHtmlSafeAdapter.py';process=$null}
}
$c=$cfg[$AppId]
$session=(Get-Process -Id $PID).SessionId
if($c.process){
  $existing=@(Get-Process -Name $c.process -ErrorAction SilentlyContinue|Where-Object{$_.SessionId -eq $session})
  if($existing.Count -gt 0){throw "Refusing launch: pre-existing user process for $AppId"}
}
$adapter=Join-Path $root $c.adapter
if(-not (Test-Path -LiteralPath $adapter)){throw "Adapter missing: $adapter"}
if($AppId -eq 'fusion'){
  if(Get-Process FusionServer -ErrorAction SilentlyContinue){throw 'Refusing launch: pre-existing FusionServer detected'}
  $started=Get-Date
  $fusion=Start-Process -FilePath 'C:\Program Files\Blackmagic Design\Fusion 21\Fusion.exe' -WorkingDirectory 'C:\Program Files\Blackmagic Design\Fusion 21' -PassThru
  try{Start-Sleep -Seconds 6;& $python $adapter serve;if($LASTEXITCODE -ne 0){throw "Fusion adapter exited with code $LASTEXITCODE"}}
  finally{Get-Process Fusion,FusionServer -ErrorAction SilentlyContinue|Where-Object{$_.StartTime -ge $started}|Stop-Process -Force -ErrorAction SilentlyContinue}
}else{
  & $python $adapter serve
  if($LASTEXITCODE -ne 0){throw "Candidate adapter exited with code $LASTEXITCODE"}
}
