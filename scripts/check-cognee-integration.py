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
GROK_MANIFEST = ROOT / "automation" / "grok" / "manifest.json"
GROK_COGNEE = ROOT / "automation" / "grok" / "cognee-routines.json"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not CFG.is_file() or not ADAPTER.is_file() or not VFMEM.is_file() or not RUNTIME.is_file():
        fail("Cognee integration files missing")
    if not GROK_MANIFEST.is_file() or not GROK_COGNEE.is_file():
        fail("Cognee Grok cutover contract files missing")
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

    grok_manifest = json.loads(GROK_MANIFEST.read_text(encoding="utf-8"))
    cutover = grok_manifest.get("cogneeCutover") or {}
    if int(grok_manifest.get("version", 0)) < 4:
        fail("Grok manifest must include verified Cognee cutover contract v4+")
    if cutover.get("packet") != "automation/grok/cognee-routines.json":
        fail("Grok manifest is not bound to Cognee cutover packet")
    if cutover.get("providerActivation") != "live_verified":
        fail("Cognee Grok provider state must remain live_verified after cutover")
    if cutover.get("chatgptCopies") != "disabled_after_verified_grok_readback":
        fail("ChatGPT Cognee copies must stay disabled after verified Grok cutover")
    if cutover.get("verifiedDate") != "2026-09-23":
        fail("Cognee Grok cutover verification date missing")
    if cutover.get("providerRoutineIds") != {
        "cognee-memory-sync": "cognee-memory-sync",
        "cognee-stable-updates": "cognee-stable-updates",
    }:
        fail("unexpected live Grok Cognee provider routine IDs")
    guard_binding = cutover.get("integrityGuard") or {}
    if guard_binding.get("providerRoutineId") != "velvetos-integrity-guard":
        fail("Integrity Guard provider binding missing after Cognee cutover")
    if guard_binding.get("enabled") is not True or guard_binding.get("cadence") != "daily 01:45":
        fail("Integrity Guard enabled/cadence drift after Cognee cutover")
    if guard_binding.get("protectedRoutineCount") != 9:
        fail("Integrity Guard must protect nine routines after Cognee cutover")

    manifest_routines = {row.get("id"): row for row in (grok_manifest.get("routines") or [])}
    expected_manifest = {
        "cognee-memory-sync": "daily 06:30",
        "cognee-stable-updates": "Monday 10:00",
    }
    if len(manifest_routines) != 9:
        fail("Grok manifest must contain the nine protected routines")
    for routine_id, cadence in expected_manifest.items():
        row = manifest_routines.get(routine_id) or {}
        if row.get("cadence") != cadence or row.get("enabled") is not True:
            fail(f"verified Grok manifest drift for {routine_id}")

    grok_packet = json.loads(GROK_COGNEE.read_text(encoding="utf-8"))
    if grok_packet.get("schema") != "vf.grok.cognee-cutover.v1":
        fail("unexpected Cognee Grok cutover packet schema")
    if grok_packet.get("providerActivation") != "live_verified":
        fail("Cognee Grok packet must preserve verified provider activation")
    if grok_packet.get("verifiedReadbackOn") != "2026-09-23":
        fail("Cognee Grok packet missing verified readback date")
    if grok_packet.get("chatgptCopiesState") != "disabled_after_verified_grok_readback":
        fail("Cognee Grok packet must record disabled ChatGPT copies")
    copies = grok_packet.get("chatgptCopies") or {}
    expected_copies = {
        "cognee-memory-sync": "6ab3734b12b0819199033ef833efc7f4",
        "cognee-stable-updates": "6ab3734c95b081919188941903f4ec2c",
    }
    if copies != expected_copies:
        fail("Cognee Grok cutover packet has unexpected ChatGPT automation bindings")
    routines = {row.get("id"): row for row in (grok_packet.get("routines") or [])}
    expected_cadence = {
        "cognee-memory-sync": "daily 06:30",
        "cognee-stable-updates": "Monday 10:00",
    }
    for routine_id, cadence in expected_cadence.items():
        row = routines.get(routine_id) or {}
        if row.get("cadence") != cadence or row.get("desiredEnabled") is not True:
            fail(f"unexpected Grok cadence/enabled intent for {routine_id}")
        prompt = str(row.get("prompt") or "")
        for needle in ("66", "active-state.json", "canonicalSource", "requiresCanonicalVerification=true"):
            if needle not in prompt:
                fail(f"Grok Cognee prompt {routine_id} missing {needle}")

    verified = grok_packet.get("verifiedReadback") or {}
    expected_readback = {
        "cognee-memory-sync": "CRON_TZ=Asia/Jerusalem 30 6 * * *",
        "cognee-stable-updates": "CRON_TZ=Asia/Jerusalem 0 10 * * 1",
    }
    for routine_id, schedule in expected_readback.items():
        row = verified.get(routine_id) or {}
        if row.get("providerRoutineId") != routine_id:
            fail(f"verified Grok provider ID drift for {routine_id}")
        if row.get("active") is not True or row.get("timezone") != "Asia/Jerusalem":
            fail(f"verified Grok active/timezone drift for {routine_id}")
        if row.get("schedule") != schedule or row.get("instructionMatchesCanonicalPacket") is not True:
            fail(f"verified Grok schedule/instruction drift for {routine_id}")

    guard = verified.get("integrityGuard") or {}
    if guard.get("providerRoutineId") != "velvetos-integrity-guard":
        fail("verified Integrity Guard provider ID missing")
    if guard.get("active") is not True or guard.get("timezone") != "Asia/Jerusalem":
        fail("verified Integrity Guard active/timezone drift")
    if guard.get("schedule") != "CRON_TZ=Asia/Jerusalem 45 1 * * *":
        fail("verified Integrity Guard schedule drift")
    if guard.get("protectedRoutineCount") != 9:
        fail("verified Integrity Guard must protect nine routines")
    expected_titles = {
        "VelvetOS Integrity Guard", "Velvet Research Seat", "OpenPost Release Watch",
        "Velvet Morning Brief", "Morning Delivery Guard", "VelvetOS Office Loop",
        "Weekly Research Accountability", "Cognee Memory Sync", "Cognee Stable Updates",
    }
    if set(guard.get("protectedRoutineTitles") or []) != expected_titles:
        fail("verified Integrity Guard protected-title set drift")
    if "sole scheduler" not in str(grok_packet.get("cutoverRule") or ""):
        fail("Cognee Grok cutover packet must record Grok as sole scheduler")

    print(f"OK cognee pin={version} role=derived fallback=vfmem sources={len(sync.get('sources', []))}")


if __name__ == "__main__":
    main()