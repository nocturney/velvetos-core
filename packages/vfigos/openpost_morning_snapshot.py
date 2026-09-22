#!/usr/bin/env python3
"""Read-only OpenPost snapshot for the Velvet Morning Brief.

Never schedules or publishes. Never prints the bearer token.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_BASE = "https://openpost.34.9.7.22.sslip.io/api/v1"

def get_json(base: str, path: str, token: str, query: dict | None = None):
    url = base.rstrip('/') + path
    if query:
        url += '?' + urllib.parse.urlencode({k:v for k,v in query.items() if v is not None})
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}', 'Accept':'application/json'})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode('utf-8'))

def public_thumb(media: object) -> str | None:
    """Return only an already-absolute HTTPS thumbnail.

    OpenPost local-storage rows can expose relative /media/<id> paths while the
    route is still authenticated. Those are NOT public-email URLs and must be
    materialized separately through the deployment-safe CID cache.
    """
    rows = sorted(list(media or []), key=lambda m: int(m.get('display_order') or 0))
    for item in rows:
        if item.get('public_url_ready') is not True:
            continue
        for key in ('poster_thumbnail_url','url'):
            raw=str(item.get(key) or '').strip()
            if raw.startswith('https://'):
                return raw
    return None

def main() -> int:
    ap=argparse.ArgumentParser(description='Read OpenPost scheduled publications for Morning Green')
    ap.add_argument('--base', default=DEFAULT_BASE)
    ap.add_argument('--days', type=int, default=14)
    ap.add_argument('--output', type=Path)
    args=ap.parse_args()
    token=(os.environ.get('OPENPOST_TOKEN') or '').strip()
    if not token:
        print('no token: set OPENPOST_TOKEN', file=os.sys.stderr); return 2
    if args.days < 1 or args.days > 60:
        print('--days must be 1..60', file=os.sys.stderr); return 2

    workspaces=get_json(args.base,'/workspaces',token)
    if not isinstance(workspaces,list) or len(workspaces)!=1:
        raise RuntimeError(f'expected exactly one OpenPost workspace, got {len(workspaces) if isinstance(workspaces,list) else "non-list"}')
    workspace_id=str(workspaces[0]['id'])
    now=dt.datetime.now(dt.timezone.utc)
    end=now+dt.timedelta(days=args.days)
    publications=get_json(args.base,'/publications',token,{
        'workspace_id':workspace_id,
        'activity_bucket':'scheduled',
        'calendar_from':now.isoformat().replace('+00:00','Z'),
        'calendar_before':end.isoformat().replace('+00:00','Z'),
        'limit':50,
    })
    rows=[]; missing=[]
    for pub in publications or []:
        scheduled=str(pub.get('scheduled_at') or '').strip()
        if not scheduled:
            continue
        thumb=public_thumb(pub.get('media'))
        media_safe=[]
        for item in sorted(list(pub.get('media') or []), key=lambda m:int(m.get('display_order') or 0)):
            media_safe.append({
                'id':str(item.get('id') or ''),
                'filename':str(item.get('filename') or ''),
                'public_url_ready':item.get('public_url_ready') is True,
                'url':str(item.get('url') or ''),
                'poster_thumbnail_url':str(item.get('poster_thumbnail_url') or ''),
            })
        record={
            'publication_id':str(pub.get('id') or ''),
            'title':str(pub.get('title') or '').strip(),
            'scheduled_at':scheduled,
            'status':str(pub.get('status') or '').strip(),
            'content_profile':str(pub.get('content_profile') or '').strip(),
            'thumbnail_url':thumb,
            'thumbnail_media_id':str(media_safe[0].get('id') or '') if media_safe else '',
            'thumbnail_cid':None,
            'media':media_safe,
        }
        rows.append(record)
        if not thumb:
            missing.append({k:record[k] for k in ('publication_id','title','scheduled_at','status','media')})
    rows.sort(key=lambda r:r['scheduled_at'])
    payload={
        'schema':'velvet.morning_brief.openpost_snapshot.v1',
        'observed_at':now.isoformat().replace('+00:00','Z'),
        'window_days':args.days,
        'workspace_id':workspace_id,
        'scheduled':rows,
        'scheduled_thumbnail_issues':missing,
    }
    raw=json.dumps(payload,ensure_ascii=False,indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(raw,encoding='utf-8')
        print(args.output)
    else:
        print(raw)
    return 0

if __name__=='__main__':
    raise SystemExit(main())