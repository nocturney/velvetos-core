#requires -Version 5.1
# E5 observation only. This is NOT continuous enforcement.
param(
    [Parameter(Mandatory=$true)][int]$PilotPid,
    [Parameter(Mandatory=$true)][string]$ReceiptDirectory,
    [int]$DuringSeconds = 10,
    [int]$IntervalMilliseconds = 250
)
$ErrorActionPreference = 'Stop'
$root = 'D:\Velvet\'
if (-not $ReceiptDirectory.StartsWith($root,[StringComparison]::OrdinalIgnoreCase)) { throw 'D_ONLY_REQUIRED' }
if ($DuringSeconds -lt 1 -or $IntervalMilliseconds -lt 50) { throw 'INVALID_INTERVAL' }
[IO.Directory]::CreateDirectory($ReceiptDirectory) | Out-Null
function Tree-Pids([int]$rootPid) {
    $all = @(Get-CimInstance Win32_Process -ErrorAction Stop)
    $found = [System.Collections.Generic.HashSet[int]]::new()
    [void]$found.Add($rootPid)
    do {
        $old = $found.Count
        foreach ($p in $all) {
            if ($found.Contains([int]$p.ParentProcessId)) { [void]$found.Add([int]$p.ProcessId) }
        }
    } while ($old -ne $found.Count)
    return @($found | Sort-Object)
}
function Snapshot([string]$phase) {
    $now = [DateTime]::UtcNow.ToString('o')
    $ids = @(Tree-Pids $PilotPid)
    $tcp = @(Get-NetTCPConnection -ErrorAction Stop | Where-Object { $ids -contains [int]$_.OwningProcess } | ForEach-Object {
        @{pid=[int]$_.OwningProcess;state=[string]$_.State;local_address=[string]$_.LocalAddress;local_port=[int]$_.LocalPort;remote_address=[string]$_.RemoteAddress;remote_port=[int]$_.RemotePort}
    })
    $udp = @(Get-NetUDPEndpoint -ErrorAction Stop | Where-Object { $ids -contains [int]$_.OwningProcess } | ForEach-Object {
        @{pid=[int]$_.OwningProcess;local_address=[string]$_.LocalAddress;local_port=[int]$_.LocalPort}
    })
    return @{phase=$phase;utc=$now;ok=$true;pids=$ids;tcp=$tcp;udp=$udp}
}
$started = [DateTime]::UtcNow.ToString('o')
$snapshots = @{}
$errors = @()
try {
    $snapshots.before = Snapshot 'before'
    $deadline = [DateTime]::UtcNow.AddSeconds($DuringSeconds)
    $samples = @()
    do {
        $samples += ,(Snapshot 'during')
        Start-Sleep -Milliseconds $IntervalMilliseconds
    } while ([DateTime]::UtcNow -lt $deadline)
    $snapshots.during = @{ok=$true;pids=@($samples | ForEach-Object { $_.pids } | Sort-Object -Unique);tcp=@($samples | ForEach-Object { $_.tcp });udp=@($samples | ForEach-Object { $_.udp });utc=[DateTime]::UtcNow.ToString('o');sample_count=$samples.Count}
    $snapshots.after = Snapshot 'after'
} catch { $errors += $_.Exception.Message }
$body = @{schema='e5-network-v1';started_utc=$started;ended_utc=[DateTime]::UtcNow.ToString('o');pilot_pid=$PilotPid;snapshots=$snapshots;errors=$errors;sampling_only=$true;monitor_complete=($errors.Count -eq 0);process_tree_complete=$false;enforcement_proven=$false;verdict='FAIL_CLOSED_OBSERVATION_ONLY'}
$json = ConvertTo-Json -InputObject $body -Depth 20
$path = Join-Path $ReceiptDirectory 'e5-network-observation.json'
[IO.File]::WriteAllText($path,$json+"\n",[Text.UTF8Encoding]::new($false))
$hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
$index = @{receipt_file=$path;sha256=$hash;hash_algorithm='sha256';utc=[DateTime]::UtcNow.ToString('o');verdict='FAIL_CLOSED_OBSERVATION_ONLY'}
[IO.File]::WriteAllText((Join-Path $ReceiptDirectory 'e5-network-hash.json'),(ConvertTo-Json -InputObject $index -Compress)+"\n",[Text.UTF8Encoding]::new($false))
Write-Output $path
exit 1
