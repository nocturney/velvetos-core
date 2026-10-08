$ErrorActionPreference = 'Stop'
$base = 'D:\Velvet\Tools\DashyLaunchpad\4.7.0\smoke'
$exe = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
$profile = Join-Path $base 'isolated-edge'
$out = Join-Path $base 'rendered-dom.html'
$err = Join-Path $base 'edge-stderr.txt'
$args = @('--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check','--disable-extensions',"--user-data-dir=$profile",'--virtual-time-budget=12000','--dump-dom','http://127.0.0.1:4000/')
$proc = Start-Process -FilePath $exe -ArgumentList $args -PassThru -Wait -WindowStyle Hidden -RedirectStandardOutput $out -RedirectStandardError $err
$dom = if(Test-Path -LiteralPath $out){Get-Content -LiteralPath $out -Raw}else{''}
$checks = [ordered]@{
  exit_code = $proc.ExitCode
  html_bytes = $dom.Length
  app_initialized = ($dom -match 'id="app"')
  velvet_office_header = ($dom -match 'Velvet Office')
  control_center_link = ($dom -match 'velvetos-control-center-staging')
  api_health_link = ($dom -match 'velvetos-control-api')
  errors_found = ($dom -match 'catastrophic-error.+display: block')
}
$checks | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $base 'browser-smoke.json') -Encoding utf8
