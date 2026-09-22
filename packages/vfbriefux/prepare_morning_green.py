#!/usr/bin/env python3
"""Prepare Morning Green artifacts and a fail-closed Gmail send request."""
from __future__ import annotations
import argparse, json, re, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PACK=ROOT/'packages'/'vfbriefux'
OUT=ROOT/'packages'/'vfops'/'out'

def extract_date(brief_json: Path) -> tuple[str,str]:
    data=json.loads(brief_json.read_text(encoding='utf-8'))
    line=str(data.get('date_line') or '')
    m=re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})',line)
    if not m: raise ValueError('brief date_line has no DD.MM.YYYY date')
    dd,mm,yyyy=(int(m.group(1)),int(m.group(2)),int(m.group(3)))
    return f'{yyyy:04d}-{mm:02d}-{dd:02d}', f'{dd}.{mm}.{yyyy}'

def run(cmd: list[str]) -> None:
    proc=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,encoding='utf-8')
    if proc.returncode:
        raise RuntimeError((proc.stderr or proc.stdout or 'command failed').strip())

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--brief-json',type=Path,required=True)
    ap.add_argument('--brief-txt',type=Path,required=True)
    ap.add_argument('--openpost',type=Path)
    ap.add_argument('--request',type=Path,default=OUT/'gmail-send-request.json')
    ap.add_argument('--enable',action='store_true',help='Explicitly arm the one-shot Gmail request')
    args=ap.parse_args()
    iso,display=extract_date(args.brief_json)
    green_json=OUT/f'morning-green-{iso}.json'
    green_txt=OUT/f'morning-green-{iso}.txt'
    green_html=OUT/f'morning-green-{iso}.html'
    build=[sys.executable,str(PACK/'build_morning_green.py'),'--brief-json',str(args.brief_json),'--brief-txt',str(args.brief_txt),'--output',str(green_json),'--visible-text',str(green_txt)]
    if args.openpost: build += ['--openpost',str(args.openpost)]
    run(build)
    run([sys.executable,str(PACK/'render_morning_green.py'),str(green_json),'-o',str(green_html)])
    def rel(p: Path) -> str: return p.resolve().relative_to(ROOT.resolve()).as_posix()
    req={
      'enabled':bool(args.enable),
      'requestId':f'morning-green-{iso}',
      'to':'nocturney@gmail.com',
      'subject':f'Velvet Factory · Morning Brief · {display}',
      'html':rel(green_html),
      'visibleText':rel(green_txt),
      'images':'packages/vfbriefux/assets/morning-green',
      'embedRemoteImages':True,
      'remoteImageLimit':8,
    }
    args.request.parent.mkdir(parents=True,exist_ok=True)
    args.request.write_text(json.dumps(req,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'date':iso,'enabled':req['enabled'],'html':req['html'],'visibleText':req['visibleText'],'request':rel(args.request)},ensure_ascii=False))
    return 0

if __name__=='__main__': raise SystemExit(main())