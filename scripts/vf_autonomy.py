#!/usr/bin/env python3
"""VelvetOS autonomy composition — projections over existing Office/HQ sources of truth.

Compose next-action + safe execute over existing handlers.
No second queue/database/runtime. Orange/red stay gated by POLICY.

CLI:
  python3 scripts/vf_autonomy.py status
  python3 scripts/vf_autonomy.py next-action
  python3 scripts/vf_autonomy.py blockers
  python3 scripts/vf_autonomy.py approvals
  python3 scripts/vf_autonomy.py context <id>
  python3 scripts/vf_autonomy.py quiet-plan
  python3 scripts/vf_autonomy.py snapshot
  python3 scripts/vf_autonomy.py execute [--action ...] [--dry-run]
  python3 scripts/vf_autonomy.py selftest
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("Asia/Jerusalem")

CONFIG = ROOT / "packages" / "velvetos" / "living-studio" / "AUTONOMY.json"
OUT = ROOT / "packages" / "velvetos" / "living-studio" / "data" / "autonomy-latest.json"
RUNS = ROOT / "packages" / "velvetos" / "living-studio" / "data" / "autonomy-runs.jsonl"
INBOX = ROOT / "office" / "control" / "inbox.json"
FOLLOWUPS = ROOT / "office" / "control" / "followups.json"
DEAD = ROOT / "office" / "control" / "dead-letter.json"
DECISIONS = ROOT / "office" / "control" / "decisions.jsonl"
APPROVAL_QUEUE = ROOT / "packages" / "vfgrowth" / "data" / "approval-queue.json"
JOBS = ROOT / "office" / "ledger" / "live" / "jobs.csv"
JOBS_TEMPLATE = ROOT / "office" / "ledger" / "templates" / "jobs.csv"
POLICY = ROOT / "office" / "control" / "POLICY.md"
CONTROL_PLANE = ROOT / "office" / "control-plane.json"
INTAKE_RUNNER = ROOT / "packages" / "vfmedia" / "state" / "intake-runner.json"

RISK_ORDER = {"red": 0, "orange": 1, "yellow": 2, "green": 3, "": 4}
CLOSED_STATES = {"closed", "closed_verified", "completed", "done", "resolved"}
WAITING_PREFIXES = ("waiting_", "blocked")

# Actions autonomy may execute without owner (green/yellow internal)
SAFE_ACTIONS = {
    "reconcile_before_retry",
    "projection refresh",
    "projection_refresh",
    "refresh_projections",
    "media_intake_retry",
    "run_media_intake_status",
    "jobs_pull_status",
    "memory_context",
    "vfmem_who",
    "content_factory_prepare",
    "watchdog_repair",
    "health_repair",
    "followup_safe_transition",
    "review_current_state",
    "classify",
    "checkpoint",
    "context pack",
    "readiness check",
}


def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def load_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if raw:
            rows.append(json.loads(raw))
    return rows


def jobs_path() -> Path:
    return JOBS if JOBS.is_file() else JOBS_TEMPLATE


def load_jobs() -> list[dict[str, str]]:
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import vf_jobs_adapter as jobs_adapter  # noqa: WPS433

        return jobs_adapter.read_cache()
    except Exception:  # noqa: BLE001
        path = jobs_path()
        if not path.is_file():
            return []
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            return [dict(row) for row in csv.DictReader(fh) if (row.get("job_id") or "").strip()]


def _append_run(row: dict[str, Any]) -> None:
    RUNS.parent.mkdir(parents=True, exist_ok=True)
    with RUNS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _risk_allows_execute(risk: str) -> str:
    """Return decision: execute | waiting_approval | refuse."""
    r = (risk or "green").lower()
    if r in {"red", "orange"}:
        return "waiting_approval"
    return "execute"


def flatten_inbox() -> list[dict[str, Any]]:
    data = load_json(INBOX, {"buckets": {}})
    rows: list[dict[str, Any]] = []
    for bucket, items in (data.get("buckets") or {}).items():
        for item in items or []:
            rows.append({**item, "bucket": bucket, "_source": "office/control/inbox.json"})
    return rows


def open_dead_letters() -> list[dict[str, Any]]:
    data = load_json(DEAD, {"items": []})
    rows = []
    for item in data.get("items") or []:
        state = str(item.get("status") or item.get("state") or "open").lower()
        if state not in CLOSED_STATES:
            rows.append({**item, "_source": "office/control/dead-letter.json"})
    return rows


def blockers() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    followups = load_json(FOLLOWUPS, {"items": []}).get("items") or []
    for item in followups:
        state = str(item.get("state") or "").lower()
        if state in CLOSED_STATES:
            continue
        if state.startswith(WAITING_PREFIXES) or item.get("next_action"):
            rows.append(
                {
                    "id": item.get("id"),
                    "state": item.get("state"),
                    "waiting_for": item.get("waiting_for") or _waiting_from_state(state),
                    "blocked_item": item.get("blocked_item") or item.get("contentId") or item.get("jobId") or item.get("sku"),
                    "since": item.get("since") or item.get("created_at"),
                    "safe_until": item.get("safe_until"),
                    "next_action": item.get("next_action"),
                    "risk": item.get("risk") or "",
                    "source": "office/control/followups.json",
                }
            )
    for item in flatten_inbox():
        if item.get("bucket") == "blocked":
            rows.append(
                {
                    "id": item.get("id"),
                    "state": item.get("state") or "blocked",
                    "waiting_for": item.get("waiting_for"),
                    "blocked_item": item.get("blocked_item") or item.get("title"),
                    "since": item.get("since") or item.get("created_at") or item.get("updatedAt"),
                    "safe_until": item.get("safe_until"),
                    "next_action": item.get("next_action"),
                    "risk": item.get("risk") or "orange",
                    "source": "office/control/inbox.json",
                }
            )
    for item in open_dead_letters():
        rows.append(
            {
                "id": item.get("id"),
                "state": item.get("status") or item.get("state") or "dead_letter",
                "waiting_for": item.get("waiting_for") or "exception_resolution",
                "blocked_item": item.get("title") or item.get("kind") or item.get("id"),
                "since": item.get("created_at") or item.get("updatedAt"),
                "safe_until": item.get("safe_until"),
                "next_action": item.get("next_action") or "reconcile_before_retry",
                "risk": item.get("risk") or "orange",
                "source": "office/control/dead-letter.json",
            }
        )
    return _dedupe(rows)


def _waiting_from_state(state: str) -> str | None:
    if state.startswith("waiting_for_"):
        return state.removeprefix("waiting_for_")
    if state == "blocked":
        return "blocker_resolution"
    return None


def approval_bundle() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in flatten_inbox():
        risk = str(item.get("risk") or "").lower()
        if item.get("bucket") == "approvals" or risk in {"orange", "red"}:
            rows.append(
                {
                    "id": item.get("id"),
                    "title": item.get("title") or item.get("kind") or item.get("id"),
                    "risk": risk or "orange",
                    "action": item.get("next_action") or item.get("action"),
                    "source": "office/control/inbox.json",
                }
            )
    queue = load_json(APPROVAL_QUEUE, {"items": []})
    for item in queue.get("items") or []:
        gate = str(item.get("gate") or "")
        if gate and gate not in {"approved", "approved_for_manual_posting", "live_verified", "closed"}:
            rows.append(
                {
                    "id": item.get("content_id") or item.get("id"),
                    "title": f"Content approval · {item.get('format') or 'content'}",
                    "risk": "orange",
                    "action": gate,
                    "slot": item.get("slot"),
                    "source": "packages/vfgrowth/data/approval-queue.json",
                }
            )
    rows.sort(key=lambda r: (RISK_ORDER.get(str(r.get("risk") or ""), 4), str(r.get("id") or "")))
    return _dedupe(rows)


def _dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        key = (str(row.get("source") or row.get("_source") or ""), str(row.get("id") or row.get("blocked_item") or ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def next_action() -> dict[str, Any]:
    approvals = approval_bundle()
    if approvals:
        top = approvals[0]
        return {
            "kind": "approval",
            "id": top.get("id"),
            "action": top.get("action") or "review_approval",
            "reason": "highest-gated owner decision currently present in canonical approval sources",
            "risk": top.get("risk"),
            "source": top.get("source"),
        }

    waiting = blockers()
    actionable = [row for row in waiting if row.get("next_action") and row.get("next_action") not in {"wait", "none"}]
    if actionable:
        top = sorted(actionable, key=lambda r: (RISK_ORDER.get(str(r.get("risk") or ""), 4), str(r.get("since") or "")))[0]
        return {
            "kind": "blocker",
            "id": top.get("id"),
            "action": top.get("next_action"),
            "reason": "canonical waiting item already declares a next action",
            "risk": top.get("risk"),
            "source": top.get("source"),
        }

    inbox = [i for i in flatten_inbox() if str(i.get("state") or "").lower() not in CLOSED_STATES]
    if inbox:
        top = inbox[0]
        return {
            "kind": "inbox",
            "id": top.get("id"),
            "action": top.get("next_action") or "review_current_state",
            "reason": "open canonical inbox item; no stronger approval/blocker action exists",
            "risk": top.get("risk") or "green",
            "source": top.get("_source"),
        }

    return {"kind": "none", "action": "no_action", "reason": "no open canonical action found"}


def context_pack(identifier: str) -> dict[str, Any]:
    needle = identifier.strip().lower()
    if not needle:
        raise SystemExit("FAIL context requires a non-empty id")

    found: dict[str, list[dict[str, Any]]] = {
        "inbox": [],
        "followups": [],
        "dead_letter": [],
        "approvals": [],
        "jobs": [],
        "decisions": [],
    }

    def matches(row: dict[str, Any]) -> bool:
        hay = json.dumps(row, ensure_ascii=False).lower()
        return needle in hay

    for row in flatten_inbox():
        if matches(row):
            found["inbox"].append(row)
    for row in load_json(FOLLOWUPS, {"items": []}).get("items") or []:
        if matches(row):
            found["followups"].append(row)
    for row in load_json(DEAD, {"items": []}).get("items") or []:
        if matches(row):
            found["dead_letter"].append(row)
    for row in load_json(APPROVAL_QUEUE, {"items": []}).get("items") or []:
        if matches(row):
            found["approvals"].append(row)
    for row in load_jobs():
        if matches(row):
            found["jobs"].append(row)
    for row in load_jsonl(DECISIONS):
        if matches(row):
            found["decisions"].append(row)

    return {
        "id": identifier,
        "generatedAt": now_iso(),
        "rule": "source-linked retrieval only; absence is unknown, not permission to invent",
        "sources": found,
        "counts": {key: len(value) for key, value in found.items()},
    }


def quiet_plan() -> dict[str, Any]:
    cfg = load_json(CONFIG, {})
    bg = next((c for c in cfg.get("components") or [] if c.get("id") == "background-executor-policy"), {})
    candidates: list[dict[str, Any]] = []
    for row in blockers():
        action = str(row.get("next_action") or "")
        if action in {"reconcile_before_retry", "wait_matching_print_done", "media_intake_retry", "projection_refresh"}:
            candidates.append({"id": row.get("id"), "action": action, "source": row.get("source"), "risk": row.get("risk") or "yellow"})
    candidates.append({"id": "autonomy-snapshot", "action": "projection_refresh", "source": "AUTONOMY.json", "risk": "green"})
    candidates.append({"id": "media-intake-status", "action": "run_media_intake_status", "source": "vfmedia", "risk": "green"})
    return {
        "generatedAt": now_iso(),
        "mode": "quiet-hours-safe-plan",
        "allowed": bg.get("allowed") or [],
        "forbidden": bg.get("forbidden") or [],
        "candidates": candidates,
        "note": "green/yellow candidates may be executed via vf_autonomy.py execute; orange/red stay gated",
    }


def _reconcile_before_action(action: str, target_id: str | None) -> dict[str, Any]:
    """Reconcile actual state before retry — never blind retry."""
    evidence: dict[str, Any] = {"action": action, "target_id": target_id}
    if action in {"media_intake_retry", "run_media_intake_status"}:
        state = load_json(INTAKE_RUNNER, {})
        evidence["intake_runner"] = {
            "auth_ready": (state.get("auth") or {}).get("ready"),
            "lastSuccessAt": state.get("lastSuccessAt"),
            "activation_proven": (state.get("activation") or {}).get("proven"),
            "lastError": state.get("lastError"),
        }
    if action in {"reconcile_before_retry"} and target_id:
        # look up followup/dead-letter current state
        for item in load_json(FOLLOWUPS, {"items": []}).get("items") or []:
            if item.get("id") == target_id:
                evidence["followup"] = {"state": item.get("state"), "next_action": item.get("next_action")}
        for item in load_json(DEAD, {"items": []}).get("items") or []:
            if item.get("id") == target_id:
                evidence["dead_letter"] = {"status": item.get("status") or item.get("state")}
    if action in {"projection_refresh", "projection refresh", "refresh_projections"}:
        evidence["projections"] = {
            "autonomy": OUT.is_file(),
            "pulse": (ROOT / "packages/velvetos/living-studio/data/pulse-latest.json").is_file(),
        }
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import vf_jobs_adapter as jobs_adapter  # noqa: WPS433

        evidence["jobs"] = jobs_adapter.status()
    except Exception as exc:  # noqa: BLE001
        evidence["jobs_error"] = str(exc)
    return evidence


def _run_handler(action: str, *, target_id: str | None, dry_run: bool) -> dict[str, Any]:
    action_norm = action.strip().replace(" ", "_").lower()
    if action in {"projection refresh", "projection_refresh", "refresh_projections"} or action_norm == "projection_refresh":
        if dry_run:
            return {"ok": True, "dry_run": True, "handler": "snapshot+pulse+world-model"}
        snap = snapshot()
        pulse = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "vf_living_studio.py"), "pulse"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        world = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "vf_living_studio.py"), "world-model"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "ok": pulse.returncode == 0 and world.returncode == 0,
            "handler": "snapshot+pulse+world-model",
            "nextBestAction": snap.get("nextBestAction"),
            "pulse_exit": pulse.returncode,
            "world_exit": world.returncode,
        }

    if action in {"run_media_intake_status", "media_intake_retry"} or action_norm in {
        "run_media_intake_status",
        "media_intake_retry",
    }:
        if dry_run:
            return {"ok": True, "dry_run": True, "handler": "vfmedia.py intake status"}
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "vfmedia.py"), "intake", "status"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        body = {}
        try:
            body = json.loads(proc.stdout) if proc.stdout.strip() else {}
        except json.JSONDecodeError:
            body = {"raw": (proc.stdout or "")[:500]}
        # retry only when auth ready and lastError set — never invent success
        retried = False
        if action in {"media_intake_retry", "media_intake_retry"} and (body.get("auth") or {}).get("ready") and body.get("lastError"):
            # status-only safe path here; full google run stays on GHA OIDC runner
            retried = False
        return {
            "ok": proc.returncode == 0,
            "handler": "vfmedia.py intake status",
            "status": body,
            "retried_run": retried,
            "note": "full Drive intake remains on commissioned GHA OIDC runner when auth.ready",
        }

    if action in {"reconcile_before_retry"} or action_norm == "reconcile_before_retry":
        evidence = _reconcile_before_action(action, target_id)
        # safe followup transition: if waiting item already resolved externally, mark note
        if target_id and not dry_run:
            fu = load_json(FOLLOWUPS, {"items": []})
            changed = False
            for item in fu.get("items") or []:
                if item.get("id") == target_id and item.get("state") not in CLOSED_STATES:
                    item["lastReconcileAt"] = now_iso()
                    item["reconcileNote"] = "autonomy reconciled actual state before retry"
                    changed = True
            if changed:
                FOLLOWUPS.write_text(json.dumps(fu, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return {"ok": True, "handler": "reconcile_before_retry", "evidence": evidence, "dry_run": dry_run}

    if action in {"memory_context", "vfmem_who", "context pack"} or action_norm in {"memory_context", "vfmem_who"}:
        q = target_id or "inquiry"
        if dry_run:
            return {"ok": True, "dry_run": True, "handler": "vfmem.py who", "query": q}
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "vfmem.py"), "--json", "who", q],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        result = None
        if proc.stdout.strip():
            try:
                result = json.loads(proc.stdout)
            except json.JSONDecodeError:
                result = {"text": proc.stdout[:1000]}
        return {"ok": proc.returncode == 0, "handler": "vfmem.py who", "query": q, "result": result}

    if action in {"content_factory_prepare"} or action_norm == "content_factory_prepare":
        if dry_run:
            return {"ok": True, "dry_run": True, "handler": "vf_living_studio work-to-story + content-universe"}
        wts = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "vf_living_studio.py"), "work-to-story"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        cu = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "vf_living_studio.py"), "content-universe"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "ok": wts.returncode == 0 and cu.returncode == 0,
            "handler": "work-to-story + content-universe",
            "note": "prepare only — no publish",
        }

    if action in {"watchdog_repair", "health_repair"} or action_norm in {"watchdog_repair", "health_repair"}:
        if dry_run:
            return {"ok": True, "dry_run": True, "handler": "vf_control_plane.py watchdog"}
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "vf_control_plane.py"), "watchdog"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "handler": "vf_control_plane.py watchdog",
            "stdout": (proc.stdout or "")[:1000],
        }

    if action in {"followup_safe_transition"} or action_norm == "followup_safe_transition":
        return _run_handler("reconcile_before_retry", target_id=target_id, dry_run=dry_run)

    if action in {"review_current_state", "classify", "checkpoint", "readiness check", "jobs_pull_status"}:
        if dry_run:
            return {"ok": True, "dry_run": True, "handler": "jobs status + snapshot"}
        sys.path.insert(0, str(ROOT / "scripts"))
        import vf_jobs_adapter as jobs_adapter  # noqa: WPS433

        st = jobs_adapter.status()
        snap = snapshot()
        return {"ok": True, "handler": "jobs.status + snapshot", "jobs": st, "next": snap.get("nextBestAction")}

    if action in {"wait_matching_print_done", "wait", "none", "no_action"}:
        return {"ok": True, "handler": "noop_wait", "note": "waiting is managed state — no mutation"}

    return {"ok": False, "handler": None, "error": f"no safe handler for action {action!r}"}


def execute_action(
    action: str | None = None,
    *,
    target_id: str | None = None,
    risk: str | None = None,
    dry_run: bool = False,
    source: str = "vf_autonomy",
) -> dict[str, Any]:
    """Lifecycle: queued → running → checkpoint → completed | waiting_approval | failed."""
    nxt = next_action() if not action else {
        "kind": "manual",
        "id": target_id,
        "action": action,
        "risk": risk or "green",
        "source": source,
        "reason": "explicit execute",
    }
    act = action or str(nxt.get("action") or "")
    tid = target_id or (str(nxt.get("id")) if nxt.get("id") else None)
    risk_val = (risk or nxt.get("risk") or "green")
    run_id = f"arun-{uuid.uuid4().hex[:12]}"
    correlation_id = f"corr-{hashlib.sha256(f'{act}|{tid}'.encode()).hexdigest()[:12]}"
    idempotency_key = f"exec|{act}|{tid}|{rows_fingerprint(act, tid)}"
    # idempotent: skip if same key completed recently
    if RUNS.is_file():
        for line in RUNS.read_text(encoding="utf-8").splitlines()[-200:]:
            try:
                prev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if prev.get("idempotency_key") == idempotency_key and prev.get("state") == "completed":
                return {**prev, "status": "idempotent_skip"}

    decision = _risk_allows_execute(str(risk_val))
    row: dict[str, Any] = {
        "run_id": run_id,
        "correlation_id": correlation_id,
        "idempotency_key": idempotency_key,
        "source": source,
        "decision": decision,
        "action": act,
        "target_id": tid,
        "risk": risk_val,
        "state": "queued",
        "at": now_iso(),
        "next_action_snapshot": nxt,
    }
    _append_run(row)

    if decision == "waiting_approval":
        row["state"] = "waiting_approval"
        row["evidence"] = {"policy": "office/control/POLICY.md", "gate": risk_val}
        row["resulting_state"] = "waiting_approval"
        _append_run(row)
        return row

    row["state"] = "running"
    _append_run({"run_id": run_id, "state": "running", "at": now_iso()})

    reconcile = _reconcile_before_action(act, tid)
    row["checkpoint"] = {"reconcile": reconcile, "at": now_iso()}
    _append_run({"run_id": run_id, "state": "checkpoint", "checkpoint": row["checkpoint"]})

    try:
        result = _run_handler(act, target_id=tid, dry_run=dry_run)
        row["evidence"] = result
        if result.get("ok"):
            row["state"] = "completed"
            row["resulting_state"] = "completed"
        else:
            row["state"] = "failed"
            row["resulting_state"] = "failed"
            row["error"] = result.get("error") or result.get("stderr")
    except Exception as exc:  # noqa: BLE001
        row["state"] = "failed"
        row["resulting_state"] = "failed"
        row["error"] = str(exc)
        row["evidence"] = {"exception": str(exc)}
    row["finishedAt"] = now_iso()
    _append_run(row)
    return row


def rows_fingerprint(action: str, target_id: str | None) -> str:
    return hashlib.sha256(f"{action}|{target_id}|{datetime.now(TZ).date().isoformat()}".encode()).hexdigest()[:10]


def snapshot() -> dict[str, Any]:
    cfg = load_json(CONFIG, {})
    data = {
        "name": "velvetos-autonomy-snapshot",
        "generatedAt": now_iso(),
        "contract": cfg.get("executionContract") or {},
        "componentStatus": {c.get("id"): c.get("status") for c in cfg.get("components") or []},
        "nextBestAction": next_action(),
        "blockers": blockers(),
        "approvalBundle": approval_bundle(),
        "quietPlan": quiet_plan(),
        "executor": "vf_autonomy.py execute — composition over existing handlers",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def selftest() -> tuple[bool, list[str]]:
    errors: list[str] = []
    cfg = load_json(CONFIG, {})
    if not cfg:
        errors.append("missing AUTONOMY.json")
    if not CONTROL_PLANE.is_file():
        errors.append("missing office/control-plane.json")
    if not POLICY.is_file():
        errors.append("missing office/control/POLICY.md")
    ids = [c.get("id") for c in cfg.get("components") or []]
    expected = {
        "foundation-runtime-contract",
        "router-context-engine",
        "blocker-waiting-engine",
        "project-lifecycle-engine",
        "approval-system",
        "reliability-exception-engine",
        "work-prioritization",
        "background-executor-policy",
    }
    missing = sorted(expected - set(ids))
    if missing:
        errors.append("missing components: " + ", ".join(missing))
    contract = cfg.get("executionContract") or {}
    for required in ("run_id", "idempotency_key", "correlation_id"):
        if required not in (contract.get("requiredIds") or []):
            errors.append(f"execution contract missing {required}")
    states = set(contract.get("states") or [])
    if not {"queued", "running", "waiting_approval", "completed", "failed"}.issubset(states):
        errors.append("execution contract states incomplete")
    # behavioral: green execute dry-run
    ex = execute_action("projection_refresh", risk="green", dry_run=True, source="selftest")
    if ex.get("state") not in {"completed", "idempotent_skip"} and ex.get("status") != "idempotent_skip":
        if ex.get("state") != "completed":
            errors.append(f"execute dry-run failed: {ex.get('state')} {ex.get('error')}")
    # orange gated
    gated = execute_action("content_factory_prepare", risk="orange", dry_run=True, source="selftest")
    if gated.get("state") != "waiting_approval" and gated.get("decision") != "waiting_approval":
        errors.append("orange action must wait for approval")
    return not errors, errors


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="VelvetOS autonomy composition")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("next-action")
    sub.add_parser("blockers")
    sub.add_parser("approvals")
    ctx = sub.add_parser("context")
    ctx.add_argument("identifier")
    sub.add_parser("quiet-plan")
    sub.add_parser("snapshot")
    ex = sub.add_parser("execute", help="run next safe action or an explicit green/yellow action")
    ex.add_argument("--action", default="")
    ex.add_argument("--id", default="")
    ex.add_argument("--risk", default="")
    ex.add_argument("--dry-run", action="store_true")
    sub.add_parser("selftest")
    args = parser.parse_args()

    if args.cmd == "status":
        cfg = load_json(CONFIG, {})
        print_json(
            {
                "name": cfg.get("name"),
                "updatedAt": cfg.get("updatedAt"),
                "components": [{"id": c.get("id"), "status": c.get("status")} for c in cfg.get("components") or []],
                "nextBestAction": next_action(),
                "blockerCount": len(blockers()),
                "approvalCount": len(approval_bundle()),
                "executor": "execute",
            }
        )
        return 0
    if args.cmd == "next-action":
        print_json(next_action())
        return 0
    if args.cmd == "blockers":
        print_json(blockers())
        return 0
    if args.cmd == "approvals":
        print_json(approval_bundle())
        return 0
    if args.cmd == "context":
        print_json(context_pack(args.identifier))
        return 0
    if args.cmd == "quiet-plan":
        print_json(quiet_plan())
        return 0
    if args.cmd == "snapshot":
        print_json(snapshot())
        return 0
    if args.cmd == "execute":
        print_json(
            execute_action(
                args.action or None,
                target_id=args.id or None,
                risk=args.risk or None,
                dry_run=bool(args.dry_run),
            )
        )
        return 0
    if args.cmd == "selftest":
        ok, errors = selftest()
        if not ok:
            print_json({"ok": False, "errors": errors})
            return 1
        print_json({"ok": True, "nextBestAction": next_action(), "execute": "wired"})
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
