# Office #604 LAB ONLY: one-shot Windows interactive-user identity proof.
# NOT a worker, signed lease, credential bridge, model runner or GUI controller.
[CmdletBinding()]
param(
  [ValidateSet('Controller','Child')][string]$Mode='Controller',
  [string]$AttemptId='',
  [string]$ExpectedSourceSha256=''
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'

$Schema='velvetos.office2.604.windows-user-context-one-shot-lab.v1'
$Root='D:\Velvet\Pilots\OfficeP0UserBridgeCP054-20261014'
$TaskPrefix='VelvetOS-CP054-UserBridge-'
$AllowedHost='CHRIS'
$AllowedUser='CHRIS\Chris'
$Powershell='C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
$Schtasks='C:\Windows\System32\schtasks.exe'

function Deny([string]$Reason) { throw "LAB_REFUSED_$Reason" }
function Identity {
  $win=[Security.Principal.WindowsIdentity]::GetCurrent()
  $principal=New-Object Security.Principal.WindowsPrincipal($win)
  return @{
    user=$win.Name
    system=[bool]$win.IsSystem
    elevated=[bool]$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    session=[int](Get-Process -Id $PID).SessionId
  }
}
function IsGuid([string]$Value) {
  return ($Value -match '^[0-9a-f]{32}$')
}
if ([Environment]::MachineName -ine $AllowedHost) { Deny 'WRONG_HOST' }
if (-not (Test-Path -LiteralPath $Powershell -PathType Leaf) -or
    -not (Test-Path -LiteralPath $Schtasks -PathType Leaf)) { Deny 'WINDOWS_TOOLS_ABSENT' }
if (([IO.Path]::GetFullPath($PSCommandPath)) -notmatch '(?i)\\user-session-bridge\.ps1$') {
  Deny 'UNEXPECTED_SOURCE_FILENAME'
}

if ($Mode -eq 'Child') {
  if (-not (IsGuid $AttemptId)) { Deny 'INVALID_ATTEMPT_ID' }
  $who=Identity
  if ($who.system -or $who.elevated -or $who.session -ne 1 -or
      $who.user -ine $AllowedUser) { Deny 'INTERACTIVE_LOW_PRIVILEGE_IDENTITY' }
  if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
    Deny 'PRECREATED_ROOT_REQUIRED'
  }
  $destination=Join-Path $Root ("receipt-"+$AttemptId+".json")
  if (Test-Path -LiteralPath $destination) { Deny 'RECEIPT_COLLISION' }
  $receipt=[ordered]@{
    schema=$Schema
    status='PASS_USER_CONTEXT_ONLY'
    attempt_id=$AttemptId
    host=[Environment]::MachineName
    principal=$who.user
    session_id=$who.session
    is_system=$who.system
    elevated=$who.elevated
    process_id=$PID
    source_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
    observed_utc=[DateTime]::UtcNow.ToString('o')
    gui_action_executed=$false
    model_called=$false
    model_generated_code_executed=$false
    git_or_provider_write=$false
    core_lease_issued=$false
    isolated_code_executor_proven=$false
    receipt_authenticated_to_core=$false
  }
  $tmp=Join-Path $Root ("pending-"+$AttemptId+"-"+$PID+".tmp")
  $encoding=New-Object System.Text.UTF8Encoding($false)
  [IO.File]::WriteAllText($tmp,(ConvertTo-Json -InputObject $receipt -Depth 5)+[Environment]::NewLine,$encoding)
  Move-Item -LiteralPath $tmp -Destination $destination -ErrorAction Stop
  exit 0
}

if (-not [Security.Principal.WindowsIdentity]::GetCurrent().IsSystem) {
  Deny 'CONTROLLER_REQUIRES_SYSTEM_MANAGEMENT_CONTEXT'
}
if ($ExpectedSourceSha256 -notmatch '^[0-9a-fA-F]{64}$') { Deny 'SOURCE_DIGEST_REQUIRED' }
$actual=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
if ($actual -ine $ExpectedSourceSha256) { Deny 'SOURCE_DIGEST_MISMATCH' }
if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
  Deny 'PRECREATED_ROOT_REQUIRED'
}
if ((Get-ScheduledTask -TaskName ($TaskPrefix+'*') -ErrorAction SilentlyContinue)) {
  Deny 'OTHER_LAB_TASK_STILL_REGISTERED'
}
$acc=Get-CimInstance Win32_UserAccount -Filter "Name='Chris' AND LocalAccount=TRUE" -ErrorAction Stop
if ($null -eq $acc -or [bool]$acc.Disabled -or
    ($acc.Domain+'\'+$acc.Name) -ine $AllowedUser) { Deny 'AUTHORIZED_LOCAL_USER_MISSING' }
$attempt=[Guid]::NewGuid().ToString('N')
$task=$TaskPrefix+$attempt.Substring(0,12)
$receiptPath=Join-Path $Root ("receipt-"+$attempt+".json")
$created=$false
$ok=$false
try {
  $run='powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+$PSCommandPath+'" -Mode Child -AttemptId '+$attempt
  if ($run.Length -ge 261) { Deny 'TASK_COMMAND_LENGTH_OVERFLOW' }
  $create=& $Schtasks /Create /SC ONCE /ST 23:59 /TN $task /TR $run /RU $AllowedUser /IT /RL LIMITED 2>&1
  if ($LASTEXITCODE -ne 0) { Deny 'TASK_CREATE_FAILED' }
  $created=$true
  $info=Get-ScheduledTask -TaskName $task -ErrorAction Stop
  if ($info.Principal.LogonType -ne 'Interactive' -or
      $info.Principal.RunLevel -ne 'Limited') { Deny 'TASK_PRINCIPAL_MISMATCH' }
  if ((Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash -ine
       $ExpectedSourceSha256) { Deny 'SCRIPT_CHANGED_BEFORE_RUN' }
  $runOutput=& $Schtasks /Run /TN $task 2>&1
  if ($LASTEXITCODE -ne 0) { Deny 'TASK_START_FAILED' }
  for ($i=0; $i -lt 28; $i++) {
    Start-Sleep -Milliseconds 350
    if (Test-Path -LiteralPath $receiptPath) { break }
  }
  if (-not (Test-Path -LiteralPath $receiptPath -PathType Leaf)) {
    Deny 'USER_SESSION_RECEIPT_MISSING'
  }
  $d=Get-Content -LiteralPath $receiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($d.schema -ne $Schema -or $d.status -ne 'PASS_USER_CONTEXT_ONLY' -or
      $d.attempt_id -cne $attempt -or $d.principal -ine $AllowedUser -or
      $d.session_id -ne 1 -or $d.is_system -ne $false -or
      $d.elevated -ne $false -or $d.core_lease_issued -ne $false -or
      $d.model_called -ne $false -or $d.git_or_provider_write -ne $false -or
      $d.source_sha256 -ine $actual) { Deny 'INDEPENDENT_READBACK_MISMATCH' }
  $ok=$true
  Write-Output ('PASS_USER_CONTEXT_ONLY attempt='+$attempt+' principal='+$d.principal+' session='+$d.session_id)
  Write-Output ('RECEIPT_SHA256='+((Get-FileHash -LiteralPath $receiptPath -Algorithm SHA256).Hash))
} finally {
  if ($created) {
    $remove=& $Schtasks /Delete /TN $task /F 2>&1
    if ($LASTEXITCODE -ne 0) { $ok=$false; Write-Output 'FAIL_TASK_REMOVE' }
  }
  if (Get-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue) {
    $ok=$false
    Write-Output 'FAIL_TASK_STILL_REGISTERED'
  } else { Write-Output 'TASK_REMOVED=true' }
}
if (-not $ok) { exit 2 }
exit 0
