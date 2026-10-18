#!/usr/bin/env python3
"""Upload one log to the current GitHub Actions artifact store.

Uses the runner's ACTIONS_RUNTIME_TOKEN and ACTIONS_RESULTS_URL. No extra
action and no new secret. The signed upload URL is never printed.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

SERVICE = "github.actions.results.api.v1.ArtifactService"
ARTIFACT_NAME = "check-all-windows"


def backend_ids(token: str) -> tuple[str, str]:
    try:
        payload = token.split(".")[1]
    except IndexError as exc:
        raise ValueError("runtime token is not a JWT") from exc
    pad = "=" * (-len(payload) % 4)
    try:
        data = json.loads(base64.urlsafe_b64decode(payload + pad))
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError("runtime token payload is not JSON") from exc
    scp = data.get("scp")
    if not isinstance(scp, str):
        raise ValueError("runtime token has no scp claim")
    for scope in scp.split():
        parts = scope.split(":")
        if len(parts) == 3 and parts[0] == "Actions.Results" and parts[1] and parts[2]:
            return parts[1], parts[2]
    raise ValueError("runtime token has no Actions.Results ids")


def create_body(run_id: str, job_id: str, name: str) -> dict:
    # protobuf-ts toJson(useProtoFieldName) plus proto3 JSON wrappers:
    # google.protobuf.StringValue is a JSON string, not {"value": "..."}.
    return {
        "workflow_run_backend_id": run_id,
        "workflow_job_run_backend_id": job_id,
        "name": name,
        "version": 7,
        "mime_type": "application/zip",
    }


def finalize_body(run_id: str, job_id: str, name: str, size: int, digest: str) -> dict:
    return {
        "workflow_run_backend_id": run_id,
        "workflow_job_run_backend_id": job_id,
        "name": name,
        "size": str(size),
        "hash": "sha256:" + digest,
    }


def suite_summary(text: str) -> str:
    for line in reversed(text.splitlines()):
        stripped = line.strip()
        if stripped.startswith("OK suite passed=") or stripped.startswith("FAIL suite failed="):
            return stripped
    return "UNFINISHED"


def redact(text: str) -> str:
    return re.sub(r"(sig=)[^&\s\"']+", r"\1REDACTED", text)


def _zip_bytes(path: Path) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(path, arcname=path.name)
    return buf.getvalue()


def _post_json(url: str, token: str, body: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        method="POST",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = redact(exc.read().decode("utf-8", "replace")[:500])
        raise RuntimeError(f"{url.rsplit('/', 1)[-1]} HTTP {exc.code}: {detail}") from None


def _put(url: str, data: bytes, headers: dict) -> tuple[int, str]:
    req = urllib.request.Request(url, data=data, method="PUT", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, ""
    except urllib.error.HTTPError as exc:
        return exc.code, redact(exc.read().decode("utf-8", "replace")[:400])


def _with_query(url: str, extra: str) -> str:
    return url + ("&" if "?" in url else "?") + extra


def _put_blob(url: str, blob: bytes) -> None:
    status, detail = _put(url, blob, {
        "x-ms-blob-type": "BlockBlob",
        "x-ms-blob-content-type": "application/zip",
        "Content-Type": "application/zip",
    })
    if status in (200, 201):
        return
    block_id = base64.b64encode(b"checkallwin0001").decode()
    block_status, block_detail = _put(
        _with_query(url, "comp=block&blockid=" + block_id),
        blob,
        {"Content-Type": "application/octet-stream"},
    )
    if block_status not in (200, 201):
        raise RuntimeError(f"blob upload HTTP {status} then block HTTP {block_status}: {block_detail or detail}")
    listing = (
        "<?xml version=\"1.0\" encoding=\"utf-8\"?>"
        f"<BlockList><Latest>{block_id}</Latest></BlockList>"
    ).encode()
    commit_status, commit_detail = _put(
        _with_query(url, "comp=blocklist"),
        listing,
        {"Content-Type": "application/xml"},
    )
    if commit_status not in (200, 201):
        raise RuntimeError(f"blob block list HTTP {commit_status}: {commit_detail}")


def upload_log(path: Path, name: str = ARTIFACT_NAME) -> int:
    token = os.environ.get("ACTIONS_RUNTIME_TOKEN") or ""
    results = os.environ.get("ACTIONS_RESULTS_URL") or ""
    if not token or not results:
        raise RuntimeError("missing ACTIONS_RUNTIME_TOKEN or ACTIONS_RESULTS_URL")
    run_id, job_id = backend_ids(token)
    origin = results if results.endswith("/") else results + "/"
    blob = _zip_bytes(path)
    created = _post_json(
        origin + "twirp/" + SERVICE + "/CreateArtifact",
        token,
        create_body(run_id, job_id, name),
    )
    signed = created.get("signed_upload_url") or created.get("signedUploadUrl")
    if not created.get("ok") or not isinstance(signed, str) or not signed:
        raise RuntimeError("CreateArtifact did not return a signed upload URL")
    _put_blob(signed, blob)
    digest = hashlib.sha256(blob).hexdigest()
    final = _post_json(
        origin + "twirp/" + SERVICE + "/FinalizeArtifact",
        token,
        finalize_body(run_id, job_id, name, len(blob), digest),
    )
    if not final.get("ok"):
        raise RuntimeError("FinalizeArtifact was not ok")
    return len(blob)


def selftest() -> int:
    token = "h." + base64.urlsafe_b64encode(json.dumps({
        "scp": "Actions.Results:run-id:job-id",
    }).encode()).decode().rstrip("=") + ".s"
    if backend_ids(token) != ("run-id", "job-id"):
        print("FAIL backend ids", file=sys.stderr)
        return 1
    try:
        backend_ids("nope")
    except ValueError:
        pass
    else:
        print("FAIL bare token accepted", file=sys.stderr)
        return 1
    body = create_body("run-id", "job-id", ARTIFACT_NAME)
    if body["version"] != 7 or body["mime_type"] != "application/zip":
        print("FAIL create body", file=sys.stderr)
        return 1
    if body["workflow_run_backend_id"] != "run-id" or "mimeType" in body:
        print("FAIL create body field names", file=sys.stderr)
        return 1
    final = finalize_body("run-id", "job-id", ARTIFACT_NAME, 4, "ab")
    if final["size"] != "4" or final["hash"] != "sha256:ab":
        print("FAIL finalize body", file=sys.stderr)
        return 1
    if "signed_upload_url" in json.dumps(body):
        print("FAIL create body leaked an upload URL field", file=sys.stderr)
        return 1
    sample = "PASS check-a\nFAIL suite failed=2/10\n"
    if suite_summary(sample) != "FAIL suite failed=2/10":
        print("FAIL summary fail line", file=sys.stderr)
        return 1
    if suite_summary("noise\nOK suite passed=123\n") != "OK suite passed=123":
        print("FAIL summary pass line", file=sys.stderr)
        return 1
    if suite_summary("still running") != "UNFINISHED":
        print("FAIL summary unfinished", file=sys.stderr)
        return 1
    if "REDACTED" not in redact("https://example.test/blob?sig=super-secret&se=1"):
        print("FAIL redact", file=sys.stderr)
        return 1
    print("OK upload_gha_artifact self-test")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[1] == "--self-test":
        return selftest()
    if len(argv) != 2:
        print("usage: upload_gha_artifact.py LOG | --self-test", file=sys.stderr)
        return 2
    path = Path(argv[1])
    text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    print("WINDOWS_SUITE " + suite_summary(text), flush=True)
    if not path.is_file():
        print("no log to upload", file=sys.stderr)
        return 1
    try:
        size = upload_log(path)
    except (RuntimeError, ValueError, OSError) as exc:
        print(redact(str(exc)), file=sys.stderr)
        return 1
    print(f"artifact {ARTIFACT_NAME} uploaded bytes={size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
