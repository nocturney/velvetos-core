import os,time,subprocess,win32ts,json,socket

ROOT=r'C:\ProgramData\GrokBotBoot'; GROK=r'C:\Program Files\Grok Bot\Grok Bot.exe'; LOG=os.path.join(ROOT,'supervisor.log'); STATUS=r'C:\Users\Chris\AppData\Roaming\Grok Bot\desktop-status.json'
ARGS=[GROK,'--remote-debugging-address=127.0.0.1','--remote-debugging-port=9222','--remote-allow-origins=*']
FAILOVER_DISPATCH=r'C:\ProgramData\VelvetOS\instagram-failover\trusted-dispatch.py'
FAILOVER_REQUESTS=r'C:\ProgramData\VelvetOS\instagram-failover\requests'
FAILOVER_WATCH=r'C:\ProgramData\VelvetOS\instagram-failover\failover-watch.py'
dispatch_proc=None
watch_proc=None
def log(m):
 with open(LOG,'a',encoding='utf-8') as f:f.write(time.strftime('%Y-%m-%d %H:%M:%S ')+m+'\n')
def interactive_chris():
 for s in win32ts.WTSEnumerateSessions(None,1,0):
  if s['SessionId']==0 or s['State']!=win32ts.WTSActive: continue
  try:u=win32ts.WTSQuerySessionInformation(None,s['SessionId'],win32ts.WTSUserName)
  except Exception:u=''
  if u.lower()=='chris': return True
 return False
def s0_running():
 p=subprocess.run(['tasklist','/fi','IMAGENAME eq Grok Bot.exe','/fi','SESSION eq 0'],capture_output=True,text=True,errors='ignore'); return 'Grok Bot.exe' in p.stdout
def stop_s0(): subprocess.run(['taskkill','/f','/t','/im','Grok Bot.exe','/fi','SESSION eq 0'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def health():
 time.sleep(8); st={}
 try: st=json.load(open(STATUS,encoding='utf-8'))
 except Exception as e: st={'error':repr(e)}
 try: c=socket.create_connection(('127.0.0.1',9222),1); c.close(); port=True
 except Exception: port=False
 log('health session0='+str(s0_running())+' signedIn='+str(st.get('signedIn'))+' pid='+str(st.get('pid'))+' port9222='+str(port))
def start_s0(): subprocess.Popen(ARGS,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP); log('no interactive Chris; started session0 Grok'); health()
def supervise_failover_watch():
 global watch_proc
 if watch_proc is not None and watch_proc.poll() is not None:
  log('instagram failover watch rc='+str(watch_proc.returncode)); watch_proc=None
 if watch_proc is None and os.path.isfile(FAILOVER_WATCH):
  watch_proc=subprocess.Popen([r'C:\Python314\python.exe','-X','utf8',FAILOVER_WATCH,'--interval','30'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
  log('instagram failover watch started pid='+str(watch_proc.pid))
def dispatch_failover():
 global dispatch_proc
 if dispatch_proc is not None and dispatch_proc.poll() is not None:
  out,err=dispatch_proc.communicate(); detail=(err or out or '').strip().splitlines(); tail=detail[-1][:300] if detail else ''
  log('instagram failover dispatch rc='+str(dispatch_proc.returncode)+' detail='+tail); dispatch_proc=None
 if dispatch_proc is None and os.path.isdir(FAILOVER_REQUESTS) and any(x.endswith('.json') for x in os.listdir(FAILOVER_REQUESTS)):
  dispatch_proc=subprocess.Popen([r'C:\Python314\python.exe','-X','utf8',FAILOVER_DISPATCH],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
  log('instagram failover dispatch started')
log('supervisor started')
while True:
 try:
  supervise_failover_watch()
  dispatch_failover()
  if interactive_chris():
   if s0_running(): stop_s0(); log('interactive Chris detected; stopped session0 Grok')
  elif not s0_running(): start_s0()
 except Exception as e: log('error '+repr(e))
 time.sleep(5)