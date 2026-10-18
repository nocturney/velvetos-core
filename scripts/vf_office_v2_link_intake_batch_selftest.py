#!/usr/bin/env python3
"""Offline adversarial acceptance tests for #595 AC5/AC6 batch link intake."""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

import vf_office_v2_link_intake as core
import vf_office_v2_link_intake_batch as batch

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = core.REGISTRY


def require(test: bool, message: str) -> None:
    if not test:
        raise AssertionError(message)


def main() -> int:
    real_before = REGISTRY.read_bytes()
    with tempfile.TemporaryDirectory(prefix="vf595-intake-batch-") as tmp:
        root = Path(tmp)
        registry = root / "registry.json"
        receipt_dir = root / "receipts"
        shutil.copyfile(REGISTRY, registry)
        first = json.loads(registry.read_text(encoding="utf-8"))
        original_rows = first["items"]
        n0 = len(original_rows)

        # Any attempt to perform an implicit metadata fetch fails this test.
        original_fetch = batch.fetch_metadata
        def offline_guard(_key):
            raise AssertionError("network attempted without --metadata")
        batch.fetch_metadata = offline_guard
        try:
            new_url = "https://github.com/QA-INTAKE-595/New.Tool.git/tree/main"
            x = batch.process_one(new_url, registry_path=registry, receipt_dir=receipt_dir)
        finally:
            batch.fetch_metadata = original_fetch
        rx = x["receipt"]
        require(rx["status"] == "REGISTERED" and rx["network_used"] is False,
                "unregistered offline source must be admitted as DISCOVERED without network")
        require(rx["source_sync"] == "NEEDS_SYNC" and rx["triage_state"] == "NEEDS_SOURCE_REVIEW",
                "offline metadata uncertainty must be explicit")
        require(rx["normalized_url"] == "https://github.com/qa-intake-595/new.tool",
                "URL normalization failed")
        require(Path(rx["receipt_path"]).is_file(), "receipt not persisted")
        persisted = json.loads(Path(rx["receipt_path"]).read_text(encoding="utf-8"))
        require(persisted["input_url"] == new_url and persisted["next_action"],
                "triage receipt does not preserve original source/next action")
        changed = json.loads(registry.read_text(encoding="utf-8"))
        require(changed["items"][:n0] == original_rows and changed["candidate_count"] == n0 + 1,
                "historical entries mutated or candidate lost")
        created = changed["items"][-1]
        require(created["candidate_id"] in rx["candidate_ids"]
                and created["lifecycle_state"] == "DISCOVERED"
                and created["authority_role"] == "NONE"
                and created["runtime_verification"] == "NOT_RUN",
                "unregistered source was not routed with safe authority")
        require(not batch.coverage_problems([{"url": new_url}], [x], registry),
                "positive postcondition rejected a real stored intake")

        dup = batch.process_one("github.com/QA-INTAKE-595/NEW.Tool/", registry_path=registry,
                                receipt_dir=receipt_dir)
        require(dup["receipt"]["status"] == "DUPLICATE"
                and dup["receipt"]["candidate_ids"] == rx["candidate_ids"],
                "owner/repo canonical duplicate missed")
        alias = batch.process_one("https://github.com/qa-intake-595/unrelated",
                                  alias="live-gmail-connector", registry_path=registry,
                                  receipt_dir=receipt_dir)
        require(alias["receipt"]["status"] == "DUPLICATE"
                and "live-gmail-connector" in alias["receipt"]["candidate_ids"],
                "candidate ID alias duplicate missed")
        named = batch.process_one("https://github.com/qa-intake-595/another-unrelated",
                                  alias="Gmail Connector", registry_path=registry,
                                  receipt_dir=receipt_dir)
        require(named["receipt"]["status"] == "DUPLICATE"
                and "live-gmail-connector" in named["receipt"]["candidate_ids"],
                "candidate display alias duplicate missed")
        require(json.loads(registry.read_text(encoding="utf-8"))["candidate_count"] == n0 + 1,
                "duplicate/alias added an unwanted candidate")

        for invalid in ("https://gitlab.com/a/b", "https://github.com/one",
                        "https://github.com/nocturney/velvetos-core/issues/595"):
            r = batch.process_one(invalid, registry_path=registry, receipt_dir=receipt_dir)
            require(r["receipt"]["status"] == "INVALID_INPUT"
                    and Path(r["receipt"]["receipt_path"]).is_file(),
                    "invalid GitHub URL was not durably refused")

        denied = batch.process_one("https://github.com/qa-private-595/private-repo",
                                   registry_path=registry, receipt_dir=receipt_dir,
                                   metadata=True,
                                   metadata_reader=lambda key: {
                                       "full_name": "qa-private-595/private-repo", "private": True})
        require(denied["receipt"]["status"] == "NEEDS_SYNC"
                and denied["receipt"]["source_sync"] == "NEEDS_SYNC"
                and Path(denied["receipt"]["receipt_path"]).is_file(),
                "private repo did not produce durable NEEDS_SYNC")
        def inaccessible(_key):
            raise batch.MetadataUnavailable("HTTP 404 (private or absent)")
        denied_404 = batch.process_one("https://github.com/qa-private-595/unavailable",
                                       registry_path=registry, receipt_dir=receipt_dir,
                                       metadata=True, metadata_reader=inaccessible)
        require(denied_404["receipt"]["status"] == "NEEDS_SYNC"
                and "404" in denied_404["receipt"]["error"],
                "inaccessible repo was silently discarded")
        require(json.loads(registry.read_text(encoding="utf-8"))["candidate_count"] == n0 + 1,
                "unverified/private sources were incorrectly added")

        verified = batch.process_one("https://github.com/qa-public-595/available",
                                     registry_path=registry, receipt_dir=receipt_dir,
                                     metadata=True, metadata_reader=lambda key: {
                                         "full_name": "qa-public-595/available", "private": False,
                                         "archived": False})
        require(verified["receipt"]["status"] == "REGISTERED"
                and verified["receipt"]["source_sync"] == "SYNCED",
                "opt-in verified metadata could not register public repo")

        # Mutation 1: a credible unregistered input is dropped from output.
        two = [{"url": new_url}, {"url": "https://github.com/qa-public-595/available"}]
        outputs = [x, verified]
        require(not batch.coverage_problems(two, outputs, registry), "valid batch falsely flagged")
        require(any("lost intake results" in e for e in
                    batch.coverage_problems(two, outputs[:-1], registry)),
                "MUTATION: silently dropping an incoming URL escaped coverage")
        # Mutation 2: a false REGISTERED receipt with no actual registry record.
        fake = dict(verified["receipt"], input_url="https://github.com/qa-ghost-595/missing",
                    normalized_url="https://github.com/qa-ghost-595/missing",
                    candidate_ids=["candidate-does-not-exist"])
        require(any("candidate missing" in e for e in batch.coverage_problems(
            [{"url": fake["input_url"]}], [{"receipt": fake}], registry)),
            "MUTATION: forged registration with no canonical candidate escaped coverage")
        # Mutation 3: register succeeds, then candidate disappears from registry.
        saved = registry.read_bytes()
        mutated = json.loads(saved)
        mutated["items"] = [i for i in mutated["items"]
                            if i["candidate_id"] not in verified["receipt"]["candidate_ids"]]
        mutated["candidate_count"] = len(mutated["items"])
        registry.write_text(json.dumps(mutated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        require(batch.coverage_problems([{"url": verified["receipt"]["input_url"]}],
                                        [verified], registry),
                "MUTATION: deleted registered candidate escaped coverage")
        registry.write_bytes(saved)
        # Mutation 4: a receipt path points to a different input's durable file.
        wrong_receipt = dict(rx, receipt_path=dup["receipt"]["receipt_path"])
        require(any("receipt content mismatch" in e for e in batch.coverage_problems(
            [{"url": new_url}], [{"receipt": wrong_receipt}], registry)),
            "MUTATION: wrong durable receipt silently covered the incoming URL")

        lines = root / "links.txt"
        lines.write_text("# owner supplied\nhttps://github.com/qa-list-595/one\n"
                         "https://github.com/qa-list-595/two\n", encoding="utf-8")
        objs = root / "links.json"
        objs.write_text(json.dumps([{"url": "https://github.com/qa-list-595/three",
                                     "alias": "Gmail Connector"},
                                    "https://github.com/qa-list-595/four"]), encoding="utf-8")
        require(len(batch.inputs_from_file(lines)) == 2 and len(batch.inputs_from_file(objs)) == 2,
                "newline and JSON input lists not accepted")
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = batch.main(["--file", str(lines), "--registry", str(registry),
                               "--receipt-dir", str(receipt_dir)])
        run = json.loads(buffer.getvalue())
        require(code == 0 and run["input_count"] == run["output_count"] == 2
                and run["coverage"] == "PASS"
                and all(v["receipt"]["status"] == "REGISTERED" for v in run["results"]),
                "batch CLI did not preserve all two inputs")
        tail = json.loads(registry.read_text(encoding="utf-8"))
        require(tail["items"][:n0] == original_rows, "batch modified historical registry prefix")

    require(REGISTRY.read_bytes() == real_before, "sensor wrote to canonical registry")
    print("OK link-intake-batch offline=PASS alias=PASS duplicate=PASS invalid=PASS "
          "private-needs-sync=PASS list=PASS mutations=4/4 history=immutable authority=NONE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print("FAIL " + str(exc), file=sys.stderr)
        raise SystemExit(1)
