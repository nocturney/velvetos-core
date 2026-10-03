param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('coreldraw','corel-designer')]
    [string]$AppId
)

$ErrorActionPreference='Stop'
$Adapter='D:\Velvet\Runtime\CreativeTools\Corel\CorelTechnicalSafeAdapter.py'
$Python='C:\Python314\python.exe'
$ports=@{'coreldraw'=6771;'corel-designer'=6772}
$port=$ports[$AppId]
$listener=Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue |
    Where-Object {$_.LocalAddress -eq '127.0.0.1'} | Select-Object -First 1
if(-not $listener){
    [pscustomobject]@{status='PASS';app=$AppId;sidecar='not_running'}|ConvertTo-Json -Compress
    exit 0
}

$raw=& $Python $Adapter shutdown --app $AppId
$code=$LASTEXITCODE
if(-not $raw){throw "Corel shutdown returned no result for $AppId"}
$result=$raw|ConvertFrom-Json
if($code -ne 0 -or $result.status -ne 'PASS'){
    throw ("Corel safe shutdown failed for {0}: {1}" -f $AppId,$result.error)
}
$deadline=(Get-Date).AddSeconds(20)
do{
    $listener=Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue |
        Where-Object {$_.LocalAddress -eq '127.0.0.1'} | Select-Object -First 1
    if(-not $listener){break}
    Start-Sleep -Milliseconds 250
}while((Get-Date)-lt $deadline)
if($listener){throw "Corel sidecar did not stop for $AppId"}
$result|ConvertTo-Json -Depth 5 -Compress
