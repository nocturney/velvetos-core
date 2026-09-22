param(
  [Parameter(Mandatory=$true)][string]$Snapshot,
  [Parameter(Mandatory=$true)][string]$OutputDir,
  [string]$Project='instamcp',
  [string]$Zone='us-central1-a',
  [string]$Instance='openpost-prod',
  [string]$RemoteMediaDir='/var/lib/openpost/media'
)
$ErrorActionPreference='Stop'
function Invoke-Gcloud([string[]]$CommandArgs){
  for($attempt=1;$attempt -le 2;$attempt++){
    & gcloud @CommandArgs
    if($LASTEXITCODE -eq 0){ return }
    if($attempt -lt 2){ Start-Sleep -Seconds 2 }
  }
  throw "gcloud failed after 2 attempts: $($CommandArgs -join ' ')"
}
$data=Get-Content -Raw $Snapshot | ConvertFrom-Json
if($data.schema -ne 'velvet.morning_brief.openpost_snapshot.v1'){ throw 'unexpected snapshot schema' }
if(Test-Path $OutputDir){ Remove-Item -Recurse -Force $OutputDir }
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$count=0
foreach($row in @($data.scheduled)){
  $pub=[string]$row.publication_id
  $media=[string]$row.thumbnail_media_id
  if($pub -notmatch '^[0-9a-f-]{36}$' -or $media -notmatch '^[0-9a-f-]{36}$'){ throw 'invalid OpenPost UUID in scheduled row' }
  $cid="scheduled-$pub.jpg"
  $tmp="/tmp/vfbrief-$media.jpg"
  $sm="$RemoteMediaDir/sm_$media.jpg"
  $orig="$RemoteMediaDir/$media.jpg"
  $remote="sudo install -m 0644 $sm $tmp"
  try {
    Invoke-Gcloud @('compute','ssh',$Instance,"--project=$Project","--zone=$Zone",'--tunnel-through-iap',"--command=$remote") | Out-Null
  } catch {
    $remote="sudo install -m 0644 $orig $tmp"
    Invoke-Gcloud @('compute','ssh',$Instance,"--project=$Project","--zone=$Zone",'--tunnel-through-iap',"--command=$remote") | Out-Null
  }
  Invoke-Gcloud @('compute','scp',"$($Instance):$tmp",(Join-Path $OutputDir $cid),"--project=$Project","--zone=$Zone",'--tunnel-through-iap') | Out-Null
  Invoke-Gcloud @('compute','ssh',$Instance,"--project=$Project","--zone=$Zone",'--tunnel-through-iap',"--command=sudo rm -f $tmp") | Out-Null
  $row.thumbnail_cid=$cid
  $row.thumbnail_url=$null
  $count++
}
$tmpJson="$Snapshot.tmp"
$json=$data | ConvertTo-Json -Depth 20
[IO.File]::WriteAllText($tmpJson,$json,[Text.UTF8Encoding]::new($false))
$written=$false
for($attempt=1;$attempt -le 3;$attempt++){
  try { Move-Item -Force $tmpJson $Snapshot; $written=$true; break }
  catch { if($attempt -lt 3){ Start-Sleep -Seconds 1 } }
}
if(-not $written){ throw 'failed to atomically replace snapshot after thumbnail materialization' }
Write-Output "THUMBNAILS_MATERIALIZED count=$count dir=$OutputDir"