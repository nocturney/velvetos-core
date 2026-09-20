"""GrokBot-safe Instagram failover runner.

This runner can only publish an already prepared, owner-approved publish_image
package. It re-runs VelvetOS preflight, checks for an existing identical caption,
obtains a fresh signed delivery approval, uses the server-side MCP bearer through
openpost-prod, and verifies the resulting Instagram media.

Without --execute the command is a dry-run and cannot write to Instagram.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from typing import Any

SCHEMA = "velvet.instagram_failover.v1"
PROJECT = "instamcp"
ZONE = "us-central1-a"
INSTANCE = "openpost-prod"
REMOTE_HELPER = "/opt/velvetos/instagram-failover-mcp.py"
REMOTE_STATE = "/opt/velvetos/openpost-failover-state.py"
SSH_KEY = r"C:\Users\Chris\.ssh\google_compute_engine"
SHA_RE = re.compile(r"/sha256/([0-9a-f]{64})/", re.I)


class Blocked(RuntimeError):
    pass


def _gcloud() -> str:
    explicit = os.environ.get("GCLOUD_BIN", "").strip()
    if explicit:
        return explicit
    for name in ("gcloud", "gcloud.cmd"):
        found = shutil.which(name)
        if found:
            return found
    known = Path(r"C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd")
    if known.exists():
        return str(known)
    raise Blocked("gcloud not found")


def _run(argv: list[str], *, timeout: int = 180, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if os.name == "nt":
        env.setdefault("CLOUDSDK_CONFIG", r"C:\Users\Chris\AppData\Roaming\gcloud")
        env["USERPROFILE"] = r"C:\Users\Chris"
        env["HOME"] = r"C:\Users\Chris"
        env["HOMEDRIVE"] = "C:"
        env["HOMEPATH"] = r"\Users\Chris"
    proc = subprocess.run(argv, text=True, capture_output=True, timeout=timeout, check=False, env=env)
    if check and proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        tail = detail[-1] if detail else "command failed"
        raise Blocked(f"{' '.join(argv[:3])}: {tail[:300]}")
    return proc


def _json_from_text(text: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    start = text.find("{")
    if start < 0:
        raise Blocked("expected JSON output")
    try:
        value, _ = decoder.raw_decode(text[start:])
    except json.JSONDecodeError as exc:
        raise Blocked("invalid JSON output") from exc
    if not isinstance(value, dict):
        raise Blocked("JSON output is not an object")
    return value


def _remote_command(gcloud: str, command: str, *, timeout: int = 180) -> dict[str, Any]:
    proc = _run(
        [
            gcloud,
            "compute",
            "ssh",
            INSTANCE,
            f"--project={PROJECT}",
            f"--zone={ZONE}",
            "--tunnel-through-iap",
            f"--ssh-key-file={SSH_KEY}",
            "--quiet",
            f"--command={command}",
        ],
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        raise Blocked("remote helper failed")
    return _json_from_text(proc.stdout)


def _remote_list_media(gcloud: str, limit: int = 25) -> dict[str, Any]:
    return _remote_command(
        gcloud,
        f"sudo python3 {REMOTE_HELPER} list-media --limit {max(1, min(limit, 100))}",
    )


def _primary_failover_state(gcloud: str, manifest: dict[str, Any]) -> dict[str, Any]:
    publication_id = manifest.get("publication_id")
    rendition_id = manifest.get("rendition_id")
    if not isinstance(publication_id, str) or not publication_id.strip():
        raise Blocked("failover manifest missing publication_id")
    if not isinstance(rendition_id, str) or not rendition_id.strip():
        raise Blocked("failover manifest missing rendition_id")
    state = _remote_command(
        gcloud,
        f"sudo python3 {REMOTE_STATE} --publication-id {publication_id.strip()} --rendition-id {rendition_id.strip()}",
    )
    if state.get("ok") is not True:
        raise Blocked("OpenPost failover-state check failed")
    return state


def _extract_media_sha(payload: dict[str, Any]) -> str:
    url = payload.get("image_url")
    if not isinstance(url, str):
        raise Blocked("approval request image_url missing")
    match = SHA_RE.search(url)
    if not match:
        raise Blocked("image_url is not bound to the Velvet media CAS sha256 path")
    return match.group(1).lower()


def _preflight(repo: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    preflight_path = Path(manifest["preflight_path"])
    if not preflight_path.exists():
        raise Blocked("preflight evidence file missing")
    proc = _run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(repo / "scripts" / "vf_send_preflight.py"),
            "--gate",
            "instagram",
            "--content-id",
            manifest["content_id"],
            "--format",
            manifest.get("format", "post"),
            "--approval-ref",
            str(preflight_path),
            "--package-sha256",
            manifest["package_sha256"],
        ],
        timeout=120,
    )
    result = _json_from_text(proc.stdout)
    quality = result.get("publication_quality") if isinstance(result.get("publication_quality"), dict) else {}
    if quality.get("publishAuthorized") is not True or quality.get("problems") not in ([], None):
        raise Blocked("Instagram preflight did not authorize publish")
    if quality.get("packageSha256") != manifest["package_sha256"]:
        raise Blocked("preflight package SHA mismatch")
    return quality


def _load_manifest(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    if manifest.get("schema") != SCHEMA:
        raise Blocked("unsupported failover manifest schema")
    for field in ("content_id", "package_sha256", "preflight_path", "approval_request_path"):
        value = manifest.get(field)
        if not isinstance(value, str) or not value.strip():
            raise Blocked(f"manifest missing {field}")
    if not re.fullmatch(r"[0-9a-f]{64}", manifest["package_sha256"]):
        raise Blocked("invalid package SHA")

    request_path = Path(manifest["approval_request_path"])
    if not request_path.exists():
        raise Blocked("approval request file missing")
    request = json.loads(request_path.read_text(encoding="utf-8-sig"))
    if request.get("content_id") != manifest["content_id"]:
        raise Blocked("approval request content_id mismatch")
    if request.get("package_sha256") != manifest["package_sha256"]:
        raise Blocked("approval request package SHA mismatch")
    if request.get("mutation_tool") != "publish_image":
        raise Blocked("failover supports publish_image only")
    payload = request.get("mutation_payload")
    if not isinstance(payload, dict):
        raise Blocked("approval request mutation_payload missing")
    if payload.get("account") != "env":
        raise Blocked("Instagram account binding must be env")
    caption = payload.get("caption")
    if not isinstance(caption, str) or not caption.strip():
        raise Blocked("approved caption missing")
    media_sha = _extract_media_sha(payload)
    expected = manifest.get("expected_media_sha256")
    if expected is not None and expected != media_sha:
        raise Blocked("manifest media SHA mismatch")
    return manifest, request


def _duplicate(media_listing: dict[str, Any], caption: str) -> dict[str, Any] | None:
    for media in media_listing.get("media") or []:
        if isinstance(media, dict) and media.get("caption") == caption:
            return media
    return None


def _issue_approval(repo: Path, request_path: Path, output: Path) -> dict[str, Any]:
    proc = _run(
        [
            sys.executable,
            str(repo / "packages" / "vfigos" / "approval" / "owner_call.py"),
            "issue",
            "--body-file",
            str(request_path),
            "--output",
            str(output),
        ],
        timeout=90,
    )
    safe = _json_from_text(proc.stdout)
    if safe.get("ok") is not True:
        raise Blocked("delivery approval issuer did not return ok=true")
    response = json.loads(output.read_text(encoding="utf-8-sig"))
    receipt = response.get("receipt")
    if not isinstance(receipt, dict):
        raise Blocked("signed receipt missing")
    return receipt


def _safe_summary(*, manifest: dict[str, Any], mode: str, extra: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": extra.get("ok", True),
        "mode": mode,
        "content_id": manifest["content_id"],
        "package_sha256": manifest["package_sha256"],
        "publication_id": manifest.get("publication_id"),
        "rendition_id": manifest.get("rendition_id"),
        **{k: v for k, v in extra.items() if k not in {"receipt", "delivery_approval"}},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    manifest, request = _load_manifest(manifest_path)
    repo_hint = manifest.get("repo_root") or os.environ.get("VELVETOS_REPO_ROOT")
    if repo_hint:
        repo = Path(repo_hint).resolve()
    else:
        bundled = Path(__file__).resolve().parents[3]
        fallback = Path(r"C:\Users\Chris\velvetos-core")
        repo = bundled if (bundled / "scripts" / "vf_send_preflight.py").exists() else fallback
    if not (repo / "scripts" / "vf_send_preflight.py").exists():
        raise Blocked("VelvetOS repo root not available")
    payload = request["mutation_payload"]
    media_sha = _extract_media_sha(payload)

    quality = _preflight(repo, manifest)
    visual_hashes = ((quality.get("evidenceValidation") or {}).get("visualHashes") or [])
    if visual_hashes and media_sha not in visual_hashes:
        raise Blocked("preflight visual hash does not contain approved media SHA")

    gcloud = _gcloud()
    listing = _remote_list_media(gcloud, 25)
    if listing.get("ok") is not True:
        raise Blocked("Instagram duplicate check failed")
    existing = _duplicate(listing, payload["caption"])
    if existing:
        print(json.dumps(_safe_summary(
            manifest=manifest,
            mode="duplicate-safe",
            extra={
                "ok": True,
                "skipped_duplicate": True,
                "media_id": existing.get("id"),
                "permalink": existing.get("permalink"),
                "media_sha256": media_sha,
            },
        ), ensure_ascii=False))
        return 0

    primary = _primary_failover_state(gcloud, manifest)
    if not args.execute:
        print(json.dumps(_safe_summary(
            manifest=manifest,
            mode="dry-run",
            extra={
                "ok": True,
                "publish_authorized": True,
                "duplicate_found": False,
                "media_sha256": media_sha,
                "primary_safe_to_failover": primary.get("safe_to_failover") is True,
                "primary_reason": primary.get("reason"),
            },
        ), ensure_ascii=False))
        return 0

    if primary.get("safe_to_failover") is not True:
        print(json.dumps(_safe_summary(
            manifest=manifest,
            mode="primary-blocked",
            extra={
                "ok": False,
                "blocked": True,
                "error": "OpenPost primary outcome is not proven safe for failover",
                "primary_reason": primary.get("reason"),
                "primary_publication_status": (primary.get("publication") or {}).get("status"),
                "primary_rendition_status": (primary.get("rendition") or {}).get("status"),
                "primary_job_status": (primary.get("job") or {}).get("status"),
                "primary_delivery_state": (primary.get("delivery") or {}).get("state"),
                "primary_retry_safety": (primary.get("delivery") or {}).get("retry_safety"),
            },
        ), ensure_ascii=False))
        return 2

    token = uuid.uuid4().hex
    remote_call = f"/tmp/velvet-instagram-failover-{token}.json"
    request_path = Path(manifest["approval_request_path"])
    with tempfile.TemporaryDirectory(prefix="velvet-instagram-failover-") as td:
        temp = Path(td)
        receipt_path = temp / "receipt.json"
        call_path = temp / "call.json"
        receipt = _issue_approval(repo, request_path, receipt_path)

        if receipt.get("content_id") != manifest["content_id"]:
            raise Blocked("receipt content_id mismatch")
        if receipt.get("package_sha256") != manifest["package_sha256"]:
            raise Blocked("receipt package SHA mismatch")
        if receipt.get("mutation_tool") != "publish_image":
            raise Blocked("receipt mutation tool mismatch")

        call_payload = dict(payload)
        call_payload.update(
            {
                "delivery_approval": receipt,
                "content_id": manifest["content_id"],
                "package_sha256": manifest["package_sha256"],
            }
        )
        call_path.write_text(
            json.dumps({"name": "publish_image", "arguments": call_payload}, ensure_ascii=False),
            encoding="utf-8",
        )
        try:
            _run(
                [
                    gcloud,
                    "compute",
                    "scp",
                    str(call_path),
                    f"{INSTANCE}:{remote_call}",
                    f"--project={PROJECT}",
                    f"--zone={ZONE}",
                    "--tunnel-through-iap",
                    f"--ssh-key-file={SSH_KEY}",
                    "--quiet",
                ],
                timeout=120,
            )
            publish = _remote_command(
                gcloud,
                f"sudo python3 {REMOTE_HELPER} publish-call --call {remote_call}",
                timeout=180,
            )
        finally:
            _run(
                [
                    gcloud,
                    "compute",
                    "ssh",
                    INSTANCE,
                    f"--project={PROJECT}",
                    f"--zone={ZONE}",
                    "--tunnel-through-iap",
                    f"--ssh-key-file={SSH_KEY}",
                    "--quiet",
                    f"--command=sudo rm -f {remote_call}",
                ],
                timeout=90,
                check=False,
            )

    if publish.get("ok") is not True:
        print(json.dumps(_safe_summary(
            manifest=manifest,
            mode="publish-blocked",
            extra={
                "ok": False,
                "error": publish.get("error"),
                "error_class": publish.get("error_class"),
                "stage": publish.get("stage"),
                "provider_code": publish.get("provider_code"),
                "http_status": publish.get("http_status"),
                "write_outcome": publish.get("write_outcome"),
                "retry_safety": publish.get("retry_safety"),
            },
        ), ensure_ascii=False))
        return 2

    media_id = publish.get("media_id") or publish.get("id")
    if not isinstance(media_id, str) or not media_id:
        raise Blocked("publish returned no media id")
    verified = _remote_command(
        gcloud,
        f"sudo python3 {REMOTE_HELPER} get-media --media-id {media_id}",
    )
    media = verified.get("media") if isinstance(verified.get("media"), dict) else {}
    if verified.get("ok") is not True or media.get("id") != media_id:
        raise Blocked("Instagram live verification failed")
    if media.get("caption") != payload["caption"]:
        raise Blocked("live caption does not match approved caption")

    print(json.dumps(_safe_summary(
        manifest=manifest,
        mode="executed",
        extra={
            "ok": True,
            "media_id": media_id,
            "permalink": media.get("permalink"),
            "media_sha256": media_sha,
            "live_verified": True,
        },
    ), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Blocked, OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"ok": False, "blocked": True, "error": str(exc)[:500]}, ensure_ascii=False))
        raise SystemExit(2)
