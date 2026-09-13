#!/usr/bin/env python3
"""
vf_graceful_escalation.py — Graduated escalation ladder for the vfharness
agent loop (packages/vfharness/LOOP.md).

Ladder:
    retry as-is -> retry with fallback strategy -> downgrade scope
    -> optional safe ruling -> escalate to human

`safe_ruling` is fail-closed. It only runs when the caller supplies both a
ruling_fn and safe_to_rule=True after policy classification. A ruling cannot
replace a required sensor/receipt or a human/constitutional gate. Every rung
is logged to packages/vfharness/state/ — nothing hidden, nothing invented.

Usage (library):
    from vf_graceful_escalation import run_ladder
    run_ladder(task_id, pack, attempt_fn, fallback_fn, downgrade_fn)

    run_ladder(
        task_id,
        pack,
        attempt_fn,
        fallback_fn,
        downgrade_fn,
        ruling_fn=ruling_fn,
        safe_to_rule=True,
    )

Self-test:
    python3 vf_graceful_escalation.py --self-test
"""
import argparse
import json
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

STATE_DIR = Path(__file__).resolve().parents[1] / "state"


class Rung:
    RETRY = "retry_as_is"
    FALLBACK = "retry_with_fallback"
    DOWNGRADE = "downgrade_scope"
    SAFE_RULING = "safe_ruling"
    ESCALATE = "escalate_to_human"


def _log(task_id, entry):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / f"ladder-{task_id}.json"
    history = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    entry["ts"] = datetime.now(timezone.utc).isoformat()
    history.append(entry)
    path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _normalize_ruling(ruling):
    if not isinstance(ruling, dict):
        raise ValueError("ruling must be a dict")
    required = ("decision", "why", "cost_if_wrong")
    normalized = {}
    for field in required:
        value = ruling.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"ruling missing non-empty {field}")
        normalized[field] = value.strip()
    return normalized


def format_ruling(ruling):
    normalized = _normalize_ruling(ruling)
    return (
        f"Ruling: {normalized['decision']} — {normalized['why']} — "
        f"{normalized['cost_if_wrong']}"
    )


def write_escalation(task_id, pack, decision_needed, recommended, already_tried, artifact=""):
    text = (
        f"# הסלמה — {task_id}\n\nלא כישלון. אדם מחליט. HQ לא שולח בינתיים.\n\n```\n"
        f"task_id: {task_id}\npack: {pack}\ndecision_needed: {decision_needed}\n"
        f"recommended: {recommended}\nalready_tried: {already_tried}\n"
        "sensor_or_guide: vf_graceful_escalation ladder exhausted\n"
        f"artifact: {artifact}\nsafest_default: לא לשלוח / לא להמציא ₪ / לחכות לאדם\n```\n"
    )
    out = STATE_DIR / f"escalation-{task_id}.md"
    out.write_text(text, encoding="utf-8")
    return out


def run_ladder(
    task_id,
    pack,
    attempt_fn,
    fallback_fn=None,
    downgrade_fn=None,
    max_retries=2,
    retry_delay=0.0,
    *,
    ruling_fn=None,
    safe_to_rule=False,
):
    """Run the existing ladder, optionally resolving a safe local ambiguity.

    The keyword-only ruling arguments preserve the positional API used by
    existing callers. `safe_to_rule` must be granted only after the caller has
    classified the decision as local/reversible and outside all authority
    gates. Invalid or blocked rulings fail closed into normal escalation.
    """
    tried = []
    for i in range(max_retries):
        ok, result = attempt_fn()
        tried.append(f"{Rung.RETRY}#{i + 1}")
        _log(task_id, {"rung": Rung.RETRY, "attempt": i + 1, "ok": ok})
        if ok:
            return {"rung": Rung.RETRY, "result": result, "tried": tried}
        if retry_delay:
            time.sleep(retry_delay)

    if fallback_fn is not None:
        ok, result = fallback_fn()
        tried.append(Rung.FALLBACK)
        _log(task_id, {"rung": Rung.FALLBACK, "ok": ok})
        if ok:
            return {"rung": Rung.FALLBACK, "result": result, "tried": tried}

    if downgrade_fn is not None:
        ok, result = downgrade_fn()
        tried.append(Rung.DOWNGRADE)
        _log(task_id, {"rung": Rung.DOWNGRADE, "ok": ok})
        if ok:
            return {
                "rung": Rung.DOWNGRADE,
                "result": result,
                "tried": tried,
                "note": "partial/safe artifact — not full scope",
            }

    if ruling_fn is not None:
        tried.append(Rung.SAFE_RULING)
        if not safe_to_rule:
            _log(
                task_id,
                {
                    "rung": Rung.SAFE_RULING,
                    "ok": False,
                    "skipped": True,
                    "reason": "safe_to_rule guard not granted",
                },
            )
        else:
            try:
                response = ruling_fn()
                if not isinstance(response, tuple) or len(response) != 3:
                    raise ValueError("ruling_fn must return (ok, result, ruling)")
                ok, result, ruling = response
                normalized = _normalize_ruling(ruling)
            except Exception as exc:  # fail closed; do not leak exception payloads
                _log(
                    task_id,
                    {
                        "rung": Rung.SAFE_RULING,
                        "ok": False,
                        "reason": "invalid_or_failed_ruling",
                        "error_type": type(exc).__name__,
                    },
                )
            else:
                _log(
                    task_id,
                    {
                        "rung": Rung.SAFE_RULING,
                        "ok": bool(ok),
                        "ruling": normalized,
                    },
                )
                if ok:
                    return {
                        "rung": Rung.SAFE_RULING,
                        "result": result,
                        "tried": tried,
                        "ruling": normalized,
                        "ruling_text": format_ruling(normalized),
                    }

    esc_path = write_escalation(
        task_id,
        pack,
        "Ladder exhausted — human decision required",
        "Review already_tried and artifact, then decide",
        tried,
    )
    _log(task_id, {"rung": Rung.ESCALATE, "escalation_file": str(esc_path)})
    return {
        "rung": Rung.ESCALATE,
        "result": None,
        "tried": tried,
        "escalation_file": str(esc_path),
    }


def _self_test():
    global STATE_DIR
    original_state_dir = STATE_DIR
    with tempfile.TemporaryDirectory(prefix="vf-ladder-selftest-") as tmp:
        STATE_DIR = Path(tmp)
        try:
            state = {"calls": 0}

            def attempt():
                state["calls"] += 1
                return False, None

            def fallback():
                state["calls"] += 1
                return False, None

            def downgrade():
                state["calls"] += 1
                return True, "partial-caption-draft-only"

            out = run_ladder(
                "selftest-001",
                pack="vfcopy",
                attempt_fn=attempt,
                fallback_fn=fallback,
                downgrade_fn=downgrade,
            )
            assert out["rung"] == Rung.DOWNGRADE

            ruling_state = {"calls": 0}

            def fail_attempt():
                ruling_state["calls"] += 1
                return False, None

            def fail_fallback():
                ruling_state["calls"] += 1
                return False, None

            def fail_downgrade():
                ruling_state["calls"] += 1
                return False, None

            def ruling():
                ruling_state["calls"] += 1
                return (
                    True,
                    "continued-with-local-default",
                    {
                        "decision": "use the existing local default",
                        "why": "the ambiguity is reversible and has no external side effect",
                        "cost_if_wrong": "redo this local step",
                    },
                )

            ruled = run_ladder(
                "selftest-ruling-001",
                pack="vfharness",
                attempt_fn=fail_attempt,
                fallback_fn=fail_fallback,
                downgrade_fn=fail_downgrade,
                max_retries=1,
                ruling_fn=ruling,
                safe_to_rule=True,
            )
            assert ruled["rung"] == Rung.SAFE_RULING
            assert ruled["ruling_text"].startswith("Ruling: ")

            blocked_called = {"value": False}

            def blocked_ruling():
                blocked_called["value"] = True
                return True, "must-not-run", {
                    "decision": "unsafe",
                    "why": "unsafe",
                    "cost_if_wrong": "unsafe",
                }

            blocked = run_ladder(
                "selftest-ruling-guard-001",
                pack="vfharness",
                attempt_fn=fail_attempt,
                fallback_fn=fail_fallback,
                downgrade_fn=fail_downgrade,
                max_retries=1,
                ruling_fn=blocked_ruling,
                safe_to_rule=False,
            )
            assert blocked["rung"] == Rung.ESCALATE
            assert blocked_called["value"] is False

            print(json.dumps(ruled, ensure_ascii=False, indent=2))
            print(
                f"\nOK — downgrade preserved; safe ruling opt-in works; guard fails closed. "
                f"calls={state['calls'] + ruling_state['calls']}"
            )
        finally:
            STATE_DIR = original_state_dir


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        _self_test()
    else:
        print(__doc__)
