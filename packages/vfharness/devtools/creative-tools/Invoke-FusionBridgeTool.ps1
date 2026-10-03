[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ToolName,
    [string]$ArgumentsJson = '{}',
    [int]$TimeoutSeconds = 20
)

$ErrorActionPreference = 'Stop'
$TokenPath = 'D:\Velvet\State\CreativeTools\Fusion\token.txt'
$Endpoint = 'http://127.0.0.1:49110/'

if (-not (Test-Path -LiteralPath $TokenPath)) {
    throw 'Fusion bridge token file is missing.'
}

$token = (Get-Content -Raw -LiteralPath $TokenPath).Trim()
$argsObject = $ArgumentsJson | ConvertFrom-Json

$payload = [ordered]@{
    jsonrpc = '2.0'
    id = 1
    method = 'tools/call'
    params = @{
        name = $ToolName
        arguments = $argsObject
    }
}

Invoke-RestMethod -Method Post -Uri $Endpoint -Headers @{
    Authorization = ('Bearer ' + $token)
} -ContentType 'application/json' -Body ($payload | ConvertTo-Json -Depth 20 -Compress) -TimeoutSec $TimeoutSeconds |
    ConvertTo-Json -Depth 20
