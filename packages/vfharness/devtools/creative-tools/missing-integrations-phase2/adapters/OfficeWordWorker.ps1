$ErrorActionPreference='Stop'
$state='D:\Velvet\State\MissingIntegrationsPhase2'
$jobPath=Join-Path $state 'office-word-job.txt'
$titlePath=Join-Path $state 'office-word-title.txt'
$bodyPath=Join-Path $state 'office-word-body.txt'
$targetPath=Join-Path $state 'office-word-target.txt'
$response=Join-Path $state 'office-word-response.json'
$r=[ordered]@{status='FAIL'};$word=$null;$doc=$null
try{
 foreach($p in @($jobPath,$titlePath,$bodyPath,$targetPath)){if(-not(Test-Path -LiteralPath $p)){throw "missing input $p"}}
 $job=(Get-Content -LiteralPath $jobPath -Raw -Encoding UTF8).Trim()
 $title=(Get-Content -LiteralPath $titlePath -Raw -Encoding UTF8).Trim()
 $body=Get-Content -LiteralPath $bodyPath -Raw -Encoding UTF8
 $target=(Get-Content -LiteralPath $targetPath -Raw -Encoding UTF8).Trim()
 if($job -notmatch '^[A-Za-z0-9_-]{1,64}$'){throw 'invalid job_id'}
 if($title.Length -lt 1 -or $title.Length -gt 500){throw 'invalid title'}
 if($body.Length -lt 1 -or $body.Length -gt 19000){throw 'invalid body'}
 if($target -notin @('tmp','production')){throw 'invalid target'}
 $dir=if($target -eq 'tmp'){'D:\Velvet\Tmp\creative-tools\missing-integrations-phase2'}else{'D:\Velvet\Output\CreativeCraft\Office\Word'}
 New-Item -ItemType Directory -Force -Path $dir|Out-Null
 $docx=$dir+'\'+$job+'.docx';$pdf=$dir+'\'+$job+'.pdf'
 if((Test-Path $docx) -or (Test-Path $pdf)){throw 'refusing to overwrite existing output'}
 $word=New-Object -ComObject Word.Application
 $word.Visible=$false;$word.DisplayAlerts=0
 $doc=$word.Documents.Add()
 $doc.Content.Text=($title+[Environment]::NewLine+[Environment]::NewLine+$body)
 $doc.SaveAs2($docx,16)
 $doc.ExportAsFixedFormat($pdf,17)
 $version=[string]$word.Version;$chars=[int]$doc.Content.Characters.Count
 $doc.Close($false);$doc=$null
 $word.Quit();$word=$null
 $di=Get-Item -LiteralPath $docx;$pi=Get-Item -LiteralPath $pdf
 $r=[ordered]@{status='PASS';app='word';version=$version;job_id=$job;readback=[ordered]@{characters=$chars};artifacts=[ordered]@{docx=[ordered]@{path=$di.FullName;bytes=[long]$di.Length;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $docx).Hash};pdf=[ordered]@{path=$pi.FullName;bytes=[long]$pi.Length;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $pdf).Hash}}}
}catch{$r=[ordered]@{status='FAIL';error=$_.Exception.Message}}
finally{
 if($doc){try{$doc.Close($false)}catch{}}
 if($word){try{$word.Quit()}catch{}}
 $r|ConvertTo-Json -Depth 10|Set-Content -LiteralPath $response -Encoding UTF8
}
