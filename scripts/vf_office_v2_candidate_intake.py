#!/usr/bin/env python3
"""Fail-closed OFFLINE intake preflight against the ONE Office v2 candidate registry.

No automatic candidate creation, API/model call, publication, runtime queue or authority.
The receipt's queue is a proposed human review list, not a job scheduler.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

SCHEMA = "velvetos.office-v2.repo-intake-receipt.v0"
REGISTRY_SCHEMA = "velvetos.office-v2.phase2-candidate-registry.v0"
IDENT = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,99}$")
SEGMENT = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,99}$")
MAX_ENTRIES = 500


class IntakeRejected(ValueError):
    pass


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(json_bytes(value)).hexdigest()


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalize_repo_url(value, *, evidence_link=False):
    if not isinstance(value, str) or len(value) > 1024 or any(ord(c) < 32 for c in value):
        raise IntakeRejected("INVALID_URL")
    try:
        u = urlsplit(value)
    except ValueError as exc:
        raise IntakeRejected("INVALID_URL") from exc
    if (u.scheme != "https" or u.netloc.lower() not in ("github.com", "www.github.com")
            or u.username is not None or u.password is not None or u.port is not None
            or u.query or u.fragment):
        raise IntakeRejected("UNSUPPORTED_OR_UNTRUSTED_URL")
    parts = u.path.strip("/").split("/")
    if len(parts) < 2 or (len(parts) > 2 and not evidence_link):
        raise IntakeRejected("REPOSITORY_ROOT_REQUIRED")
    if any("%" in p or not SEGMENT.fullmatch(p) for p in parts):
        raise IntakeRejected("INVALID_REPOSITORY_SEGMENT")
    if evidence_link and len(parts) > 2 and parts[2].lower() not in (
        "releases", "blob", "tree", "issues", "pull", "tags", "actions", "commit"
    ):
        raise IntakeRejected("UNRECOGNIZED_EVIDENCE_SUBRESOURCE")
    owner, repo = parts[:2]
    if repo.endswith(".git"):
        repo = repo[:-4]
    if not repo or repo in (".", "..") or owner in (".", ".."):
        raise IntakeRejected("INVALID_REPOSITORY_SEGMENT")
    return "https://github.com/" + owner.lower() + "/" + repo.lower()


def registry_urls(row):
    # Only explicit URL values. Freeform sentences, names and ID similarity
    # are not evidence that two repos are the same upstream project.
    values = [row.get(k) for k in ("repo_url", "source_url", "upstream_url")]
    for k in ("evidence_refs", "notes"):
        refs = row.get(k, [])
        if isinstance(refs, list):
            values.extend(x for x in refs if isinstance(x, str) and x.startswith("https://github.com/"))
    urls = set()
    for value in values:
        if isinstance(value, str):
            try:
                urls.add(normalize_repo_url(value, evidence_link=True))
            except IntakeRejected:
                pass
    return urls


def build(source, registry, source_sha256, registry_sha256):
    if not isinstance(source, dict) or source.get("schema") != "velvetos.office-v2.repo-link-intake.v0":
        raise IntakeRejected("SOURCE_SCHEMA_REQUIRED")
    if not isinstance(registry, dict) or registry.get("schema") != REGISTRY_SCHEMA:
        raise IntakeRejected("CANONICAL_REGISTRY_REQUIRED")
    items = source.get("items")
    if not isinstance(items, list) or not (1 <= len(items) <= MAX_ENTRIES):
        raise IntakeRejected("INVALID_SOURCE_SIZE")
    registry_items = registry.get("items")
    if not isinstance(registry_items, list):
        raise IntakeRejected("REGISTRY_ITEMS_REQUIRED")
    if registry.get("candidate_count") != len(registry_items):
        raise IntakeRejected("CANONICAL_REGISTRY_COUNT_DRIFT")
    registered = defaultdict(set)
    ids = set()
    for row in registry_items:
        if not isinstance(row, dict) or not isinstance(row.get("candidate_id"), str):
            raise IntakeRejected("INVALID_REGISTRY_ENTRY")
        key = row["candidate_id"]
        if key in ids:
            raise IntakeRejected("DUPLICATE_CANONICAL_CANDIDATE_ID")
        ids.add(key)
        for url in registry_urls(row):
            registered[url].add(key)

    provenance_ids = set()
    grouped = defaultdict(list)
    for index, item in enumerate(items):
        if not isinstance(item, dict) or set(item) != {"url", "origin_ref"}:
            raise IntakeRejected("INVALID_SOURCE_ROW")
        origin = item["origin_ref"]
        if not isinstance(origin, str) or not IDENT.fullmatch(origin) or origin in provenance_ids:
            raise IntakeRejected("INVALID_OR_DUPLICATE_PROVENANCE")
        provenance_ids.add(origin)
        url = normalize_repo_url(item["url"])
        grouped[url].append({"input_index": index, "origin_ref": origin, "submitted_url": item["url"]})

    records = []
    for url, aliases in sorted(grouped.items()):
        matches = sorted(registered.get(url, set()))
        state = ("BLOCKED_AMBIGUOUS_EXISTING_CANDIDATES" if len(matches) > 1
                 else "EXISTING_CANONICAL_CANDIDATE" if matches
                 else "TRIAGE_PENDING_NO_ADMISSION")
        records.append({"canonical_repo_url": url, "aliases": aliases,
                        "candidate_ids": matches, "review_state": state,
                        "runtime_authority": False, "auto_admission": False})
    receipt = {
        "schema": SCHEMA,
        "authority": "OFFLINE_REVIEW_ONLY",
        "registry_path": "docs/implementation/office-v2/phase2/candidate-registry-v0.json",
        "source_sha256": source_sha256,
        "registry_sha256": registry_sha256,
        "source_rows": len(items),
        "unique_repositories": len(records),
        "alias_rows": len(items) - len(records),
        "queue": records,
        "runtime_authority": False,
        "model_invocations": 0,
        "paid_api_calls": 0,
        "external_effects": "NONE",
    }
    receipt["receipt_sha256"] = digest(receipt)
    return receipt


def verify(source, registry, receipt, source_sha256, registry_sha256):
    if not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA:
        raise IntakeRejected("RECEIPT_SCHEMA_INVALID")
    sealed = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    if receipt.get("receipt_sha256") != digest(sealed):
        raise IntakeRejected("RECEIPT_TAMPERED")
    expected = build(source, registry, source_sha256, registry_sha256)
    if json_bytes(receipt) != json_bytes(expected):
        raise IntakeRejected("RECEIPT_STALE_OR_MISMATCHED")
    if sum(len(entry["aliases"]) for entry in receipt["queue"]) != receipt["source_rows"]:
        raise IntakeRejected("SILENT_SOURCE_LOSS")
    return {"status": "PASS", "source_rows": receipt["source_rows"],
            "unique_repositories": receipt["unique_repositories"], "receipt_sha256": receipt["receipt_sha256"]}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["build", "verify"])
    parser.add_argument("--source", required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    try:
        source, registry = read(args.source), read(args.registry)
        srch, regh = file_sha(args.source), file_sha(args.registry)
        if args.command == "build":
            result = build(source, registry, srch, regh)
            out = Path(args.receipt)
            if out.exists():
                raise IntakeRejected("RECEIPT_EXISTS_NO_OVERWRITE")
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("x", encoding="utf-8") as fh:
                json.dump(result, fh, ensure_ascii=False, sort_keys=True, indent=2)
                fh.write("\n")
            print(json.dumps({"status": "REVIEW_ONLY", "receipt_sha256": result["receipt_sha256"]}))
        else:
            print(json.dumps(verify(source, registry, read(args.receipt), srch, regh), sort_keys=True))
        return 0
    except (IntakeRejected, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())
