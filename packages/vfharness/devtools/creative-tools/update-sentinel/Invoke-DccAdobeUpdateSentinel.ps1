[CmdletBinding()]
param(
    [ValidateSet('scan','status','probe','seed')]
    [string]$Action = 'scan',
    [string]$AppId,
    [switch]$ConfirmKnownGood,
    [string]$ConfigPath,
    [string]$StateRoot,
    [string]$LogRoot
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($ConfigPath)) {
    $scriptDir = $PSScriptRoot
    if ([string]::IsNullOrWhiteSpace($scriptDir) -and $PSCommandPath) { $scriptDir = Split-Path -Parent $PSCommandPath }
    if ([string]::IsNullOrWhiteSpace($scriptDir) -and $MyInvocation.MyCommand.Path) { $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
    if ([string]::IsNullOrWhiteSpace($scriptDir)) { throw 'Unable to resolve UpdateSentinel script directory; provide -ConfigPath explicitly.' }
    $ConfigPath = Join-Path $scriptDir 'dcc-adobe-update-sentinel.json'
}
$Config = Get-Content -Raw -LiteralPath $ConfigPath | ConvertFrom-Json
if (-not $StateRoot) { $StateRoot = $Config.paths.state_root }
if (-not $LogRoot) { $LogRoot = $Config.paths.log_root }
$BaselinePath = Join-Path $StateRoot 'accepted-baseline.json'
$InventoryPath = Join-Path $StateRoot 'last-inventory.json'
$RoutingPath = Join-Path $StateRoot 'routing-state.json'
$NotificationDir = Join-Path $StateRoot 'notification-state'
$NotificationLog = Join-Path $LogRoot 'notifications.jsonl'
$ReceiptDir = Join-Path $LogRoot 'receipts'

function Ensure-Directories {
    foreach ($path in @($StateRoot,$LogRoot,$NotificationDir,$ReceiptDir)) {
        New-Item -ItemType Directory -Force -Path $path | Out-Null
    }
}

function Write-JsonAtomic([string]$Path, $Value) {
    $tmp = "$Path.tmp.$PID"
    $Value | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $tmp -Encoding UTF8
    Move-Item -Force -LiteralPath $tmp -Destination $Path
}

function Get-StringHash([string]$Text) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [Text.Encoding]::UTF8.GetBytes($Text)
        return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','')
    } finally { $sha.Dispose() }
}

function Get-FileMarker([string]$Path, [switch]$Hash) {
    if (-not $Path -or -not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return [ordered]@{ exists=$false; path=$Path }
    }
    $item = Get-Item -LiteralPath $Path
    $vi = $item.VersionInfo
    $m = [ordered]@{
        exists = $true
        path = $item.FullName
        product_version = [string]$vi.ProductVersion
        file_version = [string]$vi.FileVersion
        length = [int64]$item.Length
        last_write_utc = $item.LastWriteTimeUtc.ToString('o')
    }
    if ($Hash) { $m.sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash }
    return $m
}

function Resolve-Shortcut([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return [ordered]@{ exists=$false; path=$Path; target=$null; arguments=$null }
    }
    if ([IO.Path]::GetExtension($Path) -ine '.lnk') {
        return [ordered]@{ exists=$true; path=$Path; target=$Path; arguments=$null }
    }
    $wsh = New-Object -ComObject WScript.Shell
    $sc = $wsh.CreateShortcut($Path)
    return [ordered]@{ exists=$true; path=$Path; target=$sc.TargetPath; arguments=$sc.Arguments }
}

function Find-ShortcutCandidates([string]$ExeName) {
    if (-not $ExeName) { return @() }
    $roots = @(
        "$env:ProgramData\Microsoft\Windows\Start Menu\Programs",
        "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
    )
    $rows = @()
    $wsh = New-Object -ComObject WScript.Shell
    foreach ($root in $roots) {
        foreach ($lnk in @(Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.lnk' -ErrorAction SilentlyContinue)) {
            try {
                $sc = $wsh.CreateShortcut($lnk.FullName)
                if ([IO.Path]::GetFileName($sc.TargetPath) -ieq $ExeName) {
                    $rows += [ordered]@{ path=$lnk.FullName; target=$sc.TargetPath; arguments=$sc.Arguments }
                }
            } catch {}
        }
    }
    return @($rows)
}

function Get-AdapterMarker($HostConfig) {
    if (-not $HostConfig.adapter_version) { return $null }
    $v = [string]$HostConfig.adapter_version
    $dir = $null
    switch ([string]$HostConfig.id) {
        'maya' { $dir = "D:\Velvet\Tools\DCC-MCP\maya-$v" }
        '3dsmax' { $dir = "D:\Velvet\Tools\DCC-MCP\3dsmax-$v" }
        'blender' { $dir = "D:\Velvet\Tools\DCC-MCP\blender-$v" }
        'zbrush' { $dir = "D:\Velvet\Tools\DCC-MCP\zbrush-$v" }
        'substance-painter' { $dir = "D:\Velvet\Tools\DCC-MCP\substance-painter-$v" }
        'substance-designer' { $dir = "D:\Velvet\Tools\DCC-MCP\substance-designer-$v" }
        'illustrator' { $dir = "D:\Velvet\Tools\DCC-MCP\illustrator-$v" }
        'aftereffects' { $dir = "D:\Velvet\Tools\DCC-MCP\aftereffects-$v" }
        'meshmixer' { $dir = "D:\Velvet\Tools\CreativeTools\Meshmixer\adapter-$v" }
    }
    if ($HostConfig.probe.kind -eq 'stdio') {
        return [ordered]@{ version=$v; server=(Get-FileMarker ([string]$HostConfig.probe.server)) }
    }
    if (-not $dir) { return [ordered]@{ version=$v } }
    $marker = [ordered]@{ version=$v; path=$dir; exists=(Test-Path -LiteralPath $dir -PathType Container) }
    if ($marker.exists -and $HostConfig.id -eq 'meshmixer') {
        $marker.executable = Get-FileMarker (Join-Path $dir 'VelvetMeshmixerAdapter.exe') -Hash
        $marker.mmapi_csharp = Get-FileMarker (Join-Path $dir 'mmapi_csharp.dll') -Hash
        $marker.mmapi_native = Get-FileMarker (Join-Path $dir 'mmapi.dll') -Hash
    }
    if ($marker.exists) {
        $metadata = Get-ChildItem -LiteralPath (Join-Path $dir 'venv\Lib\site-packages') -Recurse -File -Filter 'METADATA' -ErrorAction SilentlyContinue |
            Where-Object { $_.Directory.Name -match 'dcc_mcp.*dist-info' } | Sort-Object FullName | Select-Object -First 1
        if ($metadata) { $marker.metadata_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $metadata.FullName).Hash }
    }
    return $marker
}

function Get-PluginMarker($HostConfig) {
    if (-not $HostConfig.runtime_plugin_dir) { return $null }
    $dir = [string]$HostConfig.runtime_plugin_dir
    $m = [ordered]@{ path=$dir; exists=(Test-Path -LiteralPath $dir -PathType Container); bridge_version=[string]$HostConfig.bridge_version }
    if ($m.exists) {
        $pluginFiles = $(if ($HostConfig.plugin_files) { @($HostConfig.plugin_files) } else { @('manifest.json','main.js','index.html') })
        foreach ($name in $pluginFiles) {
            $f = Join-Path $dir ([string]$name)
            if (Test-Path -LiteralPath $f -PathType Leaf) {
                $key = ([string]$name).Replace('\','/')
                $m[$key] = (Get-FileHash -Algorithm SHA256 -LiteralPath $f).Hash
            }
        }
    }
    return $m
}

function Get-SharedInventory {
    $rows = [ordered]@{}
    foreach ($c in @($Config.shared_components)) {
        if ($c.kind -eq 'dcc_registry_gateway') {
            $entry = $null
            if (Test-Path -LiteralPath $Config.paths.dcc_registry) {
                $servicesRaw = Get-Content -Raw -LiteralPath $Config.paths.dcc_registry | ConvertFrom-Json
                $services = @($servicesRaw)
                $entry = $services | Where-Object { $_.dcc_type -eq '__gateway__' -and $_.status -eq 'available' } | Select-Object -First 1
            }
            $rows[$c.id] = [ordered]@{
                kind='dcc_registry_gateway'
                available=[bool]$entry
                version=$(if($entry){[string]$entry.version}else{$null})
                process_exe=$(if($entry){[string]$entry.metadata.gateway_process_exe}else{$null})
            }
        } elseif ($c.kind -eq 'loopback_listener_process') {
            $conn = Get-NetTCPConnection -State Listen -LocalPort ([int]$c.port) -ErrorAction SilentlyContinue |
                Where-Object { $_.LocalAddress -in @('127.0.0.1','::1') } | Select-Object -First 1
            $exe = $null
            if ($conn) {
                try { $exe = (Get-CimInstance Win32_Process -Filter "ProcessId=$($conn.OwningProcess)").ExecutablePath } catch {}
            }
            $rows[$c.id] = [ordered]@{
                kind='loopback_listener_process'
                port=[int]$c.port
                listening=[bool]$conn
                executable=(Get-FileMarker $exe)
            }
        }
    }
    return $rows
}

function Get-SharedDependencies([string]$Id) {
    if ($Id -in @('maya','3dsmax','blender','zbrush','substance-painter','substance-designer')) { return @('dcc-core') }
    if ($Id -eq 'illustrator') { return @() } # production surface is resident bounded COM; CEP broker is non-authoritative
    if ($Id -in @('aftereffects','premiere')) { return @('adobepy-aftereffects-premiere') }
    if ($Id -eq 'photoshop') { return @('adobepy-photoshop') }
    return @()
}

function Get-HostInventory($HostConfig, $RuntimeManifest, $Shared) {
    $app = $RuntimeManifest.apps | Where-Object { $_.id -eq $HostConfig.id } | Select-Object -First 1
    $shortcut = $(if ($app) { Resolve-Shortcut ([string]$app.path) } else { [ordered]@{exists=$false;path=$null;target=$null;arguments=$null} })
    $versionPath = $(if ($HostConfig.version_executable) { [string]$HostConfig.version_executable } else { [string]$shortcut.target })
    if ($HostConfig.version_search_root -and $HostConfig.version_filename) {
        $candidate = Get-ChildItem -LiteralPath ([string]$HostConfig.version_search_root) -Recurse -File -Filter ([string]$HostConfig.version_filename) -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
        if ($candidate) { $versionPath = $candidate.FullName }
    }
    if ($versionPath -and ([IO.Path]::GetFileName($versionPath) -ieq 'cmd.exe')) { $versionPath = $null }
    if ($versionPath -and -not (Test-Path -LiteralPath $versionPath) -and $shortcut.target) {
        $sibling = Join-Path ([IO.Path]::GetDirectoryName([string]$shortcut.target)) ([IO.Path]::GetFileName($versionPath))
        if (Test-Path -LiteralPath $sibling) { $versionPath = $sibling }
    }
    $discovery = @()
    if ((-not $shortcut.exists -or -not $versionPath -or -not (Test-Path -LiteralPath $versionPath)) -and $HostConfig.version_executable) {
        $discovery = @(Find-ShortcutCandidates ([IO.Path]::GetFileName([string]$HostConfig.version_executable)))
        if ($discovery.Count -eq 1) { $versionPath = [string]$discovery[0].target }
    }
    $deps = [ordered]@{}
    foreach ($name in @(Get-SharedDependencies ([string]$HostConfig.id))) { $deps[$name] = $Shared[$name] }
    $fingerprintFiles = [ordered]@{}
    foreach ($fp in @($HostConfig.fingerprint_files)) {
        if ($fp) { $fingerprintFiles[[string]$fp] = Get-FileMarker ([string]$fp) -Hash }
    }
    $isStandaloneCli = ([string]$HostConfig.probe.kind -eq 'standalone_cli')
    $marker = [ordered]@{
        id=[string]$HostConfig.id
        support=[string]$HostConfig.support
        enabled=$(if($isStandaloneCli){[bool]($versionPath -and (Test-Path -LiteralPath $versionPath -PathType Leaf))}elseif($app){[bool]$app.enabled}else{$false})
        process=$(if($app){[string]$app.process}else{$null})
        shortcut=$shortcut
        discovered_shortcuts=$discovery
        version_executable=(Get-FileMarker $versionPath)
        adapter=(Get-AdapterMarker $HostConfig)
        plugin=(Get-PluginMarker $HostConfig)
        shared_dependencies=$deps
    }
    if ($HostConfig.fingerprint_files) { $marker.fingerprint_files = $fingerprintFiles }
    $fingerprintSource = $marker | ConvertTo-Json -Depth 14 -Compress
    $marker.fingerprint = Get-StringHash $fingerprintSource
    return $marker
}

function Get-Inventory {
    $runtime = Get-Content -Raw -LiteralPath $Config.paths.runtime_manifest | ConvertFrom-Json
    $shared = Get-SharedInventory
    $hosts = [ordered]@{}
    foreach ($h in @($Config.hosts)) { $hosts[$h.id] = Get-HostInventory $h $runtime $shared }
    return [ordered]@{
        schema='velvetos.dcc-adobe.installed-inventory.v1'
        observed_at=(Get-Date).ToString('o')
        runtime_policy=$runtime.policy
        shared_components=$shared
        hosts=$hosts
    }
}

function Get-ObjectProperty($Object, [string]$Name) {
    if ($null -eq $Object) { return $null }
    $p = $Object.PSObject.Properties[$Name]
    if($p){ return $p.Value } else { return $null }
}

function Set-ObjectProperty($Object, [string]$Name, $Value) {
    $p = $Object.PSObject.Properties[$Name]
    if ($p) { $p.Value = $Value } else { $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value }
}

function Get-RoutingState {
    if (Test-Path -LiteralPath $RoutingPath) { return Get-Content -Raw -LiteralPath $RoutingPath | ConvertFrom-Json }
    return [pscustomobject]@{schema='velvetos.dcc-adobe.routing-state.v1';updated_at=$null;hosts=[pscustomobject]@{}}
}

function Set-RoutingStatus($Routing, [string]$Id, [string]$Status, [string]$Fingerprint, [string]$Reason) {
    $row = [pscustomobject]@{status=$Status;fingerprint=$Fingerprint;reason=$Reason;updated_at=(Get-Date).ToString('o')}
    Set-ObjectProperty $Routing.hosts $Id $row
    $Routing.updated_at = (Get-Date).ToString('o')
}

function Write-OwnerNotification([string]$Id, [string]$Status, [string]$Fingerprint, [string]$Message) {
    $key = Get-StringHash "$Id|$Status|$Fingerprint"
    $statePath = Join-Path $NotificationDir "$Id.json"
    if (Test-Path -LiteralPath $statePath) {
        $prior = Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json
        if ($prior.key -eq $key) { return $false }
    }
    $note = [ordered]@{schema='velvetos.owner-notification.v1';created_at=(Get-Date).ToString('o');host_id=$Id;status=$Status;fingerprint=$Fingerprint;message=$Message}
    Add-Content -LiteralPath $NotificationLog -Value ($note | ConvertTo-Json -Compress) -Encoding UTF8
    Write-JsonAtomic $statePath ([ordered]@{key=$key;created_at=$note.created_at})
    return $true
}

function Wait-ProcessState([string]$Name, [bool]$Running, [int]$TimeoutSeconds) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $p = @(Get-Process -Name $Name -ErrorAction SilentlyContinue)
        if ($Running -and $p.Count -gt 0) { return $p }
        if (-not $Running -and $p.Count -eq 0) { return @() }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    return @(Get-Process -Name $Name -ErrorAction SilentlyContinue)
}

function Get-RegistryEndpoint([string]$DccType, [int]$TimeoutSeconds, [int[]]$OwnerPids=@()) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        if (Test-Path -LiteralPath $Config.paths.dcc_registry) {
            try {
                $servicesRaw = Get-Content -Raw -LiteralPath $Config.paths.dcc_registry | ConvertFrom-Json
                $services = @($servicesRaw)
                $live = @($services | Where-Object {
                    if ($_.dcc_type -ne $DccType -or $_.status -ne 'available') { return $false }
                    if ($OwnerPids.Count -eq 0) { return $true }
                    $ownerPid = if (($_.PSObject.Properties.Name -contains 'host_pid') -and $_.host_pid) { [int]$_.host_pid } else { [int]$_.pid }
                    return $ownerPid -in $OwnerPids
                })
                if ($live.Count -gt 0) {
                    $entry = $live | Sort-Object @{Expression={if($_.last_heartbeat){[int64]$_.last_heartbeat.secs_since_epoch}else{0}};Descending=$true} | Select-Object -First 1
                    try {
                        $healthUrl = if ($entry.metadata -and $entry.metadata.discovery_mcp_url) {
                            ([string]$entry.metadata.discovery_mcp_url -replace '/mcp$','/health')
                        } else {
                            ("http://127.0.0.1:{0}/health" -f [int]$entry.port)
                        }
                        $h = Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 2
                        if ($h.StatusCode -eq 200) { return $entry }
                    } catch {}
                }
            } catch {}
        }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    return $null
}

function Invoke-JsonProcess([string]$Exe, [string[]]$Arguments, [int]$TimeoutSeconds=120) {
    $out = Join-Path $env:TEMP ("velvet-sentinel-$PID-"+[guid]::NewGuid().ToString('N')+'.out')
    $err = "$out.err"
    try {
        $p = Start-Process -FilePath $Exe -ArgumentList $Arguments -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden -PassThru
        if (-not $p.WaitForExit($TimeoutSeconds*1000)) { try{$p.Kill()}catch{}; throw "probe timeout after $TimeoutSeconds seconds" }
        # Complete redirected stdout/stderr draining before reading ExitCode.
        $p.WaitForExit()
        $p.Refresh()
        $stdoutRaw = $(if(Test-Path $out){Get-Content -Raw -LiteralPath $out}else{''})
        $stderrRaw = $(if(Test-Path $err){Get-Content -Raw -LiteralPath $err}else{''})
        $stdout = $(if($null -eq $stdoutRaw){''}else{[string]$stdoutRaw}).Trim()
        $stderr = $(if($null -eq $stderrRaw){''}else{[string]$stderrRaw}).Trim()
        $json = $null
        if ($stdout) {
            $last = ($stdout -split "\r?\n" | Where-Object { $_.Trim() } | Select-Object -Last 1)
            try { $json = $last | ConvertFrom-Json } catch {}
        }
        $exitCode = $p.ExitCode
        # Windows PowerShell can occasionally surface a null ExitCode for a completed
        # redirected child. Only structured probe PASS/FAIL may resolve that ambiguity.
        if ($null -eq $exitCode -and $json -and $json.status -eq 'PASS') { $exitCode = 0 }
        elseif ($null -eq $exitCode -and $json -and $json.status -eq 'FAIL') { $exitCode = 2 }
        return [ordered]@{exit_code=$exitCode;json=$json;stdout_sha256=(Get-StringHash $stdout);stderr_sha256=(Get-StringHash $stderr)}
    } finally {
        Remove-Item -Force -LiteralPath $out,$err -ErrorAction SilentlyContinue
    }
}

function Test-BackgroundHealth {
    $gateway = $false
    try { $gateway = ((Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:9765/health' -TimeoutSec 2).StatusCode -eq 200) } catch {}
    $brokers = [ordered]@{}
    foreach ($port in @(47391,47392,47393)) {
        $brokers["$port"] = [bool](Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -First 1)
    }
    return [ordered]@{gateway_9765=$gateway;brokers=$brokers}
}

function Invoke-HostProbe($HostConfig, $HostInventory, [switch]$Automatic) {
    $probe = $HostConfig.probe
    if ([string]$probe.kind -eq 'standalone_cli') {
        $stages = [ordered]@{
            preexisting_pids=@()
            launched_by_sentinel=$false
            host_pids=@()
            hidden=$true
            stopped_cleanly=$true
        }
        try {
            $args = @()
            foreach ($a in @($probe.args)) { $args += [string]$a }
            $timeout = $(if($probe.timeout_seconds){[int]$probe.timeout_seconds}else{30})
            $r = Invoke-JsonProcess ([string]$probe.executable) $args $timeout
            $stages.probe = $r
            if ($r.exit_code -ne 0 -or -not $r.json -or $r.json.status -ne 'PASS') {
                throw 'read-only compatibility probe failed'
            }
            $stages.background_health_before_stop = Test-BackgroundHealth
        } catch {
            $stages.error = $_.Exception.Message
        } finally {
            $stages.background_health_after = Test-BackgroundHealth
        }
        $pass = (-not $stages.error) -and ($stages.probe.exit_code -eq 0) -and
            ($stages.probe.json.status -eq 'PASS') -and $stages.background_health_after.gateway_9765
        return [ordered]@{
            classification=$(if($pass){'PASS_NEW_VERSION'}else{'NEEDS_COMPATIBILITY_REPAIR'})
            stage=$(if($pass){'complete'}else{'probe'})
            stages=$stages
        }
    }

    $runtime = Get-Content -Raw -LiteralPath $Config.paths.runtime_manifest | ConvertFrom-Json
    $app = $runtime.apps | Where-Object { $_.id -eq $HostConfig.id } | Select-Object -First 1
    if (-not $app) { return [ordered]@{classification='NEEDS_COMPATIBILITY_REPAIR';stage='runtime_manifest';error='host missing from runtime manifest'} }
    $processName = if (($app.PSObject.Properties.Name -contains 'automation_mode') -and
        [string]$app.automation_mode -eq 'headless_mayapy' -and
        ($app.PSObject.Properties.Name -contains 'automation_process') -and
        -not [string]::IsNullOrWhiteSpace([string]$app.automation_process)) {
        [string]$app.automation_process
    } else {
        [string]$app.process
    }
    $existing = @(Get-Process -Name $processName -ErrorAction SilentlyContinue)
    if ($Automatic -and $existing.Count -gt 0) {
        return [ordered]@{classification='DEFERRED_HOST_ALREADY_RUNNING';stage='preflight';preexisting_pids=@($existing.Id)}
    }
    $launched = ($existing.Count -eq 0)
    $stages = [ordered]@{preexisting_pids=@($existing.Id);launched_by_sentinel=$launched;effective_process=$processName}
    try {
        if ($launched) {
            & $Config.paths.host_manager -Action start -AppId $HostConfig.id -CompatibilityProbe | Out-Null
            $running = @(Wait-ProcessState $processName $true 45)
            if ($running.Count -eq 0) { throw 'host did not start' }
        } else { $running = $existing }
        Start-Sleep -Seconds 2
        $running = @(Get-Process -Name $processName -ErrorAction SilentlyContinue)
        $stages.host_pids = @($running.Id)
        $stages.hidden = (@($running | Where-Object { $_.MainWindowHandle -ne 0 }).Count -eq 0)
        if ($launched -and -not $stages.hidden) { throw 'agent-launched host remained visible' }

        $probe = $HostConfig.probe
        if ($probe.kind -eq 'streamable_registry') {
            $entry = Get-RegistryEndpoint ([string]$probe.dcc_type) 50 @($running.Id)
            if (-not $entry) { throw "no live dynamic MCP endpoint owned by the active $processName host for $($probe.dcc_type)" }
            $endpointUrl = if ($entry.metadata -and $entry.metadata.discovery_mcp_url) {
                [string]$entry.metadata.discovery_mcp_url
            } elseif ($entry.metadata -and $entry.metadata.mcp_url) {
                [string]$entry.metadata.mcp_url
            } else {
                ("http://127.0.0.1:{0}/mcp" -f [int]$entry.port)
            }
            $stages.endpoint_url = $endpointUrl
            $args = @((Join-Path $PSScriptRoot 'streamable_mcp_probe.py'),'--url',$endpointUrl)
            foreach ($tool in @($probe.tools)) { $args += @('--tool',[string]$tool) }
            $r = Invoke-JsonProcess ([string]$Config.paths.python) $args 30
        } elseif ($probe.kind -eq 'stdio') {
            $args = @((Join-Path $PSScriptRoot 'stdio_mcp_probe.py'),'--server',[string]$probe.server)
            foreach ($a in @($probe.server_args)) { $args += ("--server-arg=$a") }
            foreach ($e in @($probe.env)) { $args += @('--env',[string]$e) }
            $args += @('--tool',[string]$probe.tool)
            if ($probe.accept_result_error) { $args += @('--accept-result-error',[string]$probe.accept_result_error) }
            if ($probe.expected_server_name) { $args += @('--expected-server-name',[string]$probe.expected_server_name) }
            $r = Invoke-JsonProcess ([string]$Config.paths.python) $args 45
        } elseif ($probe.kind -eq 'fusion_native') {
            $deadline = (Get-Date).AddSeconds(35)
            $native = $null
            do {
                $native = Get-NetTCPConnection -State Listen -LocalPort ([int]$probe.port) -ErrorAction SilentlyContinue |
                    Where-Object { $_.LocalAddress -in @('127.0.0.1','::1') } | Select-Object -First 1
                if ($native) { break }
                Start-Sleep -Milliseconds 500
            } while ((Get-Date) -lt $deadline)
            if (-not $native) { throw "Fusion native MCP port $($probe.port) is not listening on loopback" }
            if ($running.Count -gt 0 -and $native.OwningProcess -notin @($running.Id)) {
                throw "Fusion native MCP port $($probe.port) is not owned by the active Fusion process"
            }
            $expectedServerNameArg = '"' + [string]$probe.expected_server_name + '"'
            $args = @((Join-Path $PSScriptRoot 'fusion_native_read_probe.py'),'--host',[string]$probe.host,'--port',[string]$probe.port,'--expected-server-name',$expectedServerNameArg)
            $r = Invoke-JsonProcess ([string]$Config.paths.python) $args 30
        } elseif ($probe.kind -eq 'meshmixer_cli') {
            $deadline = (Get-Date).AddSeconds(20)
            $udp = $null
            do {
                $udp = Get-NetUDPEndpoint -LocalPort ([int]$probe.port) -ErrorAction SilentlyContinue |
                    Where-Object { $_.LocalAddress -eq '127.0.0.1' } | Select-Object -First 1
                if ($udp) { break }
                Start-Sleep -Milliseconds 500
            } while ((Get-Date) -lt $deadline)
            if (-not $udp) { throw "Meshmixer mm-api UDP port $($probe.port) is not listening on loopback" }
            if ($running.Count -gt 0 -and $udp.OwningProcess -notin @($running.Id)) {
                throw "Meshmixer mm-api UDP port $($probe.port) is not owned by the active Meshmixer process"
            }
            $r = Invoke-JsonProcess ([string]$probe.executable) @('probe') 15
        } elseif ($probe.kind -eq 'affinity_mcp') {
            $deadline = (Get-Date).AddSeconds(30)
            $listener = $null
            do {
                $listener = Get-NetTCPConnection -State Listen -LocalPort ([int]$probe.port) -ErrorAction SilentlyContinue |
                    Where-Object { $_.LocalAddress -eq '127.0.0.1' } | Select-Object -First 1
                if ($listener) { break }
                Start-Sleep -Milliseconds 500
            } while ((Get-Date) -lt $deadline)
            if (-not $listener) { throw "Affinity MCP port $($probe.port) is not listening on loopback" }
            if ($running.Count -gt 0 -and $listener.OwningProcess -notin @($running.Id)) {
                throw "Affinity MCP port $($probe.port) is not owned by the active Affinity process"
            }
            $r = Invoke-JsonProcess ([string]$probe.python) @([string]$probe.adapter,'probe') 30
        } elseif ($probe.kind -eq 'corel_com') {
            $deadline = (Get-Date).AddSeconds(30)
            $listener = $null
            do {
                $listener = Get-NetTCPConnection -State Listen -LocalPort ([int]$probe.port) -ErrorAction SilentlyContinue |
                    Where-Object { $_.LocalAddress -eq '127.0.0.1' } | Select-Object -First 1
                if ($listener) { break }
                Start-Sleep -Milliseconds 500
            } while ((Get-Date) -lt $deadline)
            if (-not $listener) { throw "Corel safe adapter port $($probe.port) is not listening on loopback" }
            $r = Invoke-JsonProcess ([string]$probe.python) @([string]$probe.adapter,'probe','--app',[string]$probe.app) 30
            if ($r.exit_code -eq 0 -and $r.json) {
                if ([string]$r.json.app -ne [string]$probe.app) { throw "Corel probe app identity mismatch" }
                if ([string]$r.json.name -ne [string]$probe.expected_name) { throw "Corel probe name mismatch" }
                if ([string]$r.json.version -ne [string]$probe.expected_version) { throw "Corel probe version mismatch" }
                if ([bool]$r.json.visible) { throw "Corel probe reports a visible host" }
                if ([string]$r.json.automation -ne 'official_com') { throw "Corel probe automation identity mismatch" }
                if ([int]$r.json.session -le 0) { throw "Corel probe is not running in an interactive session" }
            }
        } elseif ($probe.kind -eq 'resolve_cli') {
            $deadline = (Get-Date).AddSeconds(30)
            $listener = $null
            do {
                $resolveIds = @($running | ForEach-Object Id)
                $fuscripts = @(
                    Get-CimInstance Win32_Process -Filter "Name='fuscript.exe'" -ErrorAction SilentlyContinue |
                        Where-Object { $_.ParentProcessId -in $resolveIds }
                )
                foreach ($fu in $fuscripts) {
                    $candidate = Get-NetTCPConnection -State Listen -LocalPort ([int]$probe.port) -ErrorAction SilentlyContinue |
                        Where-Object { $_.OwningProcess -eq $fu.ProcessId } |
                        Select-Object -First 1
                    if ($candidate) { $listener = $candidate; break }
                }
                if ($listener) { break }
                Start-Sleep -Milliseconds 500
            } while ((Get-Date) -lt $deadline)
            if (-not $listener) {
                throw "Resolve scripting port $($probe.port) is not owned by a fuscript child of the active Resolve process"
            }
            $probeDeadline = (Get-Date).AddSeconds(45)
            $r = $null
            do {
                $r = Invoke-JsonProcess ([string]$probe.python) @([string]$probe.script) 10
                if ($r.exit_code -eq 0 -and $r.json -and $r.json.status -eq 'PASS') { break }
                Start-Sleep -Milliseconds 750
            } while ((Get-Date) -lt $probeDeadline)
            if ($r.exit_code -eq 0 -and $r.json -and $probe.expected_version -and
                [string]$r.json.version -ne [string]$probe.expected_version) {
                throw "Resolve probe version mismatch: expected $($probe.expected_version), got $($r.json.version)"
            }
        } elseif ($probe.kind -eq 'adobe') {
            $conn = Get-NetTCPConnection -State Listen -LocalPort ([int]$probe.port) -ErrorAction SilentlyContinue | Select-Object -First 1
            if (-not $conn) { throw "AdobePy broker $($probe.port) is not listening" }
            $args = @((Join-Path $PSScriptRoot 'adobe_readonly_probe.py'),'--host',[string]$probe.host,'--port',[string]$probe.port)
            if ($probe.token_file) { $args += @('--token-file',('"' + [string]$probe.token_file + '"')) }
            if ($probe.config_js) { $args += @('--config-js',('"' + [string]$probe.config_js + '"')) }
            $probeDeadline = (Get-Date).AddSeconds(45)
            $attempts = 0
            do {
                $attempts += 1
                $r = Invoke-JsonProcess ([string]$probe.python) $args 20
                if ($r.exit_code -eq 0 -and $r.json -and $r.json.status -eq 'PASS') { break }
                Start-Sleep -Milliseconds 1500
            } while ((Get-Date) -lt $probeDeadline)
            $stages.adobe_probe_attempts = $attempts
        } else {
            throw "unsupported automatic probe kind: $($probe.kind)"
        }
        $stages.probe = $r
        if ($r.exit_code -ne 0 -or -not $r.json -or $r.json.status -ne 'PASS') { throw 'read-only compatibility probe failed' }
        $stages.background_health_before_stop = Test-BackgroundHealth
    } catch {
        $stages.error = $_.Exception.Message
    } finally {
        if ($launched) {
            try { & $Config.paths.host_manager -Action stop -AppId $HostConfig.id | Out-Null } catch { $stages.stop_error = $_.Exception.Message }
            $remaining = @(Wait-ProcessState $processName $false 25)
            $stages.stopped_cleanly = ($remaining.Count -eq 0)
        } else {
            $stages.stopped_cleanly = $null
        }
        $stages.background_health_after = Test-BackgroundHealth
    }
    $pass = (-not $stages.error) -and (-not $stages.stop_error) -and ($stages.probe.exit_code -eq 0) -and
        ($stages.probe.json.status -eq 'PASS') -and ((-not $launched) -or $stages.hidden) -and
        ((-not $launched) -or $stages.stopped_cleanly) -and $stages.background_health_after.gateway_9765
    return [ordered]@{
        classification=$(if($pass){'PASS_NEW_VERSION'}else{'NEEDS_COMPATIBILITY_REPAIR'})
        stage=$(if($pass){'complete'}elseif($stages.error){'probe_or_launch'}elseif($stages.stop_error){'cleanup'}else{'postcheck'})
        stages=$stages
    }
}

function Write-Receipt([string]$Id, $Previous, $Current, $ProbeResult) {
    $exePath = [string]$Current.version_executable.path
    $receipt = [ordered]@{
        schema='velvetos.dcc-adobe.post-update-receipt.v1'
        created_at=(Get-Date).ToString('o')
        host_id=$Id
        previous_fingerprint=$(if($Previous){[string]$Previous.fingerprint}else{$null})
        new_fingerprint=[string]$Current.fingerprint
        previous_version=$(if($Previous){$Previous.version_executable}else{$null})
        new_version=$Current.version_executable
        host_executable_sha256=$(if($exePath -and (Test-Path -LiteralPath $exePath -PathType Leaf)){(Get-FileHash -Algorithm SHA256 -LiteralPath $exePath).Hash}else{$null})
        adapter=$Current.adapter
        plugin=$Current.plugin
        shared_dependencies=$Current.shared_dependencies
        result=$ProbeResult
    }
    $stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
    $receiptPath = Join-Path $ReceiptDir "$stamp-$Id.json"
    Write-JsonAtomic $receiptPath $receipt
    return [ordered]@{path=$receiptPath;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $receiptPath).Hash}
}

Ensure-Directories
$openScadWatch = $null
$openScadWatchScript = Join-Path $PSScriptRoot 'Check-OpenScadNightlyUpdate.ps1'
if (Test-Path -LiteralPath $openScadWatchScript -PathType Leaf) {
    try {
        $watchRaw = (& $openScadWatchScript 2>&1 | Out-String).Trim()
        if ($watchRaw) { $openScadWatch = $watchRaw | ConvertFrom-Json }
    } catch {
        $openScadWatch = [ordered]@{status='CHECK_FAILED';error=$_.Exception.Message}
    }
}
$inventory = Get-Inventory

if ($Action -eq 'status') {
    $baselineExists = Test-Path -LiteralPath $BaselinePath
    $routing = Get-RoutingState
    [ordered]@{status='OK';baseline_exists=$baselineExists;inventory=$inventory;routing=$routing;update_watch=$openScadWatch} | ConvertTo-Json -Depth 20
    exit 0
}
Write-JsonAtomic $InventoryPath $inventory

if ($Action -eq 'seed') {
    if (-not $ConfirmKnownGood) { throw 'Seed requires -ConfirmKnownGood after live acceptance evidence is reviewed.' }
    $hosts = [pscustomobject]@{}
    foreach ($h in @($Config.hosts)) {
        $cur = $inventory.hosts[$h.id]
        if ($h.support -eq 'integrated') {
            if ([string]$h.probe.kind -eq 'standalone_cli') {
                if (-not $cur.enabled -or -not $cur.version_executable.exists -or ($cur.plugin -and -not $cur.plugin.exists)) {
                    throw "Cannot seed $($h.id): standalone CLI runtime state is incomplete"
                }
            } elseif (-not $cur.enabled -or -not $cur.version_executable.exists -or -not $cur.shortcut.exists) {
                throw "Cannot seed $($h.id): live installed/shortcut state is incomplete"
            }
        }
        Set-ObjectProperty $hosts ([string]$h.id) ([pscustomobject]$cur)
    }
    $baseline = [ordered]@{
        schema='velvetos.dcc-adobe.accepted-baseline.v1'
        accepted_at=(Get-Date).ToString('o')
        source='2026-09-30 accepted integration evidence plus live readback'
        hosts=$hosts
    }
    Write-JsonAtomic $BaselinePath $baseline
    $routing = Get-RoutingState
    foreach ($h in @($Config.hosts | Where-Object {$_.support -eq 'integrated'})) {
        Set-RoutingStatus $routing ([string]$h.id) 'available' ([string]$inventory.hosts[$h.id].fingerprint) 'known-good baseline seed'
    }
    Write-JsonAtomic $RoutingPath $routing
    [ordered]@{status='BASELINE_SEEDED';baseline=$BaselinePath;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $BaselinePath).Hash} | ConvertTo-Json -Depth 5
    exit 0
}

if (-not (Test-Path -LiteralPath $BaselinePath)) {
    [ordered]@{status='NEEDS_BASELINE';message='Run seed with -ConfirmKnownGood only after live known-good verification.';inventory=$InventoryPath} | ConvertTo-Json -Depth 5
    exit 3
}

$baseline = Get-Content -Raw -LiteralPath $BaselinePath | ConvertFrom-Json
$routing = Get-RoutingState
$reconciled = @()
foreach ($h in @($Config.hosts | Where-Object {$_.support -eq 'integrated'})) {
    $cur = $inventory.hosts[$h.id]
    $old = Get-ObjectProperty $baseline.hosts ([string]$h.id)
    $route = Get-ObjectProperty $routing.hosts ([string]$h.id)
    if ($old -and $cur -and $route -and
        [string]$old.fingerprint -eq [string]$cur.fingerprint -and
        [string]$route.status -eq 'pending_validation') {
        Set-RoutingStatus $routing ([string]$h.id) 'available' ([string]$cur.fingerprint) 'current fingerprint matches accepted baseline; stale pending state reconciled'
        $reconciled += [string]$h.id
    }
}
$changed = @()
foreach ($h in @($Config.hosts)) {
    $cur = $inventory.hosts[$h.id]
    $old = Get-ObjectProperty $baseline.hosts ([string]$h.id)
    if (-not $old -or $old.fingerprint -ne $cur.fingerprint) {
        $changed += [pscustomobject]@{config=$h;current=$cur;previous=$old}
    }
}
if ($Action -eq 'probe') {
    if (-not $AppId) { throw 'probe requires -AppId' }
    $h = $Config.hosts | Where-Object {$_.id -eq $AppId} | Select-Object -First 1
    if (-not $h -or $h.support -ne 'integrated') { throw "No integrated host config for $AppId" }
    $probePrevious = Get-ObjectProperty $baseline.hosts ([string]$h.id)
    $changed = @([pscustomobject]@{
        config=$h
        current=$inventory.hosts[$h.id]
        previous=$probePrevious
        manual_same_fingerprint=($probePrevious -and $probePrevious.fingerprint -eq $inventory.hosts[$h.id].fingerprint)
    })
}

if ($changed.Count -eq 0) {
    Write-JsonAtomic $InventoryPath $inventory
    Write-JsonAtomic $RoutingPath $routing
    [ordered]@{status='NO_DRIFT';observed_at=$inventory.observed_at;changed_hosts=@();reconciled_hosts=@($reconciled)} | ConvertTo-Json -Depth 5
    exit 0
}

$results = @()
foreach ($row in @($changed | Where-Object {$_.config.support -eq 'inventory_only'})) {
    $notified = Write-OwnerNotification ([string]$row.config.id) 'INVENTORY_ONLY_CHANGED' ([string]$row.current.fingerprint) 'Installed version changed; this GUI host has no accepted official VelvetOS adapter.'
    Set-ObjectProperty $baseline.hosts ([string]$row.config.id) ([pscustomobject]$row.current)
    $results += [ordered]@{id=$row.config.id;classification='INVENTORY_ONLY_CHANGED';notified=$notified}
}
$integrated = @($changed | Where-Object {$_.config.support -eq 'integrated'})
foreach ($row in $integrated) {
    Set-RoutingStatus $routing ([string]$row.config.id) 'pending_validation' ([string]$row.current.fingerprint) 'installed-version or integration-component drift detected'
}
Write-JsonAtomic $RoutingPath $routing

$limit = $(if($Action -eq 'probe'){1}else{[int]$Config.policy.max_automatic_probes_per_run})
$toProbe = @($integrated | Select-Object -First $limit)
foreach ($row in $toProbe) {
    $result = Invoke-HostProbe $row.config $row.current -Automatic:($Action -eq 'scan')
    if ($Action -eq 'probe' -and $row.manual_same_fingerprint -and $result.classification -eq 'PASS_NEW_VERSION') {
        $result.classification = 'PASS_COMPATIBILITY_CHECK'
    }
    $receipt = Write-Receipt ([string]$row.config.id) $row.previous $row.current $result
    if ($result.classification -in @('PASS_NEW_VERSION','PASS_COMPATIBILITY_CHECK')) {
        Set-ObjectProperty $baseline.hosts ([string]$row.config.id) ([pscustomobject]$row.current)
        Set-RoutingStatus $routing ([string]$row.config.id) 'available' ([string]$row.current.fingerprint) 'post-update compatibility gate passed'
        $notified = $(if ($result.classification -eq 'PASS_NEW_VERSION') {
            Write-OwnerNotification ([string]$row.config.id) 'PASS_NEW_VERSION' ([string]$row.current.fingerprint) 'Installed version changed and passed the hidden read-only compatibility gate.'
        } else { $false })
    } elseif ($result.classification -eq 'DEFERRED_HOST_ALREADY_RUNNING') {
        $notified = Write-OwnerNotification ([string]$row.config.id) 'VALIDATION_DEFERRED' ([string]$row.current.fingerprint) 'Version drift detected, but the host is already running; automatic validation was deferred to avoid disrupting the owner.'
    } else {
        Set-RoutingStatus $routing ([string]$row.config.id) 'needs_compatibility_repair' ([string]$row.current.fingerprint) 'post-update compatibility gate failed'
        $notified = Write-OwnerNotification ([string]$row.config.id) 'NEEDS_COMPATIBILITY_REPAIR' ([string]$row.current.fingerprint) 'Installed version changed and did not pass the compatibility gate; automatic routing is blocked only for this host.'
    }
    $results += [ordered]@{id=$row.config.id;classification=$result.classification;receipt=$receipt;notified=$notified}
}

foreach ($row in @($integrated | Select-Object -Skip $limit)) {
    $results += [ordered]@{id=$row.config.id;classification='PENDING_VALIDATION';notified=$false}
}

$baseline.accepted_at = (Get-Date).ToString('o')
Write-JsonAtomic $BaselinePath $baseline
Write-JsonAtomic $RoutingPath $routing
[ordered]@{
    status='DRIFT_PROCESSED'
    observed_at=$inventory.observed_at
    results=$results
    pending_count=@($integrated | Select-Object -Skip $limit).Count
} | ConvertTo-Json -Depth 12
