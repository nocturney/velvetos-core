$ErrorActionPreference='Stop'
$blob='D:\Velvet\OfficeV2Lab\state\phase3b-security\production\production-read-bundle.dpapi'
$current='D:\Velvet\State\OfficeV2\project-state\CURRENT.json'
$bindingPath='D:\Velvet\Artifacts\OfficeV2\phase3b\evidence\2026-10-07\production-runtime-binding.json'
$rotationPath='D:\Velvet\Artifacts\OfficeV2\phase3b\evidence\2026-10-07\production-provider-rotation.json'
$out='D:\Velvet\Artifacts\OfficeV2\phase3b\evidence\2026-10-07\production-recovery.json'
$script='/var/officev2/artifacts/phase3b-security/production-recovery-drill.sh'
$wsl='C:\Windows\System32\wsl.exe'

function Write-Json($Doc) {
  [IO.File]::WriteAllText($out,($Doc|ConvertTo-Json -Depth 12)+[Environment]::NewLine,[Text.UTF8Encoding]::new($false))
}
function Invoke-Wsl([string]$Expected,[string]$Bundle) {
  $psi=[Diagnostics.ProcessStartInfo]::new()
  $psi.FileName=$wsl
  $psi.Arguments="-d OfficeV2-Lab -u root -- bash $script $Expected"
  $psi.UseShellExecute=$false
  $psi.RedirectStandardInput=$true
  $psi.RedirectStandardOutput=$true
  $psi.RedirectStandardError=$true
  $psi.CreateNoWindow=$true
  $p=[Diagnostics.Process]::new(); $p.StartInfo=$psi; [void]$p.Start()
  $p.StandardInput.Write($Bundle); $p.StandardInput.Close()
  $stdout=$p.StandardOutput.ReadToEnd(); $stderr=$p.StandardError.ReadToEnd()
  $p.WaitForExit()
  return [pscustomobject]@{ExitCode=$p.ExitCode;Stdout=$stdout;Stderr=$stderr}
}

if((whoami) -ne 'chris\chris'){throw 'production recovery drill requires Chris interactive user context'}
foreach($p in @($blob,$current,$bindingPath,$rotationPath)){if(-not (Test-Path $p)){throw "production recovery required file missing: $p"}}
$st=Get-Content $current -Raw|ConvertFrom-Json
if($st.phase -ne 'PHASE_3B_PILOT_ACTIVE' -or $st.checkpoint_id -ne 'office-v2-phase3b-v0-cp016-pilot-active' -or $st.gate -ne 'GREEN'){throw 'production recovery pre-promotion drill requires exact cp016 GREEN'}
$binding=Get-Content $bindingPath -Raw|ConvertFrom-Json
$rotation=Get-Content $rotationPath -Raw|ConvertFrom-Json
if($binding.status -ne 'PASS' -or $binding.mode -ne 'ROTATED_PRODUCTION_CREDENTIAL_READY_FOR_PROMOTION'){throw 'production binding is not rotated/ready'}
if($rotation.status -ne 'PASS' -or $rotation.pilot_provider_credential_invalidated -ne $true){throw 'production provider rotation receipt not PASS'}
$expected=[string]$binding.active_credential_reference_sha256
if(-not $expected -or $expected -ne [string]$rotation.new_credential_reference_sha256){throw 'production recovery credential lineage mismatch'}

$enc=[IO.File]::ReadAllText($blob)
$secure=ConvertTo-SecureString $enc
$cred=[Management.Automation.PSCredential]::new('officev2-production-read',$secure)
$bundle=$cred.GetNetworkCredential().Password
try {
  $r=Invoke-Wsl $expected $bundle
  if($r.ExitCode -ne 0){
    $safe=@(($r.Stderr -split "[\r\n]+")|Where-Object {$_}|Select-Object -Last 1)
    throw ('production recovery drill denied: '+$(if($safe){$safe}else{'unknown'}))
  }
  $proof=$r.Stdout.Trim()|ConvertFrom-Json
  if($proof.status -ne 'PASS' -or $proof.opa.outage_fail_closed -ne $true -or $proof.opa.recovery -ne 'PASS' -or $proof.zitadel.outage_fail_closed -ne $true -or $proof.zitadel.recovery -ne 'PASS' -or $proof.openbao.outage_fail_closed -ne $true -or $proof.openbao.recovery -ne 'PASS' -or $proof.openbao.unseal_without_persistent_root -ne $true){throw 'production recovery sanitized proof mismatch'}
  $doc=[ordered]@{
    schema='velvetos.office-v2.phase3b-production-recovery.v0'
    captured_at=[DateTime]::UtcNow.ToString('o')
    status='PASS'
    scope_id='instagram-publisher-snapshot-read'
    credential_reference_sha256=$expected
    project_state_checkpoint=$st.checkpoint_id
    baseline='PASS'
    opa=$proof.opa
    zitadel=$proof.zitadel
    openbao=$proof.openbao
    raw_secret_recorded=$false
    production_authority_active=$false
    production_writer_change=$false
    external_mutation_performed=$false
    production_promoted=$false
  }
  Write-Json $doc
  Write-Output ('PASS PRODUCTION_RECOVERY receipt_sha256='+(Get-FileHash $out -Algorithm SHA256).Hash.ToLowerInvariant())
  exit 0
} catch {
  $doc=[ordered]@{
    schema='velvetos.office-v2.phase3b-production-recovery.v0'
    captured_at=[DateTime]::UtcNow.ToString('o')
    status='FAIL_CLOSED'
    error=$_.Exception.Message
    raw_secret_recorded=$false
    production_authority_active=$false
    production_writer_change=$false
    external_mutation_performed=$false
    production_promoted=$false
  }
  Write-Json $doc
  throw
} finally {
  $bundle=$null; $cred=$null; $secure=$null
  [GC]::Collect()
}
