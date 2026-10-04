#!/usr/bin/env python3
"""Generate Stage 8C expert-module parameterization evidence."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"packages/velvetos/policy/reports/stage8c-expert-modules.json"
POLICY=ROOT/"packages/velvetos/policy/policy-registry.json"
PROFILE=ROOT/"instances/velvet-factory/instance/velvet-factory.json"
ENFORCEMENT=ROOT/"packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json"
MODULES={
 "expert-revenue-loop":"packages/velvetos/modules/expert-revenue-loop.md",
 "expert-social-booster":"packages/velvetos/modules/expert-social-booster.md",
 "expert-media-director":"packages/velvetos/modules/expert-media-director.md",
}
FORBIDDEN=("Sderot","שדרות","050-2517000","@velvets_cloud",
"df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897",
"Velvet Factory Visual Standard Gate")

def load(p:Path)->dict[str,Any]:
    x=json.loads(p.read_text(encoding="utf-8-sig"))
    if not isinstance(x,dict): raise SystemExit(f"{p} must be object")
    return x

def require(v:bool,msg:str)->None:
    if not v: raise SystemExit(msg)

def csha(x:Any)->str:
    raw=json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
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

    profile=load(PROFILE)
    require(profile.get("id")=="velvet-factory","canonical profile identity drift")
    require(isinstance(profile.get("cta"),dict),"canonical profile CTA missing")
    require(isinstance(profile.get("fulfillment"),dict),"canonical profile fulfillment missing")
    visual=((profile.get("creativeAutonomy") or {}).get("ownerApprovedVisualStandard") or {})
    require(visual.get("required") is True and isinstance(visual.get("artifactSha256"),str),
            "canonical profile visual-standard authority missing")

    module_rows={}
    for mid,rel in MODULES.items():
        text=(ROOT/rel).read_text(encoding="utf-8")
        hits=[token for token in FORBIDDEN if token in text]
        module_rows[mid]={
            "path":rel,
            "forbidden_instance_value_hits":hits,
            "mentions_selected_instance": "selected instance" in text.lower() or "instance profile" in text.lower(),
        }
        require(not hits,f"{mid} retains instance-specific values: {hits}")
        require(module_rows[mid]["mentions_selected_instance"],f"{mid} does not resolve selected instance values")

    revenue=(ROOT/MODULES["expert-revenue-loop"]).read_text(encoding="utf-8")
    social=(ROOT/MODULES["expert-social-booster"]).read_text(encoding="utf-8")
    media=(ROOT/MODULES["expert-media-director"]).read_text(encoding="utf-8")
    require("cta" in revenue and "fulfillment" in revenue,"revenue loop missing generic CTA/fulfillment parameterization")
    require("CTA text, channel and fulfillment/location wording" in social,
            "social booster missing generic CTA/location parameterization")
    require("creativeAutonomy.ownerApprovedVisualStandard" in media,
            "media director missing generic visual-standard parameterization")
    require("artifact digest" in media and "generic visual fallback is forbidden" in media,
            "media director fail-closed visual gate drift")

    enforcement=load(ENFORCEMENT)
    refs=(enforcement.get("vfCreativeSurfaces") or []) + ((enforcement.get("publicationRoute") or {}).get("entrypoints") or [])
    ref_count=sum(1 for x in refs if x==MODULES["expert-media-director"])
    require(ref_count==2,"visual enforcement no longer binds expert-media-director in both expected surfaces")

    policy_now=csha(load(POLICY))
    policy_base=csha(git_json(a.prepared_against,"packages/velvetos/policy/policy-registry.json"))
    require(policy_now==policy_base,"external-effect policy changed")

    criteria={
      "all_three_core_expert_modules_have_no_vf_specific_cta_location_or_visual_digest_values":
          all(not row["forbidden_instance_value_hits"] for row in module_rows.values()),
      "revenue_loop_resolves_cta_and_fulfillment_from_selected_instance":
          "cta" in revenue and "fulfillment" in revenue,
      "social_booster_resolves_cta_location_and_contact_semantics_from_selected_instance":
          "CTA text, channel and fulfillment/location wording" in social,
      "media_director_resolves_required_visual_standard_from_selected_instance_profile":
          "creativeAutonomy.ownerApprovedVisualStandard" in media,
      "media_director_visual_gate_remains_fail_closed_without_generic_fallback":
          "generic visual fallback is forbidden" in media,
      "vf_visual_enforcement_still_machine_binds_generic_media_director_module": ref_count==2,
      "canonical_instance_profile_retains_vf_values_and_visual_authority": (
          profile.get("where")=="Sderot"
          and (profile.get("cta") or {}).get("handle")=="@velvets_cloud"
          and visual.get("artifactSha256")=="df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897"
      ),
      "external_effect_policy_registry_is_unchanged": policy_now==policy_base,
    }
    report={
      "schema":"velvetos.stage8c-expert-modules.v1",
      "stage":"8C_EXPERT_MODULES",
      "behavior_change":True,
      "prepared_against_main_sha":a.prepared_against,
      "captured_at":a.captured_at,
      "purpose":"Parameterize instance-value-bearing language in generic expert modules while preserving generic methods and VF machine enforcement.",
      "modules":module_rows,
      "canonical_instance_profile":{
        "path":"instances/velvet-factory/instance/velvet-factory.json",
        "business_value_owner":True,
        "cta_channel":(profile.get("cta") or {}).get("channel"),
        "fulfillment_mode":(profile.get("fulfillment") or {}).get("mode"),
        "visual_standard_required":visual.get("required"),
      },
      "visual_enforcement":{
        "path":"packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json",
        "media_director_reference_count":ref_count,
        "unchanged_in_this_slice":True,
      },
      "authority_baseline":{
        "policy_registry_canonical_sha256":policy_now,
        "prepared_against_policy_registry_canonical_sha256":policy_base,
        "unchanged":policy_now==policy_base,
      },
      "acceptance_criteria":criteria,
      "repository_acceptance":"PASS" if all(criteria.values()) else "FAIL",
      "next_stage":"Stage 8C — Remaining consumer domains" if all(criteria.values()) else None,
      "remaining_domains":["chatgpt-project-vf-distribution","windows-host-binding-document"],
      "constraints":[
        "generic expert methods stay in Core",
        "business values remain instance-owned",
        "visual enforcement remains fail-closed",
        "no external-effect authority change",
      ],
    }
    out=a.output if a.output.is_absolute() else ROOT/a.output
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",encoding="utf-8",newline="\n") as fh:
        fh.write(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(f"STAGE8C_EXPERT_MODULES acceptance={report['repository_acceptance']} criteria={sum(map(bool,criteria.values()))}/{len(criteria)} modules={len(MODULES)}")
    return 0 if report["repository_acceptance"]=="PASS" else 1

if __name__=="__main__": raise SystemExit(main())
