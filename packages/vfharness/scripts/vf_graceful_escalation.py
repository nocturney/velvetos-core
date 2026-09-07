#!/usr/bin/env python3
"""
vf_graceful_escalation.py — Graduated escalation ladder for the vfharness
agent loop (packages/vfharness/LOOP.md).

Today the loop is binary: 2 attempts then escalate to the human. This adds
a 4-rung ladder: retry as-is -> retry with fallback strategy -> downgrade
scope (safe partial artifact) -> escalate to human (existing
templates/escalation.md format). Every rung is logged to
packages/vfharness/state/ — nothing hidden, nothing invented.

Usage (library):
    from vf_graceful_escalation import run_ladder
    run_ladder(task_id, pack, attempt_fn, fallback_fn, downgrade_fn)

Self-test:
    python3 vf_graceful_escalation.py --self-test
"""
import argparse, json, time
from datetime import datetime, timezone
from pathlib import Path

STATE_DIR = Path(__file__).resolve().parents[1] / "state"

class Rung:
    RETRY = "retry_as_is"
    FALLBACK = "retry_with_fallback"
    DOWNGRADE = "downgrade_scope"
    ESCALATE = "escalate_to_human"

def _log(task_id, entry):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / f"ladder-{task_id}.json"
    history = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    entry["ts"] = datetime.now(timezone.utc).isoformat()
    history.append(entry)
    path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    return path

def write_escalation(task_id, pack, decision_needed, recommended, already_tried, artifact=""):
    text = (f"# הסלמה — {task_id}\n\nלא כישלון. אדם מחליט. HQ לא שולח בינתיים.\n\n```\n"
            f"task_id: {task_id}\npack: {pack}\ndecision_needed: {decision_needed}\n"
            f"recommended: {recommended}\nalready_tried: {already_tried}\n"
            "sensor_or_guide: vf_graceful_escalation ladder exhausted\n"
            f"artifact: {artifact}\nsafest_default: לא לשלוח / לא להמציא ₪ / לחכות לאדם\n```\n")
    out = STATE_DIR / f"escalation-{task_id}.md"
    out.write_text(text, encoding="utf-8")
    return out

def run_ladder(task_id, pack, attempt_fn, fallback_fn=None, downgrade_fn=None,
               max_retries=2, retry_delay=0.0):
    tried = []
    for i in range(max_retries):
        ok, result = attempt_fn()
        tried.append(f"{Rung.RETRY}#{i+1}")
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
            return {"rung": Rung.DOWNGRADE, "result": result, "tried": tried,
                     "note": "partial/safe artifact — not full scope"}
    esc_path = write_escalation(task_id, pack, "Ladder exhausted — human decision required",
                                 "Review already_tried and artifact, then decide", tried)
    _log(task_id, {"rung": Rung.ESCALATE, "escalation_file": str(esc_path)})
    return {"rung": Rung.ESCALATE, "result": None, "tried": tried, "escalation_file": str(esc_path)}

def _self_test():
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
    out = run_ladder("selftest-001", pack="vfcopy", attempt_fn=attempt,
                      fallback_fn=fallback, downgrade_fn=downgrade)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    assert out["rung"] == Rung.DOWNGRADE
    print(f"\nOK — resolved at rung '{Rung.DOWNGRADE}' without escalating to human. calls={state['calls']}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        _self_test()
    else:
        print(__doc__)
