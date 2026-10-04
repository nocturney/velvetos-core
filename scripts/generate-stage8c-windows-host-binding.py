#!/usr/bin/env python3
"""Generate Stage 8C Windows host-binding separation evidence."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"packages/velvetos/policy/reports/stage8c-windows-host-binding.json"
POLICY=ROOT/"packages/velvetos/policy/policy-registry.json"
CONTRACT=ROOT/"packages/velvetos/WINDOWS-PATH-CONTRACT.md"
BINDING=ROOT/"instances/velvet-factory/instance/windows-host-binding.json"
MANIFEST=ROOT/"instances/velvet-factory/INSTANCE.json"
RENDER_HOSTS=ROOT/"packages/vfmcp/RENDER-HOSTS.json"
OPENPOST=ROOT/"packages/vfigos/OPENPOST.json"

SCOPED_CORE=(
    "packages/velvetos/WINDOWS-PATH-CONTRACT.md",
    ".cursor/rules/windows-d-paths.mdc",
    "scripts/bootstrap-edge-host-windows.ps1",
    "scripts/bootstrap-speech-host-windows.ps1",
    "scripts/bootstrap-manim-host-windows.ps1",
    "scripts/bootstrap-media-host-windows.ps1",
    "packages/vfmem/scripts/vf_cognee.py",
    "packages/vfmem/scripts/vf_cognee_runtime.py",
)
FORBIDDEN_CORE=(r"D:\Velvet","sderot-windows","Sderot Windows",r"C:\Users\Chris")

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

    binding=load(BINDING)
    manifest=load(MANIFEST)
    env=binding.get("environment") or {}
    require(binding.get("schema")=="velvetos.instance-windows-host-binding.v1","binding schema drift")
    require(binding.get("instanceId")=="velvet-factory","binding instance drift")
    require(binding.get("platform")=="Windows","binding platform drift")
    require(binding.get("hostId")=="sderot-windows","binding host id drift")
    require(binding.get("machineScopeRequired") is True,"binding machine scope drift")
    require(binding.get("fallbackToUserProfile") is False,"binding fallback drift")
    require(env=={
        "VELVET_ROOT":r"D:\Velvet",
        "VELVETOS_REPO_ROOT":r"D:\Velvet\Repos\velvetos-core",
        "VELVETOS_RUNTIME_ROOT":r"D:\Velvet\Runtime\VelvetOS",
        "VELVETOS_STATE_ROOT":r"D:\Velvet\State\VelvetOS",
        "VELVETOS_HOST_ID":"sderot-windows",
    },"binding environment drift")
    require((manifest.get("surfaces") or {}).get("windowsHostBinding")=="instance/windows-host-binding.json",
            "instance manifest host-binding surface drift")

    leaks:dict[str,list[str]]={}
    for rel in SCOPED_CORE:
        text=(ROOT/rel).read_text(encoding="utf-8")
        hits=[token for token in FORBIDDEN_CORE if token in text]
        leaks[rel]=hits
        require(not hits,f"instance/private value leaked into generic Core consumer {rel}: {hits}")

    contract=CONTRACT.read_text(encoding="utf-8")
    for needle in (
        "VELVET_ROOT=<absolute Windows root for VelvetOS work>",
        "VELVETOS_HOST_ID=<explicit host identifier>",
        "instance/private deployment bindings",
        "fallbacks are closed (fail closed)",
    ):
        require(needle in contract,f"generic Windows contract missing {needle}")

    for rel in (
        "scripts/bootstrap-edge-host-windows.ps1",
        "scripts/bootstrap-speech-host-windows.ps1",
        "scripts/bootstrap-manim-host-windows.ps1",
    ):
        text=(ROOT/rel).read_text(encoding="utf-8")
        require("VELVETOS_HOST_ID" in text,f"{rel} does not require explicit host id")
        require("GetEnvironmentVariable" in text,f"{rel} does not resolve machine env")
        require("The legacy user-profile fallback is closed" in text,f"{rel} fail-closed message drift")

    render_now=load(RENDER_HOSTS)
    render_base=git_json(a.prepared_against,"packages/vfmcp/RENDER-HOSTS.json")
    openpost_now=load(OPENPOST)
    openpost_base=git_json(a.prepared_against,"packages/vfigos/OPENPOST.json")
    require(csha(render_now)==csha(render_base),"render-host registry changed during binding split")
    require(csha(openpost_now)==csha(openpost_base),"OpenPost registry changed during binding split")

    windows=((render_now.get("hosts") or {}).get(env["VELVETOS_HOST_ID"]) or {})
    require(windows.get("repoPath")==r"%VELVETOS_REPO_ROOT%","render host repo path drift")
    require(windows.get("localState")==r"%VELVETOS_STATE_ROOT%\edge-host.json","render host state path drift")
    persistence=((openpost_now.get("runtime") or {}).get("persistence") or {})
    expected_openpost=env["VELVET_ROOT"]+r"\Services\OpenPost\staging\start-openpost-staging.ps1"
    require(persistence.get("startScript")==expected_openpost,"OpenPost path does not match instance service lane")

    policy_now=csha(load(POLICY))
    policy_base=csha(git_json(a.prepared_against,"packages/velvetos/policy/policy-registry.json"))
    require(policy_now==policy_base,"external-effect policy changed")

    criteria={
      "generic_core_windows_contract_has_no_instance_host_or_absolute_root_values":
          all(not hits for hits in leaks.values()),
      "canonical_instance_declares_windows_host_binding_surface":
          (manifest.get("surfaces") or {}).get("windowsHostBinding")=="instance/windows-host-binding.json",
      "instance_windows_binding_owns_current_host_identity_and_machine_paths":
          binding.get("hostId")=="sderot-windows" and env.get("VELVET_ROOT")==r"D:\Velvet",
      "windows_bootstraps_require_explicit_host_id_without_hardcoded_identity":
          all("VELVETOS_HOST_ID" in (ROOT/rel).read_text(encoding="utf-8")
              and "sderot-windows" not in (ROOT/rel).read_text(encoding="utf-8")
              for rel in (
                  "scripts/bootstrap-edge-host-windows.ps1",
                  "scripts/bootstrap-speech-host-windows.ps1",
                  "scripts/bootstrap-manim-host-windows.ps1",
              )),
      "windows_path_consumers_keep_fail_closed_variable_driven_behavior":
          all("The legacy user-profile fallback is closed" in (ROOT/rel).read_text(encoding="utf-8")
              for rel in (
                  "scripts/bootstrap-edge-host-windows.ps1",
                  "scripts/bootstrap-speech-host-windows.ps1",
                  "scripts/bootstrap-manim-host-windows.ps1",
              )),
      "vfmem_windows_consumers_remain_generic_and_variable_driven":
          not leaks["packages/vfmem/scripts/vf_cognee.py"]
          and not leaks["packages/vfmem/scripts/vf_cognee_runtime.py"],
      "operational_host_and_openpost_registries_are_unchanged_and_match_binding":
          csha(render_now)==csha(render_base)
          and csha(openpost_now)==csha(openpost_base)
          and windows.get("repoPath")==r"%VELVETOS_REPO_ROOT%"
          and persistence.get("startScript")==expected_openpost,
      "external_effect_policy_registry_is_unchanged": policy_now==policy_base,
    }
    report={
      "schema":"velvetos.stage8c-windows-host-binding.v1",
      "stage":"8C_WINDOWS_HOST_BINDING",
      "behavior_change":True,
      "prepared_against_main_sha":a.prepared_against,
      "captured_at":a.captured_at,
      "purpose":"Separate generic Windows path semantics from the Velvet Factory private Windows host identity and absolute machine paths.",
      "binding":{
        "path":"instances/velvet-factory/instance/windows-host-binding.json",
        "surface":"windowsHostBinding",
        "host_id":binding.get("hostId"),
        "machine_scope_required":binding.get("machineScopeRequired"),
        "fallback_to_user_profile":binding.get("fallbackToUserProfile"),
        "environment_keys":sorted(env),
        "lane_count":len(binding.get("lanes") or {}),
      },
      "generic_core":{
        "contract":"packages/velvetos/WINDOWS-PATH-CONTRACT.md",
        "scoped_files":list(SCOPED_CORE),
        "private_value_hits":leaks,
      },
      "operational_registry_baseline":{
        "render_hosts_unchanged":csha(render_now)==csha(render_base),
        "openpost_unchanged":csha(openpost_now)==csha(openpost_base),
        "host_registry_id":env["VELVETOS_HOST_ID"],
      },
      "authority_baseline":{
        "policy_registry_canonical_sha256":policy_now,
        "prepared_against_policy_registry_canonical_sha256":policy_base,
        "unchanged":policy_now==policy_base,
      },
      "acceptance_criteria":criteria,
      "repository_acceptance":"PASS" if all(criteria.values()) else "FAIL",
      "next_stage":"Stage 8C complete" if all(criteria.values()) else None,
      "remaining_domains":[],
      "constraints":[
        "host registry remains operational authority",
        "instance binding owns concrete deployment values",
        "machine environment must be provisioned explicitly",
        "no user-profile fallback",
        "no external-effect authority change",
      ],
    }
    out=a.output if a.output.is_absolute() else ROOT/a.output
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",encoding="utf-8",newline="\n") as fh:
        fh.write(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(f"STAGE8C_WINDOWS_HOST_BINDING acceptance={report['repository_acceptance']} criteria={sum(map(bool,criteria.values()))}/{len(criteria)} lanes={report['binding']['lane_count']}")
    return 0 if report["repository_acceptance"]=="PASS" else 1

if __name__=="__main__": raise SystemExit(main())
