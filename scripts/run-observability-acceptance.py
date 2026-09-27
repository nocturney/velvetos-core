#!/usr/bin/env python3
"""Run one safe local VelvetOS flow and persist a sanitized trace receipt."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from vf_observability import LocalTrace, write_receipt
from openinference.semconv.trace import OpenInferenceSpanKindValues as Kind

def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args, cwd=ROOT, text=True, capture_output=True, timeout=90,
    )

def run_json(args: list[str]) -> tuple[int, dict]:
    proc = run(args)
    if proc.returncode != 0:
        return proc.returncode, {}
    try:
        return 0, json.loads(proc.stdout)
    except json.JSONDecodeError:
        return 3, {}

def stage_status(ok: bool) -> str:
    return "PASS" if ok else "FAIL"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--output",
        default="packages/vfharness/state/observability-phase2-2026-09-27.json",
    )
    args = ap.parse_args()
    output = (ROOT / args.output).resolve()
    try:
        output.relative_to(ROOT)
    except ValueError:
        print("FAIL output must stay inside repo", file=sys.stderr)
        return 2

    trace = LocalTrace()
    overall = True
    with trace.span("request", Kind.CHAIN, {
        "velvetos.stage": "request",
        "velvetos.status": "STARTED",
        "velvetos.component": "vfharness",
        "velvetos.incremental_cost_ils": 0,
    }) as root_span:
        with trace.span("routing", Kind.CHAIN, {
            "velvetos.stage": "routing",
            "velvetos.component": "project-request-gate",
            "velvetos.domain": "system_engineering",
        }) as span:
            rc, data = run_json([
                sys.executable, "scripts/vf_project_preflight.py",
                "--domain", "system_engineering",
                "--text", "Local zero-cost observability acceptance flow",
            ])
            ok = rc == 0 and data.get("project_preflight") == "PASS"
            span.set_attribute("velvetos.status", stage_status(ok))
            overall &= ok

        with trace.span("retrieval", Kind.RETRIEVER, {
            "velvetos.stage": "retrieval",
            "velvetos.component": "vfmem",
        }) as span:
            rc, data = run_json([
                sys.executable, "scripts/vfmem.py", "--json", "who", "harness",
            ])
            hits = data.get("hits") or []
            ok = rc == 0 and any(x.get("id") == "Pack:vfharness" for x in hits)
            span.set_attribute("velvetos.status", stage_status(ok))
            span.set_attribute("velvetos.hit_count", len(hits))
            span.set_attribute("velvetos.top_route", "Pack:vfharness" if ok else "none")
            overall &= ok

        with trace.span("agent", Kind.AGENT, {
            "velvetos.stage": "agent",
            "velvetos.component": "behavior-policy-target",
        }) as span:
            case = json.dumps(
                {"kind": "missing_authority", "authoritative_source": True},
                separators=(",", ":"),
            )
            proc = run([
                sys.executable,
                "packages/vfharness/evals/policy_target.py",
                case,
            ])
            decision = proc.stdout.strip()
            ok = proc.returncode == 0 and decision == "ALLOW|authority_present"
            span.set_attribute("velvetos.status", stage_status(ok))
            span.set_attribute("velvetos.decision", "ALLOW" if ok else "BLOCK")
            overall &= ok
        with trace.span("tool", Kind.TOOL, {
            "velvetos.stage": "tool",
            "velvetos.component": "cost-preflight",
        }) as span:
            rc, data = run_json([
                sys.executable, "scripts/vf_cost_preflight.py", "validate",
                "packages/vfharness/cost-preflight/opentelemetry-python-sdk-1.45.0.json",
            ])
            ok = rc == 0 and data.get("status") == "PASS"
            span.set_attribute("velvetos.status", stage_status(ok))
            span.set_attribute(
                "velvetos.cost_classification",
                str(data.get("classification", "unverified")),
            )
            overall &= ok

        with trace.span("approval", Kind.GUARDRAIL, {
            "velvetos.stage": "approval",
            "velvetos.component": "cost-policy",
        }) as span:
            approval_required = bool(data.get("explicit_approval_required", True))
            ok = rc == 0 and not approval_required
            span.set_attribute("velvetos.status", stage_status(ok))
            span.set_attribute("velvetos.approval_required", approval_required)
            overall &= ok
        with trace.span("execution", Kind.TOOL, {
            "velvetos.stage": "execution",
            "velvetos.component": "behavioral-evals-sensor",
        }) as span:
            proc = run([sys.executable, "scripts/check-behavioral-evals.py"])
            ok = proc.returncode == 0
            span.set_attribute("velvetos.status", stage_status(ok))
            overall &= ok

        with trace.span("readback", Kind.EVALUATOR, {
            "velvetos.stage": "readback",
            "velvetos.component": "promptfoo-config",
        }) as span:
            config = json.loads(
                (ROOT / "packages/vfharness/evals/promptfooconfig.json").read_text(
                    encoding="utf-8"
                )
            )
            case_count = len(config.get("tests") or [])
            ok = case_count == 17
            span.set_attribute("velvetos.status", stage_status(ok))
            span.set_attribute("velvetos.case_count", case_count)
            span.set_attribute("velvetos.readback_verified", ok)
            overall &= ok
        with trace.span("result", Kind.EVALUATOR, {
            "velvetos.stage": "result",
            "velvetos.component": "observability-acceptance",
        }) as span:
            span.set_attribute("velvetos.status", stage_status(overall))
            span.set_attribute("velvetos.incremental_cost_ils", 0)

        root_span.set_attribute("velvetos.status", stage_status(overall))

    spans = trace.snapshot()
    write_receipt(
        output,
        flow_status=stage_status(overall),
        spans=spans,
    )
    if not overall:
        print(f"FAIL observability flow; receipt={output.relative_to(ROOT)}", file=sys.stderr)
        return 2
    print(
        f"OK observability flow spans={len(spans)} "
        f"receipt={output.relative_to(ROOT)} cost=0"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
