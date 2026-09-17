#!/usr/bin/env python3
"""Fail-closed effective-IAM preflight for vfigos Cloud Build deployments.

Resolve the actual Cloud Build identity and prove through gcloud Policy
Troubleshooter that it cannot cross signer-isolation boundaries. This helper
never reads secret values or prints identity/access tokens.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path
from typing import Callable

DENIED_ALLOW_STATE = "ALLOW_ACCESS_STATE_NOT_GRANTED"
DENIED_OVERALL_STATE = "CANNOT_ACCESS"
ISSUER_SERVICE = "velvet-delivery-approval-issuer"
SIGNING_SECRET = "velvet-delivery-approval-ed25519-private"
INSTAGRAM_SECRETS = (
    "velvet-instagram-mcp-access",
    "velvet-instagram-mcp-bearer",
    "velvet-instagram-mcp-ig-user",
)
SENSITIVE_PERMISSIONS = frozenset(
    {
        "run.routes.invoke",
        "run.services.setIamPolicy",
        "secretmanager.versions.access",
        "iam.serviceAccounts.actAs",
        "iam.serviceAccounts.getAccessToken",
        "iam.serviceAccounts.getOpenIdToken",
    }
)
_EMAIL_RE = re.compile(r"[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com")
_SA_LINE_RE = re.compile(r"^\s*serviceAccount\s*:\s*(\S+)\s*$")
Troubleshoot = Callable[[str, str, str], tuple[str, str]]


class IsolationError(RuntimeError):
    """Raised when deployment isolation cannot be proven."""


def redact(text: str) -> str:
    cleaned = re.sub(r"ya29\.[0-9A-Za-z\-_]+", "[redacted]", text or "")
    cleaned = re.sub(r"Bearer\s+\S+", "Bearer [redacted]", cleaned)
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    return (lines[-1] if lines else "command failed")[:180]
def _gcloud(*args: str) -> str:
    binary = os.environ.get("GCLOUD_BIN", "gcloud")
    proc = subprocess.run(
        [binary, *args],
        text=True,
        capture_output=True,
        timeout=45,
        check=False,
    )
    if proc.returncode != 0:
        raise IsolationError(
            f"gcloud {' '.join(args[:2])} failed: {redact(proc.stderr or proc.stdout)}"
        )
    return proc.stdout.strip()


def parse_build_identity(text: str) -> str:
    emails = list(dict.fromkeys(_EMAIL_RE.findall(text or "")))
    if len(emails) != 1:
        raise IsolationError("Cloud Build default service account could not be resolved")
    return emails[0]


def parse_project_number(text: str) -> str:
    value = (text or "").strip()
    if not value.isdigit():
        raise IsolationError("GCP project number could not be resolved")
    return value
def cloudbuild_service_accounts(text: str) -> list[str]:
    found: list[str] = []
    for raw in (text or "").splitlines():
        line = raw.split("#", 1)[0]
        match = _SA_LINE_RE.match(line)
        if not match:
            if re.search(r"(?<![A-Za-z0-9_-])serviceAccount\s*:", line):
                raise IsolationError(
                    "Cloud Build serviceAccount syntax is not a supported concrete field"
                )
            continue
        value = match.group(1).strip("\"'")
        if "/serviceAccounts/" in value:
            value = value.rsplit("/serviceAccounts/", 1)[1]
        if not _EMAIL_RE.fullmatch(value):
            raise IsolationError("Cloud Build serviceAccount override is not a concrete email")
        if value not in found:
            found.append(value)
    return found


def signer_email(project: str) -> str:
    return f"velvet-delivery-issuer@{project}.iam.gserviceaccount.com"


def owner_invoker_email(project: str) -> str:
    return f"velvet-delivery-owner-invoker@{project}.iam.gserviceaccount.com"


def mutation_runtime_email(project: str) -> str:
    return f"velvet-instagram-mcp-runtime@{project}.iam.gserviceaccount.com"


def protected_identities(project: str) -> tuple[str, str, str]:
    return (signer_email(project), owner_invoker_email(project), mutation_runtime_email(project))
def build_probe_plan(
    project: str, region: str, project_number: str
) -> list[tuple[str, str, str]]:
    issuer = (
        f"//run.googleapis.com/projects/{project}/locations/{region}/services/"
        f"{ISSUER_SERVICE}"
    )
    probes: list[tuple[str, str, str]] = [
        (issuer, "run.routes.invoke", "issuer invoke"),
        (issuer, "run.services.setIamPolicy", "issuer setIamPolicy"),
    ]
    for secret in (SIGNING_SECRET, *INSTAGRAM_SECRETS):
        probes.append(
            (
                f"//secretmanager.googleapis.com/projects/{project_number}/secrets/"
                f"{secret}/versions/latest",
                "secretmanager.versions.access",
                f"secret access {secret}",
            )
        )
    for email in protected_identities(project):
        resource = f"//iam.googleapis.com/projects/{project}/serviceAccounts/{email}"
        for permission, label in (
            ("iam.serviceAccounts.actAs", "actAs"),
            ("iam.serviceAccounts.getAccessToken", "access token"),
            ("iam.serviceAccounts.getOpenIdToken", "OIDC token"),
        ):
            probes.append((resource, permission, f"{label} {email}"))
    return probes
def parse_troubleshoot_output(text: str) -> tuple[str, str]:
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    if len(lines) != 1:
        raise IsolationError("Policy Troubleshooter returned malformed output")
    fields = lines[0].split()
    if len(fields) != 2:
        raise IsolationError("Policy Troubleshooter returned incomplete access state")
    return fields[0], fields[1]


def require_denied(states: tuple[str, str], label: str) -> None:
    allow_state, overall_state = states
    if allow_state != DENIED_ALLOW_STATE or overall_state != DENIED_OVERALL_STATE:
        raise IsolationError(
            f"{label}: effective IAM is not proven denied "
            f"({allow_state!r}, {overall_state!r})"
        )


def live_troubleshoot(resource: str, principal: str, permission: str) -> tuple[str, str]:
    output = _gcloud(
        "policy-intelligence",
        "troubleshoot-policy",
        "iam",
        resource,
        f"--principal-email={principal}",
        f"--permission={permission}",
        "--format=value(allowPolicyExplanation.allowAccessState,overallAccessState)",
    )
    return parse_troubleshoot_output(output)
def assert_build_identity_isolated(
    project: str,
    region: str,
    cloudbuild_config: Path,
    *,
    principal: str | None = None,
    project_number: str | None = None,
    troubleshoot: Troubleshoot | None = None,
) -> tuple[str, int]:
    overrides = cloudbuild_service_accounts(cloudbuild_config.read_text(encoding="utf-8"))
    resolved = principal or parse_build_identity(
        _gcloud("builds", "get-default-service-account", f"--project={project}")
    )
    number = project_number or parse_project_number(
        _gcloud("projects", "describe", project, "--format=value(projectNumber)")
    )
    identities = list(dict.fromkeys([resolved, *overrides]))
    probe = troubleshoot or live_troubleshoot
    plan = build_probe_plan(project, region, number)

    for identity in identities:
        if identity in protected_identities(project):
            raise IsolationError(
                "Cloud Build identity must be separate from signer/owner/mutation runtime"
            )
        for resource, permission, label in plan:
            require_denied(probe(resource, identity, permission), f"{identity} {label}")
    return resolved, len(plan) * len(identities)
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail-closed vfigos Cloud Build identity isolation preflight"
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--cloudbuild-config", type=Path, required=True)
    args = parser.parse_args()
    try:
        principal, probes = assert_build_identity_isolated(
            args.project, args.region, args.cloudbuild_config
        )
    except (IsolationError, OSError, subprocess.SubprocessError) as exc:
        print(f"BLOCKED build-isolation: {redact(str(exc))}")
        return 1
    print(f"OK build-isolation principal={principal} probes={probes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
