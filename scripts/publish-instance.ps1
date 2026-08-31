# Publish VelvetOS instance scaffold to GitHub (Windows PowerShell).
# Usage: .\scripts\publish-instance.ps1 -InstanceId velvet-factory -RemoteSlug nocturney/velvetos-velvet-factory
# Requires: git, empty GitHub repo already created under your account.
param(
    [Parameter(Mandatory = $true)][string]$InstanceId,
    [Parameter(Mandatory = $true)][string]$RemoteSlug,
    [switch]$Push
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Src = Join-Path $Root "instances\$InstanceId"
if (-not (Test-Path $Src)) {
    Write-Error "Missing scaffold: $Src"
}

$Tmp = Join-Path $env:TEMP ("velvetos-publish-" + [guid]::NewGuid().ToString("n"))
New-Item -ItemType Directory -Path $Tmp | Out-Null
try {
    Copy-Item -Path (Join-Path $Src "*") -Destination $Tmp -Recurse -Force
    if (Test-Path (Join-Path $Src ".cursor")) {
        Copy-Item -Path (Join-Path $Src ".cursor") -Destination (Join-Path $Tmp ".cursor") -Recurse -Force
    }
    if (Test-Path (Join-Path $Src ".gitignore")) {
        Copy-Item -Path (Join-Path $Src ".gitignore") -Destination $Tmp -Force
    }

    Push-Location $Tmp
    git init -b main
    git add -A
    git commit -m "VelvetOS instance scaffold: $InstanceId"
    git remote add origin "https://github.com/$RemoteSlug.git"

    Write-Host "Ready at: $Tmp"
    Write-Host "  git push -u origin main"
    if ($Push) {
        git push -u origin main
        Write-Host "OK published $RemoteSlug"
    } else {
        Write-Host "Re-run with -Push when logged in as repo owner (PAT as password)."
    }
} finally {
    Pop-Location
}
