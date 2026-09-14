param()

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$MANIM_VERSION = '0.21.0'
$PYTHON_VERSION = '3.12'
$HOST_ID = 'sderot-windows'
$VelvetDir = Join-Path $env:USERPROFILE '.velvetos'
$Toolchain = Join-Path $VelvetDir "toolchain\manim-$MANIM_VERSION-py312"
$StateFile = Join-Path $VelvetDir 'manim-host.json'

function Say([string]$Message) { Write-Host $Message }
function Fail([string]$Message) { throw "FAIL $Message" }

if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
  Fail 'this bootstrap is for the Windows Manim slot host only'
}

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { Fail 'ffmpeg is required' }
if (-not (Get-Command ffprobe -ErrorAction SilentlyContinue)) { Fail 'ffprobe is required' }

$pyCheck = & py -3.12 --version 2>$null
if ($LASTEXITCODE -ne 0) {
  if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { Fail 'Python 3.12 is required and winget is unavailable' }
  Say 'Installing Python 3.12 for current user...'
  & winget install --id Python.Python.3.12 -e --scope user --silent --accept-package-agreements --accept-source-agreements
  if ($LASTEXITCODE -ne 0) { Fail 'Python 3.12 installation failed' }
}
New-Item -ItemType Directory -Force -Path (Split-Path $Toolchain -Parent) | Out-Null
if (-not (Test-Path (Join-Path $Toolchain 'Scripts\python.exe'))) {
  Say "Creating isolated Python $PYTHON_VERSION venv..."
  & py -3.12 -m venv $Toolchain
  if ($LASTEXITCODE -ne 0) { Fail 'venv creation failed' }
}

$Python = Join-Path $Toolchain 'Scripts\python.exe'
$Manim = Join-Path $Toolchain 'Scripts\manim.exe'
$current = ''
if (Test-Path $Manim) {
  $current = (& $Manim --version 2>$null | Select-Object -First 1)
}
if ($current -notmatch [regex]::Escape($MANIM_VERSION)) {
  Say "Installing Manim $MANIM_VERSION into isolated venv..."
  & $Python -m pip install --disable-pip-version-check --no-input "manim==$MANIM_VERSION"
  if ($LASTEXITCODE -ne 0) { Fail 'Manim install failed' }
}

$current = (& $Manim --version | Select-Object -First 1)
if ($current -notmatch [regex]::Escape($MANIM_VERSION)) {
  Fail "Manim version mismatch: expected $MANIM_VERSION, got $current"
}
Say "OK Manim version $MANIM_VERSION"

$SmokeRoot = Join-Path ([IO.Path]::GetTempPath()) 'velvet-manim-windows-smoke'
if (Test-Path $SmokeRoot) { Remove-Item -Recurse -Force $SmokeRoot }
New-Item -ItemType Directory -Force -Path $SmokeRoot | Out-Null
$Scene = @'
from manim import *
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16

class VelvetSmoke(Scene):
    def construct(self):
        title = Text("VF technical slot", font_size=42).to_edge(UP)
        line = Line(LEFT * 2.5, RIGHT * 2.5)
        dot = Dot(line.get_start())
        label = Text("5.0 mm", font_size=34).next_to(line, DOWN)
        self.add(title, line, dot, label)
        self.play(dot.animate.move_to(line.get_end()), run_time=1.2)
        self.wait(0.3)
'@
$ScenePath = Join-Path $SmokeRoot 'scene.py'
[IO.File]::WriteAllText($ScenePath, $Scene, (New-Object Text.UTF8Encoding($false)))
$MediaDir = Join-Path $SmokeRoot 'media'
Say 'Rendering Manim technical-slot smoke...'
& $Manim -ql --disable_caching --format mp4 --media_dir $MediaDir $ScenePath VelvetSmoke
if ($LASTEXITCODE -ne 0) { Fail 'Manim smoke render failed' }

$Output = Get-ChildItem -Path $MediaDir -Recurse -Filter 'VelvetSmoke.mp4' | Select-Object -First 1
if (-not $Output) { Fail 'Manim smoke output missing' }
$ProbeRaw = & ffprobe -v error -show_entries stream=codec_type,width,height -show_entries format=duration -of json $Output.FullName
if ($LASTEXITCODE -ne 0) { Fail 'ffprobe failed for Manim smoke' }
$Probe = $ProbeRaw | ConvertFrom-Json
$Video = $Probe.streams | Where-Object { $_.codec_type -eq 'video' } | Select-Object -First 1
if (-not $Video -or $Video.width -ne 1080 -or $Video.height -ne 1920) { Fail 'Manim smoke is not 1080x1920' }
$Duration = [double]$Probe.format.duration
if ($Duration -le 0) { Fail 'Manim smoke duration is zero' }
$Sha = (Get-FileHash -Algorithm SHA256 $Output.FullName).Hash.ToLowerInvariant()

$State = [ordered]@{
  schemaVersion = 1
  hostId = $HOST_ID
  engine = 'manim'
  version = $MANIM_VERSION
  python = $PYTHON_VERSION
  toolchain = $Toolchain
  smoke = 'pass'
  width = 1080
  height = 1920
  duration = $Duration
  sha256 = $Sha
  verifiedAt = [DateTimeOffset]::UtcNow.ToString('o')
}
New-Item -ItemType Directory -Force -Path $VelvetDir | Out-Null
[IO.File]::WriteAllText($StateFile, ($State | ConvertTo-Json -Depth 5), (New-Object Text.UTF8Encoding($false)))

Say 'OK Manim Windows host smoke verified'
Say "  host=$HOST_ID"
Say "  version=$MANIM_VERSION"
Say "  output=$($Output.FullName)"
Say "  sha256=$Sha"
Say "  state=$StateFile"
