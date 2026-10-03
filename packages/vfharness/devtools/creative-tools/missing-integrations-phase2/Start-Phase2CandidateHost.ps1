param([Parameter(Mandatory=$true)][ValidateSet('indesign','photopaint','fusion','openscad','acrobat','sketchup-capi','media-encoder','xvl-studio-corel','xvl-html5')][string]$AppId)
$ErrorActionPreference='Stop'
$diag='D:\Velvet\State\MissingIntegrationsPhase2\candidate-host-last-error.txt'
Remove-Item -LiteralPath $diag -Force -ErrorAction SilentlyContinue
trap{($_|Out-String)|Set-Content -LiteralPath $diag -Encoding UTF8;exit 1}
if((Get-Process -Id $PID).SessionId -eq 0){throw 'Phase2 candidate host requires an interactive user session'}
$root='D:\Velvet\Runtime\CreativeTools\MissingIntegrationsPhase2'
$python='C:\Python314\python.exe'
$state='D:\Velvet\State\MissingIntegrationsPhase2'
$cfg=@{
  indesign=@{adapter='InDesignSafeAdapter.py';process='InDesign'}
  photopaint=@{adapter='PhotoPaintSafeAdapter.py';process='CorelPP'}
  fusion=@{adapter='FusionStudioSafeAdapter.py';process='Fusion'}
  openscad=@{adapter='OpenSCADSafeAdapter.py';process=$null}
  acrobat=@{adapter='AcrobatSafeAdapter.py';process=$null}
  'sketchup-capi'=@{adapter='SketchUpCapiSafeAdapter.py';process=$null}
  'media-encoder'=@{adapter='MediaEncoderWatchSafeAdapter.py';process='Adobe Media Encoder'}
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
}elseif($AppId -eq 'media-encoder'){
  $ameExe='C:\Program Files\Adobe\Adobe Media Encoder 2026\Adobe Media Encoder.exe'
  $ameDir=Split-Path -Parent $ameExe
  $started=Get-Date
  $ownedState=Join-Path $state 'media-encoder-owned.json'
  Remove-Item -LiteralPath $ownedState -Force -ErrorAction SilentlyContinue
  $ame=Start-Process -FilePath $ameExe -WorkingDirectory $ameDir -PassThru
  try{
    if(-not ('VelvetPhase2.NativeWindow' -as [type])){
      Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; namespace VelvetPhase2 { public static class NativeWindow { [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow); } }'
    }
    $ready=$false
    $stableCount=0
    for($i=0;$i -lt 60;$i++){
      Start-Sleep -Milliseconds 500
      $owned=@(Get-Process -Name 'Adobe Media Encoder' -ErrorAction SilentlyContinue|Where-Object{$_.SessionId -eq $session -and $_.StartTime -ge $started.AddSeconds(-2)})
      if($owned.Count -gt 0){
        @($owned|ForEach-Object{[pscustomobject]@{Id=$_.Id;StartTime=$_.StartTime.ToString('o')}})|ConvertTo-Json|Set-Content -LiteralPath $ownedState -Encoding UTF8
        $stableCount++
      }else{
        $stableCount=0
      }
      foreach($proc in $owned){
        if($proc.MainWindowHandle -ne 0){
          [VelvetPhase2.NativeWindow]::ShowWindowAsync($proc.MainWindowHandle,0)|Out-Null
        }
      }
      if($stableCount -ge 6){$ready=$true;break}
    }
    if(-not $ready){throw 'Adobe Media Encoder did not remain alive long enough for Watch Folder startup'}
    & $python $adapter serve
    if($LASTEXITCODE -ne 0){throw "Media Encoder adapter exited with code $LASTEXITCODE"}
  }finally{
    $cleanupUntil=(Get-Date).AddSeconds(12)
    do{
      $owned=@(Get-Process -Name 'Adobe Media Encoder' -ErrorAction SilentlyContinue|Where-Object{$_.SessionId -eq $session -and $_.StartTime -ge $started.AddSeconds(-2)})
      foreach($proc in $owned){
        $proc.CloseMainWindow()|Out-Null
        try{if(-not $proc.WaitForExit(1500)){Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue}}catch{}
      }
      Start-Sleep -Milliseconds 500
      $remaining=@(Get-Process -Name 'Adobe Media Encoder' -ErrorAction SilentlyContinue|Where-Object{$_.SessionId -eq $session -and $_.StartTime -ge $started.AddSeconds(-2)})
    }while($remaining.Count -gt 0 -and (Get-Date) -lt $cleanupUntil)
    Remove-Item -LiteralPath $ownedState -Force -ErrorAction SilentlyContinue
  }
}else{
  & $python $adapter serve
  if($LASTEXITCODE -ne 0){throw "Candidate adapter exited with code $LASTEXITCODE"}
}
