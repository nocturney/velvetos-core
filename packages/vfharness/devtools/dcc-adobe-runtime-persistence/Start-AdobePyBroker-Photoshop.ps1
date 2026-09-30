$ErrorActionPreference = 'Stop'
$TokenPath = 'D:\Velvet\State\AdobeBridge\photoshop\broker.token'
$Exe = 'D:\Velvet\Tools\AdobePy\0.6.2\adobepy-0.6.2-windows-x64\bin\adobepy.exe'
$LogDir = 'D:\Velvet\Logs\AdobeBridge'
$LogPath = Join-Path $LogDir 'adobepy-photoshop-broker.log'
$Stdout = Join-Path $LogDir 'adobepy-photoshop-broker.stdout.log'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
if (-not (Test-Path $TokenPath) -or -not (Test-Path $Exe)) { exit 2 }

while ($true) {
    $env:ADOBEPY_TOKEN = [IO.File]::ReadAllText($TokenPath).Trim()
    Add-Content -Path $LogPath -Value ('{0:o} START photoshop broker 0.6.2 127.0.0.1:47393 user={1}' -f (Get-Date), [Security.Principal.WindowsIdentity]::GetCurrent().Name) -Encoding UTF8
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & $Exe broker --bind 127.0.0.1:47393 1>> $Stdout 2> $null
    $code = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorAction
    Add-Content -Path $LogPath -Value ('{0:o} EXIT code={1}; restart in 2s' -f (Get-Date), $code) -Encoding UTF8
    Start-Sleep -Seconds 2
}