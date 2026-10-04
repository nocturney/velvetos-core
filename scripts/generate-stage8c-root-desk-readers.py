#!/usr/bin/env python3
"""Generate Stage 8C root-desk direct-reader migration evidence."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"packages/velvetos/policy/reports/stage8c-root-desk-readers.json"
POLICY=ROOT/"packages/velvetos/policy/policy-registry.json"
ROOT_DESK=ROOT/".cursor/vf-desk.json"
CANON=ROOT/"instances/velvet-factory/.cursor/vf-desk.json"
DIRECT_READERS=(
    "scripts/check-vfmedia.py",
    "scripts/check-vf-offering.py",
    "scripts/vf_send_preflight.py",
)
TOOLS=("gmail","instagram","gemini","chatgpt","drive")

def load(p:Path)->dict[str,Any]:
    x=json.loads(p.read_text(encoding="utf-8-sig"))
    if not isinstance(x,dict): raise SystemExit(f"{p} must be object")
    return x

def require(v:bool,msg:str)->None:
    if not v: raise SystemExit(msg)

def sha(obj:Any)->str:
    raw=json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def git_json(commit:str,rel:str)->dict[str,Any]:
    raw=subprocess.check_output(["git","show",f"{commit}:{rel}"],cwd=ROOT)
    obj=json.loads(raw.decode("utf-8-sig"))
    if not isinstance(obj,dict): raise SystemExit(f"{rel}@{commit} must be object")
    return obj

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--prepared-against",required=True)
    ap.add_argument("--captured-at",required=True)
    ap.add_argument("--output",type=Path,default=OUT)
    a=ap.parse_args()
    require(re.fullmatch(r"[0-9a-f]{40}",a.prepared_against) is not None,"bad sha")
    root=load(ROOT_DESK); canon=load(CANON)
    base_root=git_json(a.prepared_against,".cursor/vf-desk.json")
    require(sha(root)==sha(base_root),"root desk changed during migration")

    parity={}
    for k in TOOLS:
        parity[k]=root.get("tools",{}).get(k)==canon.get("tools",{}).get(k)
    ro=next((x for x in root.get("seats",[]) if x.get("id")=="ops"),None)
    co=next((x for x in canon.get("seats",[]) if x.get("id")=="ops"),None)
    parity["opsSeat"]=ro==co
    require(all(parity.values()),f"canonical desk parity failed: {parity}")

    reader_scan={}
    for rel in DIRECT_READERS:
        text=(ROOT/rel).read_text(encoding="utf-8")
        reader_scan[rel]={
            "root_desk_literal_present": bool(
                re.search(r"(?<!instances/velvet-factory/)\.cursor/vf-desk\.json", text)
                or 'ROOT / ".cursor" / "vf-desk.json"' in text
            ),
            "instance_resolver_present": "instance_resolver" in text or "canonical_tool_desk" in text or "_canonical_tool_desk" in text,
        }
    require(all(not row["root_desk_literal_present"] for row in reader_scan.values()),
            "direct reader still names root desk")
    require(reader_scan["scripts/check-vfmedia.py"]["instance_resolver_present"],"vfmedia not resolver-bound")
    require(reader_scan["scripts/vf_send_preflight.py"]["instance_resolver_present"],"send preflight not resolver-bound")

    offering=(ROOT/"scripts/check-vf-offering.py").read_text(encoding="utf-8")
    require('".cursor/vf-desk.json"' not in offering,"offering still treats root desk as active authority")
    media=(ROOT/"scripts/check-vfmedia.py").read_text(encoding="utf-8")
    require("instances/velvet-factory/.cursor/vf-desk.json" in media,"vfmedia canonical desk reference missing")

    policy_now=sha(load(POLICY))
    policy_base=sha(git_json(a.prepared_against,"packages/velvetos/policy/policy-registry.json"))
    require(policy_now==policy_base,"policy registry changed")

    criteria={
      "root_desk_is_unchanged_and_retained_for_rollback": sha(root)==sha(base_root) and ROOT_DESK.is_file(),
      "canonical_instance_desk_has_exact_required_tool_subtree_parity": all(parity[k] for k in TOOLS),
      "canonical_instance_desk_has_exact_ops_seat_parity": parity["opsSeat"],
      "vfmedia_reads_tool_desk_through_instance_resolver": reader_scan["scripts/check-vfmedia.py"]["instance_resolver_present"],
      "send_preflight_reads_tool_desk_through_instance_resolver": reader_scan["scripts/vf_send_preflight.py"]["instance_resolver_present"],
      "offering_guard_no_longer_treats_root_desk_as_active_authority": '".cursor/vf-desk.json"' not in offering,
      "all_direct_readers_are_free_of_root_desk_literal": all(not row["root_desk_literal_present"] for row in reader_scan.values()),
      "external_effect_policy_registry_is_unchanged": policy_now==policy_base,
      "legacy_root_desk_delete_is_not_authorized": ROOT_DESK.is_file(),
    }
    report={
      "schema":"velvetos.stage8c-root-desk-readers.v1",
      "stage":"8C_ROOT_DESK_READERS",
      "behavior_change":True,
      "prepared_against_main_sha":a.prepared_against,
      "captured_at":a.captured_at,
      "purpose":"Migrate direct machine readers from root reference desk to canonical instance toolDesk while retaining root desk for rollback.",
      "root_desk":{
        "path":".cursor/vf-desk.json",
        "retained":ROOT_DESK.is_file(),
        "unchanged_from_prepared_against":sha(root)==sha(base_root),
        "delete_authorized":False,
        "rollback_window_open":True,
      },
      "canonical_tool_desk":{
        "path":"instances/velvet-factory/.cursor/vf-desk.json",
        "parity":parity,
      },
      "cutover_readers":reader_scan,
      "authority_baseline":{
        "policy_registry_canonical_sha256":policy_now,
        "prepared_against_policy_registry_canonical_sha256":policy_base,
        "unchanged":policy_now==policy_base,
      },
      "acceptance_criteria":criteria,
      "repository_acceptance":"PASS" if all(criteria.values()) else "FAIL",
      "next_stage":"Stage 8C — Remaining consumer domains" if all(criteria.values()) else None,
      "remaining_root_desk_domains":[
        "vfmem/vfgraft/vfharness catalog references",
        "root desk documentation/rules",
        "historical policy receipts/generators",
      ],
      "constraints":[
        "root desk remains during rollback window",
        "no external-effect authority change",
        "remaining references migrate independently",
      ],
    }
    out=a.output if a.output.is_absolute() else ROOT/a.output
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",encoding="utf-8",newline="\n") as fh:
        fh.write(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(f"STAGE8C_ROOT_DESK_READERS acceptance={report['repository_acceptance']} criteria={sum(map(bool,criteria.values()))}/{len(criteria)}")
    return 0 if report["repository_acceptance"]=="PASS" else 1

if __name__=="__main__": raise SystemExit(main())
