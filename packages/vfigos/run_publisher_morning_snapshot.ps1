param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
  [string]$Output = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..\vfops\out')).Path 'publisher-morning-snapshot.json'),
  [string]$CredentialPath = (Join-Path $env:APPDATA 'VelvetOS\cloudflare-instagram-publisher-control.token.dpapi')
)
$ErrorActionPreference='Stop'
if(-not (Test-Path $CredentialPath)){ throw 'Morning Brief Cloudflare Publisher credential missing' }
$adapter=Join-Path $RepoRoot 'packages\vfigos\publisher_morning_snapshot.py'
if(-not (Test-Path $adapter)){ throw 'Cloudflare Publisher Morning adapter missing' }
$enc=(Get-Content -Raw $CredentialPath).Trim()
$sec=ConvertTo-SecureString $enc
$bstr=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
try {
  $env:CLOUDFLARE_PUBLISHER_CONTROL_TOKEN=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
  & python $adapter --output $Output
  if($LASTEXITCODE -ne 0){ throw "Publisher snapshot failed exit=$LASTEXITCODE" }
} finally {
  Remove-Item Env:CLOUDFLARE_PUBLISHER_CONTROL_TOKEN -ErrorAction SilentlyContinue
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}
Write-Output "PUBLISHER_SNAPSHOT_OK output=$Output"
