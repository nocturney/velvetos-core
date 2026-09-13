param(
    [switch]$SkipHyperFramesInstall
)

$ErrorActionPreference = "Stop"
$HostId = "sderot-windows"
$Repo = Join-Path $env:USERPROFILE "velvetos-core"
$StateDir = Join-Path $env:USERPROFILE ".velvetos"
$StateFile = Join-Path $StateDir "edge-host.json"
$HyperFramesVersion = "0.8.34"

function Require-Command([string]$Name) {
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $cmd) { throw "Missing required command: $Name" }
    return $cmd.Source
}

Write-Host "=== VelvetOS Windows Edge Fallback ==="
Write-Host "host=$HostId"

Require-Command git | Out-Null
Require-Command python | Out-Null
Require-Command node | Out-Null
Require-Command npm | Out-Null
Require-Command ffmpeg | Out-Null
Require-Command ffprobe | Out-Null

if (-not (Test-Path $Repo)) {
    git clone https://github.com/nocturney/velvetos-core.git $Repo
}
Set-Location $Repo

git fetch origin main
git checkout main
git pull --ff-only origin main

$nodeMajor = [int]((node --version).TrimStart('v').Split('.')[0])
if ($nodeMajor -lt 22) { throw "Node >=22 required; found $(node --version)" }

if (-not $SkipHyperFramesInstall) {
    $installed = $null
    try { $installed = (hyperframes --version 2>$null).Trim() } catch {}
    if ($installed -ne $HyperFramesVersion) {
        npm install --global "hyperframes@$HyperFramesVersion"
    }
}

$actual = (hyperframes --version).Trim()
if ($actual -ne $HyperFramesVersion) {
    throw "HyperFrames pin mismatch: expected $HyperFramesVersion, got $actual"
}

python scripts/vf_hyperframes.py doctor

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
$state = [ordered]@{
    hostId = $HostId
    platform = "Windows"
    repo = $Repo
    repoHead = (git rev-parse HEAD).Trim()
    hyperframesVersion = $actual
    ffmpeg = (ffmpeg -version | Select-Object -First 1)
    ffprobe = (ffprobe -version | Select-Object -First 1)
    doctor = "pass"
    remoteDesktopCommander = "registration-required"
    subscriptionHost = $false
    computerUse = $false
    verifiedAt = (Get-Date).ToString("o")
}
$state | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 $StateFile

Write-Host "OK Windows edge prerequisites + HyperFrames doctor"
Write-Host "State: $StateFile"
Write-Host "NEXT: connect this PC to Remote Desktop Commander; once it appears online as a device, VelvetOS may route fallback work here."
