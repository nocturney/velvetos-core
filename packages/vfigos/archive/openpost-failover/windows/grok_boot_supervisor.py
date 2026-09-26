import os,time,subprocess

ROOT=r'C:\ProgramData\GrokBotBoot'
LOG=os.path.join(ROOT,'supervisor.log')
PYTHON=r'C:\Python314\python.exe'
FAILOVER_DISPATCH=r'C:\ProgramData\VelvetOS\instagram-failover\trusted-dispatch.py'
FAILOVER_REQUESTS=r'C:\ProgramData\VelvetOS\instagram-failover\requests'
FAILOVER_WATCH=r'C:\ProgramData\VelvetOS\instagram-failover\failover-watch.py'
dispatch_proc=None
watch_proc=None

def log(m):
 with open(LOG,'a',encoding='utf-8') as f:f.write(time.strftime('%Y-%m-%d %H:%M:%S ')+m+'\n')

def supervise_failover_watch():
 global watch_proc
 if watch_proc is not None and watch_proc.poll() is not None:
  log('instagram failover watch rc='+str(watch_proc.returncode))
  watch_proc=None
 if watch_proc is None and os.path.isfile(FAILOVER_WATCH):
  watch_proc=subprocess.Popen([PYTHON,'-X','utf8',FAILOVER_WATCH,'--interval','30'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
  log('instagram failover watch started pid='+str(watch_proc.pid))

def dispatch_failover():
 global dispatch_proc
 if dispatch_proc is not None and dispatch_proc.poll() is not None:
  out,err=dispatch_proc.communicate()
  detail=(err or out or '').strip().splitlines()
  tail=detail[-1][:300] if detail else ''
  log('instagram failover dispatch rc='+str(dispatch_proc.returncode)+' detail='+tail)
  dispatch_proc=None
 if dispatch_proc is None and os.path.isdir(FAILOVER_REQUESTS) and any(x.endswith('.json') for x in os.listdir(FAILOVER_REQUESTS)):
  dispatch_proc=subprocess.Popen([PYTHON,'-X','utf8',FAILOVER_DISPATCH],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
  log('instagram failover dispatch started')

log('boot-safe supervisor started; desktop_launch=forbidden; interactive launch owned by handoff/watchdog')
while True:
 try:
  supervise_failover_watch()
  dispatch_failover()
 except Exception as e:
  log('error '+repr(e))
 time.sleep(5)
