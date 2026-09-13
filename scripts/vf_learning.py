#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'packages/vfharness/state/learning-candidates'
VALID={'candidate','accepted','rejected','promoted','superseded','pruned'}

def now(): return datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')
def path_for(cid): return DIR/f'{cid}.json'
def load(cid):
    p=path_for(cid)
    if not p.exists(): raise SystemExit(f'missing candidate: {cid}')
    return p,json.loads(p.read_text())
def save(p,d): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n'); print(p)

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
    if a.status in {'accepted','promoted'} and not d.get('evidence'): raise SystemExit('cannot accept/promote without evidence')
    if a.status=='promoted' and not a.promote_to: raise SystemExit('promoted requires --promote-to')
    d['status']=a.status; d['last_seen']=now()
    if a.promote_to: d['promote_to']=a.promote_to
    save(p,d); return 0

def parser():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    c=sub.add_parser('new'); c.add_argument('candidate_id'); c.add_argument('--trigger',required=True); c.add_argument('--action',required=True); c.add_argument('--scope',choices=['task','project','owner'],required=True); c.add_argument('--confidence',type=float,default=0.3); c.add_argument('--evidence',action='append'); c.add_argument('--owner-correction',action='store_true'); c.add_argument('--supersedes'); c.set_defaults(fn=create)
    e=sub.add_parser('evidence'); e.add_argument('candidate_id'); e.add_argument('ref'); e.add_argument('--confidence',type=float); e.set_defaults(fn=evidence)
    s=sub.add_parser('status'); s.add_argument('candidate_id'); s.add_argument('status',choices=sorted(VALID)); s.add_argument('--promote-to'); s.set_defaults(fn=status)
    return p
if __name__=='__main__':
    a=parser().parse_args(); raise SystemExit(a.fn(a))
