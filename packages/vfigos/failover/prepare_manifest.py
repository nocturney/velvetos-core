from __future__ import annotations
import argparse, datetime, json, re
from pathlib import Path

SCHEMA='velvet.instagram_failover.v1'
SHA64=re.compile(r'^[0-9a-f]{64}$')
CAS_RE=re.compile(r'/sha256/([0-9a-f]{64})/',re.I)

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--approval-request',required=True)
    p.add_argument('--preflight',required=True)
    p.add_argument('--repo-root',required=True)
    p.add_argument('--publication-id',required=True)
    p.add_argument('--rendition-id',required=True)
    p.add_argument('--scheduled-at-utc')
    p.add_argument('--auto-failover',action='store_true')
    p.add_argument('--failover-window-minutes',type=int,default=30)
    p.add_argument('--output',required=True)
    args=p.parse_args()
    if args.failover_window_minutes < 1 or args.failover_window_minutes > 180:
        raise SystemExit('failover window must be 1..180 minutes')
    scheduled_at=None
    if args.scheduled_at_utc:
        raw=args.scheduled_at_utc.strip().replace('Z','+00:00')
        try:
            dt=datetime.datetime.fromisoformat(raw)
        except ValueError as exc:
            raise SystemExit('invalid --scheduled-at-utc') from exc
        if dt.tzinfo is None:
            raise SystemExit('--scheduled-at-utc must include timezone')
        scheduled_at=dt.astimezone(datetime.timezone.utc).isoformat().replace('+00:00','Z')
    if args.auto_failover and scheduled_at is None:
        raise SystemExit('--auto-failover requires --scheduled-at-utc')
    req_path=Path(args.approval_request).resolve()
    preflight=Path(args.preflight).resolve()
    repo=Path(args.repo_root).resolve()
    if not req_path.is_file(): raise SystemExit('approval request missing')
    if not preflight.is_file(): raise SystemExit('preflight missing')
    if not (repo/'scripts'/'vf_send_preflight.py').is_file(): raise SystemExit('repo root missing preflight runner')
    req=json.loads(req_path.read_text(encoding='utf-8-sig'))
    for key in ('content_id','package_sha256','mutation_tool','mutation_payload'):
        if key not in req: raise SystemExit(f'approval request missing {key}')
    if req['mutation_tool']!='publish_image': raise SystemExit('only publish_image is supported')
    if not isinstance(req['package_sha256'],str) or not SHA64.fullmatch(req['package_sha256']): raise SystemExit('invalid package sha')
    payload=req['mutation_payload']
    if not isinstance(payload,dict) or payload.get('account')!='env': raise SystemExit('invalid mutation payload/account')
    image_url=payload.get('image_url')
    caption=payload.get('caption')
    if not isinstance(image_url,str) or not isinstance(caption,str) or not caption.strip(): raise SystemExit('image_url/caption missing')
    m=CAS_RE.search(image_url)
    if not m: raise SystemExit('image url is not bound to CAS sha256')
    manifest={
      'schema':SCHEMA,
      'content_id':req['content_id'],
      'package_sha256':req['package_sha256'],
      'format':'post',
      'repo_root':str(repo),
      'preflight_path':str(preflight),
      'approval_request_path':str(req_path),
      'expected_media_sha256':m.group(1).lower(),
      'publication_id':args.publication_id.strip(),
      'rendition_id':args.rendition_id.strip(),
      'scheduled_at_utc':scheduled_at,
      'auto_failover':bool(args.auto_failover),
      'failover_window_minutes':args.failover_window_minutes,
    }
    if not manifest['publication_id'] or not manifest['rendition_id']: raise SystemExit('publication/rendition id missing')
    out=Path(args.output).resolve(); out.parent.mkdir(parents=True,exist_ok=True)
    tmp=out.with_name('.'+out.name+'.tmp')
    tmp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    tmp.replace(out)
    print(json.dumps({'ok':True,'manifest':str(out),'content_id':manifest['content_id'],'publication_id':manifest['publication_id'],'rendition_id':manifest['rendition_id'],'media_sha256':manifest['expected_media_sha256']},ensure_ascii=False))
    return 0

if __name__=='__main__': raise SystemExit(main())