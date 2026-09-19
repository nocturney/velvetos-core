param(
  [string]$Repo = "C:\Users\Chris\velvetos-core",
  [int]$TimeoutSeconds = 300
)

$ErrorActionPreference = "Stop"

function Test-Context([string]$Path) {
  if (-not (Test-Path $Path)) { return $false }
  $payload = Get-Content $Path -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($payload.schema -ne "velvet.antigravity.live_context.v1") { return $false }
  $generated = [DateTimeOffset]$payload.generatedAt
  if ([DateTimeOffset]::UtcNow - $generated -gt [TimeSpan]::FromMinutes(15)) {
    return $false
  }
  foreach ($name in @("jobs", "sku", "quotes", "books")) {
    if (-not $payload.workbooks.$name.spreadsheetId) { return $false }
  }
  return $true
}

$root = Join-Path $env:LOCALAPPDATA "VelvetOS\antigravity-live-context"
New-Item -ItemType Directory -Force -Path $root | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$localOut = Join-Path $root "local-$stamp.json"
$oauthStore = Join-Path $env:USERPROFILE ".gemini\antigravity\mcp_oauth_tokens.json"
# Preferred local provider path: use Antigravity OAuth with direct Google APIs.
if (Test-Path $oauthStore) {
  $env:VELVETOS_ANTIGRAVITY_OAUTH_STORE = $oauthStore
  $env:VELVETOS_LIVE_CONTEXT_OUT = $localOut
  Push-Location $Repo
  try {
    $prior = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & python "scripts\antigravity\export-live-context.py" | Out-Null
    $exit = $LASTEXITCODE
    $ErrorActionPreference = $prior
  } finally {
    Pop-Location
  }
  if ($exit -eq 0 -and (Test-Context $localOut)) {
    Write-Output $localOut
    return
  }
}

# Fallback: deterministic GitHub OIDC/WIF export.
Push-Location $Repo
try {
  $workflow = "antigravity-live-context.yml"
  $started = [DateTimeOffset]::UtcNow
  & gh workflow run $workflow --ref main | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "Failed to dispatch $workflow" }

  $deadline = [DateTimeOffset]::UtcNow.AddSeconds($TimeoutSeconds)
  $runId = $null
  while (-not $runId -and [DateTimeOffset]::UtcNow -lt $deadline) {
    Start-Sleep -Seconds 2
    $raw = & gh run list --workflow $workflow --event workflow_dispatch --branch main --limit 10 --json databaseId,createdAt,status,conclusion
    if ($LASTEXITCODE -ne 0) { throw "Unable to list $workflow runs" }
    $runs = @($raw | ConvertFrom-Json)
    $candidate = $runs |
      Where-Object { [DateTimeOffset]$_.createdAt -ge $started.AddSeconds(-10) } |
      Sort-Object { [DateTimeOffset]$_.createdAt } -Descending |
      Select-Object -First 1
    if ($candidate) { $runId = [string]$candidate.databaseId }
  }
  if (-not $runId) { throw "Timed out locating dispatched live-context run" }

  & gh run watch $runId --exit-status | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "Live-context workflow failed: run=$runId" }

  $dest = Join-Path $root $runId
  if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
  New-Item -ItemType Directory -Force -Path $dest | Out-Null
  & gh run download $runId --name antigravity-live-context --dir $dest | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "Unable to download live-context artifact: run=$runId" }

  $file = Join-Path $dest "antigravity-live-context.json"
  if (-not (Test-Context $file)) { throw "Downloaded live-context artifact failed validation" }
  Write-Output $file
} finally {
  Pop-Location
}
