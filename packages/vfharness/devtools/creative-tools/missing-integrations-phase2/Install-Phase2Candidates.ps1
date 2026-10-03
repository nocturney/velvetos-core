$ErrorActionPreference='Stop'
$base=$PSScriptRoot
$src=Join-Path $base 'adapters'
$runtime='D:\Velvet\Runtime\CreativeTools\MissingIntegrationsPhase2'
$state='D:\Velvet\State\MissingIntegrationsPhase2'
$launcher='D:\Velvet\Runtime\Autostart\Start-Phase2CandidateHost.ps1'
$template='VelvetOS DCC OnDemand coreldraw'
$q=[char]34
$ids=@('indesign','photopaint','fusion','openscad','acrobat','sketchup-capi','media-encoder','xvl-studio-corel','xvl-html5')
$files=@(
 'InDesignSafeAdapter.py','PhotoPaintSafeAdapter.py','FusionStudioSafeAdapter.py',
 'OpenSCADSafeAdapter.py','AcrobatSafeAdapter.py','Invoke-AcrobatInspect.ps1',
 'SketchUpCapiSafeAdapter.py','MediaEncoderWatchSafeAdapter.py','XVLCorelSafeAdapter.py','XvlHtmlSafeAdapter.py','OfficeSafeAdapter.py','OfficeWordWorker.ps1','OfficeExcelWorker.ps1','OfficePowerPointWorker.ps1'
)
$unsupported=@(
 'VelvetOS Phase2 Candidate media-encoder-adapter',
 'VelvetOS Phase2 Candidate sketchup','VelvetOS Phase2 Candidate office-word-worker',
 'VelvetOS Phase2 Candidate fusion-adapter','VelvetOS Phase2 Candidate openscad-adapter',
 'VelvetOS Phase2 Candidate acrobat-adapter'
)
foreach($name in $unsupported){
 Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
 Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
}
$unsupportedRuntime=@('MediaEncoderSafeAdapter.py','MediaEncoderWatchAdapter.py','SketchUpHost.rb','ame_webservice_config.ini','ame_webservice_config.original.ini')
foreach($file in $unsupportedRuntime){Remove-Item -LiteralPath (Join-Path $runtime $file) -Force -ErrorAction SilentlyContinue}
Remove-Item -LiteralPath 'D:\Velvet\Runtime\Autostart\Start-MediaEncoderPhase2.ps1','D:\Velvet\Runtime\Autostart\Start-SketchUpPhase2.ps1' -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $runtime,$state | Out-Null
$ameWatch='D:\Velvet\AME\Watch\h264-high'
$ameOutput=Join-Path $ameWatch 'Output'
$amePreset='C:\Program Files\Adobe\Adobe Media Encoder 2026\MediaIO\systempresets\3F3F3F3F_4D6F6F56\H264 Match Source - High bitrate.epr'
if(-not(Test-Path -LiteralPath $ameWatch -PathType Container)){throw "Media Encoder Watch Folder missing: $ameWatch"}
if(-not(Test-Path -LiteralPath $ameOutput -PathType Container)){throw "Media Encoder Watch Folder is not initialized by AME: $ameOutput"}
if(-not(Test-Path -LiteralPath $amePreset -PathType Leaf)){throw "Media Encoder system preset missing: $amePreset"}
[pscustomobject]@{watch=$ameWatch;output=$ameOutput;preset_id='h264-high';preset_path=$amePreset;preset_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $amePreset).Hash}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $state 'media-encoder-watch.json') -Encoding UTF8
$xvlGen='C:\Program Files\Lattice\XVLStudio3DCADCorelEdition27\xvlgenhtm.exe'
$xvlTemplate='C:\Program Files\Lattice\XVLStudio3DCADCorelEdition27\Etc\HTML5'
if(-not(Test-Path -LiteralPath $xvlGen -PathType Leaf)){throw "XVL HTML5 generator missing: $xvlGen"}
if(-not(Test-Path -LiteralPath $xvlTemplate -PathType Container)){throw "XVL HTML5 template missing: $xvlTemplate"}
[pscustomobject]@{generator=$xvlGen;generator_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $xvlGen).Hash;template=$xvlTemplate;capability='xv2-to-html5';full_studio_sdk=$false}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $state 'xvl-html5.json') -Encoding UTF8
foreach($file in $files){
 $from=Join-Path $src $file
 if(-not(Test-Path -LiteralPath $from)){throw "Missing accepted runtime file: $from"}
 Copy-Item -LiteralPath $from -Destination (Join-Path $runtime $file) -Force
}
Copy-Item -LiteralPath (Join-Path $base 'Start-Phase2CandidateHost.ps1') -Destination $launcher -Force
$token=Join-Path $state 'adapter-token.txt'
if(-not(Test-Path -LiteralPath $token)){
 $bytes=New-Object byte[] 32
 $rng=[Security.Cryptography.RandomNumberGenerator]::Create()
 try{$rng.GetBytes($bytes)}finally{$rng.Dispose()}
 [IO.File]::WriteAllText($token,([BitConverter]::ToString($bytes)-replace '-',''))
}
$officeBaseline=Join-Path $state 'office-service-baseline.json'
if(-not(Test-Path -LiteralPath $officeBaseline)){
 $svc=Get-CimInstance Win32_Service -Filter "Name='ClickToRunSvc'"
 [pscustomobject]@{State=[string]$svc.State;StartMode=[string]$svc.StartMode}|
  ConvertTo-Json|Set-Content -LiteralPath $officeBaseline -Encoding UTF8
}
function New-TaskXml([string]$Name){
 [xml]$xml=Export-ScheduledTask -TaskName $template
 $ns=New-Object System.Xml.XmlNamespaceManager($xml.NameTable)
 $ns.AddNamespace('t','http://schemas.microsoft.com/windows/2004/02/mit/task')
 $xml.SelectSingleNode('//t:RegistrationInfo/t:URI',$ns).InnerText="\"+$Name
 return @($xml,$ns)
}
foreach($id in $ids){
 $name="VelvetOS Phase2 Candidate $id"
 Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
 Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
 $pair=New-TaskXml $name;$xml=$pair[0];$ns=$pair[1]
 $exec=$xml.SelectSingleNode('//t:Actions/t:Exec',$ns)
 $exec.Command='powershell.exe'
 $exec.Arguments='-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File '+$q+$launcher+$q+' -AppId '+$id
 Register-ScheduledTask -TaskName $name -Xml $xml.OuterXml -Force | Out-Null
}
$officeAdapter='VelvetOS Phase2 Candidate office-adapter'
Stop-ScheduledTask -TaskName $officeAdapter -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName $officeAdapter -Confirm:$false -ErrorAction SilentlyContinue
$pair=New-TaskXml $officeAdapter;$xml=$pair[0];$ns=$pair[1]
$exec=$xml.SelectSingleNode('//t:Actions/t:Exec',$ns)
$exec.Command='C:\Python314\python.exe'
$exec.Arguments=$q+'D:\Velvet\Runtime\CreativeTools\MissingIntegrationsPhase2\OfficeSafeAdapter.py'+$q+' serve'
Register-ScheduledTask -TaskName $officeAdapter -Xml $xml.OuterXml -Force | Out-Null
$workers=@(
 @{id='word';script='OfficeWordWorker.ps1';req='';resp=''},
 @{id='excel';script='OfficeExcelWorker.ps1';req='office-excel-request.json';resp='office-excel-response.json'},
 @{id='powerpoint';script='OfficePowerPointWorker.ps1';req='office-powerpoint-request.json';resp='office-powerpoint-response.json'}
)
foreach($w in $workers){
 $name="VelvetOS Phase2 Candidate office-$($w.id)"
 Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
 Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
 $pair=New-TaskXml $name;$xml=$pair[0];$ns=$pair[1]
 $exec=$xml.SelectSingleNode('//t:Actions/t:Exec',$ns)
 $exec.Command='powershell.exe'
 $script=Join-Path $runtime $w.script
 if($w.id -eq 'word'){
  $exec.Arguments='-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File '+$q+$script+$q
 }else{
  $req=Join-Path $state $w.req;$resp=Join-Path $state $w.resp
  $exec.Arguments='-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File '+$q+$script+$q+' -Spec '+$q+$req+$q+' -Response '+$q+$resp+$q
 }
 Register-ScheduledTask -TaskName $name -Xml $xml.OuterXml -Force | Out-Null
}
[pscustomobject]@{
 status='INSTALLED'
 runtime=$runtime
 accepted=@('indesign','photopaint','fusion-studio','openscad','office','acrobat','sketchup-capi','layout-capi','media-encoder','xvl-studio-corel-gui','xvl-html5')
 blocked=@()
 tasks=@($ids|ForEach-Object{"VelvetOS Phase2 Candidate $_"})+
  @($officeAdapter)+@($workers|ForEach-Object{"VelvetOS Phase2 Candidate office-$($_.id)"})
 shared_router_untouched=$true
}|ConvertTo-Json -Depth 5
