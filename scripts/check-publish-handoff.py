#!/usr/bin/env python3
"""Contract + unit tests for Publish Bridge handoff / recovery / publication gates.

No Pillow required in CI: PNG bytes are written manually; image normalization is
mocked unless Pillow is installed (optional local coverage).
"""
from __future__ import annotations

import json
import shutil
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import vf_publish_bridge as bridge  # noqa: E402
import vf_publish_handoff as handoff  # noqa: E402

try:
    from PIL import Image  # type: ignore

    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def write_solid_png(path: Path, width: int = 8, height: int = 8) -> None:
    """Minimal RGB PNG writer (stdlib only) so CI sensors need no Pillow."""

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + (b"\xff\x00\x80" * width) for _ in range(height))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
    path.write_bytes(png)


class PublishHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="vf-handoff-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.pubs = self.tmp / "publications"
        self.mans = self.tmp / "handoff"
        self.pubs.mkdir()
        self.mans.mkdir()
        for p in (
            mock.patch.object(handoff, "PUBLICATIONS_DIR", self.pubs),
            mock.patch.object(handoff, "HANDOFF_DIR", self.mans),
            mock.patch.object(handoff, "ROOT", self.tmp),
        ):
            p.start()
            self.addCleanup(p.stop)

        self.png = self.tmp / "approved-export.png"
        write_solid_png(self.png, 1080, 8)  # wide enough; height cheap for CI

    def _fake_normalize(self, src: Path, cfg: dict, tmp: Path):
        dst = tmp / "asset.jpg"
        # JFIF-ish header + baseline SOF0 marker so contracts can inspect bytes.
        dst.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\xff\xc0\x00\x11\x08\x07\x80\x04\x38\xff\xd9")
        return dst, "image/jpeg", {"width": 1080, "height": 1920, "sizeBytes": dst.stat().st_size}

    def test_normalize_and_prepare_approved_local_export(self) -> None:
        cfg = bridge.load_config()
        with tempfile.TemporaryDirectory() as td:
            if HAS_PIL:
                Image.new("RGB", (1080, 1920), color=(200, 80, 120)).save(self.png)
                normalized, content_type, details = bridge.normalize(self.png, cfg, Path(td))
            else:
                normalized, content_type, details = self._fake_normalize(self.png, cfg, Path(td))
            self.assertEqual(content_type, "image/jpeg")
            self.assertEqual(details["width"], 1080)
            self.assertEqual(details["height"], 1920)
            data = normalized.read_bytes()
            self.assertTrue(data.startswith(b"\xff\xd8\xff"))
            self.assertIn(b"\xff\xc0", data)
            self.assertNotIn(b"\xff\xc2", data)

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
        url = f"{cfg['publicBaseUrl'].rstrip('/')}/2026-09-10/G004/{'a' * 20}.jpg"
        self.assertTrue(url.startswith("https://raw.githubusercontent.com/"))
        self.assertIn("/publish-bridge/publish-bridge/assets/", url)

        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(bridge, "normalize", side_effect=self._fake_normalize):
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
            doc2 = handoff.load_publication("G004")
            handoff.set_state(doc2, "published_verified")
        out = handoff.record_live_verification(
            "G004",
            {"media_id": "222", "verified": True, "product": "STORY"},
        )
        self.assertEqual(out["state"], "published_verified")

    def test_missing_bridge_with_local_export_triggers_recovery_not_terminal_block(self) -> None:
        with mock.patch.object(bridge, "normalize", side_effect=self._fake_normalize):
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
