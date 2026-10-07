param(
  [ValidateSet('Prepare','Rotate','Cleanup')][string]$Mode='Prepare'
)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Net.Http

$stateRoot='D:\Velvet\OfficeV2Lab\state\phase3b-security'
$pilotBlob=Join-Path $stateRoot 'pilot\openbao-pilot-approle.dpapi'
$prodDir=Join-Path $stateRoot 'production'
$prodBlob=Join-Path $prodDir 'production-read-bundle.dpapi'
$current='D:\Velvet\State\OfficeV2\project-state\CURRENT.json'
$ev='D:\Velvet\Artifacts\OfficeV2\phase3b\evidence\2026-10-07'
$pilotPromotion=Join-Path $ev 'pilot-promotion.json'
$authorization=Join-Path $ev 'production-authority-transfer-authorization-v1.json'
$bindingReceipt=Join-Path $ev 'production-runtime-binding.json'
$rotationReceipt=Join-Path $ev 'production-provider-rotation.json'
$runtimeReceipt='D:\Velvet\OfficeV2Lab\artifacts\phase3b-security\shadow-runtime\production-snapshot-read.json'
$wsl='C:\Windows\System32\wsl.exe'
$workerCandidates=@()
if($env:VELVETOS_CORE){$workerCandidates+=(Join-Path $env:VELVETOS_CORE 'packages\vfigos\cloudflare-publisher')}
$workerCandidates+=@(
  'D:\Velvet\Worktrees\office-v2-phase3b-production-read-20261007\packages\vfigos\cloudflare-publisher',
  'D:\Velvet\Worktrees\office-v2-phase3b-production-authority-20261007\packages\vfigos\cloudflare-publisher',
  'D:\Velvet\Worktrees\office-v2-phase3b-pilot-main-47f74c7f\packages\vfigos\cloudflare-publisher'
)
$workerDir=@($workerCandidates|Where-Object {Test-Path (Join-Path $_ 'wrangler.toml')}|Select-Object -First 1)[0]
if(-not $workerDir){throw 'Cloudflare publisher working directory unavailable'}
$npx='C:\Program Files\nodejs\npx.cmd'
$base='https://velvetos-instagram-publisher.velvetos-vf.workers.dev'

$pilotRead='/var/officev2/artifacts/phase3b-security/pilot-token-read.sh'
$zitadelBootstrap='/var/officev2/artifacts/phase3b-security/production-zitadel-bootstrap.sh'
$zitadelDelete='/var/officev2/artifacts/phase3b-security/production-zitadel-delete.sh'
$openbaoBind='/var/officev2/artifacts/phase3b-security/production-openbao-bind.sh'
$openbaoBootstrap='/var/officev2/artifacts/phase3b-security/production-openbao-bootstrap.sh'
$pilotApproleCapture='/var/officev2/artifacts/phase3b-security/pilot-approle-capture.sh'
$shadowSecretRecapture='D:\Velvet\Runtime\OfficeV2Lab\Phase3B-ShadowSecretRecapture.ps1'
$opaApply='/var/officev2/artifacts/phase3b-security/production-opa-apply.sh'
$productionRead='/var/officev2/artifacts/phase3b-security/production-snapshot-read.sh'

function Hash-Text([string]$Value) {
  $sha=[Security.Cryptography.SHA256]::Create()
  try { return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Value)))).Replace('-','').ToLowerInvariant() }
  finally { $sha.Dispose() }
}
function Random-Token {
  $bytes=New-Object byte[] 32
  $rng=[Security.Cryptography.RandomNumberGenerator]::Create()
  try {$rng.GetBytes($bytes)} finally {$rng.Dispose()}
  return ([BitConverter]::ToString($bytes)).Replace('-','').ToLowerInvariant()
}
function Unprotect-Text([string]$Path) {
  $enc=[IO.File]::ReadAllText($Path)
  $secure=ConvertTo-SecureString $enc
  $cred=[Management.Automation.PSCredential]::new('officev2',$secure)
  try { return $cred.GetNetworkCredential().Password }
  finally { $cred=$null; $secure=$null }
}
function Protect-Text([string]$Text,[string]$Path) {
  New-Item -ItemType Directory -Force -Path (Split-Path $Path -Parent) | Out-Null
  $me=[Security.Principal.WindowsIdentity]::GetCurrent().Name
  & icacls.exe (Split-Path $Path -Parent) /inheritance:r /grant:r "${me}:(OI)(CI)F" "SYSTEM:(OI)(CI)F" | Out-Null
  if($LASTEXITCODE -ne 0){throw 'production state directory ACL setup failed'}
  $secure=ConvertTo-SecureString $Text -AsPlainText -Force
  $enc=ConvertFrom-SecureString $secure
  [IO.File]::WriteAllText($Path,$enc,[Text.UTF8Encoding]::new($false))
  & icacls.exe $Path /inheritance:r /grant:r "${me}:F" "SYSTEM:F" | Out-Null
  if($LASTEXITCODE -ne 0){throw 'production runtime bundle ACL setup failed'}
}
function Invoke-Wsl([string]$Script,[string[]]$Args=@(),[string]$InputText='') {
  $psi=[Diagnostics.ProcessStartInfo]::new()
  $psi.FileName=$wsl
  $quoted=@($Args | ForEach-Object { "'" + ($_.Replace("'","'\''")) + "'" })
  $psi.Arguments=("-d OfficeV2-Lab -u root -- bash " + $Script + ($(if($quoted.Count){" "+($quoted -join ' ')}else{''})))
  $psi.UseShellExecute=$false
  $psi.RedirectStandardInput=$true
  $psi.RedirectStandardOutput=$true
  $psi.RedirectStandardError=$true
  $psi.CreateNoWindow=$true
  $p=[Diagnostics.Process]::new(); $p.StartInfo=$psi; [void]$p.Start()
  if($InputText){$p.StandardInput.Write($InputText)}
  $p.StandardInput.Close()
  $stdout=$p.StandardOutput.ReadToEnd()
  $stderr=$p.StandardError.ReadToEnd()
  $p.WaitForExit()
  return [pscustomobject]@{ExitCode=$p.ExitCode;Stdout=$stdout;Stderr=$stderr}
}
function Safe-Wsl-Error($Result,[string]$Fallback) {
  $lines=@(($Result.Stderr -split "[\n]+") | Where-Object {$_})
  if($lines.Count){return [string]$lines[-1]}
  return $Fallback
}
function Refresh-Pilot-AppRole([string]$ExpectedSha) {
  $capture=Invoke-Wsl $pilotApproleCapture @('Read')
  if($capture.ExitCode -ne 0){throw ('pilot AppRole capture failed: '+(Safe-Wsl-Error $capture 'capture denied'))}
  $raw=$capture.Stdout.Trim()
  if(-not $raw){throw 'pilot AppRole capture returned empty output'}
  $p=$raw | ConvertFrom-Json
  if(-not [string]$p.role_id -or -not [string]$p.secret_id -or [string]$p.credential_reference_sha256 -ne $ExpectedSha){throw 'pilot AppRole capture lineage mismatch'}
  $bundle=[ordered]@{schema='velvetos.office-v2.phase3b-pilot-approle-bundle.v0';scope_id='instagram-publisher-snapshot-read';role_id=[string]$p.role_id;secret_id=[string]$p.secret_id}
  Protect-Text ($bundle|ConvertTo-Json -Compress) $pilotBlob
  $cleanup=Invoke-Wsl $pilotApproleCapture @('Cleanup')
  if($cleanup.ExitCode -ne 0){throw ('pilot AppRole runtime plaintext cleanup failed: '+(Safe-Wsl-Error $cleanup 'cleanup denied'))}
  return [pscustomobject]@{
    RoleIdReferenceSha256=(Hash-Text ([string]$p.role_id))
    SecretIdReferenceSha256=(Hash-Text ([string]$p.secret_id))
    BlobSha256=(Get-FileHash -Algorithm SHA256 $pilotBlob).Hash.ToLowerInvariant()
  }
}
function Recapture-ShadowRuntimeSecrets {
  if(-not (Test-Path $shadowSecretRecapture)){throw 'shadow secret recapture wrapper missing'}
  $proc=Start-Process -FilePath 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -ArgumentList @('-NoProfile','-NonInteractive','-WindowStyle','Hidden','-ExecutionPolicy','Bypass','-File',$shadowSecretRecapture) -Wait -PassThru
  if($proc.ExitCode -ne 0){throw 'shadow runtime secret recapture failed after OpenBao bootstrap'}
}
function New-BrokerAdminInput($Bundle,[string]$ProviderToken='') {
  return ([ordered]@{
    admin_role_id=[string]$Bundle.admin_role_id
    admin_secret_id=[string]$Bundle.admin_secret_id
    role_id=[string]$Bundle.role_id
    secret_id=[string]$Bundle.secret_id
    provider_token=$ProviderToken
  } | ConvertTo-Json -Compress)
}
function Invoke-Wrangler([string[]]$CommandArgs,[string]$Stdin='') {
  $old=Get-Location
  try {
    Set-Location $workerDir
    if($Stdin){$stdout=($Stdin | & $npx @CommandArgs 2>&1 | Out-String)}
    else {$stdout=(& $npx @CommandArgs 2>&1 | Out-String)}
    return [pscustomobject]@{ExitCode=$LASTEXITCODE;Stdout=$stdout}
  } finally { Set-Location $old }
}
function Put-Snapshot([string]$Token) {
  $r=Invoke-Wrangler @('--yes','wrangler','secret','put','SNAPSHOT_TOKEN') $Token
  if($r.ExitCode -ne 0){throw 'provider SNAPSHOT_TOKEN update failed'}
}
function Http-Code([string]$Token,[string]$Method,[string]$Path) {
  $handler=[System.Net.Http.HttpClientHandler]::new()
  $client=[System.Net.Http.HttpClient]::new($handler)
  try {
    $client.Timeout=[TimeSpan]::FromSeconds(20)
    $client.DefaultRequestHeaders.Authorization=[System.Net.Http.Headers.AuthenticationHeaderValue]::new('Bearer',$Token)
    $client.DefaultRequestHeaders.UserAgent.ParseAdd('OfficeV2-Phase3B-Production-Bind/1.0')
    $httpMethod=if($Method -eq 'POST'){[System.Net.Http.HttpMethod]::Post}else{[System.Net.Http.HttpMethod]::Get}
    $req=[System.Net.Http.HttpRequestMessage]::new($httpMethod,($base+$Path))
    if($Method -eq 'POST'){$req.Content=[System.Net.Http.StringContent]::new('{}',[Text.Encoding]::UTF8,'application/json')}
    $resp=$client.SendAsync($req).GetAwaiter().GetResult()
    [void]$resp.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    return [int]$resp.StatusCode
  } finally {
    if($req){$req.Dispose()}
    if($resp){$resp.Dispose()}
    $client.Dispose(); $handler.Dispose()
  }
}
function Require-Cp016 {
  if(-not (Test-Path $current)){throw 'Office v2 CURRENT missing'}
  $st=Get-Content $current -Raw | ConvertFrom-Json
  if($st.phase -ne 'PHASE_3B_PILOT_ACTIVE' -or $st.checkpoint_id -ne 'office-v2-phase3b-v0-cp016-pilot-active' -or $st.gate -ne 'GREEN'){throw 'production preparation requires cp016 PILOT_ACTIVE GREEN'}
  return $st
}
function Require-Authorization {
  if(-not (Test-Path $authorization)){throw 'production authority-transfer authorization v1 missing'}
  $a=Get-Content $authorization -Raw | ConvertFrom-Json
  if($a.status -ne 'AUTHORIZED' -or $a.scope_id -ne 'instagram-publisher-snapshot-read' -or $a.production_domain -ne 'instagram_read' -or $a.production_promoted -ne $false -or $a.production_writer_change -ne $false -or $a.external_mutation_allowed -ne $false){throw 'production authority-transfer authorization v1 invalid'}
  return $a
}
function Read-Pilot-Token {
  if(-not (Test-Path $pilotBlob)){throw 'pilot AppRole DPAPI bundle missing'}
  $pilotBundle=Unprotect-Text $pilotBlob
  try {
    $r=Invoke-Wsl $pilotRead @() $pilotBundle
    if($r.ExitCode -ne 0){throw ('pilot credential read failed: '+(Safe-Wsl-Error $r 'broker denied'))}
    $value=$r.Stdout.Trim()
    if(-not $value){throw 'pilot credential read returned empty value'}
    return $value
  } finally {$pilotBundle=$null}
}
function Invoke-Production-Read([string]$Bundle,[string]$Expected) {
  $r=Invoke-Wsl $productionRead @($Expected) $Bundle
  if($r.ExitCode -ne 0){throw ('production correlated read denied: '+(Safe-Wsl-Error $r 'production read denied'))}
  $payload=$r.Stdout.Trim()
  if(-not $payload){throw 'production correlated read returned no snapshot'}
  [void]($payload | ConvertFrom-Json)
  return $payload
}
function Write-Json([string]$Path,$Doc) {
  [IO.File]::WriteAllText($Path,($Doc|ConvertTo-Json -Depth 14)+[Environment]::NewLine,[Text.UTF8Encoding]::new($false))
}

if((whoami) -ne 'chris\chris'){throw 'production runtime binding requires Chris interactive user context'}
New-Item -ItemType Directory -Force -Path $ev,$prodDir | Out-Null

if($Mode -eq 'Cleanup'){
  if(-not (Test-Path $prodBlob)){throw 'production runtime bundle missing for cleanup'}
  $cleanupBundleJson=Unprotect-Text $prodBlob
  $cleanupBundle=$cleanupBundleJson|ConvertFrom-Json
  $machineId=[string]$cleanupBundle.zitadel_machine_id
  $cleanupInput=New-BrokerAdminInput $cleanupBundle
  $bao=Invoke-Wsl $openbaoBind @('Cleanup') $cleanupInput
  if($bao.ExitCode -ne 0){throw ('production OpenBao cleanup failed: '+(Safe-Wsl-Error $bao 'broker cleanup denied'))}
  $baoProof=$bao.Stdout.Trim()|ConvertFrom-Json
  if($baoProof.status -ne 'PASS' -or $baoProof.admin_auth -ne 'APPROLE_NARROW' -or $baoProof.root_used -ne $false){throw 'production OpenBao cleanup proof mismatch'}
  if($machineId){
    $zit=Invoke-Wsl $zitadelDelete @($machineId)
    if($zit.ExitCode -ne 0){throw ('production ZITADEL cleanup failed: '+(Safe-Wsl-Error $zit 'identity cleanup denied'))}
  }
  Remove-Item -Force $prodBlob
  $cleanupBundleJson=$null;$cleanupBundle=$null;$cleanupInput=$null
  [GC]::Collect()
  Write-Output 'PASS PRODUCTION_RUNTIME_CLEANUP broker_admin=APPROLE_NARROW root_used=false'
  exit 0
}

[void](Require-Cp016)
$auth=Require-Authorization
if(-not (Test-Path $pilotPromotion)){throw 'PILOT promotion receipt missing'}
$pilot=Get-Content $pilotPromotion -Raw | ConvertFrom-Json
if($pilot.status -ne 'PASS' -or $pilot.pilot_promoted -ne $true){throw 'PILOT promotion receipt is not PASS'}
$pilotExpected=[string]$pilot.active_credential_reference_sha256
if(-not $pilotExpected){throw 'PILOT credential reference missing'}

if($Mode -eq 'Prepare'){
  if(Test-Path $prodBlob){throw 'production runtime bundle already exists; cleanup or use Rotate'}
  $pilotToken=$null; $identityRaw=$null; $brokerRaw=$null; $machineId=$null; $broker=$null; $bundleJson=$null
  $identityCreated=$false; $brokerBootstrapped=$false; $pilotRefreshed=$false
  try {
    $pilotToken=Read-Pilot-Token
    $pilotHash=Hash-Text $pilotToken
    if($pilotHash -ne $pilotExpected){throw 'PILOT broker/provider credential hash mismatch before production prepare'}

    $opa=Invoke-Wsl $opaApply
    if($opa.ExitCode -ne 0){throw ('production OPA policy apply failed: '+(Safe-Wsl-Error $opa 'OPA apply denied'))}

    $zit=Invoke-Wsl $zitadelBootstrap
    if($zit.ExitCode -ne 0){throw ('production ZITADEL bootstrap failed: '+(Safe-Wsl-Error $zit 'identity bootstrap denied'))}
    $identityRaw=$zit.Stdout.Trim()
    $identity=$identityRaw | ConvertFrom-Json
    foreach($f in @('machine_id','username','client_secret')){if(-not [string]$identity.$f){throw "production ZITADEL bootstrap output missing $f"}}
    $machineId=[string]$identity.machine_id
    $identityCreated=$true

    $bao=Invoke-Wsl $openbaoBootstrap @($pilotHash) $pilotToken
    if($bao.ExitCode -ne 0){throw ('production OpenBao bootstrap failed: '+(Safe-Wsl-Error $bao 'broker bootstrap denied'))}
    $brokerRaw=$bao.Stdout.Trim()
    $broker=$brokerRaw | ConvertFrom-Json
    if(
      $broker.status -ne 'PASS' -or
      $broker.broker_path -ne 'officev2-prod/data/instagram-publisher-snapshot' -or
      $broker.broker_role -ne 'officev2-prod-publisher-snapshot' -or
      $broker.admin_role -ne 'officev2-prod-broker-admin' -or
      [string]$broker.credential_reference_sha256 -ne $pilotHash -or
      $broker.read_exact_scope_http -ne 200 -or
      $broker.read_unrelated_scope_http -ne 403 -or
      $broker.admin_unrelated_scope_http -ne 403 -or
      $broker.generated_root_revoked -ne $true -or
      $broker.root_token_persisted -ne $false
    ){throw 'production OpenBao bootstrap proof mismatch'}
    foreach($f in @('read_role_id','read_secret_id','admin_role_id','admin_secret_id')){if(-not [string]$broker.$f){throw "production OpenBao bootstrap output missing $f"}}
    $brokerBootstrapped=$true

    $pilotRefresh=Refresh-Pilot-AppRole $pilotHash
    $pilotRefreshed=$true
    Recapture-ShadowRuntimeSecrets

    $bundle=[ordered]@{
      schema='velvetos.office-v2.phase3b-production-runtime-bundle.v1'
      scope_id='instagram-publisher-snapshot-read'
      role_id=[string]$broker.read_role_id
      secret_id=[string]$broker.read_secret_id
      admin_role_id=[string]$broker.admin_role_id
      admin_secret_id=[string]$broker.admin_secret_id
      zitadel_machine_id=[string]$identity.machine_id
      zitadel_username=[string]$identity.username
      zitadel_client_secret=[string]$identity.client_secret
    }
    $bundleJson=$bundle|ConvertTo-Json -Compress
    Protect-Text $bundleJson $prodBlob
    $acl=Get-Acl $prodBlob

    [void](Invoke-Production-Read $bundleJson $pilotHash)
    $runtime=Get-Content $runtimeReceipt -Raw | ConvertFrom-Json
    if($runtime.status -ne 'PASS' -or $runtime.principal -ne 'svc:officev2-p3b-prod-publisher-snapshot' -or $runtime.provider.write_run_http -ne 401){throw 'production prepare correlated runtime proof mismatch'}

    $doc=[ordered]@{
      schema='velvetos.office-v2.phase3b-production-runtime-binding.v1'
      captured_at=[DateTime]::UtcNow.ToString('o')
      status='PASS'
      mode='PREPARED_WITH_PILOT_PROVIDER_CREDENTIAL_NO_CUTOVER'
      scope_id='instagram-publisher-snapshot-read'
      production_domain='instagram_read'
      credential_class='PRODUCTION_READ'
      principal='svc:officev2-p3b-prod-publisher-snapshot'
      active_credential_reference_sha256=$pilotHash
      provider_credential_rotated=$false
      identity=[ordered]@{
        provider='ZITADEL'
        persistent=$true
        machine_id_reference_sha256=(Hash-Text ([string]$identity.machine_id))
        username_reference_sha256=(Hash-Text ([string]$identity.username))
        client_secret_recorded=$false
      }
      broker=[ordered]@{
        provider='OpenBao'
        role='officev2-prod-publisher-snapshot'
        logical_path='officev2-prod/data/instagram-publisher-snapshot'
        role_id_reference_sha256=(Hash-Text ([string]$broker.read_role_id))
        secret_id_reference_sha256=(Hash-Text ([string]$broker.read_secret_id))
        administration='APPROLE_NARROW'
        admin_role='officev2-prod-broker-admin'
        admin_role_id_reference_sha256=(Hash-Text ([string]$broker.admin_role_id))
        admin_secret_id_reference_sha256=(Hash-Text ([string]$broker.admin_secret_id))
        exact_scope_read_http=200
        unrelated_scope_http=403
        admin_unrelated_scope_http=403
        root_generated_during_bootstrap_only=$true
        root_token_persisted=$false
        generated_root_revoked=$true
      }
      pilot_broker_rebound=[ordered]@{
        status='PASS'
        credential_reference_sha256=$pilotHash
        role_id_reference_sha256=$pilotRefresh.RoleIdReferenceSha256
        secret_id_reference_sha256=$pilotRefresh.SecretIdReferenceSha256
        dpapi_blob_sha256=$pilotRefresh.BlobSha256
        runtime_plaintext_removed=$true
      }
      shadow_runtime_secret_recap='PASS'
      correlated_probe=[ordered]@{
        status=$runtime.status
        identity_persistent=$runtime.identity.persistent_principal
        authorization_decision=$runtime.authorization.decision
        broker_exact_scope_read_http=$runtime.broker.exact_scope_read_http
        broker_unrelated_scope_http=$runtime.broker.unrelated_scope_http
        provider_runtime_http=$runtime.provider.runtime_http
        provider_meta_health_http=$runtime.provider.meta_health_http
        provider_jobs_http=$runtime.provider.jobs_http
        provider_write_run_http=$runtime.provider.write_run_http
      }
      dpapi_bundle_ref='D:/Velvet/OfficeV2Lab/state/phase3b-security/production/production-read-bundle.dpapi'
      dpapi_acl_protected=$acl.AreAccessRulesProtected
      authorization_receipt_sha256=(Get-FileHash $authorization -Algorithm SHA256).Hash.ToLowerInvariant()
      raw_secret_recorded=$false
      production_authority_change=$true
      production_authority_active=$false
      production_writer_change=$false
      external_mutation_allowed=$false
      production_promoted=$false
      next_gate='Rotate provider SNAPSHOT_TOKEN, invalidate PILOT provider credential, update production OpenBao value through narrow admin AppRole, and re-prove correlated read before promotion.'
    }
    Write-Json $bindingReceipt $doc
    Write-Output ('PASS PRODUCTION_RUNTIME_PREPARE binding_sha256='+(Get-FileHash $bindingReceipt -Algorithm SHA256).Hash.ToLowerInvariant())
    exit 0
  } catch {
    $cause=$_.Exception.Message
    if(Test-Path $prodBlob){Remove-Item -Force $prodBlob -ErrorAction SilentlyContinue}
    if($brokerBootstrapped -and $broker){
      try {
        $cleanupBundle=[pscustomobject]@{
          admin_role_id=[string]$broker.admin_role_id
          admin_secret_id=[string]$broker.admin_secret_id
          role_id=[string]$broker.read_role_id
          secret_id=[string]$broker.read_secret_id
        }
        $cleanupInput=New-BrokerAdminInput $cleanupBundle
        [void](Invoke-Wsl $openbaoBind @('Cleanup') $cleanupInput)
      } catch {}
    }
    if($pilotHash){
      try {
        if(-not $pilotRefreshed){$pilotRefresh=Refresh-Pilot-AppRole $pilotHash;$pilotRefreshed=$true}
        Recapture-ShadowRuntimeSecrets
      } catch {}
    }
    if($identityCreated -and $machineId){try{[void](Invoke-Wsl $zitadelDelete @($machineId))}catch{}}
    throw ('production prepare failed closed: '+$cause)
  } finally {
    $pilotToken=$null; $identityRaw=$null; $brokerRaw=$null; $bundleJson=$null; $bundle=$null; $cleanupInput=$null
    [GC]::Collect()
  }
}

# Rotate
if(-not (Test-Path $prodBlob)){throw 'production runtime bundle missing; run Prepare first'}
if(-not (Test-Path $bindingReceipt)){throw 'production runtime binding receipt missing; run Prepare first'}
$binding=Get-Content $bindingReceipt -Raw | ConvertFrom-Json
if($binding.status -ne 'PASS' -or $binding.production_promoted -ne $false){throw 'production runtime binding is not ready for Rotate'}
$bundleJson=Unprotect-Text $prodBlob
$bundle=$bundleJson|ConvertFrom-Json
foreach($f in @('role_id','secret_id','admin_role_id','admin_secret_id')){if(-not [string]$bundle.$f){throw "production runtime bundle missing $f"}}
$oldToken=$null; $newToken=$null
$providerChanged=$false; $brokerChanged=$false
try {
  $oldToken=Read-Pilot-Token
  $oldHash=Hash-Text $oldToken
  if($oldHash -ne [string]$binding.active_credential_reference_sha256 -or $oldHash -ne $pilotExpected){throw 'pre-rotation PILOT credential hash mismatch'}
  $newToken=Random-Token
  $newHash=Hash-Text $newToken
  if($newHash -eq $oldHash){throw 'provider rotation generated duplicate credential reference'}

  Put-Snapshot $newToken
  $providerChanged=$true
  $oldAfter=0; $newRead=0
  for($i=0;$i -lt 30;$i++){
    $oldAfter=Http-Code $oldToken 'GET' '/v1/runtime'
    $newRead=Http-Code $newToken 'GET' '/v1/runtime'
    if($oldAfter -eq 401 -and $newRead -eq 200){break}
    Start-Sleep -Seconds 2
  }
  $newMeta=Http-Code $newToken 'GET' '/v1/meta-health'
  $newJobs=Http-Code $newToken 'GET' '/v1/jobs'
  $newWrite=Http-Code $newToken 'POST' '/v1/run'
  if($oldAfter -ne 401 -or $newRead -ne 200 -or $newMeta -ne 200 -or $newJobs -ne 200 -or $newWrite -ne 401){throw "provider rotation boundary failed old=$oldAfter read=$newRead meta=$newMeta jobs=$newJobs write=$newWrite"}

  $baoInput=New-BrokerAdminInput $bundle $newToken
  $bao=Invoke-Wsl $openbaoBind @('Rotate') $baoInput
  if($bao.ExitCode -ne 0){throw ('production OpenBao Rotate failed: '+(Safe-Wsl-Error $bao 'broker rotate denied'))}
  $baoProof=$bao.Stdout.Trim() | ConvertFrom-Json
  if($baoProof.status -ne 'PASS' -or [string]$baoProof.credential_reference_sha256 -ne $newHash -or $baoProof.admin_auth -ne 'APPROLE_NARROW' -or $baoProof.root_used -ne $false -or $baoProof.read_exact_scope_http -ne 200 -or $baoProof.read_unrelated_scope_http -ne 403){throw 'production OpenBao Rotate proof mismatch'}
  $brokerChanged=$true

  [void](Invoke-Production-Read $bundleJson $newHash)
  $runtime=Get-Content $runtimeReceipt -Raw | ConvertFrom-Json
  if($runtime.status -ne 'PASS' -or [string]$runtime.broker.credential_reference_sha256 -ne $newHash){throw 'post-rotation production correlated proof mismatch'}

  $rotation=[ordered]@{
    schema='velvetos.office-v2.phase3b-production-provider-rotation.v0'
    captured_at=[DateTime]::UtcNow.ToString('o')
    status='PASS'
    scope_id='instagram-publisher-snapshot-read'
    old_credential_reference_sha256=$oldHash
    new_credential_reference_sha256=$newHash
    provider=[ordered]@{old_after_rotate_http=$oldAfter;new_runtime_http=$newRead;new_meta_health_http=$newMeta;new_jobs_http=$newJobs;new_write_run_http=$newWrite}
    broker=[ordered]@{role='officev2-prod-publisher-snapshot';logical_path='officev2-prod/data/instagram-publisher-snapshot';credential_reference_sha256=$newHash;administration='APPROLE_NARROW';root_used=$false;root_token_persisted=$false;bootstrap_root_revoked=$true;admin_unrelated_scope_http=403}
    correlated_read=[ordered]@{status=$runtime.status;identity_persistent=$runtime.identity.persistent_principal;authorization_decision=$runtime.authorization.decision;exact_scope_read_http=$runtime.broker.exact_scope_read_http;unrelated_scope_http=$runtime.broker.unrelated_scope_http;provider_write_run_http=$runtime.provider.write_run_http}
    pilot_provider_credential_invalidated=($oldAfter -eq 401)
    rollback_available=$true
    raw_secret_recorded=$false
    production_writer_change=$false
    external_mutation_allowed=$false
    production_promoted=$false
  }
  Write-Json $rotationReceipt $rotation

  $binding.active_credential_reference_sha256=$newHash
  $binding.mode='ROTATED_PRODUCTION_CREDENTIAL_READY_FOR_PROMOTION'
  $binding.provider_credential_rotated=$true
  $binding.production_authority_active=$false
  $binding.next_gate='Run production recovery/DR drill, exact regression and merged-main CI, then write sanitized promotion receipt and advance Project State.'
  $binding.captured_at=[DateTime]::UtcNow.ToString('o')
  Write-Json $bindingReceipt $binding
  Write-Output ('PASS PRODUCTION_RUNTIME_ROTATE new_ref='+$newHash+' receipt_sha256='+(Get-FileHash $rotationReceipt -Algorithm SHA256).Hash.ToLowerInvariant())
  exit 0
} catch {
  $cause=$_.Exception.Message
  if($providerChanged -and $oldToken){
    try {
      Put-Snapshot $oldToken
      for($i=0;$i -lt 30;$i++){if((Http-Code $oldToken 'GET' '/v1/runtime') -eq 200){break};Start-Sleep -Seconds 2}
      if($brokerChanged){$rollbackBrokerInput=New-BrokerAdminInput $bundle $oldToken;[void](Invoke-Wsl $openbaoBind @('Rotate') $rollbackBrokerInput)}
    } catch {}
  }
  $fail=[ordered]@{
    schema='velvetos.office-v2.phase3b-production-provider-rotation.v0'
    captured_at=[DateTime]::UtcNow.ToString('o')
    status='FAIL_CLOSED'
    error=$cause
    provider_change_attempted=$providerChanged
    broker_change_attempted=$brokerChanged
    rollback_attempted=($providerChanged -and [bool]$oldToken)
    raw_secret_recorded=$false
    production_authority_active=$false
    production_writer_change=$false
    external_mutation_allowed=$false
    production_promoted=$false
  }
  Write-Json $rotationReceipt $fail
  throw ('production rotation failed closed: '+$cause)
} finally {
  $oldToken=$null; $newToken=$null; $bundleJson=$null; $bundle=$null; $baoInput=$null; $rollbackBrokerInput=$null
  [GC]::Collect()
}
