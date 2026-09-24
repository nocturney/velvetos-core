$ErrorActionPreference='Stop'
try {
 $boot='GrokBot Boot Supervisor'
 $handoff='GrokBot Interactive Handoff'
 $python='C:\Python314\python.exe'
 $root='C:\ProgramData\GrokBotBoot'
 $supervisor=Join-Path $root 'grok_boot_supervisor.py'
 $handoffScript=Join-Path $root 'grok_handoff.py'
 if (-not (Test-Path -LiteralPath $python)) { throw "Python missing: $python" }
 if (-not (Test-Path -LiteralPath $supervisor)) { throw "Supervisor missing: $supervisor" }
 if (-not (Test-Path -LiteralPath $handoffScript)) { throw "Handoff missing: $handoffScript" }

 $a1=New-ScheduledTaskAction -Execute $python -Argument ('"' + $supervisor + '"')
 $t1=New-ScheduledTaskTrigger -AtStartup
 $p1=New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
 $s1=New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 999 -RestartInterval ([TimeSpan]::FromMinutes(1))
 Register-ScheduledTask -TaskName $boot -Action $a1 -Trigger $t1 -Principal $p1 -Settings $s1 -Description 'Boot-safe failover supervisor. Never launches Grok desktop; desktop launch is interactive-only.' -Force | Out-Null

 $a2=New-ScheduledTaskAction -Execute $python -Argument ('"' + $handoffScript + '"')
 $t2=New-ScheduledTaskTrigger -AtLogOn -User 'CHRIS\Chris'
 $p2=New-ScheduledTaskPrincipal -UserId 'CHRIS\Chris' -LogonType Interactive -RunLevel Limited
 $s2=New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::FromMinutes(5))
 Register-ScheduledTask -TaskName $handoff -Action $a2 -Trigger $t2 -Principal $p2 -Settings $s2 -Description 'Starts Grok Bot only after a real interactive Chris logon.' -Force | Out-Null

 Start-ScheduledTask -TaskName $boot
 Start-Sleep -Seconds 3
 $b=Get-ScheduledTask -TaskName $boot
 $bi=Get-ScheduledTaskInfo -TaskName $boot
 $h=Get-ScheduledTask -TaskName $handoff
 if ([string]$b.Principal.LogonType -ne 'ServiceAccount') { throw 'Boot supervisor is not ServiceAccount' }
 if ([string]$h.Principal.LogonType -ne 'Interactive') { throw 'Interactive handoff lost Interactive logon type' }
 @{ok=$true;bootState=[string]$b.State;bootUser=[string]$b.Principal.UserId;bootLogon=[string]$b.Principal.LogonType;bootResult=$bi.LastTaskResult;handoffState=[string]$h.State;handoffLogon=[string]$h.Principal.LogonType} | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $root 'install_result.json')
} catch {
 @{ok=$false;error=$_.Exception.Message} | ConvertTo-Json | Set-Content -Encoding UTF8 'C:\ProgramData\GrokBotBoot\install_result.json'
 exit 1
}
