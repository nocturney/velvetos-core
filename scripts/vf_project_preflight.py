#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json"
PROJECT_AUTHORITY = Path("packages/velvetos/chatgpt-project/PROJECT-AUTHORITY-v6.2.txt")
PROJECT_ASSET_MANIFEST = Path("packages/velvetos/chatgpt-project/ASSET-MANIFEST-v6.2.json")
VISUAL_ENFORCEMENT = Path("packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json")
PROJECT_GATE = Path("packages/velvetos/PROJECT-REQUEST-GATE.md")


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))

def project_binding_problems(root: Path = ROOT, *, creative: bool = False) -> list[str]:
    problems: list[str] = []
    paths = [PROJECT_AUTHORITY, PROJECT_ASSET_MANIFEST, PROJECT_GATE]
    if creative:
        paths.append(VISUAL_ENFORCEMENT)
    if any(not (root / rel).is_file() for rel in paths):
        return ["project binding file missing"]
    authority_path = root / PROJECT_AUTHORITY
    try:
        authority = authority_path.read_text(encoding="utf-8")
        gate = (root / PROJECT_GATE).read_text(encoding="utf-8")
        assets = json.loads((root / PROJECT_ASSET_MANIFEST).read_text(encoding="utf-8"))
        policy = json.loads((root / VISUAL_ENFORCEMENT).read_text(encoding="utf-8")) if creative else None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"project binding cannot be decoded: {type(exc).__name__}"]
    if not isinstance(assets, dict) or (creative and not isinstance(policy, dict)):
        return ["project binding JSON must contain top-level objects"]
    asset_rows = assets.get("assets")
    if not isinstance(asset_rows, list) or not all(isinstance(row, dict) for row in asset_rows):
        return ["Project asset manifest assets must be an array of objects"]
    if not all(x in authority for x in ("Contract version: 6", "Revision: 6.2", "Bundle: VF-PROJECT-6.2-DETAIL-TRUTH")):
        problems.append("Project Authority identity mismatch")
    rows = [x for x in asset_rows if x.get("filename") == "Velvet-Factory-Project-Authority-v6.txt"]
    digest = hashlib.sha256(authority_path.read_bytes()).hexdigest()
    if len(rows) != 1 or rows[0].get("sha256") != digest:
        problems.append("Project Authority hash does not match ASSET-MANIFEST-v6.2.json")
    if creative:
        route = policy.get("publicationRoute", {})
        if not isinstance(route, dict):
            problems.append("publicationRoute must be an object")
            return problems
        if "vfcovers/vfcanva composition route" in authority:
            problems.append("stale vfcanva publication route remains active in Project Authority")
        if "Canva/vfcanva are forbidden" not in authority:
            problems.append("Project Authority lacks the current no-Canva publication override")
        if "creative_execution_authorized: true" not in authority or "creative_execution_authorized: true" not in gate:
            problems.append("pre-tool creative execution receipt is not bound into Project Authority/Gate")
        denied_tools = route.get("deniedTools")
        if not isinstance(denied_tools, list) or not all(isinstance(x, str) for x in denied_tools):
            problems.append("publicationRoute deniedTools must be an array of strings")
        else:
            denied = {x.casefold() for x in denied_tools}
            if not {"canva", "vfcanva"}.issubset(denied):
                problems.append("publicationRoute does not deny Canva/vfcanva")
    return problems


def _phrase_in(probe: str, phrase: str) -> bool:
    """Substring match for multi-word / non-ASCII phrases."""
    return phrase.casefold() in probe


def _token_in(probe: str, token: str) -> bool:
    """Word-boundary match so 'feed' does not hit 'feedback' / 'story'≠'history'."""
    return re.search(rf"(?<!\w){re.escape(token.casefold())}(?!\w)", probe) is not None


def _hint_matches(probe: str, hint: str) -> bool:
    """ASCII single-token hints use word boundaries; phrases/Hebrew stay substring."""
    h = str(hint).casefold()
    if " " in h or any(ord(c) > 127 for c in h):
        return h in probe
    return _token_in(probe, h)


def _instagram_publish_request(probe: str) -> bool:
    """True when an Instagram destination appears with a publish-intent verb.

    Verbs and destination need not be adjacent (`post this on Instagram`,
    `share this on Instagram`). Pure drafting (`write an Instagram caption`)
    has destination but no publish-intent verb.
    """
    has_ig = _phrase_in(probe, "instagram") or _phrase_in(probe, "אינסטגרם")
    if not has_ig:
        return False
    if any(_token_in(probe, v) for v in ("post", "upload", "publish", "schedule", "share", "put")):
        return True
    return any(_phrase_in(probe, h) for h in ("פרסם", "העלה לאינסטגרם", "העלה", "שתף"))


def _bare_publication_request(probe: str) -> bool:
    """Public publication prep without an Instagram destination (not IG delivery)."""
    if _token_in(probe, "publish") or _phrase_in(probe, "פרסם"):
        return True
    if _token_in(probe, "post") and any(
        _phrase_in(probe, p) for p in ("this post", "a post", "the post", "new post", "publish this")
    ):
        return True
    return False


def classify(text: str, manifest: dict) -> list[str]:
    probe = text.casefold()
    hits: list[str] = []
    for name, cfg in manifest["domains"].items():
        if any(_hint_matches(probe, hint) for hint in cfg.get("hints", [])):
            hits.append(name)
    # Caption / public-social copy requests are creative by default in VF. Co-route
    # them through the Creative Manifest gate instead of allowing copywriting alone.
    public_copy_phrases = (
        "caption",
        "כיתוב",
        "public-social",
        "visual-copy",
        "social media",
        "social-media",
        "instagram",
        "אינסטגרם",
        "לפיד",
    )
    public_copy_tokens = ("feed",)
    if (
        "copywriting" in hits
        and "creative_publication" not in hits
        and (
            any(_phrase_in(probe, h) for h in public_copy_phrases)
            or any(_token_in(probe, t) for t in public_copy_tokens)
        )
    ):
        hits.append("creative_publication")
    # Instagram Story / create-a-Story production — not narrative "success/customer/user story".
    if "creative_publication" not in hits and _token_in(probe, "story"):
        narrative = any(
            _phrase_in(probe, p)
            for p in ("success story", "customer story", "user story", "case study")
        )
        social_story = any(
            _phrase_in(probe, p)
            for p in ("instagram story", "ig story", "create a story", "make a story", "write a story", "story for the")
        )
        if social_story and not narrative:
            hits.append("creative_publication")
    # Structural Instagram publish detection (verb + destination, intervening words OK).
    if _instagram_publish_request(probe):
        if "instagram_action" not in hits:
            hits.append("instagram_action")
    elif "instagram_action" in hits:
        # No IG destination: drop Instagram delivery route, but keep publication prep.
        hits = [h for h in hits if h != "instagram_action"]
        if "creative_publication" not in hits and _bare_publication_request(probe):
            hits.append("creative_publication")
    elif "creative_publication" not in hits and _bare_publication_request(probe):
        # e.g. "publish this post" never entered instagram_action but is still public prep.
        hits.append("creative_publication")
    return hits or ["general_business"]

def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve VelvetOS project request authority preflight")
    parser.add_argument("--domain", action="append", choices=None)
    parser.add_argument("--text")
    parser.add_argument("--manifest", help="Exact Creative Manifest for creative production evidence")
    parser.add_argument("--content-id")
    parser.add_argument("--phase", choices=("production", "delivery"), help="Use delivery for review handoff; Instagram actions require delivery")
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
    creative = bool(set(domains) & {"creative_publication", "instagram_action"})
    binding_problems = project_binding_problems(creative=creative)
    receipt = {
        "request_domain": domains,
        "authority_manifest_version": manifest["schemaVersion"],
        "baseline_authority": "FAIL" if (missing or binding_problems) else "PASS",
        "routed_packs": list(dict.fromkeys(packs)),
        "required_skills": [],
        "required_sources": authorities,
        "required_tools": [],
        "hard_gates": list(dict.fromkeys(hard_gates)),
        "current_evidence_state": "authority_paths_resolved",
        "project_preflight": "BLOCKED" if (missing or binding_problems) else "PASS",
        "missing_authority_paths": missing,
        "authority_conflicts": binding_problems,
        "creative_execution_authorized": False,
    }
    receipt["route_resolution"] = "BLOCKED" if (missing or binding_problems) else "PASS"
    if creative:
        from vf_publication_evidence import validate
        phase = args.phase or ("delivery" if "instagram_action" in domains else "production")
        if "instagram_action" in domains and phase != "delivery":
            evidence = {"ok": False, "evidence_state": "BLOCKED", "publishAuthorized": False,
                        "problems": ["Instagram actions require delivery evidence"]}
        else:
            evidence = validate(ROOT, args.manifest or "", args.content_id or "", phase)
        receipt["publication_evidence_phase"] = phase
        receipt["production_evidence"] = evidence
        receipt["required_skills"] = ["velvet-creative-director", "velvet-brand-guardian", "velvet-hebrew-copy"]
        receipt["current_evidence_state"] = evidence["evidence_state"]
        receipt["project_preflight"] = "PASS" if evidence["ok"] and not missing and not binding_problems else "BLOCKED"
        receipt["creative_execution_authorized"] = bool(phase == "production" and receipt["project_preflight"] == "PASS")
        receipt["delivery_authorized"] = bool(phase == "delivery" and receipt["project_preflight"] == "PASS")
    else:
        receipt["evidence_scope"] = "authority path resolution only; no action authorization"
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 2 if receipt["project_preflight"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())