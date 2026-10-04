#!/usr/bin/env python3
"""Regenerate historical Stage 8C ChatGPT distribution evidence from its source commit."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"packages/velvetos/policy/reports/stage8c-chatgpt-distribution-consumers.json"
REPORT_REL=OUT.relative_to(ROOT).as_posix()
POLICY_REL="packages/velvetos/policy/policy-registry.json"
PROJECT_MANIFEST_REL="packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json"
CORE_PREFIX="packages/velvetos/chatgpt-project/"
INST_PREFIX="instances/velvet-factory/distribution/chatgpt-project/"
INSTANCE_REL="instances/velvet-factory/INSTANCE.json"
CHECKER_REL="scripts/check-chat-cold-start-preflight.py"
PREFLIGHT_REL="scripts/vf_chat_cold_start_preflight.py"
HELPER_REL="scripts/vf_project_distribution.py"

def require(v:bool,msg:str)->None:
    if not v: raise SystemExit(msg)

def csha(x:Any)->str:
    return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest()

def git_bytes(commit:str,rel:str)->bytes:
    return subprocess.check_output(["git","show",f"{commit}:{rel}"],cwd=ROOT)

def git_json(commit:str,rel:str)->dict[str,Any]:
    obj=json.loads(git_bytes(commit,rel).decode("utf-8-sig"))
    if not isinstance(obj,dict): raise SystemExit(f"{rel}@{commit} must be object")
    return obj

def git_text(commit:str,rel:str)->str:
    return git_bytes(commit,rel).decode("utf-8")

def source_commit()->str:
    p=subprocess.run(["git","log","-1","--format=%H","--",REPORT_REL],
                     cwd=ROOT,text=True,capture_output=True,encoding="utf-8",errors="replace")
    commits=[x.strip() for x in p.stdout.splitlines() if x.strip()]
    require(bool(commits),"cannot resolve Stage 8C ChatGPT receipt source commit")
    return commits[-1]

def tree_files(commit:str,prefix:str)->dict[str,bytes]:
    p=subprocess.run(["git","ls-tree","-r","--name-only",commit,"--",prefix.rstrip("/")],
                     cwd=ROOT,text=True,capture_output=True,encoding="utf-8",errors="replace")
    require(p.returncode==0,p.stderr.strip() or f"git ls-tree failed for {prefix}")
    out={}
    for rel in p.stdout.splitlines():
        rel=rel.strip().replace("\\","/")
        if rel.startswith(prefix):
            out[rel[len(prefix):]]=git_bytes(commit,rel)
    return out

def normalize_runtime_pin_manifest(obj:dict[str,Any])->dict[str,Any]:
    copy=json.loads(json.dumps(obj))
    for row in copy.get("chat_runtime") or []:
        if isinstance(row,dict) and row.get("repo_path")==PREFLIGHT_REL:
            row["sha256"]="__VF_CHAT_PREFLIGHT_SHA__"
    return copy

def normalize_project_manifest_pin(obj:dict[str,Any])->dict[str,Any]:
    copy=json.loads(json.dumps(obj))
    bundle=copy.get("chatgptProjectBundle") or {}
    if isinstance(bundle,dict) and "assetManifestSha256" in bundle:
        bundle["assetManifestSha256"]="__ASSET_MANIFEST_SHA__"
    return copy

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--prepared-against",required=True)
    ap.add_argument("--captured-at",required=True)
    ap.add_argument("--output",type=Path,default=OUT)
    a=ap.parse_args()
    require(re.fullmatch(r"[0-9a-f]{40}",a.prepared_against) is not None,"bad sha")
    src=source_commit()

    meta=git_json(src,INSTANCE_REL)
    surfaces=meta.get("surfaces") or {}
    require(surfaces.get("chatgptProject")=="distribution/chatgpt-project/LATEST.json",
            "instance chatgptProject surface drift")

    core_files=tree_files(src,CORE_PREFIX)
    inst_files=tree_files(src,INST_PREFIX)
    require(set(core_files)==set(inst_files),"instance distribution file set differs from Core compatibility bundle")
    mismatches=[rel for rel in sorted(core_files) if hashlib.sha256(core_files[rel]).digest()!=hashlib.sha256(inst_files[rel]).digest()]
    require(not mismatches,f"instance distribution byte parity mismatch: {mismatches[:5]}")

    core_non_pin_unchanged=[]
    for rel,raw in sorted(core_files.items()):
        if rel=="ASSET-MANIFEST-v6.6.4.json": continue
        try: before=git_bytes(a.prepared_against,CORE_PREFIX+rel)
        except subprocess.CalledProcessError:
            core_non_pin_unchanged.append(False); continue
        core_non_pin_unchanged.append(before==raw)
    require(all(core_non_pin_unchanged),"Core compatibility bundle changed outside the approved runtime pin update")

    current_asset=json.loads(core_files["ASSET-MANIFEST-v6.6.4.json"].decode("utf-8-sig"))
    baseline_asset=git_json(a.prepared_against,CORE_PREFIX+"ASSET-MANIFEST-v6.6.4.json")
    pin_only_asset_change=csha(normalize_runtime_pin_manifest(current_asset))==csha(normalize_runtime_pin_manifest(baseline_asset))
    require(pin_only_asset_change,"asset manifest changed beyond the approved chat runtime hash pin")
    runtime_rows=[row for row in current_asset.get("chat_runtime") or []
                  if isinstance(row,dict) and row.get("repo_path")==PREFLIGHT_REL]
    current_script_sha=hashlib.sha256(git_bytes(src,PREFLIGHT_REL)).hexdigest()
    require(len(runtime_rows)==1 and runtime_rows[0].get("sha256")==current_script_sha,
            "asset manifest does not pin the source-commit chat preflight bytes")

    current_project_manifest=git_json(src,PROJECT_MANIFEST_REL)
    baseline_project_manifest=git_json(a.prepared_against,PROJECT_MANIFEST_REL)
    project_manifest_pin_only_change=(
        csha(normalize_project_manifest_pin(current_project_manifest))
        == csha(normalize_project_manifest_pin(baseline_project_manifest))
    )
    require(project_manifest_pin_only_change,
            "Project Authority manifest changed beyond assetManifestSha256 trust-pin refresh")
    current_asset_sha=hashlib.sha256(core_files["ASSET-MANIFEST-v6.6.4.json"]).hexdigest()
    require(((current_project_manifest.get("chatgptProjectBundle") or {}).get("assetManifestSha256"))==current_asset_sha,
            "Project Authority manifest assetManifestSha256 does not bind source asset manifest")

    checker=git_text(src,CHECKER_REL); preflight=git_text(src,PREFLIGHT_REL); helper=git_text(src,HELPER_REL)
    require("resolve_distribution" in checker and 'instance_id="velvet-factory"' in checker,
            "cold-start checker is not bound to explicit instance distribution")
    require("chatgptProject" in helper and "resolve_surface" in helper,
            "distribution helper does not resolve instance surface")
    forbidden=('REVISION="6.6.4"','CONTRACT=6','VF-PROJECT-6.6.4-CHAT-RUNTIME-DEPENDENCY-CLOSURE','PROJECT-AUTHORITY-v6.6.4.txt')
    hits=[x for x in forbidden if x in preflight]
    require(not hits,f"generic cold-start preflight retains bundle literals: {hits}")
    require("bundle_contract" in preflight and 'latest_path=base/"LATEST.json"' in preflight,
            "cold-start preflight does not derive bundle identity dynamically")

    policy_now=csha(git_json(src,POLICY_REL))
    policy_base=csha(git_json(a.prepared_against,POLICY_REL))
    require(policy_now==policy_base,"external-effect policy changed")

    criteria={
      "instance_manifest_declares_chatgpt_project_distribution_surface":surfaces.get("chatgptProject")=="distribution/chatgpt-project/LATEST.json",
      "instance_distribution_file_set_matches_core_compatibility_bundle":set(core_files)==set(inst_files),
      "instance_distribution_is_byte_equal_to_core_compatibility_bundle":not mismatches,
      "core_compatibility_non_pin_files_are_unchanged":all(core_non_pin_unchanged),
      "core_compatibility_trust_updates_are_limited_to_chat_runtime_and_asset_manifest_pins":pin_only_asset_change and project_manifest_pin_only_change,
      "cold_start_checker_resolves_explicit_instance_distribution":"resolve_distribution" in checker and 'instance_id="velvet-factory"' in checker,
      "cold_start_preflight_has_no_hardcoded_vf_bundle_revision_or_authority_filename":not hits,
      "cold_start_preflight_derives_identity_from_bundle_manifest_or_latest":"bundle_contract" in preflight and 'latest_path=base/"LATEST.json"' in preflight,
      "generic_core_checkout_without_instance_distribution_selection_remains_fail_closed":"silent business defaults are forbidden" in git_text(src,"packages/velvetos/instance_resolver.py"),
      "external_effect_policy_registry_is_unchanged":policy_now==policy_base,
    }
    report={
      "schema":"velvetos.stage8c-chatgpt-distribution-consumers.v1",
      "stage":"8C_CHATGPT_DISTRIBUTION_CONSUMERS","behavior_change":True,
      "prepared_against_main_sha":a.prepared_against,"captured_at":a.captured_at,
      "purpose":"Create an instance-owned ChatGPT Project distribution snapshot and migrate cold-start machine consumers while retaining the Core bundle as rollback compatibility.",
      "distribution":{"surface":"chatgptProject","surface_pointer":"distribution/chatgpt-project/LATEST.json",
        "instance_root":"instances/velvet-factory/distribution/chatgpt-project",
        "core_compatibility_root":"packages/velvetos/chatgpt-project","file_count":len(inst_files),
        "byte_parity":not mismatches,"core_compatibility_non_pin_files_unchanged":all(core_non_pin_unchanged),
        "asset_manifest_pin_only_change":pin_only_asset_change,"project_manifest_pin_only_change":project_manifest_pin_only_change,
        "delete_authorized":False},
      "consumers":{"scripts/check-chat-cold-start-preflight.py":"instance-distribution-explicit-vf",
                   "scripts/vf_chat_cold_start_preflight.py":"generic-bundle-derived-identity"},
      "authority_baseline":{"policy_registry_canonical_sha256":policy_now,
                            "prepared_against_policy_registry_canonical_sha256":policy_base,
                            "unchanged":policy_now==policy_base},
      "acceptance_criteria":criteria,
      "repository_acceptance":"PASS" if all(criteria.values()) else "FAIL",
      "next_stage":"Stage 8C — ChatGPT distribution contract continuation" if all(criteria.values()) else None,
      "constraints":["Core compatibility bundle remains during rollback window","no legacy delete in this slice",
                     "remaining project-bundle consumers migrate after parity proof","no external-effect authority change"],
    }
    out=a.output if a.output.is_absolute() else ROOT/a.output
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(f"STAGE8C_CHATGPT_DISTRIBUTION_CONSUMERS acceptance={report['repository_acceptance']} criteria={sum(map(bool,criteria.values()))}/{len(criteria)} files={len(inst_files)} source={src}")
    return 0 if report["repository_acceptance"]=="PASS" else 1

if __name__=="__main__": raise SystemExit(main())
