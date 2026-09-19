param(
  [Parameter(Mandatory = $true)]
  [string]$RoutineId,
  [ValidateSet("shadow", "production")]
  [string]$Mode = "shadow"
)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$agy = "C:\Users\Chris\AppData\Local\agy\bin\agy.exe"
if (-not (Test-Path $agy)) { throw "Antigravity CLI not found: $agy" }

$repo = if ($env:VELVETOS_REPO_ROOT) {
  $env:VELVETOS_REPO_ROOT
} else {
  "C:\Users\Chris\velvetos-core"
}

$manifestPath = Join-Path $repo "automation\antigravity\manifest.json"
if (-not (Test-Path $manifestPath)) { throw "Manifest not found: $manifestPath" }
$manifest = Get-Content $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$routine = $manifest.routines | Where-Object { $_.id -eq $RoutineId } | Select-Object -First 1
if (-not $routine) { throw "Unknown routine id: $RoutineId" }
$promptPath = Join-Path $repo ($routine.promptFile -replace "/", "\")
if (-not (Test-Path $promptPath)) { throw "Prompt not found: $promptPath" }
$body = Get-Content $promptPath -Raw -Encoding UTF8

$contextPath = $null
if ($routine.requiresLiveSheets -eq $true) {
  $contextPath = & (Join-Path $repo "scripts\antigravity\fetch-live-context.ps1") -Repo $repo
  if (-not $contextPath -or -not (Test-Path $contextPath)) {
    throw "Required live office context could not be obtained"
  }
}

$runtimeBanner = @"
VELVETOS_AUTOMATION_ID=$RoutineId
VELVETOS_AUTOMATION_TITLE=$($routine.title)
VELVETOS_AUTOMATION_MODE=$Mode
VELVETOS_EXPECTED_TIMEZONE=Asia/Jerusalem
VELVETOS_EXPECTED_CRON=$($routine.cron)
VELVETOS_LIVE_CONTEXT_PATH=$contextPath

You are running unattended under the VelvetOS Antigravity automation contract.
Read automation/antigravity/CONTRACT.md first, then CURRENT merged/runtime authority before acting.
If VELVETOS_LIVE_CONTEXT_PATH is non-empty, treat that fresh provider snapshot as valid Google Sheets evidence for jobs/sku/quotes/books. It is ephemeral execution input, not a new source of truth.
In shadow mode, do not perform external writes, owner email sends, publication, customer messaging, repo writes, scheduler repairs, or branch pushes.
If a required capability is unavailable, fail closed and report it; do not improvise a weaker path.
Before ending a shadow run, output an explicit final SHADOW_PASS or SHADOW_BLOCKED marker.

"@
$prompt = $runtimeBanner + $body
$logRoot = Join-Path $env:USERPROFILE ".gemini\antigravity\velvetos-automation-logs"
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logPath = Join-Path $logRoot "$RoutineId-$Mode-$stamp.log"

$models = @("claude-sonnet-4-6", "gpt-oss-120b-medium", "gemini-3.8-flash-medium")
if ($manifest.modelPolicy -and $manifest.modelPolicy.models) {
  $models = @($manifest.modelPolicy.models)
}

Push-Location $repo
try {
  $lastFailure = $null
  foreach ($model in $models) {
    "MODEL_ATTEMPT routine=$RoutineId model=$model" |
      Tee-Object -FilePath $logPath -Append | Write-Output

    $args = @(
      "--project", "velvetos-core",
      "--model", $model,
      "--mode", "accept-edits",
      "--output-format", "json",
      "--print-timeout", "25s"
    )
    if ($contextPath) {
      $args += @("--add-dir", (Split-Path -Parent $contextPath))
    }
    $args += @("-p", $prompt)
    $prior = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $output = & $agy @args 2>&1
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $prior

    $joined = ($output | Out-String).Trim()
    $response = $joined
    $agyStatus = $null
    try {
      $parsed = $joined | ConvertFrom-Json
      $agyStatus = [string]$parsed.status
      if ($parsed.response) { $response = [string]$parsed.response }
    } catch {
      # Keep raw output for compatibility with a future CLI output change.
    }

    $response | Tee-Object -FilePath $logPath -Append | Write-Output

    $success = ($exitCode -eq 0) -and
      ($joined -notmatch "AGY_ERROR:") -and
      (($null -eq $agyStatus) -or ($agyStatus -eq "SUCCESS"))

    if ($success -and $Mode -eq "shadow") {
      if ($response -match "SHADOW_BLOCKED") {
        throw "Shadow verification blocked for $RoutineId. Log: $logPath"
      }
      $success = $response -match "SHADOW_PASS"
    }
    if ($success) {
      Write-Output "AUTOMATION_OK routine=$RoutineId model=$model log=$logPath"
      return
    }

    $lastFailure = "model=$model exit=$exitCode status=$agyStatus"
    $retryable = $joined -match "RESOURCE_EXHAUSTED|UNAVAILABLE|No capacity|high traffic|quota reached|timed out|timeout|deadline|\b429\b|\b503\b"
    if (-not $retryable) {
      throw "Antigravity run failed without safe model failover. $lastFailure Log: $logPath"
    }

    "MODEL_FAILOVER routine=$RoutineId from=$model" |
      Tee-Object -FilePath $logPath -Append | Write-Output
    Start-Sleep -Seconds 2
  }

  "ENGINE_FAILOVER routine=$RoutineId from=antigravity-cli to=cursor-agent-auto" |
    Tee-Object -FilePath $logPath -Append | Write-Output

  $cursorArgs = @(
    "-p",
    "--trust",
    "--workspace", $repo,
    "--model", "auto",
    "--output-format", "json"
  )
  if ($Mode -eq "shadow") {
    $cursorArgs += @("--mode", "plan", "--force", "--approve-mcps")
  } else {
    $cursorArgs += @("--force", "--approve-mcps")
  }
  if ($contextPath) {
    $cursorArgs += @("--add-dir", (Split-Path -Parent $contextPath))
  }
  $cursorArgs += @($prompt)

  $prior = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  $cursorOutput = & agent @cursorArgs 2>&1
  $cursorExit = $LASTEXITCODE
  $ErrorActionPreference = $prior
  $cursorJoined = ($cursorOutput | Out-String).Trim()
  $cursorResponse = $cursorJoined
  try {
    $cursorParsed = $cursorJoined | ConvertFrom-Json
    if ($cursorParsed.result) { $cursorResponse = [string]$cursorParsed.result }
  } catch { }
  $cursorResponse | Tee-Object -FilePath $logPath -Append | Write-Output

  $cursorSuccess = ($cursorExit -eq 0)
  if ($cursorSuccess -and $Mode -eq "shadow") {
    if ($cursorResponse -match "SHADOW_BLOCKED") {
      throw "Shadow verification blocked for $RoutineId via Cursor fallback. Log: $logPath"
    }
    $cursorSuccess = $cursorResponse -match "SHADOW_PASS"
  }
  if ($cursorSuccess) {
    Write-Output "AUTOMATION_OK routine=$RoutineId engine=cursor-agent-auto log=$logPath"
    return
  }
  throw "All Antigravity models and Cursor fallback unavailable. $lastFailure Log: $logPath"
} finally {
  Pop-Location
}
