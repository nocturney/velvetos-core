#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CHECKS={
  'runtime_contract':'check-runtime-doctor.py',
  'handoffs':'check-vf-handoff.py',
  'learning':'check-learning-lifecycle.py',
  'review_convergence':'check-review-convergence.py',
  'living_docs':'check-living-docs.py',
  'skill_health':'check-skill-health.py',
  'agent_surface':'check-agent-surface-security.py',
  'harness':'check-vfharness.py',
}

def main():
    results={}
    for key,name in CHECKS.items():
        path=ROOT/'scripts'/name
        if not path.exists():
            results[key]={'state':'missing','detail':name}; continue
        p=subprocess.run([sys.executable,str(path)],cwd=ROOT,text=True,capture_output=True)
        detail=((p.stdout or '')+'\n'+(p.stderr or '')).strip().splitlines()
        results[key]={'state':'pass' if p.returncode==0 else 'fail','detail':detail[-1] if detail else f'exit {p.returncode}'}
    failed=[k for k,v in results.items() if v['state'] in {'fail','missing'}]
    summary={'schema':'vf.health.v1','state':'healthy' if not failed else 'unhealthy','checks':results,'failed':failed}
    print(json.dumps(summary,ensure_ascii=False,sort_keys=True))
    return 1 if failed else 0
if __name__=='__main__': raise SystemExit(main())
