param([ValidateSet('Probe','Production')][string]$Mode='Production')
$ErrorActionPreference='Stop'
$blob='D:\Velvet\OfficeV2Lab\state\phase3b-security\pilot\openbao-pilot-approle.dpapi'
$current='D:\Velvet\State\OfficeV2\project-state\CURRENT.json'
$pilotPromotion='D:\Velvet\Artifacts\OfficeV2\phase3b\evidence\2026-10-07\pilot-promotion.json'
$productionPromotion='D:\Velvet\Artifacts\OfficeV2\phase3b\evidence\2026-10-07\production-promotion.json'
$runtimeReceipt='D:\Velvet\OfficeV2Lab\artifacts\phase3b-security\shadow-runtime\production-snapshot-read.json'
$script='/var/officev2/artifacts/phase3b-security/production-snapshot-read.sh'
$wsl='C:\Windows\System32\wsl.exe'

if((whoami) -ne 'chris\chris'){throw 'production snapshot resolver requires Chris interactive user context'}
if(-not (Test-Path $blob)){throw 'production snapshot AppRole bundle missing'}
if(-not (Test-Path $current)){throw 'Office v2 CURRENT missing'}
$state=Get-Content $current -Raw | ConvertFrom-Json

if($Mode -eq 'Probe'){
  if($state.phase -ne 'PHASE_3B_PILOT_ACTIVE' -or $state.gate -ne 'GREEN'){throw 'Probe requires PHASE_3B_PILOT_ACTIVE GREEN'}
  $promotion=Get-Content $pilotPromotion -Raw | ConvertFrom-Json
  if($promotion.status -ne 'PASS' -or $promotion.pilot_promoted -ne $true){throw 'PILOT promotion receipt not PASS'}
  $expected=[string]$promotion.active_credential_reference_sha256
}else{
  if($state.phase -ne 'PHASE_3B_PRODUCTION_READ_ACTIVE' -or $state.gate -ne 'GREEN'){throw 'Production resolver requires PHASE_3B_PRODUCTION_READ_ACTIVE GREEN'}
  $promotion=Get-Content $productionPromotion -Raw | ConvertFrom-Json
  if($promotion.status -ne 'PASS' -or $promotion.production_promoted -ne $true){throw 'production promotion receipt not PASS'}
  $expected=[string]$promotion.active_credential_reference_sha256
}
if(-not $expected){throw 'expected production read credential reference missing'}

$enc=[IO.File]::ReadAllText($blob)
$secure=ConvertTo-SecureString $enc
$cred=[Management.Automation.PSCredential]::new('officev2-production-read',$secure)
$bundle=$cred.GetNetworkCredential().Password
try {
  $psi=[Diagnostics.ProcessStartInfo]::new()
  $psi.FileName=$wsl
  $psi.Arguments="-d OfficeV2-Lab -u root -- bash $script $expected"
  $psi.UseShellExecute=$false
  $psi.RedirectStandardInput=$true
  $psi.RedirectStandardOutput=$true
  $psi.RedirectStandardError=$true
  $psi.CreateNoWindow=$true
  $p=[Diagnostics.Process]::new()
  $p.StartInfo=$psi
  [void]$p.Start()
  $p.StandardInput.Write($bundle)
  $p.StandardInput.Close()
  $stdout=$p.StandardOutput.ReadToEnd()
  $stderr=$p.StandardError.ReadToEnd()
  $p.WaitForExit()
  if($p.ExitCode -ne 0){throw ('production snapshot bridge denied: '+(($stderr -split "[\r\n]+" | Where-Object {$_} | Select-Object -Last 1)))}
  $snapshot=$stdout | ConvertFrom-Json
  if($snapshot.schema -ne 'vf.instagram.schedule-snapshot.v1' -or $snapshot.source -ne 'cloudflare-instagram-publisher'){throw 'production snapshot payload schema mismatch'}
  if(-not (Test-Path $runtimeReceipt)){throw 'production snapshot runtime receipt missing'}
  $receipt=Get-Content $runtimeReceipt -Raw | ConvertFrom-Json
  if($receipt.status -ne 'PASS' -or $receipt.credential_class -ne 'PRODUCTION_READ'){throw 'production snapshot receipt not PASS'}
  if([string]$receipt.broker.credential_reference_sha256 -ne $expected){throw 'production snapshot credential hash mismatch'}
  if($receipt.authorization.decision -ne 'ALLOW' -or $receipt.authorization.default -ne 'DENY'){throw 'production snapshot policy decision mismatch'}
  if($receipt.broker.exact_scope_read_http -ne 200 -or $receipt.broker.unrelated_scope_http -ne 403){throw 'production snapshot broker scope mismatch'}
  if($receipt.provider.runtime_http -ne 200 -or $receipt.provider.meta_health_http -ne 200 -or $receipt.provider.jobs_http -ne 200 -or $receipt.provider.write_run_http -ne 401){throw 'production snapshot provider boundary mismatch'}
  if($receipt.control_token_read_or_reused -ne $false -or $receipt.meta_access_token_read_or_reused -ne $false -or $receipt.external_mutation_performed -ne $false){throw 'production snapshot safety boundary mismatch'}
  Write-Output $stdout.Trim()
  exit 0
} finally {
  $bundle=$null; $cred=$null; $secure=$null
  [GC]::Collect()
}
