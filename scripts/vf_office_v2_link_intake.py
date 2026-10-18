#!/usr/bin/env python3
"""Durable GitHub repo-link intake for the Office v2 Phase 2 candidate registry (#595 AC5).

Repo-only and offline: no network calls. An incoming GitHub URL is normalized,
deduplicated against the ONE canonical candidate registry, and either appended
as a DISCOVERED / BENCHMARK_REQUIRED candidate with a NEEDS_SOURCE_REVIEW
evaluation_route, or reported as a duplicate. Every outcome (registered,
duplicate, invalid, write failure) produces a visible receipt so a link can
never silently disappear. Historical rows are never modified, and no
promotion, install, credential or runtime authority is granted.

Usage:
  python3 scripts/vf_office_v2_link_intake.py <github-url> [--name NAME]
      [--provenance-class CLASS] [--requested-by REF] [--registry PATH]
      [--receipt-dir DIR] [--dry-run]
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P2 = ROOT / "docs" / "implementation" / "office-v2" / "phase2"
REGISTRY = P2 / "candidate-registry-v0.json"
SCHEMA = P2 / "candidate-registry.schema.json"
RECEIPT_DIR = P2 / "link-intake-receipts"
OWNER_ISSUE = "https://github.com/nocturney/velvetos-core/issues/595"
RECEIPT_SCHEMA = "velvetos.office-v2.phase2-link-intake-receipt.v0"
INTAKE_LANE = "repo-link-intake-triage"
DEFAULT_PROVENANCE = "OWNER_LINK_INTAKE"
# Links to this repository (issues/PRs) are provenance, not candidate identity.
SELF_REPOS = {("nocturney", "velvetos-core")}

_GH = re.compile(
    r"^(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))/([A-Za-z0-9._-]+?)(?:\.git)?(?:[/?#].*)?$",
    re.IGNORECASE,
)


class IntakeError(ValueError):
    pass


def parse_repo(url: str) -> tuple[str, str] | None:
    """Return (owner, repo) lowercase, ignoring case, `.git`, trailing slashes and sub-paths."""
    if not isinstance(url, str):
        return None
    m = _GH.match(url.strip())
    if not m:
        return None
    owner, repo = m.group(1).lower(), m.group(2).lower()
    if repo.endswith(".git"):
        repo = repo[:-4]
    if not repo or repo in {".", ".."}:
        return None
    return owner, repo


def canonical_url(owner: str, repo: str) -> str:
    return f"https://github.com/{owner}/{repo}"


def load_registry(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8")
    return json.loads(raw), raw


def dump_registry(data: dict) -> str:
    # Matches the committed formatting exactly (indent=2, UTF-8, trailing newline).
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def find_duplicates(items: list[dict], key: tuple[str, str]) -> list[str]:
    hits = []
    for item in items:
        for ref in item.get("evidence_refs") or []:
            parsed = parse_repo(ref)
            if parsed and parsed not in SELF_REPOS and parsed == key:
                hits.append(item["candidate_id"])
                break
    return hits


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def build_candidate(items: list[dict], owner: str, repo: str, *, name: str | None,
                    provenance_class: str, requested_by: str) -> dict:
    base = f"candidate-intake-{_slug(owner)}-{_slug(repo)}"
    existing = {i["candidate_id"] for i in items}
    cid, n = base, 2
    while cid in existing:
        cid, n = f"{base}-{n}", n + 1
    url = canonical_url(owner, repo)
    next_action = ("Source review: read upstream README/license/release state, map to an existing "
                   "Phase 2 lane or record an evidence-backed defer/reject; no install or runtime.")
    refs = [url, OWNER_ISSUE]
    if requested_by and requested_by not in refs:
        refs.append(requested_by)
    return {
        "candidate_id": cid,
        "source_item_id": None,
        "name": name or f"{owner}/{repo}",
        "category": "UNTRIAGED_REPO_INTAKE",
        "provenance_class": provenance_class,
        "lifecycle_state": "DISCOVERED",
        "decision_verdict": "BENCHMARK_REQUIRED",
        "verdict_reason": "Recorded by durable link intake; not yet source-reviewed. No capability, rights or runtime claim is made.",
        "runtime_verification": "NOT_RUN",
        "authority_role": "NONE",
        "capability_tags": ["untriaged"],
        "platform_constraints": ["Do not install, run or grant credentials until source review and admission gates pass."],
        "shortlist_lanes": [INTAKE_LANE],
        "evidence_refs": refs,
        "notes": ["Intake into the existing registry only; no installation, credential grant, scheduler, network exposure or production effect."],
        "original_office_v2_verdict": None,
        "comparison_review": {
            "policy": "COMPETITOR_NEUTRAL_ADMISSION_V1",
            "eligibility": "OPEN_FOR_COMPARISON",
            "variants": ["full_replacement", "component_replacement", "hybrid"],
            "evidence_status": "RESEARCH_ONLY",
            "next_action": next_action,
            "rationale": "Incoming link preserved for competitor-neutral comparison; replacement scope is undetermined until source review.",
            "decision_evidence_refs": [],
        },
        "evaluation_route": {
            "workstream": INTAKE_LANE,
            "owner_ref": OWNER_ISSUE,
            "phase": "Office v2 Phase 2 source and capability evaluation",
            "status": "NEEDS_SOURCE_REVIEW",
            "next_gate": next_action,
            "unlock_condition": "Source review recorded with evidence, lane assigned or evidence-backed exit verdict; admission gates unchanged.",
            "evidence_refs": [url, OWNER_ISSUE],
        },
    }


def validate_entry(entry: dict, schema: dict) -> list[str]:
    """Minimal offline validator for the registry entry schema (no jsonschema dependency)."""
    problems: list[str] = []

    def check(value, spec, path):
        if "const" in spec and value != spec["const"]:
            problems.append(f"{path}: expected const {spec['const']}")
        if "enum" in spec and value not in spec["enum"]:
            problems.append(f"{path}: {value!r} not in enum")
        types = spec.get("type")
        if types:
            types = types if isinstance(types, list) else [types]
            ok = any({"string": isinstance(value, str), "null": value is None,
                      "array": isinstance(value, list), "object": isinstance(value, dict)}.get(t, True)
                     for t in types)
            if not ok:
                problems.append(f"{path}: wrong type")
                return
        if isinstance(value, str) and len(value) < spec.get("minLength", 0):
            problems.append(f"{path}: too short")
        if isinstance(value, list):
            if len(value) < spec.get("minItems", 0):
                problems.append(f"{path}: too few items")
            if spec.get("uniqueItems") and len(value) != len({json.dumps(v, sort_keys=True) for v in value}):
                problems.append(f"{path}: duplicate items")
            for i, v in enumerate(value):
                check(v, spec.get("items", {}), f"{path}[{i}]")
        if isinstance(value, dict):
            for key in spec.get("required", []):
                if key not in value:
                    problems.append(f"{path}.{key}: missing")
            props = spec.get("properties", {})
            if spec.get("additionalProperties") is False:
                for key in value:
                    if key not in props:
                        problems.append(f"{path}.{key}: not allowed")
            for key, sub in props.items():
                if key in value:
                    check(value[key], sub, f"{path}.{key}")

    check(entry, schema, "entry")
    return problems


def intake(url: str, *, registry_path: Path = REGISTRY, schema_path: Path = SCHEMA,
           receipt_dir: Path | None = RECEIPT_DIR, name: str | None = None,
           provenance_class: str = DEFAULT_PROVENANCE, requested_by: str = "",
           dry_run: bool = False, now: dt.datetime | None = None) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc).astimezone()
    stamp = now.isoformat(timespec="seconds")
    receipt: dict = {"schema": RECEIPT_SCHEMA, "received_at": stamp, "input_url": url,
                     "registry_ref": str(registry_path.relative_to(ROOT)) if registry_path.is_relative_to(ROOT) else str(registry_path),
                     "network_used": False, "authority_granted": False}
    key = parse_repo(url)
    if key is None or key in SELF_REPOS:
        receipt.update(status="INVALID_INPUT", next_action="Provide a public github.com/<owner>/<repo> URL; nothing was recorded in the registry.")
        return _emit(receipt, receipt_dir, None, dry_run)
    owner, repo = key
    receipt["normalized_url"] = canonical_url(owner, repo)
    try:
        data, raw = load_registry(registry_path)
        items = data["items"]
        dups = find_duplicates(items, key)
        if dups:
            receipt.update(status="DUPLICATE", candidate_ids=dups,
                           next_action="Already tracked; continue under the existing candidate record(s). No new candidate added.")
            return _emit(receipt, receipt_dir, key, dry_run)
        entry = build_candidate(items, owner, repo, name=name, provenance_class=provenance_class, requested_by=requested_by)
        problems = validate_entry(entry, json.loads(schema_path.read_text(encoding="utf-8")))
        if problems:
            raise IntakeError("; ".join(problems))
        before = copy.deepcopy(items)
        new = dict(data)
        new["items"] = items + [entry]
        new["candidate_count"] = len(new["items"])
        new["updated_at"] = stamp
        if new["items"][: len(before)] != before:
            raise IntakeError("historical rows changed")
        receipt.update(status="REGISTERED", candidate_ids=[entry["candidate_id"]],
                       candidate_count_before=len(before), candidate_count_after=len(new["items"]),
                       next_action=entry["comparison_review"]["next_action"])
        if not dry_run:
            if dump_registry(data) != raw:
                raise IntakeError("registry formatting does not round-trip; refusing to rewrite historical bytes")
            registry_path.write_text(dump_registry(new), encoding="utf-8")
        return _emit(receipt, receipt_dir, key, dry_run)
    except Exception as exc:  # explicit failure state, never silent
        receipt.update(status="NEEDS_SYNC", error=f"{type(exc).__name__}: {exc}",
                       next_action="Registry not updated; fix the error and re-run intake for this URL.")
        receipt.pop("candidate_ids", None)
        return _emit(receipt, receipt_dir, key, dry_run)


def _emit(receipt: dict, receipt_dir: Path | None, key, dry_run: bool) -> dict:
    if receipt_dir is not None and not dry_run:
        receipt_dir.mkdir(parents=True, exist_ok=True)
        day = receipt["received_at"][:10]
        tag = f"{_slug(key[0])}-{_slug(key[1])}" if key else "invalid"
        path = receipt_dir / f"{day}-{tag}-{receipt['status'].lower()}.json"
        n = 2
        while path.exists():
            path = receipt_dir / f"{day}-{tag}-{receipt['status'].lower()}-{n}.json"
            n += 1
        path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        receipt["receipt_path"] = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    return receipt


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("url")
    ap.add_argument("--name")
    ap.add_argument("--provenance-class", default=DEFAULT_PROVENANCE)
    ap.add_argument("--requested-by", default="")
    ap.add_argument("--registry", type=Path, default=REGISTRY)
    ap.add_argument("--receipt-dir", type=Path, default=RECEIPT_DIR)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    r = intake(a.url, registry_path=a.registry.resolve(), receipt_dir=a.receipt_dir.resolve(), name=a.name,
               provenance_class=a.provenance_class, requested_by=a.requested_by, dry_run=a.dry_run)
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return 0 if r["status"] in {"REGISTERED", "DUPLICATE"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
