#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def score(rows):
    tp=sum(bool(r['expected']) and bool(r['observed']) for r in rows)
    fp=sum((not bool(r['expected'])) and bool(r['observed']) for r in rows)
    fn=sum(bool(r['expected']) and (not bool(r['observed'])) for r in rows)
    tn=sum((not bool(r['expected'])) and (not bool(r['observed'])) for r in rows)
    precision=tp/(tp+fp) if tp+fp else None
    recall=tp/(tp+fn) if tp+fn else None
    f1=(2*precision*recall/(precision+recall)) if precision is not None and recall is not None and precision+recall else None
    return {'tp':tp,'fp':fp,'fn':fn,'tn':tn,'precision':precision,'recall':recall,'f1':f1,'cases':len(rows)}

def load_jsonl(path):
    rows=[]
    for no,line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(),1):
        if not line.strip(): continue
        row=json.loads(line)
        if not isinstance(row.get('expected'),bool) or not isinstance(row.get('observed'),bool):
            raise ValueError(f'line {no}: expected/observed must be booleans')
        rows.append(row)
    if not rows: raise ValueError('empty evaluation set')
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input')
    ap.add_argument('--self-test',action='store_true')
    args=ap.parse_args()
    if args.self_test:
        got=score([{'expected':True,'observed':True},{'expected':False,'observed':True},{'expected':True,'observed':False},{'expected':False,'observed':False}])
        assert got['tp']==got['fp']==got['fn']==got['tn']==1
        assert abs(got['precision']-.5)<1e-9 and abs(got['recall']-.5)<1e-9 and abs(got['f1']-.5)<1e-9
        print(json.dumps({'status':'PASS','self_test':got},indent=2)); return
    if not args.input: ap.error('--input is required unless --self-test')
    print(json.dumps({'status':'PASS','metrics':score(load_jsonl(args.input))},indent=2))

if __name__=='__main__': main()
