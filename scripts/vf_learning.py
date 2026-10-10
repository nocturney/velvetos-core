#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'packages/vfharness/state/learning-candidates'
VALID={'candidate','accepted','rejected','promoted','superseded','expired','pruned'}
ALLOWED_TRANSITIONS={
    'candidate': {'candidate','accepted','rejected','expired','pruned'},
    'accepted': {'accepted','promoted','rejected','superseded','expired','pruned'},
    'promoted': {'promoted','superseded','expired'},
    'rejected': {'rejected'},
    'superseded': {'superseded'},
    'expired': {'expired'},
    'pruned': {'pruned'},
}

def now(): return datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')
def path_for(cid): return DIR/f'{cid}.json'
def load(cid):
    p=path_for(cid)
    if not p.exists(): raise SystemExit(f'missing candidate: {cid}')
    return p,json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(p)

def create(a):
    p=path_for(a.candidate_id)
    if p.exists(): raise SystemExit(f'candidate exists: {a.candidate_id}')
    d={'schema':'vf.learning-candidate.v1','candidate_id':a.candidate_id,'trigger':a.trigger,'action':a.action,
       'scope':a.scope,'confidence':a.confidence,'status':'candidate','evidence':a.evidence or [],
       'first_seen':now(),'last_seen':now(),'owner_correction':a.owner_correction,'promote_to':None,'supersedes':a.supersedes}
    save(p,d); return 0

def evidence(a):
    p,d=load(a.candidate_id); d.setdefault('evidence',[]).append(a.ref); d['last_seen']=now()
    if a.confidence is not None: d['confidence']=max(0,min(1,a.confidence))
    save(p,d); return 0

def status(a):
    p,d=load(a.candidate_id)
    if a.status not in VALID: raise SystemExit('invalid status')
    current=d.get('status')
    if a.status not in ALLOWED_TRANSITIONS.get(current,set()):
        raise SystemExit(f'invalid learning transition: {current} -> {a.status}')
    if a.status in {'accepted','promoted'} and not d.get('evidence'):
        raise SystemExit('cannot accept/promote without evidence')
    if a.status=='promoted':
        if current!='accepted': raise SystemExit('promotion requires current status=accepted')
        if not a.promote_to: raise SystemExit('promoted requires --promote-to')
    elif a.promote_to:
        raise SystemExit('--promote-to is only valid with status=promoted')
    d['status']=a.status; d['last_seen']=now()
    if a.promote_to: d['promote_to']=a.promote_to
    save(p,d); return 0

# --- CI failure signals -> learning candidates -------------------------------------------
# Deterministic and idempotent: candidate id, evidence and timestamps come only from the run
# records (never from the wall clock), evidence is de-duplicated by run id, a file is written
# only when its content changes, and status is never changed here (triage stays with the
# Office Loop / a human: accept, reject, promote, prune).
CI_FAILED={'failure','timed_out','startup_failure'}
CI_EVENTS={'push','schedule','workflow_dispatch'}
CI_ACTION=('Open a fix PR from the failing run log; if the root cause can recur, add or tighten a sensor/contract; '
           'triage this candidate (accept/reject/prune) instead of letting it accumulate.')

def _slug(name):
    import re
    return re.sub(r'[^a-z0-9]+','-',name.lower()).strip('-') or 'workflow'

def _ts(v):
    return datetime.fromisoformat(str(v).replace('Z','+00:00'))

def ingest_ci(a, runs=None, now=None):
    import sys
    target=Path(a.dir) if getattr(a,'dir',None) else DIR
    if runs is None: runs=json.loads(Path(a.runs).read_text(encoding='utf-8'))
    ref=_ts(a.now) if getattr(a,'now',None) else (now or datetime.now(timezone.utc))
    horizon=ref.timestamp()-a.window_days*86400
    groups={}
    for r in runs:
        if r.get('headBranch')!='main' or r.get('event') not in CI_EVENTS or r.get('conclusion') not in CI_FAILED: continue
        if not r.get('databaseId') or not r.get('workflowName') or not r.get('createdAt'): continue
        if _ts(r['createdAt']).timestamp()<horizon: continue
        groups.setdefault(r['workflowName'],[]).append(r)
    written=0
    for name in sorted(groups):
        rows=sorted(groups[name],key=lambda r:(r['createdAt'],r['databaseId']))
        cid='learn-ci-'+_slug(name); p=target/f'{cid}.json'
        d=json.loads(p.read_text(encoding='utf-8')) if p.exists() else {
            'schema':'vf.learning-candidate.v1','candidate_id':cid,
            'trigger':f"GitHub Actions workflow '{name}' failed on main",'action':CI_ACTION,'scope':'project',
            'confidence':0.3,'status':'candidate','evidence':[],'first_seen':rows[0]['createdAt'],
            'last_seen':rows[0]['createdAt'],'owner_correction':False,'promote_to':None,'supersedes':None,
            'source':'ci-failure-ingest','workflow':name}
        before=json.dumps(d,sort_keys=True,ensure_ascii=False)
        ev=d.setdefault('evidence',[]); seen={e.split(':')[1] for e in ev if isinstance(e,str) and e.startswith('gh-run:')}
        for r in rows:
            if str(r['databaseId']) not in seen:
                ev.append(f"gh-run:{r['databaseId']}:{r['conclusion']}:{r['createdAt']}:{r.get('url','')}"); seen.add(str(r['databaseId']))
        n=sum(1 for e in ev if isinstance(e,str) and e.startswith('gh-run:'))
        d['confidence']=max(float(d.get('confidence') or 0),round(min(0.8,0.3+0.1*(n-1)),2))
        last=rows[-1]['createdAt']
        if _ts(last)>_ts(d.get('last_seen') or last): d['last_seen']=last
        if json.dumps(d,sort_keys=True,ensure_ascii=False)!=before:
            save(p,d); written+=1
    print(f'OK ingest-ci workflows_failed={len(groups)} candidates_written={written} window_days={a.window_days}',file=sys.stderr)
    return 0

def selftest(_a):
    import tempfile, types
    runs=[
        {'databaseId':1,'workflowName':'VelvetOS Core Sensors','conclusion':'failure','createdAt':'2026-09-25T06:07:00Z','headBranch':'main','event':'push','url':'u1'},
        {'databaseId':2,'workflowName':'VelvetOS Core Sensors','conclusion':'failure','createdAt':'2026-09-25T09:00:00Z','headBranch':'main','event':'push','url':'u2'},
        {'databaseId':3,'workflowName':'VelvetOS Core Sensors','conclusion':'success','createdAt':'2026-09-26T09:00:00Z','headBranch':'main','event':'push','url':'u3'},
        {'databaseId':4,'workflowName':'VelvetOS Core Sensors','conclusion':'failure','createdAt':'2026-09-25T10:00:00Z','headBranch':'feature','event':'pull_request','url':'u4'},
        {'databaseId':5,'workflowName':'Old Workflow','conclusion':'failure','createdAt':'2026-09-01T00:00:00Z','headBranch':'main','event':'schedule','url':'u5'},
    ]
    with tempfile.TemporaryDirectory() as td:
        a=types.SimpleNamespace(dir=td,window_days=7,now='2026-09-26T12:00:00Z',runs=None)
        ingest_ci(a,runs=runs)
        files=sorted(Path(td).glob('*.json'))
        if [f.name for f in files]!=['learn-ci-velvetos-core-sensors.json']:
            raise AssertionError('INCORRECT_LEARNING_CANDIDATE_FILES:'+str(files))
        d=json.loads(files[0].read_text(encoding='utf-8')); first=files[0].read_text(encoding='utf-8')
        if not (d['status']=='candidate' and d['scope']=='project' and d['confidence']==0.4):
            raise AssertionError('CANDIDATE_STATUS_SCOPE_OR_CONFIDENCE_DRIFT')
        if not ([e.split(':')[1] for e in d['evidence']]==['1','2'] and
                d['first_seen']=='2026-09-25T06:07:00Z' and
                d['last_seen']=='2026-09-25T09:00:00Z'):
            raise AssertionError('RUN_EVIDENCE_OR_DERIVED_TIMESTAMPS_DRIFT')
        ingest_ci(a,runs=runs)
        if files[0].read_text(encoding='utf-8')!=first:
            raise AssertionError('CI_INGEST_NOT_IDEMPOTENT')
        d['status']='rejected'; files[0].write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        runs.append({'databaseId':6,'workflowName':'VelvetOS Core Sensors','conclusion':'timed_out','createdAt':'2026-09-26T10:00:00Z','headBranch':'main','event':'schedule','url':'u6'})
        ingest_ci(a,runs=runs); d=json.loads(files[0].read_text(encoding='utf-8'))
        if not (d['status']=='rejected' and len(d['evidence'])==3 and
                d['confidence']==0.5 and d['last_seen']=='2026-09-26T10:00:00Z'):
            raise AssertionError('CI_INGEST_WAS_NOT_STATUS_PRESERVING')
        # Windows default CP1252 must never corrupt an admitted UTF-8 record.
        # Test the actual persisted raw bytes and idempotent re-ingest.
        unicode_name='Owner ' + chr(0x2013) + ' ' + ''.join(chr(c) for c in (0x5d1,0x5d3,0x5d9,0x5e7,0x5d4))
        special=[{'databaseId':7,'workflowName':unicode_name,'conclusion':'failure',
                  'createdAt':'2026-09-26T11:00:00Z','headBranch':'main',
                  'event':'schedule','url':'u7'}]
        ingest_ci(a,runs=special)
        encoded=Path(td)/('learn-ci-'+_slug(unicode_name)+'.json')
        original_bytes=encoded.read_bytes()
        if not (original_bytes.startswith(b'{') and unicode_name.encode('utf-8') in original_bytes):
            raise AssertionError('UTF8_WRITE_CORRUPT')
        if json.loads(original_bytes.decode('utf-8'))['workflow']!=unicode_name:
            raise AssertionError('UTF8_ROUNDTRIP_FAILED')
        ingest_ci(a,runs=special)
        if encoded.read_bytes()!=original_bytes:
            raise AssertionError('UNICODE_INGEST_NOT_IDEMPOTENT')
    print('OK vf_learning selftest ingest-ci deterministic+idempotent+status-preserving+utf8')
    return 0

def parser():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    c=sub.add_parser('new'); c.add_argument('candidate_id'); c.add_argument('--trigger',required=True); c.add_argument('--action',required=True); c.add_argument('--scope',choices=['task','project','owner'],required=True); c.add_argument('--confidence',type=float,default=0.3); c.add_argument('--evidence',action='append'); c.add_argument('--owner-correction',action='store_true'); c.add_argument('--supersedes'); c.set_defaults(fn=create)
    e=sub.add_parser('evidence'); e.add_argument('candidate_id'); e.add_argument('ref'); e.add_argument('--confidence',type=float); e.set_defaults(fn=evidence)
    s=sub.add_parser('status'); s.add_argument('candidate_id'); s.add_argument('status',choices=sorted(VALID)); s.add_argument('--promote-to'); s.set_defaults(fn=status)
    i=sub.add_parser('ingest-ci',help='record failed main-branch GitHub Actions runs as learning candidates (idempotent)')
    i.add_argument('--runs',required=True,help='JSON from: gh run list --branch main --json databaseId,workflowName,conclusion,createdAt,headBranch,event,url')
    i.add_argument('--window-days',type=int,default=7); i.add_argument('--now',help='ISO-8601 reference time (tests); default: current UTC time')
    i.add_argument('--dir',help='candidate directory override (tests)'); i.set_defaults(fn=ingest_ci)
    t=sub.add_parser('selftest'); t.set_defaults(fn=selftest)
    return p
if __name__=='__main__':
    a=parser().parse_args(); raise SystemExit(a.fn(a))
