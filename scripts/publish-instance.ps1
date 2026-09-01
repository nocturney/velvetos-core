# Publish VelvetOS instance scaffold to GitHub (Windows PowerShell).
# Usage: .\scripts\publish-instance.ps1 -InstanceId velvet-factory -RemoteSlug nocturney/velvetos-velvet-factory -Push
# Requires: git, GitHub repo already created under your account.
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
if (-not (Test-Path (Join-Path $Src ".cursor\environment.json"))) {
    Write-Error "Missing $($Src)\.cursor\environment.json"
}

function Copy-ScaffoldOverlay {
    param([string]$Dest)
    Get-ChildItem -Path $Src -Force | Where-Object { $_.Name -ne ".git" } | ForEach-Object {
        $target = Join-Path $Dest $_.Name
        if ($_.PSIsContainer) {
            Copy-Item -Path $_.FullName -Destination $target -Recurse -Force
        } else {
            Copy-Item -Path $_.FullName -Destination $target -Force
        }
    }
}

$RemoteUrl = "https://github.com/$RemoteSlug.git"
$Tmp = Join-Path $env:TEMP ("velvetos-publish-" + [guid]::NewGuid().ToString("n"))
New-Item -ItemType Directory -Path $Tmp | Out-Null

try {
    $hasMain = $false
    git ls-remote --exit-code $RemoteUrl refs/heads/main 2>$null
    if ($LASTEXITCODE -eq 0) { $hasMain = $true }

    if ($hasMain) {
        Write-Host "Remote has main — clone + overlay scaffold"
        git clone $RemoteUrl $Tmp
        Copy-ScaffoldOverlay -Dest $Tmp
    } else {
        Write-Host "Remote empty — init from scaffold"
        Copy-ScaffoldOverlay -Dest $Tmp
        Push-Location $Tmp
        git init -b main
        Pop-Location
    }

    Push-Location $Tmp
    git add -A
    git diff --staged --quiet
    if ($LASTEXITCODE -ne 0) {
        git commit -m "VelvetOS instance scaffold: $InstanceId"
    } else {
        Write-Host "OK scaffold already matches remote — nothing to commit"
    }

    Write-Host "Remote: $RemoteUrl"
    Write-Host "Working tree: $Tmp"
    if ($Push) {
        git push -u origin main
        Write-Host "OK published $RemoteSlug"
    } else {
        Write-Host "Re-run with -Push when logged in as repo owner."
    }
} finally {
    if ((Get-Location).Path -eq $Tmp) { Pop-Location }
}
