#!/usr/bin/env python3
"""Validate Phase 7 memory rationalization evidence without creating memory authority."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "packages" / "vfharness" / "state" / "memory-retrieval-phase7-2026-09-27.json"
DECISION = ROOT / "packages" / "vfharness" / "state" / "memory-rationalization-phase7-2026-09-27.json"


def load(path: Path) -> dict:
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    bench = load(BENCH)
    decision = load(DECISION)

    assert decision.get("status") == "COMPLETE"
    assert decision.get("incrementalRecurringCostIls") == 0

    roles = decision.get("roles") or {}
    assert roles.get("vfmem") == "CANONICAL_DURABLE_MEMORY"
    assert roles.get("cognee") == "DERIVED_SEMANTIC_INDEX"
    assert roles.get("dejaVu") == "SESSION_HISTORY_ADJUNCT"
    assert roles.get("hindsight") == "NOT_PROMOTED"
    assert roles.get("supermemory") == "NOT_PROMOTED"

    guard = bench.get("guardrails") or {}
    assert guard.get("requiresCanonicalVerification") is True
    assert guard.get("remoteProvidersAllowed") is False
    assert guard.get("writebackToCanonicalMemory") is False
    assert guard.get("incrementalRecurringCostIls") == 0
    assert int(bench.get("cases", 0)) >= 22

    tfidf = bench.get("tfidf") or {}
    cognee = bench.get("cognee") or {}
    assert tfidf.get("summary"), "missing TF-IDF benchmark summary"
    assert cognee.get("summary"), "missing Cognee benchmark summary"

    cognee_summary = cognee["summary"]
    assert str(cognee_summary.get("dataset") or "").startswith("velvetos_shared_")
    assert len(str(cognee_summary.get("sourceDigest") or "")) == 64
    assert cognee_summary.get("provenance") == 1.0, "Cognee canonical provenance must be complete"
    assert cognee_summary.get("repeatability") == 1.0, "Cognee repeated retrieval must be stable"
    for row in cognee.get("rows") or []:
        paths = row.get("paths") or []
        assert len(paths) == len(set(paths)), f"Cognee duplicate canonical sources in {row.get('id')}"

    for backend_name, backend in (("tfidf", tfidf), ("cognee", cognee)):
        dimensions = backend.get("byDimension") or {}
        for name in ("temporal_correctness", "contradiction_handling"):
            row = dimensions.get(name)
            assert row and int(row.get("cases", 0)) >= 2, (
                f"{backend_name} missing measured {name} cases"
            )

    candidates = decision.get("candidates") or {}
    assert candidates.get("hindsight", {}).get("installed") is False
    assert candidates.get("supermemory", {}).get("installed") is False
    assert candidates.get("dejaVu", {}).get("canonicalAuthority") is False
    assert candidates.get("cognee", {}).get("canonicalAuthority") is False
    assert candidates.get("cognee", {}).get("dataset") == cognee_summary["dataset"]
    assert candidates.get("cognee", {}).get("sourceDigest") == cognee_summary["sourceDigest"]

    assert decision.get("newAlwaysOnMemorySystems") == 0
    print(
        "OK memory-rationalization "
        f"cases={bench['cases']} provenance=1 repeatability=1 cost=0 "
        "authority=vfmem"
    )


if __name__ == "__main__":
    main()
