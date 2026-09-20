#!/usr/bin/env python3
import hashlib, json, shutil, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
PREF=ROOT/"scripts/vf_chat_cold_start_preflight.py"; ING=ROOT/"scripts/vf_source_ingest.py"
PROJECT=ROOT/"packages/velvetos/chatgpt-project"
def run(cmd): return subprocess.run(cmd,text=True,capture_output=True)
def fail(x): print("FAIL "+x,file=sys.stderr); raise SystemExit(1)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory() as t:
    t=Path(t); bundle=t/"bundle"; bundle.mkdir(); intake=t/"attachments"; ws=t/"runtime"; intake.mkdir(); ws.mkdir()
    # Build a self-consistent synthetic bundle around the real 6.6.3 authority/instructions/guide.
    for src,dst in [
        (PROJECT/"PROJECT-AUTHORITY-v6.6.3.txt",bundle/"PROJECT-AUTHORITY-v6.6.3.txt"),
        (PROJECT/"PROJECT-INSTRUCTIONS-v6.6.3.txt",bundle/"PROJECT-INSTRUCTIONS-v6.6.3.txt"),
        (PROJECT/"PRODUCT-TRUTH-GUIDE-v1.txt",bundle/"PRODUCT-TRUTH-GUIDE-v1.txt")]:
        shutil.copyfile(src,dst)
    mf=json.loads((PROJECT/"ASSET-MANIFEST-v6.6.3.json").read_text(encoding="utf-8"))
    mf["instructions"]["sha256"]=sha(bundle/"PROJECT-INSTRUCTIONS-v6.6.3.txt")
    for row in mf["assets"]:
        if row["filename"]=="Velvet-Factory-Project-Authority-v6.txt":
            row["sha256"]=sha(bundle/"PROJECT-AUTHORITY-v6.6.3.txt")
        elif row["filename"]==mf["product_truth"]["guide"]:
            row["sha256"]=sha(bundle/"PRODUCT-TRUTH-GUIDE-v1.txt")
        elif row["filename"] in set(mf["current_references"].values()):
            p=bundle/row["filename"]; idx=list(mf["current_references"].values()).index(row["filename"])
            Image.new("RGB",(64,64),(210-idx*20,200-idx*15,190-idx*10)).save(p)
            row["sha256"]=sha(p); row["bytes"]=p.stat().st_size; row["dimensions"]=[64,64]
    (bundle/"ASSET-MANIFEST-v6.6.3.json").write_text(json.dumps(mf),encoding="utf-8")
    ingested=[]
    for idx,(name,color) in enumerate((("hero.png",(235,230,220)),("alternate.png",(225,215,205))),1):
        src=intake/name; Image.new("RGB",(100+idx*5,120),(color)).save(src)
        p=run([sys.executable,str(ING),"register","--root",str(ws),"--input",str(src),"--workspace","work/job","--index",str(idx),
               "--origin-kind","CHAT_ATTACHMENT_FILE","--intake-root",str(intake)])
        if p.returncode: fail(p.stderr)
        ingested.append(json.loads(p.stdout))
    refs={x["filename"]:x["sha256"] for x in mf["assets"] if x["filename"] in set(mf["current_references"].values())}
    source_shas=[x["source"]["sha256"] for x in ingested]
    plan={"public_intent":"showcase","source_sha256":source_shas,"reference_sha256":list(refs.values()),
          "product_truth":{"protected_regions":["whole-product"],"observations":"Both source frames inspected; preserve geometry and texture."},
          "reference_decomposition":{k:"Concrete inspected reference observation" for k in ("product_to_frame","environment","light","depth","negative_space","hierarchy","typography","details","surfaces","accent")},
          "source_set_detail_map":[
              {"source_sha256":source_shas[0],"crop_region":"whole frame","visible_detail":"open lattice body","graphic_role":"hero","provenance":"SAME_FRAME_CROP"},
              {"source_sha256":source_shas[1],"crop_region":"upper body","visible_detail":"alternate verified angle","graphic_role":"detail inset","provenance":"ALTERNATE_VERIFIED_SOURCE"}],
          "creative_output_route":"LOCAL_FILE_OUTPUT","deterministic_overlay_expected":True}
    (ws/"plan.json").write_text(json.dumps(plan),encoding="utf-8")
    cmd=[sys.executable,str(PREF),"--bundle-dir",str(bundle),"--workspace",str(ws),"--plan","plan.json"]
    for x in ingested: cmd += ["--source-ingest",x["source_ingest"]["path"]]
    q=run(cmd)
    if q.returncode: fail(q.stdout+q.stderr)
    out=json.loads(q.stdout)
    if out.get("creative_execution_authorized") is not True or out.get("delivery_authorized") is not False:
        fail("valid chat-local preflight scope mismatch")
    plan["source_sha256"]=["0"*64, source_shas[1]]; (ws/"plan.json").write_text(json.dumps(plan),encoding="utf-8")
    q=run(cmd)
    if q.returncode==0: fail("source identity drift passed")

    # A style reference may be readable image bytes, but must never cross into PRODUCT_SOURCE.
    ref_name=next(iter(mf["current_references"].values())); ref_path=bundle/ref_name
    p=run([sys.executable,str(ING),"register","--root",str(ws),"--input",str(ref_path),"--workspace","work/style-as-source","--index","1",
           "--origin-kind","LOCAL_USER_FILE","--intake-root",str(bundle)])
    if p.returncode: fail("fixture could not stage style bytes for negative test: "+p.stderr)
    bad_ing=json.loads(p.stdout)
    bad_plan=dict(plan); bad_plan["source_sha256"]=[bad_ing["source"]["sha256"]]
    bad_plan["source_set_detail_map"]=[{"source_sha256":bad_ing["source"]["sha256"],"crop_region":"whole frame",
        "visible_detail":"should be rejected","graphic_role":"hero","provenance":"SAME_FRAME_CROP"}]
    (ws/"bad-plan.json").write_text(json.dumps(bad_plan),encoding="utf-8")
    q=run([sys.executable,str(PREF),"--bundle-dir",str(bundle),"--workspace",str(ws),"--plan","bad-plan.json",
           "--source-ingest",bad_ing["source_ingest"]["path"]])
    if q.returncode==0 or "STYLE_ONLY reference bytes cannot be PRODUCT_SOURCE" not in q.stdout:
        fail("style reference bytes crossed into PRODUCT_SOURCE")
print("OK chat-local cold-start preflight + two-image source set + source-role separation + creative-only scope")
