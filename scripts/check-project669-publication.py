#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import vf_project669_publication as p669


class Project669PublicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ws = self.root / ".vf-private" / "run"
        self.ws.mkdir(parents=True)

    def image(self, rel: str, value: tuple[int, int, int]) -> dict:
        path = self.ws / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (40, 50), value).save(path)
        return {"path": rel, "sha256": p669.digest(path)}

    def data(self, rel: str, body: dict) -> dict:
        path = self.ws / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(body), encoding="utf-8")
        return {"path": rel, "sha256": p669.digest(path)}

    def fixture(self):
        src = self.image("sources/source-01.png", (10, 20, 30))
        ingest = self.data("sources/source-01.ingest.json", {"exact_bytes_copied": True})
        candidate = self.image("candidate.png", (40, 50, 60))
        cand_mobile = self.image("qa/candidate-mobile.png", (40, 50, 60))
        product_proof = self.data("product-proof.json", {
            "publication_authorized": False,
            "source_pixel_integrity": "PASS",
        })
        master = self.image("creative-master/master.png", (40, 50, 60))
        materialization = self.data("creative-master/materialization.json", {"exact_bytes_copied": True})
        master_review = self.data("master-review.json", {
            "candidate_sha256": candidate["sha256"],
            "source_sha256": [src["sha256"]],
            "checks": {k: {"verdict": "PASS", "notes": "fixture"} for k in p669.FALLBACK_MASTER_CHECKS},
        })
        master_evidence = self.data("master-evidence.json", {
            "route": "SOURCE_COMPOSITE",
            "candidate": candidate,
            "reviews": {"fallback": master_review},
        })
        final = self.image("final.png", (70, 80, 90))
        mobile = self.image("qa/final-mobile.png", (70, 80, 90))
        final_spec = self.data("final-spec.json", {"mode": "EDITORIAL"})
        final_proof = self.data("final-proof.json", {
            "copy_lexical_checks": "PASS",
            "final": final,
            "mobile": mobile,
            "compositor_input": master,
        })
        review = self.data("final-review.json", {
            "reviewer_kind": "ASSISTANT_VISION",
            "opened_full_size": True,
            "opened_mobile": True,
            "final_sha256": final["sha256"],
            "mobile_sha256": mobile["sha256"],
            "master_sha256": master["sha256"],
            "source_sha256": [src["sha256"]],
            "checks": {k: {"verdict": "PASS", "notes": "fixture"} for k in p669.FINAL_CHECKS},
        })
        release = self.data("release.json", {
            "scope": "REVIEW_ARTIFACT_ONLY",
            "review_delivery_authorized": True,
            "publication_authorized": False,
            "final_qa": "EXACT_FILE_REVIEWER_ATTESTED_PASS",
            "source_ingest": "PASS",
            "route": "SOURCE_COMPOSITE",
            "artifact": final,
            "review": review,
        })
        self.data("candidate-spec.json", {"mode": "SOURCE_COMPOSITE"})
        run = {
            "schema": 6,
            "revision": "6.6.9",
            "bundle_id": p669.PROJECT_BUNDLE_ID,
            "fixture": False,
            "sources": [{"file": src, "ingest": ingest}],
            "candidate": {
                "route": "SOURCE_COMPOSITE", "file": candidate, "mobile": cand_mobile,
                "proof": product_proof, "spec": {"path": "candidate-spec.json", "sha256": p669.digest(self.ws/"candidate-spec.json")},
            },
            "master": {
                "route": "SOURCE_COMPOSITE", "file": master,
                "materialization": materialization, "evidence": master_evidence,
            },
            "final": {"file": final, "mobile": mobile, "proof": final_proof, "spec": final_spec},
            "release": release,
        }
        run_path = self.ws / ".vf-run.json"
        run_path.write_text(json.dumps(run), encoding="utf-8")
        caption = self.ws / "caption.txt"
        caption.write_text("fixture caption\n", encoding="utf-8")
        csha = p669.digest(caption)
        self.data("caption-receipt.json", {
            "text_sha256": csha, "visible_text_gate": "PASS", "lint": {"status": "pass"}
        })
        package = p669._package_digest(final["sha256"], csha)
        return run_path, final, package

    def test_valid_release(self):
        run_path, final, package = self.fixture()
        result = p669.validate(
            self.root, str(run_path.relative_to(self.root)), "TEST", "post", package,
            caption_ref=".vf-private/run/caption.txt",
            caption_receipt_ref=".vf-private/run/caption-receipt.json",
        )
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["projectFinalSha256"], final["sha256"])

    def test_tampered_final_fails(self):
        run_path, _, package = self.fixture()
        (self.ws / "final.png").write_bytes(b"tampered")
        result = p669.validate(
            self.root, str(run_path.relative_to(self.root)), "TEST", "post", package,
            caption_ref=".vf-private/run/caption.txt",
            caption_receipt_ref=".vf-private/run/caption-receipt.json",
        )
        self.assertFalse(result["ok"])

    def test_failed_identity_review_fails_closed(self):
        run_path, _, package = self.fixture()
        path = self.ws / "final-review.json"
        review = json.loads(path.read_text())
        review["checks"]["source_identity"]["verdict"] = "FAIL"
        path.write_text(json.dumps(review), encoding="utf-8")
        run = json.loads(run_path.read_text())
        release_path = self.ws / "release.json"
        release = json.loads(release_path.read_text())
        release["review"]["sha256"] = p669.digest(path)
        release_path.write_text(json.dumps(release), encoding="utf-8")
        run["release"]["sha256"] = p669.digest(release_path)
        run_path.write_text(json.dumps(run), encoding="utf-8")
        result = p669.validate(
            self.root, str(run_path.relative_to(self.root)), "TEST", "post", package,
            caption_ref=".vf-private/run/caption.txt",
            caption_receipt_ref=".vf-private/run/caption-receipt.json",
        )
        self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
