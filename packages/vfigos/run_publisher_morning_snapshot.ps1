param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
  [string]$Output = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..\vfops\out')).Path 'publisher-morning-snapshot.json'),
  [string]$CredentialPath = (Join-Path $env:APPDATA 'VelvetOS\cloudflare-publisher-control.dpapi')
)
$ErrorActionPreference='Stop'
if(-not (Test-Path $CredentialPath)){ throw 'Morning Brief Publisher credential missing' }
$adapter=Join-Path $RepoRoot 'packages\vfigos\cloudflare_publisher_morning_snapshot.py'
if(-not (Test-Path $adapter)){ throw 'Cloudflare Publisher Morning adapter missing' }
$enc=(Get-Content -Raw $CredentialPath).Trim()
$sec=ConvertTo-SecureString $enc
$bstr=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
try {
  $env:VELVET_PUBLISHER_CONTROL_TOKEN=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
  & python $adapter --output $Output
  if($LASTEXITCODE -ne 0){ throw "Publisher snapshot failed exit=$LASTEXITCODE" }
} finally {
  Remove-Item Env:VELVET_PUBLISHER_CONTROL_TOKEN -ErrorAction SilentlyContinue
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}
Write-Output "PUBLISHER_SNAPSHOT_OK output=$Output"