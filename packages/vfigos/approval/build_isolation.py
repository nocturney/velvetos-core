#!/usr/bin/env python3
"""Fail-closed effective-IAM preflight for vfigos Cloud Build deployments.

Resolve the actual Cloud Build identity and prove through gcloud Policy
Troubleshooter that it cannot cross signer-isolation boundaries. This helper
never reads secret values or prints identity/access tokens.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Callable

DENIED_ALLOW_STATE = "ALLOW_ACCESS_STATE_NOT_GRANTED"
DENIED_OVERALL_STATE = "CANNOT_ACCESS"
TROUBLESHOOT_MIN_INTERVAL_SECONDS = 4.25
_LAST_TROUBLESHOOT_STARTED = 0.0
ISSUER_SERVICE = "velvet-delivery-approval-issuer"
SIGNING_SECRET = "velvet-delivery-approval-ed25519-private"
KEY_ID_SECRET = "velvet-delivery-approval-key-id"
INSTAGRAM_SECRETS = (
    "velvet-instagram-mcp-access",
    "velvet-instagram-mcp-bearer",
    "velvet-instagram-mcp-ig-user",
)
SPEND_BUCKET = "velvet-ig-approval-spend"
SENSITIVE_PERMISSIONS = frozenset(
    {
        "run.routes.invoke",
        "run.services.setIamPolicy",
        "resourcemanager.projects.setIamPolicy",
        "secretmanager.secrets.setIamPolicy",
        "secretmanager.secrets.update",
        "secretmanager.secrets.delete",
        "secretmanager.versions.access",
        "secretmanager.versions.add",
        "secretmanager.versions.enable",
        "secretmanager.versions.disable",
        "secretmanager.versions.destroy",
        "iam.serviceAccounts.setIamPolicy",
        "iam.serviceAccounts.actAs",
        "iam.serviceAccounts.getAccessToken",
        "iam.serviceAccounts.getOpenIdToken",
        "iam.serviceAccounts.implicitDelegation",
        "iam.serviceAccounts.signBlob",
        "iam.serviceAccounts.signJwt",
        "iam.serviceAccountKeys.create",
        "storage.buckets.setIamPolicy",
        "storage.buckets.update",
        "storage.buckets.delete",
        "storage.objects.create",
        "storage.objects.delete",
        "storage.objects.update",
    }
)
_EMAIL_RE = re.compile(r"[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+\.gserviceaccount\.com")
Troubleshoot = Callable[[str, str, str], tuple[str, str]]
PolicyReader = Callable[[str, str], str]


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
def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise IsolationError(f"Cloud Build JSON contains duplicate key {key!r}")
        result[key] = value
    return result


def cloudbuild_service_accounts(text: str, project: str | None = None) -> list[str]:
    """Parse the Cloud Build config and keep explicit builders in the canonical project."""
    try:
        config = json.loads(text or "", object_pairs_hook=_unique_json_object)
    except IsolationError:
        raise
    except (json.JSONDecodeError, TypeError) as exc:
        raise IsolationError("Cloud Build config must be valid strict JSON") from exc
    if not isinstance(config, dict):
        raise IsolationError("Cloud Build config root must be a JSON object")

    value = config.get("serviceAccount")
    if value is None:
        return []
    if not isinstance(value, str):
        raise IsolationError("Cloud Build serviceAccount override must be a string")
    concrete = value.strip()
    if "/serviceAccounts/" in concrete:
        prefix, concrete = concrete.rsplit("/serviceAccounts/", 1)
        if not prefix.startswith("projects/"):
            raise IsolationError("Cloud Build serviceAccount resource is malformed")
        if project is not None and prefix != f"projects/{project}":
            raise IsolationError(
                "Cloud Build serviceAccount override must remain in the canonical project"
            )
    if not _EMAIL_RE.fullmatch(concrete):
        raise IsolationError("Cloud Build serviceAccount override is not a concrete email")
    if project is not None and not concrete.endswith(
        f"@{project}.iam.gserviceaccount.com"
    ):
        raise IsolationError(
            "Cloud Build serviceAccount override must belong to the canonical project"
        )
    return [concrete]


def default_compute_email(project_number: str) -> str:
    return f"{project_number}-compute@developer.gserviceaccount.com"


def signer_email(project: str) -> str:
    return f"velvet-delivery-issuer@{project}.iam.gserviceaccount.com"


def owner_invoker_email(project: str) -> str:
    return f"velvet-delivery-owner-invoker@{project}.iam.gserviceaccount.com"


def mutation_runtime_email(project: str) -> str:
    return f"velvet-instagram-mcp-runtime@{project}.iam.gserviceaccount.com"


def protected_identities(project: str) -> tuple[str, str, str]:
    return (signer_email(project), owner_invoker_email(project), mutation_runtime_email(project))


def assert_issuer_invoker_policy(text: str, project: str) -> None:
    try:
        policy = json.loads(text or "", object_pairs_hook=_unique_json_object)
    except IsolationError:
        raise
    except (json.JSONDecodeError, TypeError) as exc:
        raise IsolationError("Issuer IAM policy must be valid strict JSON") from exc
    if not isinstance(policy, dict) or not isinstance(policy.get("bindings"), list):
        raise IsolationError("Issuer IAM policy bindings must be a list")
    bindings = policy["bindings"]
    if len(bindings) != 1 or not isinstance(bindings[0], dict):
        raise IsolationError("Issuer IAM policy must contain exactly one binding")
    binding = bindings[0]
    if binding.get("role") != "roles/run.invoker":
        raise IsolationError("Issuer IAM policy may contain only roles/run.invoker")
    if binding.get("condition") is not None:
        raise IsolationError("Issuer run.invoker binding must be unconditional")
    members = binding.get("members")
    expected = [f"serviceAccount:{owner_invoker_email(project)}"]
    if members != expected:
        raise IsolationError(
            "Issuer run.invoker must contain only the dedicated owner invoker"
        )


def live_issuer_policy(project: str, region: str) -> str:
    return _gcloud(
        "run",
        "services",
        "get-iam-policy",
        ISSUER_SERVICE,
        f"--project={project}",
        f"--region={region}",
        "--format=json",
    )


def build_probe_plan(
    project: str,
    region: str,
    project_number: str,
    *,
    include_issuer_resource: bool = True,
) -> list[tuple[str, str, str]]:
    issuer = (
        f"//run.googleapis.com/projects/{project}/locations/{region}/services/"
        f"{ISSUER_SERVICE}"
    )
    project_resource = f"//cloudresourcemanager.googleapis.com/projects/{project}"
    spend_bucket_resource = f"//storage.googleapis.com/projects/_/buckets/{SPEND_BUCKET}"
    probes: list[tuple[str, str, str]] = []
    if include_issuer_resource:
        probes.extend(
            [
                (issuer, "run.routes.invoke", "issuer invoke"),
                (issuer, "run.services.setIamPolicy", "issuer setIamPolicy"),
            ]
        )
    probes.extend([
        (
            project_resource,
            "resourcemanager.projects.setIamPolicy",
            "project setIamPolicy",
        ),
        (
            spend_bucket_resource,
            "storage.buckets.setIamPolicy",
            "replay bucket setIamPolicy",
        ),
        (spend_bucket_resource, "storage.buckets.update", "replay bucket update"),
        (spend_bucket_resource, "storage.buckets.delete", "replay bucket delete"),
        (spend_bucket_resource, "storage.objects.create", "replay object create"),
        (spend_bucket_resource, "storage.objects.delete", "replay object delete"),
        (spend_bucket_resource, "storage.objects.update", "replay object update"),
    ])
    for secret in (SIGNING_SECRET, KEY_ID_SECRET, *INSTAGRAM_SECRETS):
        secret_resource = (
            f"//secretmanager.googleapis.com/projects/{project_number}/secrets/{secret}"
        )
        for permission, label in (
            ("secretmanager.versions.access", "secret access"),
            ("secretmanager.versions.add", "secret version add"),
            ("secretmanager.versions.enable", "secret version enable"),
            ("secretmanager.versions.disable", "secret version disable"),
            ("secretmanager.versions.destroy", "secret version destroy"),
            ("secretmanager.secrets.update", "secret update"),
            ("secretmanager.secrets.delete", "secret delete"),
            ("secretmanager.secrets.setIamPolicy", "secret setIamPolicy"),
        ):
            probes.append((secret_resource, permission, f"{label} {secret}"))
    for email in protected_identities(project):
        resource = f"//iam.googleapis.com/projects/{project}/serviceAccounts/{email}"
        for permission, label in (
            ("iam.serviceAccounts.setIamPolicy", "service account setIamPolicy"),
            ("iam.serviceAccounts.actAs", "actAs"),
            ("iam.serviceAccounts.getAccessToken", "access token"),
            ("iam.serviceAccounts.getOpenIdToken", "OIDC token"),
            ("iam.serviceAccounts.implicitDelegation", "implicit delegation"),
            ("iam.serviceAccounts.signBlob", "sign blob"),
            ("iam.serviceAccounts.signJwt", "sign JWT"),
            ("iam.serviceAccountKeys.create", "service account key create"),
        ):
            probes.append((resource, permission, f"{label} {email}"))
    return probes
def mutation_runtime_probe_plan(
    project: str,
    region: str,
    project_number: str,
    build_identities: tuple[str, ...] = (),
    *,
    include_issuer_resource: bool = True,
) -> list[tuple[str, str, str]]:
    """Deny signer/issuer and build-identity escalation from the mutation runtime."""
    issuer = (
        f"//run.googleapis.com/projects/{project}/locations/{region}/services/"
        f"{ISSUER_SERVICE}"
    )
    project_resource = f"//cloudresourcemanager.googleapis.com/projects/{project}"
    spend_bucket_resource = f"//storage.googleapis.com/projects/_/buckets/{SPEND_BUCKET}"
    probes: list[tuple[str, str, str]] = []
    if include_issuer_resource:
        probes.extend(
            [
                (issuer, "run.routes.invoke", "mutation runtime issuer invoke"),
                (issuer, "run.services.setIamPolicy", "mutation runtime issuer setIamPolicy"),
            ]
        )
    probes.extend([
        (
            project_resource,
            "resourcemanager.projects.setIamPolicy",
            "mutation runtime project setIamPolicy",
        ),
        (
            spend_bucket_resource,
            "storage.buckets.setIamPolicy",
            "mutation runtime replay bucket setIamPolicy",
        ),
        (spend_bucket_resource, "storage.buckets.update", "mutation runtime replay bucket update"),
        (spend_bucket_resource, "storage.buckets.delete", "mutation runtime replay bucket delete"),
        (spend_bucket_resource, "storage.objects.delete", "mutation runtime replay object delete"),
        (spend_bucket_resource, "storage.objects.update", "mutation runtime replay object update"),
    ])
    protected_secrets = (SIGNING_SECRET, KEY_ID_SECRET)
    for secret in protected_secrets:
        resource = f"//secretmanager.googleapis.com/projects/{project_number}/secrets/{secret}"
        for permission, label in (
            ("secretmanager.versions.access", "secret access"),
            ("secretmanager.versions.add", "secret version add"),
            ("secretmanager.versions.enable", "secret version enable"),
            ("secretmanager.versions.disable", "secret version disable"),
            ("secretmanager.versions.destroy", "secret version destroy"),
            ("secretmanager.secrets.update", "secret update"),
            ("secretmanager.secrets.delete", "secret delete"),
            ("secretmanager.secrets.setIamPolicy", "secret setIamPolicy"),
        ):
            probes.append((resource, permission, f"mutation runtime {label} {secret}"))
    for secret in INSTAGRAM_SECRETS:
        resource = f"//secretmanager.googleapis.com/projects/{project_number}/secrets/{secret}"
        for permission, label in (
            ("secretmanager.versions.add", "Instagram secret version add"),
            ("secretmanager.versions.enable", "Instagram secret version enable"),
            ("secretmanager.versions.disable", "Instagram secret version disable"),
            ("secretmanager.versions.destroy", "Instagram secret version destroy"),
            ("secretmanager.secrets.update", "Instagram secret update"),
            ("secretmanager.secrets.delete", "Instagram secret delete"),
            ("secretmanager.secrets.setIamPolicy", "Instagram secret setIamPolicy"),
        ):
            probes.append((resource, permission, f"mutation runtime {label} {secret}"))
    credential_targets = tuple(
        dict.fromkeys(
            (
                signer_email(project),
                owner_invoker_email(project),
                default_compute_email(project_number),
                *build_identities,
            )
        )
    )
    for email in credential_targets:
        resource = f"//iam.googleapis.com/projects/{project}/serviceAccounts/{email}"
        for permission, label in (
            ("iam.serviceAccounts.setIamPolicy", "service account setIamPolicy"),
            ("iam.serviceAccounts.actAs", "actAs"),
            ("iam.serviceAccounts.getAccessToken", "access token"),
            ("iam.serviceAccounts.getOpenIdToken", "OIDC token"),
            ("iam.serviceAccounts.implicitDelegation", "implicit delegation"),
            ("iam.serviceAccounts.signBlob", "sign blob"),
            ("iam.serviceAccounts.signJwt", "sign JWT"),
            ("iam.serviceAccountKeys.create", "service account key create"),
        ):
            probes.append((resource, permission, f"mutation runtime {label} {email}"))
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


def troubleshoot_condition_args(resource: str, permission: str) -> tuple[str, ...]:
    """Add Cloud Storage object context without using an unsupported object fullResourceName."""
    spend_bucket_resource = f"//storage.googleapis.com/projects/_/buckets/{SPEND_BUCKET}"
    if resource == spend_bucket_resource and permission.startswith("storage.objects."):
        object_name = f"projects/_/buckets/{SPEND_BUCKET}/objects/spent/__isolation_probe__"
        return (
            f"--resource-name={object_name}",
            "--resource-service=storage.googleapis.com",
            "--resource-type=storage.googleapis.com/Object",
        )
    return ()


def _pace_troubleshooter() -> None:
    global _LAST_TROUBLESHOOT_STARTED
    now = time.monotonic()
    wait_for = TROUBLESHOOT_MIN_INTERVAL_SECONDS - (now - _LAST_TROUBLESHOOT_STARTED)
    if wait_for > 0:
        time.sleep(wait_for)
    _LAST_TROUBLESHOOT_STARTED = time.monotonic()


def live_troubleshoot(resource: str, principal: str, permission: str) -> tuple[str, str]:
    _pace_troubleshooter()
    output = _gcloud(
        "policy-intelligence",
        "troubleshoot-policy",
        "iam",
        resource,
        f"--principal-email={principal}",
        f"--permission={permission}",
        *troubleshoot_condition_args(resource, permission),
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
    issuer_policy_text: str | None = None,
    require_issuer_policy: bool = False,
    issuer_policy_reader: PolicyReader | None = None,
    include_issuer_resource: bool = True,
) -> tuple[str, int]:
    overrides = cloudbuild_service_accounts(
        cloudbuild_config.read_text(encoding="utf-8"), project
    )
    resolved = principal or parse_build_identity(
        _gcloud("builds", "get-default-service-account", f"--project={project}")
    )
    number = project_number or parse_project_number(
        _gcloud("projects", "describe", project, "--format=value(projectNumber)")
    )
    identities = list(dict.fromkeys([resolved, *overrides]))
    if not include_issuer_resource and (
        issuer_policy_text is not None or require_issuer_policy
    ):
        raise IsolationError(
            "issuer policy checks require an existing issuer resource"
        )
    if issuer_policy_text is not None:
        assert_issuer_invoker_policy(issuer_policy_text, project)
    elif require_issuer_policy:
        reader = issuer_policy_reader or live_issuer_policy
        assert_issuer_invoker_policy(reader(project, region), project)
    probe = troubleshoot or live_troubleshoot
    plan = build_probe_plan(
        project,
        region,
        number,
        include_issuer_resource=include_issuer_resource,
    )

    for identity in identities:
        if identity in protected_identities(project):
            raise IsolationError(
                "Cloud Build identity must be separate from signer/owner/mutation runtime"
            )
        for resource, permission, label in plan:
            require_denied(probe(resource, identity, permission), f"{identity} {label}")

    mutation_principal = mutation_runtime_email(project)
    mutation_plan = mutation_runtime_probe_plan(
        project,
        region,
        number,
        tuple(identities),
        include_issuer_resource=include_issuer_resource,
    )
    for resource, permission, label in mutation_plan:
        require_denied(
            probe(resource, mutation_principal, permission),
            f"{mutation_principal} {label}",
        )
    return resolved, len(plan) * len(identities) + len(mutation_plan)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail-closed vfigos Cloud Build identity isolation preflight"
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--cloudbuild-config", type=Path, required=True)
    parser.add_argument("--require-issuer-policy", action="store_true")
    parser.add_argument("--issuer-policy-only", action="store_true")
    parser.add_argument("--issuer-resource-absent", action="store_true")
    args = parser.parse_args()
    try:
        selected_modes = sum(
            bool(value)
            for value in (
                args.require_issuer_policy,
                args.issuer_policy_only,
                args.issuer_resource_absent,
            )
        )
        if selected_modes > 1:
            raise IsolationError(
                "issuer policy/resource modes are mutually exclusive"
            )
        if args.issuer_policy_only:
            assert_issuer_invoker_policy(
                live_issuer_policy(args.project, args.region), args.project
            )
            print("OK issuer-invoker-policy exact_owner_only=PASS")
            return 0
        principal, probes = assert_build_identity_isolated(
            args.project,
            args.region,
            args.cloudbuild_config,
            require_issuer_policy=args.require_issuer_policy,
            include_issuer_resource=not args.issuer_resource_absent,
        )
    except (IsolationError, OSError, subprocess.SubprocessError) as exc:
        print(f"BLOCKED build-isolation: {redact(str(exc))}")
        return 1
    print(f"OK build-isolation principal={principal} probes={probes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
