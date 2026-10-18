$ErrorActionPreference = 'Stop'
$root = 'D:\Velvet\Tools\CuaPilot\0.34.0'
$driver = Join-Path $root 'runtime\cua-driver-rs-0.34.0-windows-x86_64\cua-driver.exe'
$fixture = Join-Path $root 'fixture\CuaSmokeFixture.exe'
$policy = Join-Path $root 'config\pilot-capabilities.yaml'
$log = Join-Path $root 'logs\session1-launch.log'
$meta = Join-Path $root 'logs\session1-meta.txt'
$env:CUA_DRIVER_RS_HOME = Join-Path $root 'state'
Remove-Item Env:CUA_DRIVER_RS_MCP_HTTP_PORT -ErrorAction SilentlyContinue
Remove-Item Env:CUA_DRIVER_RS_MCP_HTTP_TOKEN -ErrorAction SilentlyContinue
"identity=$([Security.Principal.WindowsIdentity]::GetCurrent().Name)" | Set-Content -LiteralPath $meta
"session_id=$((Get-Process -Id $PID).SessionId)" | Add-Content -LiteralPath $meta
"exe=$driver" | Add-Content -LiteralPath $meta
"fixture_hash=$((Get-FileHash -LiteralPath $fixture -Algorithm SHA256).Hash)" | Add-Content -LiteralPath $meta
"manifest_hash=$((Get-FileHash -LiteralPath $policy -Algorithm SHA256).Hash)" | Add-Content -LiteralPath $meta
& $driver telemetry disable 2>&1 | Out-File -FilePath $log -Encoding utf8
& $driver telemetry status 2>&1 | Out-File -FilePath $log -Append -Encoding utf8
$existing = Get-CimInstance Win32_Process -Filter "Name='CuaSmokeFixture.exe'" | Where-Object { $_.SessionId -eq 1 -and $_.ExecutablePath -eq $fixture }
if (-not $existing) { Start-Process -FilePath $fixture | Out-Null; Start-Sleep -Seconds 2 }
Get-CimInstance Win32_Process -Filter "Name='CuaSmokeFixture.exe'" | Where-Object { $_.SessionId -eq 1 -and $_.ExecutablePath -eq $fixture } | ForEach-Object { "fixture_pid=$($_.ProcessId)" | Add-Content -LiteralPath $meta }
"serve_start=$(Get-Date -Format o)" | Add-Content -LiteralPath $meta
try {
  $proc = Start-Process -FilePath $driver -ArgumentList @('serve','--permission-mode','bounded','--capability-manifest',$policy,'--approve-capability-manifest','--no-overlay') -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput (Join-Path $root 'logs\serve-stdout.log') -RedirectStandardError (Join-Path $root 'logs\serve-stderr.log') -PassThru -Wait
  "serve_exit=$($proc.ExitCode)" | Add-Content -LiteralPath $meta
} catch {
  "launcher_error=$($_.Exception.Message)" | Add-Content -LiteralPath $meta
  $_ | Out-String | Out-File -FilePath $log -Append -Encoding utf8
}
