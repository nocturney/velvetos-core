param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
  [string]$Output = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..\vfops\out')).Path 'openpost-morning-snapshot.json'),
  [string]$CredentialPath = (Join-Path $env:APPDATA 'VelvetOS\openpost-morning-brief.token.dpapi')
)
$ErrorActionPreference='Stop'
if(-not (Test-Path $CredentialPath)){ throw 'Morning Brief OpenPost credential missing' }
$adapter=Join-Path $RepoRoot 'packages\vfigos\openpost_morning_snapshot.py'
if(-not (Test-Path $adapter)){ throw 'OpenPost Morning adapter missing' }
$enc=(Get-Content -Raw $CredentialPath).Trim()
$sec=ConvertTo-SecureString $enc
$bstr=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
try {
  $env:OPENPOST_TOKEN=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
  & python $adapter --output $Output
  if($LASTEXITCODE -ne 0){ throw "OpenPost snapshot failed exit=$LASTEXITCODE" }
} finally {
  Remove-Item Env:OPENPOST_TOKEN -ErrorAction SilentlyContinue
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}
Write-Output "OPENPOST_SNAPSHOT_OK output=$Output"