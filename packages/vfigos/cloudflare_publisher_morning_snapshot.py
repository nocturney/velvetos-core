#!/usr/bin/env python3
"""Read-only Cloudflare Publisher schedule snapshot for Morning Green.

Never schedules, cancels, uploads, or publishes. Never prints the control token.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import urllib.request
from pathlib import Path

DEFAULT_BASE = 'https://velvetos-instagram-publisher.velvetos-vf.workers.dev'

def get_json(base: str, path: str, token: str):
    req=urllib.request.Request(base.rstrip('/')+path, headers={
        'Authorization':f'Bearer {token}',
        'Accept':'application/json',
        'User-Agent':'VelvetOS-Morning-Green/1.0',
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode('utf-8'))

def main() -> int:
    ap=argparse.ArgumentParser(description='Read Cloudflare Publisher scheduled jobs for Morning Green')
    ap.add_argument('--base', default=DEFAULT_BASE)
    ap.add_argument('--days', type=int, default=14)
    ap.add_argument('--output', type=Path)
    args=ap.parse_args()
    token=(os.environ.get('VELVET_PUBLISHER_CONTROL_TOKEN') or '').strip()
    if not token:
        print('no token: set VELVET_PUBLISHER_CONTROL_TOKEN', file=os.sys.stderr); return 2
    if args.days < 1 or args.days > 60:
        print('--days must be 1..60', file=os.sys.stderr); return 2
    now=dt.datetime.now(dt.timezone.utc)
    end=now+dt.timedelta(days=args.days)
    runtime=get_json(args.base,'/v1/runtime',token)
    tick=int(runtime.get('last_cron_tick') or 0)
    heartbeat_age=max(0,int(now.timestamp())-tick) if tick else None
    if heartbeat_age is None or heartbeat_age > 180:
        print(f'publisher cron heartbeat stale/missing: age={heartbeat_age}', file=os.sys.stderr); return 3
    meta=get_json(args.base,'/v1/meta-health',token)
    if not meta.get('ok'):
        print('publisher Meta health failed', file=os.sys.stderr); return 3
    listing=get_json(args.base,'/v1/jobs',token)
    rows=[]; issues=[]
    for summary in listing.get('jobs') or []:
        if summary.get('status') not in {'scheduled','retry'}:
            continue
        ts=int(summary.get('scheduled_at') or 0)
        if not ts:
            continue
        scheduled_dt=dt.datetime.fromtimestamp(ts,dt.timezone.utc)
        if not (now <= scheduled_dt < end):
            continue
        jid=str(summary.get('id') or '')
        full=get_json(args.base,'/v1/jobs/'+jid,token).get('job') or {}
        media=list(full.get('media') or [])
        first=media[0] if media else {}
        thumb=str(first.get('url') or '').strip()
        if not thumb.startswith('https://'):
            issues.append({'publication_id':jid,'title':str(full.get('content_id') or jid),'scheduled_at':scheduled_dt.isoformat().replace('+00:00','Z'),'reason':'no_public_https_media'})
            thumb=None
        kind=str(full.get('kind') or '').strip().lower()
        rows.append({
            'publication_id':jid,
            'title':str(full.get('content_id') or jid),
            'scheduled_at':scheduled_dt.isoformat().replace('+00:00','Z'),
            'status':str(full.get('status') or ''),
            'content_profile':kind,
            'thumbnail_url':thumb,
            'thumbnail_media_id':str(first.get('key') or ''),
            'thumbnail_cid':None,
            'media':[{'id':str(m.get('key') or ''),'filename':'','public_url_ready':str(m.get('url') or '').startswith('https://'),'url':str(m.get('url') or ''),'poster_thumbnail_url':''} for m in media],
        })
    rows.sort(key=lambda r:r['scheduled_at'])
    payload={
        'schema':'velvet.morning_brief.publisher_snapshot.v1',
        'source':'cloudflare-instagram-publisher',
        'observed_at':now.isoformat().replace('+00:00','Z'),
        'window_days':args.days,
        'runtime':{'last_cron_tick':tick,'heartbeat_age_seconds':heartbeat_age,'job_counts':runtime.get('job_counts') or []},
        'meta_health':{'ok':bool(meta.get('ok')),'username':str(meta.get('username') or '')},
        'scheduled':rows,
        'scheduled_thumbnail_issues':issues,
    }
    raw=json.dumps(payload,ensure_ascii=False,indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(raw,encoding='utf-8')
        print(args.output)
    else:
        print(raw)
    return 0

if __name__=='__main__':
    raise SystemExit(main())