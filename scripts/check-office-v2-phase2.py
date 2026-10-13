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
    P2 / "admission-policy-v0.md",
    P2 / "scorecard.schema.json",
    P2 / "golden-fixture-contract.schema.json",
    P2 / "fixture-adapter-receipt.schema.json",
    P2 / "pattern-adoption-receipt.schema.json",
    P2 / "research-freeze-record.schema.json",
    P2 / "p0-shortlists-v0.json",
    ROOT / "scripts" / "vf_office_v2_golden_fixture.py",
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

    print(
        f"OK office-v2-phase2 registry={len(items)} lifecycle=PASS "
        f"shortlists={len(lanes)} fixtures={len(fixture_ids)} research-freeze=DEFINED"
    )


if __name__ == "__main__":
    main()
