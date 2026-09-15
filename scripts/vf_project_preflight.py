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


def _advisory_only_request(probe: str) -> bool:
    """True for discussion/howto — not authorization to create or execute.

    This flags advisory *language* in a prompt. It must NOT alone erase an
    Instagram action found in another clause of a mixed request.
    """
    return any(
        _phrase_in(probe, p)
        for p in (
            "should we",
            "should i",
            "do we delete",
            "do i delete",
            "how do i",
            "how to delete",
            "how to remove",
            "how can i",
            "how should",
            "what is an",
            "what is a",
            "what's an",
            "what's a",
            "what happens if",
            "what if i",
            "whether i should",
            "whether we should",
            "tell me whether",
            "write instructions",
            "instructions for deleting",
            "instructions for remove",
            "explain how",
            "explain how to",
            "האם כדאי",
            "האם למחוק",
            "איך מוחקים",
            "איך למחוק",
            "מה זה",
            "מה קורה אם",
            "תכתוב הוראות",
        )
    )


def _split_intent_clauses(probe: str) -> list[str]:
    """Split mixed prompts so later action clauses stay visible to gates."""
    parts = re.split(
        r"(?:\b(?:and\s+then|then)\b|,?\s*ואז|,?\s*ואחר כך|,?\s*לאחר מכן)",
        probe,
        flags=re.IGNORECASE,
    )
    return [p.strip(" \t,.;:") for p in parts if p and p.strip(" \t,.;:")]


def _hypothetical_or_howto_clause(clause: str) -> bool:
    """True when a clause itself is advice/howto, not an imperative mutation."""
    return any(
        _phrase_in(clause, p)
        for p in (
            "should we",
            "should i",
            "whether i should",
            "whether we should",
            "how do i",
            "how to",
            "how can i",
            "how should",
            "what happens if",
            "what if i",
            "explain how to",
            "explain how publishing",
            "explain how deleting",
            "write instructions",
            "האם כדאי",
            "איך מוחקים",
            "איך למחוק",
            "מה קורה אם",
            "מה זה",
        )
    )


def _followthrough_mutation_clause(clause: str) -> bool:
    """True for short follow-through publish/delete clauses after 'then' / 'ואז'."""
    if _hypothetical_or_howto_clause(clause):
        return False
    # publish/post/share/push/upload it|this [to Instagram] [live]
    if re.search(
        r"(?<!\w)(?:publish|post|share|push|upload|send)\b"
        r"(?:\W+\w+){0,6}\W+(?:it|this|that|them)\b",
        clause,
    ):
        return True
    if re.search(
        r"(?<!\w)(?:publish|post|share|push|upload|send)\b"
        r"(?:\W+\w+){0,6}\W+(?:to|on)\s+instagram",
        clause,
    ):
        return True
    if _go_live_request(clause):
        return True
    # delete/remove/archive/unpublish + object
    if re.search(
        r"(?<!\w)(?:delete|remove|archive|unpublish)\b"
        r"(?:\W+\w+){0,6}\W+(?:it|this|that|post|reel|story|media)\b",
        clause,
    ):
        return True
    # Hebrew follow-through publish / take-down
    if any(
        _phrase_in(clause, v)
        for v in (
            "תפרסם",
            "תעלה אותו",
            "תעלה אותה",
            "תעלה את זה",
            "תעלה",
            "שתף",
            "פרסם",
            "תמחק",
            "תוריד אותו",
            "תוריד אותה",
            "תוריד את זה",
            "תוריד",
            "תארכב",
            "ארכב",
            "מחק את הפוסט",
            "הסר",
        )
    ):
        return True
    return False


def _clause_instagram_action(clause: str, *, allow_followthrough: bool = False) -> bool:
    """Action intent inside one clause (ignores advisory language elsewhere).

    Follow-through mutations (`publish it`, `תמחק את הפוסט`) only count when the
    prompt was split into multiple clauses. Otherwise bare prep like
    `publish this post` would be mis-routed as Instagram delivery.
    """
    if not clause or _hypothetical_or_howto_clause(clause):
        return False
    if _instagram_delivery_request(clause) or _instagram_destructive_request(clause):
        return True
    if allow_followthrough:
        return _followthrough_mutation_clause(clause)
    return False


def _instagram_post_prep_request(probe: str) -> bool:
    """True for creating/drafting/designing an Instagram post (creative prep).

    Not delivery/action: preparation only. Advisory discussion about whether
    to create a post is excluded.
    """
    if _advisory_only_request(probe):
        return False
    if any(
        _phrase_in(probe, h)
        for h in (
            "תכין פוסט לאינסטגרם",
            "תיצור פוסט לאינסטגרם",
            "תעצב פוסט לאינסטגרם",
            "תכין לי פוסט באינסטגרם",
            "תכין פרסום לאינסטגרם",
            "צור פוסט לאינסטגרם",
            "עצב פוסט לאינסטגרם",
        )
    ):
        return True
    has_ig = _phrase_in(probe, "instagram") or _phrase_in(probe, "אינסטגרם")
    if not has_ig:
        return False
    # create/draft/design/make/prepare + Instagram + post
    if re.search(
        r"(?<!\w)(?:create|draft|design|make|prepare)\b(?:\W+\w+){0,6}\W+"
        r"instagram\b(?:\W+\w+){0,4}\W+posts?\b",
        probe,
    ):
        return True
    # create/draft/... + post + for/on Instagram
    if re.search(
        r"(?<!\w)(?:create|draft|design|make|prepare)\b(?:\W+\w+){0,4}\W+"
        r"posts?\b(?:\W+\w+){0,6}\W+(?:for|on)\s+instagram",
        probe,
    ):
        return True
    # Hebrew prep verb + פוסט/פרסום with Instagram already present
    if any(_phrase_in(probe, v) for v in ("תכין", "תיצור", "תעצב", "צור", "עצב", "הכן")) and any(
        _phrase_in(probe, o) for o in ("פוסט", "פרסום")
    ):
        return True
    return False


def _go_live_request(probe: str) -> bool:
    """Push/make content live — VF delivery channel is Instagram."""
    if re.search(
        r"(?<!\w)(?:push|make|take|put)\b(?:\W+\w+){0,5}\W+live\b",
        probe,
    ):
        return True
    if re.search(r"(?<!\w)publish\b(?:\W+\w+){0,5}\W+live\b", probe):
        return True
    return any(
        _phrase_in(probe, p)
        for p in (
            "לאוויר",
            "תפרסם את זה עכשיו",
            "פרסם עכשיו",
            "תעלה את זה לאוויר",
            "העלה את זה לאוויר",
        )
    )


def _instagram_delivery_request(probe: str) -> bool:
    """True when the ask is to publish/send content onto Instagram (delivery)."""
    has_ig = _phrase_in(probe, "instagram") or _phrase_in(probe, "אינסטגרם")
    if any(
        _phrase_in(probe, h)
        for h in (
            "העלה לאינסטגרם",
            "שלח לאינסטגרם",
            "שתף לאינסטגרם",
            "שתף את זה באינסטגרם",
            "תשתף באינסטגרם",
            "תעלה את הפוסט לאינסטגרם",
            "תעלה לאינסטגרם",
            "תפרסם את זה באינסטגרם",
            "פרסם באינסטגרם",
            "העלה את זה לאוויר באינסטגרם",
        )
    ):
        return True
    # Destination-scoped English delivery (excludes office co-occurrence).
    if has_ig and re.search(
        r"(?<!\w)(?:upload|publish|schedule|put|send|post|share|push|add)\b"
        r"(?:\W+\w+){0,8}\W+(?:on|to|onto|in|from)\s+instagram",
        probe,
    ):
        return True
    # Go-live / push-live family (Instagram is the VF publication channel).
    if _go_live_request(probe):
        return True
    # Hebrew upload token with explicit Instagram destination.
    if has_ig and any(_phrase_in(probe, h) for h in ("העלה", "תעלה", "פרסם", "תפרסם", "שתף")):
        return True
    return False


def _instagram_destructive_request(probe: str) -> bool:
    """True for mutating/deleting Instagram content (Graph DELETE / take-down)."""
    if any(
        _phrase_in(probe, h)
        for h in (
            "מחק מאינסטגרם",
            "הסר מאינסטגרם",
            "תוריד את זה מהאינסטגרם",
            "מחק את הפוסט באינסטגרם",
            "תמחק את הריל",
            "תמחק את הפוסט",
            "הסר את הסטורי",
            "תוריד את הפוסט",
        )
    ):
        return True
    has_ig = _phrase_in(probe, "instagram") or _phrase_in(probe, "אינסטגרם")
    if has_ig and re.search(
        r"(?<!\w)(?:delete|remove|unpublish|archive)\b(?:\W+\w+){0,12}\W+instagram"
        r"|(?<!\w)(?:delete|remove|unpublish|archive)\b\W+instagram"
        r"|\binstagram\b(?:\W+\w+){0,6}\W+(?:delete|remove|unpublish|archive)\b",
        probe,
    ):
        return True
    # take down + social object
    if re.search(
        r"(?<!\w)take\s+down\b(?:\W+\w+){0,6}\W+(?:post|reel|story|media)\b"
        r"|(?<!\w)take\s+(?:this|that|the)\s+(?:post|reel|story|media)\s+down\b",
        probe,
    ):
        return True
    # Reel is Instagram-native
    if re.search(r"(?<!\w)(?:delete|remove|archive)\b(?:\W+\w+){0,5}\W+reels?\b", probe):
        return True
    # Story take-down / remove (not narrative success/customer/user story)
    if re.search(r"(?<!\w)(?:delete|remove|archive)\b(?:\W+\w+){0,5}\W+story\b", probe):
        if not any(
            _phrase_in(probe, p)
            for p in ("success story", "customer story", "user story", "case study")
        ):
            return True
    return False


def _instagram_publish_request(probe: str) -> bool:
    """True for Instagram delivery or destructive mutation intents.

    Delivery: destination-scoped publish/send (`send this to Instagram`) and
    go-live commands (`push this live`, `תעלה את זה לאוויר`). Preparation
    (`prepare a post`, `תכין פוסט`) is not delivery.

    Destructive: delete/remove/archive/take-down of Instagram media/posts/
    reels/stories.

    Mixed prompts keep the strictest clause: advisory language in one clause
    must not erase a real publish/delete clause later (`explain …, then
    publish it to Instagram`). Pure howto/hypothetical discussion with no
    action clause stays non-action.
    """
    clauses = _split_intent_clauses(probe)
    multi = len(clauses) > 1
    # Mixed prompts: keep the strictest clause. Follow-through publish/delete
    # after then/ואז is action even when an earlier clause is advisory.
    if any(_clause_instagram_action(c, allow_followthrough=multi) for c in clauses):
        return True
    # Single-clause destination/destructive patterns (no advisory short-circuit).
    if len(clauses) == 1 and _hypothetical_or_howto_clause(clauses[0]):
        return False
    if _advisory_only_request(probe) and len(clauses) == 1:
        return False
    return _instagram_delivery_request(probe) or _instagram_destructive_request(probe)


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
    # Instagram post create/draft/design/prepare → creative prep (not delivery).
    if "creative_publication" not in hits and _instagram_post_prep_request(probe):
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
    # Pure advisory/howto (no action clause) must not authorize creative production
    # or IG actions. Mixed prompts that already carry instagram_action keep it —
    # never strip the strictest action route with a global advisory override.
    if _advisory_only_request(probe) and "instagram_action" not in hits:
        hits = [h for h in hits if h != "creative_publication"]
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