$ErrorActionPreference='Stop'
try {
 $legacyBoot='GrokBot Boot Supervisor'
 $handoff='GrokBot Interactive Handoff'
 $python='C:\Python314\python.exe'
 $root='C:\ProgramData\GrokBotBoot'
 $handoffScript=Join-Path $root 'grok_handoff.py'
 if (-not (Test-Path -LiteralPath $python)) { throw "Python missing: $python" }
 if (-not (Test-Path -LiteralPath $handoffScript)) { throw "Handoff missing: $handoffScript" }

 # OpenPost failover boot supervision was retired at the Cloudflare Publisher cutover.
 # Fail closed: if an old task exists, stop and disable it; never recreate it.
 $legacy=Get-ScheduledTask -TaskName $legacyBoot -ErrorAction SilentlyContinue
 if ($legacy) {
   Stop-ScheduledTask -TaskName $legacyBoot -ErrorAction SilentlyContinue
   Disable-ScheduledTask -TaskName $legacyBoot | Out-Null
 }

 $a=New-ScheduledTaskAction -Execute $python -Argument ('"' + $handoffScript + '"')
 $t=New-ScheduledTaskTrigger -AtLogOn -User 'CHRIS\Chris'
 $p=New-ScheduledTaskPrincipal -UserId 'CHRIS\Chris' -LogonType Interactive -RunLevel Limited
 $s=New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::FromMinutes(5))
 Register-ScheduledTask -TaskName $handoff -Action $a -Trigger $t -Principal $p -Settings $s -Description 'Starts Grok Bot only after a real interactive Chris logon.' -Force | Out-Null

 $h=Get-ScheduledTask -TaskName $handoff
 if ([string]$h.Principal.LogonType -ne 'Interactive') { throw 'Interactive handoff lost Interactive logon type' }
 $legacyState=if($legacy){[string](Get-ScheduledTask -TaskName $legacyBoot).State}else{'Absent'}
 @{ok=$true;legacyBootState=$legacyState;handoffState=[string]$h.State;handoffLogon=[string]$h.Principal.LogonType;publisher='cloudflare'} | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $root 'install_result.json')
} catch {
 @{ok=$false;error=$_.Exception.Message} | ConvertTo-Json | Set-Content -Encoding UTF8 'C:\ProgramData\GrokBotBoot\install_result.json'
 exit 1
}
