#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json"


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def classify(text: str, manifest: dict) -> list[str]:
    probe = text.casefold()
    hits: list[str] = []
    for name, cfg in manifest["domains"].items():
        if any(str(hint).casefold() in probe for hint in cfg.get("hints", [])):
            hits.append(name)
    return hits or ["general_business"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve VelvetOS project request authority preflight")
    parser.add_argument("--domain", action="append", choices=None)
    parser.add_argument("--text")
    parser.add_argument("--manifest", help="Exact Creative Manifest for creative production evidence")
    parser.add_argument("--content-id")
    args = parser.parse_args()
    manifest = load_manifest()
    domains = args.domain or classify(args.text or "", manifest)
    unknown = [d for d in domains if d not in manifest["domains"]]
    if unknown:
        print(json.dumps({"project_preflight": "BLOCKED", "reason": "unknown_domain", "domains": unknown}, ensure_ascii=False, indent=2))
        return 2
    authorities = list(manifest["baselineAuthorities"])
    packs: list[str] = []
    hard_gates: list[str] = []
    for domain in domains:
        cfg = manifest["domains"][domain]
        authorities.extend(cfg.get("authorities", []))
        packs.extend(cfg.get("packs", []))
        hard_gates.extend(cfg.get("hardGates", []))
    authorities = list(dict.fromkeys(authorities))
    missing = [path for path in authorities if not (ROOT / path).is_file()]
    receipt = {
        "request_domain": domains,
        "authority_manifest_version": manifest["schemaVersion"],
        "baseline_authority": "FAIL" if missing else "PASS",
        "routed_packs": list(dict.fromkeys(packs)),
        "required_skills": [],
        "required_sources": authorities,
        "required_tools": [],
        "hard_gates": list(dict.fromkeys(hard_gates)),
        "current_evidence_state": "authority_paths_resolved",
        "project_preflight": "BLOCKED" if missing else "PASS",
        "missing_authority_paths": missing,
    }
    receipt["route_resolution"] = "BLOCKED" if missing else "PASS"
    creative = bool(set(domains) & {"creative_publication", "instagram_action"})
    if creative:
        from vf_publication_evidence import validate
        evidence = validate(ROOT, args.manifest or "", args.content_id or "", "production")
        receipt["production_evidence"] = evidence
        receipt["required_skills"] = ["velvet-creative-director", "velvet-brand-guardian", "velvet-hebrew-copy"]
        receipt["current_evidence_state"] = evidence["evidence_state"]
        receipt["project_preflight"] = "PASS" if evidence["ok"] and not missing else "BLOCKED"
    else:
        receipt["evidence_scope"] = "authority path resolution only; no action authorization"
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 2 if receipt["project_preflight"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())