param(
    [switch]$SkipHyperFramesInstall,
    [switch]$SkipToolchainInstall
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$HostId = "sderot-windows"
$Repo = Join-Path $env:USERPROFILE "velvetos-core"
$StateDir = Join-Path $env:USERPROFILE ".velvetos"
$StateFile = Join-Path $StateDir "edge-host.json"
$ToolchainDir = Join-Path $StateDir "toolchain"
$NpmPrefix = Join-Path $StateDir "npm"
$HyperFramesVersion = "0.8.34"
$NodeVersionPin = "22.22.0"
$FfmpegStaticPackage = "ffmpeg-ffprobe-static@6.1.2-rc.1"

function Fail([string]$Message) {
    throw "FAIL $Message"
}

function Add-UserPath([string]$PathToAdd) {
    if (-not (Test-Path $PathToAdd)) { return }

    $sessionParts = @($env:Path -split ';' | Where-Object { $_ })
    if ($sessionParts -notcontains $PathToAdd) {
        $env:Path = "$PathToAdd;$env:Path"
    }

    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $userParts = @($userPath -split ';' | Where-Object { $_ })
    if ($userParts -notcontains $PathToAdd) {
        $newPath = if ([string]::IsNullOrWhiteSpace($userPath)) { $PathToAdd } else { "$userPath;$PathToAdd" }
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        Write-Host "Persisted user PATH: $PathToAdd"
    }
}

function Resolve-Command([string]$Name) {
    return Get-Command $Name -ErrorAction SilentlyContinue
}

function Install-WithWinget([string]$Id, [string]$Label) {
    if (-not (Resolve-Command "winget")) {
        Fail "$Label is missing and winget is unavailable for user-local provisioning"
    }

    Write-Host "Installing $Label for current user..."
    & winget install --id $Id -e --scope user --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        Fail "winget failed to install $Label ($Id)"
    }
}

function Ensure-Git {
    if (Resolve-Command "git") { return }
    if ($SkipToolchainInstall) { Fail "git missing and -SkipToolchainInstall was supplied" }

    Install-WithWinget "Git.Git" "Git"
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Git\cmd"),
        (Join-Path $env:ProgramFiles "Git\cmd")
    )
    foreach ($candidate in $candidates) { Add-UserPath $candidate }
    if (-not (Resolve-Command "git")) { Fail "git missing after provisioning; reopen PowerShell once and rerun" }
}

function Get-NodeMajor {
    if (-not (Resolve-Command "node")) { return 0 }
    try {
        $version = (& node --version 2>$null | Select-Object -First 1).Trim()
        if ($version -match '^v?(\d+)') { return [int]$Matches[1] }
    } catch {}
    return 0
}

function Install-UserNode {
    if (-not [Environment]::Is64BitOperatingSystem) {
        Fail "Windows x64 is required for the pinned Node toolchain"
    }

    $artifact = "node-v$NodeVersionPin-win-x64.zip"
    $base = "https://nodejs.org/dist/v$NodeVersionPin"
    $tmp = Join-Path ([IO.Path]::GetTempPath()) ("velvet-node-" + [Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    try {
        Write-Host "Installing Node v$NodeVersionPin user-locally (no admin)..."
        Invoke-WebRequest "$base/$artifact" -OutFile (Join-Path $tmp $artifact)
        Invoke-WebRequest "$base/SHASUMS256.txt" -OutFile (Join-Path $tmp "SHASUMS256.txt")

        $line = Get-Content (Join-Path $tmp "SHASUMS256.txt") | Where-Object { $_ -match "\s+$([regex]::Escape($artifact))$" } | Select-Object -First 1
        if (-not $line) { Fail "Node checksum entry not found for $artifact" }
        $expected = ($line -split '\s+')[0].ToLowerInvariant()
        $actual = (Get-FileHash -Algorithm SHA256 (Join-Path $tmp $artifact)).Hash.ToLowerInvariant()
        if ($expected -ne $actual) { Fail "Node checksum mismatch for $artifact" }

        New-Item -ItemType Directory -Force -Path $ToolchainDir | Out-Null
        $nodeDir = Join-Path $ToolchainDir "node-v$NodeVersionPin-win-x64"
        if (Test-Path $nodeDir) { Remove-Item -Recurse -Force $nodeDir }
        Expand-Archive -Path (Join-Path $tmp $artifact) -DestinationPath $ToolchainDir -Force
        if (-not (Test-Path (Join-Path $nodeDir "node.exe"))) { Fail "Node binary missing after extraction" }
        Add-UserPath $nodeDir
    }
    finally {
        Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
    }
}

function Ensure-Node {
    if ((Get-NodeMajor) -ge 22) { return }
    if ($SkipToolchainInstall) { Fail "Node >=22 missing and -SkipToolchainInstall was supplied" }
    Install-UserNode
    if ((Get-NodeMajor) -lt 22) { Fail "Node >=22 required; found $(node --version 2>$null)" }
}

function Resolve-Python {
    if (Resolve-Command "python") {
        try {
            & python --version *> $null
            if ($LASTEXITCODE -eq 0) { return @("python") }
        } catch {}
    }
    if (Resolve-Command "py") {
        try {
            & py -3 --version *> $null
            if ($LASTEXITCODE -eq 0) { return @("py", "-3") }
        } catch {}
    }

    if ($SkipToolchainInstall) { Fail "Python 3 missing and -SkipToolchainInstall was supplied" }
    Install-WithWinget "Python.Python.3.12" "Python 3.12"

    $pythonRoot = Join-Path $env:LOCALAPPDATA "Programs\Python\Python312"
    Add-UserPath $pythonRoot
    Add-UserPath (Join-Path $pythonRoot "Scripts")

    if (Resolve-Command "python") {
        & python --version *> $null
        if ($LASTEXITCODE -eq 0) { return @("python") }
    }
    if (Resolve-Command "py") {
        & py -3 --version *> $null
        if ($LASTEXITCODE -eq 0) { return @("py", "-3") }
    }
    Fail "Python 3 missing after provisioning; reopen PowerShell once and rerun"
}

function Invoke-Python([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args) {
    if ($script:Python.Count -eq 1) {
        & $script:Python[0] @Args
    } else {
        & $script:Python[0] $script:Python[1] @Args
    }
    if ($LASTEXITCODE -ne 0) { Fail "Python command failed: $($Args -join ' ')" }
}

function Ensure-FFmpeg {
    if ((Resolve-Command "ffmpeg") -and (Resolve-Command "ffprobe")) { return }
    if ($SkipToolchainInstall) { Fail "FFmpeg/ffprobe missing and -SkipToolchainInstall was supplied" }

    $ffmpegRoot = Join-Path $ToolchainDir "ffmpeg-ffprobe-static"
    New-Item -ItemType Directory -Force -Path $ffmpegRoot | Out-Null
    Write-Host "Installing FFmpeg + ffprobe user-locally (no admin)..."
    & npm install --prefix $ffmpegRoot --no-audit --no-fund $FfmpegStaticPackage
    if ($LASTEXITCODE -ne 0) { Fail "npm failed to install $FfmpegStaticPackage" }

    $bin = Join-Path $ffmpegRoot "node_modules\ffmpeg-ffprobe-static"
    if (-not (Test-Path (Join-Path $bin "ffmpeg.exe"))) { Fail "ffmpeg.exe missing after provisioning" }
    if (-not (Test-Path (Join-Path $bin "ffprobe.exe"))) { Fail "ffprobe.exe missing after provisioning" }
    Add-UserPath $bin

    if (-not (Resolve-Command "ffmpeg") -or -not (Resolve-Command "ffprobe")) {
        Fail "FFmpeg/ffprobe still missing after provisioning"
    }
}

if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
    Fail "this bootstrap is for the Windows fallback host only"
}

Write-Host "=== VelvetOS Windows Edge Fallback ==="
Write-Host "host=$HostId"

New-Item -ItemType Directory -Force -Path $StateDir, $ToolchainDir, $NpmPrefix | Out-Null
$env:HYPERFRAMES_NO_UPDATE_CHECK = "1"
$env:HYPERFRAMES_NO_AUTO_INSTALL = "1"
$env:NPM_CONFIG_PREFIX = $NpmPrefix
Add-UserPath $NpmPrefix

Ensure-Git
Ensure-Node
$script:Python = Resolve-Python
Ensure-FFmpeg

if (-not (Test-Path $Repo)) {
    Write-Host "Cloning velvetos-core..."
    & git clone https://github.com/nocturney/velvetos-core.git $Repo
    if ($LASTEXITCODE -ne 0) { Fail "git clone failed" }
}
Set-Location $Repo

& git fetch origin main
if ($LASTEXITCODE -ne 0) { Fail "git fetch origin main failed" }
& git checkout main
if ($LASTEXITCODE -ne 0) { Fail "git checkout main failed" }
& git pull --ff-only origin main
if ($LASTEXITCODE -ne 0) { Fail "git pull --ff-only origin main failed" }

if (-not $SkipHyperFramesInstall) {
    $installed = ""
    if (Resolve-Command "hyperframes") {
        try { $installed = ((& hyperframes --version 2>$null | Select-Object -First 1).Trim()).TrimStart('v') } catch {}
    }
    if ($installed -ne $HyperFramesVersion) {
        Write-Host "Installing pinned HyperFrames $HyperFramesVersion user-locally..."
        & npm install --global --no-audit --no-fund "hyperframes@$HyperFramesVersion"
        if ($LASTEXITCODE -ne 0) { Fail "HyperFrames npm install failed" }
        Add-UserPath $NpmPrefix
    }
}

if (-not (Resolve-Command "hyperframes")) { Fail "hyperframes CLI missing" }
$actual = ((& hyperframes --version | Select-Object -First 1).Trim()).TrimStart('v')
if ($actual -ne $HyperFramesVersion) {
    Fail "HyperFrames pin mismatch: expected $HyperFramesVersion, got $actual"
}

Write-Host "Ensuring HyperFrames browser runtime..."
& hyperframes browser ensure
if ($LASTEXITCODE -ne 0) { Fail "hyperframes browser ensure failed" }

Write-Host "Running VelvetOS HyperFrames doctor..."
Invoke-Python "scripts/vf_hyperframes.py" "doctor"

$SmokeRoot = Join-Path ([IO.Path]::GetTempPath()) "velvet-hyperframes-windows-smoke"
if (Test-Path $SmokeRoot) { Remove-Item -Recurse -Force $SmokeRoot }
New-Item -ItemType Directory -Force -Path (Join-Path $SmokeRoot "renders") | Out-Null

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
[IO.File]::WriteAllText((Join-Path $SmokeRoot "index.html"), $html, (New-Object Text.UTF8Encoding($false)))

$request = [ordered]@{
    jobId = "windows-host-smoke"
    backend = "hyperframes"
    projectDir = $SmokeRoot
    composition = "index.html"
    stage = "review"
    target = "review"
    format = "mp4"
    resolution = "portrait"
    fps = 30
    quality = "standard"
    output = "renders/host-smoke.mp4"
    audioRequired = $false
    strictAll = $false
}
$requestPath = Join-Path $SmokeRoot "request.json"
[IO.File]::WriteAllText($requestPath, ($request | ConvertTo-Json -Depth 5), (New-Object Text.UTF8Encoding($false)))

Write-Host "Planning Windows smoke render..."
Invoke-Python "scripts/vf_hyperframes.py" "plan" $requestPath
Write-Host "Rendering Windows smoke video..."
Invoke-Python "scripts/vf_hyperframes.py" "run" $requestPath

$receiptPath = Join-Path $SmokeRoot "renders\host-smoke.mp4.receipt.json"
if (-not (Test-Path $receiptPath)) { Fail "smoke render receipt missing" }
$receipt = Get-Content -Raw -Encoding UTF8 $receiptPath | ConvertFrom-Json
if (-not $receipt.sha256) { Fail "smoke render receipt missing sha256" }

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
$state = [ordered]@{
    schemaVersion = 2
    hostId = $HostId
    platform = "Windows"
    repo = $Repo
    repoHead = (& git rev-parse HEAD).Trim()
    hyperframesVersion = $actual
    node = (& node --version).Trim()
    ffmpeg = (& ffmpeg -version | Select-Object -First 1)
    ffprobe = (& ffprobe -version | Select-Object -First 1)
    doctor = "pass"
    renderSmoke = "pass"
    smokeReceipt = $receiptPath
    smokeReceiptSha256 = $receipt.sha256
    smokeVerifiedAt = $receipt.verifiedAt
    remoteDesktopCommander = "registration-required"
    subscriptionHost = $false
    computerUse = $false
    verifiedAt = (Get-Date).ToUniversalTime().ToString("o")
}
[IO.File]::WriteAllText($StateFile, ($state | ConvertTo-Json -Depth 5), (New-Object Text.UTF8Encoding($false)))

Write-Host "OK Windows edge prerequisites + HyperFrames doctor + real smoke render"
Write-Host "Receipt: $receiptPath"
Write-Host "State: $StateFile"
Write-Host "NEXT: connect/register this PC in Remote Desktop Commander. Once it appears online, VelvetOS may promote sderot-windows from configured_pending_device_registration to an eligible fallback host."
