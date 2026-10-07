param([ValidateSet('Probe','Production')][string]$Mode='Production')
$ErrorActionPreference='Stop'
$blob='D:\Velvet\OfficeV2Lab\state\phase3b-security\production\production-read-bundle.dpapi'
$current='D:\Velvet\State\OfficeV2\project-state\CURRENT.json'
$bindingReceipt='D:\Velvet\Artifacts\OfficeV2\phase3b\evidence\2026-10-07\production-runtime-binding.json'
$authorizationReceipt='D:\Velvet\Artifacts\OfficeV2\phase3b\evidence\2026-10-07\production-authority-transfer-authorization-v1.json'
$productionPromotion='D:\Velvet\Artifacts\OfficeV2\phase3b\evidence\2026-10-07\production-promotion.json'
$runtimeReceipt='D:\Velvet\OfficeV2Lab\artifacts\phase3b-security\shadow-runtime\production-snapshot-read.json'
$script='/var/officev2/artifacts/phase3b-security/production-snapshot-read.sh'
$wsl='C:\Windows\System32\wsl.exe'

function Hash-Text([string]$Text) {
  $sha=[Security.Cryptography.SHA256]::Create()
  try { return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Text)))).Replace('-','').ToLowerInvariant() }
  finally { $sha.Dispose() }
}

if((whoami) -ne 'chris\chris'){throw 'production snapshot resolver requires Chris interactive user context'}
foreach($p in @($blob,$current,$bindingReceipt)){if(-not (Test-Path $p)){throw "production snapshot required file missing: $p"}}
$state=Get-Content $current -Raw | ConvertFrom-Json
$binding=Get-Content $bindingReceipt -Raw | ConvertFrom-Json
if($binding.status -ne 'PASS' -or $binding.scope_id -ne 'instagram-publisher-snapshot-read' -or $binding.credential_class -ne 'PRODUCTION_READ'){throw 'production runtime binding receipt not PASS'}
if($binding.production_writer_change -ne $false -or $binding.external_mutation_allowed -ne $false){throw 'production runtime binding safety boundary mismatch'}

if($Mode -eq 'Probe'){
  if($state.phase -ne 'PHASE_3B_PILOT_ACTIVE' -or $state.checkpoint_id -ne 'office-v2-phase3b-v0-cp016-pilot-active' -or $state.gate -ne 'GREEN'){throw 'Probe requires exact cp016 PHASE_3B_PILOT_ACTIVE GREEN'}
  if(-not (Test-Path $authorizationReceipt)){throw 'production authority-transfer authorization missing'}
  $auth=Get-Content $authorizationReceipt -Raw | ConvertFrom-Json
  if($auth.status -ne 'AUTHORIZED' -or $auth.production_promoted -ne $false){throw 'production authority-transfer authorization invalid'}
  $expected=[string]$binding.active_credential_reference_sha256
}else{
  if($state.phase -ne 'PHASE_3B_PRODUCTION_READ_ACTIVE' -or $state.checkpoint_id -ne 'office-v2-phase3b-v0-cp017-production-read-active' -or $state.gate -ne 'GREEN'){throw 'Production resolver requires exact cp017 PHASE_3B_PRODUCTION_READ_ACTIVE GREEN'}
  if(-not (Test-Path $productionPromotion)){throw 'production promotion receipt missing'}
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
  $bundleObj=$bundle | ConvertFrom-Json
  if($bundleObj.schema -ne 'velvetos.office-v2.phase3b-production-runtime-bundle.v0' -or $bundleObj.scope_id -ne 'instagram-publisher-snapshot-read'){throw 'production runtime DPAPI bundle schema/scope mismatch'}
  foreach($field in @('role_id','secret_id','zitadel_username','zitadel_client_secret','zitadel_machine_id')){if(-not [string]$bundleObj.$field){throw "production runtime DPAPI bundle missing $field"}}
  if((Hash-Text ([string]$bundleObj.role_id)) -ne [string]$binding.broker.role_id_reference_sha256){throw 'production AppRole role-id reference mismatch'}
  if((Hash-Text ([string]$bundleObj.secret_id)) -ne [string]$binding.broker.secret_id_reference_sha256){throw 'production AppRole secret-id reference mismatch'}
  if((Hash-Text ([string]$bundleObj.zitadel_machine_id)) -ne [string]$binding.identity.machine_id_reference_sha256){throw 'production identity machine-id reference mismatch'}
  if((Hash-Text ([string]$bundleObj.zitadel_username)) -ne [string]$binding.identity.username_reference_sha256){throw 'production identity username reference mismatch'}

  $psi=[Diagnostics.ProcessStartInfo]::new()
  $psi.FileName=$wsl
  $psi.Arguments="-d OfficeV2-Lab -u root -- bash $script $expected"
  $psi.UseShellExecute=$false
  $psi.RedirectStandardInput=$true
  $psi.RedirectStandardOutput=$true
  $psi.RedirectStandardError=$true
  $psi.CreateNoWindow=$true
  $p=[Diagnostics.Process]::new(); $p.StartInfo=$psi; [void]$p.Start()
  $p.StandardInput.Write($bundle); $p.StandardInput.Close()
  $stdout=$p.StandardOutput.ReadToEnd(); $stderr=$p.StandardError.ReadToEnd(); $p.WaitForExit()
  if($p.ExitCode -ne 0){throw ('production snapshot bridge denied: '+(($stderr -split "[\r\n]+" | Where-Object {$_} | Select-Object -Last 1)))}
  $snapshot=$stdout | ConvertFrom-Json
  if($snapshot.schema -ne 'vf.instagram.schedule-snapshot.v1' -or $snapshot.source -ne 'cloudflare-instagram-publisher'){throw 'production snapshot payload schema mismatch'}
  if(-not (Test-Path $runtimeReceipt)){throw 'production snapshot runtime receipt missing'}
  $receipt=Get-Content $runtimeReceipt -Raw | ConvertFrom-Json
  if($receipt.status -ne 'PASS' -or $receipt.credential_class -ne 'PRODUCTION_READ'){throw 'production snapshot receipt not PASS'}
  if([string]$receipt.broker.credential_reference_sha256 -ne $expected){throw 'production snapshot credential hash mismatch'}
  if($receipt.identity.persistent_principal -ne $true -or $receipt.identity.ephemeral_cleanup_on_exit -ne $false){throw 'production identity is not persistent'}
  if($receipt.principal -ne 'svc:officev2-p3b-prod-publisher-snapshot'){throw 'production principal mismatch'}
  if($receipt.authorization.decision -ne 'ALLOW' -or $receipt.authorization.default -ne 'DENY'){throw 'production snapshot policy decision mismatch'}
  if($receipt.broker.role -ne 'officev2-prod-publisher-snapshot' -or $receipt.broker.logical_secret_path -ne 'officev2-prod/data/instagram-publisher-snapshot'){throw 'production broker path/role mismatch'}
  if($receipt.broker.exact_scope_read_http -ne 200 -or $receipt.broker.unrelated_scope_http -ne 403){throw 'production snapshot broker scope mismatch'}
  if($receipt.provider.runtime_http -ne 200 -or $receipt.provider.meta_health_http -ne 200 -or $receipt.provider.jobs_http -ne 200 -or $receipt.provider.write_run_http -ne 401){throw 'production snapshot provider boundary mismatch'}
  if($receipt.control_token_read_or_reused -ne $false -or $receipt.meta_access_token_read_or_reused -ne $false -or $receipt.external_mutation_performed -ne $false -or $receipt.production_writer_change -ne $false){throw 'production snapshot safety boundary mismatch'}
  Write-Output $stdout.Trim()
  exit 0
} finally {
  $bundle=$null; $bundleObj=$null; $cred=$null; $secure=$null
  [GC]::Collect()
}
