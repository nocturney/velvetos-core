# CrewAI E5: attended, sampled process-tree TCP/UDP evidence on Chris only.
# This is NOT a firewall and does not authorize or launch an unapproved pilot.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$PilotExecutable,
    [Parameter(Mandatory = $true)][string]$PilotArguments,
    [Parameter(Mandatory = $true)][string]$WorkingDirectory,
    [Parameter(Mandatory = $true)][string]$ValidatorPython,
    [Parameter(Mandatory = $true)][string]$ValidatorScript,
    [Parameter(Mandatory = $true)][string]$EvidencePath,
    [Parameter(Mandatory = $true)][string]$ReceiptPath,
    [ValidateRange(100, 1000)][int]$SampleIntervalMs = 250,
    [ValidateRange(1, 600)][int]$MaxSeconds = 600
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$Root = 'D:\Velvet\Pilots\OfficeV2-VerifiedTrio\'
$script:Known = @{}
$script:Child = $null
$script:CollectorErrors = New-Object 'System.Collections.Generic.List[string]'
$script:During = New-Object 'System.Collections.Generic.List[object]'
$script:Before = $null
$script:After = $null
$script:Started = $null
$script:Ended = $null
$script:TimedOut = $false

function UtcNow {
    return [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ', [Globalization.CultureInfo]::InvariantCulture)
}
function UtcBirth($processRow) {
    if ($null -eq $processRow.CreationDate) { throw 'PROCESS_BIRTH_MISSING' }
    return ([DateTime]$processRow.CreationDate).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ', [Globalization.CultureInfo]::InvariantCulture)
}
function Assert-PilotPath([string]$Path, [bool]$MustExist) {
    if (-not [IO.Path]::IsPathRooted($Path) -or $Path -notmatch '^[Dd]:\\') {
        throw 'D_ABSOLUTE_PATH_REQUIRED'
    }
    $full = [IO.Path]::GetFullPath($Path)
    if (-not $full.StartsWith($Root, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'OUT_OF_PILOT_ROOT_PATH'
    }
    if ($MustExist -and -not (Test-Path -LiteralPath $full)) { throw 'INPUT_PATH_MISSING' }
    if ((Get-Item -LiteralPath 'D:\Velvet' -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw 'REPARSE_POINT_REFUSED'
    }
    $cursor = $full
    if (-not (Test-Path -LiteralPath $cursor)) { $cursor = Split-Path -Parent $cursor }
    while ($cursor.StartsWith('D:\Velvet\', [StringComparison]::OrdinalIgnoreCase)) {
        if (-not (Test-Path -LiteralPath $cursor)) { throw 'OUTPUT_PARENT_MISSING' }
        $item = Get-Item -LiteralPath $cursor -Force -ErrorAction Stop
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'REPARSE_POINT_REFUSED'
        }
        $next = Split-Path -Parent $cursor
        if ($next -eq $cursor) { break }
        $cursor = $next
    }
    return $full
}

# Capture all OS endpoints, then restrict by the discovered pilot process tree.
# A tracked PID is only reused when its Win32_Process creation time still matches.
function Take-Snapshot {
    $processes = @(Get-CimInstance -ClassName Win32_Process -ErrorAction Stop)
    $byId = @{}
    foreach ($row in $processes) { $byId[[int]$row.ProcessId] = $row }
    $selected = @{}
    if ($null -ne $script:Child) {
        $rootId = [int]$script:Child.Id
        if ($byId.ContainsKey($rootId)) {
            $observedBirth = [DateTime]$byId[$rootId].CreationDate
            $expectedBirth = $script:Child.StartTime
            if ([Math]::Abs(($observedBirth.ToUniversalTime() - $expectedBirth.ToUniversalTime()).TotalSeconds) -gt 2) {
                throw 'ROOT_PID_BIRTH_MISMATCH'
            }
            $selected[$rootId] = $true
        }
    }
    foreach ($entry in $script:Known.GetEnumerator()) {
        $processId = [int]$entry.Key
        if ($byId.ContainsKey($processId)) {
            if ((UtcBirth $byId[$processId]) -ne $entry.Value) { throw 'TRACKED_PID_REUSED' }
            $selected[$processId] = $true
        }
    }
    $changed = $true
    while ($changed) {
        $changed = $false
        foreach ($row in $processes) {
            $processId = [int]$row.ProcessId
            if (-not $selected.ContainsKey($processId) -and $selected.ContainsKey([int]$row.ParentProcessId)) {
                $selected[$processId] = $true
                $changed = $true
            }
        }
    }
    $tree = @(
        foreach ($processId in ($selected.Keys | Sort-Object)) {
            $row = $byId[[int]$processId]
            $birth = UtcBirth $row
            if ($script:Known.ContainsKey([int]$processId) -and $script:Known[[int]$processId] -ne $birth) {
                throw 'TRACKED_PID_REUSED'
            }
            $script:Known[[int]$processId] = $birth
            @{ pid = [int]$processId; parent_pid = [int]$row.ParentProcessId; created_at_utc = $birth }
        }
    )
    $tcp = @(
        foreach ($connection in @(Get-NetTCPConnection -ErrorAction Stop)) {
            $ownerId = [int]$connection.OwningProcess
            if ($selected.ContainsKey($ownerId)) {
                @{ pid = $ownerId; state = [string]$connection.State;
                   local_address = [string]$connection.LocalAddress; local_port = [int]$connection.LocalPort;
                   remote_address = [string]$connection.RemoteAddress; remote_port = [int]$connection.RemotePort }
            }
        }
    )
    $udp = @(
        foreach ($endpoint in @(Get-NetUDPEndpoint -ErrorAction Stop)) {
            $ownerId = [int]$endpoint.OwningProcess
            if ($selected.ContainsKey($ownerId)) {
                @{ pid = $ownerId; local_address = [string]$endpoint.LocalAddress;
                   local_port = [int]$endpoint.LocalPort }
            }
        }
    )
    return @{ captured_at_utc = UtcNow; process_tree = $tree; tcp = $tcp; udp = $udp }
}

# Immediate stop on a forbidden observation; the Python verifier repeats this
# policy against every saved snapshot, including incomplete/failure cases.
function Assert-Network-Safe($snapshot) {
    foreach ($row in $snapshot.tcp) {
        if ($row.state -eq 'Listen') { throw 'TCP_LISTENER_DETECTED' }
        if ($row.remote_address -cne '127.0.0.1' -or $row.remote_port -ne 11435) {
            throw 'UNAPPROVED_TCP_REMOTE'
        }
    }
    if (@($snapshot.udp).Count -gt 0) { throw 'UDP_ENDPOINT_DETECTED' }
}
function Stop-Owned {
    foreach ($entry in $script:Known.GetEnumerator()) {
        $processId = [int]$entry.Key
        try {
            $live = Get-CimInstance -ClassName Win32_Process -Filter "ProcessId=$processId" -ErrorAction Stop
            if ($null -ne $live -and (UtcBirth $live) -eq $entry.Value) {
                Stop-Process -Id $processId -Force -ErrorAction Stop
            }
        } catch {
            $script:CollectorErrors.Add('OWNED_STOP_UNVERIFIED:' + [string]$processId)
        }
    }
}

try {
    if ($env:COMPUTERNAME -ne 'Chris') { throw 'HOST_NOT_CHRIS' }
    $exe = Assert-PilotPath $PilotExecutable $true
    $cwd = Assert-PilotPath $WorkingDirectory $true
    $python = Assert-PilotPath $ValidatorPython $true
    $validator = Assert-PilotPath $ValidatorScript $true
    $evidence = Assert-PilotPath $EvidencePath $false
    $receipt = Assert-PilotPath $ReceiptPath $false
    if ($evidence -eq $receipt) { throw 'EVIDENCE_RECEIPT_COLLISION' }
    if (-not (Test-Path -LiteralPath (Split-Path -Parent $evidence)) -or
        -not (Test-Path -LiteralPath (Split-Path -Parent $receipt))) { throw 'RECEIPT_DIRECTORY_MISSING' }
    $script:Before = Take-Snapshot
    # Equivalent to a restricted Start-Process -PassThru with no shell/profile.
    $script:Child = Start-Process -FilePath $exe -ArgumentList $PilotArguments `
        -WorkingDirectory $cwd -PassThru -NoNewWindow -ErrorAction Stop
    # Prime the native Process handle now: Windows PowerShell may otherwise
    # return a null ExitCode from a Start-Process -PassThru object.
    $null = $script:Child.Handle
    $script:Started = UtcNow
    $timer = [Diagnostics.Stopwatch]::StartNew()
    while ($true) {
        $sample = Take-Snapshot
        $script:During.Add($sample)
        Assert-Network-Safe $sample
        if ($script:Child.HasExited) { break }
        if ($timer.Elapsed.TotalSeconds -ge $MaxSeconds) {
            $script:TimedOut = $true
            throw 'MAX_RUNTIME_EXCEEDED'
        }
        Start-Sleep -Milliseconds $SampleIntervalMs
    }
} catch {
    $script:CollectorErrors.Add([string]$_.Exception.Message)
} finally {
    if ($null -ne $script:Child) {
        try {
            if (-not $script:Child.HasExited -or $script:CollectorErrors.Count -gt 0) { Stop-Owned }
            $script:Child.WaitForExit(3000) | Out-Null
        } catch { $script:CollectorErrors.Add('PROCESS_END_UNVERIFIED') }
    }
    $script:Ended = UtcNow
    try { $script:After = Take-Snapshot }
    catch { $script:CollectorErrors.Add('AFTER_SNAPSHOT_FAILED:' + [string]$_.Exception.Message) }
}

$exitCode = $null
if ($null -ne $script:Child) {
    try {
        if ($script:Child.HasExited) {
            $observedExitCode = $script:Child.ExitCode
            if ($null -ne $observedExitCode) {
                $exitCode = [int]$observedExitCode
            } else {
                $script:CollectorErrors.Add('PILOT_EXIT_CODE_UNKNOWN')
            }
        } else {
            $script:CollectorErrors.Add('PILOT_EXIT_NOT_OBSERVED')
        }
    } catch {
        $script:CollectorErrors.Add('PILOT_EXIT_CODE_UNAVAILABLE')
    }
}
$raw = @{
    schema = 'velvetos.office-v2.crewai-e5-snapshots.v1'
    host = 'Chris'
    root_pid = $(if ($null -eq $script:Child) { $null } else { [int]$script:Child.Id })
    started_at_utc = $script:Started
    ended_at_utc = $script:Ended
    sample_interval_ms = $SampleIntervalMs
    collector_complete = ($script:CollectorErrors.Count -eq 0)
    collector_errors = @($script:CollectorErrors.ToArray())
    timed_out = $script:TimedOut
    exit_code = $exitCode
    snapshots = @{ before = $script:Before; during = @($script:During.ToArray()); after = $script:After }
}
try {
    if (-not $evidence -or -not $receipt -or -not $python -or -not $validator) { throw 'OUTPUT_PATH_NOT_ADMITTED' }
    $json = $raw | ConvertTo-Json -Depth 12
    [IO.File]::WriteAllText($evidence, $json + "`n", ([Text.UTF8Encoding]::new($false)))
    & $python $validator --evidence $evidence --receipt $receipt
    if ($LASTEXITCODE -ne 0) { exit 1 }
    exit 0
} catch {
    Write-Error ('FAIL E5: ' + [string]$_.Exception.Message)
    exit 2
}
