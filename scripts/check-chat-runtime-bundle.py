#!/usr/bin/env python3
"""Verify the ChatGPT Project runtime is dependency-closed when isolated from the repo."""
from __future__ import annotations
import hashlib, json, shutil, subprocess, sys, tempfile
from pathlib import Path
from vf_project_bundle import resolve_reference

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=resolve_reference(ROOT,"instance:surface:chatgptProject/ASSET-MANIFEST-v6.6.4.json",instance_id="velvet-factory",env={})

def fail(msg:str)->None:
    print("FAIL chat-runtime-bundle: "+msg,file=sys.stderr)
    raise SystemExit(1)

def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n",b"\n")).hexdigest()

m=json.loads(MANIFEST.read_text(encoding="utf-8"))
rows=m.get("chat_runtime")
if not isinstance(rows,list) or len(rows)!=5:
    fail("manifest must bind exactly five dependency-closed runtime files")
expected={
    "vf_source_ingest.py","vf_chat_cold_start_preflight.py","vf_media_integrity.py",
    "vf_media_limits.py","vf_creative_master_bridge.py"
}
if {x.get("filename") for x in rows}!=expected:
    fail("runtime filename set mismatch")
with tempfile.TemporaryDirectory(prefix="vf-chat-runtime-") as td:
    dst=Path(td)
    for row in rows:
        src=ROOT/row["repo_path"]
        if not src.is_file() or sha(src)!=row.get("sha256"):
            fail("runtime hash mismatch: "+str(row.get("repo_path")))
        shutil.copyfile(src,dst/row["filename"])
    probes=[
        [sys.executable,"vf_source_ingest.py","--help"],
        [sys.executable,"vf_chat_cold_start_preflight.py","--help"],
        [sys.executable,"vf_creative_master_bridge.py","--help"],
        [sys.executable,"-c","import vf_media_integrity, vf_media_limits"],
    ]
    for cmd in probes:
        p=subprocess.run(cmd,cwd=dst,text=True,capture_output=True)
        if p.returncode!=0:
            fail("isolated runtime import/entrypoint failed: "+" ".join(cmd)+" :: "+(p.stderr or p.stdout)[-500:])
print("OK chat runtime dependency-closed files=5 isolated_imports=PASS")
