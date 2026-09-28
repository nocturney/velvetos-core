#!/usr/bin/env python3
"""Chat-local creative preflight for current-attachment publication work.

This gate exists for ChatGPT cold starts where GitHub can establish current authority
but the repo filesystem is not the same machine that owns the chat attachment bytes.
It authorizes creative production only; it never authorizes publication.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
from vf_media_integrity import inspect_media

CONTRACT=6
REVISION="6.6.5"
BUNDLE="VF-PROJECT-6.6.5-REEL-ROUTE"
MANIFEST_NAME="Velvet-Factory-ASSET-MANIFEST-v6.6.5.json"
AUTHORITY_NAMES=("Velvet-Factory-Project-Authority-v6.txt","PROJECT-AUTHORITY-v6.6.5.txt")
INSTRUCTION_NAMES=("Velvet-Factory-Project-Instructions-v6.6.5.txt","PROJECT-INSTRUCTIONS-v6.6.5.txt")
GUIDE_NAMES=("Velvet-Factory-PRODUCT-TRUTH-GUIDE-v1.txt","PRODUCT-TRUTH-GUIDE-v1.txt")
AXES=("product_to_frame","environment","light","depth","negative_space","hierarchy","typography","details","surfaces","accent")
PROVENANCE={"SAME_FRAME_CROP","ALTERNATE_VERIFIED_SOURCE"}
ROUTES={"LOCAL_FILE_OUTPUT","FETCHABLE_PROVIDER_RESULT","SAME_PROVIDER_NO_TEXT_FINAL"}

def digest(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def text_candidates(p:Path)->set[str]:
    b=p.read_bytes(); return {hashlib.sha256(b).hexdigest(),hashlib.sha256(b.replace(b"\r\n",b"\n")).hexdigest()}

def load(p:Path):
    return json.loads(p.read_text(encoding="utf-8-sig"))

def find(base:Path,names):
    for n in names:
        p=base/n
        if p.is_file(): return p
    raise ValueError("missing bundle file: "+"/".join(names))

def meaningful(v):
    return isinstance(v,str) and bool(v.strip()) and v.strip().upper() not in {"PENDING","UNPROVEN","TODO","N/A"}

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--bundle-dir",required=True)
    ap.add_argument("--workspace",required=True)
    ap.add_argument("--plan",required=True)
    ap.add_argument("--source-ingest",action="append",required=True)
    a=ap.parse_args()
    try:
        bundle=Path(a.bundle_dir).resolve(); ws=Path(a.workspace).resolve()
        manifest_path=find(bundle,(MANIFEST_NAME,"ASSET-MANIFEST-v6.6.5.json"))
        manifest=load(manifest_path)
        if (manifest.get("contract_version"),str(manifest.get("revision")),manifest.get("bundle_id"))!=(CONTRACT,REVISION,BUNDLE):
            raise ValueError("bundle identity mismatch")
        reel_meta=manifest.get("reel_route") or {}
        reel=find(bundle,(reel_meta.get("filename") or "REEL-ROUTE.md",))
        if reel_meta.get("filename")!="REEL-ROUTE.md" or reel_meta.get("sha256") not in text_candidates(reel):
            raise ValueError("Reel route hash mismatch")
        authority=find(bundle,AUTHORITY_NAMES); instructions=find(bundle,INSTRUCTION_NAMES)
        rows=manifest.get("assets") or []
        auth_rows=[x for x in rows if x.get("filename")=="Velvet-Factory-Project-Authority-v6.txt"]
        if len(auth_rows)!=1 or auth_rows[0].get("sha256") not in text_candidates(authority): raise ValueError("authority hash mismatch")
        ins=manifest.get("instructions") or {}
        if ins.get("sha256") not in text_candidates(instructions): raise ValueError("instructions hash mismatch")
        guide=find(bundle,GUIDE_NAMES); product_truth=manifest.get("product_truth") or {}
        guide_rows=[x for x in rows if x.get("filename")==product_truth.get("guide")]
        if len(guide_rows)!=1 or guide_rows[0].get("sha256") not in text_candidates(guide): raise ValueError("Product Truth guide mismatch")
        current=manifest.get("current_references") or {}
        if set(current)!={"broad_visual","editorial_layout","current_direction","multi_source_composition"}: raise ValueError("four aesthetic reference bindings required")
        byname={x.get("filename"):x for x in rows}
        refs=[]
        for name in current.values():
            p=find(bundle,(name,))
            row=byname.get(name) or {}
            if digest(p)!=row.get("sha256"): raise ValueError("reference hash mismatch: "+name)
            inspect_media(p,"aesthetic reference")
            refs.append({"role":"STYLE_ONLY","path":str(p),"sha256":row["sha256"]})
        source_refs=[]; ingest_refs=[]; source_shas=set()
        for raw in a.source_ingest:
            rp=Path(raw); rp=rp if rp.is_absolute() else ws/rp; rp=rp.resolve()
            try: rp.relative_to(ws)
            except ValueError as e: raise ValueError("source ingest receipt escapes workspace") from e
            rec=load(rp)
            if rec.get("version")!=1 or rec.get("ingest_method")!="LOCAL_EXACT_COPY" or rec.get("exact_bytes_copied") is not True:
                raise ValueError("invalid source ingest receipt")
            o=rec.get("origin") or {}; m=rec.get("materialized") or {}
            if o.get("kind") not in {"CHAT_ATTACHMENT_FILE","LOCAL_USER_FILE","WORKSPACE_EXISTING"}: raise ValueError("invalid ingest origin")
            if o.get("sha256")!=m.get("sha256"): raise ValueError("ingest is not exact-byte")
            sp=(ws/Path(m.get("path",""))).resolve()
            try: sp.relative_to(ws)
            except ValueError as e: raise ValueError("materialized source escapes workspace") from e
            if not sp.is_file() or digest(sp)!=m.get("sha256") or sp.stat().st_size!=m.get("bytes"): raise ValueError("materialized source mismatch")
            inspect_media(sp,"product source",source=True)
            source_refs.append({"role":"PRODUCT_SOURCE","path":m["path"],"sha256":m["sha256"]})
            ingest_refs.append({"path":str(rp.relative_to(ws)).replace("\\","/"),"sha256":digest(rp)})
            source_shas.add(m["sha256"])
        ref_shas={x["sha256"] for x in refs}
        if source_shas & ref_shas:
            raise ValueError("STYLE_ONLY reference bytes cannot be PRODUCT_SOURCE")
        planp=Path(a.plan); planp=planp if planp.is_absolute() else ws/planp; plan=load(planp.resolve())
        if plan.get("public_intent") not in {"showcase","commercial"}: raise ValueError("public_intent missing")
        if set(plan.get("source_sha256") or [])!=source_shas: raise ValueError("plan source identities mismatch")
        if set(plan.get("reference_sha256") or [])!=ref_shas: raise ValueError("plan reference identities mismatch")
        truth=plan.get("product_truth") or {}
        if not truth.get("protected_regions") or not meaningful(truth.get("observations")): raise ValueError("Product Truth plan incomplete")
        dec=plan.get("reference_decomposition") or {}
        if any(not meaningful(dec.get(x)) for x in AXES): raise ValueError("reference decomposition incomplete")
        detail=plan.get("source_set_detail_map") or []
        if not isinstance(detail,list) or not detail: raise ValueError("source-set detail map missing")
        for item in detail:
            if item.get("source_sha256") not in source_shas or item.get("provenance") not in PROVENANCE:
                raise ValueError("source-set detail map provenance mismatch")
            if not all(meaningful(item.get(k)) for k in ("crop_region","visible_detail","graphic_role")):
                raise ValueError("source-set detail map incomplete")
        route=plan.get("creative_output_route")
        if route not in ROUTES: raise ValueError("creative output route not materializable/declared")
        if plan.get("deterministic_overlay_expected") is True and route=="SAME_PROVIDER_NO_TEXT_FINAL":
            raise ValueError("NO_TEXT route conflicts with deterministic overlay plan")
        out={"project_preflight":"PASS","creative_execution_authorized":True,"delivery_authorized":False,
             "mode":"CHAT_LOCAL_ATTACHMENT","contract":CONTRACT,"revision":REVISION,"bundle_id":BUNDLE,
             "sources":source_refs,"source_ingest":ingest_refs,"references":refs,
             "product_truth_guide_sha256":guide_rows[0]["sha256"],"creative_output_route":route}
        print(json.dumps(out,ensure_ascii=False,indent=2)); return 0
    except Exception as e:
        print(json.dumps({"project_preflight":"BLOCKED","creative_execution_authorized":False,"delivery_authorized":False,
                          "mode":"CHAT_LOCAL_ATTACHMENT","reason":str(e)[:1000]},ensure_ascii=False,indent=2))
        return 2
if __name__=="__main__": raise SystemExit(main())
