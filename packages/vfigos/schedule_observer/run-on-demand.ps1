# VelvetOS Instagram Source Observer: on-demand read, no publisher changes.
param([switch]$SkipMeta)
$ErrorActionPreference='Stop'
$now=[DateTime]::UtcNow
$out='D:\Velvet\Artifacts\MetaPlannerReader'
$code='D:\Velvet\Projects\MetaPlannerReader'
$profile='D:\Velvet\State\MetaPlannerReader\chrome-profile'
$meta=Join-Path $out 'scheduled-v3-snapshot.json'
$metaStatus=Join-Path $out 'status-v3.json'
$publisher=Join-Path $out 'publisher-production-read.json'
$calendar=Join-Path $out 'calendar-connector-snapshot.json'
$graph=Join-Path $out 'instagram-graph-snapshot.json'
$unified=Join-Path $out 'all-sources-latest.json'
$receipt=Join-Path $out 'on-demand-read-receipt.json'
$node='C:\Program Files\nodejs\node.exe'
$python='C:\Python311\python.exe'
$resolver='D:\Velvet\Runtime\OfficeV2Lab\Resolve-Phase3B-ProductionSnapshot.ps1'
$report=[ordered]@{
  schema='velvet.instagram.autonomous_read_receipt.v1'
  started_at=$now.ToString('o')
  identity=(whoami)
  external_mutations_performed=$false
  publisher_write_authority_change=$false
  meta='UNAVAILABLE'
  cloudflare='UNAVAILABLE'
  calendar='UNAVAILABLE'
  instagram_graph='UNAVAILABLE'
  completed_at=$null
  result='STARTED'
  error=$null
}
function StoreReceipt {
  $report.completed_at=[DateTime]::UtcNow.ToString('o')
  $report|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $receipt -Encoding UTF8
}
function Fresh([string]$f,[int]$ttl) {
  if(-not (Test-Path -LiteralPath $f)){return $false}
  try {
    $j=Get-Content -LiteralPath $f -Raw -Encoding UTF8|ConvertFrom-Json
    $t=$j.observed_at
    if(-not $t){return $false}
    $age=([DateTime]::UtcNow - ([DateTime]::Parse($t).ToUniversalTime())).TotalSeconds
    return ($age -ge -300 -and $age -le $ttl)
  }catch{return $false}
}
try {
  if((whoami) -ne 'chris\chris'){throw 'production read requires interactive Chris account'}
  if(-not (Test-Path $node) -or -not (Test-Path $python)){throw 'local reader executable missing'}
  if(-not (Test-Path (Join-Path $code 'source-registry.json'))){throw 'source registry missing'}
  if(-not (Test-Path $profile)){throw 'Meta browser login profile missing'}
  New-Item -ItemType Directory -Path $out -Force|Out-Null
  $metaLive=@(Get-CimInstance Win32_Process -Filter "Name='node.exe'" | Where-Object {
    $_.CommandLine -match 'MetaPlannerReader' -and $_.CommandLine -match 'reader-v3[.]cjs'
  })
  if(-not $SkipMeta -and $metaLive.Count -eq 0) {
    $script=Join-Path $code 'reader-v3.cjs'
    $args='"'+$script+'" --once --headless'
    $p=Start-Process -FilePath $node -ArgumentList $args -WorkingDirectory $code -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $out 'on-demand-meta-stdout.txt') -RedirectStandardError (Join-Path $out 'on-demand-meta-stderr.txt')
    if(-not $p.WaitForExit(150000)) {
      $report.meta='SCAN_TIMEOUT_PROCESS_RETAINED'
    }else {
      $j=$null
      try{$j=Get-Content -LiteralPath $metaStatus -Raw -Encoding UTF8|ConvertFrom-Json}catch{}
      $snap=$null
      try{$snap=Get-Content -LiteralPath $meta -Raw -Encoding UTF8|ConvertFrom-Json}catch{}
      $sameRun=$false
      if($snap -and $snap.observed_at){
        $when=[DateTime]::Parse([string]$snap.observed_at).ToUniversalTime()
        $sameRun=($when -ge $now.AddSeconds(-5))
      }
      if($j.phase -eq 'SCAN_COMPLETE' -and $snap.scheduled_selected -eq $true -and $snap.account_expected -eq 'velvets_cloud' -and $sameRun -and (Fresh $meta 900)) {
        $report.meta='FRESH_UI_CAPTURE'
      }else {
        $report.meta='SCAN_FAILED'
      }
    }
  }elseif(Fresh $meta 900){
    $report.meta=if($metaLive.Count) {'LIVE_BROWSER_CAPTURE_REUSED'} else {'RECENT_UI_CAPTURE_REUSED'}
  }else {
    $report.meta=if($metaLive.Count) {'BROWSER_BUSY_STALE_CAPTURE'}else{'META_REFRESH_SKIPPED_OR_UNAVAILABLE'}
  }
  $metaArgument=$null
  if($report.meta -in @('FRESH_UI_CAPTURE','LIVE_BROWSER_CAPTURE_REUSED','RECENT_UI_CAPTURE_REUSED')) {
    $metaArgument=$meta
  }
  $publisherArgument=$null
  try {
    if(-not (Test-Path $resolver)){throw 'Office v2 production resolver missing'}
    $raw=(& $resolver -Mode Production|Out-String).Trim()
    if($LASTEXITCODE -ne 0 -or -not $raw){throw 'production resolver returned empty or denied'}
    $d=$raw|ConvertFrom-Json
    if($d.schema -ne 'vf.instagram.schedule-snapshot.v1' -or $d.source -ne 'cloudflare-instagram-publisher' -or $d.meta_health.ok -ne $true){throw 'production resolver schema/health check failed'}
    $raw|Set-Content -LiteralPath $publisher -Encoding UTF8
    $publisherArgument=$publisher
    $report.cloudflare='FRESH_OFFICEV2_PRODUCTION_READ'
  }catch{
    # Never use incumbent control token or production write fallback.
    $report.cloudflare='OFFICEV2_READER_DENIED'
  }
  if(Fresh $calendar 3600){$report.calendar='CONNECTOR_SNAPSHOT_AVAILABLE'}
  if(Fresh $graph 3600){$report.instagram_graph='CONNECTOR_SNAPSHOT_AVAILABLE'}
  $arg=@((Join-Path $code 'source-reconciler.py'),'--registry',(Join-Path $code 'source-registry.json'),'--output',$unified)
  if($metaArgument){$arg+=@('--meta',$metaArgument)}
  if($publisherArgument){$arg+=@('--publisher',$publisherArgument)}
  if($report.calendar -eq 'CONNECTOR_SNAPSHOT_AVAILABLE'){$arg+=@('--calendar',$calendar)}
  if($report.instagram_graph -eq 'CONNECTOR_SNAPSHOT_AVAILABLE'){$arg+=@('--graph',$graph)}
  $message=& $python @arg
  if($LASTEXITCODE -ne 0){throw 'source reconciliation failed'}
  if(-not (Test-Path $unified)){throw 'source reconciliation output missing'}
  $r=Get-Content -LiteralPath $unified -Raw -Encoding UTF8|ConvertFrom-Json
  if($r.schema -ne 'velvet.instagram.source_reconciliation.v1' -or $r.policy.read_only -ne $true -or $r.policy.external_mutations_performed -ne $false){throw 'reconciler output contract invalid'}
  $report.result='PASS_WITH_SOURCE_COVERAGE_STATUS'
  $report.source_health=@($r.source_health|Select-Object source_id,state,count,age_seconds)
  $report.counts=$r.counts
  Write-Output ('OBSERVER '+$report.result+' meta='+$r.counts.meta_scheduled_lower_bound+' cloudflare='+$r.counts.cloudflare_scheduled+' missing='+$r.counts.missing_or_unverified_sources)
}catch{
  $report.result='FAIL_CLOSED'
  $report.error=([string]$_.Exception.Message -split "[\r\n]")[0]
  Write-Output ('OBSERVER '+$report.result)
}finally{
  StoreReceipt
}
if($report.result -ne 'PASS_WITH_SOURCE_COVERAGE_STATUS'){exit 3}
exit 0
