#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
PREF=ROOT/"scripts/vf_chat_cold_start_preflight.py"; ING=ROOT/"scripts/vf_source_ingest.py"
BUNDLE=ROOT/"packages/velvetos/chatgpt-project"
def run(cmd): return subprocess.run(cmd,text=True,capture_output=True)
def fail(x): print("FAIL "+x,file=sys.stderr); raise SystemExit(1)
with tempfile.TemporaryDirectory() as t:
    t=Path(t); intake=t/"attachments"; ws=t/"runtime"; intake.mkdir(); ws.mkdir()
    src=intake/"product.png"; Image.new("RGB",(100,120),(235,230,220)).save(src)
    p=run([sys.executable,str(ING),"register","--root",str(ws),"--input",str(src),"--workspace","work/job","--index","1",
           "--origin-kind","CHAT_ATTACHMENT_FILE","--intake-root",str(intake)])
    if p.returncode: fail(p.stderr)
    ing=json.loads(p.stdout); mf=json.loads((BUNDLE/"ASSET-MANIFEST-v6.6.3.json").read_text())
    refs={x["filename"]:x["sha256"] for x in mf["assets"] if x["filename"] in set(mf["current_references"].values())}
    plan={"public_intent":"showcase","source_sha256":[ing["source"]["sha256"]],"reference_sha256":list(refs.values()),
          "product_truth":{"protected_regions":["whole-product"],"observations":"Source pixels inspected; preserve geometry and texture."},
          "reference_decomposition":{k:"Concrete inspected reference observation" for k in ("product_to_frame","environment","light","depth","negative_space","hierarchy","typography","details","surfaces","accent")},
          "source_set_detail_map":[{"source_sha256":ing["source"]["sha256"],"crop_region":"whole frame","visible_detail":"open lattice body","graphic_role":"hero","provenance":"SAME_FRAME_CROP"}],
          "creative_output_route":"LOCAL_FILE_OUTPUT","deterministic_overlay_expected":True}
    (ws/"plan.json").write_text(json.dumps(plan),encoding="utf-8")
    q=run([sys.executable,str(PREF),"--bundle-dir",str(BUNDLE),"--workspace",str(ws),"--plan","plan.json","--source-ingest",ing["source_ingest"]["path"]])
    if q.returncode: fail(q.stdout+q.stderr)
    out=json.loads(q.stdout)
    if out.get("creative_execution_authorized") is not True: fail("valid chat-local preflight did not authorize")
    plan["source_sha256"]=["0"*64]; (ws/"plan.json").write_text(json.dumps(plan),encoding="utf-8")
    q=run([sys.executable,str(PREF),"--bundle-dir",str(BUNDLE),"--workspace",str(ws),"--plan","plan.json","--source-ingest",ing["source_ingest"]["path"]])
    if q.returncode==0: fail("source identity drift passed")
print("OK chat-local cold-start preflight + exact source ingest")
