#!/usr/bin/env python3
"""Post-hoc temperature calibration for the Laya Hebrew shadow benchmark."""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "packages" / "vfharness" / "state" / "laya-shadow-2026-09-27.json"
OUTPUT = ROOT / "packages" / "vfharness" / "state" / "laya-shadow-calibration-2026-09-27.json"
TASKS = ("domain", "action", "escalation")


def normalize_with_temperature(probs: dict[str, float], temperature: float) -> dict[str, float]:
    inv_t = 1.0 / temperature
    values = {k: max(float(v), 1e-12) ** inv_t for k, v in probs.items()}
    total = sum(values.values())
    return {k: v / total for k, v in values.items()}


def nll(cases: list[dict], task: str, temperature: float) -> float:
    total = 0.0
    for case in cases:
        p = normalize_with_temperature(case["probabilities"][task], temperature)
        total += -math.log(max(p.get(case["expected"][task], 0.0), 1e-12))
    return total / len(cases)


def ece(items: list[tuple[float, bool]]) -> float:
    bins = [[] for _ in range(10)]
    for conf, ok in items:
        bins[min(9, int(max(0.0, min(1.0, conf)) * 10))].append((conf, ok))
    total = len(items)
    return sum(
        len(bucket) / total
        * abs(
            sum(conf for conf, _ in bucket) / len(bucket)
            - sum(1.0 for _, ok in bucket if ok) / len(bucket)
        )
        for bucket in bins
        if bucket
    )
def score(cases: list[dict], task: str, temperature: float) -> dict:
    correct = 0
    brier = 0.0
    nll_total = 0.0
    calibration = []
    high_wrong = []
    for case in cases:
        expected = case["expected"][task]
        p = normalize_with_temperature(case["probabilities"][task], temperature)
        predicted = max(p, key=p.get)
        conf = p[predicted]
        ok = predicted == expected
        correct += int(ok)
        calibration.append((conf, ok))
        brier += sum((value - (1.0 if label == expected else 0.0)) ** 2 for label, value in p.items())
        nll_total += -math.log(max(p.get(expected, 0.0), 1e-12))
        if not ok and conf >= 0.80:
            high_wrong.append({
                "id": case["id"],
                "expected": expected,
                "predicted": predicted,
                "confidence": round(conf, 4),
            })
    n = len(cases)
    return {
        "n": n,
        "accuracy": round(correct / n, 4),
        "multiclass_brier_sum": round(brier / n, 6),
        "negative_log_likelihood": round(nll_total / n, 6),
        "ece_10_equal_width_bins": round(ece(calibration), 6),
        "high_confidence_wrong": high_wrong,
    }


def fit_temperature(cases: list[dict], task: str) -> tuple[float, float]:
    lo = math.log(0.25)
    hi = math.log(8.0)
    candidates = [math.exp(lo + (hi - lo) * i / 240.0) for i in range(241)]
    scored = [(nll(cases, task, t), t) for t in candidates]
    best_nll, best_t = min(scored)
    return best_t, best_nll
def main() -> None:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    if receipt.get("state") != "SHADOW":
        raise SystemExit("Laya receipt is not SHADOW")
    cases = receipt["cases"]
    hebrew = [case for case in cases if case["lang"] == "he"]
    calibration = [case for case in hebrew if int(case["id"][1:]) % 3 != 0]
    holdout = [case for case in hebrew if int(case["id"][1:]) % 3 == 0]
    if not calibration or not holdout:
        raise SystemExit("invalid calibration split")

    tasks = {}
    for task in TASKS:
        temperature, fit_nll = fit_temperature(calibration, task)
        tasks[task] = {
            "temperature": round(temperature, 6),
            "fit_nll": round(fit_nll, 6),
            "holdout_before": score(holdout, task, 1.0),
            "holdout_after": score(holdout, task, temperature),
        }

    output = {
        "schema": 1,
        "phase": 6,
        "state": "SHADOW_CALIBRATION_EVIDENCE",
        "source_receipt": str(RECEIPT.relative_to(ROOT)),
        "method": (
            "Additional scalar temperature over published class probabilities; "
            "fit by NLL on Hebrew calibration split, evaluated on disjoint Hebrew holdout. "
            "Argmax labels and accuracy are unchanged by construction."
        ),
        "split": {
            "rule": "Hebrew cases only; numeric id modulo 3 == 0 is holdout, all other Hebrew cases are calibration",
            "hebrew_total": len(hebrew),
            "calibration_n": len(calibration),
            "holdout_n": len(holdout),
            "calibration_ids": [case["id"] for case in calibration],
            "holdout_ids": [case["id"] for case in holdout],
        },
        "tasks": tasks,
        "deployment_effect": "NONE; evidence only, no runtime calibration installed",
        "authorization_effect": "NONE; VelvetOS remains the only authorization authority",
    }
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "calibration_n": len(calibration),
        "holdout_n": len(holdout),
        "tasks": {
            task: {
                "temperature": tasks[task]["temperature"],
                "ece_before": tasks[task]["holdout_before"]["ece_10_equal_width_bins"],
                "ece_after": tasks[task]["holdout_after"]["ece_10_equal_width_bins"],
                "nll_before": tasks[task]["holdout_before"]["negative_log_likelihood"],
                "nll_after": tasks[task]["holdout_after"]["negative_log_likelihood"],
                "accuracy": tasks[task]["holdout_after"]["accuracy"],
            }
            for task in TASKS
        },
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
