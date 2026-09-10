#!/usr/bin/env python3
"""Contract + unit tests for Publish Bridge handoff / recovery / publication gates."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import vf_publish_bridge as bridge  # noqa: E402
import vf_publish_handoff as handoff  # noqa: E402


class PublishHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="vf-handoff-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        # Isolate publication / handoff writes inside tmp.
        self.pubs = self.tmp / "publications"
        self.mans = self.tmp / "handoff"
        self.pubs.mkdir()
        self.mans.mkdir()
        self._patchers = [
            mock.patch.object(handoff, "PUBLICATIONS_DIR", self.pubs),
            mock.patch.object(handoff, "HANDOFF_DIR", self.mans),
            mock.patch.object(handoff, "ROOT", self.tmp),
        ]
        for p in self._patchers:
            p.start()
            self.addCleanup(p.stop)

        # Tiny RGB PNG via Pillow
        from PIL import Image

        self.png = self.tmp / "approved-export.png"
        Image.new("RGB", (1080, 1920), color=(200, 80, 120)).save(self.png)

    def test_normalize_and_prepare_approved_local_export(self) -> None:
        cfg = bridge.load_config()
        with tempfile.TemporaryDirectory() as td:
            normalized, content_type, details = bridge.normalize(self.png, cfg, Path(td))
            self.assertEqual(content_type, "image/jpeg")
            self.assertEqual(details["width"], 1080)
            self.assertEqual(details["height"], 1920)
            data = normalized.read_bytes()
            self.assertTrue(data.startswith(b"\xff\xd8\xff"))
            self.assertIn(b"\xff\xc0", data)  # baseline SOF0
            self.assertNotIn(b"\xff\xc2", data)  # not progressive

    def test_no_binary_written_to_main_paths(self) -> None:
        cfg = bridge.load_config()
        self.assertEqual(cfg["branch"], "publish-bridge")
        self.assertNotEqual(cfg["branch"], "main")
        self.assertTrue(str(cfg["pathPrefix"]).startswith("publish-bridge/"))

    def test_unapproved_assets_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            handoff.register_local_export(
                correlation="G004",
                file_path=self.png,
                approval_ref="packages/vfgrowth/preflight/G004.md",
                source_ref="canva:DAHUaUo3bAk",
                frame_index=1,
                public_release_approved=False,
            )

    def test_historical_g004_job_assets_rejected(self) -> None:
        bad = self.tmp / "packages" / "vfcanva" / "jobs" / "g004-stories-fix" / "story-1.png"
        bad.parent.mkdir(parents=True)
        shutil.copy(self.png, bad)
        with self.assertRaises(ValueError):
            handoff.reject_source_path(str(bad))

    def test_canva_thumbnail_urls_rejected(self) -> None:
        with self.assertRaises(ValueError):
            handoff.reject_source_path("https://example.com/design/thumbnail/xyz.png")

    def test_private_drive_urls_rejected(self) -> None:
        with self.assertRaises(ValueError):
            handoff.reject_source_path("https://drive.google.com/file/d/abc/view")

    def test_bridge_url_shape_and_fetch_contract(self) -> None:
        cfg = bridge.load_config()
        url = (
            f"{cfg['publicBaseUrl'].rstrip('/')}/2026-09-10/G004/"
            f"{'a' * 20}.jpg"
        )
        self.assertTrue(url.startswith("https://raw.githubusercontent.com/"))
        self.assertIn("/publish-bridge/publish-bridge/assets/", url)

        # Fake successful fetch verification against local bytes.
        with tempfile.TemporaryDirectory() as td:
            normalized, content_type, details = bridge.normalize(self.png, cfg, Path(td))
            digest = bridge.sha256_file(normalized)
            body = normalized.read_bytes()

            class Resp:
                def __enter__(self):
                    return self

                def __exit__(self, *a):
                    return False

                def read(self):
                    return body

                @property
                def headers(self):
                    class H:
                        def get_content_type(self_inner):
                            return "image/jpeg"

                    return H()

            with mock.patch("urllib.request.urlopen", return_value=Resp()):
                out = bridge.verify_public_url(url, digest, content_type, len(body), attempts=1)
            self.assertTrue(out["ok"])

    def test_rerun_does_not_duplicate_publication_receipt(self) -> None:
        handoff.record_publish_receipt(
            "G004",
            {"ok": True, "media_id": "111", "container_id": "c1", "frameIndex": 1},
        )
        again = handoff.record_publish_receipt(
            "G004",
            {"ok": True, "media_id": "111", "container_id": "c1", "frameIndex": 1},
        )
        self.assertTrue(again.get("idempotent"))
        doc = handoff.load_publication("G004")
        self.assertEqual(len(doc["receipts"]), 1)

    def test_published_verified_requires_receipt_and_live(self) -> None:
        doc = handoff.load_publication("G004")
        with self.assertRaises(ValueError):
            handoff.set_state(doc, "published_verified")
        handoff.record_publish_receipt("G004", {"ok": True, "media_id": "222"})
        with self.assertRaises(ValueError):
            # still no liveVerification
            doc2 = handoff.load_publication("G004")
            handoff.set_state(doc2, "published_verified")
        out = handoff.record_live_verification(
            "G004",
            {"media_id": "222", "verified": True, "product": "STORY"},
        )
        self.assertEqual(out["state"], "published_verified")

    def test_missing_bridge_with_local_export_triggers_recovery_not_terminal_block(self) -> None:
        # recover without --stage should land approved_export_local / prepare, not terminal transport block.
        out = handoff.recover_and_stage_frame(
            correlation="G004",
            file_path=self.png,
            approval_ref="packages/vfgrowth/preflight/G004.md",
            source_ref="canva:DAHUaUo3bAk",
            frame_index=1,
            public_release_approved=True,
            do_stage=False,
        )
        self.assertTrue(out["ok"])
        self.assertNotEqual(out.get("blocker"), "blocked_publish_transport")
        doc = handoff.load_publication("G004")
        self.assertEqual(doc["state"], "approved_export_local")

    def test_frame4_whatsapp_fails_cta_validation(self) -> None:
        with self.assertRaises(ValueError):
            handoff.validate_public_cta_text(
                "שלחו וואטסאפ 050-2517000\nאיסוף שדרות", frame_role="cta"
            )

    def test_instagram_only_cta_passes(self) -> None:
        handoff.validate_public_cta_text(
            "שלחו הודעה כאן באינסטגרם\nאיסוף שדרות", frame_role="cta"
        )


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PublishHandoffTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
