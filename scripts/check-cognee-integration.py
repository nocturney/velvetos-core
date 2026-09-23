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
    if sync.get("knowledgeProfile") != "velvetos-durable-v1":
        fail("unexpected Cognee knowledge profile")
    if sync.get("ingestionRevision") != "granular-file-multilingual-v2":
        fail("unexpected Cognee ingestion revision")
    if sync.get("embeddingProvider") != "fastembed":
        fail("Cognee embeddings must stay local fastembed")
    if sync.get("embeddingModel") != "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2":
        fail("unexpected Cognee multilingual embedding model")
    if sync.get("embeddingDimensions") != 384:
        fail("unexpected Cognee embedding dimensions")
    if sync.get("retrievalMode") != "chunks-with-canonical-provenance-v1":
        fail("Cognee retrieval must retain canonical chunk provenance")
    add_batch = sync.get("addDataPerBatch")
    chunk_size = sync.get("chunkSize")
    chunks_per_batch = sync.get("chunksPerBatch")
    cognify_batch = sync.get("cognifyDataPerBatch")
    if not isinstance(add_batch, int) or not 1 <= add_batch <= 32:
        fail("Cognee addDataPerBatch must be 1..32")
    if chunk_size != 384:
        fail("Cognee chunkSize must be 384 for the local multilingual model")
    if not isinstance(chunks_per_batch, int) or not 1 <= chunks_per_batch <= 32:
        fail("Cognee chunksPerBatch must be 1..32")
    if not isinstance(cognify_batch, int) or not 1 <= cognify_batch <= 32:
        fail("Cognee cognifyDataPerBatch must be 1..32")
    sources = sync.get("sources", [])
    metadata = sync.get("sourceMetadata") or {}
    if len(sources) < 20 or len(sources) != len(set(sources)):
        fail("Cognee durable knowledge allowlist is too small or contains duplicates")
    required_categories = {
        "memory-governance", "architecture", "operations", "production", "media",
        "publication", "growth", "brand-copy", "creative", "sales", "research",
        "tooling-capability",
    }
    seen_categories = set()
    forbidden_parts = ("/live/", "/jobs/", "/out/", "/dead-letter/")
    for rel in sources:
        path = (ROOT / rel).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
            fail(f"missing/unsafe Cognee source {rel}")
        normalized = "/" + rel.replace("\\", "/").lower() + "/"
        if any(part in normalized for part in forbidden_parts):
            fail(f"ephemeral/live path cannot be indexed by Cognee: {rel}")
        meta = metadata.get(rel)
        if not isinstance(meta, dict):
            fail(f"missing Cognee metadata for {rel}")
        for key in ("category", "authority", "freshness"):
            if not str(meta.get(key, "")).strip():
                fail(f"missing Cognee metadata field {key} for {rel}")
        seen_categories.add(meta["category"])
    if not required_categories.issubset(seen_categories):
        fail("Cognee durable knowledge categories incomplete")
    denied = set(cfg.get("deny") or [])
    required_denied = {
        "secrets", "credentials", "raw-transcripts", "customer-sensitive-records",
        "live-finance-state", "live-production-state", "live-publication-state",
        "live-inventory-state", "live-schedule-state", "ephemeral-job-output",
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
        "requiresCanonicalVerification", "cognee.add", "cognee.cognify",
        "raise_on_error=True", "tempfile.mkstemp", "os.fsync",
        "PermissionError", "atomic JSON readback mismatch",
        "materialize_ingest_files", "documentMap", "SearchType.CHUNKS",
        "canonicalSource", "chunks-with-canonical-provenance-v1",
        "active-state.json", "legacy rollback evidence",
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