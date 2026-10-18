[CmdletBinding()]
param(
 [ValidateSet('Controller','Child')][string]$Mode='Controller',
 [string]$Attempt='',
 [string]$SourceSha256=''
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$Root='D:\Velvet\Pilots\CuaCalcCP057-20261014'
$Script=Join-Path $Root 'calc.ps1'
$Prefix='VelvetOS-CP057-Calc-'
$AllowedHost='CHRIS'
$AllowedUser='CHRIS\Chris'
$Schema='velvetos.office2.cp057.native-calculator-uia-one-shot.v1'
$TaskExe='C:\Windows\System32\schtasks.exe'
$PSExe='C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
$UiaReadyWaitMs=10000
$UiaReadyPollMs=250
$script:BoundElementName=''
$script:BoundProcessName=''
$script:AttemptStarted=$null
$script:OwnedPids=@()
$script:CandidateFrameCount=0
$script:CandidateFrameTitles=''
$script:SelectedHost=''
$script:SelectedHostPid=0
$script:MatchedTitle=''
function Refuse([string]$reason){throw ('REFUSED_'+$reason)}
function Identity {
 $id=[Security.Principal.WindowsIdentity]::GetCurrent()
 $principal=New-Object Security.Principal.WindowsPrincipal($id)
 return @{user=$id.Name;system=[bool]$id.IsSystem;elevated=[bool]$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator);session=[int](Get-Process -Id $PID).SessionId}
}
function Calcs {
 return @(Get-Process -Name CalculatorApp,Calculator,calc -ErrorAction SilentlyContinue | Where-Object {$_.SessionId -eq 1})
}
function IdleSeconds {
 $cs=@'
using System;
using System.Runtime.InteropServices;
public static class IdleNativeCP057 {
 [StructLayout(LayoutKind.Sequential)] public struct LASTINPUTINFO { public UInt32 cbSize; public UInt32 dwTime; }
 [DllImport("user32.dll",SetLastError=true)] public static extern bool GetLastInputInfo(ref LASTINPUTINFO value);
 [DllImport("kernel32.dll")] public static extern UInt32 GetTickCount();
}
'@
 if(-not ('IdleNativeCP057' -as [type])) {Add-Type -TypeDefinition $cs -ErrorAction Stop}
 $li=New-Object IdleNativeCP057+LASTINPUTINFO
 $li.cbSize=8
 if(-not [IdleNativeCP057]::GetLastInputInfo([ref]$li)){Refuse 'IDLE_API_UNAVAILABLE'}
 $now=[uint64][IdleNativeCP057]::GetTickCount()
 return [math]::Round((($now+4294967296-[uint64]$li.dwTime)%4294967296)/1000,2)
}
function Get-CalculatorHostName($window) {
 if($null -eq $window){Refuse 'CALCULATOR_WINDOW_HOST_MISMATCH'}
 $name=''
 try { $name=[string](Get-Process -Id ([int]$window.Current.ProcessId) -ErrorAction Stop).ProcessName } catch {
  Refuse 'CALCULATOR_WINDOW_HOST_MISMATCH'
 }
 if($name -eq 'ApplicationFrameHost'){return $name}
 if(Test-ContentProcess $name){return $name}
 Refuse 'CALCULATOR_WINDOW_HOST_MISMATCH'
}
function Test-CalculatorTitle([string]$title) {
 if($title -eq 'Calculator'){return $true}
 if($title -eq 'מחשבון'){return $true}
 return $false
}
function Get-FrameTitle($el) {
 if($null -eq $el){return ''}
 try { return [string]$el.Current.Name } catch { return '' }
}
function Format-FrameTitles([string]$raw) {
 if([string]::IsNullOrEmpty($raw)){return ''}
 $text=(($raw -replace '[\r\n\t]+',' ').Trim())
 $text=$text -replace '(?i)[A-Za-z]:\\[^\s''";]+','<path>'
 $text=$text -replace '(?i)\\\\[^\s''";]+','<path>'
 $text=$text -replace '(?i)CHRIS\\Chris','<user>'
 $limited=$text
 if($text.Length -gt 160){$limited=$text.Substring(0,160)}
 return $limited.Trim()
}
function Update-OwnedPids {
 foreach($pr in @(Calcs)){
  $ownedId=[int]$pr.Id
  if(@($script:OwnedPids) -notcontains $ownedId){ $script:OwnedPids+=$ownedId }
 }
}
function Test-StartedThisAttempt($proc) {
 if($null -eq $proc){return $false}
 if(-not (Test-ContentProcess ([string]$proc.ProcessName))){return $false}
 try { if([int]$proc.SessionId -ne 1){return $false} } catch { return $false }
 $ownedId=[int]$proc.Id
 if(@($script:OwnedPids) -contains $ownedId){return $true}
 if($null -eq $script:AttemptStarted){return $false}
 $started=$null
 try { $started=$proc.StartTime.ToUniversalTime() } catch { return $false }
 if($started -lt $script:AttemptStarted.AddSeconds(-2)){return $false}
 if(@($script:OwnedPids) -notcontains $ownedId){ $script:OwnedPids+=$ownedId }
 return $true
}
function Get-FrameContentPid($frame) {
 if($null -eq $frame){return 0}
 $core=Find-UiaCoreWindow $frame
 if($null -eq $core){$core=Find-Win32CoreWindow $frame}
 if($null -eq $core){return 0}
 try { return [int]$core.Current.ProcessId } catch { return 0 }
}
function Test-FrameOwnsAttempt($frame) {
 if($null -eq $frame){return $false}
 $frameName=Get-ContentProcessName $frame
 $proc=$null
 if(Test-ContentProcess $frameName){
  try { $proc=Get-Process -Id ([int]$frame.Current.ProcessId) -ErrorAction SilentlyContinue } catch { $proc=$null }
 } else {
  $corePid=Get-FrameContentPid $frame
  if($corePid -le 0){return $false}
  try { $proc=Get-Process -Id $corePid -ErrorAction SilentlyContinue } catch { $proc=$null }
 }
 if(-not (Test-StartedThisAttempt $proc)){return $false}
 $title=Get-FrameTitle $frame
 if(Test-CalculatorTitle $title){ $script:MatchedTitle=[string]$title }
 $script:SelectedHost=Get-CalculatorHostName $frame
 $script:SelectedHostPid=[int]$frame.Current.ProcessId
 return $true
}
function Get-TopLevelFrames {
 $root=[System.Windows.Automation.AutomationElement]::RootElement
 $cond=[System.Windows.Automation.PropertyCondition]::new(
   [System.Windows.Automation.AutomationElement]::ClassNameProperty,'ApplicationFrameWindow')
 $hits=$null
 try { $hits=$root.FindAll([System.Windows.Automation.TreeScope]::Children,$cond) } catch { $hits=$null }
 $found=@()
 foreach($item in $hits){
  if($null -ne $item){$found+=$item}
 }
 Update-OwnedPids
 foreach($pr in @(Calcs)){
  $pidCond=[System.Windows.Automation.PropertyCondition]::new(
    [System.Windows.Automation.AutomationElement]::ProcessIdProperty,[int]$pr.Id)
  $self=$null
  try { $self=$root.FindFirst([System.Windows.Automation.TreeScope]::Children,$pidCond) } catch { $self=$null }
  if($null -ne $self){$found+=$self}
 }
 $seen=@()
 foreach($item in $found){
  $handle=0
  try { $handle=[int]$item.Current.NativeWindowHandle } catch { $handle=0 }
  if($handle -ne 0){
   if($seen -contains $handle){continue}
   $seen+=$handle
  }
  $item
 }
}
function Remember-CandidateFrames($frames) {
 $titles=@()
 foreach($frame in @($frames)){
  if($null -eq $frame){continue}
  $titles+=(Get-FrameTitle $frame)
 }
 $script:CandidateFrameCount=$titles.Count
 $script:CandidateFrameTitles=Format-FrameTitles ($titles -join ' | ')
}
function Find-OwnedFrame {
 $frames=@(Get-TopLevelFrames)
 Remember-CandidateFrames $frames
 $chosen=@()
 foreach($frame in $frames){
  if(Test-FrameOwnsAttempt $frame){ $chosen+=$frame }
 }
 if($chosen.Count -gt 1){Refuse 'CALCULATOR_FRAME_AMBIGUOUS'}
 if($chosen.Count -eq 1){return $chosen[0]}
 return $null
}
function FindWindow {
 return (Find-OwnedFrame)
}
function Test-ContentProcess([string]$name) {
 if(@('CalculatorApp','Calculator','calc') -contains $name){return $true}
 return $false
}
function Get-ContentProcessName($el) {
 if($null -eq $el){return ''}
 $contentPid=0
 try { $contentPid=[int]$el.Current.ProcessId } catch { return '' }
 if($contentPid -le 0){return ''}
 $proc=Get-Process -Id $contentPid -ErrorAction SilentlyContinue
 if($null -eq $proc){return ''}
 return [string]$proc.ProcessName
}
function Get-ElementClass($el) {
 if($null -eq $el){return ''}
 try { return [string]$el.Current.ClassName } catch { return '' }
}
function Remember-BoundElement($el) {
 if($null -eq $el){return}
 $script:BoundElementName=Get-ElementClass $el
 $script:BoundProcessName=Get-ContentProcessName $el
}
function Add-CalcContentNative {
 if('CalcContentNativeCP057' -as [type]){return}
 $cs=@'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
public static class CalcContentNativeCP057 {
 public delegate bool EnumProc(IntPtr hwnd, IntPtr lParam);
 static EnumProc keepAlive;
 [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr parent, EnumProc callback, IntPtr lParam);
 [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr hwnd, StringBuilder name, int max);
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint processId);
 public static IntPtr[] Children(IntPtr parent) {
  if(parent == IntPtr.Zero){ return new IntPtr[0]; }
  List<IntPtr> found = new List<IntPtr>();
  keepAlive = delegate(IntPtr hwnd, IntPtr lParam) { found.Add(hwnd); return true; };
  EnumChildWindows(parent, keepAlive, IntPtr.Zero);
  return found.ToArray();
 }
 public static string ClassOf(IntPtr hwnd) {
  StringBuilder name = new StringBuilder(256);
  GetClassName(hwnd, name, name.Capacity);
  return name.ToString();
 }
 public static int ProcessOf(IntPtr hwnd) {
  uint pid;
  GetWindowThreadProcessId(hwnd, out pid);
  return (int)pid;
 }
}
'@
 Add-Type -TypeDefinition $cs -ErrorAction Stop
}
function Select-ContentElement($hits) {
 $found=@()
 foreach($item in $hits){
  if($null -eq $item){continue}
  if(Test-ContentProcess (Get-ContentProcessName $item)){ $found+=$item }
 }
 if($found.Count -gt 1){Refuse 'CALCULATOR_CONTENT_WINDOW_AMBIGUOUS'}
 if($found.Count -eq 1){return $found[0]}
 return $null
}
function Find-UiaCoreWindow($frame) {
 if($null -eq $frame){return $null}
 $classCond=[System.Windows.Automation.PropertyCondition]::new(
   [System.Windows.Automation.AutomationElement]::ClassNameProperty,'Windows.UI.Core.CoreWindow')
 $hits=$null
 try { $hits=$frame.FindAll([System.Windows.Automation.TreeScope]::Children,$classCond) } catch { $hits=$null }
 $match=Select-ContentElement $hits
 if($null -ne $match){return $match}
 try { $hits=$frame.FindAll([System.Windows.Automation.TreeScope]::Descendants,$classCond) } catch { $hits=$null }
 return (Select-ContentElement $hits)
}
function Find-Win32CoreWindow($frame) {
 if($null -eq $frame){return $null}
 Add-CalcContentNative
 $parent=[IntPtr]::Zero
 try { $parent=[IntPtr]$frame.Current.NativeWindowHandle } catch { return $null }
 if($parent -eq [IntPtr]::Zero){return $null}
 $children=@([CalcContentNativeCP057]::Children($parent))
 $matched=@()
 foreach($hwnd in $children){
  if([CalcContentNativeCP057]::ClassOf($hwnd) -ne 'Windows.UI.Core.CoreWindow'){continue}
  $contentPid=[CalcContentNativeCP057]::ProcessOf($hwnd)
  $proc=Get-Process -Id $contentPid -ErrorAction SilentlyContinue
  if($null -eq $proc){continue}
  if(-not (Test-ContentProcess ([string]$proc.ProcessName))){continue}
  $matched+=$hwnd
 }
 if($matched.Count -gt 1){Refuse 'CALCULATOR_CONTENT_WINDOW_AMBIGUOUS'}
 if($matched.Count -ne 1){return $null}
 return [System.Windows.Automation.AutomationElement]::FromHandle($matched[0])
}
function Find-CalculatorContent($frame) {
 if($null -eq $frame){return $null}
 if(Test-ContentProcess (Get-ContentProcessName $frame)){
  Remember-BoundElement $frame
  return $frame
 }
 $core=Find-UiaCoreWindow $frame
 if($null -eq $core){$core=Find-Win32CoreWindow $frame}
 if($null -eq $core){return $null}
 Remember-BoundElement $core
 if(-not (Test-ContentProcess ([string]$script:BoundProcessName))){Refuse 'CALCULATOR_CONTENT_PROCESS_MISMATCH'}
 return $core
}
function Find-BoundRoot {
 $frame=FindWindow
 if($null -eq $frame){return $null}
 return (Find-CalculatorContent $frame)
}
function Resolve-ContentWindow($window) {
 if($null -ne $window -and (Test-ContentProcess (Get-ContentProcessName $window))){return $window}
 return (Find-BoundRoot)
}
function FindElementOnce($window,[string]$id) {
 if($null -eq $window){return $null}
 $c=[System.Windows.Automation.PropertyCondition]::new(
   [System.Windows.Automation.AutomationElement]::AutomationIdProperty,$id)
 try { return $window.FindFirst([System.Windows.Automation.TreeScope]::Descendants,$c) } catch { return $null }
}
function FindElement($window,[string]$id) {
 $deadline=[DateTime]::UtcNow.AddMilliseconds($UiaReadyWaitMs)
 while($true){
  if((IdleSeconds) -lt 600){Refuse 'USER_BECAME_ACTIVE'}
  $window=Resolve-ContentWindow $window
  if($null -eq $window){
   if([DateTime]::UtcNow -ge $deadline){Refuse 'EXPECTED_CALCULATOR_WINDOW_ABSENT'}
  } else {
   $el=FindElementOnce $window $id
   if($null -ne $el){return $el}
   if([DateTime]::UtcNow -ge $deadline){Refuse ('CALCULATOR_ELEMENT_UNAVAILABLE_'+$id)}
  }
  Start-Sleep -Milliseconds $UiaReadyPollMs
  $window=$null
 }
}
function Wait-CalculatorTree {
 $ids=@('CalculatorResults','num6Button','multiplyButton','num7Button','equalButton')
 $deadline=[DateTime]::UtcNow.AddMilliseconds($UiaReadyWaitMs)
 while($true){
  if((IdleSeconds) -lt 600){Refuse 'USER_BECAME_ACTIVE'}
  $frame=FindWindow
  $window=$null
  $missing=$null
  if($null -ne $frame){
   $window=Find-CalculatorContent $frame
   if($null -ne $window){
    foreach($id in $ids){
     if($null -eq (FindElementOnce $window $id)){$missing=$id;break}
    }
    if($null -eq $missing){return $window}
   }
  }
  if([DateTime]::UtcNow -ge $deadline){
   Update-OwnedPids
   if($null -eq $frame){
    if(@($script:OwnedPids).Count -eq 0){Refuse 'OWNED_CALCULATOR_PROCESS_NOT_FOUND'}
    Refuse 'CALCULATOR_CONTENT_WINDOW_UNAVAILABLE'
   }
   if($null -eq $window){Refuse 'CALCULATOR_CONTENT_WINDOW_UNAVAILABLE'}
   if($null -eq $missing){$missing='CalculatorResults'}
   Refuse ('CALCULATOR_ELEMENT_UNAVAILABLE_'+$missing)
  }
  Start-Sleep -Milliseconds $UiaReadyPollMs
 }
}
function Display {
 $window=Find-BoundRoot
 $display=FindElement $window 'CalculatorResults'
 return [string]$display.Current.Name
}
function Format-RefusalMessage([string]$raw) {
 if([string]::IsNullOrEmpty($raw)){return ''}
 $text=(($raw -replace '[\r\n\t]+',' ').Trim())
 if($text -cmatch '^(REFUSED_[A-Za-z0-9_]+)$'){return $Matches[1]}
 $code=''
 if($text -cmatch '(REFUSED_[A-Za-z0-9_]+)'){$code=$Matches[1]}
 $text=$text -replace '(?i)[A-Za-z]:\\[^\s''";]+','<path>'
 $text=$text -replace '(?i)\\\\[^\s''";]+','<path>'
 $text=$text -replace '(?i)CHRIS\\Chris','<user>'
 $limited=$text
 if($text.Length -gt 160){$limited=$text.Substring(0,160)}
 if($code -ne ''){return $code}
 return $limited.Trim()
}
function Press([string]$id) {
 if((IdleSeconds) -lt 600){Refuse 'USER_BECAME_ACTIVE'}
 $window=Find-BoundRoot
 $button=FindElement $window $id
 if($button.Current.ControlType -ne [System.Windows.Automation.ControlType]::Button){
   Refuse 'WRONG_UIA_CONTROL_TYPE'
 }
 $pattern=$button.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
 if($null -eq $pattern){Refuse ('NO_INVOKE_PATTERN_'+$id)}
 $pattern.Invoke()
}
if([Environment]::MachineName -ine $AllowedHost){Refuse 'WRONG_HOST'}
if([IO.Path]::GetFullPath($PSCommandPath) -ine $Script){Refuse 'WRONG_SOURCE_PATH'}
if(-not (Test-Path -LiteralPath $Root -PathType Container)){Refuse 'ROOT_MISSING'}
if($Mode -eq 'Child'){
 if($Attempt -notmatch '^[0-9a-f]{32}$'){Refuse 'BAD_ATTEMPT'}
 $rec=[ordered]@{
  schema=$Schema; status='DENIED';attempt_id=$Attempt;host=$env:COMPUTERNAME
  user='';session=-1;system_identity=$true;elevated=$true
  idle_seconds=0;source_sha256='';model_called=$false
  customer_or_production_effect=$false;gui_scope='CALCULATOR_ONLY'
  calc_created=$false;calc_closed=$false;step_results=@()
  core_signed_lease=$false;private_desktop_capture=$false
  first_result='';last_result='';failure_class='';failure_message='';refusal_code='';failure_stage=''
  calculator_window_host=''
  bound_element='';bound_process=''
  candidate_frame_count=0;candidate_frame_titles=''
 }
 $opened=$false
 $calcWindow=$null
 $prior=@()
 $owned=@()
 try {
  $who=Identity
  $rec.user=$who.user;$rec.session=$who.session
  $rec.system_identity=$who.system;$rec.elevated=$who.elevated
  if($who.system -or $who.elevated -or $who.session -ne 1 -or
      $who.user -ine $AllowedUser){Refuse 'NOT_INTERACTIVE_LIMITED_USER'}
  $rec.source_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
  $rec.idle_seconds=IdleSeconds
  if($rec.idle_seconds -lt 600){$rec.status='DENIED_USER_ACTIVE';Refuse 'USER_ACTIVE'}
  $prior=@(Calcs)
  if($prior.Count -ne 0){Refuse 'CALCULATOR_ALREADY_OPEN'}
  Add-Type -AssemblyName UIAutomationClient,UIAutomationTypes -ErrorAction Stop
  $script:AttemptStarted=[DateTime]::UtcNow
  $p=Start-Process -FilePath (Join-Path $env:WINDIR 'System32\calc.exe') -PassThru
  $opened=$true;$rec.calc_created=$true
  $owned=@( @(Calcs) | Select-Object -ExpandProperty Id )
  Update-OwnedPids
  $calcWindow=Wait-CalculatorTree
  $rec.calculator_window_pid=[int]$script:SelectedHostPid
  $rec.calculator_window_host=[string]$script:SelectedHost
  if([string]::IsNullOrEmpty([string]$rec.calculator_window_host)){Refuse 'CALCULATOR_WINDOW_HOST_MISMATCH'}
  $rec.bound_element=[string]$script:BoundElementName
  $rec.bound_process=[string]$script:BoundProcessName
  $rec.candidate_frame_count=[int]$script:CandidateFrameCount
  $rec.candidate_frame_titles=Format-FrameTitles ([string]$script:CandidateFrameTitles)
  if(-not (Test-ContentProcess $rec.bound_process)){Refuse 'CALCULATOR_CONTENT_PROCESS_MISMATCH'}
  $rec.first_result=Display
  if($rec.first_result -notmatch '0'){Refuse 'WRONG_CALCULATOR_INITIAL_STATE'}
  foreach($step in @(
    @{id='num6Button';expected='6'},
    @{id='multiplyButton';expected='6'},
    @{id='num7Button';expected='7'},
    @{id='equalButton';expected='42'}
  )){
    Press $step.id
    Start-Sleep -Milliseconds 400
    $label=Display
    $rec.step_results+=@{step=$step.id;observed=$label}
    if($label -notmatch [regex]::Escape($step.expected)){
      Refuse ('CALCULATOR_POSTCONDITION_'+$step.id)
    }
  }
  Start-Sleep -Milliseconds 500
  $rec.last_result=Display
  if($rec.last_result -notmatch '(^|[^\d])42\s*$'){Refuse 'CALCULATOR_42_READBACK_MISSING'}
  $rec.status='PASS_NATIVE_UIA_CALCULATOR_42_ONLY'
 } catch {
  if($rec.status -ne 'DENIED_USER_ACTIVE'){$rec.status='FAIL_CLOSED_REAL_APP'}
  $rec.failure_class=$_.Exception.GetType().Name
  $rec.failure_stage=[string]$_.CategoryInfo.Category
  $rec.failure_message=Format-RefusalMessage ([string]$_.Exception.Message)
  if($rec.failure_message -cmatch '^REFUSED_([A-Za-z0-9_]+)$'){
   $rec.refusal_code=$Matches[1]
  } else {
   $rec.refusal_code=''
  }
  if(-not [string]::IsNullOrEmpty([string]$script:BoundElementName)){
   $rec.bound_element=[string]$script:BoundElementName
  }
  if(-not [string]::IsNullOrEmpty([string]$script:BoundProcessName)){
   $rec.bound_process=[string]$script:BoundProcessName
  }
 } finally {
  if($opened){
   try {
    if($null -ne $calcWindow){
     $closeName=Get-ContentProcessName $calcWindow
     if(Test-ContentProcess $closeName){
      $wpat=$calcWindow.GetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern)
      if($null -ne $wpat){$wpat.Close()}
     }
    }
   }catch{}
   Start-Sleep -Milliseconds 250
   Update-OwnedPids
   foreach($pr in @(Calcs)){
    try { Stop-Process -Id ([int]$pr.Id) -Force -ErrorAction Stop } catch {}
   }
   Start-Sleep -Milliseconds 250
   $rec.calc_closed=(@(Calcs).Count -eq 0)
   $rec.candidate_frame_count=[int]$script:CandidateFrameCount
   $rec.candidate_frame_titles=Format-FrameTitles ([string]$script:CandidateFrameTitles)
   if($script:SelectedHostPid -gt 0){
    $rec.calculator_window_pid=[int]$script:SelectedHostPid
    $rec.calculator_window_host=[string]$script:SelectedHost
   }
  } else {$rec.calc_closed=$true}
  $dest=Join-Path $Root ('receipt-'+$Attempt+'.json')
  if(Test-Path -LiteralPath $dest){Refuse 'RECEIPT_COLLISION'}
  $temp=Join-Path $Root ('pending-'+$Attempt+'.tmp')
  [IO.File]::WriteAllText($temp,($rec|ConvertTo-Json -Depth 10)+[Environment]::NewLine,
    (New-Object Text.UTF8Encoding($false)))
  Move-Item -LiteralPath $temp -Destination $dest -ErrorAction Stop
 }
 if($rec.status -eq 'PASS_NATIVE_UIA_CALCULATOR_42_ONLY' -and $rec.calc_closed){exit 0}
 exit 2
}
# Controller: system management context solely for ephemeral task registration.
if(-not [Security.Principal.WindowsIdentity]::GetCurrent().IsSystem){Refuse 'CONTROLLER_REQUIRES_SYSTEM'}
if($SourceSha256 -notmatch '^[0-9a-fA-F]{64}$'){Refuse 'SOURCE_DIGEST_REQUIRED'}
$actual=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
if($actual -ine $SourceSha256){Refuse 'SOURCE_DIGEST_MISMATCH'}
if((Get-ScheduledTask -TaskName ($Prefix+'*') -ErrorAction SilentlyContinue)){Refuse 'TASK_COLLISION'}
if(@(Get-Process -Name CalculatorApp,Calculator,calc -ErrorAction SilentlyContinue).Count -ne 0){Refuse 'CALCULATOR_ALREADY_OPEN'}
$attempt=[Guid]::NewGuid().ToString('N')
$task=$Prefix+$attempt.Substring(0,12)
$receipt=Join-Path $Root ('receipt-'+$attempt+'.json')
$created=$false;$ok=$false
try {
 $run='powershell.exe -NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+$PSCommandPath+'" -Mode Child -Attempt '+$attempt
 if($run.Length -ge 261){Refuse 'TASK_COMMAND_TOO_LONG'}
 $create=& $TaskExe /Create /SC ONCE /ST 23:59 /TN $task /TR $run /RU $AllowedUser /IT /RL LIMITED 2>&1
 if($LASTEXITCODE -ne 0){Refuse 'TASK_REGISTRATION_DENIED'}
 $created=$true
 $info=Get-ScheduledTask -TaskName $task -ErrorAction Stop
 if($info.Principal.LogonType -ne 'Interactive' -or $info.Principal.RunLevel -ne 'Limited'){Refuse 'TASK_PRINCIPAL_WRONG'}
 if((Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash -ine $actual){Refuse 'SOURCE_CHANGED'}
 $started=& $TaskExe /Run /TN $task 2>&1
 if($LASTEXITCODE -ne 0){Refuse 'TASK_START_DENIED'}
 for($i=0;$i -lt 145;$i++){Start-Sleep -Milliseconds 500;if(Test-Path -LiteralPath $receipt){break}}
 if(-not (Test-Path -LiteralPath $receipt -PathType Leaf)){Refuse 'RECEIPT_MISSING'}
 $data=Get-Content -LiteralPath $receipt -Raw | ConvertFrom-Json
 if($data.schema -ne $Schema -or $data.attempt_id -cne $attempt -or
    $data.source_sha256 -ine $actual -or $data.user -ine $AllowedUser -or
    $data.session -ne 1 -or $data.system_identity -ne $false -or
    $data.elevated -ne $false -or $data.core_signed_lease -ne $false -or
    $data.model_called -ne $false -or $data.calc_closed -ne $true){
   Refuse 'CHILD_RECEIPT_IDENTITY_MISMATCH'
 }
 Write-Output ('CHILD_STATUS='+$data.status+' IDLE_SECONDS='+$data.idle_seconds+' STEP_COUNT='+@($data.step_results).Count)
 Write-Output ('FIRST_RESULT='+$data.first_result+' LAST_RESULT='+$data.last_result)
 if($data.failure_class){Write-Output ('FAILURE_CLASS='+$data.failure_class)}
 if($data.refusal_code){Write-Output ('REFUSAL_CODE='+$data.refusal_code)}
 if($data.bound_process){Write-Output ('BOUND_PROCESS='+$data.bound_process)}
 if($data.bound_element){Write-Output ('BOUND_ELEMENT='+$data.bound_element)}
 Write-Output ('CANDIDATE_FRAMES='+$data.candidate_frame_count+' TITLES='+$data.candidate_frame_titles)
 Get-FileHash -LiteralPath $receipt -Algorithm SHA256 | ForEach-Object{Write-Output ('RECEIPT_SHA256='+$_.Hash)}
 $ok=($data.status -eq 'PASS_NATIVE_UIA_CALCULATOR_42_ONLY')
} finally {
 if($created){
  $deleted=& $TaskExe /Delete /TN $task /F 2>&1
  if($LASTEXITCODE -ne 0){$ok=$false;Write-Output 'FAIL_TASK_CLEANUP'}
 }
 if(Get-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue){$ok=$false;Write-Output 'TASK_STILL_PRESENT'}else{Write-Output 'TASK_REMOVED=true'}
}
if($ok){exit 0}else{exit 2}
