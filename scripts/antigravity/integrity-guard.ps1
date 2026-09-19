param(
  [ValidateSet("shadow", "production")]
  [string]$Mode = "shadow"
)

$ErrorActionPreference = "Stop"
$repo = if ($env:VELVETOS_REPO_ROOT) { $env:VELVETOS_REPO_ROOT } else { "C:\Users\Chris\velvetos-core" }
$manifestPath = Join-Path $repo "automation\antigravity\manifest.json"
$cfgPath = Join-Path $env:USERPROFILE ".gemini\config\config.json"
$sidecarRoot = Join-Path $env:USERPROFILE ".gemini\config\sidecars"
$manifest = Get-Content $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$cfg = Get-Content $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json
$repairs = New-Object System.Collections.Generic.List[string]
$blocked = New-Object System.Collections.Generic.List[string]

function Save-Json([string]$Path, $Value) {
  $json = $Value | ConvertTo-Json -Depth 30
  [System.IO.File]::WriteAllText($Path, $json, (New-Object System.Text.UTF8Encoding($false)))
}

$tz = (Get-TimeZone).Id
if ($tz -ne $manifest.windowsTimezone) {
  $blocked.Add("timezone expected=$($manifest.windowsTimezone) actual=$tz")
}

$projectId = [string]$manifest.antigravityProjectId
$runner = Join-Path $repo "scripts\antigravity\run-automation.ps1"
$guard = Join-Path $repo "scripts\antigravity\integrity-guard.ps1"
foreach ($routine in $manifest.routines) {
  $sidecarId = "velvetos-$($routine.id)"
  $entry = $cfg.sidecars.PSObject.Properties[$sidecarId]
  if (-not $entry) {
    if ($Mode -eq "production") {
      $cfg.sidecars | Add-Member -Force -NotePropertyName $sidecarId -NotePropertyValue ([pscustomobject]@{
        enabled = $true
        projectId = $projectId
      })
      $repairs.Add("$sidecarId config entry restored")
    } else {
      $blocked.Add("$sidecarId config entry missing")
    }
  } else {
    if ($entry.Value.enabled -ne $true) {
      if ($Mode -eq "production") {
        $entry.Value.enabled = $true
        $repairs.Add("$sidecarId enabled restored")
      } else {
        $blocked.Add("$sidecarId disabled")
      }
    }
    if ([string]$entry.Value.projectId -ne $projectId) {
      if ($Mode -eq "production") {
        $entry.Value.projectId = $projectId
        $repairs.Add("$sidecarId projectId repaired")
      } else {
        $blocked.Add("$sidecarId projectId drift")
      }
    }
  }

  $dir = Join-Path $sidecarRoot $sidecarId
  $file = Join-Path $dir "sidecar.json"
  $command = if ($routine.id -eq "integrity-guard") { $guard } else { $runner }
  $args = if ($routine.id -eq "integrity-guard") {
    @($routine.cron, "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $command, "-Mode", $Mode)
  } else {
    @($routine.cron, "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $command, "-RoutineId", $routine.id, "-Mode", $Mode)
  }
  $expected = [ordered]@{
    description = "VelvetOS $($routine.title) $Mode scheduler"
    builtin = "schedule"
    args = $args
    restart_policy = "always"
    display_name = $routine.title
  }
  $needsWrite = $false
  if (-not (Test-Path $file)) {
    $needsWrite = $true
  } else {
    try {
      $actual = Get-Content $file -Raw -Encoding UTF8 | ConvertFrom-Json
      if ($actual.builtin -ne "schedule") { $needsWrite = $true }
      if (($actual.args -join [char]0) -ne ($args -join [char]0)) { $needsWrite = $true }
      if ($actual.restart_policy -ne "always") { $needsWrite = $true }
    } catch {
      $needsWrite = $true
    }
  }
  if ($needsWrite) {
    if ($Mode -eq "production") {
      New-Item -ItemType Directory -Force -Path $dir | Out-Null
      Save-Json $file $expected
      $repairs.Add("$sidecarId schedule/runtime repaired")
    } else {
      $blocked.Add("$sidecarId schedule/runtime drift")
    }
  }
}
$contract = Get-Content (Join-Path $repo "automation\antigravity\CONTRACT.md") -Raw -Encoding UTF8
foreach ($needle in @(
  "V10.3",
  "packages/vfops/out/gmail-send-request.json",
  ".github/workflows/gmail-brief-send.yml",
  "packages/vfops/gmail_brief_request.py",
  "Interactive/connected Gmail"
)) {
  if ($contract -notlike "*$needle*") { $blocked.Add("owner-email contract marker missing: $needle") }
}

foreach ($routine in $manifest.routines) {
  $prompt = Join-Path $repo ($routine.promptFile -replace "/", "\")
  if (-not (Test-Path $prompt)) { $blocked.Add("prompt missing: $($routine.id)") }
}

if ($Mode -eq "production" -and $repairs.Count -gt 0) {
  Save-Json $cfgPath $cfg
}

$eventRoot = Join-Path $env:USERPROFILE ".gemini\antigravity\velvetos-integrity"
New-Item -ItemType Directory -Force -Path $eventRoot | Out-Null
$event = [ordered]@{
  checkedAt = ([DateTimeOffset]::Now).ToString("o")
  mode = $Mode
  repairs = @($repairs)
  blocked = @($blocked)
  verified = ($blocked.Count -eq 0)
}
Save-Json (Join-Path $eventRoot "latest.json") $event

if ($blocked.Count -gt 0) {
  Write-Output ("INTEGRITY_BLOCKED " + ($blocked -join "; "))
  exit 2
}
if ($repairs.Count -gt 0) {
  Write-Output ("INTEGRITY_REPAIRED " + ($repairs -join "; "))
  exit 0
}
Write-Output "INTEGRITY_CLEAN"
exit 0
