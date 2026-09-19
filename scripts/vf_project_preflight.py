#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json"

def _current_bundle_config() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    bundle = manifest.get("chatgptProjectBundle")
    if not isinstance(bundle, dict):
        raise RuntimeError("chatgptProjectBundle missing from authority manifest")
    required = ("contractVersion", "revision", "bundleId", "authority", "assetManifest")
    if any(not bundle.get(k) for k in required):
        raise RuntimeError("chatgptProjectBundle is incomplete")
    return bundle

_PROJECT_BUNDLE = _current_bundle_config()
PROJECT_AUTHORITY = Path(_PROJECT_BUNDLE["authority"])
PROJECT_ASSET_MANIFEST = Path(_PROJECT_BUNDLE["assetManifest"])
PROJECT_CONTRACT_VERSION = int(_PROJECT_BUNDLE["contractVersion"])
PROJECT_REVISION = str(_PROJECT_BUNDLE["revision"])
PROJECT_BUNDLE_ID = str(_PROJECT_BUNDLE["bundleId"])
VISUAL_ENFORCEMENT = Path("packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json")
PROJECT_GATE = Path("packages/velvetos/PROJECT-REQUEST-GATE.md")
# Canonical Instagram tool capability SoT + MCP write/read binding (no parallel registry).
IG_CAPABILITIES = ROOT / "packages/vfigos/CAPABILITIES.json"
CORE_MCP = ROOT / "packages/vfmcp/core-mcp.json"


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
    identity = (assets.get("contract_version"), str(assets.get("revision")), assets.get("bundle_id"))
    expected = (PROJECT_CONTRACT_VERSION, PROJECT_REVISION, PROJECT_BUNDLE_ID)
    if identity != expected:
        problems.append("Project asset manifest identity does not match current chatgptProjectBundle")
    markers = (
        f"Contract version: {PROJECT_CONTRACT_VERSION}",
        f"Revision: {PROJECT_REVISION}",
        f"Bundle: {PROJECT_BUNDLE_ID}",
    )
    if not all(x in authority for x in markers):
        problems.append("Project Authority identity mismatch")
    rows = [x for x in asset_rows if x.get("filename") == "Velvet-Factory-Project-Authority-v6.txt"]
    canonical = authority.encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    if len(rows) != 1 or rows[0].get("sha256") != digest:
        problems.append("Project Authority hash does not match current asset manifest")
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


@lru_cache(maxsize=1)
def _instagram_tool_classes() -> tuple[frozenset[str], frozenset[str]]:
    """Return (mutation_tool_ids, read_only_tool_ids) from canonical IG SoT.

    Mutation ids come from supported write capabilities in
    ``packages/vfigos/CAPABILITIES.json`` (publish.* / media.delete) plus
    ``allowedWriteAfterGates`` on the Instagram server in
    ``packages/vfmcp/core-mcp.json`` (comment moderation writes).

    Read-only ids come from supported read capabilities in CAPABILITIES plus
    ``allowedRead`` in core-mcp. ``graph_mutation_matrix`` is always read-only
    even when listed beside delete.
    """
    mutation: set[str] = set()
    read_only: set[str] = set()
    if IG_CAPABILITIES.is_file():
        caps = json.loads(IG_CAPABILITIES.read_text(encoding="utf-8"))
        for row in caps.get("capabilities") or []:
            if not isinstance(row, dict):
                continue
            tools = [t for t in (row.get("tools") or []) if isinstance(t, str) and t]
            if not tools:
                continue
            cap_id = str(row.get("id") or "")
            supported = row.get("supported", True)
            # graph_mutation_matrix is capability discovery SoT — never a mutation.
            if "graph_mutation_matrix" in tools:
                read_only.add("graph_mutation_matrix")
            write_tools = [t for t in tools if t != "graph_mutation_matrix"]
            if supported is False:
                continue
            if cap_id.startswith("instagram.publish.") or cap_id == "instagram.media.delete":
                mutation.update(write_tools)
            elif write_tools:
                read_only.update(write_tools)
    if CORE_MCP.is_file():
        core = json.loads(CORE_MCP.read_text(encoding="utf-8"))
        for server in core.get("servers") or []:
            if not isinstance(server, dict) or server.get("id") != "instagram":
                continue
            for t in server.get("allowedWriteAfterGates") or []:
                if isinstance(t, str) and t:
                    mutation.add(t)
            for t in server.get("allowedRead") or []:
                if isinstance(t, str) and t:
                    read_only.add(t)
            break
    # Never treat a write id as read-only if it also appears on a write surface.
    read_only -= mutation
    return frozenset(mutation), frozenset(read_only)


def _tool_id_in(probe: str, tool_id: str) -> bool:
    """Token-aware match for snake_case MCP tool ids (no substring false hits)."""
    return re.search(rf"(?<!\w){re.escape(tool_id)}(?!\w)", probe, flags=re.IGNORECASE) is not None


def _tool_documentation_or_advisory(probe: str) -> bool:
    """True when the ask is about a tool (docs/compare/advice), not executing it."""
    return any(
        _phrase_in(probe, p)
        for p in (
            "what does",
            "what is",
            "what's",
            "how does",
            "how do",
            "how to use",
            "explain",
            "tell me how",
            "tell me what",
            "compare",
            "difference between",
            "should we use",
            "should i use",
            "documentation",
            "docs for",
            "meaning of",
            "מה זה",
            "מה עושה",
            "איך עובד",
            "הסבר",
            "האם כדאי להשתמש",
            "השווה",
        )
    )


def _generic_instagram_publish_tool_execution(probe: str) -> bool:
    """True for 'call/use the Instagram publish tool' without a specific tool id."""
    if _tool_documentation_or_advisory(probe):
        return False
    if not (_phrase_in(probe, "instagram") or _phrase_in(probe, "אינסטגרם")):
        return False
    return (
        re.search(
            r"(?<!\w)(?:use|run|call|invoke|execute|trigger)\b"
            r"(?:\W+\w+){0,6}\W+publish(?:_\w+)?\s+tools?\b",
            probe,
            flags=re.IGNORECASE,
        )
        is not None
        or re.search(
            r"(?<!\w)(?:תשתמש|השתמש|תריץ|הרץ|תפעיל|הפעל|בצע)\b"
            r"(?:\W+\w+){0,6}\W+(?:ב)?כלי\s+ה?פרסום",
            probe,
        )
        is not None
    )


def _mutation_tool_execution_intent(probe: str, tool_id: str) -> bool:
    """True when probe asks to execute a specific mutation tool id."""
    if not _tool_id_in(probe, tool_id):
        return False
    if _tool_documentation_or_advisory(probe):
        return False
    # Explicit execution verbs around the tool id.
    if re.search(
        rf"(?<!\w)(?:use|run|call|invoke|execute|trigger|apply|perform)\b"
        rf"(?:\W+\w+){{0,6}}\W+{re.escape(tool_id)}\b",
        probe,
        flags=re.IGNORECASE,
    ):
        return True
    if re.search(
        rf"(?<!\w)(?:תשתמש|השתמש|תריץ|הרץ|תפעיל|הפעל|בצע|תקרא\s+ל)\b"
        rf"(?:\W+\w+){{0,6}}\W+{re.escape(tool_id)}\b",
        probe,
    ):
        return True
    # Instagram-scoped tool invocation: "Instagram delete_media 123"
    if re.search(
        rf"(?i)(?<!\w)(?:instagram|אינסטגרם)\b(?:\W+\w+){{0,4}}\W+{re.escape(tool_id)}\b",
        probe,
    ):
        return True
    # Imperative tool command with args / target: "publish_image with …", "delete_media 123"
    if re.search(
        rf"(?<!\w){re.escape(tool_id)}\b(?:\W+(?:now|with|on|using|for|this|that|\d))",
        probe,
        flags=re.IGNORECASE,
    ):
        return True
    # "Delete this with delete_media" / Hebrew equivalent already covered by verbs.
    if re.search(
        rf"(?<!\w)(?:delete|remove|publish|post|share)\b(?:\W+\w+){{0,6}}\W+{re.escape(tool_id)}\b",
        probe,
        flags=re.IGNORECASE,
    ):
        return True
    # Bare tool id as the whole command (or leading command token).
    stripped = probe.strip(" \t,.;:!?\"'`")
    if re.fullmatch(rf"{re.escape(tool_id)}(?:\W+\S+)*", stripped, flags=re.IGNORECASE):
        return True
    return False


def _instagram_mutation_tool_request(probe: str) -> bool:
    """True when a canonical IG mutation MCP tool is being invoked/executed."""
    if _generic_instagram_publish_tool_execution(probe):
        return True
    mutation_ids, _read_ids = _instagram_tool_classes()
    return any(_mutation_tool_execution_intent(probe, tool_id) for tool_id in mutation_ids)


def _clause_instagram_action(clause: str, *, allow_followthrough: bool = False) -> bool:
    """Action intent inside one clause (ignores advisory language elsewhere).

    Follow-through mutations (`publish it`, `תמחק את הפוסט`) only count when the
    prompt was split into multiple clauses. Otherwise bare prep like
    `publish this post` would be mis-routed as Instagram delivery.

    Canonical Instagram mutation tool identifiers (from CAPABILITIES / core-mcp
    write binding) with execution intent are always action — including mixed
    advisory+tool clauses.
    """
    if not clause or _hypothetical_or_howto_clause(clause):
        return False
    if _instagram_mutation_tool_request(clause):
        return True
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
    """True for Instagram delivery, destructive, or mutation-tool intents.

    Delivery: destination-scoped publish/send (`send this to Instagram`) and
    go-live commands (`push this live`, `תעלה את זה לאוויר`). Preparation
    (`prepare a post`, `תכין פוסט`) is not delivery.

    Destructive: delete/remove/archive/take-down of Instagram media/posts/
    reels/stories.

    Mutation tools: canonical write tool ids from CAPABILITIES.json /
    core-mcp.json (`publish_image`, `publish_story`, `delete_media`, …)
    with execution intent. Read-only ids (`list_media`, `get_profile`, …)
    stay non-action. Docs/advisory about a tool stay non-action.

    Mixed prompts keep the strictest clause: advisory language in one clause
    must not erase a real publish/delete/tool clause later (`explain …, then
    use publish_image`). Pure howto/hypothetical discussion with no
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
    parser.add_argument(
        "--delivery-approval",
        help="Path to signed velvet.delivery_approval.v1 JSON receipt (or inline JSON)",
    )
    parser.add_argument(
        "--mutation-tool",
        help="Exact Instagram mutation tool id the approval must bind to",
    )
    parser.add_argument(
        "--package-sha256",
        help="Exact package digest the approval must bind to",
    )
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
        "delivery_authorized": False,
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
        evidence_ok = bool(evidence.get("ok")) and not missing and not binding_problems
        receipt["creative_execution_authorized"] = bool(phase == "production" and evidence_ok)
        # Publication evidence is NECESSARY but NOT SUFFICIENT for delivery.
        if phase == "delivery":
            approval_problems, delivery_auth = _evaluate_delivery_approval(
                args,
                evidence_ok=evidence_ok,
            )
            receipt["delivery_approval"] = {
                "required": True,
                "ok": delivery_auth,
                "problems": approval_problems,
                "advisory_only": True,
                "note": "preflight PASS is not mutation capability; mutation endpoint re-verifies + claims",
            }
            receipt["delivery_authorized"] = bool(delivery_auth)
            receipt["project_preflight"] = "PASS" if delivery_auth else "BLOCKED"
        else:
            receipt["project_preflight"] = "PASS" if evidence_ok else "BLOCKED"
            receipt["delivery_authorized"] = False
    else:
        receipt["evidence_scope"] = "authority path resolution only; no action authorization"
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 2 if receipt["project_preflight"] == "BLOCKED" else 0


def _evaluate_delivery_approval(args: argparse.Namespace, *, evidence_ok: bool) -> tuple[list[str], bool]:
    """Advisory delivery-approval check. Never grants mutation capability by itself."""
    problems: list[str] = []
    if not evidence_ok:
        problems.append("publication evidence invalid")
    raw = (args.delivery_approval or "").strip()
    if not raw:
        problems.append("signed delivery approval missing")
        return problems, False

    import sys

    packages = ROOT / "packages"
    if str(packages) not in sys.path:
        sys.path.insert(0, str(packages))
    from vfigos.approval.keys_registry import KeyRegistry
    from vfigos.approval.verify import verify_receipt

    try:
        if raw.startswith("{"):
            envelope = json.loads(raw)
        else:
            path = Path(raw)
            envelope = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        problems.append(f"delivery approval unreadable: {exc}")
        return problems, False

    import os
    reg_path = (os.environ.get("VELVET_DELIVERY_APPROVAL_REGISTRY") or "").strip()
    registry = KeyRegistry.from_path(Path(reg_path)) if reg_path else KeyRegistry.from_path()
    vr = verify_receipt(
        envelope,
        registry=registry,
        expected_mutation_tool=(args.mutation_tool or None),
        expected_content_id=(args.content_id or None),
        expected_package_sha256=(args.package_sha256 or None),
    )
    if not vr.ok:
        problems.extend(vr.problems)
        return problems, False
    if problems:
        return problems, False
    return [], True


if __name__ == "__main__":
    raise SystemExit(main())
