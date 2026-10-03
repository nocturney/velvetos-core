param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('coreldraw','corel-designer')]
    [string]$AppId
)

$ErrorActionPreference='Stop'
$Adapter='D:\Velvet\Runtime\CreativeTools\Corel\CorelTechnicalSafeAdapter.py'
$Python='C:\Python314\python.exe'
$cfg=@{
    'coreldraw'=@{port=6771;process='CorelDRW'}
    'corel-designer'=@{port=6772;process='Designer'}
}
$c=$cfg[$AppId]
if(-not (Test-Path -LiteralPath $Adapter)){throw "Corel safe adapter missing: $Adapter"}
if(-not (Test-Path -LiteralPath $Python)){throw "Python missing: $Python"}
$session=(Get-Process -Id $PID).SessionId
if($session -eq 0){throw 'Corel host wrapper must run in an interactive user session'}

$listener=Get-NetTCPConnection -State Listen -LocalPort $c.port -ErrorAction SilentlyContinue |
    Where-Object {$_.LocalAddress -eq '127.0.0.1'} | Select-Object -First 1
if($listener){
    throw "Corel safe adapter is already listening on 127.0.0.1:$($c.port)"
}

$before=@(Get-Process -Name $c.process -ErrorAction SilentlyContinue |
    Where-Object {$_.SessionId -eq $session})
if($before.Count -gt 0){
    throw "Refusing agent launch because a pre-existing user Corel process is already running for $AppId"
}

# Run synchronously so Task Scheduler owns the full lifecycle.
# The scheduled task itself is hidden; the adapter launches Corel with Visible=false.
& $Python $Adapter serve --app $AppId
$code=$LASTEXITCODE
if($code -ne 0){throw "Corel safe adapter exited with code $code for $AppId"}
