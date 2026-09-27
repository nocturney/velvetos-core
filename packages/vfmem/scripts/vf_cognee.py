#!/usr/bin/env python3
"""Optional local Cognee backend for vfmem.

Cognee is a derived semantic index. Canonical Git/live sources remain authoritative.
No command here publishes, sends, spends, or promotes recalled context to policy.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "packages" / "vfmem" / "cognee.json"
REMOTE_ENV = (
    "LLM_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY",
    "MISTRAL_API_KEY", "COHERE_API_KEY", "EMBEDDING_API_KEY",
    "EMBEDDING_ENDPOINT", "EMBEDDING_API_BASE", "EMBEDDING_PROVIDER",
    "EMBEDDING_MODEL", "EMBEDDING_DIMENSIONS", "LLM_ENDPOINT",
    "LLM_PROVIDER", "LLM_MODEL",
)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def index_contract(cfg: dict[str, Any]) -> dict[str, Any]:
    sync = cfg["sync"]
    return {
        "ingestionRevision": sync.get("ingestionRevision"),
        "embeddingProvider": sync.get("embeddingProvider"),
        "embeddingModel": sync.get("embeddingModel"),
        "embeddingDimensions": int(sync.get("embeddingDimensions", 0)),
        "chunkSize": int(sync.get("chunkSize", 0)),
        "chunksPerBatch": int(sync.get("chunksPerBatch", 0)),
        "retrievalMode": sync.get("retrievalMode"),
    }


def runtime_root(cfg: dict[str, Any]) -> Path:
    override = os.environ.get("VFMEM_COGNEE_ROOT")
    if override:
        return Path(override).expanduser()
    velvet_runtime = os.environ.get("VELVETOS_RUNTIME_ROOT")
    if velvet_runtime:
        return Path(velvet_runtime).expanduser() / "Cognee" / "cognee"
    return Path(cfg["runtimeRoot"]).expanduser()


def apply_runtime_env(root: Path, cfg: dict[str, Any] | None = None) -> None:
    root.mkdir(parents=True, exist_ok=True)
    cfg = cfg or load_config()
    os.environ["PYTHON_DOTENV_DISABLED"] = "1"
    os.environ["GRAPH_EXTRACTOR"] = "gliner_demo"
    os.environ["CACHING"] = "false"
    os.environ["ENABLE_BACKEND_ACCESS_CONTROL"] = "false"
    # Keep the host HuggingFace cache shared; model weights are disposable cache,
    # while Cognee data/system paths remain isolated under the VelvetOS runtime.
    for key, rel in (
        ("DATA_ROOT_DIRECTORY", "data"),
        ("SYSTEM_ROOT_DIRECTORY", "system"),
        ("CACHE_ROOT_DIRECTORY", "cache"),
        ("COGNEE_LOGS_DIR", "logs"),
        ("FASTEMBED_CACHE_PATH", "cache/fastembed"),
    ):
        os.environ[key] = str(root / rel)
    if os.environ.get("VFMEM_COGNEE_ALLOW_REMOTE") != "1":
        for key in REMOTE_ENV:
            os.environ.pop(key, None)
    contract = index_contract(cfg)
    if contract["embeddingProvider"] != "fastembed":
        raise RuntimeError("Cognee derived memory requires local fastembed embeddings")
    if not str(contract["embeddingModel"] or "").strip() or contract["embeddingDimensions"] <= 0:
        raise RuntimeError("Cognee local embedding model contract is incomplete")
    os.environ["EMBEDDING_PROVIDER"] = contract["embeddingProvider"]
    os.environ["EMBEDDING_MODEL"] = contract["embeddingModel"]
    os.environ["EMBEDDING_DIMENSIONS"] = str(contract["embeddingDimensions"])


def installed_version() -> str | None:
    try:
        return importlib.metadata.version("cognee")
    except importlib.metadata.PackageNotFoundError:
        return None


def source_manifest(cfg: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    limit = int(cfg["sync"]["maxSourceBytes"])
    h = hashlib.sha256()
    profile = str(cfg["sync"].get("knowledgeProfile", ""))
    contract_json = json.dumps(index_contract(cfg), sort_keys=True, separators=(",", ":"))
    h.update(profile.encode("utf-8") + b"\0" + contract_json.encode("utf-8") + b"\n")
    metadata = cfg["sync"].get("sourceMetadata") or {}
    for rel in cfg["sync"]["sources"]:
        path = (ROOT / rel).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
            raise RuntimeError(f"missing canonical memory source: {rel}")
        meta = metadata.get(rel)
        if not isinstance(meta, dict):
            raise RuntimeError(f"missing Cognee source metadata: {rel}")
        for key in ("category", "authority", "freshness"):
            if not str(meta.get(key, "")).strip():
                raise RuntimeError(f"missing Cognee source metadata field {key}: {rel}")
        size = path.stat().st_size
        if size > limit:
            raise RuntimeError(f"source exceeds configured size cap: {rel}")
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        row = {"path": rel, "sha256": digest, "bytes": size, **meta}
        rows.append(row)
        meta_hash = json.dumps(meta, sort_keys=True, separators=(",", ":"))
        h.update(rel.encode("utf-8") + b"\0" + digest.encode("ascii") + b"\0" + meta_hash.encode("utf-8") + b"\n")
    return h.hexdigest(), rows


def state_path(root: Path) -> Path:
    # state.json is retained as legacy rollback evidence. On the Windows host it can
    # be held open without delete-sharing, which prevents atomic replacement. The v2
    # pointer uses a fresh filename so every cutover still goes through os.replace.
    return root / "active-state.json"


def read_state(root: Path) -> dict[str, Any] | None:
    path = state_path(root)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, body: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(body, ensure_ascii=False, indent=2) + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        for attempt in range(8):
            try:
                os.replace(tmp, path)
                break
            except PermissionError:
                if os.name != "nt":
                    raise
                if attempt < 7:
                    time.sleep(0.05 * (attempt + 1))
                    continue
                # Windows can deny rename/replace on an otherwise writable JSON
                # pointer (for example due to delete-sharing/legacy ownership).
                # Preserve the previous derived pointer, then fail closed unless
                # an fsynced in-place write and exact readback both succeed.
                rollback = path.with_name(path.name + ".windows-rollback")
                if path.is_file():
                    previous = path.read_bytes()
                    rollback.write_bytes(previous)
                    if rollback.read_bytes() != previous:
                        raise RuntimeError(f"Windows JSON rollback readback mismatch: {rollback}")
                with path.open("w", encoding="utf-8", newline="\n") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                break
        observed = json.loads(path.read_text(encoding="utf-8"))
        if observed != body:
            raise RuntimeError(f"atomic JSON readback mismatch: {path}")
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def materialize_ingest_files(root: Path, digest: str, sources: list[dict[str, Any]]) -> tuple[list[str], dict[str, str]]:
    folder = root / "ingest" / digest[:16]
    folder.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    document_map: dict[str, str] = {}
    for index, row in enumerate(sources, 1):
        rel = row["path"]
        token = hashlib.sha256(rel.encode("utf-8")).hexdigest()[:12]
        document_name = f"{index:03d}-{token}"
        path = folder / f"{document_name}.txt"
        source_path = ROOT / rel
        raw = source_path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise RuntimeError(f"canonical source changed during materialization: {rel}; rerun sync")
        text = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        payload = (
            f"VELVETOS_CANONICAL_SOURCE: {rel}\n"
            f"VELVETOS_KNOWLEDGE_CATEGORY: {row['category']}\n"
            f"VELVETOS_SOURCE_AUTHORITY: {row['authority']}\n"
            f"VELVETOS_FRESHNESS: {row['freshness']}\n"
            "COGNEE_ROLE: derived context only; verify canonical source before action.\n\n"
            + text
        )
        if path.is_file():
            if path.read_text(encoding="utf-8") != payload:
                raise RuntimeError(f"derived Cognee ingest file mismatch: {path}")
        else:
            path.write_text(payload, encoding="utf-8", newline="\n")
            if path.read_text(encoding="utf-8") != payload:
                raise RuntimeError(f"derived Cognee ingest file readback mismatch: {path}")
        paths.append(str(path))
        document_map[document_name] = rel
    if len(document_map) != len(sources):
        raise RuntimeError("Cognee derived document names are not unique")
    return paths, document_map


def emit(body: Any, code: int = 0) -> int:
    if os.environ.get("VFMEM_COGNEE_MACHINE") == "1":
        print("VFMEM_COGNEE_JSON:" + json.dumps(body, ensure_ascii=True, separators=(",", ":"), default=str))
    else:
        print(json.dumps(body, ensure_ascii=False, indent=2, default=str))
    return code


def dataset_for(cfg: dict[str, Any], digest: str) -> str:
    prefix = re.sub(r"[^A-Za-z0-9_]+", "_", cfg["datasetPrefix"]).strip("_")
    return f"{prefix}_{digest[:16]}"


def serialize_entry(entry: Any) -> Any:
    if hasattr(entry, "model_dump"):
        return entry.model_dump(mode="json")
    if isinstance(entry, (str, int, float, bool, type(None), dict, list)):
        return entry
    return str(entry)


async def sync_memory(cfg: dict[str, Any], root: Path) -> dict[str, Any]:
    digest, sources = source_manifest(cfg)
    dataset = dataset_for(cfg, digest)
    current = read_state(root)
    contract = index_contract(cfg)
    if current and current.get("sourceDigest") == digest and current.get("dataset") == dataset:
        document_map = current.get("documentMap")
        if current.get("indexContract") != contract or not isinstance(document_map, dict) or len(document_map) != len(sources):
            raise RuntimeError("current Cognee state lacks the canonical provenance/index contract")
        return {
            "status": "CURRENT",
            "dataset": dataset,
            "knowledgeProfile": cfg["sync"].get("knowledgeProfile"),
            "sourceCount": len(sources),
            "indexContract": contract,
            "sources": sources,
        }

    if contract["retrievalMode"] != "chunks-with-canonical-provenance-v1":
        raise RuntimeError("unsupported Cognee retrieval contract")
    apply_runtime_env(root, cfg)
    import cognee

    progress_path = root / f"sync-{digest[:16]}.json"
    progress = {
        "dataset": dataset,
        "ingestionRevision": cfg["sync"].get("ingestionRevision"),
        "indexContract": contract,
        "sourceCount": len(sources),
        "added": False,
        "cognified": False,
    }
    if progress_path.is_file():
        loaded = json.loads(progress_path.read_text(encoding="utf-8"))
        if loaded.get("dataset") == dataset:
            progress.update(loaded)

    add_data_per_batch = int(cfg["sync"].get("addDataPerBatch", 1))
    chunk_size = int(cfg["sync"].get("chunkSize", 384))
    chunks_per_batch = int(cfg["sync"].get("chunksPerBatch", 1))
    cognify_data_per_batch = int(cfg["sync"].get("cognifyDataPerBatch", 1))
    if not 1 <= add_data_per_batch <= 32:
        raise RuntimeError("Cognee addDataPerBatch must be 1..32")
    if not 128 <= chunk_size <= 512:
        raise RuntimeError("Cognee chunkSize must be 128..512 for the configured local multilingual model")
    if not 1 <= chunks_per_batch <= 32:
        raise RuntimeError("Cognee chunksPerBatch must be 1..32")
    if not 1 <= cognify_data_per_batch <= 32:
        raise RuntimeError("Cognee cognifyDataPerBatch must be 1..32")

    ingest_paths, document_map = materialize_ingest_files(root, digest, sources)

    if not progress.get("added"):
        await cognee.add(
            ingest_paths,
            dataset_name=dataset,
            data_per_batch=add_data_per_batch,
        )
        progress["added"] = True
        atomic_json(progress_path, progress)

    if not progress.get("cognified"):
        await cognee.cognify(
            datasets=dataset,
            extractor="gliner_demo",
            chunk_size=chunk_size,
            chunks_per_batch=chunks_per_batch,
            data_per_batch=cognify_data_per_batch,
            raise_on_error=True,
        )
        progress["cognified"] = True
        atomic_json(progress_path, progress)

    final_digest, _ = source_manifest(cfg)
    if final_digest != digest:
        raise RuntimeError(
            "canonical sources changed during Cognee sync; refusing active-state cutover; rerun sync"
        )

    state = {
        "schema": "vf.cognee.state.v1",
        "dataset": dataset,
        "sourceDigest": digest,
        "knowledgeProfile": cfg["sync"].get("knowledgeProfile"),
        "sourceCount": len(sources),
        "categories": sorted({row["category"] for row in sources}),
        "sources": sources,
        "indexContract": contract,
        "documentMap": document_map,
        "cogneeVersion": installed_version(),
        "syncedAt": datetime.now(timezone.utc).isoformat(),
        "authority": cfg["authority"],
    }
    atomic_json(state_path(root), state)
    return {"status": "SYNCED", **state}


async def recall_memory(cfg: dict[str, Any], root: Path, query: str, top_k: int) -> dict[str, Any]:
    state = read_state(root)
    if not state:
        raise RuntimeError("Cognee index is not synced")
    digest, sources = source_manifest(cfg)
    if state.get("sourceDigest") != digest:
        raise RuntimeError("Cognee index is stale; run sync before semantic recall")
    contract = index_contract(cfg)
    if state.get("indexContract") != contract:
        raise RuntimeError("Cognee index contract does not match current configuration")
    document_map = state.get("documentMap")
    if not isinstance(document_map, dict) or len(document_map) != len(sources):
        raise RuntimeError("Cognee canonical document provenance map is missing or incomplete")
    source_by_path = {row["path"]: row for row in sources}
    apply_runtime_env(root, cfg)
    import cognee
    from cognee.modules.search.types import SearchType

    # Cognee ranks chunks, and several top chunks can come from the same
    # canonical document. vfmem recall is source-oriented, so over-fetch chunks
    # and collapse them to unique canonical sources while preserving rank.
    candidate_top_k = min(max(top_k * 8, 20), 100)
    rows = await cognee.recall(
        query,
        query_type=SearchType.CHUNKS,
        auto_route=False,
        datasets=[state["dataset"]],
        top_k=candidate_top_k,
        only_context=False,
    )
    results = []
    seen_sources: set[str] = set()
    for row in rows:
        item = serialize_entry(row)
        if not isinstance(item, dict):
            raise RuntimeError("Cognee chunk result is not structured")
        metadata = item.get("metadata") or {}
        document_name = metadata.get("document_name")
        canonical_path = document_map.get(document_name)
        source = source_by_path.get(canonical_path)
        if not source:
            raise RuntimeError("Cognee chunk result is missing canonical provenance")
        if canonical_path in seen_sources:
            continue
        seen_sources.add(canonical_path)
        results.append({
            "kind": item.get("kind"),
            "search_type": item.get("search_type"),
            "text": item.get("text"),
            "score": item.get("score"),
            "chunk": {
                "documentName": document_name,
                "chunkIndex": metadata.get("chunk_index"),
                "chunkId": metadata.get("chunk_id"),
            },
            "canonicalSource": {
                "path": source["path"],
                "sha256": source["sha256"],
                "category": source["category"],
                "authority": source["authority"],
                "freshness": source["freshness"],
            },
            "requiresCanonicalVerification": True,
        })
        if len(results) >= top_k:
            break
    return {
        "status": "OK",
        "backend": "cognee-local-derived",
        "dataset": state["dataset"],
        "sourceDigest": state["sourceDigest"],
        "indexContract": contract,
        "authority": cfg["authority"],
        "requiresCanonicalVerification": cfg["sync"]["requiresCanonicalVerification"],
        "results": results,
    }


async def smoke(cfg: dict[str, Any], root: Path) -> dict[str, Any]:
    apply_runtime_env(root / "smoke", cfg)
    import cognee
    from cognee.modules.search.types import SearchType

    token = "cobalt-sparrow-7319"
    contract_hash = hashlib.sha256(
        json.dumps(index_contract(cfg), sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:8]
    dataset = f"vf_cognee_smoke_{cfg['pinnedVersion'].replace('.', '_')}_{contract_hash}"
    await cognee.remember(
        f"VelvetOS synthetic smoke sentinel is {token}.",
        dataset_name=dataset,
        self_improvement=False,
        extractor="gliner_demo",
    )
    rows = await cognee.recall(
        "What is the VelvetOS synthetic smoke sentinel?",
        query_type=SearchType.CHUNKS,
        auto_route=False,
        datasets=[dataset],
        top_k=5,
        only_context=False,
    )
    rendered = json.dumps([serialize_entry(x) for x in rows], ensure_ascii=False, default=str)
    if token not in rendered:
        raise RuntimeError("Cognee smoke recall missed synthetic sentinel")
    return {
        "status": "PASS",
        "version": installed_version(),
        "dataset": dataset,
        "indexContract": index_contract(cfg),
    }


def doctor(cfg: dict[str, Any], root: Path) -> dict[str, Any]:
    digest, sources = source_manifest(cfg)
    contract = index_contract(cfg)
    version = installed_version()
    root.mkdir(parents=True, exist_ok=True)
    probe = root / ".write-probe"
    probe.write_text("ok", encoding="utf-8")
    probe.unlink()
    state = read_state(root)
    document_map = state.get("documentMap") if isinstance(state, dict) else None
    state_current = bool(
        isinstance(state, dict)
        and state.get("sourceDigest") == digest
        and state.get("dataset") == dataset_for(cfg, digest)
        and state.get("indexContract") == contract
        and isinstance(document_map, dict)
        and len(document_map) == len(sources)
    )
    return {
        "status": "PASS" if version == cfg["pinnedVersion"] else "BLOCKED",
        "installedVersion": version,
        "pinnedVersion": cfg["pinnedVersion"],
        "versionMatch": version == cfg["pinnedVersion"],
        "runtimeRoot": str(root),
        "sourceDigest": digest,
        "knowledgeProfile": cfg["sync"].get("knowledgeProfile"),
        "sourceCount": len(sources),
        "categories": sorted({row["category"] for row in sources}),
        "sources": sources,
        "indexContract": contract,
        "stateCurrent": state_current,
        "activeDataset": state.get("dataset") if isinstance(state, dict) else None,
        "activeSourceDigest": state.get("sourceDigest") if isinstance(state, dict) else None,
        "remoteProvidersAllowed": os.environ.get("VFMEM_COGNEE_ALLOW_REMOTE") == "1",
        "authority": cfg["authority"],
    }


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")
    sub.add_parser("sync")
    recall = sub.add_parser("recall")
    recall.add_argument("query", nargs="+")
    recall.add_argument("--top-k", type=int, default=8)
    sub.add_parser("smoke")
    sub.add_parser("version")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    cfg = load_config()
    root = runtime_root(cfg)
    try:
        if args.cmd == "doctor":
            result = doctor(cfg, root)
            return emit(result, 0 if result["status"] == "PASS" else 2)
        if args.cmd == "sync":
            return emit(asyncio.run(sync_memory(cfg, root)))
        if args.cmd == "recall":
            if not 1 <= args.top_k <= 50:
                raise RuntimeError("top-k must be 1..50")
            return emit(asyncio.run(recall_memory(cfg, root, " ".join(args.query), args.top_k)))
        if args.cmd == "smoke":
            return emit(asyncio.run(smoke(cfg, root)))
        if args.cmd == "version":
            return emit({"installed": installed_version(), "pinned": cfg["pinnedVersion"]})
        raise RuntimeError("unknown command")
    except Exception as exc:
        return emit({"status": "BLOCKED", "reason": str(exc)[:1200]}, 2)


if __name__ == "__main__":
    sys.exit(main())