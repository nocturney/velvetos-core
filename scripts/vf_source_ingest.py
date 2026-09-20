#!/usr/bin/env python3
"""Ingest current-request media into a VelvetOS workspace with exact-byte receipts.

External files are accepted only when they are explicitly named and live under an
allowed intake root supplied by the caller. The bridge never scans arbitrary
folders, never downloads URLs, and never alters source pixels.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil, sys
from pathlib import Path
from vf_media_integrity import inspect_media

VERSION=1
ORIGIN_KINDS={"CHAT_ATTACHMENT_FILE","LOCAL_USER_FILE","WORKSPACE_EXISTING"}

def digest(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def under(path:Path, root:Path)->bool:
    try: path.resolve().relative_to(root.resolve()); return True
    except ValueError: return False

def rel(root:Path,p:Path)->str:
    return p.resolve().relative_to(root.resolve()).as_posix()

def register(a):
    root=Path(a.root).resolve()
    src=Path(a.input).resolve()
    if not src.is_file(): raise ValueError("input file missing")
    allowed=[Path(x).resolve() for x in (a.intake_root or [])]
    if not under(src,root) and not allowed:
        raise ValueError("external input requires explicit --intake-root")
    if not under(src,root) and not any(under(src,x) for x in allowed):
        raise ValueError("input is outside explicit intake roots")
    if a.origin_kind not in ORIGIN_KINDS: raise ValueError("unsupported origin kind")
    info=inspect_media(src,"product source intake",source=True)
    src_sha=digest(src)
    forbidden={x.lower() for x in (a.forbid_sha or [])}
    if src_sha in forbidden: raise ValueError("source matches forbidden style/rejected artifact SHA")
    ws=(root/Path(a.workspace)).resolve()
    if not under(ws,root): raise ValueError("workspace escapes root")
    d=ws/"sources"; d.mkdir(parents=True,exist_ok=True)
    suffix=src.suffix.lower() or ".bin"
    dest=d/f"source-{a.index:02d}{suffix}"
    if dest.exists() and digest(dest)!=src_sha: raise ValueError("destination collision with different bytes")
    if not dest.exists(): shutil.copyfile(src,dest)
    if digest(dest)!=src_sha: raise ValueError("exact-byte source copy mismatch")
    receipt=d/f"source-{a.index:02d}.ingest.json"
    body={"version":VERSION,"ingest_method":"LOCAL_EXACT_COPY","exact_bytes_copied":True,
          "origin":{"kind":a.origin_kind,"locator":str(src),"sha256":src_sha},
          "materialized":{"path":rel(root,dest),"sha256":src_sha,"bytes":dest.stat().st_size,"media":info}}
    receipt.write_text(json.dumps(body,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return {"ok":True,"source":{"role":"PRODUCT_SOURCE","path":rel(root,dest),"sha256":src_sha},
            "source_ingest":{"path":rel(root,receipt),"sha256":digest(receipt)}}

def verify(a):
    root=Path(a.root).resolve(); rp=(root/Path(a.receipt)).resolve()
    if not under(rp,root) or not rp.is_file(): raise ValueError("receipt missing/outside root")
    body=json.loads(rp.read_text(encoding="utf-8"))
    if body.get("version")!=VERSION or body.get("ingest_method")!="LOCAL_EXACT_COPY" or body.get("exact_bytes_copied") is not True:
        raise ValueError("receipt does not prove exact-byte ingest")
    m=body.get("materialized") or {}; p=(root/Path(m.get("path",""))).resolve()
    if not under(p,root) or not p.is_file(): raise ValueError("materialized source missing")
    if digest(p)!=m.get("sha256") or p.stat().st_size!=m.get("bytes"): raise ValueError("materialized source mismatch")
    inspect_media(p,"materialized product source",source=True)
    return {"ok":True,"source":{"role":"PRODUCT_SOURCE","path":rel(root,p),"sha256":m["sha256"]},
            "source_ingest":{"path":rel(root,rp),"sha256":digest(rp)}}

def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest="cmd",required=True)
    r=sp.add_parser("register"); r.add_argument("--root",required=True); r.add_argument("--input",required=True)
    r.add_argument("--workspace",required=True); r.add_argument("--index",type=int,required=True)
    r.add_argument("--origin-kind",choices=sorted(ORIGIN_KINDS),required=True)
    r.add_argument("--intake-root",action="append",default=[]); r.add_argument("--forbid-sha",action="append",default=[])
    v=sp.add_parser("verify"); v.add_argument("--root",required=True); v.add_argument("--receipt",required=True)
    a=ap.parse_args()
    try: out=register(a) if a.cmd=="register" else verify(a)
    except Exception as e:
        print(json.dumps({"ok":False,"error":str(e)[:1000]},sort_keys=True),file=sys.stderr); return 1
    print(json.dumps(out,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
