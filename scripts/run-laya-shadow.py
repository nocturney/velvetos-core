#!/usr/bin/env python3
"""Run a local, non-authoritative Laya shadow evaluation."""
from __future__ import annotations

import argparse
import json
import math
import os
import platform
import re
import time
from collections import Counter, defaultdict
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "packages" / "vfharness" / "evals" / "laya-shadow-dataset.jsonl"
DEFAULT_OUTPUT = ROOT / "packages" / "vfharness" / "state" / "laya-shadow-2026-09-27.json"

LABELS = {
    "domain": ["office", "velvet-factory", "development", "media", "system", "unknown"],
    "action": ["read", "analyse", "generate", "write", "execute", "publish"],
    "escalation": ["no-model", "local/small", "reasoning/frontier capability"],
}

QUESTIONS = {
    "domain": {
        "type": "choice",
        "instructions": "Route this request to exactly one VelvetOS domain. בחר דומיין אחד בלבד.",
        "criteria": {
            "office": "calendar, mail, orders, CRM/admin and business operations; יומן, מייל, הזמנות ואדמיניסטרציה",
            "velvet-factory": "physical products, CAD, 3D printing, printers/slicers and Velvet Factory product/social workflows; מוצרי הסטודיו והדפסה תלת-ממדית",
            "development": "source code, Git, tests, CI, developer docs and software engineering; קוד, בדיקות ופיתוח",
            "media": "images, video, assets, metadata, transcoding, media storage and integrity; תמונות, וידאו ונכסי מדיה",
            "system": "host, OS, services, backups, infrastructure, security/runtime; מערכת, שירותים, גיבוי ותשתית",
            "unknown": "outside known VelvetOS domains or too underspecified to route safely; לא שייך או חסר מידע מספיק",
        },
    },
    "action": {
        "type": "choice",
        "instructions": "Classify the requested end action, not its authorization. סווג את פעולת הקצה המבוקשת.",
        "criteria": {
            "read": "retrieve or inspect without mutation or interpretation-heavy analysis; קריאה או בדיקה בלבד",
            "analyse": "compare, diagnose, evaluate or explain existing information; ניתוח, השוואה או אבחון",
            "generate": "create a new draft/content/code/model/plan without persisting or executing it as the end action; יצירת תוצר חדש",
            "write": "persist or edit a file, record, config or status without running a job or public publication; כתיבה או עדכון מתמשך",
            "execute": "run a command, job, tool or operational control action; הרצת פקודה, כלי או פעולה תפעולית",
            "publish": "release or schedule content to a public/external publication channel; פרסום תוכן בערוץ ציבורי",
        },
    },
    "escalation": {
        "type": "choice",
        "instructions": (
            "Recommend cognitive capability only, never permission. "
            "Authorization is handled elsewhere by VelvetOS. "
            "בחר רמת יכולת חשיבה בלבד ולא הרשאה."
        ),
        "criteria": {
            "no-model": "deterministic lookup, exact state mutation, known command, sensor or rules path; אין צורך במודל יוצר",
            "local/small": "bounded summary, classification, drafting or simple transformation; משימה תחומה למודל מקומי קטן",
            "reasoning/frontier capability": "multi-source diagnosis, architecture, ambiguity, complex tradeoffs or novel reasoning; נדרש ניתוח מורכב ורב-שלבי",
        },
    },
}

HEBREW_RE = re.compile(r"[\u0590-\u05FF]")


def load_rows(path: Path) -> list[dict]:
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        missing = {"id", "lang", "text", "domain", "action", "escalation"} - set(row)
        if missing:
            raise ValueError(f"line {line_no}: missing {sorted(missing)}")
        for task, labels in LABELS.items():
            if row[task] not in labels:
                raise ValueError(f"line {line_no}: invalid {task}={row[task]!r}")
        rows.append(row)
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("dataset ids are not unique")
    return rows


def ece_10(items: list[tuple[float, bool]]) -> float:
    if not items:
        return 0.0
    bins: list[list[tuple[float, bool]]] = [[] for _ in range(10)]
    for conf, ok in items:
        bins[min(9, int(max(0.0, min(1.0, conf)) * 10))].append((conf, ok))
    total = len(items)
    return sum(
        (len(bucket) / total)
        * abs(sum(c for c, _ in bucket) / len(bucket) - sum(1.0 for _, ok in bucket if ok) / len(bucket))
        for bucket in bins
        if bucket
    )
def summarize_task(rows: list[dict], predictions: list[dict], task: str) -> dict:
    labels = LABELS[task]
    correct = 0
    brier_total = 0.0
    nll_total = 0.0
    calibration: list[tuple[float, bool]] = []
    confusion: dict[str, Counter] = defaultdict(Counter)
    per_label: dict[str, Counter] = defaultdict(Counter)
    high_confidence_wrong = []

    for row, result in zip(rows, predictions):
        ans = result["answers"][task]
        pred = ans["choice"]
        expected = row[task]
        probs = {label: float(ans.get("probabilities", {}).get(label, 0.0)) for label in labels}
        conf = float(ans.get("answer_confidence", max(probs.values(), default=0.0)))
        ok = pred == expected
        correct += int(ok)
        calibration.append((conf, ok))
        confusion[expected][pred] += 1
        per_label[expected]["total"] += 1
        per_label[expected]["correct"] += int(ok)
        brier_total += sum((probs[label] - (1.0 if label == expected else 0.0)) ** 2 for label in labels)
        nll_total += -math.log(max(probs.get(expected, 0.0), 1e-12))
        if not ok and conf >= 0.80:
            high_confidence_wrong.append({
                "id": row["id"],
                "lang": row["lang"],
                "expected": expected,
                "predicted": pred,
                "answer_confidence": round(conf, 4),
                "true_probability": round(probs.get(expected, 0.0), 4),
            })

    n = len(rows)
    return {
        "n": n,
        "correct": correct,
        "accuracy": round(correct / n, 4) if n else 0.0,
        "multiclass_brier_sum": round(brier_total / n, 6) if n else 0.0,
        "negative_log_likelihood": round(nll_total / n, 6) if n else 0.0,
        "ece_10_equal_width_bins": round(ece_10(calibration), 6),
        "confusion": {k: dict(v) for k, v in sorted(confusion.items())},
        "per_label": {
            label: {
                "total": per_label[label]["total"],
                "correct": per_label[label]["correct"],
                "accuracy": round(per_label[label]["correct"] / per_label[label]["total"], 4)
                if per_label[label]["total"] else None,
            }
            for label in labels
        },
        "high_confidence_wrong": high_confidence_wrong,
    }


def language_summary(rows: list[dict], predictions: list[dict]) -> dict:
    out = {}
    for lang in sorted({row["lang"] for row in rows}):
        idxs = [i for i, row in enumerate(rows) if row["lang"] == lang]
        subset = [rows[i] for i in idxs]
        preds = [predictions[i] for i in idxs]
        out[lang] = {
            "n": len(subset),
            **{
                task: round(
                    sum(pred["answers"][task]["choice"] == row[task] for row, pred in zip(subset, preds))
                    / len(subset),
                    4,
                )
                for task in LABELS
            },
        }
    return out
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--model", default="convaiinnovations/laya-multilingual")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()

    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    if args.offline:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"

    rows = load_rows(args.dataset)
    if args.limit:
        rows = rows[: args.limit]
    if not rows:
        raise SystemExit("dataset is empty")

    import laya
    import torch
    import transformers

    load_started = time.perf_counter()
    agent = laya.load(args.model, device=args.device)
    load_ms = (time.perf_counter() - load_started) * 1000.0

    predictions: list[dict | None] = [None] * len(rows)
    infer_started = time.perf_counter()
    for lang in sorted({row["lang"] for row in rows}):
        idxs = [i for i, row in enumerate(rows) if row["lang"] == lang]
        states = [rows[i]["text"] for i in idxs]
        lang_results = agent.predict_batch(
            states,
            QUESTIONS,
            batch_size=args.batch_size,
            lang=lang,
        )
        for idx, result in zip(idxs, lang_results):
            predictions[idx] = result
    inference_ms = (time.perf_counter() - infer_started) * 1000.0
    if any(item is None for item in predictions):
        raise RuntimeError("missing prediction")
    predictions = list(predictions)

    metrics = {task: summarize_task(rows, predictions, task) for task in LABELS}
    joint = sum(
        all(pred["answers"][task]["choice"] == row[task] for task in LABELS)
        for row, pred in zip(rows, predictions)
    )

    cases = []
    for row, pred in zip(rows, predictions):
        cases.append({
            "id": row["id"],
            "lang": row["lang"],
            "expected": {task: row[task] for task in LABELS},
            "predicted": {task: pred["answers"][task]["choice"] for task in LABELS},
            "answer_confidence": {
                task: pred["answers"][task].get("answer_confidence")
                for task in LABELS
            },
            "probabilities": {
                task: pred["answers"][task].get("probabilities", {})
                for task in LABELS
            },
        })
    lang_counts = Counter(row["lang"] for row in rows)
    hebrew_texts = sum(bool(HEBREW_RE.search(row["text"])) for row in rows)
    model_path = Path(args.model)
    snapshot_sha = (
        model_path.name
        if model_path.is_dir() and re.fullmatch(r"[0-9a-f]{40}", model_path.name)
        else None
    )
    receipt = {
        "schema": 1,
        "phase": 6,
        "state": "SHADOW",
        "authority": {
            "execution_authority": False,
            "authorization_authority": False,
            "production_routing_authority": False,
            "role": "LOCAL_DECISION_HELPER_EVALUATION_ONLY",
        },
        "model": {
            "requested": args.model,
            "snapshot_sha": snapshot_sha,
            "device": args.device,
            "laya_version": version("laya"),
            "torch_version": torch.__version__,
            "transformers_version": transformers.__version__,
            "offline": args.offline,
        },
        "dataset": {
            "path": str(args.dataset.relative_to(ROOT)) if args.dataset.is_relative_to(ROOT) else str(args.dataset),
            "n": len(rows),
            "language_counts": dict(lang_counts),
            "hebrew_script_rows": hebrew_texts,
            "hebrew_script_share": round(hebrew_texts / len(rows), 4),
            "label_counts": {
                task: dict(Counter(row[task] for row in rows))
                for task in LABELS
            },
        },
        "performance": {
            "model_load_ms": round(load_ms, 2),
            "inference_ms": round(inference_ms, 2),
            "inference_ms_per_case": round(inference_ms / len(rows), 2),
            "batch_size": args.batch_size,
            "platform": platform.platform(),
        },
        "metrics": metrics,
        "joint": {
            "correct_all_three": joint,
            "accuracy_all_three": round(joint / len(rows), 4),
        },
        "by_language_accuracy": language_summary(rows, predictions),
        "cases": cases,
        "promotion_criterion": None,
        "promotion_decision": "UNASSESSED_MEASURE_FIRST",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS_MEASUREMENT_COMPLETED",
        "state": "SHADOW",
        "n": len(rows),
        "metrics": {task: receipt["metrics"][task]["accuracy"] for task in LABELS},
        "joint_accuracy": receipt["joint"]["accuracy_all_three"],
        "hebrew_share": receipt["dataset"]["hebrew_script_share"],
        "inference_ms_per_case": receipt["performance"]["inference_ms_per_case"],
        "output": str(args.output),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
