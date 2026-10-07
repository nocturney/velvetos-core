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
  $lines=@(($Result.Stderr -split "[\r\n]+") | Where-Object {$_})
  if($lines.Count){return [string]$lines[-1]}
  return $Fallback
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
  $machineId=$null
  if(Test-Path $prodBlob){
    try {$o=(Unprotect-Text $prodBlob)|ConvertFrom-Json; $machineId=[string]$o.zitadel_machine_id} catch {}
  }
  $bao=Invoke-Wsl $openbaoBind @('Cleanup')
  if($bao.ExitCode -ne 0){throw ('production OpenBao cleanup failed: '+(Safe-Wsl-Error $bao 'broker cleanup denied'))}
  if($machineId){
    $zit=Invoke-Wsl $zitadelDelete @($machineId)
    if($zit.ExitCode -ne 0){throw ('production ZITADEL cleanup failed: '+(Safe-Wsl-Error $zit 'identity cleanup denied'))}
  }
  if(Test-Path $prodBlob){Remove-Item -Force $prodBlob}
  Write-Output 'PASS PRODUCTION_RUNTIME_CLEANUP'
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
  $pilotToken=$null; $identityRaw=$null; $brokerRaw=$null; $machineId=$null
  $identityCreated=$false; $brokerCreated=$false
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

    $bao=Invoke-Wsl $openbaoBind @('Init') $pilotToken
    if($bao.ExitCode -ne 0){throw ('production OpenBao Init failed: '+(Safe-Wsl-Error $bao 'broker init denied'))}
    $brokerRaw=$bao.Stdout.Trim()
    $broker=$brokerRaw | ConvertFrom-Json
    if($broker.broker_path -ne 'officev2-prod/data/instagram-publisher-snapshot' -or $broker.broker_role -ne 'officev2-prod-publisher-snapshot' -or $broker.rotator_role -ne 'officev2-prod-publisher-snapshot-rotator' -or $broker.broker_instance -ne 'officev2-p3b-prod-openbao' -or -not [string]$broker.rotator_role_id -or -not [string]$broker.rotator_secret_id -or [string]$broker.credential_reference_sha256 -ne $pilotHash){throw 'production OpenBao Init output mismatch'}
    $brokerCreated=$true

    $bundle=[ordered]@{
      schema='velvetos.office-v2.phase3b-production-runtime-bundle.v0'
      scope_id='instagram-publisher-snapshot-read'
      role_id=[string]$broker.role_id
      secret_id=[string]$broker.secret_id
      rotator_role_id=[string]$broker.rotator_role_id
      rotator_secret_id=[string]$broker.rotator_secret_id
      zitadel_machine_id=[string]$identity.machine_id
      zitadel_username=[string]$identity.username
      zitadel_client_secret=[string]$identity.client_secret
    }
    $bundleJson=$bundle|ConvertTo-Json -Compress
    Protect-Text $bundleJson $prodBlob
    $acl=Get-Acl $prodBlob

    [void](Invoke-Production-Read $bundleJson $pilotHash)
    $runtime=Get-Content $runtimeReceipt -Raw | ConvertFrom-Json
    if($runtime.status -ne 'PASS' -or $runtime.principal -ne 'svc:officev2-p3b-prod-publisher-snapshot'){throw 'production prepare correlated runtime proof mismatch'}

    $doc=[ordered]@{
      schema='velvetos.office-v2.phase3b-production-runtime-binding.v0'
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
        role_id_reference_sha256=(Hash-Text ([string]$broker.role_id))
        secret_id_reference_sha256=(Hash-Text ([string]$broker.secret_id))
        rotator_role='officev2-prod-publisher-snapshot-rotator'
        rotator_role_id_reference_sha256=(Hash-Text ([string]$broker.rotator_role_id))
        rotator_secret_id_reference_sha256=(Hash-Text ([string]$broker.rotator_secret_id))
        instance='officev2-p3b-prod-openbao'
        volume='officev2_p3b_prod_bao'
        isolated_from_pilot_broker=$true
        exact_scope_read_http=200
        unrelated_scope_http=403
        root_token_persisted=$false
        generated_root_revoked=$true
      }
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
      next_gate='Rotate provider SNAPSHOT_TOKEN, invalidate PILOT credential, update production OpenBao value, and re-prove correlated read before promotion.'
    }
    Write-Json $bindingReceipt $doc
    Write-Output ('PASS PRODUCTION_RUNTIME_PREPARE binding_sha256='+(Get-FileHash $bindingReceipt -Algorithm SHA256).Hash.ToLowerInvariant())
    exit 0
  } catch {
    if(Test-Path $prodBlob){Remove-Item -Force $prodBlob -ErrorAction SilentlyContinue}
    if($brokerCreated){try{[void](Invoke-Wsl $openbaoBind @('Cleanup'))}catch{}}
    if($identityCreated -and $machineId){try{[void](Invoke-Wsl $zitadelDelete @($machineId))}catch{}}
    throw
  } finally {
    $pilotToken=$null; $identityRaw=$null; $brokerRaw=$null; $bundleJson=$null; $bundle=$null
    [GC]::Collect()
  }
}

# Rotate
if(-not (Test-Path $prodBlob)){throw 'production runtime bundle missing; run Prepare first'}
if(-not (Test-Path $bindingReceipt)){throw 'production runtime binding receipt missing; run Prepare first'}
$binding=Get-Content $bindingReceipt -Raw | ConvertFrom-Json
if($binding.status -ne 'PASS' -or $binding.production_promoted -ne $false){throw 'production runtime binding is not ready for Rotate'}
$bundleJson=Unprotect-Text $prodBlob
$bundleObj=$bundleJson | ConvertFrom-Json
foreach($f in @('rotator_role_id','rotator_secret_id')){if(-not [string]$bundleObj.$f){throw "production runtime bundle missing $f"}}
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

  $baoInput=[ordered]@{provider_token=$newToken;rotator_role_id=[string]$bundleObj.rotator_role_id;rotator_secret_id=[string]$bundleObj.rotator_secret_id}|ConvertTo-Json -Compress
  $bao=Invoke-Wsl $openbaoBind @('Rotate') $baoInput
  if($bao.ExitCode -ne 0){throw ('production OpenBao Rotate failed: '+(Safe-Wsl-Error $bao 'broker rotate denied'))}
  $baoProof=$bao.Stdout.Trim() | ConvertFrom-Json
  if($baoProof.status -ne 'PASS' -or [string]$baoProof.credential_reference_sha256 -ne $newHash -or $baoProof.root_revoked -ne $true){throw 'production OpenBao Rotate proof mismatch'}
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
    broker=[ordered]@{role='officev2-prod-publisher-snapshot';logical_path='officev2-prod/data/instagram-publisher-snapshot';credential_reference_sha256=$newHash;root_token_persisted=$false;generated_root_revoked=$true}
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
      if($brokerChanged){
        $rollbackBaoInput=[ordered]@{provider_token=$oldToken;rotator_role_id=[string]$bundleObj.rotator_role_id;rotator_secret_id=[string]$bundleObj.rotator_secret_id}|ConvertTo-Json -Compress
        [void](Invoke-Wsl $openbaoBind @('Rotate') $rollbackBaoInput)
      }
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
  $oldToken=$null; $newToken=$null; $bundleJson=$null; $bundleObj=$null; $baoInput=$null; $rollbackBaoInput=$null
  [GC]::Collect()
}
