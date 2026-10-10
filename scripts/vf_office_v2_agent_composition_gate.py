#!/usr/bin/env python3
"""Phase 2 research-only agent composition gate (offline, standard library)."""
from __future__ import annotations
import copy
import json
import sys
from pathlib import Path

P2 = Path(__file__).resolve().parents[1] / "docs" / "implementation" / "office-v2" / "phase2"
SOURCES = {
    "candidate-rakazo": "https://github.com/elie222/rakazo",
    "candidate-hermes-agent": "https://github.com/NousResearch/hermes-agent",
    "candidate-agent-zero": "https://github.com/agent0ai/agent-zero",
    "candidate-copilotkit-openbot": "https://github.com/CopilotKit/OpenBot",
    "candidate-copilotkit-openmuse": "https://github.com/CopilotKit/openmuse",
    "candidate-copilotkit-opendots": "https://github.com/CopilotKit/OpenDots",
    "candidate-anil-open-dots": "https://github.com/Anil-matcha/open-dots",
    "candidate-diggerhq-opendots": "https://github.com/diggerhq/opendots",
}
PHASES = {"PHASE_2", "P0_612", "PHASE_3A", "PHASE_3B", "PHASE_3C",
          "PHASE_3D", "PHASE_3E_604", "SHADOW_PILOT_PRODUCTION"}
VARIANTS = {"A_INCUMBENT_ONLY", "B_ONE_SPECIALIST", "C_MODULAR_COMPOSITION"}
FIXTURES = {"instagram-request-publish-live-verify",
            "customer-quote-production-ready-paid", "3d-asset-dcc-slice-artifact",
            "agent-approval-effect-reconciliation", "long-job-crash-resume",
            "morning-brief-compose-send-verify"}
NO_AUTHORITY = {"new_scheduler_or_queue_allowed", "production_authority_change",
                "production_writer_change", "production_credentials_allowed",
                "new_recurring_cost_allowed", "codex_cli_allowed",
                "unreviewed_host_access_allowed", "provider_invocation_at_intake_allowed",
                "unverified_fixture_claims_allowed", "canonical_memory_replacement_allowed"}

def check(plan: dict, registry: dict, shortlists: dict) -> None:
    def demand(condition: bool, error: str) -> None:
        if not condition:
            raise ValueError(error)
    demand(plan.get("schema") == "velvetos.office-v2.phase2-agent-composition-plan.v0"
           and plan.get("status") == "RESEARCH_INTAKE_ONLY_NO_LAB", "invalid plan state")
    demand(str(plan.get("owner_issue")).endswith("/612")
           and str(plan.get("fleet_owner_issue")).endswith("/604"), "owner route changed")
    flags = plan.get("no_authority_expansion") or {}
    demand(set(flags) == NO_AUTHORITY and all(value is False for value in flags.values()),
           "research granted model/credential/cost/production authority")
    ids = plan.get("new_candidate_ids") or []
    demand(len(ids) == len(SOURCES) and set(ids) == set(SOURCES), "candidate inventory drift")
    entries = registry.get("items") or []
    demand(registry.get("candidate_count") == len(entries), "candidate count drift")
    byid = {x["candidate_id"]: x for x in entries}
    demand(len(entries) == len(byid), "duplicate candidate ids")
    lanes = {x["lane_id"]: x for x in shortlists.get("lanes") or []}
    for cid, upstream in SOURCES.items():
        entry = byid.get(cid) or {}
        demand(entry.get("source_item_id") is None and upstream in entry.get("evidence_refs", []),
               "missing/wrong source identity: " + cid)
        demand(entry.get("lifecycle_state") == "RESEARCHED"
               and entry.get("decision_verdict") == "BENCHMARK_REQUIRED"
               and entry.get("runtime_verification") == "NOT_RUN"
               and entry.get("authority_role") == "NONE", "unearned status/authority: " + cid)
        review = entry.get("comparison_review") or {}
        demand(review.get("eligibility") == "OPEN_FOR_COMPARISON"
               and review.get("evidence_status") == "RESEARCH_ONLY"
               and set(review.get("variants") or []) ==
               {"full_replacement", "component_replacement", "hybrid"},
               "candidate comparison claim wrong: " + cid)
        demand(bool(entry.get("shortlist_lanes")), "no lanes for " + cid)
        for lid in entry["shortlist_lanes"]:
            lane = lanes.get(lid) or {}
            demand(cid in lane.get("queued_challengers", [])
                   and cid not in lane.get("challengers", []), "agent bypassed review queue: " + cid)
    historical = byid.get("candidate-opendots") or {}
    demand(historical.get("source_item_id") == "candidate-opendots"
           and historical.get("authority_role") == "NONE"
           and historical.get("shortlist_lanes") == []
           and all("candidate-opendots" not in x.get("queued_challengers", [])
                   for x in lanes.values()), "ambiguous historical OpenDots source aliased")
    letta = byid.get("candidate-letta") or {}
    demand(letta.get("source_item_id") == "candidate-letta"
           and letta.get("runtime_verification") == "NOT_RUN"
           and letta.get("authority_role") == "NONE"
           and "candidate-letta" in lanes["memory-context"].get("queued_challengers", []),
           "historical Letta lineage/queue/authority drift")
    variants = plan.get("variants") or []
    demand(len(variants) == 3 and {x.get("id") for x in variants} == VARIANTS,
           "A/B/C variants missing")
    demand(all(x.get("single_task_owner") is True
               and x.get("production_enabled_by_plan") is False for x in variants),
           "second scheduler or production promotion")
    demand(next(x for x in variants if x["id"] == "B_ONE_SPECIALIST").get(
        "mutually_exclusive_specialist") is True, "parallel specialist owners")
    bench = plan.get("benchmark") or {}
    demand(bench.get("status") == "NOT_RUN" and bench.get("scorecards") == []
           and bench.get("winner") is None, "fabricated benchmark evidence")
    demand(set(bench.get("fixture_ids") or []) == FIXTURES
           and "scorecard.schema.json" in bench.get("scorecard_schema", "")
           and len(bench.get("negative_controls") or []) >= 8, "missing fixture/QA coverage")
    gates = plan.get("phase_gates") or []
    demand(len(gates) == len(PHASES) and {x.get("phase") for x in gates} == PHASES,
           "missing Office stage handoff")
    demand(any(x.get("phase") == "SHADOW_PILOT_PRODUCTION"
               and x.get("status") == "NOT_AUTHORIZED" for x in gates),
           "unearned future production stage")
    demand(lanes["durable-execution"].get("winner") == "candidate-restate"
           and lanes["agent-runtime"].get("incumbent") == "live-grokbot"
           and lanes["agent-runtime"].get("challengers") ==
           ["candidate-herdr", "candidate-pydantic-ai", "candidate-mastra"],
           "incumbent Restate/agent benchmark silently replaced")

def reject(plan: dict, registry: dict, shortlists: dict, description: str) -> None:
    try:
        check(plan, registry, shortlists)
    except (ValueError, KeyError, StopIteration, TypeError):
        return
    raise ValueError("negative control incorrectly accepted: " + description)

def selftest(plan: dict, registry: dict, shortlists: dict) -> None:
    check(plan, registry, shortlists)
    m = copy.deepcopy(plan)
    m["no_authority_expansion"]["new_recurring_cost_allowed"] = True
    reject(m, registry, shortlists, "unapproved spend")
    m = copy.deepcopy(plan)
    m["benchmark"]["winner"] = "candidate-rakazo"
    reject(m, registry, shortlists, "unverified winner")
    m = copy.deepcopy(registry)
    next(x for x in m["items"] if x["candidate_id"] == "candidate-rakazo")[
        "authority_role"] = "PRODUCTION_INCUMBENT"
    reject(plan, m, shortlists, "unauthorized production role")
    m = copy.deepcopy(shortlists)
    next(x for x in m["lanes"] if x["lane_id"] == "agent-runtime")[
        "queued_challengers"].remove("candidate-hermes-agent")
    reject(plan, registry, m, "dropped candidate")
    m = copy.deepcopy(registry)
    next(x for x in m["items"] if x["candidate_id"] == "candidate-copilotkit-opendots")[
        "evidence_refs"] = ["https://github.com/diggerhq/opendots"]
    reject(plan, m, shortlists, "upstream identity substitution")

def main() -> int:
    args = sys.argv[1:]
    if args not in ([], ["validate"], ["selftest"]):
        print("Usage: check-office-v2-agent-composition.py [validate|selftest]", file=sys.stderr)
        return 2
    try:
        plan = json.loads((P2 / "agent-composition-plan-v0.json").read_text(encoding="utf-8-sig"))
        reg = json.loads((P2 / "candidate-registry-v0.json").read_text(encoding="utf-8-sig"))
        shorts = json.loads((P2 / "p0-shortlists-v0.json").read_text(encoding="utf-8-sig"))
        (selftest if args == ["selftest"] else check)(plan, reg, shorts)
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as e:
        print("FAIL office-v2-agent-composition: " + str(e), file=sys.stderr)
        return 1
    print("OK office-v2-agent-composition candidates=8 variants=3 phase-gates=8 mode=" +
          ("selftest" if args == ["selftest"] else "validate"))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
