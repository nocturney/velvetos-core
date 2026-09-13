param(
  [switch]$StartWorker
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$HYPERFRAMES_VERSION = '0.8.34'
$NODE_VERSION_PIN = '22.22.0'
$FFMPEG_STATIC_PACKAGE = 'ffmpeg-ffprobe-static@6.1.2-rc.1'
$HOST_ID = 'sderot-windows'

function Say([string]$Message) { Write-Host $Message }
function Fail([string]$Message) { throw "FAIL $Message" }

if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
  Fail 'this bootstrap is for the Windows fallback render host only'
}

$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $Root

$VelvetDir = Join-Path $env:USERPROFILE '.velvetos'
$Toolchain = Join-Path $VelvetDir 'toolchain'
$NpmPrefix = Join-Path $VelvetDir 'npm'
$StateFile = Join-Path $VelvetDir 'render-host.json'
New-Item -ItemType Directory -Force -Path $Toolchain, $NpmPrefix | Out-Null

$env:HYPERFRAMES_NO_UPDATE_CHECK = '1'
$env:HYPERFRAMES_NO_AUTO_INSTALL = '1'
$env:NPM_CONFIG_PREFIX = $NpmPrefix

function Add-UserPath([string]$PathToAdd) {
  if (-not (Test-Path $PathToAdd)) { return }
  $parts = @($env:Path -split ';' | Where-Object { $_ })
  if ($parts -notcontains $PathToAdd) {
    $env:Path = "$PathToAdd;$env:Path"
  }
  $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
  $userParts = @($userPath -split ';' | Where-Object { $_ })
  if ($userParts -notcontains $PathToAdd) {
    $newUserPath = if ([string]::IsNullOrWhiteSpace($userPath)) { $PathToAdd } else { "$userPath;$PathToAdd" }
    [Environment]::SetEnvironmentVariable('Path', $newUserPath, 'User')
    Say "Persisted user PATH: $PathToAdd"
  }
}

function Get-NodeMajor {
  $cmd = Get-Command node -ErrorAction SilentlyContinue
  if (-not $cmd) { return 0 }
  $version = (& node --version 2>$null | Select-Object -First 1).Trim()
  if ($version -match '^v?(\d+)') { return [int]$Matches[1] }
  return 0
}

function Install-UserNode {
  if (-not [Environment]::Is64BitOperatingSystem) { Fail 'Windows x64 is required for the pinned Node toolchain' }
  $artifact = "node-v$NODE_VERSION_PIN-win-x64.zip"
  $base = "https://nodejs.org/dist/v$NODE_VERSION_PIN"
  $tmp = Join-Path ([IO.Path]::GetTempPath()) ("velvet-node-" + [Guid]::NewGuid().ToString('N'))
  New-Item -ItemType Directory -Force -Path $tmp | Out-Null
  try {
    Say "Installing Node v$NODE_VERSION_PIN user-locally (no admin)..."
    Invoke-WebRequest "$base/$artifact" -OutFile (Join-Path $tmp $artifact)
    Invoke-WebRequest "$base/SHASUMS256.txt" -OutFile (Join-Path $tmp 'SHASUMS256.txt')
    $line = Get-Content (Join-Path $tmp 'SHASUMS256.txt') | Where-Object { $_ -match "\s+$([regex]::Escape($artifact))$" } | Select-Object -First 1
    if (-not $line) { Fail "Node checksum entry not found for $artifact" }
    $expected = ($line -split '\s+')[0].ToLowerInvariant()
    $actual = (Get-FileHash -Algorithm SHA256 (Join-Path $tmp $artifact)).Hash.ToLowerInvariant()
    if ($expected -ne $actual) { Fail "Node checksum mismatch for $artifact" }

    $nodeDir = Join-Path $Toolchain "node-v$NODE_VERSION_PIN-win-x64"
    if (Test-Path $nodeDir) { Remove-Item -Recurse -Force $nodeDir }
    Expand-Archive -Path (Join-Path $tmp $artifact) -DestinationPath $Toolchain -Force
    if (-not (Test-Path (Join-Path $nodeDir 'node.exe'))) { Fail 'Node binary missing after extraction' }
    Add-UserPath $nodeDir
  }
  finally {
    Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
  }
}

if ((Get-NodeMajor) -lt 22) { Install-UserNode }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { Fail 'node missing after bootstrap' }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { Fail 'npm missing after bootstrap' }
if ((Get-NodeMajor) -lt 22) { Fail "Node >=22 required; found $(& node --version)" }

Add-UserPath $NpmPrefix

$FfmpegRoot = Join-Path $Toolchain 'ffmpeg-ffprobe-static'
$FfmpegBin = Join-Path $FfmpegRoot 'node_modules\ffmpeg-ffprobe-static'
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue) -or -not (Get-Command ffprobe -ErrorAction SilentlyContinue)) {
  Say 'Installing FFmpeg + ffprobe user-locally (no admin)...'
  New-Item -ItemType Directory -Force -Path $FfmpegRoot | Out-Null
  & npm install --prefix $FfmpegRoot --no-audit --no-fund $FFMPEG_STATIC_PACKAGE
  if ($LASTEXITCODE -ne 0) { Fail 'npm failed to install ffmpeg-ffprobe-static' }
  if (-not (Test-Path (Join-Path $FfmpegBin 'ffmpeg.exe'))) { Fail 'user-local ffmpeg.exe missing after npm install' }
  if (-not (Test-Path (Join-Path $FfmpegBin 'ffprobe.exe'))) { Fail 'user-local ffprobe.exe missing after npm install' }
  Add-UserPath $FfmpegBin
}
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { Fail 'ffmpeg missing after bootstrap' }
if (-not (Get-Command ffprobe -ErrorAction SilentlyContinue)) { Fail 'ffprobe missing after bootstrap' }

$currentHF = ''
if (Get-Command hyperframes -ErrorAction SilentlyContinue) {
  $currentHF = (& hyperframes --version 2>$null | Select-Object -First 1).Trim().TrimStart('v')
}
if ($currentHF -ne $HYPERFRAMES_VERSION) {
  Say "Installing pinned HyperFrames $HYPERFRAMES_VERSION user-locally..."
  & npm install -g --no-audit --no-fund "hyperframes@$HYPERFRAMES_VERSION"
  if ($LASTEXITCODE -ne 0) { Fail 'HyperFrames npm install failed' }
  Add-UserPath $NpmPrefix
}
if (-not (Get-Command hyperframes -ErrorAction SilentlyContinue)) { Fail 'hyperframes CLI missing after install' }
$currentHF = (& hyperframes --version | Select-Object -First 1).Trim().TrimStart('v')
if ($currentHF -ne $HYPERFRAMES_VERSION) { Fail "HyperFrames version mismatch: expected $HYPERFRAMES_VERSION, got $currentHF" }

function Resolve-Python {
  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) { return @('python') }
  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($py) { return @('py', '-3') }
  if (Get-Command winget -ErrorAction SilentlyContinue) {
    Say 'Installing Python 3.12 for the current user via winget...'
    & winget install --id Python.Python.3.12 -e --scope user --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -eq 0) {
      $userPythonScripts = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312'
      Add-UserPath $userPythonScripts
      Add-UserPath (Join-Path $userPythonScripts 'Scripts')
      if (Get-Command python -ErrorAction SilentlyContinue) { return @('python') }
      if (Get-Command py -ErrorAction SilentlyContinue) { return @('py', '-3') }
    }
  }
  Fail 'Python 3 is required for scripts/vf_hyperframes.py and could not be provisioned automatically'
}

$Python = Resolve-Python
function Invoke-Python([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args) {
  if ($Python.Count -eq 1) { & $Python[0] @Args }
  else { & $Python[0] $Python[1] @Args }
  if ($LASTEXITCODE -ne 0) { Fail "Python command failed: $($Args -join ' ')" }
}

Say 'Ensuring HyperFrames browser runtime...'
& hyperframes browser ensure
if ($LASTEXITCODE -ne 0) { Fail 'hyperframes browser ensure failed' }

Say 'Running VelvetOS host doctor...'
Invoke-Python 'scripts/vf_hyperframes.py' 'doctor'

$SmokeRoot = Join-Path ([IO.Path]::GetTempPath()) 'velvet-hyperframes-host-smoke-windows'
if (Test-Path $SmokeRoot) { Remove-Item -Recurse -Force $SmokeRoot }
New-Item -ItemType Directory -Force -Path (Join-Path $SmokeRoot 'renders') | Out-Null

$html = @'
<!doctype html>
<html lang="he">
<head>
  <meta charset="utf-8" />
  <style>
    html, body { margin: 0; width: 100%; height: 100%; overflow: hidden; background: #000; }
    .frame { width: 1080px; height: 1920px; display: flex; align-items: center; justify-content: center; background: #000; color: #fff; font-family: system-ui, sans-serif; }
    .label { font-size: 76px; font-weight: 700; direction: rtl; text-align: center; }
  </style>
</head>
<body>
  <div class="frame" data-composition-id="main" data-width="1080" data-height="1920" data-start="0" data-duration="2" data-no-timeline>
    <div class="label" dir="rtl">בדיקת מנוע וידאו</div>
  </div>
</body>
</html>
'@
[IO.File]::WriteAllText((Join-Path $SmokeRoot 'index.html'), $html, (New-Object Text.UTF8Encoding($false)))

$request = [ordered]@{
  jobId = 'host-smoke-windows'
  backend = 'hyperframes'
  projectDir = $SmokeRoot
  composition = 'index.html'
  stage = 'review'
  target = 'review'
  format = 'mp4'
  resolution = 'portrait'
  fps = 30
  quality = 'standard'
  output = 'renders/host-smoke.mp4'
  audioRequired = $false
  strictAll = $false
}
$requestPath = Join-Path $SmokeRoot 'request.json'
[IO.File]::WriteAllText($requestPath, ($request | ConvertTo-Json -Depth 5), (New-Object Text.UTF8Encoding($false)))

Say 'Planning smoke render...'
Invoke-Python 'scripts/vf_hyperframes.py' 'plan' $requestPath
Say 'Rendering smoke video...'
Invoke-Python 'scripts/vf_hyperframes.py' 'run' $requestPath

$Receipt = Join-Path $SmokeRoot 'renders\host-smoke.mp4.receipt.json'
if (-not (Test-Path $Receipt)) { Fail 'smoke render receipt missing' }
$receiptData = Get-Content -Raw -Encoding UTF8 $Receipt | ConvertFrom-Json
$commit = 'unknown'
try { $commit = (& git -C $Root rev-parse HEAD).Trim() } catch {}
$state = [ordered]@{
  schemaVersion = 1
  hostId = $HOST_ID
  hostname = $env:COMPUTERNAME
  role = 'velvetos-render-host'
  backend = 'hyperframes'
  hyperframesVersion = $HYPERFRAMES_VERSION
  repoCommit = $commit
  smokeReceiptSha256 = $receiptData.sha256
  smokeVerifiedAt = $receiptData.verifiedAt
  registeredAt = [DateTimeOffset]::UtcNow.ToString('o')
  status = 'host-smoke-verified'
  route = 'cursor-agent-worker'
}
[IO.File]::WriteAllText($StateFile, ($state | ConvertTo-Json -Depth 5), (New-Object Text.UTF8Encoding($false)))

Say 'OK HyperFrames Windows host smoke verified'
Say "  host=$HOST_ID"
Say "  hyperframes=$HYPERFRAMES_VERSION"
Say "  receipt=$Receipt"
Say "  state=$StateFile"

if (-not (Get-Command agent -ErrorAction SilentlyContinue)) {
  Say 'Installing official Cursor CLI for native Windows...'
  Invoke-Expression (Invoke-RestMethod 'https://cursor.com/install?win32=true')
}
if (-not (Get-Command agent -ErrorAction SilentlyContinue)) { Fail 'Cursor agent CLI missing after install' }
& agent status
if ($LASTEXITCODE -ne 0) { Fail "Cursor agent is not logged in. Run 'agent login' once on this Windows PC, then rerun this bootstrap." }

$existingWorker = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "agent(.exe)?\s+worker.*$HOST_ID" }
if ($existingWorker) {
  Say "OK Cursor worker '$HOST_ID' is already running"
  exit 0
}

if ($StartWorker) {
  Say "Starting Windows fallback Cursor worker '$HOST_ID'. This PowerShell window will remain attached."
  & agent worker --name $HOST_ID start
  exit $LASTEXITCODE
}

Say 'HOST READY, WORKER NOT RUNNING'
Say "Start the fallback Edge route with: agent worker --name '$HOST_ID' start"
Say 'Windows is a render/terminal fallback only; do not add --computer-use or --share-desktop.'
