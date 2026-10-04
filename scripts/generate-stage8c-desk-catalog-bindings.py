#!/usr/bin/env python3
"""Generate Stage 8C desk catalog/graph binding migration evidence."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"packages/velvetos/policy/reports/stage8c-desk-catalog-bindings.json"
POLICY=ROOT/"packages/velvetos/policy/policy-registry.json"
ROOT_DESK=ROOT/".cursor/vf-desk.json"
CANON="instances/velvet-factory/.cursor/vf-desk.json"
TARGETS=(
 "packages/vfmem/catalog.json",
 "packages/vfgraft/graph.json",
 "packages/vfgraft/graph/blast.md",
 "packages/vfgraft/graph/desk.md",
 "packages/vfgraft/graph/grok-bot.md",
 "packages/vfgraft/graph/laws.md",
 "packages/vfgraft/graph/pipeline.md",
 "packages/vfgraft/graph/tools.md",
 "packages/vfharness/layers.json",
 "packages/vfharness/playbooks/domain-glossary.md",
 "packages/vfharness/playbooks/skill-first.md",
)
EXPECTED_COUNTS={
 "packages/vfmem/catalog.json":3,
 "packages/vfgraft/graph.json":6,
 "packages/vfgraft/graph/blast.md":1,
 "packages/vfgraft/graph/desk.md":1,
 "packages/vfgraft/graph/grok-bot.md":1,
 "packages/vfgraft/graph/laws.md":1,
 "packages/vfgraft/graph/pipeline.md":1,
 "packages/vfgraft/graph/tools.md":1,
 "packages/vfharness/layers.json":1,
 "packages/vfharness/playbooks/domain-glossary.md":1,
 "packages/vfharness/playbooks/skill-first.md":1,
}
def load(p:Path)->dict[str,Any]:
    x=json.loads(p.read_text(encoding="utf-8-sig"))
    if not isinstance(x,dict): raise SystemExit(f"{p} must be object")
    return x
def require(v:bool,msg:str)->None:
    if not v: raise SystemExit(msg)
def sha(obj:Any)->str:
    return hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def git_json(commit:str,rel:str)->dict[str,Any]:
    raw=subprocess.check_output(["git","show",f"{commit}:{rel}"],cwd=ROOT)
    x=json.loads(raw.decode("utf-8-sig"))
    if not isinstance(x,dict): raise SystemExit(f"{rel}@{commit} must be object")
    return x
def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--prepared-against",required=True)
    ap.add_argument("--captured-at",required=True)
    ap.add_argument("--output",type=Path,default=OUT)
    a=ap.parse_args()
    require(re.fullmatch(r"[0-9a-f]{40}",a.prepared_against) is not None,"bad sha")
    root=load(ROOT_DESK)
    base_root=git_json(a.prepared_against,".cursor/vf-desk.json")
    require(sha(root)==sha(base_root),"root desk changed")

    counts={}
    root_only={}
    pattern=re.compile(r"(?<!instances/velvet-factory/)\.cursor/vf-desk\.json")
    for rel in TARGETS:
        text=(ROOT/rel).read_text(encoding="utf-8")
        counts[rel]=text.count(CANON)
        root_only[rel]=len(pattern.findall(text))
    require(counts==EXPECTED_COUNTS,f"canonical binding counts drift: {counts}")
    require(all(v==0 for v in root_only.values()),f"root-only bindings remain: {root_only}")

    policy_now=sha(load(POLICY))
    policy_base=sha(git_json(a.prepared_against,"packages/velvetos/policy/policy-registry.json"))
    require(policy_now==policy_base,"policy changed")
    criteria={
      "all_target_catalog_graph_bindings_point_to_canonical_instance_desk": counts==EXPECTED_COUNTS,
      "no_root_only_desk_binding_remains_in_target_packages": all(v==0 for v in root_only.values()),
      "vfmem_binding_count_is_exact": counts["packages/vfmem/catalog.json"]==3,
      "vfgraft_binding_count_is_exact": sum(counts[k] for k in counts if k.startswith("packages/vfgraft/"))==12,
      "vfharness_binding_count_is_exact": sum(counts[k] for k in counts if k.startswith("packages/vfharness/"))==3,
      "root_desk_remains_unchanged_for_rollback": sha(root)==sha(base_root) and ROOT_DESK.is_file(),
      "external_effect_policy_registry_is_unchanged": policy_now==policy_base,
      "legacy_root_desk_delete_is_not_authorized": ROOT_DESK.is_file(),
    }
    report={
      "schema":"velvetos.stage8c-desk-catalog-bindings.v1",
      "stage":"8C_DESK_CATALOG_BINDINGS",
      "behavior_change":True,
      "prepared_against_main_sha":a.prepared_against,
      "captured_at":a.captured_at,
      "purpose":"Migrate vfmem/vfgraft/vfharness desk source bindings to canonical instance desk without deleting the root rollback desk.",
      "canonical_path":CANON,
      "targets":{rel:{"canonical_binding_count":counts[rel],"root_only_binding_count":root_only[rel]} for rel in TARGETS},
      "total_canonical_bindings":sum(counts.values()),
      "root_desk":{"retained":ROOT_DESK.is_file(),"unchanged_from_prepared_against":sha(root)==sha(base_root),"delete_authorized":False},
      "authority_baseline":{"unchanged":policy_now==policy_base,"policy_registry_canonical_sha256":policy_now,"prepared_against_policy_registry_canonical_sha256":policy_base},
      "acceptance_criteria":criteria,
      "repository_acceptance":"PASS" if all(criteria.values()) else "FAIL",
      "next_stage":"Stage 8C — Remaining consumer domains" if all(criteria.values()) else None,
      "remaining_domains":["root desk rules/documentation","Living Studio embedded business rules","Control API/fleet projection","ChatGPT project distribution","expert-module instance values","Windows host binding"],
    }
    out=a.output if a.output.is_absolute() else ROOT/a.output
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",encoding="utf-8",newline="\n") as fh: fh.write(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(f"STAGE8C_DESK_CATALOG_BINDINGS acceptance={report['repository_acceptance']} criteria={sum(map(bool,criteria.values()))}/{len(criteria)} bindings={sum(counts.values())}")
    return 0 if report["repository_acceptance"]=="PASS" else 1
if __name__=="__main__": raise SystemExit(main())
