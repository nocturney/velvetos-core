#!/usr/bin/env python3
"""Static fail-closed contract check for the optional vfmem Cognee backend.

No network and no Cognee import. This sensor is safe in generic CI.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "packages" / "vfmem" / "cognee.json"
ADAPTER = ROOT / "packages" / "vfmem" / "scripts" / "vf_cognee.py"
VFMEM = ROOT / "scripts" / "vfmem.py"
RUNTIME = ROOT / "packages" / "vfmem" / "scripts" / "vf_cognee_runtime.py"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not CFG.is_file() or not ADAPTER.is_file() or not VFMEM.is_file() or not RUNTIME.is_file():
        fail("Cognee integration files missing")
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    if cfg.get("schema") != "vf.cognee.v1":
        fail("unexpected Cognee contract schema")
    if cfg.get("role") != "optional-local-derived-semantic-backend":
        fail("Cognee must remain an optional derived backend")
    if cfg.get("canonicalMemory") != "vfmem":
        fail("vfmem must remain canonical memory")
    if cfg.get("authority") != "context-only-never-authority":
        fail("Cognee recall must not become authority")
    if cfg.get("failover") != "vfmem-local-search":
        fail("Cognee requires deterministic vfmem fallback")
    if cfg.get("remoteProvidersAllowedByDefault") is not False:
        fail("remote model providers must be disabled by default")
    version = str(cfg.get("pinnedVersion", ""))
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        fail("Cognee version must be a stable exact pin")
    sync = cfg.get("sync") or {}
    if sync.get("strategy") != "content-hash-versioned-dataset":
        fail("sync must use immutable content-hash datasets")
    if sync.get("requiresCanonicalVerification") is not True:
        fail("recalled context must require canonical verification")
    for rel in sync.get("sources", []):
        path = (ROOT / rel).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
            fail(f"missing/unsafe Cognee source {rel}")
    denied = set(cfg.get("deny") or [])
    required_denied = {
        "secrets", "raw-transcripts", "customer-sensitive-records",
        "live-finance-state", "live-production-state", "live-publication-state",
    }
    if not required_denied.issubset(denied):
        fail("Cognee deny classes incomplete")
    updates = cfg.get("updates") or {}
    for key in ("stagingVenv", "requireSmoke", "requireVfmemSensor",
                "rollbackOnFailure", "updatePinOnlyAfterGreen"):
        if updates.get(key) is not True:
            fail(f"safe update gate disabled: {key}")

    adapter = ADAPTER.read_text(encoding="utf-8")
    for needle in (
        "PYTHON_DOTENV_DISABLED", "GRAPH_EXTRACTOR", "gliner_demo",
        "VFMEM_COGNEE_ALLOW_REMOTE", "content-hash-versioned-dataset",
        "requiresCanonicalVerification",
    ):
        if needle not in adapter and needle not in CFG.read_text(encoding="utf-8"):
            fail(f"adapter/config missing safety marker {needle}")

    runtime = RUNTIME.read_text(encoding="utf-8")
    for needle in ("runtime-stage.v1", "promotion blocked", "rollback", "post-promotion doctor"):
        if needle not in runtime:
            fail(f"runtime updater missing safety marker {needle}")

    vfmem = VFMEM.read_text(encoding="utf-8")
    for needle in ("cmd_recall", "vfmem-fallback", "cognee-recall-failed"):
        if needle not in vfmem:
            fail(f"vfmem fallback contract missing {needle}")

    print(f"OK cognee pin={version} role=derived fallback=vfmem sources={len(sync.get('sources', []))}")


if __name__ == "__main__":
    main()