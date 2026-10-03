param([Parameter(Mandatory=$true)][string]$Spec,[Parameter(Mandatory=$true)][string]$Response)
$ErrorActionPreference='Stop'
$r=[ordered]@{status='FAIL'};$pp=$null;$pres=$null
try{
 $s=Get-Content -LiteralPath $Spec -Raw -Encoding UTF8|ConvertFrom-Json
 if([string]$s.action -ne 'powerpoint_deck'){throw 'unsupported action'}
 $job=[string]$s.job_id
 if($job -notmatch '^[A-Za-z0-9_-]{1,64}$'){throw 'invalid job_id'}
 $slides=@($s.slides)
 if($slides.Count -lt 1 -or $slides.Count -gt 50){throw 'invalid slides'}
 $dir=if([string]$s.target -eq 'tmp'){'D:\Velvet\Tmp\creative-tools\missing-integrations-phase2'}else{'D:\Velvet\Output\CreativeCraft\Office\PowerPoint'}
 New-Item -ItemType Directory -Force -Path $dir|Out-Null
 $pptx=Join-Path $dir ($job+'.pptx');$pdf=Join-Path $dir ($job+'.pdf')
 if((Test-Path $pptx) -or (Test-Path $pdf)){throw 'refusing to overwrite existing output'}
 $pp=New-Object -ComObject PowerPoint.Application
 $pres=$pp.Presentations.Add()
 $idx=1
 foreach($item in $slides){
  $title=[string]$item.title;$body=[string]$item.body
  if($title.Length -lt 1 -or $title.Length -gt 500){throw 'invalid slide title'}
  if($body.Length -gt 4000){throw 'slide body too long'}
  $slide=$pres.Slides.Add($idx,1)
  $slide.Shapes.Title.TextFrame.TextRange.Text=$title
  $slide.Shapes.Placeholders.Item(2).TextFrame.TextRange.Text=$body
  [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($slide)
  $idx++
 }
 $pres.SaveAs($pptx,24);$pres.SaveAs($pdf,32)
 $version=[string]$pp.Version;$slideCount=[int]$pres.Slides.Count
 $pres.Close();$pres=$null
 $pp.Quit();$pp=$null
 $pi=Get-Item -LiteralPath $pptx;$fi=Get-Item -LiteralPath $pdf
 $r=[ordered]@{status='PASS';app='powerpoint';version=$version;job_id=$job;readback=[ordered]@{slides=$slideCount};artifacts=[ordered]@{pptx=[ordered]@{path=$pi.FullName;bytes=[long]$pi.Length;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $pptx).Hash};pdf=[ordered]@{path=$fi.FullName;bytes=[long]$fi.Length;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $pdf).Hash}}}
}catch{$r=[ordered]@{status='FAIL';error=$_.Exception.Message}}
finally{
 if($pres){try{$pres.Close()}catch{}}
 if($pp){try{$pp.Quit()}catch{}}
 $r|ConvertTo-Json -Depth 10|Set-Content -LiteralPath $Response -Encoding UTF8
}
