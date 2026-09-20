#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]; BR=ROOT/"scripts/vf_source_ingest.py"
def run(*a,cwd): return subprocess.run([sys.executable,str(BR),*a],cwd=cwd,text=True,capture_output=True)
def fail(x): print("FAIL "+x,file=sys.stderr); raise SystemExit(1)
with tempfile.TemporaryDirectory() as t:
    base=Path(t); intake=base/"chat"; root=base/"runtime"; intake.mkdir(); root.mkdir()
    src=intake/"upload.png"; Image.new("RGB",(80,60),(230,220,200)).save(src)
    p=run("register","--root",str(root),"--input",str(src),"--workspace","work/job","--index","1",
          "--origin-kind","CHAT_ATTACHMENT_FILE","--intake-root",str(intake),cwd=base)
    if p.returncode: fail(p.stderr)
    out=json.loads(p.stdout); rec=out["source_ingest"]["path"]; mat=root/out["source"]["path"]
    if not mat.is_file(): fail("materialized source missing")
    q=run("verify","--root",str(root),"--receipt",rec,cwd=base)
    if q.returncode: fail(q.stderr)
    bad=run("register","--root",str(root),"--input",str(src),"--workspace","work/bad","--index","1",
            "--origin-kind","CHAT_ATTACHMENT_FILE",cwd=base)
    if bad.returncode==0: fail("external source accepted without intake root")
    mat.write_bytes(mat.read_bytes()+b"x")
    q=run("verify","--root",str(root),"--receipt",rec,cwd=base)
    if q.returncode==0: fail("tamper passed")
print("OK chat attachment source ingest exact-byte + bounds + tamper")
