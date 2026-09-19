param(
  [Parameter(Mandatory = $true)]
  [string]$RoutineId,
  [ValidateSet("shadow", "production")]
  [string]$Mode = "shadow"
)

$ErrorActionPreference = "Stop"
$agy = "C:\Users\Chris\AppData\Local\agy\bin\agy.exe"
if (-not (Test-Path $agy)) { throw "Antigravity CLI not found: $agy" }

$repo = if ($env:VELVETOS_REPO_ROOT) {
  $env:VELVETOS_REPO_ROOT
} elseif ($Mode -eq "production") {
  "C:\Users\Chris\velvetos-core"
} else {
  "C:\Users\Chris\velvetos-antigravity-migration"
}

$manifestPath = Join-Path $repo "automation\antigravity\manifest.json"
if (-not (Test-Path $manifestPath)) { throw "Manifest not found: $manifestPath" }
$manifest = Get-Content $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$routine = $manifest.routines | Where-Object { $_.id -eq $RoutineId } | Select-Object -First 1
if (-not $routine) { throw "Unknown routine id: $RoutineId" }

$promptPath = Join-Path $repo ($routine.promptFile -replace "/", "\")
if (-not (Test-Path $promptPath)) { throw "Prompt not found: $promptPath" }
$body = Get-Content $promptPath -Raw -Encoding UTF8
$runtimeBanner = @"
VELVETOS_AUTOMATION_ID=$RoutineId
VELVETOS_AUTOMATION_TITLE=$($routine.title)
VELVETOS_AUTOMATION_MODE=$Mode
VELVETOS_EXPECTED_TIMEZONE=Asia/Jerusalem
VELVETOS_EXPECTED_CRON=$($routine.cron)

You are running unattended. Read automation/antigravity/CONTRACT.md first, then current merged/runtime authority before acting.
In shadow mode, do not use shell/terminal commands and obey every shadow restriction.
If a required capability is unavailable, fail closed and report it; do not improvise a weaker path.

"@
$prompt = $runtimeBanner + $body

$logRoot = Join-Path $env:USERPROFILE ".gemini\antigravity\velvetos-automation-logs"
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logPath = Join-Path $logRoot "$RoutineId-$Mode-$stamp.log"

Push-Location $repo
try {
  $priorErrorAction = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  $projectName = if ($Mode -eq "production") { "velvetos-core" } else { "velvetos-antigravity-migration" }
  $output = & $agy --project $projectName -p $prompt --mode accept-edits --output-format text --print-timeout 0 2>&1
  $exit = $LASTEXITCODE
  $ErrorActionPreference = $priorErrorAction
  $output | Tee-Object -FilePath $logPath
} finally {
  $ErrorActionPreference = "Stop"
  Pop-Location
}
if ($exit -ne 0) { throw "Antigravity run failed with exit code $exit. Log: $logPath" }
Write-Output "VELVETOS_AUTOMATION_LOG=$logPath"
