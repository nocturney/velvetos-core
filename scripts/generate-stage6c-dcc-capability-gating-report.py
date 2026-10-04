#!/usr/bin/env python3
"""Generate Reform v2 Stage 6C DCC latest-compatible capability-gating evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "packages" / "vfharness" / "devtools" / "creative-tools" / "update-sentinel" / "dcc-adobe-update-sentinel.json"
SENTINEL = ROOT / "packages" / "vfharness" / "devtools" / "creative-tools" / "update-sentinel" / "Invoke-DccAdobeUpdateSentinel.ps1"
ADOBE_PROBE = ROOT / "packages" / "vfharness" / "devtools" / "creative-tools" / "update-sentinel" / "adobe_readonly_probe.py"
VALIDATOR = ROOT / "scripts" / "validate-dcc-adobe-compat.py"
POLICY = ROOT / "packages" / "velvetos" / "policy" / "policy-registry.json"
OUT = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage6c-dcc-capability-gating.json"


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_bytes(ref: str, rel: str) -> bytes:
    proc = subprocess.run(
        ["git", "show", f"{ref}:{rel}"],
        cwd=ROOT,
        capture_output=True,
        timeout=30,
    )
    if proc.returncode != 0:
        raise SystemExit(f"cannot read {rel} at {ref}: {proc.stderr.decode(errors='replace').strip()}")
    return proc.stdout


def version_tuple(value: str) -> tuple[int, ...]:
    match = re.search(r"(\d+(?:\.\d+)+)", value or "")
    if not match:
        return ()
    return tuple(int(part) for part in match.group(1).split("."))


def host(config: dict[str, Any], host_id: str) -> dict[str, Any]:
    for row in config.get("hosts") or []:
        if row.get("id") == host_id:
            return row
    raise SystemExit(f"host missing from update-sentinel config: {host_id}")


def run_validator() -> tuple[bool, str]:
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )
    output = (proc.stdout.strip() or proc.stderr.strip())
    return proc.returncode == 0, output


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-against", required=True)
    ap.add_argument("--captured-at", required=True)
    ap.add_argument("--illustrator-receipt-sha256", required=True)
    ap.add_argument("--illustrator-version", required=True)
    ap.add_argument("--illustrator-classification", required=True)
    ap.add_argument("--illustrator-routing-status", required=True)
    ap.add_argument("--aftereffects-receipt-sha256", required=True)
    ap.add_argument("--aftereffects-version", required=True)
    ap.add_argument("--aftereffects-classification", required=True)
    ap.add_argument("--aftereffects-routing-status", required=True)
    ap.add_argument("--aftereffects-probe-timeout", type=int, required=True)
    ap.add_argument("--aftereffects-max-attempts", type=int, required=True)
    ap.add_argument("--aftereffects-attempts", type=int, required=True)
    ap.add_argument("--aftereffects-probe-status", required=True)
    ap.add_argument("--aftereffects-transport", required=True)
    ap.add_argument("--aftereffects-operations", required=True)
    ap.add_argument("--premiere-receipt-sha256", required=True)
    ap.add_argument("--premiere-classification", required=True)
    ap.add_argument("--premiere-routing-status", required=True)
    ap.add_argument("--photoshop-receipt-sha256", required=True)
    ap.add_argument("--photoshop-classification", required=True)
    ap.add_argument("--photoshop-routing-status", required=True)
    ap.add_argument("--runtime-sentinel-sha256", required=True)
    ap.add_argument("--runtime-config-sha256", required=True)
    ap.add_argument("--runtime-adobe-probe-sha256", required=True)
    ap.add_argument("--ccc-server-sha256", required=True)
    ap.add_argument("--ccc-app-sha256", required=True)
    ap.add_argument("--ccc-i18n-sha256", required=True)
    ap.add_argument("--ccc-aftereffects-route-status", required=True)
    ap.add_argument("--ccc-aftereffects-display-status", required=True)
    ap.add_argument("--ccc-recovery-baseline-version", required=True)
    ap.add_argument("--ccc-recovery-baseline-role", required=True)
    ap.add_argument("--ccc-version-policy", required=True)
    ap.add_argument("--ccc-availability-basis", required=True)
    ap.add_argument("--ccc-repair-guard-http-status", type=int, required=True)
    ap.add_argument("--output", type=Path, default=OUT)
    ns = ap.parse_args()
    if len(ns.prepared_against) != 40:
        ap.error("--prepared-against must be a full Git SHA")

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    policy = config.get("policy") or {}
    illustrator = host(config, "illustrator")
    aftereffects = host(config, "aftereffects")

    validator_pass, validator_output = run_validator()
    before_policy = git_bytes(ns.prepared_against, "packages/velvetos/policy/policy-registry.json")
    current_policy = POLICY.read_bytes()
    policy_unchanged = sha_bytes(before_policy) == sha_bytes(current_policy)

    sentinel_bytes = SENTINEL.read_bytes()
    config_bytes = CONFIG.read_bytes()
    adobe_probe_bytes = ADOBE_PROBE.read_bytes()
    sentinel_text = sentinel_bytes.decode("utf-8-sig")
    adobe_probe_text = adobe_probe_bytes.decode("utf-8-sig")
    source_sentinel_sha = sha_bytes(sentinel_bytes)
    source_config_sha = sha_bytes(config_bytes)
    source_adobe_probe_sha = sha_bytes(adobe_probe_bytes)

    version_policy_pass = (
        policy.get("version_policy") == "latest-compatible"
        and policy.get("recovery_baseline_role") == "drift-comparison-and-recovery-evidence-not-allowlist"
        and policy.get("exact_version_match_required") is False
        and policy.get("drift_action") == "pending_validation_then_capability_probe"
        and policy.get("available_requires") == "typed_capability_probe_pass"
        and policy.get("fail_closed") is True
    )
    destructive_actions_disabled = all(
        policy.get(key) is False for key in ("auto_update", "auto_rollback", "auto_uninstall")
    )

    illustrator_newer = version_tuple(ns.illustrator_version) > version_tuple(
        illustrator.get("recovery_baseline_display_version", "")
    )
    illustrator_pass = (
        ns.illustrator_classification == "PASS_COMPATIBILITY_CHECK"
        and ns.illustrator_routing_status == "available"
        and illustrator_newer
    )
    aftereffects_newer = version_tuple(ns.aftereffects_version) > version_tuple(
        aftereffects.get("recovery_baseline_display_version", "")
    )
    aftereffects_operations = [
        item.strip() for item in ns.aftereffects_operations.split(",") if item.strip()
    ]
    aftereffects_pass = (
        ns.aftereffects_classification == "PASS_COMPATIBILITY_CHECK"
        and ns.aftereffects_routing_status == "available"
        and aftereffects_newer
        and ns.aftereffects_probe_status == "PASS"
        and ns.aftereffects_transport == "adobepy-cep-typed-readonly"
        and aftereffects_operations == ["app.getVersion", "project.getActive"]
        and ns.aftereffects_max_attempts == 1
        and ns.aftereffects_attempts == 1
        and ns.aftereffects_probe_timeout >= 120
    )
    shared_adobe_regressions_pass = (
        ns.premiere_classification == "PASS_COMPATIBILITY_CHECK"
        and ns.premiere_routing_status == "available"
        and ns.photoshop_classification == "PASS_COMPATIBILITY_CHECK"
        and ns.photoshop_routing_status == "available"
    )
    creative_control_center_receipt_pass = (
        ns.ccc_aftereffects_route_status == "available"
        and ns.ccc_aftereffects_display_status == "available"
        and ns.ccc_recovery_baseline_version == "After Effects 26.3"
        and ns.ccc_recovery_baseline_role == "drift-comparison-and-recovery-evidence-not-allowlist"
        and ns.ccc_version_policy == "latest-compatible"
        and ns.ccc_availability_basis == "typed_capability_probe_pass"
        and ns.ccc_repair_guard_http_status == 409
        and all(
            re.fullmatch(r"[0-9A-Fa-f]{64}", value or "")
            for value in (ns.ccc_server_sha256, ns.ccc_app_sha256, ns.ccc_i18n_sha256)
        )
    )

    source_runtime_parity = (
        source_sentinel_sha.lower() == ns.runtime_sentinel_sha256.lower()
        and source_config_sha.lower() == ns.runtime_config_sha256.lower()
        and source_adobe_probe_sha.lower() == ns.runtime_adobe_probe_sha256.lower()
    )
    no_experimental_escape = (
        "Invoke-AfterEffectsIsolatedReadonlyProbe" not in sentinel_text
        and "aftereffects_isolated_read_probe" not in sentinel_text
        and "Invoke-AfterEffectsReadonly.ps1" not in adobe_probe_text
        and "aftereffects_bounded_snapshot" not in adobe_probe_text
        and 'client.call("after-effects", "raw"' not in adobe_probe_text
        and (aftereffects.get("probe") or {}).get("kind") == "adobe"
        and (illustrator.get("probe") or {}).get("kind") == "standalone_cli"
    )

    acceptance = {
        "version_policy_is_latest_compatible": version_policy_pass,
        "recovery_baseline_is_not_allowlist": policy.get("recovery_baseline_role") == "drift-comparison-and-recovery-evidence-not-allowlist",
        "exact_version_match_is_not_required": policy.get("exact_version_match_required") is False,
        "drift_routes_to_capability_probe": policy.get("drift_action") == "pending_validation_then_capability_probe",
        "available_requires_typed_capability_probe_pass": policy.get("available_requires") == "typed_capability_probe_pass",
        "illustrator_newer_than_recovery_baseline_passes_typed_probe": illustrator_pass,
        "aftereffects_newer_than_recovery_baseline_passes_typed_probe": aftereffects_pass,
        "shared_adobe_regressions_pass": shared_adobe_regressions_pass,
        "creative_control_center_runtime_receipt_pass": creative_control_center_receipt_pass,
        "source_runtime_parity_proven": source_runtime_parity,
        "dcc_adobe_validator_passes": validator_pass,
        "no_experimental_or_arbitrary_script_escape_is_wired": no_experimental_escape,
        "destructive_or_update_auto_actions_remain_disabled": destructive_actions_disabled,
        "external_effect_policy_registry_unchanged": policy_unchanged,
    }

    report = {
        "schema": "velvetos.stage6c-dcc-capability-gating.v1",
        "stage": "6C",
        "behavior_change": True,
        "prepared_against_main_sha": ns.prepared_against,
        "captured_at": ns.captured_at,
        "policy": {
            "version_policy": policy.get("version_policy"),
            "recovery_baseline_role": policy.get("recovery_baseline_role"),
            "exact_version_match_required": policy.get("exact_version_match_required"),
            "drift_action": policy.get("drift_action"),
            "available_requires": policy.get("available_requires"),
            "fail_closed": policy.get("fail_closed"),
            "auto_update": policy.get("auto_update"),
            "auto_rollback": policy.get("auto_rollback"),
            "auto_uninstall": policy.get("auto_uninstall"),
        },
        "live_evidence": {
            "illustrator": {
                "installed_version": ns.illustrator_version,
                "recovery_baseline": illustrator.get("recovery_baseline_display_version"),
                "classification": ns.illustrator_classification,
                "routing_status": ns.illustrator_routing_status,
                "receipt_sha256": ns.illustrator_receipt_sha256.upper(),
                "newer_than_recovery_baseline": illustrator_newer,
            },
            "aftereffects": {
                "installed_version": ns.aftereffects_version,
                "recovery_baseline": aftereffects.get("recovery_baseline_display_version"),
                "classification": ns.aftereffects_classification,
                "routing_status": ns.aftereffects_routing_status,
                "receipt_sha256": ns.aftereffects_receipt_sha256.upper(),
                "newer_than_recovery_baseline": aftereffects_newer,
                "probe_timeout_seconds": ns.aftereffects_probe_timeout,
                "max_probe_attempts": ns.aftereffects_max_attempts,
                "probe_attempts": ns.aftereffects_attempts,
                "probe_status": ns.aftereffects_probe_status,
                "transport": ns.aftereffects_transport,
                "operations": aftereffects_operations,
                "final_result": "typed_capability_pass",
            },
            "premiere_regression": {
                "classification": ns.premiere_classification,
                "routing_status": ns.premiere_routing_status,
                "receipt_sha256": ns.premiere_receipt_sha256.upper(),
            },
            "photoshop_regression": {
                "classification": ns.photoshop_classification,
                "routing_status": ns.photoshop_routing_status,
                "receipt_sha256": ns.photoshop_receipt_sha256.upper(),
            },
        },
        "creative_control_center_runtime_receipt": {
            "mode": "source-controlled-receipt-local-runtime-not-authority",
            "runtime_root": r"D:\Velvet\Projects\CreativeControlCenter",
            "files": {
                "server.mjs": ns.ccc_server_sha256.upper(),
                "public/app.js": ns.ccc_app_sha256.upper(),
                "public/i18n.js": ns.ccc_i18n_sha256.upper(),
            },
            "aftereffects_live_api": {
                "route_status": ns.ccc_aftereffects_route_status,
                "display_status": ns.ccc_aftereffects_display_status,
                "recovery_baseline_version": ns.ccc_recovery_baseline_version,
                "recovery_baseline_role": ns.ccc_recovery_baseline_role,
                "version_policy": ns.ccc_version_policy,
                "availability_basis": ns.ccc_availability_basis,
                "repair_request_guard_http_status": ns.ccc_repair_guard_http_status,
            },
            "runtime_authority": False,
        },
        "source_runtime_parity": {
            "sentinel_source_sha256": source_sentinel_sha.upper(),
            "sentinel_runtime_sha256": ns.runtime_sentinel_sha256.upper(),
            "config_source_sha256": source_config_sha.upper(),
            "config_runtime_sha256": ns.runtime_config_sha256.upper(),
            "adobe_probe_source_sha256": source_adobe_probe_sha.upper(),
            "adobe_probe_runtime_sha256": ns.runtime_adobe_probe_sha256.upper(),
            "pass": source_runtime_parity,
        },
        "validator": {
            "path": "scripts/validate-dcc-adobe-compat.py",
            "pass": validator_pass,
            "output": validator_output,
        },
        "authorization_semantics": {
            "entry_policy_registry_sha256": sha_bytes(before_policy),
            "current_policy_registry_sha256": sha_bytes(current_policy),
            "external_effect_policy_registry_unchanged": policy_unchanged,
            "update_sentinel_is_external_effect_authority": False,
            "recovery_baseline_is_authority": False,
        },
        "acceptance": acceptance,
        "repository_acceptance": "PASS" if all(acceptance.values()) else "FAIL",
    }

    out = ns.output if ns.output.is_absolute() else ROOT / ns.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(
        "STAGE6C_DCC_CAPABILITY "
        f"acceptance={report['repository_acceptance']} "
        f"criteria={sum(1 for value in acceptance.values() if value)}/{len(acceptance)} "
        f"illustrator={ns.illustrator_classification} "
        f"aftereffects={ns.aftereffects_classification} "
        f"parity={source_runtime_parity} validator={validator_pass}"
    )
    return 0 if report["repository_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
