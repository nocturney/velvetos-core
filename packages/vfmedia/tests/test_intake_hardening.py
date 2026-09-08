"""Focused hardening tests for vfmedia auto-intake failure modes."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "packages" / "vfmedia"
sys.path.insert(0, str(PACK))

from intake import backoff as backoff_mod  # noqa: E402
from intake import persist as persist_mod  # noqa: E402
from intake.drive import (  # noqa: E402
    DownloadUnverifiedError,
    DriveFile,
    ListingError,
    ListingProvider,
    MemoryFixtureProvider,
    content_fingerprint,
)
from intake import runner as R  # noqa: E402


def _base_catalog() -> dict:
    return {
        "name": "vfmedia-catalog",
        "title": "test",
        "oneCatalog": True,
        "updatedAt": "2026-09-08",
        "vaultRootId": "1Yg3Rj0hKWTa86EXjaeu-f7CQXswSRMCv",
        "locks": [],
        "items": [],
    }


class FakeMoveFailProvider(MemoryFixtureProvider):
    """Registers + downloads, then fails on move after durable register."""

    name = "fake-move-fail"

    def move_to_source(self, file_id: str) -> None:
        raise RuntimeError("simulated move failure")


class FakeMoveOkSaveTrapProvider(MemoryFixtureProvider):
    """Move succeeds; caller can simulate persist failure separately."""

    name = "fake-move-ok"


class HardeningTests(unittest.TestCase):
    def test_listing_size_alone_is_not_download_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            listing = Path(tmp) / "listing.json"
            listing.write_text(
                json.dumps(
                    {
                        "folderId": "1IG4zNTOuGgvPyhEbKQEKwjRjFD6BuUDJ",
                        "files": [
                            {
                                "id": "SIZE_ONLY_FILE",
                                "name": "meta-only.bin",
                                "mimeType": "image/jpeg",
                                "size": "99999",
                                "webViewLink": "https://drive.google.com/file/d/SIZE_ONLY_FILE/view",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            provider = ListingProvider(listing, move_mode="memory")
            page = provider.list_inbox_page(None, 10)
            self.assertEqual(len(page.files), 1)
            with self.assertRaises(DownloadUnverifiedError):
                provider.download_bytes(page.files[0])

    def test_register_persists_before_move_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            work = tmp_path / "vfmedia"
            (work / "fixtures").mkdir(parents=True)
            (work / "state").mkdir()
            (work / "data").mkdir()
            # copy real bytes fixture
            src = PACK / "fixtures" / "new-inbox-file.txt"
            local = work / "fixtures" / "new-inbox-file.txt"
            local.write_bytes(src.read_bytes())
            listing = work / "fixtures" / "inbox-listing.json"
            listing.write_text(
                json.dumps(
                    {
                        "files": [
                            {
                                "id": "PRE_MOVE_REG",
                                "name": "pre-move.txt",
                                "mimeType": "text/plain",
                                "size": str(local.stat().st_size),
                                "localPath": str(local),
                                "webViewLink": "https://drive.google.com/file/d/PRE_MOVE_REG/view",
                                "md5Checksum": "abc123",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            cat_path = work / "catalog.json"
            cat_path.write_text(json.dumps(_base_catalog(), indent=2), encoding="utf-8")

            old = (
                R.CATALOG,
                R.STATE_DIR,
                R.DATA_DIR,
                R.RUNNER_STATE,
                R.LOCK_PATH,
                R.PENDING_MOVES,
                R.EVENTS,
                R.BRIEF_SIGNAL,
                R.INBOX_QUEUE,
                R.RECOVERY_LOG,
            )
            R.CATALOG = cat_path
            R.STATE_DIR = work / "state"
            R.DATA_DIR = work / "data"
            R.RUNNER_STATE = R.STATE_DIR / "intake-runner.json"
            R.LOCK_PATH = R.STATE_DIR / "intake.lock"
            R.PENDING_MOVES = R.STATE_DIR / "pending-drive-actions.json"
            R.EVENTS = R.DATA_DIR / "intake-events.jsonl"
            R.BRIEF_SIGNAL = R.DATA_DIR / "intake-brief.json"
            R.RECOVERY_LOG = R.DATA_DIR / "intake-recovery.jsonl"
            R.INBOX_QUEUE = tmp_path / "inbox.json"
            R.write_json(R.INBOX_QUEUE, {"updatedAt": "2026-09-08", "buckets": {"production": []}})
            try:
                # Inject provider via process_file directly
                catalog, dig = persist_mod.load_json_with_digest(cat_path, _base_catalog())
                state = R.default_runner_state()
                state["catalogDigest"] = dig
                provider = FakeMoveFailProvider(listing)
                file = provider.list_inbox_page(None, 10).files[0]
                result = R.process_file(
                    provider,
                    catalog,
                    R.catalog_index(catalog),
                    state,
                    file,
                    register_only=False,
                    defer_verify_until_move_applied=False,
                )
                self.assertEqual(result, "failed")
                # Catalog must already contain registered row despite move failure
                saved = json.loads(cat_path.read_text(encoding="utf-8"))
                self.assertEqual(len(saved["items"]), 1)
                self.assertEqual(saved["items"][0]["intake"]["phase"], "registered")
                self.assertEqual(saved["items"][0]["status"], "inbox")
                events = R.EVENTS.read_text(encoding="utf-8")
                self.assertIn("media.intake.registered", events)
            finally:
                (
                    R.CATALOG,
                    R.STATE_DIR,
                    R.DATA_DIR,
                    R.RUNNER_STATE,
                    R.LOCK_PATH,
                    R.PENDING_MOVES,
                    R.EVENTS,
                    R.BRIEF_SIGNAL,
                    R.INBOX_QUEUE,
                    R.RECOVERY_LOG,
                ) = old

    def test_recovery_after_move_when_parents_in_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            work = tmp_path / "vfmedia"
            (work / "fixtures").mkdir(parents=True)
            (work / "state").mkdir()
            (work / "data").mkdir()
            local = work / "fixtures" / "f.txt"
            local.write_text("hello", encoding="utf-8")
            listing = work / "fixtures" / "inbox-listing.json"
            listing.write_text(
                json.dumps(
                    {
                        "files": [
                            {
                                "id": "RECOVER_ME",
                                "name": "recover.txt",
                                "mimeType": "text/plain",
                                "localPath": str(local),
                                "size": "5",
                                "webViewLink": "https://drive.google.com/file/d/RECOVER_ME/view",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            cat = _base_catalog()
            cat["items"] = [
                {
                    "id": "media-RECOVER_ME",
                    "sourceFile": {
                        "id": "RECOVER_ME",
                        "url": "https://drive.google.com/file/d/RECOVER_ME/view",
                    },
                    "viewDescription": "טקסט",
                    "uploadedAt": "2026-09-08",
                    "productLink": None,
                    "status": "inbox",
                    "assignee": "ops-intake",
                    "derivativeIds": [],
                    "sourceLinks": [],
                    "versionApproval": {"state": "none"},
                    "intake": {
                        "phase": "registered",
                        "registeredAt": "2026-09-08T00:00:00Z",
                        "moveStartedAt": "2026-09-08T00:00:01Z",
                        "downloadBytes": 5,
                    },
                    "visualReview": {"state": "none"},
                }
            ]
            cat_path = work / "catalog.json"
            cat_path.write_text(json.dumps(cat, indent=2), encoding="utf-8")

            old = (
                R.CATALOG,
                R.STATE_DIR,
                R.DATA_DIR,
                R.RUNNER_STATE,
                R.LOCK_PATH,
                R.PENDING_MOVES,
                R.EVENTS,
                R.BRIEF_SIGNAL,
                R.INBOX_QUEUE,
                R.RECOVERY_LOG,
            )
            R.CATALOG = cat_path
            R.STATE_DIR = work / "state"
            R.DATA_DIR = work / "data"
            R.RUNNER_STATE = R.STATE_DIR / "intake-runner.json"
            R.LOCK_PATH = R.STATE_DIR / "intake.lock"
            R.PENDING_MOVES = R.STATE_DIR / "pending-drive-actions.json"
            R.EVENTS = R.DATA_DIR / "intake-events.jsonl"
            R.BRIEF_SIGNAL = R.DATA_DIR / "intake-brief.json"
            R.RECOVERY_LOG = R.DATA_DIR / "intake-recovery.jsonl"
            R.INBOX_QUEUE = tmp_path / "inbox.json"
            R.write_json(R.INBOX_QUEUE, {"updatedAt": "2026-09-08", "buckets": {"production": []}})
            R.write_json(
                R.PENDING_MOVES,
                {
                    "actions": [
                        {"fileId": "RECOVER_ME", "status": "move_done_unconfirmed", "op": "move"}
                    ]
                },
            )
            try:
                provider = FakeMoveOkSaveTrapProvider(listing)
                # Simulate Drive already in source
                provider._moved.add("RECOVER_ME")
                provider._parents["RECOVER_ME"] = ["1M0WY3iIKYOlqMPcBx5xctx8sr8xidnY6"]
                catalog, dig = persist_mod.load_json_with_digest(cat_path, cat)
                state = R.default_runner_state()
                state["catalogDigest"] = dig
                n = R.recover_after_move(provider, catalog, R.catalog_index(catalog), state)
                self.assertEqual(n, 1)
                saved = json.loads(cat_path.read_text(encoding="utf-8"))
                self.assertEqual(saved["items"][0]["intake"]["phase"], "verified")
                self.assertEqual(saved["items"][0]["status"], "source")
            finally:
                (
                    R.CATALOG,
                    R.STATE_DIR,
                    R.DATA_DIR,
                    R.RUNNER_STATE,
                    R.LOCK_PATH,
                    R.PENDING_MOVES,
                    R.EVENTS,
                    R.BRIEF_SIGNAL,
                    R.INBOX_QUEUE,
                    R.RECOVERY_LOG,
                ) = old

    def test_content_change_does_not_inherit_approval(self):
        item = {
            "id": "media-X",
            "status": "source",
            "versionApproval": {"state": "approved", "approvedBy": "lead", "approvedAt": "2026-09-01"},
            "visualReview": {"state": "done", "reviewedAt": "2026-09-01"},
            "intake": {
                "phase": "verified",
                "verifiedAt": "2026-09-01",
                "contentFingerprint": "md5:old",
            },
        }
        file = DriveFile(
            id="X",
            name="x.jpg",
            mimeType="image/jpeg",
            md5Checksum="newhash",
            headRevisionId="rev2",
        )
        R.apply_content_change(item, file, "md5:newhash")
        self.assertEqual(item["versionApproval"]["state"], "none")
        self.assertEqual(item["visualReview"]["state"], "none")
        self.assertEqual(item["status"], "inbox")
        self.assertEqual(item["intake"]["phase"], "registered")
        self.assertIsNone(item["intake"]["verifiedAt"])

    def test_backoff_never_permanent_stop(self):
        row = None
        for i in range(20):
            row = backoff_mod.record_failure(row, f"err-{i}")
            self.assertFalse(row.get("permanentStop"))
            self.assertIn("nextAfter", row)
        # attempt 20 still uses last interval
        self.assertEqual(row["backoffSeconds"], backoff_mod.BACKOFF_SECONDS[-1])
        # Immediately after failure, not ready
        self.assertFalse(backoff_mod.ready_for_retry(row))
        # Far future ready
        from datetime import datetime, timedelta, timezone

        future = datetime.now(timezone.utc) + timedelta(days=1)
        self.assertTrue(backoff_mod.ready_for_retry(row, now=future))

    def test_unknown_page_token_raises_listing_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            listing = Path(tmp) / "l.json"
            listing.write_text(
                json.dumps({"files": [], "pageToken": None, "nextPageToken": None}),
                encoding="utf-8",
            )
            provider = ListingProvider(listing, move_mode="memory")
            with self.assertRaises(ListingError):
                provider.list_inbox_page("bogus-token", 10)

    def test_catalog_conflict_merge_keeps_peer_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.json"
            base = _base_catalog()
            base["items"] = [
                {
                    "id": "media-A",
                    "sourceFile": {"id": "A", "url": "https://drive.google.com/file/d/A/view"},
                }
            ]
            dig = persist_mod.atomic_write_json(path, base)
            # Peer writer adds B
            peer = json.loads(path.read_text(encoding="utf-8"))
            peer["items"].append(
                {
                    "id": "media-B",
                    "sourceFile": {"id": "B", "url": "https://drive.google.com/file/d/B/view"},
                }
            )
            persist_mod.atomic_write_json(path, peer)
            # Our stale write with only A+C should merge B
            ours = _base_catalog()
            ours["items"] = [
                {
                    "id": "media-A",
                    "sourceFile": {"id": "A", "url": "https://drive.google.com/file/d/A/view"},
                    "note": "ours",
                },
                {
                    "id": "media-C",
                    "sourceFile": {"id": "C", "url": "https://drive.google.com/file/d/C/view"},
                },
            ]
            persist_mod.save_catalog_conflict_aware(path, ours, expected_digest=dig)
            final = json.loads(path.read_text(encoding="utf-8"))
            ids = {(it.get("sourceFile") or {}).get("id") for it in final["items"]}
            self.assertEqual(ids, {"A", "B", "C"})

    def test_fingerprint_prefers_checksum(self):
        f = DriveFile(id="1", name="a", mimeType="image/jpeg", md5Checksum="deadbeef", size=10)
        self.assertEqual(content_fingerprint(f), "md5:deadbeef")
        self.assertEqual(content_fingerprint(f, b"abc"), "md5:deadbeef")


if __name__ == "__main__":
    unittest.main()
