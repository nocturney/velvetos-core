from __future__ import annotations
import argparse, datetime, json, subprocess, sys, time
from pathlib import Path
import msvcrt

ROOT=Path(r'C:\ProgramData\VelvetOS\instagram-failover')
MANIFESTS=ROOT/'manifests'
STATE=ROOT/'watch-state'
LOG=ROOT/'watch.log'
CLIENT=ROOT/'grok-instagram-failover.py'
LOCK=ROOT/'watch.lock'

def acquire_singleton():
    LOCK.parent.mkdir(parents=True,exist_ok=True)
    f=LOCK.open('a+b')
    f.seek(0,2)
    if f.tell()==0:
        f.write(b'0'); f.flush()
    f.seek(0)
    try:
        msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
    except OSError:
        f.close(); return None
    return f

def now_utc(): return datetime.datetime.now(datetime.timezone.utc)
def iso(dt=None): return (dt or now_utc()).isoformat().replace('+00:00','Z')
def atomic_json(path,payload):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name('.'+path.name+'.tmp')
    tmp.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    tmp.replace(path)
def log(event):
    event={'ts':iso(),**event}
    LOG.parent.mkdir(parents=True,exist_ok=True)
    with LOG.open('a',encoding='utf-8') as f: f.write(json.dumps(event,ensure_ascii=False)+'\n')
def parse_time(value):
    if not isinstance(value,str) or not value.strip(): return None
    try:
        dt=datetime.datetime.fromisoformat(value.strip().replace('Z','+00:00'))
    except ValueError: return None
    if dt.tzinfo is None: return None
    return dt.astimezone(datetime.timezone.utc)
def last_json(text):
    for line in reversed((text or '').splitlines()):
        line=line.strip()
        if not line.startswith('{'): continue
        try:
            x=json.loads(line)
            if isinstance(x,dict): return x
        except json.JSONDecodeError: pass
    return None
def run_client(manifest,execute=False):
    cmd=[sys.executable,'-X','utf8',str(CLIENT),'--manifest',str(manifest)]
    if execute: cmd.append('--execute')
    p=subprocess.run(cmd,text=True,capture_output=True,timeout=360,check=False)
    return p.returncode,last_json(p.stdout),((p.stderr or '').strip()[-500:])
def load_state(path):
    try:
        x=json.loads(path.read_text(encoding='utf-8-sig'))
        return x if isinstance(x,dict) else {}
    except Exception: return {}
def process_manifest(path):
    try: m=json.loads(path.read_text(encoding='utf-8-sig'))
    except Exception as exc:
        log({'event':'manifest_invalid','manifest':str(path),'error':str(exc)[:200]}); return
    if m.get('schema')!='velvet.instagram_failover.v1' or m.get('auto_failover') is not True: return
    sched=parse_time(m.get('scheduled_at_utc'))
    window=m.get('failover_window_minutes',30)
    if sched is None or not isinstance(window,int) or not (1<=window<=180):
        log({'event':'manifest_unarmed','manifest':str(path),'reason':'invalid_schedule_or_window'}); return
    pub=str(m.get('publication_id') or '')
    rid=str(m.get('rendition_id') or '')
    if not pub or not rid: return
    state_path=STATE/(pub+'.json')
    st=load_state(state_path)
    if st.get('status') in {'resolved','expired','manual_reconcile_required'}: return
    now=now_utc(); end=sched+datetime.timedelta(minutes=window)
    if now<sched: return
    if now>end:
        st.update({'status':'expired','publication_id':pub,'rendition_id':rid,'updated_at':iso(),'window_end':iso(end)})
        atomic_json(state_path,st); log({'event':'window_expired','publication_id':pub,'rendition_id':rid}); return
    if st.get('execute_attempted') is True:
        st.update({'status':'manual_reconcile_required','updated_at':iso(),'reason':'execute_was_already_attempted'})
        atomic_json(state_path,st); log({'event':'reconcile_required','publication_id':pub,'reason':'execute_already_attempted'}); return
    rc,dry,err=run_client(path,False)
    if not isinstance(dry,dict):
        st.update({'status':'waiting','updated_at':iso(),'last_error':'dry_run_no_json','stderr':err})
        atomic_json(state_path,st); return
    if dry.get('ok') is True and dry.get('mode')=='duplicate-safe':
        st.update({'status':'resolved','resolution':'duplicate_live','updated_at':iso(),'media_id':dry.get('media_id'),'permalink':dry.get('permalink')})
        atomic_json(state_path,st); log({'event':'already_live','publication_id':pub,'media_id':dry.get('media_id')}); return
    if dry.get('ok') is not True:
        st.update({'status':'waiting','updated_at':iso(),'last_dry_run':{k:dry.get(k) for k in ('blocked','error','mode','primary_reason')}})
        atomic_json(state_path,st); return
    if dry.get('mode')!='dry-run' or dry.get('primary_safe_to_failover') is not True:
        st.update({'status':'waiting_primary','updated_at':iso(),'primary_reason':dry.get('primary_reason'),'last_mode':dry.get('mode')})
        atomic_json(state_path,st); return
    st.update({'status':'executing','execute_attempted':True,'execute_started_at':iso(),'publication_id':pub,'rendition_id':rid,'primary_reason':dry.get('primary_reason')})
    atomic_json(state_path,st); log({'event':'execute_start','publication_id':pub,'rendition_id':rid,'reason':dry.get('primary_reason')})
    try:
        rc,out,stderr=run_client(path,True)
    except subprocess.TimeoutExpired:
        st.update({'status':'manual_reconcile_required','updated_at':iso(),'reason':'execute_timeout'})
        atomic_json(state_path,st); log({'event':'execute_timeout','publication_id':pub}); return
    if isinstance(out,dict) and out.get('ok') is True and out.get('mode') in {'executed','duplicate-safe'}:
        st.update({'status':'resolved','resolution':out.get('mode'),'updated_at':iso(),'media_id':out.get('media_id'),'permalink':out.get('permalink'),'live_verified':out.get('live_verified')})
        atomic_json(state_path,st); log({'event':'failover_resolved','publication_id':pub,'mode':out.get('mode'),'media_id':out.get('media_id')}); return
    st.update({'status':'manual_reconcile_required','updated_at':iso(),'reason':'execute_not_verified','result':{k:(out or {}).get(k) for k in ('mode','error','error_class','stage','write_outcome','retry_safety')},'stderr':stderr})
    atomic_json(state_path,st); log({'event':'reconcile_required','publication_id':pub,'reason':'execute_not_verified'})
def cycle():
    MANIFESTS.mkdir(parents=True,exist_ok=True); STATE.mkdir(parents=True,exist_ok=True)
    for p in sorted(MANIFESTS.glob('*.json')):
        try: process_manifest(p)
        except Exception as exc: log({'event':'watch_error','manifest':str(p),'error':str(exc)[:300]})
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--once',action='store_true'); ap.add_argument('--interval',type=int,default=30); a=ap.parse_args()
    lock=acquire_singleton()
    if lock is None: return 0
    if a.once: cycle(); return 0
    interval=max(10,min(a.interval,300))
    log({'event':'watch_start','interval_seconds':interval})
    while True:
        cycle(); time.sleep(interval)
if __name__=='__main__': raise SystemExit(main())