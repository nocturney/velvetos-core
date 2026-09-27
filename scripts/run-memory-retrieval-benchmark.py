#!/usr/bin/env python3
"""Deterministic vfmem retrieval benchmark: TF-IDF vs local Cognee derived index."""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "packages" / "vfmem" / "benchmarks" / "retrieval-v1.json"
TFIDF_SCRIPT = ROOT / "packages" / "vfmem" / "scripts" / "vf_semantic_search.py"
VFMEM = ROOT / "scripts" / "vfmem.py"
DEFAULT_OUT = ROOT / "packages" / "vfharness" / "state" / "memory-retrieval-phase7-2026-09-27.json"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("vf_semantic_search_benchmark", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rank(paths: list[str], expected: set[str]) -> int | None:
    for index, path in enumerate(paths, 1):
        if path in expected:
            return index
    return None


def row_metrics(found_rank: int | None, top_k: int) -> dict[str, Any]:
    return {
        "rank": found_rank,
        "hit1": found_rank == 1,
        "hit3": bool(found_rank and found_rank <= min(3, top_k)),
        "hit5": bool(found_rank and found_rank <= min(5, top_k)),
        "rr": (1.0 / found_rank) if found_rank else 0.0,
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"cases": 0, "hit1": 0.0, "hit3": 0.0, "hit5": 0.0, "mrr": 0.0}
    n = len(rows)
    return {
        "cases": n,
        "hit1": round(sum(bool(r["metrics"]["hit1"]) for r in rows) / n, 4),
        "hit3": round(sum(bool(r["metrics"]["hit3"]) for r in rows) / n, 4),
        "hit5": round(sum(bool(r["metrics"]["hit5"]) for r in rows) / n, 4),
        "mrr": round(sum(float(r["metrics"]["rr"]) for r in rows) / n, 4),
        "latency_ms_median": round(statistics.median(float(r["latencyMs"]) for r in rows), 2),
        "latency_ms_p95": round(
            sorted(float(r["latencyMs"]) for r in rows)[min(n - 1, max(0, math.ceil(n * 0.95) - 1))],
            2,
        ),
    }
def run_tfidf(cases: list[dict[str, Any]], top_k: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    module = load_module(TFIDF_SCRIPT)
    started = time.perf_counter()
    module.build_index()
    build_ms = (time.perf_counter() - started) * 1000
    rows = []
    for case in cases:
        t0 = time.perf_counter()
        results = module.query(case["query"], top_k)
        latency = (time.perf_counter() - t0) * 1000
        paths = [str(item["path"]).replace("\\", "/") for item in results]
        expected = set(case["expected"])
        found = rank(paths, expected)
        rows.append({
            "id": case["id"],
            "category": case["category"],
            "dimensions": case.get("dimensions", []),
            "query": case["query"],
            "expected": case["expected"],
            "paths": paths,
            "scores": [item.get("score") for item in results],
            "latencyMs": round(latency, 2),
            "metrics": row_metrics(found, top_k),
        })
    return rows, {"buildMs": round(build_ms, 2), **aggregate(rows)}


def cognee_call(query: str, top_k: int) -> tuple[dict[str, Any], float]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["VFMEM_COGNEE_ALLOW_REMOTE"] = "0"
    t0 = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(VFMEM), "--json", "recall", query, "--top-k", str(top_k)],
        cwd=ROOT,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=90,
    )
    latency = (time.perf_counter() - t0) * 1000
    if proc.returncode != 0:
        raise RuntimeError(f"vfmem recall failed: {proc.stderr[-800:] or proc.stdout[-800:]}")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"vfmem recall returned invalid JSON: {exc}: {proc.stdout[-800:]}") from exc
    return payload, latency


def run_cognee(cases: list[dict[str, Any]], top_k: int, repeat_ids: set[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = []
    provenance_total = 0
    provenance_ok = 0
    repeatability = []
    datasets: set[str] = set()
    source_digests: set[str] = set()
    for case in cases:
        payload, latency = cognee_call(case["query"], top_k)
        if payload.get("backend") != "cognee-local-derived":
            raise RuntimeError(f"Cognee unavailable for {case['id']}: {payload}")
        dataset = payload.get("dataset")
        source_digest = payload.get("sourceDigest")
        if not isinstance(dataset, str) or not dataset or not isinstance(source_digest, str) or not source_digest:
            raise RuntimeError(f"Cognee missing dataset/sourceDigest for {case['id']}: {payload}")
        if payload.get("requiresCanonicalVerification") is not True:
            raise RuntimeError(f"Cognee canonical-verification flag missing for {case['id']}")
        datasets.add(dataset)
        source_digests.add(source_digest)
        results = payload.get("results") or []
        paths = []
        scores = []
        row_provenance = True
        for item in results:
            provenance_total += 1
            source = item.get("canonicalSource") or {}
            path = source.get("path")
            ok = (
                isinstance(path, str)
                and bool(source.get("sha256"))
                and bool(source.get("category"))
                and bool(source.get("authority"))
                and bool(source.get("freshness"))
                and item.get("requiresCanonicalVerification") is True
            )
            provenance_ok += int(ok)
            row_provenance = row_provenance and ok
            if isinstance(path, str):
                paths.append(path.replace("\\", "/"))
            scores.append(item.get("score"))
        expected = set(case["expected"])
        found = rank(paths, expected)
        repeat_match = None
        if case["id"] in repeat_ids:
            again, _ = cognee_call(case["query"], top_k)
            if (
                again.get("dataset") != dataset
                or again.get("sourceDigest") != source_digest
                or again.get("requiresCanonicalVerification") is not True
            ):
                raise RuntimeError(f"Cognee index changed during repeatability check for {case['id']}")
            again_paths = [
                str((x.get("canonicalSource") or {}).get("path", "")).replace("\\", "/")
                for x in (again.get("results") or [])
            ]
            repeat_match = again_paths == paths
            repeatability.append(bool(repeat_match))
        rows.append({
            "id": case["id"],
            "category": case["category"],
            "dimensions": case.get("dimensions", []),
            "query": case["query"],
            "expected": case["expected"],
            "paths": paths,
            "scores": scores,
            "latencyMs": round(latency, 2),
            "provenanceOk": row_provenance,
            "repeatabilityMatch": repeat_match,
            "metrics": row_metrics(found, top_k),
        })
    if len(datasets) != 1 or len(source_digests) != 1:
        raise RuntimeError(
            f"Cognee benchmark crossed index versions: datasets={sorted(datasets)} digests={sorted(source_digests)}"
        )
    summary = aggregate(rows)
    summary["dataset"] = next(iter(datasets))
    summary["sourceDigest"] = next(iter(source_digests))
    summary["provenance"] = round(provenance_ok / provenance_total, 4) if provenance_total else 0.0
    summary["repeatability"] = round(sum(repeatability) / len(repeatability), 4) if repeatability else None
    return rows, summary


def by_category(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["category"]].append(row)
    return {key: aggregate(value) for key, value in sorted(grouped.items())}


def by_dimension(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        for dimension in row.get("dimensions", []):
            grouped[str(dimension)].append(row)
    return {key: aggregate(value) for key, value in sorted(grouped.items())}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, default=SPEC)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--backend", choices=["both", "tfidf", "cognee"], default="both")
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    cases = spec["cases"]
    top_k = int(spec.get("top_k", 5))
    repeat_ids = set(spec.get("repeatability_cases", []))

    tfidf_rows: list[dict[str, Any]] = []
    cognee_rows: list[dict[str, Any]] = []
    tfidf_summary: dict[str, Any] | None = None
    cognee_summary: dict[str, Any] | None = None
    if args.backend in {"both", "tfidf"}:
        tfidf_rows, tfidf_summary = run_tfidf(cases, top_k)
    if args.backend in {"both", "cognee"}:
        cognee_rows, cognee_summary = run_cognee(cases, top_k, repeat_ids)

    body = {
        "schema": 1,
        "phase": 7,
        "benchmark": spec["id"],
        "date": "2026-09-27",
        "backendMode": args.backend,
        "authority": "vfmem canonical; both retrieval backends are context-only",
        "judge": "deterministic expected canonical source paths; no LLM judge",
        "topK": top_k,
        "cases": len(cases),
        "tfidf": ({
            "summary": tfidf_summary,
            "byCategory": by_category(tfidf_rows),
            "byDimension": by_dimension(tfidf_rows),
            "rows": tfidf_rows,
        } if tfidf_summary is not None else None),
        "cognee": ({
            "summary": cognee_summary,
            "byCategory": by_category(cognee_rows),
            "byDimension": by_dimension(cognee_rows),
            "rows": cognee_rows,
        } if cognee_summary is not None else None),
        "guardrails": {
            "requiresCanonicalVerification": True,
            "remoteProvidersAllowed": False,
            "writebackToCanonicalMemory": False,
            "incrementalRecurringCostIls": 0,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "out": str(args.out),
        "tfidf": tfidf_summary,
        "cognee": cognee_summary,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
