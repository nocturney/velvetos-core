#!/usr/bin/env python3
"""Batch-capable, fail-closed entrypoint for Office v2 durable GitHub link intake.

Offline by default. Each URL gets a file-backed receipt and a triage state.
Existing registry entries are never changed; new links use the existing
single-repo registrar. Opt-in --metadata performs bounded GitHub API reads.
No install, promotion, scheduled workflow, or production authority.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import vf_office_v2_link_intake as core

ROOT = Path(__file__).resolve().parents[1]
BATCH_SCHEMA = "velvetos.office-v2.phase2-link-intake-batch.v1"


class MetadataUnavailable(ValueError):
    """The source cannot be verified; never silently treat it as public."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise MetadataUnavailable("GitHub API redirect requires manual alias review")


def fetch_metadata(key: tuple[str, str]) -> dict:
    """Explicit opt-in only. Public GitHub metadata, with no credentials."""
    owner, repo = key
    url = f"https://api.github.com/repos/{owner}/{repo}"
    req = urllib.request.Request(
        url, headers={"Accept": "application/vnd.github+json",
                      "User-Agent": "VelvetOS-OfficeV2-link-intake/1"})
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=5) as response:
            if response.geturl() != url:
                raise MetadataUnavailable("Unexpected metadata endpoint")
            raw = response.read(65537)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise MetadataUnavailable(f"GitHub metadata unavailable: {type(exc).__name__}: {exc}") from exc
    if len(raw) > 65536:
        raise MetadataUnavailable("Metadata response exceeds 64 KiB limit")
    try:
        obj = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise MetadataUnavailable("Invalid GitHub metadata JSON") from exc
    if not isinstance(obj, dict) or not isinstance(obj.get("full_name"), str):
        raise MetadataUnavailable("Missing repository identity in metadata")
    if obj["full_name"].casefold() != f"{owner}/{repo}".casefold():
        raise MetadataUnavailable("Repository alias/redirect needs explicit source reconciliation")
    if obj.get("private") is not False:
        raise MetadataUnavailable("Repository is private or visibility is unverifiable")
    return {"full_name": obj["full_name"], "archived": obj.get("archived"),
            "default_branch": obj.get("default_branch"), "private": False}


def inputs_from_file(path: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-8-sig")
    if raw.lstrip().startswith("["):
        value = json.loads(raw)
        if not isinstance(value, list):
            raise ValueError("JSON input must be a list")
        result = []
        for item in value:
            if isinstance(item, str):
                result.append({"url": item, "alias": ""})
            elif isinstance(item, dict) and isinstance(item.get("url"), str) and (
                    not item.get("alias") or isinstance(item["alias"], str)):
                result.append({"url": item["url"], "alias": item.get("alias", "")})
            else:
                raise ValueError("JSON list items must be URLs or {url, alias} objects")
        return result
    return [{"url": line.strip(), "alias": ""} for line in raw.splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def duplicate_ids(items: list[dict], key: tuple[str, str], alias: str = "") -> list[str]:
    """Match origin URLs plus explicit names/IDs, never a substring guess."""
    hits = set(core.find_duplicates(items, key))
    canonical = f"{key[0]}/{key[1]}".casefold()
    for entry in items:
        fields = (entry.get("candidate_id"), entry.get("source_item_id"), entry.get("name"))
        names = {v.strip().casefold() for v in fields if isinstance(v, str)}
        if canonical in names or (alias and alias.strip().casefold() in names):
            hits.add(entry["candidate_id"])
    return sorted(hits)


def _base(url: str, registry_path: Path) -> dict:
    return {
        "schema": core.RECEIPT_SCHEMA,
        "received_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "input_url": url,
        "registry_ref": str(registry_path),
        "network_used": False,
        "authority_granted": False,
        "candidate_ids": [],
    }


def _triage(receipt: dict) -> dict:
    return {
        "normalized_url": receipt.get("normalized_url"),
        "candidate_ids": receipt.get("candidate_ids", []),
        "state": receipt["status"],
        "source_sync": receipt.get("source_sync", "NEEDS_SYNC"),
        "next_action": receipt.get("next_action", ""),
    }


def process_one(url: str, *, alias: str = "", registry_path: Path = core.REGISTRY,
                receipt_dir: Path | None = core.RECEIPT_DIR,
                dry_run: bool = False, metadata: bool = False,
                metadata_reader=None) -> dict:
    """Produce one durable triage receipt for any input, including access failures."""
    key = core.parse_repo(url)
    r = _base(url, registry_path)
    if alias:
        r["alias"] = alias
    if key is None or key in core.SELF_REPOS:
        r.update(status="INVALID_INPUT", triage_state="INVALID_INPUT",
                 source_sync="NEEDS_SYNC",
                 next_action="Supply a GitHub repository URL, not an issue or another host.")
    else:
        r["normalized_url"] = core.canonical_url(*key)
        try:
            items = core.load_registry(registry_path)[0]["items"]
            duplicates = duplicate_ids(items, key, alias)
            if duplicates:
                r.update(status="DUPLICATE", triage_state="ALREADY_TRACKED",
                         candidate_ids=duplicates, source_sync="NOT_CHECKED_OFFLINE",
                         next_action="Use existing candidate ID(s); no second candidate was added.")
            else:
                if metadata:
                    r["network_used"] = metadata_reader is None
                    info = (metadata_reader or fetch_metadata)(key)
                    if not isinstance(info, dict) or info.get("private") is not False or (
                            str(info.get("full_name", "")).casefold()
                            != f"{key[0]}/{key[1]}".casefold()):
                        raise MetadataUnavailable("Metadata does not prove this exact public repository")
                    r["metadata"] = info
                    r["source_sync"] = "SYNCED"
                else:
                    r["source_sync"] = "NEEDS_SYNC"
                    r["access_state"] = "UNVERIFIED_OFFLINE"
                registered = core.intake(url, registry_path=registry_path, receipt_dir=None,
                                         dry_run=dry_run)
                r.update({k: v for k, v in registered.items()
                          if k in ("status", "candidate_ids", "candidate_count_before",
                                   "candidate_count_after", "next_action", "error")})
                r["triage_state"] = ("NEEDS_SOURCE_REVIEW" if r["status"] == "REGISTERED"
                                     else r["status"])
        except (MetadataUnavailable, OSError, ValueError, KeyError, TypeError) as exc:
            r.update(status="NEEDS_SYNC", triage_state="NEEDS_SYNC",
                     source_sync="NEEDS_SYNC", access_state="INACCESSIBLE_OR_PRIVATE_OR_UNVERIFIED",
                     error=f"{type(exc).__name__}: {exc}",
                     next_action="Source/registry not confirmed; verify access and re-run intake; keep this receipt.")
            r.pop("metadata", None)
    try:
        receipt = core._emit(r, receipt_dir, key, dry_run)
    except OSError as exc:
        receipt = dict(r, status="NEEDS_SYNC", triage_state="NEEDS_SYNC",
                       source_sync="NEEDS_SYNC", receipt_persisted=False,
                       error=f"Receipt persistence failed: {type(exc).__name__}: {exc}",
                       next_action="Save this JSON output externally and repair receipt storage before retrying.")
    return {"triage": _triage(receipt), "receipt": receipt}


def coverage_problems(inputs: list[dict], outputs: list[dict], registry_path: Path,
                      *, dry_run: bool = False) -> list[str]:
    """Independent batch postcondition: an incoming URL may not be dropped."""
    problems: list[str] = []
    if len(inputs) != len(outputs):
        problems.append(f"lost intake results: {len(inputs)} inputs vs {len(outputs)} outputs")
    try:
        items = core.load_registry(registry_path)[0]["items"]
    except (OSError, ValueError, KeyError, TypeError):
        items = []
    by_id = {i["candidate_id"]: i for i in items}
    for n, inp in enumerate(inputs):
        if n >= len(outputs):
            break
        r = outputs[n].get("receipt", {})
        key = core.parse_repo(inp["url"])
        if r.get("input_url") != inp["url"]:
            problems.append(f"input {n}: URL mismatch")
        if key and key not in core.SELF_REPOS and r.get("normalized_url") != core.canonical_url(*key):
            problems.append(f"input {n}: missing normalized URL")
        if r.get("status") not in {"REGISTERED", "DUPLICATE", "NEEDS_SYNC", "INVALID_INPUT"}:
            problems.append(f"input {n}: missing triage status")
        if not r.get("next_action"):
            problems.append(f"input {n}: missing next action")
        if not dry_run and r.get("receipt_persisted") is False:
            problems.append(f"input {n}: receipt could not be persisted")
        if not dry_run and not r.get("receipt_path"):
            problems.append(f"input {n}: durable receipt missing")
        if not dry_run and r.get("receipt_path"):
            path = Path(r["receipt_path"])
            if not path.is_absolute():
                path = ROOT / path
            if not path.is_file():
                problems.append(f"input {n}: receipt file absent")
        if r.get("status") in {"REGISTERED", "DUPLICATE"}:
            ids = r.get("candidate_ids", [])
            if not ids:
                problems.append(f"input {n}: accepted URL without candidate identity")
            elif not dry_run and any(cid not in by_id for cid in ids):
                problems.append(f"input {n}: candidate missing from canonical registry")
            if r["status"] == "REGISTERED" and not dry_run and (
                    not key or not any(core.canonical_url(*key) in by_id[cid].get("evidence_refs", [])
                                       for cid in ids if cid in by_id)):
                problems.append(f"input {n}: registered URL absent from canonical registry")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("urls", nargs="*", help="one or more GitHub repository URLs")
    ap.add_argument("--file", type=Path, help="UTF-8 newline list or JSON list of URLs/{url, alias}")
    ap.add_argument("--alias", default="", help="known candidate ID/name alias for ONE incoming URL")
    ap.add_argument("--metadata", action="store_true", help="opt in to bounded GitHub API metadata GET")
    ap.add_argument("--registry", type=Path, default=core.REGISTRY)
    ap.add_argument("--receipt-dir", type=Path, default=core.RECEIPT_DIR)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    try:
        inputs = [{"url": u, "alias": ""} for u in args.urls]
        if args.file:
            inputs += inputs_from_file(args.file)
        if not inputs or (args.alias and len(inputs) != 1):
            raise ValueError("Provide URLs; --alias is allowed with one URL only")
        if args.alias:
            inputs[0]["alias"] = args.alias
    except (ValueError, OSError, UnicodeError) as exc:
        print(json.dumps({"schema": BATCH_SCHEMA, "status": "NEEDS_SYNC",
                          "error": str(exc), "next_action": "Fix the input list and retry."}))
        return 1
    registry = args.registry.resolve()
    receipt_dir = args.receipt_dir.resolve()
    outputs = [process_one(i["url"], alias=i["alias"], registry_path=registry,
                           receipt_dir=receipt_dir, dry_run=args.dry_run,
                           metadata=args.metadata) for i in inputs]
    errors = coverage_problems(inputs, outputs, registry, dry_run=args.dry_run)
    result = {"schema": BATCH_SCHEMA, "input_count": len(inputs),
              "output_count": len(outputs), "results": outputs,
              "coverage": "PASS" if not errors else "FAIL", "coverage_errors": errors}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors and all(
        x["receipt"]["status"] in {"REGISTERED", "DUPLICATE"} for x in outputs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
