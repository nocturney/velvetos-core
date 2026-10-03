[CmdletBinding()]
param(
    [string]$OpenScadPath = 'C:\Program Files\OpenSCAD (Nightly)\openscad.com',
    [string]$WorkRoot = 'D:\Velvet\Tmp\openscad-nightly-update-sentinel'
)

$ErrorActionPreference = 'Stop'

try {
    if (-not (Test-Path -LiteralPath $OpenScadPath -PathType Leaf)) {
        throw "OpenSCAD Nightly CLI missing: $OpenScadPath"
    }

    $versionRaw = ((& $OpenScadPath --version 2>&1 | Out-String).Trim())
    if ($LASTEXITCODE -ne 0) { throw "OpenSCAD --version failed: $versionRaw" }
    $versionMatch = [regex]::Match($versionRaw, '\d{4}\.\d{2}\.\d{2}')
    if (-not $versionMatch.Success) { throw "Cannot parse nightly version: $versionRaw" }
    $version = $versionMatch.Value

    if (Test-Path -LiteralPath $WorkRoot) { Remove-Item -Recurse -Force -LiteralPath $WorkRoot }
    New-Item -ItemType Directory -Force -Path $WorkRoot | Out-Null
    $scadPath = Join-Path $WorkRoot 'smoke.scad'
    $stlPath = Join-Path $WorkRoot 'smoke.stl'
    $pngPath = Join-Path $WorkRoot 'smoke.png'
    $source = 'difference(){cube([20,20,10],center=true);cylinder(h=20,r=4,center=true,$fn=48);}'
    [IO.File]::WriteAllText($scadPath, $source, (New-Object Text.UTF8Encoding($false)))

    $stlLog = (& $OpenScadPath -o $stlPath $scadPath 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $stlPath) -or (Get-Item $stlPath).Length -le 0) {
        throw "OpenSCAD STL export smoke failed: $stlLog"
    }

    $pngLog = (& $OpenScadPath -o $pngPath --imgsize=320,240 --viewall --autocenter $scadPath 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $pngPath) -or (Get-Item $pngPath).Length -le 0) {
        throw "OpenSCAD PNG render smoke failed: $pngLog"
    }

    [ordered]@{
        status = 'PASS'
        version = $version
        executable = $OpenScadPath
        executable_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $OpenScadPath).Hash
        stl = [ordered]@{ path=$stlPath; bytes=(Get-Item $stlPath).Length; sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $stlPath).Hash }
        png = [ordered]@{ path=$pngPath; bytes=(Get-Item $pngPath).Length; sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $pngPath).Hash }
        observed_at = (Get-Date).ToUniversalTime().ToString('o')
    } | ConvertTo-Json -Depth 6 -Compress
    exit 0
} catch {
    [ordered]@{
        status = 'FAIL'
        error = $_.Exception.Message
        observed_at = (Get-Date).ToUniversalTime().ToString('o')
    } | ConvertTo-Json -Depth 4 -Compress
    exit 2
}
