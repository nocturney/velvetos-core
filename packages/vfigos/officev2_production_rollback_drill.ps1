$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Net.Http
$pilotBlob='D:\Velvet\OfficeV2Lab\state\phase3b-security\pilot\openbao-pilot-approle.dpapi'
$prodBlob='D:\Velvet\OfficeV2Lab\state\phase3b-security\production\production-read-bundle.dpapi'
$current='D:\Velvet\State\OfficeV2\project-state\CURRENT.json'
$ev='D:\Velvet\Artifacts\OfficeV2\phase3b\evidence\2026-10-07'
$bindingPath=Join-Path $ev 'production-runtime-binding.json'
$rotationPath=Join-Path $ev 'production-provider-rotation.json'
$out=Join-Path $ev 'production-rollback-drill.json'
$runtimeReceipt='D:\Velvet\OfficeV2Lab\artifacts\phase3b-security\shadow-runtime\production-snapshot-read.json'
$wsl='C:\Windows\System32\wsl.exe'
$npx='C:\Program Files\nodejs\npx.cmd'
$base='https://velvetos-instagram-publisher.velvetos-vf.workers.dev'
$workerCandidates=@()
if($env:VELVETOS_CORE){$workerCandidates+=(Join-Path $env:VELVETOS_CORE 'packages\vfigos\cloudflare-publisher')}
$workerCandidates+=@(
  'D:\Velvet\Worktrees\office-v2-phase3b-production-read-20261007\packages\vfigos\cloudflare-publisher',
  'D:\Velvet\Worktrees\office-v2-phase3b-production-authority-20261007\packages\vfigos\cloudflare-publisher',
  'D:\Velvet\Worktrees\office-v2-phase3b-pilot-main-47f74c7f\packages\vfigos\cloudflare-publisher'
)
$workerDir=@($workerCandidates|Where-Object {Test-Path (Join-Path $_ 'wrangler.toml')}|Select-Object -First 1)[0]
if(-not $workerDir){throw 'Cloudflare publisher working directory unavailable'}

function Hash-Text([string]$Value){
  $sha=[Security.Cryptography.SHA256]::Create()
  try{return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Value)))).Replace('-','').ToLowerInvariant()}
  finally{$sha.Dispose()}
}
function Unprotect-Text([string]$Path){
  $enc=[IO.File]::ReadAllText($Path);$sec=ConvertTo-SecureString $enc;$cred=[Management.Automation.PSCredential]::new('officev2',$sec)
  try{return $cred.GetNetworkCredential().Password}finally{$cred=$null;$sec=$null}
}
function Invoke-Wsl([string]$Script,[string[]]$Args=@(),[string]$InputText=''){
  $psi=[Diagnostics.ProcessStartInfo]::new();$psi.FileName=$wsl
  $psi.Arguments=("-d OfficeV2-Lab -u root -- bash "+$Script+$(if($Args.Count){" "+($Args -join ' ')}else{''}))
  $psi.UseShellExecute=$false;$psi.RedirectStandardInput=$true;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true;$psi.CreateNoWindow=$true
  $p=[Diagnostics.Process]::new();$p.StartInfo=$psi;[void]$p.Start();if($InputText){$p.StandardInput.Write($InputText)};$p.StandardInput.Close()
  $stdout=$p.StandardOutput.ReadToEnd();$stderr=$p.StandardError.ReadToEnd();$p.WaitForExit()
  [pscustomobject]@{ExitCode=$p.ExitCode;Stdout=$stdout;Stderr=$stderr}
}
function Invoke-Wrangler([string[]]$Args,[string]$Stdin){
  $old=Get-Location
  try{Set-Location $workerDir;$stdout=($Stdin|& $npx @Args 2>&1|Out-String);[pscustomobject]@{ExitCode=$LASTEXITCODE;Stdout=$stdout}}
  finally{Set-Location $old}
}
function Put-Snapshot([string]$Token){
  $r=Invoke-Wrangler @('--yes','wrangler','secret','put','SNAPSHOT_TOKEN') $Token
  if($r.ExitCode -ne 0){throw 'provider SNAPSHOT_TOKEN update failed during rollback drill'}
}
function Http-Code([string]$Token,[string]$Method,[string]$Path){
  $handler=[Net.Http.HttpClientHandler]::new();$client=[Net.Http.HttpClient]::new($handler)
  try{
    $client.Timeout=[TimeSpan]::FromSeconds(20);$client.DefaultRequestHeaders.Authorization=[Net.Http.Headers.AuthenticationHeaderValue]::new('Bearer',$Token)
    $req=[Net.Http.HttpRequestMessage]::new($(if($Method -eq 'POST'){[Net.Http.HttpMethod]::Post}else{[Net.Http.HttpMethod]::Get}),($base+$Path))
    if($Method -eq 'POST'){$req.Content=[Net.Http.StringContent]::new('{}',[Text.Encoding]::UTF8,'application/json')}
    $resp=$client.SendAsync($req).GetAwaiter().GetResult();[void]$resp.Content.ReadAsStringAsync().GetAwaiter().GetResult();return [int]$resp.StatusCode
  }finally{if($req){$req.Dispose()};if($resp){$resp.Dispose()};$client.Dispose();$handler.Dispose()}
}
function Read-Token([string]$Blob,[string]$Script){
  $bundle=Unprotect-Text $Blob
  try{$r=Invoke-Wsl $Script @() $bundle;if($r.ExitCode -ne 0){throw 'broker token read denied'};$v=$r.Stdout.Trim();if(-not $v){throw 'broker token read empty'};return $v}
  finally{$bundle=$null}
}
function Write-Json($Doc){[IO.File]::WriteAllText($out,($Doc|ConvertTo-Json -Depth 12)+[Environment]::NewLine,[Text.UTF8Encoding]::new($false))}

if((whoami) -ne 'chris\chris'){throw 'production rollback drill requires Chris interactive user context'}
foreach($p in @($pilotBlob,$prodBlob,$current,$bindingPath,$rotationPath)){if(-not(Test-Path $p)){throw "rollback required file missing: $p"}}
$st=Get-Content $current -Raw|ConvertFrom-Json
if($st.phase -ne 'PHASE_3B_PILOT_ACTIVE' -or $st.checkpoint_id -ne 'office-v2-phase3b-v0-cp016-pilot-active' -or $st.gate -ne 'GREEN'){throw 'production rollback drill requires exact cp016 GREEN'}
$binding=Get-Content $bindingPath -Raw|ConvertFrom-Json
$rotation=Get-Content $rotationPath -Raw|ConvertFrom-Json
if($binding.status -ne 'PASS' -or $binding.mode -ne 'ROTATED_PRODUCTION_CREDENTIAL_READY_FOR_PROMOTION'){throw 'production binding is not rotated'}
if($rotation.status -ne 'PASS' -or $rotation.pilot_provider_credential_invalidated -ne $true){throw 'production rotation receipt not PASS'}

$pilotToken=$null;$prodToken=$null;$prodBundle=$null;$providerChanged=$false;$brokerChanged=$false
try{
  $pilotToken=Read-Token $pilotBlob '/var/officev2/artifacts/phase3b-security/pilot-token-read.sh'
  $prodToken=Read-Token $prodBlob '/var/officev2/artifacts/phase3b-security/production-token-read.sh'
  $pilotHash=Hash-Text $pilotToken;$prodHash=Hash-Text $prodToken
  if($pilotHash -ne [string]$rotation.old_credential_reference_sha256){throw 'rollback PILOT credential lineage mismatch'}
  if($prodHash -ne [string]$rotation.new_credential_reference_sha256 -or $prodHash -ne [string]$binding.active_credential_reference_sha256){throw 'rollback production credential lineage mismatch'}

  Put-Snapshot $pilotToken;$providerChanged=$true
  $prodAfter=0;$pilotRead=0
  for($i=0;$i -lt 30;$i++){
    $prodAfter=Http-Code $prodToken 'GET' '/v1/runtime';$pilotRead=Http-Code $pilotToken 'GET' '/v1/runtime'
    if($prodAfter -eq 401 -and $pilotRead -eq 200){break};Start-Sleep -Seconds 2
  }
  $pilotMeta=Http-Code $pilotToken 'GET' '/v1/meta-health';$pilotWrite=Http-Code $pilotToken 'POST' '/v1/run'
  if($prodAfter -ne 401 -or $pilotRead -ne 200 -or $pilotMeta -ne 200 -or $pilotWrite -ne 401){throw "provider rollback boundary failed prod=$prodAfter pilot=$pilotRead meta=$pilotMeta write=$pilotWrite"}

  $bao=Invoke-Wsl '/var/officev2/artifacts/phase3b-security/production-openbao-bind.sh' @('Rotate') $pilotToken
  if($bao.ExitCode -ne 0){throw 'production OpenBao rollback rotate denied'}
  $bp=$bao.Stdout.Trim()|ConvertFrom-Json
  if($bp.status -ne 'PASS' -or [string]$bp.credential_reference_sha256 -ne $pilotHash -or $bp.root_revoked -ne $true){throw 'production OpenBao rollback proof mismatch'}
  $brokerChanged=$true

  $prodBundle=Unprotect-Text $prodBlob
  $rr=Invoke-Wsl '/var/officev2/artifacts/phase3b-security/production-snapshot-read.sh' @($pilotHash) $prodBundle
  if($rr.ExitCode -ne 0){throw 'production path failed after rollback to PILOT credential'}
  $runtime=Get-Content $runtimeReceipt -Raw|ConvertFrom-Json
  if($runtime.status -ne 'PASS' -or [string]$runtime.broker.credential_reference_sha256 -ne $pilotHash -or $runtime.provider.write_run_http -ne 401){throw 'post-rollback production-path proof mismatch'}

  $doc=[ordered]@{
    schema='velvetos.office-v2.phase3b-production-rollback-drill.v0'
    captured_at=[DateTime]::UtcNow.ToString('o')
    status='PASS'
    scope_id='instagram-publisher-snapshot-read'
    project_state_checkpoint=$st.checkpoint_id
    from_credential_reference_sha256=$prodHash
    restored_credential_reference_sha256=$pilotHash
    provider=[ordered]@{former_production_credential_http=$prodAfter;restored_pilot_runtime_http=$pilotRead;restored_pilot_meta_health_http=$pilotMeta;restored_pilot_write_run_http=$pilotWrite}
    broker=[ordered]@{production_path_updated_to_restored_credential=$true;root_token_persisted=$false;generated_root_revoked=$true}
    production_identity_preserved=$true
    production_correlated_read_after_rollback='PASS'
    raw_secret_recorded=$false
    production_authority_active=$false
    production_writer_change=$false
    external_mutation_performed=$false
    production_promoted=$false
    next_gate='Re-run production Rotate to establish a fresh production credential, then run recovery/DR.'
  }
  Write-Json $doc
  $binding.active_credential_reference_sha256=$pilotHash
  $binding.mode='ROLLBACK_DRILL_COMPLETE_REQUIRES_FRESH_ROTATE'
  $binding.provider_credential_rotated=$false
  $binding.rollback_drill_completed=$true
  $binding.captured_at=[DateTime]::UtcNow.ToString('o')
  [IO.File]::WriteAllText($bindingPath,($binding|ConvertTo-Json -Depth 14)+[Environment]::NewLine,[Text.UTF8Encoding]::new($false))
  Write-Output ('PASS PRODUCTION_ROLLBACK_DRILL receipt_sha256='+(Get-FileHash $out -Algorithm SHA256).Hash.ToLowerInvariant())
  exit 0
}catch{
  $cause=$_.Exception.Message
  if($providerChanged -and $prodToken){
    try{
      Put-Snapshot $prodToken
      for($i=0;$i -lt 30;$i++){if((Http-Code $prodToken 'GET' '/v1/runtime') -eq 200){break};Start-Sleep -Seconds 2}
      if($brokerChanged){[void](Invoke-Wsl '/var/officev2/artifacts/phase3b-security/production-openbao-bind.sh' @('Rotate') $prodToken)}
    }catch{}
  }
  $fail=[ordered]@{schema='velvetos.office-v2.phase3b-production-rollback-drill.v0';captured_at=[DateTime]::UtcNow.ToString('o');status='FAIL_CLOSED';error=$cause;rollback_to_pre_drill_state_attempted=($providerChanged -and [bool]$prodToken);raw_secret_recorded=$false;production_authority_active=$false;production_writer_change=$false;external_mutation_performed=$false;production_promoted=$false}
  Write-Json $fail
  throw
}finally{
  $pilotToken=$null;$prodToken=$null;$prodBundle=$null
  [GC]::Collect()
}
