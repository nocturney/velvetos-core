param([Parameter(Mandatory=$true)][string]$PdfPath,[Parameter(Mandatory=$true)][string]$OutPath)
$ErrorActionPreference='Stop'
$app=$null;$doc=$null;$r=[ordered]@{}
$started=Get-Date
try{
  if(Get-Process Acrobat,AcroRd32 -ErrorAction SilentlyContinue){throw 'pre-existing Acrobat user session detected'}
  if(-not (Test-Path -LiteralPath $PdfPath)){throw 'PDF missing'}
  $resolved=(Resolve-Path -LiteralPath $PdfPath).Path
  if(-not $resolved.StartsWith('D:\Velvet\',[System.StringComparison]::OrdinalIgnoreCase)){throw 'PDF must stay under D:\Velvet'}
  if([IO.Path]::GetExtension($resolved) -ne '.pdf'){throw 'input must be PDF'}
  $app=New-Object -ComObject AcroExch.App
  $doc=New-Object -ComObject AcroExch.PDDoc
  if(-not $doc.Open($resolved)){throw 'PDDoc.Open returned false'}
  $r.status='PASS';$r.pages=[int]$doc.GetNumPages();$r.file=[string]$doc.GetFileName();$r.path=$resolved
}catch{$r.status='FAIL';$r.error=$_.Exception.Message}
finally{
  if($doc){try{$doc.Close()}catch{}}
  if($app){try{$app.Exit()}catch{}}
  Start-Sleep -Milliseconds 800
  Get-Process Acrobat,AcroRd32 -ErrorAction SilentlyContinue|Where-Object{$_.StartTime -ge $started}|Stop-Process -Force -ErrorAction SilentlyContinue
  $r|ConvertTo-Json -Depth 4|Set-Content -LiteralPath $OutPath -Encoding UTF8
}
