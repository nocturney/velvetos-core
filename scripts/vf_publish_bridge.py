#!/usr/bin/env python3
"""Prepare and optionally stage approved VelvetOS publish derivatives.

The bridge intentionally stages only assets that are already approved for public
release. It never changes Google Drive sharing and never treats staging as
publication.

Examples:
  python3 scripts/vf_publish_bridge.py prepare --file story.png --correlation G004 \
    --approval-ref packages/vfgrowth/preflight/G004.md --source-ref canva:DA...

  python3 scripts/vf_publish_bridge.py stage --file story.png --correlation G004 \
    --approval-ref packages/vfgrowth/preflight/G004.md --source-ref canva:DA... \
    --public-release-approved

Actual staging uses GitHub's REST API and requires GH_TOKEN or GITHUB_TOKEN.
ChatGPT/agent environments may implement the same contract with the connected
GitHub connector instead of exposing a token to this CLI.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "packages" / "vfigos" / "PUBLISH-BRIDGE.json"
SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def safe_segment(value: str, label: str) -> str:
    if not SAFE_SEGMENT.fullmatch(value):
        raise ValueError(f"{label} must match {SAFE_SEGMENT.pattern}")
    return value


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_image(src: Path, dst: Path, quality: int) -> tuple[int, int]:
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise RuntimeError("Pillow is required for publish-bridge image normalization") from exc

    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode not in ("RGB", "L"):
            bg = Image.new("RGB", im.size, "white")
            if "A" in im.getbands():
                bg.paste(im, mask=im.getchannel("A"))
                im = bg
            else:
                im = im.convert("RGB")
        else:
            im = im.convert("RGB")
        width, height = im.size
        # No EXIF/ICC payload is passed: the derivative is metadata-stripped.
        im.save(dst, "JPEG", quality=quality, optimize=True, progressive=True)
        return width, height


def normalize_video(src: Path, dst: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to strip metadata from video bridge assets")
    cmd = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(src),
        "-map_metadata",
        "-1",
        "-c",
        "copy",
        str(dst),
    ]
    subprocess.run(cmd, check=True)


def normalize(src: Path, cfg: dict[str, Any], tmp: Path) -> tuple[Path, str, dict[str, Any]]:
    ext = src.suffix.lower()
    image = cfg["imageNormalization"]
    video = cfg["videoNormalization"]
    details: dict[str, Any] = {}

    if ext in image["inputExtensions"]:
        dst = tmp / f"asset{image['outputExtension']}"
        width, height = normalize_image(src, dst, int(image["quality"]))
        details.update({"width": width, "height": height})
        content_type = image["contentType"]
        limit = int(image["maxBytes"])
    elif ext in video["inputExtensions"]:
        dst = tmp / f"asset{video['outputExtension']}"
        normalize_video(src, dst)
        content_type = video["contentType"]
        limit = int(video["maxBytes"])
    else:
        allowed = image["inputExtensions"] + video["inputExtensions"]
        raise ValueError(f"unsupported extension {ext!r}; allowed: {', '.join(allowed)}")

    size = dst.stat().st_size
    if size > limit:
        raise ValueError(f"normalized asset is {size} bytes; bridge limit is {limit}")
    details["sizeBytes"] = size
    return dst, content_type, details


def api_request(token: str, method: str, url: str, payload: dict[str, Any] | None = None) -> Any:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {exc.code}: {body[:1000]}") from exc


def verify_public_url(
    url: str,
    expected_sha256: str,
    expected_content_type: str,
    expected_size: int,
    attempts: int = 4,
) -> dict[str, Any]:
    last_error = "unknown"
    for attempt in range(1, attempts + 1):
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "VelvetOS-Publish-Bridge/1"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
                content_type = (resp.headers.get_content_type() or "").lower()
                digest = hashlib.sha256(body).hexdigest()
                size = len(body)
                allowed_types = {expected_content_type.lower(), "application/octet-stream"}
                if digest != expected_sha256:
                    raise RuntimeError(f"public SHA-256 mismatch {digest} != {expected_sha256}")
                if size != expected_size:
                    raise RuntimeError(f"public size mismatch {size} != {expected_size}")
                if content_type not in allowed_types:
                    raise RuntimeError(f"unexpected public content-type {content_type!r}")
                return {
                    "ok": True,
                    "attempt": attempt,
                    "sha256": digest,
                    "sizeBytes": size,
                    "contentType": content_type,
                }
        except Exception as exc:
            last_error = str(exc)
            if attempt < attempts:
                time.sleep(min(2 ** (attempt - 1), 4))
    raise RuntimeError(f"public fetch verification failed after {attempts} attempts: {last_error}")


def stage_to_github(asset: Path, metadata: dict[str, Any], cfg: dict[str, Any]) -> tuple[str, str]:
    token = (os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or "").strip()
    if not token:
        raise RuntimeError("GH_TOKEN or GITHUB_TOKEN is required for CLI staging")

    repo = cfg["repository"]
    branch = cfg["branch"]
    owner, name = repo.split("/", 1)
    api = f"https://api.github.com/repos/{owner}/{name}"
    branch_state = api_request(token, "GET", f"{api}/branches/{urllib.parse.quote(branch, safe='')}")
    parent_sha = branch_state["commit"]["sha"]
    base_tree = branch_state["commit"]["commit"]["tree"]["sha"]

    asset_bytes = asset.read_bytes()
    asset_blob = api_request(
        token,
        "POST",
        f"{api}/git/blobs",
        {"content": base64.b64encode(asset_bytes).decode("ascii"), "encoding": "base64"},
    )["sha"]
    metadata_blob = api_request(
        token,
        "POST",
        f"{api}/git/blobs",
        {"content": json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", "encoding": "utf-8"},
    )["sha"]

    tree = api_request(
        token,
        "POST",
        f"{api}/git/trees",
        {
            "base_tree": base_tree,
            "tree": [
                {"path": metadata["path"], "mode": "100644", "type": "blob", "sha": asset_blob},
                {"path": metadata["metadataPath"], "mode": "100644", "type": "blob", "sha": metadata_blob},
            ],
        },
    )["sha"]
    commit = api_request(
        token,
        "POST",
        f"{api}/git/commits",
        {
            "message": f"publish-bridge: stage {metadata['correlation']} {metadata['sha256'][:12]}",
            "tree": tree,
            "parents": [parent_sha],
        },
    )["sha"]
    api_request(token, "PATCH", f"{api}/git/refs/heads/{urllib.parse.quote(branch, safe='')}", {"sha": commit})
    return metadata["publicUrl"], commit


def build_metadata(
    normalized: Path,
    content_type: str,
    details: dict[str, Any],
    cfg: dict[str, Any],
    correlation: str,
    approval_ref: str,
    source_ref: str,
) -> dict[str, Any]:
    digest = sha256_file(normalized)
    now = dt.datetime.now(dt.timezone.utc)
    day = now.date().isoformat()
    ext = normalized.suffix.lower()
    filename = f"{digest[:20]}{ext}"
    prefix = cfg["pathPrefix"].rstrip("/")
    path = f"{prefix}/{day}/{correlation}/{filename}"
    metadata_path = f"{path}.json"
    public_url = f"{cfg['publicBaseUrl'].rstrip('/')}/{day}/{correlation}/{filename}"
    archive_after = now + dt.timedelta(days=int(cfg["retention"]["activeDays"]))
    return {
        "schemaVersion": 1,
        "state": "staged_not_published",
        "correlation": correlation,
        "approvalRef": approval_ref,
        "sourceRefHash": hashlib.sha256(source_ref.encode("utf-8")).hexdigest(),
        "createdAt": now.isoformat().replace("+00:00", "Z"),
        "archiveAfter": archive_after.isoformat().replace("+00:00", "Z"),
        "archiveRetention": cfg["retention"].get("archiveRetention", "unlimited"),
        "sha256": digest,
        "contentType": content_type,
        **details,
        "path": path,
        "metadataPath": metadata_path,
        "publicUrl": public_url,
    }


def cmd_prepare(args: argparse.Namespace, stage: bool) -> int:
    cfg = load_config()
    src = Path(args.file).expanduser().resolve()
    if not src.is_file():
        raise FileNotFoundError(src)
    correlation = safe_segment(args.correlation, "correlation")
    if not args.approval_ref.strip() or not args.source_ref.strip():
        raise ValueError("approval-ref and source-ref are required")
    if stage and not args.public_release_approved:
        raise ValueError("stage requires --public-release-approved")

    with tempfile.TemporaryDirectory(prefix="vf-publish-bridge-") as tmp_name:
        tmp = Path(tmp_name)
        normalized, content_type, details = normalize(src, cfg, tmp)
        metadata = build_metadata(
            normalized,
            content_type,
            details,
            cfg,
            correlation,
            args.approval_ref.strip(),
            args.source_ref.strip(),
        )
        result: dict[str, Any] = {
            "ok": True,
            "mode": "stage" if stage else "prepare",
            "source": str(src),
            "normalized": {
                "sha256": metadata["sha256"],
                "contentType": content_type,
                **details,
            },
            "publicReleaseApproved": bool(args.public_release_approved),
            "target": {"path": metadata["path"], "publicUrl": metadata["publicUrl"]},
            "archiveAfter": metadata["archiveAfter"],
            "archiveRetention": metadata["archiveRetention"],
            "rule": "staged/fetch_verified != published; publish_* receipt + live verification are still required",
        }
        if stage:
            public_url, commit = stage_to_github(normalized, metadata, cfg)
            fetch_verify = verify_public_url(
                public_url,
                metadata["sha256"],
                content_type,
                int(details["sizeBytes"]),
            )
            result["target"].update({"publicUrl": public_url, "commit": commit, "fetchVerified": fetch_verify})
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "stage"):
        p = sub.add_parser(name)
        p.add_argument("--file", required=True)
        p.add_argument("--correlation", required=True, help="non-PII job/content correlation, e.g. G004")
        p.add_argument("--approval-ref", required=True, help="canonical approval/preflight reference")
        p.add_argument("--source-ref", required=True, help="private provenance; only a SHA-256 hash is published")
        p.add_argument("--public-release-approved", action="store_true")
    args = parser.parse_args()
    try:
        return cmd_prepare(args, stage=args.command == "stage")
    except Exception as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
