[CmdletBinding()]
param(
    [string]$OpenScadPath = 'C:\Program Files\OpenSCAD (Nightly)\openscad.com',
    [string]$StateRoot = 'D:\Velvet\State\OpenSCAD-Nightly-Update-Watch',
    [string]$SourceUrl = 'https://files.openscad.org/snapshots/'
)

$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $StateRoot | Out-Null
$statePath = Join-Path $StateRoot 'latest.json'

$result = [ordered]@{
    schema = 'velvetos.openscad-nightly.update-watch.v1'
    observed_at = (Get-Date).ToUniversalTime().ToString('o')
    source = $SourceUrl
    auto_update = $false
    installed = $null
    latest = $null
    status = 'CHECK_FAILED'
    error = $null
}

try {
    if (-not (Test-Path -LiteralPath $OpenScadPath -PathType Leaf)) {
        throw "OpenSCAD Nightly CLI missing: $OpenScadPath"
    }
    $installedRaw = ((& $OpenScadPath --version 2>&1 | Out-String).Trim())
    if ($LASTEXITCODE -ne 0) { throw "OpenSCAD --version failed: $installedRaw" }
    $installedMatch = [regex]::Match($installedRaw, '\d{4}\.\d{2}\.\d{2}')
    if (-not $installedMatch.Success) { throw "Cannot parse installed version: $installedRaw" }
    $result.installed = $installedMatch.Value

    $html = (Invoke-WebRequest -UseBasicParsing -Uri $SourceUrl -TimeoutSec 20).Content
    $matches = [regex]::Matches($html, 'OpenSCAD-(\d{4}\.\d{2}\.\d{2})-x86-64-Installer\.exe')
    $versions = @($matches | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
    if ($versions.Count -eq 0) { throw 'No nightly snapshot versions found on official downloads page' }
    $result.latest = @($versions | Sort-Object -Descending)[0]

    $installedDate = [datetime]::ParseExact($result.installed, 'yyyy.MM.dd', [Globalization.CultureInfo]::InvariantCulture)
    $latestDate = [datetime]::ParseExact($result.latest, 'yyyy.MM.dd', [Globalization.CultureInfo]::InvariantCulture)
    if ($installedDate -lt $latestDate) { $result.status = 'UPDATE_AVAILABLE' }
    elseif ($installedDate -eq $latestDate) { $result.status = 'CURRENT' }
    else { $result.status = 'AHEAD_OF_PUBLISHED_SNAPSHOT' }
} catch {
    $result.error = $_.Exception.Message
}

$tmp = "$statePath.tmp.$PID"
$result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $tmp -Encoding UTF8
Move-Item -Force -LiteralPath $tmp -Destination $statePath
$result | ConvertTo-Json -Depth 6 -Compress
