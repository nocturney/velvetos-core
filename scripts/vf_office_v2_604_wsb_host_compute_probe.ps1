#requires -Version 5.1
<#
#604 READ-ONLY, PUBLIC-ONLY Windows Host Compute event probe.
NEVER launches/stops a VM, changes OS settings, reads guest output, touches
secrets, or claims independent attestation. Always exits 2, even on success.
Use ONLY within the authorized Chris host with the pinned public WSB input.
The event stream can contain OTHER users'/LABs' VMs; do not publish raw messages.
#>
[CmdletBinding()]
param(
    [ValidateRange(1, 180)]
    [int] $LookbackMinutes = 180
)

$ErrorActionPreference = 'Stop'
$Schema = 'velvetos.office-v2.p0-604-wsb-host-compute-metadata.v0'
$Root = 'D:\Velvet\Pilots\OfficeAccelerator\AgentEnvelopeLab\p0-604-wsb-attended-smoke-20261011-a1'
$ExpectedConfigHash = '781c82ac2f426196c847ba32e0da9170985c7877953f144ddc992623200411ff'
$ExpectedScriptHash = 'f216aa189f54900b4ba412508de69193d591a648611e1d862da1d067f22eb056'
$Channel = 'Microsoft-Windows-Hyper-V-Compute-Operational'
$ExpectedCommand = 'C:\vf-public-input\run-public-smoke.ps1'
$ExpectedCommandJson = 'C:\\vf-public-input\\run-public-smoke.ps1'

try {
    $CfgPath = Join-Path $Root 'sandbox-smoke.wsb'
    $SrcPath = Join-Path $Root 'public-input\run-public-smoke.ps1'
    $OutPath = Join-Path $Root 'public-output'
    if (-not (Test-Path -LiteralPath $OutPath -PathType Container)) {
        throw 'ORIGINAL_PUBLIC_OUTPUT_FOLDER_MISSING'
    }
    if ((Get-FileHash -LiteralPath $CfgPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $ExpectedConfigHash) {
        throw 'EXPECTED_ORIGINAL_WSB_CONFIG_SHA_DRIFT'
    }
    if ((Get-FileHash -LiteralPath $SrcPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $ExpectedScriptHash) {
        throw 'EXPECTED_PUBLIC_GUEST_SOURCE_SHA_DRIFT'
    }
    $OutputCount = @(Get-ChildItem -LiteralPath $OutPath -Force).Count
    $End = [DateTime]::UtcNow
    $Start = $End.AddMinutes(-$LookbackMinutes)
    $Raw = @(Get-WinEvent -FilterHashtable @{
        LogName = $Channel
        Id = @(2014, 2500, 2007)
        StartTime = $Start
        EndTime = $End
    } -MaxEvents 400 -ErrorAction Stop)

    $Safe = @(
        foreach ($Evt in $Raw) {
            $Message = [string] $Evt.Message
            $Found = [regex]::Match($Message, '\[([0-9A-Fa-f-]{36})\]')
            if (-not $Found.Success) { continue }
            $Uuid = $Found.Groups[1].Value.ToLowerInvariant()
            $MatchCommand = $Evt.Id -eq 2500 -and (
                $Message.IndexOf($ExpectedCommand, [StringComparison]::OrdinalIgnoreCase) -ge 0 -or
                $Message.IndexOf($ExpectedCommandJson, [StringComparison]::OrdinalIgnoreCase) -ge 0
            )
            $MatchMemory = $Evt.Id -eq 2007 -and (
                $Message.IndexOf('"SizeInMB":2048', [StringComparison]::OrdinalIgnoreCase) -ge 0
            )
            [ordered]@{
                event_id = [int] $Evt.Id
                record_id = [int64] $Evt.RecordId
                time_utc = $Evt.TimeCreated.ToUniversalTime().ToString('o')
                compute_id = $Uuid
                exact_public_logon_command_observed = [bool] $MatchCommand
                expected_2048mb_change_observed = [bool] $MatchMemory
            }
        }
    )
    [ordered]@{
        schema = $Schema
        status = 'UNTRUSTED_READ_ONLY_HOST_COMPUTE_METADATA'
        source_host = 'Chris'
        event_channel = $Channel
        config_sha256 = $ExpectedConfigHash
        guest_script_sha256 = $ExpectedScriptHash
        window_start_utc = $Start.ToString('o')
        window_end_utc = $End.ToString('o')
        records_limit_reached = ($Raw.Count -ge 400)
        original_public_output_count = $OutputCount
        host_event_count = $Safe.Count
        events = $Safe
        current_host_user = [Security.Principal.WindowsIdentity]::GetCurrent().Name
        attended_guest_launched_by_this_probe = $false
        independent_event_attestation = $false
        production_authority = $false
    } | ConvertTo-Json -Depth 8 -Compress
    exit 2
}
catch {
    [ordered]@{
        schema = $Schema
        status = 'FAIL_CLOSED_HOST_COMPUTE_LOG_READ'
        reason = ([string] $_.Exception.Message).Substring(
            0, [Math]::Min(160, ([string] $_.Exception.Message).Length)
        )
        independent_event_attestation = $false
        production_authority = $false
    } | ConvertTo-Json -Compress
    exit 2
}
