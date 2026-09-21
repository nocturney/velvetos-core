#!/usr/bin/env python3
"""Create a reviewed transport JPEG + receipt for a VF Project 6.6.9 final.

The source project review remains authoritative for creative/product QA. This
script performs only canonical transport normalization and measurable pixel
comparison. A receipt is emitted only when the caller explicitly attests that
the normalized transport artifact was visually opened and remains equivalent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageChops
from vf_publish_bridge import load_config, normalize_image
from vf_project669_publication import digest


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--receipt", required=True)
    p.add_argument("--reviewer-kind", choices=["ASSISTANT_VISION", "OWNER", "HUMAN_REVIEWER"], required=True)
    p.add_argument("--reviewed-pass", action="store_true")
    a = p.parse_args()

    run_path = Path(a.run).resolve()
    run = json.loads(run_path.read_text(encoding="utf-8-sig"))
    if run.get("schema") != 6 or run.get("revision") != "6.6.9":
        raise SystemExit("run is not VF Project 6.6.9")
    ws = run_path.parent
    final_ref = (run.get("final") or {}).get("file") or {}
    src = (ws / final_ref.get("path", "")).resolve()
    if not src.is_file() or digest(src) != final_ref.get("sha256"):
        raise SystemExit("project final binding mismatch")

    out = Path(a.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise SystemExit("output exists; refuse overwrite")
    cfg = load_config()
    normalize_image(src, out, int(cfg["imageNormalization"]["quality"]))

    with Image.open(src) as s, Image.open(out) as t:
        s = s.convert("RGB")
        t = t.convert("RGB")
        if s.size != t.size:
            raise SystemExit("transport dimensions changed")
        diff = ImageChops.difference(s, t)
        hist = diff.histogram()
        pixels = s.width * s.height * 3
        abs_sum = sum((i % 256) * count for i, count in enumerate(hist))
        mae = abs_sum / max(1, pixels)
        mse = 0.0
        for band in range(3):
            for value in range(256):
                count = hist[band * 256 + value]
                mse += (value * value) * count
        mse /= max(1, pixels)
        psnr = 99.0 if mse == 0 else 20.0 * math.log10(255.0 / math.sqrt(mse))
        metadata_stripped = not any(
            t.info.get(k) for k in ("exif", "icc_profile", "comment", "progressive", "progression")
        )
    if not metadata_stripped:
        raise SystemExit("transport metadata/progressive markers remain")
    if not a.reviewed_pass:
        raise SystemExit("open the transport artifact and rerun with --reviewed-pass after visual equivalence review")

    receipt = {
        "schema": "velvet.project669.transport_qa.v1",
        "source_final_sha256": digest(src),
        "transport_sha256": digest(out),
        "source_dimensions": [s.width, s.height],
        "transport_dimensions": [t.width, t.height],
        "mean_absolute_channel_error": round(mae, 6),
        "psnr_db": round(psnr, 3),
        "metadata_stripped": True,
        "opened_transport": True,
        "visual_equivalence": "PASS",
        "reviewer_kind": a.reviewer_kind,
        "note": "Canonical JPEG transport normalization only; no creative/product edit.",
    }
    rp = Path(a.receipt).resolve()
    rp.parent.mkdir(parents=True, exist_ok=True)
    if rp.exists():
        raise SystemExit("receipt exists; refuse overwrite")
    rp.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
