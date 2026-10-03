param([Parameter(Mandatory=$true)][string]$Spec,[Parameter(Mandatory=$true)][string]$Response)
$ErrorActionPreference='Stop'
$r=[ordered]@{status='FAIL'};$excel=$null;$wb=$null;$ws=$null
try{
 $s=Get-Content -LiteralPath $Spec -Raw -Encoding UTF8|ConvertFrom-Json
 if([string]$s.action -ne 'excel_table'){throw 'unsupported action'}
 $job=[string]$s.job_id
 if($job -notmatch '^[A-Za-z0-9_-]{1,64}$'){throw 'invalid job_id'}
 $rows=@($s.rows)
 if($rows.Count -lt 1 -or $rows.Count -gt 200){throw 'invalid rows'}
 $dir=if([string]$s.target -eq 'tmp'){'D:\Velvet\Tmp\creative-tools\missing-integrations-phase2'}else{'D:\Velvet\Output\CreativeCraft\Office\Excel'}
 New-Item -ItemType Directory -Force -Path $dir|Out-Null
 $xlsx=Join-Path $dir ($job+'.xlsx');$pdf=Join-Path $dir ($job+'.pdf')
 if((Test-Path $xlsx) -or (Test-Path $pdf)){throw 'refusing to overwrite existing output'}
 $excel=New-Object -ComObject Excel.Application
 $excel.Visible=$false;$excel.DisplayAlerts=$false
 $wb=$excel.Workbooks.Add();$ws=$wb.Worksheets.Item(1)
 $ri=1;$maxCols=0
 foreach($row in $rows){
  $cells=@($row);if($cells.Count -gt 50){throw 'row too wide'}
  if($cells.Count -gt $maxCols){$maxCols=$cells.Count}
  $ci=1
  foreach($cell in $cells){
   $range=$ws.Cells.Item($ri,$ci)
   if($null -eq $cell){$range.ClearContents()|Out-Null}
   elseif($cell -is [bool]){$range.Value2=[bool]$cell}
   elseif($cell -is [string]){$range.Value2=[string]$cell}
   else{$range.Value2=[double]$cell}
   [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($range)
   $ci++
  }
  $ri++
 }
 $ws.UsedRange.Columns.AutoFit()|Out-Null
 $wb.SaveAs($xlsx,51);$ws.ExportAsFixedFormat(0,$pdf)
 $version=[string]$excel.Version
 $wb.Close($false);$wb=$null;$ws=$null
 $excel.Quit();$excel=$null
 $xi=Get-Item -LiteralPath $xlsx;$pi=Get-Item -LiteralPath $pdf
 $r=[ordered]@{status='PASS';app='excel';version=$version;job_id=$job;readback=[ordered]@{rows=$rows.Count;columns=$maxCols};artifacts=[ordered]@{xlsx=[ordered]@{path=$xi.FullName;bytes=[long]$xi.Length;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $xlsx).Hash};pdf=[ordered]@{path=$pi.FullName;bytes=[long]$pi.Length;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $pdf).Hash}}}
}catch{$r=[ordered]@{status='FAIL';error=$_.Exception.Message}}
finally{
 if($wb){try{$wb.Close($false)}catch{}}
 if($excel){try{$excel.Quit()}catch{}}
 $r|ConvertTo-Json -Depth 10|Set-Content -LiteralPath $Response -Encoding UTF8
}
