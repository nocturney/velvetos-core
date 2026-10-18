#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P2 = ROOT / "docs" / "implementation" / "office-v2" / "phase2"
FIXTURES = P2 / "golden-fixtures"

REQUIRED = [
    P2 / "README.md",
    P2 / "candidate-lifecycle-v0.json",
    P2 / "candidate-registry.schema.json",
    P2 / "candidate-registry-v0.json",
    P2 / "browser-automation-intake-2026-10-16.json",
    P2 / "browser-automation-intake-2026-10-16.md",
    P2 / "owner-assurance-binary-tools-intake-2026-10-14.json",
    P2 / "owner-assurance-binary-tools-intake-2026-10-14.md",
    P2 / "owner-local-inference-llamafile-intake-2026-10-14.json",
    P2 / "owner-local-inference-llamafile-intake-2026-10-14.md",
    P2 / "admission-policy-v0.md",
    P2 / "scorecard.schema.json",
    P2 / "golden-fixture-contract.schema.json",
    P2 / "fixture-adapter-receipt.schema.json",
    P2 / "pattern-adoption-receipt.schema.json",
    P2 / "research-freeze-record.schema.json",
    P2 / "p0-shortlists-v0.json",
    ROOT / "scripts" / "vf_office_v2_golden_fixture.py",
    ROOT / "scripts" / "vf_office_v2_link_intake.py",
    ROOT / "scripts" / "vf_office_v2_link_intake_selftest.py",
]

EXPECTED_FORWARD = [
    "DISCOVERED", "RESEARCHED", "CANDIDATE", "ADMITTED", "LAB",
    "SHADOW", "PILOT", "PRODUCTION", "FALLBACK", "RETIRED",
]
EXPECTED_EXIT = [
    "REJECTED_WITH_REASON", "BENCHMARKED_AND_LOST",
    "SUPERSEDED", "DEFERRED_WITH_REASON",
]
EXPECTED_FIXTURES = {
    "instagram-request-publish-live-verify",
    "customer-quote-production-ready-paid",
    "3d-asset-dcc-slice-artifact",
    "agent-approval-effect-reconciliation",
    "long-job-crash-resume",
    "morning-brief-compose-send-verify",
}


def fail(msg: str) -> None:
    print("FAIL " + msg, file=sys.stderr)
    raise SystemExit(1)


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        fail(f"invalid JSON {path.relative_to(ROOT)}: {exc}")



# Historical closed import plus Phase 3B additions (2026-10-06).
# FNV-1a is a drift detector for the legacy 82 candidate IDs, NOT a security digest.
LEGACY_CANDIDATE_COUNT = 82
LEGACY_ID_FNV1A = "2c986691"
COMPETITOR_POLICY = "COMPETITOR_NEUTRAL_ADMISSION_V1"
COMPETITOR_DOCS = [
    ROOT / "constitution" / "CONSTITUTION.md",
    ROOT / "packages" / "velvetos" / "AGENTS.md",
    P2 / "README.md",
    P2 / "admission-policy-v0.md",
    ROOT / "packages" / "vfe2b" / "LOCK.md",
    ROOT / "packages" / "vfe2b" / "DEER-FLOW-PATTERNS.md",
    ROOT / "packages" / "vfe2b" / "ORCHESTRATORS.md",
    ROOT / "packages" / "vfe2b" / "crews" / "run.md",
    ROOT / ".cursor" / "skills" / "vf-run" / "SKILL.md",
]


def evaluation_route_issues(items: list[dict], lanes: list[dict]) -> list[str]:
    """Keep unshortlisted research actionable without inventing a second candidate queue."""
    routed_ids = set()
    for lane in lanes:
        routed_ids.update(lane.get("challengers") or [])
        routed_ids.update(lane.get("queued_challengers") or [])

    problems: list[str] = []
    statuses = {"NEEDS_SOURCE_REVIEW", "WAITING_GATE", "RESEARCH_ACTIVE", "READY_FOR_ADMISSION_REVIEW"}
    required = ("workstream", "owner_ref", "phase", "status", "next_gate", "unlock_condition", "evidence_refs")
    for item in items:
        cid = item.get("candidate_id")
        route = item.get("evaluation_route")
        needs_explicit_route = (
            item.get("decision_verdict") == "BENCHMARK_REQUIRED"
            and item.get("lifecycle_state") in {"RESEARCHED", "CANDIDATE"}
            and cid not in routed_ids
        )
        if needs_explicit_route and not isinstance(route, dict):
            problems.append(f"{cid}: benchmark-required candidate missing shortlist membership or evaluation_route")
            continue
        if route is None:
            continue
        if not isinstance(route, dict):
            problems.append(f"{cid}: evaluation_route must be an object")
            continue
        for key in required:
            value = route.get(key)
            if key == "evidence_refs":
                if not isinstance(value, list) or not value or not all(
                    isinstance(x, str) and x.strip() for x in value
                ):
                    problems.append(f"{cid}: evaluation_route.{key} missing evidence")
            elif not isinstance(value, str) or not value.strip():
                problems.append(f"{cid}: evaluation_route.{key} missing")
        if route.get("status") not in statuses:
            problems.append(f"{cid}: invalid evaluation_route.status")
        if route.get("owner_ref") and not route["owner_ref"].startswith(("https://", "http://")):
            problems.append(f"{cid}: evaluation_route.owner_ref must identify an existing authority or issue")
        if item.get("lifecycle_state") in {"ADMITTED", "LAB", "SHADOW", "PILOT", "PRODUCTION"} and route.get("status") == "RESEARCH_ACTIVE":
            problems.append(f"{cid}: research route cannot assert a promoted runtime state")
    return problems


def validate_competitor_neutrality(registry: dict, items: list[dict], lanes: list[dict]) -> None:
    for path in COMPETITOR_DOCS:
        if not path.is_file() or COMPETITOR_POLICY not in path.read_text(encoding="utf-8-sig"):
            fail("competition-neutral policy missing from " + str(path.relative_to(ROOT)))

    if registry.get("candidate_count") != len(items):
        fail("candidate_count must match the complete post-policy registry")
    if len(items) < LEGACY_CANDIDATE_COUNT:
        fail("historical candidate import unexpectedly shrank")
    fingerprint = 2166136261
    for byte in ",".join(str(item.get("candidate_id", "")) for item in items[:LEGACY_CANDIDATE_COUNT]).encode("utf-8"):
        fingerprint = ((fingerprint ^ byte) * 16777619) & 0xFFFFFFFF
    if f"{fingerprint:08x}" != LEGACY_ID_FNV1A:
        fail("historic 82-item candidate prefix changed; reconcile with a documented baseline migration")

    by_id = {item["candidate_id"]: item for item in items}
    by_lane = {lane["lane_id"]: lane for lane in lanes}
    active_or_queued: dict[str, set[str]] = {}
    for lane in lanes:
        lid = lane["lane_id"]
        queued = lane.get("queued_challengers", [])
        if not isinstance(queued, list) or len(queued) != len(set(queued)):
            fail(f"{lid}: queued_challengers must be a unique list")
        active = set(lane.get("challengers") or [])
        if set(queued) & active:
            fail(f"{lid}: challenger listed in both active and queued")
        if lane.get("incumbent") in queued:
            fail(f"{lid}: incumbent cannot be queued as challenger")
        for cid in queued:
            if cid not in by_id:
                fail(f"{lid}: queued candidate absent from canonical registry: {cid}")
            if by_id[cid].get("decision_verdict") in {"REJECTED_WITH_REASON", "BENCHMARKED_AND_LOST", "SUPERSEDED"}:
                fail(f"{lid}: exited candidate still queued without reopening record: {cid}")
        active_or_queued[lid] = active | set(queued)

    new_items = items[LEGACY_CANDIDATE_COUNT:]
    for item in new_items:
        cid = item["candidate_id"]
        review = item.get("comparison_review")
        if not isinstance(review, dict) or review.get("policy") != COMPETITOR_POLICY:
            fail(f"{cid}: new candidate silently lacks comparative review")
        if review.get("eligibility") not in {
            "OPEN_FOR_COMPARISON", "BENCHMARKED", "EVIDENCE_BASED_REJECTED", "DEFERRED_WITH_REASON"
        }:
            fail(f"{cid}: comparative eligibility is missing")
        variants = review.get("variants")
        if not isinstance(variants, list) or not variants or set(variants) - {
            "full_replacement", "component_replacement", "hybrid"
        }:
            fail(f"{cid}: replacement/composition alternatives not documented")
        if not isinstance(review.get("next_action"), str) or len(review["next_action"].strip()) < 10:
            fail(f"{cid}: new challenger lacks explicit next evaluation action")
        if not isinstance(review.get("rationale"), str) or len(review["rationale"].strip()) < 10:
            fail(f"{cid}: challenger rationale missing")
        refs = item.get("evidence_refs") or []
        if not any(str(ref).startswith(("https://", "http://", "gdrive://", "D:/")) for ref in refs):
            fail(f"{cid}: new challenger lacks source/provenance link")
        if item.get("decision_verdict") in {
            "REJECTED_WITH_REASON", "BENCHMARKED_AND_LOST", "DEFERRED_WITH_REASON", "SUPERSEDED"
        }:
            if not review.get("decision_evidence_refs"):
                fail(f"{cid}: negative/deferred verdict must cite concrete decision evidence")
        if review.get("eligibility") == "OPEN_FOR_COMPARISON":
            lane_ids = item.get("shortlist_lanes") or []
            for lane_id in lane_ids:
                if lane_id in by_lane and cid not in active_or_queued[lane_id]:
                    fail(f"{cid}: silently dropped from open evaluation lane {lane_id}")
            if not lane_ids:
                fail(f"{cid}: unassigned open candidate needs a real evaluation lane or a documented lane addition")

    # Historical backfill must remain visible. A previous "second runtime" veto
    # cannot reappear as an unevidenced defer on these directly competing runtimes.
    reopen_required = {
        "deferred-openclaw", "deferred-crewai", "deferred-langgraph", "deferred-ruflo",
    }
    for cid in reopen_required:
        candidate = by_id.get(cid)
        if not candidate:
            fail("historical challenger disappeared: " + cid)
        review = candidate.get("comparison_review") or {}
        if candidate.get("decision_verdict") != "BENCHMARK_REQUIRED" or review.get("eligibility") != "OPEN_FOR_COMPARISON":
            fail("historical competitor reopened without active comparison: " + cid)
        if cid not in active_or_queued.get("agent-runtime", set()):
            fail("reopened challenger silently dropped from agent-runtime: " + cid)
        if review.get("evidence_status") != "RESEARCH_ONLY":
            fail("historic challenger incorrectly marked as tested: " + cid)
    successor = by_id.get("candidate-microsoft-agent-framework")
    ancestor = by_id.get("deferred-autogen")
    if not successor or not ancestor or "github.com/microsoft/agent-framework" not in " ".join(successor.get("evidence_refs") or []):
        fail("maintenance-mode AutoGen successor is not recorded")
    if ancestor.get("decision_verdict") != "DEFERRED_WITH_REASON" or not (ancestor.get("comparison_review") or {}).get("decision_evidence_refs"):
        fail("AutoGen historical deferral must have explicit upstream maintenance evidence")

    deerflow = by_id.get("candidate-deerflow")
    if not deerflow:
        fail("DeerFlow challenger disappeared from canonical registry")
    if deerflow.get("source_item_id") is not None:
        fail("DeerFlow must not change the original 68-item source inventory")
    if "full_replacement" not in (deerflow.get("comparison_review") or {}).get("variants", []):
        fail("DeerFlow may not be limited to pattern-only adoption")
    if deerflow.get("authority_role") != "NONE" and deerflow.get("lifecycle_state") != "PRODUCTION":
        fail("research-stage DeerFlow gained authority without production promotion")

    routing_problems = evaluation_route_issues(items, lanes)
    if routing_problems:
        fail("candidate evaluation route integrity: " + "; ".join(routing_problems[:5]))

    # Mandatory negative control: an unqueued new contender cannot silently remain unscheduled.
    test_candidate = next(
        (item for item in items if item.get("candidate_id") == "candidate-kittenml-kittentts"), None
    )
    if not test_candidate or not isinstance(test_candidate.get("evaluation_route"), dict):
        fail("KittenTTS regression exemplar is absent or lacks an actionable route")
    without_route = dict(test_candidate)
    without_route.pop("evaluation_route", None)
    test_items = [without_route]
    if not evaluation_route_issues(test_items, lanes):
        fail("candidate evaluation routing negative control failed to detect forgotten challenger")


# Source-fixed 2026-10-16 browser tools intake regression; the JSON receipt is not an authority or scheduler.
OWNER_BROWSER_20261016_SOURCES = {
    "lexmount/moli", "browser-use/browser-use", "browser-use/browser-harness",
    "browser-use/web-ui", "browser-use/bux", "guycrespin/browser-agent",
    "scrapeless-ai/scrapeless-agent-browser", "pedro-scrapeless/scrapeless-playwright",
    "lightpanda-io/browser", "CloakHQ/CloakBrowser", "h4ckf0r0day/obscura",
    "apify/crawlee", "Skyvern-AI/skyvern", "FlareSolverr/FlareSolverr",
    "browserless/browserless", "jo-inc/camofox-browser", "ntegrals/openbrowser",
    "berstend/puppeteer-extra", "autoscrape-labs/pydoll", "GoogleChrome/rendertron",
}


def owner_browser_20261016_problems(items: list[dict], lanes: list[dict], receipt: dict) -> list[str]:
    problems: list[str] = []
    if receipt.get("schema") != "velvetos.office-v2.browser-automation-intake.v1":
        problems.append("batch schema changed")
    if receipt.get("status") != "RESEARCH_ROUTED_NOT_EXECUTED":
        problems.append("batch falsely claims execution")
    if receipt.get("counts") != {
        "total": 20, "p0_queued": 5, "phase_routed": 13, "reference_only": 2,
    }:
        problems.append("batch disposition counts drifted")
    records = receipt.get("items")
    if not isinstance(records, list) or len(records) != 20:
        return problems + ["batch lost or duplicated source records"]
    expected_urls = {"https://github.com/" + r.lower() for r in OWNER_BROWSER_20261016_SOURCES}
    actual_urls = [str(r.get("url", "")).lower().rstrip("/") for r in records]
    if set(actual_urls) != expected_urls or len(set(actual_urls)) != len(records):
        problems.append("source URL set lost, duplicated or aliased")
    by_id = {i.get("candidate_id"): i for i in items}
    by_lane = {lane.get("lane_id"): lane for lane in lanes}
    seen_ids = set()
    for r in records:
        cid = r.get("candidate_id")
        if cid in seen_ids:
            problems.append("repeated browser candidate id: " + str(cid))
        seen_ids.add(cid)
        repo = str(r.get("url", "")).lower().removeprefix("https://github.com/").rstrip("/")
        if cid != "candidate-" + repo.replace("/", "-"):
            problems.append("source-to-candidate id mismatch: " + str(cid))
        item = by_id.get(cid)
        if not item:
            problems.append("missing canonical browser candidate: " + str(cid))
            continue
        if item.get("source_item_id") is not None or item.get("provenance_class") != "OWNER_REQUEST_2026_10_16_BROWSER_AUTOMATION":
            problems.append("historical source or provenance changed: " + cid)
        if item.get("lifecycle_state") != "RESEARCHED" or item.get("runtime_verification") != "NOT_RUN" or item.get("authority_role") != "NONE":
            problems.append("browser candidate was falsely promoted: " + cid)
        if r.get("url") not in (item.get("evidence_refs") or []):
            problems.append("candidate missing exact source provenance: " + cid)
        review = item.get("comparison_review") or {}
        if review.get("policy") != COMPETITOR_POLICY or review.get("evidence_status") != "RESEARCH_ONLY":
            problems.append("candidate falsely benchmarked or lost review: " + cid)
        route = item.get("evaluation_route") or {}
        if (route.get("owner_ref") != r.get("owner_ref")
                or route.get("workstream") != r.get("evaluation_lane")
                or route.get("status") != "WAITING_GATE"
                or not route.get("next_gate")):
            problems.append("candidate lost phase owner, gate or status: " + cid)
        kind = r.get("route_kind")
        p0lane = r.get("p0_lane")
        if kind == "P0_QUEUED":
            lane = by_lane.get(p0lane) or {}
            if not lane or cid not in (lane.get("queued_challengers") or []):
                problems.append("queued browser candidate omitted from P0: " + cid)
            if cid in (lane.get("challengers") or []):
                problems.append("browser candidate promoted into active shortlist: " + cid)
            if p0lane not in (item.get("shortlist_lanes") or []):
                problems.append("candidate missing declared P0 lane: " + cid)
            if item.get("decision_verdict") != "BENCHMARK_REQUIRED":
                problems.append("queued candidate lost comparison: " + cid)
        elif kind == "PHASE_ROUTED":
            if p0lane is not None or r.get("evaluation_lane") not in (item.get("shortlist_lanes") or []):
                problems.append("phase route missing or incorrectly P0 queued: " + cid)
            if item.get("decision_verdict") != "BENCHMARK_REQUIRED":
                problems.append("routed candidate lost comparison: " + cid)
        elif kind == "REFERENCE_ONLY":
            if (p0lane is not None or item.get("decision_verdict") != "DEFERRED_WITH_REASON"
                    or review.get("eligibility") != "DEFERRED_WITH_REASON"
                    or not review.get("decision_evidence_refs")):
                problems.append("source-only example/deprecated tool improperly promoted: " + cid)
        else:
            problems.append("unrecognized browser route kind: " + str(kind))
    return problems


def validate_owner_browser_20261016(items: list[dict], lanes: list[dict]) -> None:
    receipt = load(P2 / "browser-automation-intake-2026-10-16.json")
    errors = owner_browser_20261016_problems(items, lanes, receipt)
    if errors:
        fail("browser tool intake: " + "; ".join(errors[:5]))

    # Negative controls: missing candidate, duplicate upstream URL, dropped P0
    # lane, and unearned LAB/authority promotion must independently fail.
    records = receipt["items"]
    dropped = [x for x in items if x["candidate_id"] != records[0]["candidate_id"]]
    if not owner_browser_20261016_problems(dropped, lanes, receipt):
        fail("browser intake missing-record negative control failed")
    duplicate = dict(receipt)
    duplicate["items"] = records[:-1] + [dict(records[0])]
    if not owner_browser_20261016_problems(items, lanes, duplicate):
        fail("browser intake duplicate-source negative control failed")
    queued = next(r for r in records if r["route_kind"] == "P0_QUEUED")
    without_queue = [
        {**lane, "queued_challengers": [
            x for x in lane.get("queued_challengers", []) if x != queued["candidate_id"]
        ]} if lane["lane_id"] == queued["p0_lane"] else lane
        for lane in lanes
    ]
    if not owner_browser_20261016_problems(items, without_queue, receipt):
        fail("browser intake missing-P0-queue negative control failed")
    promoted = [
        {**x, "authority_role": "PRODUCTION_INCUMBENT"}
        if x["candidate_id"] == records[0]["candidate_id"] else x for x in items
    ]
    if not owner_browser_20261016_problems(promoted, lanes, receipt):
        fail("browser intake false-production negative control failed")


def validate_owner_repo_batch_20261013(items: list[dict], lanes: list[dict]) -> None:
    """Keep the owner's 19-repo intake complete, source-linked and explicitly non-authorizing."""
    receipt = load(P2 / "owner-repo-intake-2026-10-13.json")
    if receipt.get("schema") != "velvetos.office-v2.owner-repo-batch-intake.v1":
        fail("owner repo intake receipt schema changed")
    records = receipt.get("items") or []
    if len(records) != 19 or receipt.get("counts") != {"total": 19, "p0_queued": 9, "phase_routed": 10}:
        fail("owner repo intake lost source records or its disposition counts")
    ids = [r.get("candidate_id") for r in records]
    urls = [str(r.get("url") or "").lower().rstrip("/") for r in records]
    expected_ids = {
        "candidate-cyan4973-xxhash", "candidate-isair-jarvis",
        "candidate-esengine-deepseek-reasonix", "candidate-mpfaffenberger-code-puppy",
        "candidate-hiyouga-llamafactory", "candidate-rtk-ai-rtk",
        "candidate-tirth8205-code-review-graph", "candidate-oraios-serena",
        "candidate-qwenlm-qwen-code", "candidate-kilo-org-kilocode",
        "candidate-cobusgreyling-loop-engineering",
        "candidate-gentleman-programming-gentle-ai", "candidate-mvschwarz-openrig",
        "candidate-yaoapp-yao", "candidate-anus-dev-anus",
        "candidate-kunagent-kun", "candidate-q00-ouroboros",
        "candidate-nexu-io-html-video", "candidate-mikedev115-aetox-harness",
    }
    if set(ids) != expected_ids or len(set(urls)) != 19:
        fail("owner repo intake source IDs/URLs changed, duplicated or disappeared")
    p0 = next((lane for lane in lanes if lane.get("lane_id") == "agent-runtime"), None)
    if not p0:
        fail("owner repo intake: canonical agent-runtime lane missing")
    queued = set(p0.get("queued_challengers") or [])

    def issues(actual_items: list[dict], actual_queue: set[str]) -> list[str]:
        problems: list[str] = []
        by_id = {c["candidate_id"]: c for c in actual_items}
        count_queue = 0
        for r in records:
            cid, url = r["candidate_id"], r["url"]
            item = by_id.get(cid)
            if item is None:
                problems.append(f"missing candidate {cid}")
                continue
            if item.get("source_item_id") is not None:
                problems.append(f"historic-source contamination {cid}")
            if (item.get("lifecycle_state") != "RESEARCHED"
                or item.get("decision_verdict") != "BENCHMARK_REQUIRED"
                or item.get("runtime_verification") != "NOT_RUN"
                or item.get("authority_role") != "NONE"):
                problems.append(f"unearned promotion {cid}")
            refs = item.get("evidence_refs") or []
            if url not in refs or (url + "/tree/" + str(r.get("upstream_pin"))) not in refs:
                problems.append(f"source/provenance missing {cid}")
            if r.get("lane") not in (item.get("shortlist_lanes") or []):
                problems.append(f"comparison route missing {cid}")
            route = item.get("evaluation_route") or {}
            if (route.get("owner_ref") != r.get("owner_issue")
                or route.get("workstream") != r.get("lane")
                or not route.get("next_gate") or not route.get("unlock_condition")):
                problems.append(f"owner or next gate missing {cid}")
            if r.get("route_kind") == "P0_QUEUED":
                count_queue += 1
                if cid not in actual_queue:
                    problems.append(f"lost P0 queued challenger {cid}")
            elif r.get("route_kind") != "PHASE_ROUTED" or cid in actual_queue:
                problems.append(f"wrong phase/P0 classification {cid}")
        if count_queue != 9:
            problems.append("P0 routed count changed")
        return problems

    problems = issues(items, queued)
    if problems:
        fail("owner repo intake integrity: " + "; ".join(problems[:5]))
    # Deliberate negative controls: each independent omission is detected.
    without_candidate = [item for item in items if item["candidate_id"] != records[0]["candidate_id"]]
    if not issues(without_candidate, queued):
        fail("owner repo intake dropped-candidate negative control failed")
    first_p0 = next(r["candidate_id"] for r in records if r["route_kind"] == "P0_QUEUED")
    if not issues(items, queued - {first_p0}):
        fail("owner repo intake dropped-queue negative control failed")



def validate_owner_assurance_binary_tools_20261014(items: list[dict], lanes: list[dict]) -> None:
    """Protect the owner's three 2026-10-14 source/phase routes without activating a tool."""
    receipt = load(P2 / "owner-assurance-binary-tools-intake-2026-10-14.json")
    if receipt.get("schema") != "velvetos.office-v2.owner-assurance-binary-intake.v1":
        fail("assurance/binary intake receipt schema changed")
    if receipt.get("status") != "RESEARCH_ROUTED_NOT_EXECUTED" or receipt.get("counts") != {
        "total": 3, "p0_queued": 0, "phase_routed": 3,
    }:
        fail("assurance/binary intake state or counts drifted")
    records = receipt.get("items") or []
    expected = {
        "candidate-ifixai-ai-ifixai": (
            "https://github.com/ifixai-ai/iFixAi", "agent-quality-evaluation",
            "agent-quality", "https://github.com/nocturney/velvetos-core/issues/612",
            "telemetry",
        ),
        "candidate-vxcontrol-pentagi": (
            "https://github.com/vxcontrol/pentagi", "security-assurance",
            "security-assurance", "https://github.com/nocturney/velvetos-core/issues/595",
            "CVE-2026-14784",
        ),
        "candidate-nsa-ghidra": (
            "https://github.com/NationalSecurityAgency/ghidra", "binary-analysis",
            "shipped-artifact-analysis",
            "https://github.com/nocturney/velvetos-core/issues/606", "JDK 25",
        ),
    }
    if len(records) != 3 or {r.get("candidate_id") for r in records} != set(expected):
        fail("assurance/binary intake lost or duplicated its three sources")
    docpath = P2 / "owner-assurance-binary-tools-intake-2026-10-14.md"
    doc = docpath.read_text(encoding="utf-8-sig")
    p0_ids: set[str] = set()
    for lane in lanes:
        p0_ids.add(lane.get("incumbent"))
        p0_ids.update(lane.get("challengers") or [])
        p0_ids.update(lane.get("queued_challengers") or [])

    def issues(checked_items: list[dict]) -> list[str]:
        problems: list[str] = []
        by_id = {item["candidate_id"]: item for item in checked_items}
        for record in records:
            cid = record["candidate_id"]
            expected_url, expected_lane, expected_workstream, expected_owner, risk_marker = expected[cid]
            item = by_id.get(cid)
            if not item:
                problems.append(f"missing candidate {cid}")
                continue
            pin = record.get("upstream_pin") or ""
            pinned = expected_url + "/tree/" + pin
            if (record.get("url") != expected_url or len(pin) != 40 or
                any(c not in "0123456789abcdef" for c in pin) or
                record.get("lane") != expected_lane or
                record.get("workstream") != expected_workstream or
                record.get("owner_issue") != expected_owner or
                record.get("route_kind") != "PHASE_ROUTED"):
                problems.append(f"source/owner intake receipt drift {cid}")
            if cid in p0_ids:
                problems.append(f"research-only tool allocated a core P0 slot {cid}")
            if item.get("source_item_id") is not None:
                problems.append(f"closed historical import contaminated {cid}")
            if (item.get("provenance_class") != "OWNER_SUBMITTED_3_GITHUB_REPOS_2026_10_14"
                or item.get("lifecycle_state") != "RESEARCHED"
                or item.get("decision_verdict") != "BENCHMARK_REQUIRED"
                or item.get("runtime_verification") != "NOT_RUN"
                or item.get("authority_role") != "NONE"):
                problems.append(f"unearned promotion or provenance drift {cid}")
            refs = item.get("evidence_refs") or []
            if expected_url not in refs or pinned not in refs:
                problems.append(f"missing original source and immutable upstream pin {cid}")
            if item.get("shortlist_lanes") != [expected_lane]:
                problems.append(f"incorrect phase evaluation lane {cid}")
            review = item.get("comparison_review") or {}
            if (review.get("policy") != "COMPETITOR_NEUTRAL_ADMISSION_V1" or
                review.get("eligibility") != "OPEN_FOR_COMPARISON" or
                review.get("evidence_status") != "RESEARCH_ONLY"):
                problems.append(f"candidate comparison/evidence state drift {cid}")
            route = item.get("evaluation_route") or {}
            if (route.get("owner_ref") != expected_owner or
                route.get("workstream") != expected_workstream or
                route.get("status") != "WAITING_GATE" or
                route.get("next_gate") != record.get("next_gate") or
                route.get("unlock_condition") != record.get("unlock_condition")):
                problems.append(f"lost exact phase owner or unlock condition {cid}")
            if not all(token.lower() in doc.lower() for token in (cid, pin, risk_marker)):
                problems.append(f"intake explanation/safety evidence missing {cid}")
            if risk_marker.lower() not in " ".join(item.get("platform_constraints") or []).lower():
                problems.append(f"safety/cost limitation missing from candidate {cid}")
        return problems

    problems = issues(items)
    if problems:
        fail("assurance/binary owner intake integrity: " + "; ".join(problems[:6]))
    # Deliberate negative controls: source omission, route loss and false LAB success.
    for cid in expected:
        without = [item for item in items if item["candidate_id"] != cid]
        if not issues(without):
            fail("assurance/binary dropped-candidate negative control failed: " + cid)
    lost_route = [
        {**item, "evaluation_route": {}} if item["candidate_id"] == "candidate-ifixai-ai-ifixai"
        else item for item in items
    ]
    if not issues(lost_route):
        fail("assurance/binary missing-route negative control failed")
    premature = [
        {**item, "runtime_verification": "PASS"}
        if item["candidate_id"] == "candidate-vxcontrol-pentagi"
        else item for item in items
    ]
    if not issues(premature):
        fail("assurance/binary false-runtime-attestation negative control failed")



def validate_owner_llamafile_20261014(items: list[dict], lanes: list[dict]) -> None:
    """Make this source-pinned provider research intake impossible to silently lose."""
    cid = "candidate-mozilla-ai-llamafile"
    source_url = "https://github.com/mozilla-ai/llamafile"
    upstream_sha = "a3ccf098ed9c7c77687f5430b0143156d3bcc45a"
    owner_issue = "https://github.com/nocturney/velvetos-core/issues/612"
    receipt = load(P2 / "owner-local-inference-llamafile-intake-2026-10-14.json")
    doc = (P2 / "owner-local-inference-llamafile-intake-2026-10-14.md").read_text(encoding="utf-8-sig")
    phase3 = (ROOT / "docs/implementation/office-v2/phase3c/README.md").read_text(encoding="utf-8-sig")
    active_or_queued = set()
    for lane in lanes:
        active_or_queued.add(lane.get("incumbent"))
        active_or_queued.update(lane.get("challengers") or [])
        active_or_queued.update(lane.get("queued_challengers") or [])

    def issues(records: list[dict]) -> list[str]:
        problems = []
        by_id = {candidate.get("candidate_id"): candidate for candidate in records}
        candidate = by_id.get(cid)
        if (receipt.get("schema") != "velvetos.office-v2.owner-local-inference-intake.v1"
            or receipt.get("status") != "RESEARCH_ROUTED_NOT_EXECUTED"
            or receipt.get("candidate_id") != cid
            or receipt.get("url") != source_url
            or receipt.get("upstream_pin") != upstream_sha
            or receipt.get("owner_issue") != owner_issue
            or receipt.get("workstream") != "local-model-inference"
            or receipt.get("route_kind") != "PHASE_ROUTED"
            or receipt.get("p0_shortlist_changed") is not False
            or receipt.get("runtime_executed") is not False
            or receipt.get("paid_inference_authorized") is not False):
            problems.append("source, phase owner or no-execution receipt drift")
        if candidate is None:
            return problems + ["missing owner-supplied llamafile candidate"]
        if cid in active_or_queued:
            problems.append("research-only local runner promoted to a P0 shortlist")
        if (candidate.get("source_item_id") is not None
            or candidate.get("provenance_class") != "OWNER_SUBMITTED_SINGLE_GITHUB_REPO_2026_10_14"
            or candidate.get("lifecycle_state") != "RESEARCHED"
            or candidate.get("decision_verdict") != "BENCHMARK_REQUIRED"
            or candidate.get("runtime_verification") != "NOT_RUN"
            or candidate.get("authority_role") != "NONE"):
            problems.append("historical contamination or unearned promotion")
        if candidate.get("shortlist_lanes") != ["local-model-inference"]:
            problems.append("not a local model inference provider")
        refs = candidate.get("evidence_refs") or []
        if source_url not in refs or source_url + "/tree/" + upstream_sha not in refs:
            problems.append("exact upstream identity or pin disappeared")
        review = candidate.get("comparison_review") or {}
        if (review.get("policy") != "COMPETITOR_NEUTRAL_ADMISSION_V1"
            or review.get("eligibility") != "OPEN_FOR_COMPARISON"
            or review.get("evidence_status") != "RESEARCH_ONLY"):
            problems.append("invalid research-only competitor review")
        route = candidate.get("evaluation_route") or {}
        if (route.get("workstream") != "local-model-inference"
            or route.get("owner_ref") != owner_issue
            or route.get("status") != "WAITING_GATE"
            or route.get("next_gate") != receipt.get("next_gate")
            or route.get("unlock_condition") != receipt.get("unlock_condition")):
            problems.append("phase routing owner or unlock gate missing")
        for marker in (cid, upstream_sha, "Ollama", "NO_NEW_RECURRING_COST"):
            if marker not in doc:
                problems.append("source or benchmark context missing: " + marker)
        if cid not in phase3 or "Ollama" not in phase3:
            problems.append("Phase 3C local provider handoff missing")
        return problems

    if issues(items):
        fail("llamafile local inference intake: " + "; ".join(issues(items)[:6]))
    if not issues([x for x in items if x.get("candidate_id") != cid]):
        fail("llamafile omitted candidate negative control failed")
    if not issues([
        {**x, "evaluation_route": {}} if x.get("candidate_id") == cid else x
        for x in items
    ]):
        fail("llamafile lost route negative control failed")
    if not issues([
        {**x, "runtime_verification": "PASS"} if x.get("candidate_id") == cid else x
        for x in items
    ]):
        fail("llamafile false runtime success negative control failed")
    if not issues([
        {**x, "evidence_refs": [ref for ref in x.get("evidence_refs", [])
                               if ref != source_url + "/tree/" + upstream_sha]}
        if x.get("candidate_id") == cid else x for x in items
    ]):
        fail("llamafile lost source-pin negative control failed")


def main() -> None:
    missing = [str(p.relative_to(ROOT)) for p in REQUIRED if not p.is_file()]
    if missing:
        fail("missing Phase 2 files: " + ", ".join(missing))

    lifecycle = load(P2 / "candidate-lifecycle-v0.json")
    if lifecycle.get("forward_states") != EXPECTED_FORWARD:
        fail("candidate forward lifecycle mismatch")
    if lifecycle.get("exit_verdicts") != EXPECTED_EXIT:
        fail("candidate exit verdicts mismatch")

    registry = load(P2 / "candidate-registry-v0.json")
    if registry.get("status") != "CLOSED_IMPORT":
        fail("candidate registry import is not closed")
    items = registry.get("items") or []
    if len(items) < 68:
        fail(f"candidate registry incomplete: {len(items)} < 68")
    if registry.get("source_item_count") != 68 or registry.get("imported_source_item_count") != 68:
        fail("candidate registry must preserve the complete 68-item source import")
    source_ids = [x.get("source_item_id") for x in items if x.get("source_item_id") is not None]
    if len(source_ids) != 68 or len(set(source_ids)) != 68:
        fail("candidate registry source_item_id coverage is not exactly 68 unique items")
    ids = [x.get("candidate_id") for x in items]
    if len(ids) != len(set(ids)):
        fail("candidate registry ids are not unique")
    meaningful = set(lifecycle.get("decision_verdicts") or []) | set(EXPECTED_EXIT)
    for item in items:
        if item.get("lifecycle_state") not in set(EXPECTED_FORWARD):
            fail("invalid lifecycle state for " + str(item.get("candidate_id")))
        if item.get("decision_verdict") not in meaningful:
            fail("missing meaningful verdict for " + str(item.get("candidate_id")))
        if not item.get("evidence_refs"):
            fail("candidate missing evidence refs: " + str(item.get("candidate_id")))

    shortlists = load(P2 / "p0-shortlists-v0.json")
    lanes = shortlists.get("lanes") or []
    if not lanes:
        fail("P0 shortlists are empty")
    known = set(ids)
    for lane in lanes:
        incumbent = lane.get("incumbent")
        challengers = lane.get("challengers") or []
        if not incumbent or incumbent not in known:
            fail("shortlist incumbent missing from registry: " + str(lane.get("lane_id")))
        if not 2 <= len(challengers) <= 3:
            fail("shortlist must have 2-3 challengers: " + str(lane.get("lane_id")))
        if lane.get("lane_id") == "durable-execution":
            if lane.get("winner") != "candidate-restate":
                fail("closed durable-execution lane must record Restate winner")
            if lane.get("fallback") != "candidate-temporal":
                fail("closed durable-execution lane must record Temporal fallback")
            if lane.get("freeze_state") != "FROZEN_AFTER_PHASE3A_BAKEOFF":
                fail("closed durable-execution lane freeze state mismatch")
            if lane.get("verdict_receipt") != "docs/implementation/office-v2/phase3/durable-execution-verdict-v0.json":
                fail("closed durable-execution lane verdict provenance missing")
        elif lane.get("winner") is not None:
            fail("open pre-benchmark shortlist must not declare a winner: " + str(lane.get("lane_id")))
        if any(c not in known for c in challengers):
            fail("shortlist challenger missing from registry: " + str(lane.get("lane_id")))

    validate_competitor_neutrality(registry, items, lanes)
    validate_owner_repo_batch_20261013(items, lanes)
    validate_owner_browser_20261016(items, lanes)
    validate_owner_assurance_binary_tools_20261014(items, lanes)
    validate_owner_llamafile_20261014(items, lanes)

    # Strict research-only agent-composition intake: no automatic admission,
    # dual scheduler, OpenDots alias substitution, spend or authority promotion.
    composition = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vf_office_v2_agent_composition_gate.py"), "selftest"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    )
    if composition.returncode != 0 or "OK office-v2-agent-composition" not in composition.stdout:
        fail("agent composition intake gate failed: " + (composition.stderr.strip() or composition.stdout.strip()))


    fixture_files = sorted(FIXTURES.glob("*.json"))
    fixture_ids = set()
    runner = ROOT / "scripts" / "vf_office_v2_golden_fixture.py"
    selftest = subprocess.run(
        [sys.executable, str(runner), "--self-test", "--json"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8"
    )
    if selftest.returncode != 0 or json.loads(selftest.stdout).get("status") != "PASS":
        fail("Golden Fixture runner self-test failed")
    for path in fixture_files:
        data = load(path)
        fixture_ids.add(data.get("fixture_id"))
        p = subprocess.run(
            [sys.executable, str(runner), "--validate", str(path), "--json"],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8"
        )
        if p.returncode != 0 or json.loads(p.stdout).get("status") != "PASS":
            fail("fixture validation failed: " + path.name)
    if fixture_ids != EXPECTED_FIXTURES:
        fail("Golden Fixture set mismatch")

    readme = (P2 / "README.md").read_text(encoding="utf-8-sig")
    for marker in (
        "Contracts come before executable fixtures",
        "incumbent plus 2–3 serious challengers",
        "No item may remain",
        "fitness, safety, operability and evidence",
    ):
        if marker not in readme:
            fail("Phase 2 README missing rule: " + marker)

    # #595 AC5/AC6: durable repo-link intake must keep links, dedupe and leave history intact.
    intake = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vf_office_v2_link_intake_selftest.py")],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=120,
    )
    if intake.returncode != 0:
        fail("link intake self-test failed: " + (intake.stderr or intake.stdout).strip()[-400:])

    print(
        f"OK office-v2-phase2 registry={len(items)} lifecycle=PASS "
        f"shortlists={len(lanes)} fixtures={len(fixture_ids)} research-freeze=DEFINED link-intake=PASS"
    )


if __name__ == "__main__":
    main()
