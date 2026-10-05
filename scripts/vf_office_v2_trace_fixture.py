#!/usr/bin/env python3
"""Build/send a bounded OTLP/HTTP JSON trace carrying Office v2 correlation IDs."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCTOR = ROOT / "scripts" / "vf_office_v2_lab_doctor.py"
ENDPOINT = "http://127.0.0.1:14318/v1/traces"


def hex_id(seed: str, length: int) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:length]


def make_payload(c: dict[str, str], start_ns: int | None = None) -> dict[str, Any]:
    required = ["request_id", "project_id", "workflow_id", "run_id", "attempt_id"]
    missing = [k for k in required if not c.get(k)]
    if missing:
        raise ValueError("missing correlation ids: " + ",".join(missing))

    start = start_ns or time.time_ns()
    end = start + 1_000_000
    attrs = [
        {"key": f"velvetos.{key}", "value": {"stringValue": value}}
        for key, value in c.items()
        if value
    ]
    attrs.append({"key": "service.name", "value": {"stringValue": "officev2-phase1-fixture"}})
    return {
        "resourceSpans": [{
            "resource": {"attributes": [
                {"key": "service.name", "value": {"stringValue": "officev2-phase1-fixture"}},
                {"key": "velvetos.authority", "value": {"stringValue": "none"}},
            ]},
            "scopeSpans": [{
                "scope": {"name": "velvetos.officev2.phase1"},
                "spans": [{
                    "traceId": hex_id(c["run_id"], 32),
                    "spanId": hex_id(c["attempt_id"], 16),
                    "name": "officev2.phase1.correlation_fixture",
                    "kind": 1,
                    "startTimeUnixNano": str(start),
                    "endTimeUnixNano": str(end),
                    "attributes": attrs,
                }],
            }],
        }],
    }


def doctor_ready() -> tuple[bool, dict[str, Any]]:
    p = subprocess.run(
        [sys.executable, str(DOCTOR), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    if p.returncode != 0:
        return False, {"verdict": "DOCTOR_FAILED"}
    data = json.loads(p.stdout)
    return data.get("verdict") == "READY_FOR_LAB_RUNTIME", data


def send(payload: dict[str, Any]) -> dict[str, Any]:
    ready, health = doctor_ready()
    if not ready:
        return {"status": "BLOCKED", "reason": "LAB doctor is not ready", "doctor": health}
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {"status": "PASS" if 200 <= resp.status < 300 else "FAIL", "http_status": resp.status}
    except Exception as exc:
        return {"status": "FAIL", "error": str(exc)}


def self_test() -> dict[str, Any]:
    c = {
        "request_id": "req-fixture",
        "project_id": "project-fixture",
        "workflow_id": "workflow-fixture",
        "run_id": "run-fixture",
        "attempt_id": "attempt-fixture",
        "node_id": "windows-primary",
    }
    payload = make_payload(c, 1_000_000_000)
    span = payload["resourceSpans"][0]["scopeSpans"][0]["spans"][0]
    keys = {a["key"] for a in span["attributes"]}
    expected = {f"velvetos.{k}" for k in c}
    ok = (
        len(span["traceId"]) == 32
        and len(span["spanId"]) == 16
        and expected.issubset(keys)
        and span["startTimeUnixNano"] == "1000000000"
    )
    return {"status": "PASS" if ok else "FAIL", "attribute_count": len(keys), "network_calls": 0}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request-id")
    ap.add_argument("--project-id")
    ap.add_argument("--workflow-id")
    ap.add_argument("--run-id")
    ap.add_argument("--attempt-id")
    ap.add_argument("--node-id", default="windows-primary")
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        result = self_test()
        print(json.dumps(result, ensure_ascii=False) if args.json else json.dumps(result, indent=2))
        return 0 if result["status"] == "PASS" else 1

    c = {
        "request_id": args.request_id,
        "project_id": args.project_id,
        "workflow_id": args.workflow_id,
        "run_id": args.run_id,
        "attempt_id": args.attempt_id,
        "node_id": args.node_id,
    }
    try:
        payload = make_payload({k: v for k, v in c.items() if v})
    except ValueError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}))
        return 2

    result = send(payload) if args.send else {"status": "DRY_RUN", "endpoint": ENDPOINT, "payload": payload, "network_calls": 0}
    print(json.dumps(result, ensure_ascii=False) if args.json else json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"PASS", "DRY_RUN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
