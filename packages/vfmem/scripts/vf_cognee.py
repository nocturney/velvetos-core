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


def runtime_root(cfg: dict[str, Any]) -> Path:
    override = os.environ.get("VFMEM_COGNEE_ROOT")
    return Path(override).expanduser() if override else Path(cfg["runtimeRoot"]).expanduser()


def apply_runtime_env(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
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


def installed_version() -> str | None:
    try:
        return importlib.metadata.version("cognee")
    except importlib.metadata.PackageNotFoundError:
        return None


def source_manifest(cfg: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    limit = int(cfg["sync"]["maxSourceBytes"])
    h = hashlib.sha256()
    for rel in cfg["sync"]["sources"]:
        path = (ROOT / rel).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
            raise RuntimeError(f"missing canonical memory source: {rel}")
        size = path.stat().st_size
        if size > limit:
            raise RuntimeError(f"source exceeds configured size cap: {rel}")
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        rows.append({"path": rel, "sha256": digest, "bytes": size})
        h.update(rel.encode("utf-8") + b"\0" + digest.encode("ascii") + b"\n")
    return h.hexdigest(), rows


def state_path(root: Path) -> Path:
    return root / "state.json"


def read_state(root: Path) -> dict[str, Any] | None:
    path = state_path(root)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, body: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


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
    if current and current.get("sourceDigest") == digest and current.get("dataset") == dataset:
        return {"status": "CURRENT", "dataset": dataset, "sources": sources}

    apply_runtime_env(root)
    import cognee

    progress_path = root / f"sync-{digest[:16]}.json"
    progress = {"dataset": dataset, "completed": []}
    if progress_path.is_file():
        progress = json.loads(progress_path.read_text(encoding="utf-8"))
    completed = set(progress.get("completed", []))

    for row in sources:
        rel = row["path"]
        if rel in completed:
            continue
        text = (ROOT / rel).read_text(encoding="utf-8")
        payload = (
            f"VELVETOS_CANONICAL_SOURCE: {rel}\n"
            "COGNEE_ROLE: derived context only; verify canonical source before action.\n\n"
            + text
        )
        await cognee.remember(
            payload,
            dataset_name=dataset,
            self_improvement=False,
            extractor="gliner_demo",
        )
        completed.add(rel)
        atomic_json(progress_path, {"dataset": dataset, "completed": sorted(completed)})

    state = {
        "schema": "vf.cognee.state.v1",
        "dataset": dataset,
        "sourceDigest": digest,
        "sources": sources,
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
    digest, _ = source_manifest(cfg)
    if state.get("sourceDigest") != digest:
        raise RuntimeError("Cognee index is stale; run sync before semantic recall")
    apply_runtime_env(root)
    import cognee

    rows = await cognee.recall(
        query,
        datasets=[state["dataset"]],
        top_k=top_k,
        only_context=True,
    )
    return {
        "status": "OK",
        "backend": "cognee-local-derived",
        "dataset": state["dataset"],
        "authority": cfg["authority"],
        "requiresCanonicalVerification": cfg["sync"]["requiresCanonicalVerification"],
        "results": [serialize_entry(x) for x in rows],
    }


async def smoke(cfg: dict[str, Any], root: Path) -> dict[str, Any]:
    apply_runtime_env(root / "smoke")
    import cognee

    token = "cobalt-sparrow-7319"
    dataset = f"vf_cognee_smoke_{cfg['pinnedVersion'].replace('.', '_')}"
    await cognee.remember(
        f"VelvetOS synthetic smoke sentinel is {token}.",
        dataset_name=dataset,
        self_improvement=False,
        extractor="gliner_demo",
    )
    rows = await cognee.recall(
        "What is the VelvetOS synthetic smoke sentinel?",
        datasets=[dataset],
        top_k=5,
        only_context=True,
    )
    rendered = json.dumps([serialize_entry(x) for x in rows], ensure_ascii=False, default=str)
    if token not in rendered:
        raise RuntimeError("Cognee smoke recall missed synthetic sentinel")
    return {"status": "PASS", "version": installed_version(), "dataset": dataset}


def doctor(cfg: dict[str, Any], root: Path) -> dict[str, Any]:
    digest, sources = source_manifest(cfg)
    version = installed_version()
    root.mkdir(parents=True, exist_ok=True)
    probe = root / ".write-probe"
    probe.write_text("ok", encoding="utf-8")
    probe.unlink()
    return {
        "status": "PASS" if version == cfg["pinnedVersion"] else "BLOCKED",
        "installedVersion": version,
        "pinnedVersion": cfg["pinnedVersion"],
        "versionMatch": version == cfg["pinnedVersion"],
        "runtimeRoot": str(root),
        "sourceDigest": digest,
        "sources": sources,
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