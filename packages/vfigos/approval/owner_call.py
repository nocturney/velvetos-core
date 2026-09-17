#!/usr/bin/env python3
"""Owner-only calls to the delivery-approval issuer with narrow IAM.

Uses IAM Credentials generateIdToken so the human owner needs only
roles/iam.serviceAccountOpenIdTokenCreator on the delegated owner-invoker.
Access and identity tokens are kept in memory and never printed.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Any

DEFAULT_PROJECT = "instamcp"
DEFAULT_REGION = "me-west1"
DEFAULT_ISSUER_SERVICE = "velvet-delivery-approval-issuer"
DEFAULT_OWNER_INVOKER = "velvet-delivery-owner-invoker@instamcp.iam.gserviceaccount.com"
IAM_CREDENTIALS_BASE = "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/"
MAX_ISSUE_BODY_BYTES = 16 * 1024


class OwnerCallError(RuntimeError):
    pass
def _gcloud_binary(explicit: str | None = None) -> str:
    candidate = (explicit or os.environ.get("GCLOUD_BIN") or "").strip()
    if candidate:
        return candidate
    for name in ("gcloud", "gcloud.cmd"):
        resolved = shutil.which(name)
        if resolved:
            return resolved
    raise OwnerCallError("gcloud not found; install/authenticate Google Cloud CLI or set GCLOUD_BIN")


def _gcloud(binary: str, *args: str) -> str:
    proc = subprocess.run([binary, *args], text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        label = " ".join(args[:2])
        raise OwnerCallError(f"gcloud {label} failed (exit {proc.returncode})")
    return proc.stdout.strip()


def _http(method: str, url: str, *, headers: dict[str, str], body: bytes | None = None) -> tuple[int, bytes]:
    req = urllib.request.Request(url, data=body, method=method)
    for key, value in headers.items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:  # noqa: S310 - fixed HTTPS endpoints
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read() if exc.fp else b""
def _resolve_issuer_url(gcloud: str) -> str:
    return _gcloud(
        gcloud,
        "run",
        "services",
        "describe",
        DEFAULT_ISSUER_SERVICE,
        f"--project={DEFAULT_PROJECT}",
        f"--region={DEFAULT_REGION}",
        "--format=value(status.url)",
    ).rstrip("/")


def _owner_id_token(gcloud: str, audience: str) -> str:
    access_token = _gcloud(gcloud, "auth", "print-access-token")
    endpoint = IAM_CREDENTIALS_BASE + DEFAULT_OWNER_INVOKER + ":generateIdToken"
    payload = json.dumps({"audience": audience, "includeEmail": True}, separators=(",", ":")).encode()
    status, raw = _http(
        "POST",
        endpoint,
        headers={"Authorization": "Bearer " + access_token, "Content-Type": "application/json"},
        body=payload,
    )
    access_token = ""
    if status != 200:
        raise OwnerCallError(f"IAMCredentials generateIdToken failed (HTTP {status})")
    data = json.loads(raw.decode("utf-8"))
    token = data.get("token")
    if not isinstance(token, str) or not token:
        raise OwnerCallError("IAMCredentials returned no identity token")
    return token
def _health(args: argparse.Namespace, gcloud: str, issuer_url: str, token: str) -> int:
    status, raw = _http(
        "GET",
        issuer_url + "/health",
        headers={"Authorization": "Bearer " + token},
    )
    token = ""
    if status != 200:
        raise OwnerCallError(f"issuer health failed (HTTP {status})")
    data = json.loads(raw.decode("utf-8"))
    if data.get("ok") is not True:
        raise OwnerCallError("issuer health returned ok=false")
    report = {
        "ok": True,
        "status": status,
        "path": "/health",
        "service": data.get("service"),
        "schema": data.get("schema"),
        "key_id_configured": data.get("key_id_configured"),
        "mutation_service_has_private_key": data.get("mutation_service_has_private_key"),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def _issue(args: argparse.Namespace, gcloud: str, issuer_url: str, token: str) -> int:
    raw_body = Path(args.body_file).read_bytes()
    if not raw_body or len(raw_body) > MAX_ISSUE_BODY_BYTES:
        raise OwnerCallError("issue body must be 1..16384 bytes")
    data = json.loads(raw_body.decode("utf-8"))
    if not isinstance(data, dict):
        raise OwnerCallError("issue body must be a JSON object")
    status, raw = _http(
        "POST",
        issuer_url + "/v1/delivery-approvals",
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        body=raw_body,
    )
    token = ""
    if status != 200:
        raise OwnerCallError(f"issuer issue failed (HTTP {status})")
    response = json.loads(raw.decode("utf-8"))
    receipt = response.get("receipt") if isinstance(response, dict) else None
    if response.get("ok") is not True or not isinstance(receipt, dict):
        raise OwnerCallError("issuer did not return a receipt")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(response, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({
        "ok": True,
        "status": status,
        "approval_id": receipt.get("approval_id"),
        "expires_at": receipt.get("expires_at"),
        "output": str(output),
    }, ensure_ascii=False, indent=2))
    return 0
def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Call the delivery issuer via narrow owner-invoker OIDC")
    parser.add_argument("--gcloud")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("health", help="Verify owner-authenticated issuer /health")
    issue = sub.add_parser("issue", help="Issue a signed approval from a JSON request file")
    issue.add_argument("--body-file", required=True)
    issue.add_argument("--output", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        gcloud = _gcloud_binary(args.gcloud)
        issuer_url = _resolve_issuer_url(gcloud)
        token = _owner_id_token(gcloud, issuer_url)
        if args.command == "health":
            return _health(args, gcloud, issuer_url, token)
        return _issue(args, gcloud, issuer_url, token)
    except (OwnerCallError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"BLOCKED owner-call: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
