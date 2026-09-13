param(
  [switch]$StartWorker,
  [switch]$SkipVoiceStudioInstall
)

$ErrorActionPreference = 'Stop'
$HostId = 'sderot-win'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $Root

function Fail([string]$Message) { throw "FAIL $Message" }
function Say([string]$Message) { Write-Host $Message }

if (-not [Environment]::Is64BitOperatingSystem) { Fail 'Windows x64 is required' }

$ManifestPath = Join-Path $Root 'packages\vfmcp\TOOLCHAIN-VERSIONS.json'
$Manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$HyperFramesVersion = [string]$Manifest.components.hyperframes.version
$NodeVersionPin = [string]$Manifest.components.node.version
$NodeMinMajor = [int]$Manifest.components.node.minimumMajor
$FfmpegPackage = [string]$Manifest.components.ffmpegStatic.package
$FfmpegVersion = [string]$Manifest.components.ffmpegStatic.version
$VoiceVersion = [string]$Manifest.components.voicestudio.version
$VoiceArtifact = [string]$Manifest.components.voicestudio.windowsArtifact

$StateDir = Join-Path $env:USERPROFILE '.velvetos'
$ToolchainDir = Join-Path $StateDir 'toolchain'
$LocalBin = Join-Path $env:USERPROFILE '.velvetos\bin'
New-Item -ItemType Directory -Force -Path $StateDir,$ToolchainDir,$LocalBin | Out-Null

function Prepend-Path([string]$PathValue) {
  if (-not ($env:Path -split ';' | Where-Object { $_ -eq $PathValue })) {
    $env:Path = "$PathValue;$env:Path"
  }
}

function Persist-UserPath([string]$PathValue) {
  $current = [Environment]::GetEnvironmentVariable('Path','User')
  $parts = @($current -split ';' | Where-Object { $_ })
  if ($parts -notcontains $PathValue) {
    [Environment]::SetEnvironmentVariable('Path', (($PathValue) + ';' + ($parts -join ';')), 'User')
  }
  Prepend-Path $PathValue
}

function Get-NodeMajor {
  try {
    $v = (& node --version 2>$null).Trim()
    if ($v -match '^v?(\d+)') { return [int]$Matches[1] }
  } catch {}
  return 0
}

function Install-NodeLocal {
  $arch = 'win-x64'
  $zipName = "node-v$NodeVersionPin-$arch.zip"
  $base = "https://nodejs.org/dist/v$NodeVersionPin"
  $zipPath = Join-Path $env:TEMP $zipName
  $nodeRoot = Join-Path $ToolchainDir "node-v$NodeVersionPin-$arch"
  Say "Installing Node v$NodeVersionPin user-locally..."
  Invoke-WebRequest -UseBasicParsing "$base/$zipName" -OutFile $zipPath
  if (Test-Path $nodeRoot) { Remove-Item -Recurse -Force $nodeRoot }
  Expand-Archive -Path $zipPath -DestinationPath $ToolchainDir -Force
  Remove-Item -Force $zipPath
  if (-not (Test-Path (Join-Path $nodeRoot 'node.exe'))) { Fail 'Node binary missing after extraction' }
  Persist-UserPath $nodeRoot
}

if ((Get-NodeMajor) -lt $NodeMinMajor) { Install-NodeLocal }
if ((Get-NodeMajor) -lt $NodeMinMajor) { Fail "Node >=$NodeMinMajor required" }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { Fail 'npm missing after Node bootstrap' }

$NpmPrefix = Join-Path $StateDir 'npm-global'
New-Item -ItemType Directory -Force -Path $NpmPrefix | Out-Null
$env:NPM_CONFIG_PREFIX = $NpmPrefix
Persist-UserPath $NpmPrefix

$FfmpegRoot = Join-Path $ToolchainDir 'ffmpeg-ffprobe-static'
if (-not (Test-Path (Join-Path $FfmpegRoot 'node_modules\ffmpeg-ffprobe-static\ffmpeg.exe'))) {
  Say 'Installing FFmpeg + ffprobe user-locally...'
  New-Item -ItemType Directory -Force -Path $FfmpegRoot | Out-Null
  & npm install --prefix $FfmpegRoot --no-audit --no-fund "$FfmpegPackage@$FfmpegVersion"
  if ($LASTEXITCODE -ne 0) { Fail 'FFmpeg package install failed' }
}
$FfmpegExe = Join-Path $FfmpegRoot 'node_modules\ffmpeg-ffprobe-static\ffmpeg.exe'
$FfprobeExe = Join-Path $FfmpegRoot 'node_modules\ffmpeg-ffprobe-static\ffprobe.exe'
if (-not (Test-Path $FfmpegExe) -or -not (Test-Path $FfprobeExe)) { Fail 'FFmpeg binaries missing' }
Copy-Item $FfmpegExe (Join-Path $LocalBin 'ffmpeg.exe') -Force
Copy-Item $FfprobeExe (Join-Path $LocalBin 'ffprobe.exe') -Force
Persist-UserPath $LocalBin

$CurrentHf = ''
try { $CurrentHf = (& hyperframes --version 2>$null | Select-Object -First 1).Trim().TrimStart('v') } catch {}
if ($CurrentHf -ne $HyperFramesVersion) {
  Say "Installing HyperFrames $HyperFramesVersion..."
  & npm install -g --no-audit --no-fund "hyperframes@$HyperFramesVersion"
  if ($LASTEXITCODE -ne 0) { Fail 'HyperFrames install failed' }
}
$CurrentHf = (& hyperframes --version | Select-Object -First 1).Trim().TrimStart('v')
if ($CurrentHf -ne $HyperFramesVersion) { Fail "HyperFrames version mismatch: expected $HyperFramesVersion got $CurrentHf" }
$env:HYPERFRAMES_NO_UPDATE_CHECK = '1'
$env:HYPERFRAMES_NO_AUTO_INSTALL = '1'
Say 'Ensuring HyperFrames browser runtime...'
& hyperframes browser ensure
if ($LASTEXITCODE -ne 0) { Fail 'HyperFrames browser ensure failed' }

$Python = $null
foreach ($candidate in @('python','py')) {
  if (Get-Command $candidate -ErrorAction SilentlyContinue) { $Python = $candidate; break }
}
if (-not $Python) {
  if (Get-Command winget -ErrorAction SilentlyContinue) {
    Say 'Installing Python 3.11 for VelvetOS adapters...'
    & winget install --id Python.Python.3.11 -e --accept-source-agreements --accept-package-agreements
    $Python = 'python'
  } else { Fail 'Python 3.11+ is required and winget is unavailable' }
}

Say 'Running HyperFrames doctor...'
& $Python scripts/vf_hyperframes.py doctor
if ($LASTEXITCODE -ne 0) { Fail 'HyperFrames doctor failed' }

$SmokeRoot = Join-Path $env:TEMP 'velvet-hyperframes-windows-smoke'
if (Test-Path $SmokeRoot) { Remove-Item -Recurse -Force $SmokeRoot }
New-Item -ItemType Directory -Force -Path (Join-Path $SmokeRoot 'renders') | Out-Null
$SmokeHtml = @'
<!doctype html>
<html lang="he">
<head><meta charset="utf-8"><style>
html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#000}
.frame{width:1080px;height:1920px;display:flex;align-items:center;justify-content:center;background:#000;color:#fff;font-family:Arial,sans-serif}
.label{font-size:76px;font-weight:700;direction:rtl;text-align:center}
</style></head>
<body><div class="frame" data-composition-id="main" data-width="1080" data-height="1920" data-start="0" data-duration="2" data-no-timeline><div class="label" dir="rtl">בדיקת מנוע וידאו</div></div></body>
</html>
'@
Set-Content -Path (Join-Path $SmokeRoot 'index.html') -Value $SmokeHtml -Encoding UTF8
$SmokeRequest = @{
  jobId='windows-host-smoke'; backend='hyperframes'; projectDir=$SmokeRoot; composition='index.html'; stage='review'; target='review'; format='mp4'; resolution='portrait'; fps=30; quality='standard'; output='renders/host-smoke.mp4'; audioRequired=$false; strictAll=$false
} | ConvertTo-Json
Set-Content -Path (Join-Path $SmokeRoot 'request.json') -Value $SmokeRequest -Encoding UTF8
& $Python scripts/vf_hyperframes.py run (Join-Path $SmokeRoot 'request.json')
if ($LASTEXITCODE -ne 0) { Fail 'HyperFrames smoke render failed' }
$RenderReceipt = Join-Path $SmokeRoot 'renders\host-smoke.mp4.receipt.json'
if (-not (Test-Path $RenderReceipt)) { Fail 'HyperFrames smoke receipt missing' }

$VoiceCandidates = @(
  (Join-Path $env:LOCALAPPDATA 'VoiceStudio (Current User)\VoiceStudio.exe'),
  (Join-Path $env:LOCALAPPDATA 'VoiceStudio\VoiceStudio.exe'),
  (Join-Path $env:ProgramFiles 'VoiceStudio\VoiceStudio.exe')
)
$VoiceExe = $VoiceCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $VoiceExe -and -not $SkipVoiceStudioInstall) {
  $msi = Join-Path $env:TEMP $VoiceArtifact
  $url = "https://github.com/debpalash/VoiceStudio/releases/download/v$VoiceVersion/$VoiceArtifact"
  Say "Installing VoiceStudio $VoiceVersion current-user build..."
  Invoke-WebRequest -UseBasicParsing $url -OutFile $msi
  $p = Start-Process msiexec.exe -ArgumentList @('/i', $msi, '/qn', 'AUTOLAUNCHAPP=0', '/L*V', (Join-Path $env:TEMP 'VoiceStudio-user-install.log')) -Wait -PassThru
  if ($p.ExitCode -ne 0) { Fail "VoiceStudio MSI failed with exit $($p.ExitCode)" }
  $VoiceExe = $VoiceCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if (-not $VoiceExe) { Fail 'VoiceStudio executable not found' }

$ApiReady = $false
try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:3900/.well-known/voicestudio-speech' -TimeoutSec 3; $ApiReady = ($r.service_version -eq $VoiceVersion) } catch {}
if (-not $ApiReady) {
  Say 'Launching VoiceStudio...'
  Start-Process $VoiceExe | Out-Null
  foreach ($i in 1..8) {
    Start-Sleep -Seconds 3
    try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:3900/.well-known/voicestudio-speech' -TimeoutSec 3; if ($r.service_version -eq $VoiceVersion) { $ApiReady = $true; break } } catch {}
  }
}
if (-not $ApiReady) {
  Say 'ACTION REQUIRED ONCE: VoiceStudio is waiting for first-run confirmation. In the VoiceStudio window press Start installation, let setup finish, then rerun this same script.'
  exit 3
}

& $Python scripts/vf_speech.py doctor
if ($LASTEXITCODE -ne 0) { Fail 'VoiceStudio speech doctor failed' }

$RenderState = @{
  schemaVersion=1; hostId=$HostId; hostname=$env:COMPUTERNAME; platform='Windows'; role='velvetos-render-host'; backend='hyperframes'; hyperframesVersion=$HyperFramesVersion; smokeReceipt=$RenderReceipt; status='host-smoke-verified'; verifiedAt=(Get-Date).ToUniversalTime().ToString('o')
}
$SpeechState = @{
  schemaVersion=1; hostId=$HostId; hostname=$env:COMPUTERNAME; platform='Windows'; role='velvetos-speech-host'; provider='voicestudio'; providerVersion=$VoiceVersion; serviceRoot='http://127.0.0.1:3900'; compute='cpu-on-windows-amd'; status='provider-api-verified'; verifiedAt=(Get-Date).ToUniversalTime().ToString('o')
}
$RenderState | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $StateDir 'render-host.json') -Encoding UTF8
$SpeechState | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $StateDir 'speech-host.json') -Encoding UTF8
Say "OK Windows media fallback verified host=$HostId hyperframes=$HyperFramesVersion voicestudio=$VoiceVersion"

if (-not (Get-Command agent -ErrorAction SilentlyContinue)) { Fail 'Cursor agent CLI is missing; install/login once, then rerun with -StartWorker' }
& agent status
if ($LASTEXITCODE -ne 0) { Fail "Cursor agent is not logged in; run 'agent login' once" }

if ($StartWorker) {
  Say "Starting Cursor worker '$HostId'. Keep this PowerShell session running."
  & agent worker --name $HostId start
  exit $LASTEXITCODE
}
Say "HOST READY. Start fallback worker with: powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-media-host-windows.ps1 -StartWorker"
