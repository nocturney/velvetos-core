$ErrorActionPreference = 'Stop'
$root = 'D:\Velvet\Tools\CuaPilot\0.34.0'
$driver = Join-Path $root 'runtime\cua-driver-rs-0.34.0-windows-x86_64\cua-driver.exe'
$env:CUA_DRIVER_RS_HOME = Join-Path $root 'state'
$logdir = Join-Path $root 'logs'
$summary = Join-Path $logdir 'fixture-smoke-summary.json'
$fixture = Join-Path $root 'fixture\CuaSmokeFixture.exe'
$target = Get-CimInstance Win32_Process -Filter "Name='CuaSmokeFixture.exe'" | Where-Object { $_.SessionId -eq 1 -and $_.ExecutablePath -eq $fixture } | Select-Object -First 1
if (-not $target) { throw 'Pilot fixture absent' }
$pidValue = [int]$target.ProcessId
$hwnd = [long](Get-Process -Id $pidValue).MainWindowHandle.ToInt64()
if ($hwnd -le 0) { throw 'Fixture window absent' }
$session = 'vf-cua-fixture'
function Invoke-Cua([string]$tool,[hashtable]$params,[string]$outpath) {
  $j = $params | ConvertTo-Json -Compress -Depth 8
  $lines = @($j | & $driver call $tool 2>&1)
  $exitCode = $LASTEXITCODE
  $result = $lines -join [Environment]::NewLine
  $result | Set-Content -LiteralPath $outpath -Encoding utf8
  if ($exitCode -ne 0) { throw "Cua tool $tool exit=$exitCode : $result" }
  return ($result | ConvertFrom-Json)
}
$argsBase = @{pid=$pidValue;window_id=$hwnd;include_screenshot=$false;max_depth=10;timeout_ms=5000;session=$session}
$before = Invoke-Cua 'get_window_state' $argsBase (Join-Path $logdir 'fixture-smoke-before.json')
if ($before.app_name -ne 'CuaSmokeFixture.exe') {throw 'Incorrect app identity'}
if ($before.window_title -ne 'VelvetOS Cua Isolated GUI Smoke') {throw 'Unexpected initial window'}
$button = @($before.elements | Where-Object { $_.role -eq 'Button' -and $_.label -eq 'Compute 6 times 7' }) | Select-Object -First 1
if (-not $button -or -not $button.element_token) {throw 'No exact test button in UIA tree'}
$clickArgs = @{pid=$pidValue;window_id=$hwnd;element_token=[string]$button.element_token;session=$session}
$click = Invoke-Cua 'click' $clickArgs (Join-Path $logdir 'fixture-smoke-click.json')
Start-Sleep -Milliseconds 450
$after = Invoke-Cua 'get_window_state' $argsBase (Join-Path $logdir 'fixture-smoke-after.json')
$titlePass = $after.window_title -eq 'VelvetOS Cua Isolated GUI Smoke - 42'
$labelPass = $after.tree_markdown -match 'Result: 42'
$pass = $titlePass -and $labelPass
$receipt = [ordered]@{
  schema = 'velvetos.cua-bounded-gui-smoke.v1'
  tested_at = (Get-Date -Format 'o')
  host = 'Chris'
  session_identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
  session_id = (Get-Process -Id $PID).SessionId
  app = 'CuaSmokeFixture.exe'
  app_path = $fixture
  app_sha256 = (Get-FileHash -LiteralPath $fixture -Algorithm SHA256).Hash.ToLowerInvariant()
  app_pid = $pidValue
  window_id = $hwnd
  authorization = 'bounded'
  runtime_authority = $false
  before_title = $before.window_title
  clicked = $button.label
  click_tool_status = $click.status
  after_title = $after.window_title
  result_label_readback = $labelPass
  title_readback = $titlePass
  result = $(if($pass){'PASS'}else{'FAIL'})
  no_user_document_affected = $true
}
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $summary -Encoding utf8
if (-not $pass) {throw "Post-action readback failed: title=$($after.window_title); label=$labelPass"}
