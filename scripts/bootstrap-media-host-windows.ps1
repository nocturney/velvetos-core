param(
    [switch]$StartWorker,
    [switch]$SkipVoiceStudioInstall,
    [switch]$SkipHyperFramesInstall,
    [switch]$SkipToolchainInstall
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== VelvetOS canonical Windows media fallback ==="
Write-Host "This wrapper commissions the existing sderot-windows Edge host for HyperFrames + VoiceStudio."

$edgeArgs = @()
if ($SkipHyperFramesInstall) { $edgeArgs += "-SkipHyperFramesInstall" }
if ($SkipToolchainInstall) { $edgeArgs += "-SkipToolchainInstall" }
& (Join-Path $PSScriptRoot "bootstrap-edge-host-windows.ps1") @edgeArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$speechArgs = @()
if ($SkipVoiceStudioInstall) { $speechArgs += "-SkipVoiceStudioInstall" }
& (Join-Path $PSScriptRoot "bootstrap-speech-host-windows.ps1") @speechArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($StartWorker) {
    Write-Host "NOTE: -StartWorker is accepted for compatibility, but sderot-windows uses the existing Remote Desktop Commander route rather than a second Cursor worker."
}

Write-Host "OK Windows media fallback commissioned locally."
Write-Host "NEXT gate: the physical Windows PC must appear online in Remote Desktop Commander before registry promotion to host_smoke_verified."
