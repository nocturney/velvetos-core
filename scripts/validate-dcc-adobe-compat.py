#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEVTOOLS = ROOT / "packages" / "vfharness" / "devtools"
OVERLAYS = DEVTOOLS / "dcc-mcp-overlays.json"
BRIDGES = DEVTOOLS / "adobe-first-party-bridges.json"
PERSISTENCE = DEVTOOLS / "dcc-adobe-runtime-persistence.json"
SENTINEL_DIR = DEVTOOLS / "creative-tools" / "update-sentinel"
SENTINEL_CONFIG = SENTINEL_DIR / "dcc-adobe-update-sentinel.json"
SENTINEL_SCRIPT = SENTINEL_DIR / "Invoke-DccAdobeUpdateSentinel.ps1"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_hash(path: Path, expected: str, errors: list[str]) -> None:
    if not path.is_file():
        errors.append(f"missing file: {path.relative_to(ROOT)}")
        return
    actual = sha256(path)
    if actual.lower() != str(expected).lower():
        errors.append(f"sha256 mismatch: {path.relative_to(ROOT)} expected={expected} actual={actual}")


def main() -> int:
    errors: list[str] = []
    overlays = load_json(OVERLAYS)
    bridges = load_json(BRIDGES)
    persistence = load_json(PERSISTENCE)
    sentinel = load_json(SENTINEL_CONFIG)
    sentinel_text = SENTINEL_SCRIPT.read_text(encoding="utf-8-sig")
    sentinel_policy = sentinel.get("policy") or {}
    if sentinel.get("schema") != "velvetos.dcc-adobe.update-sentinel.v1":
        errors.append("update-sentinel: schema drift")
    expected_sentinel_policy = {
        "version_policy": "latest-compatible",
        "recovery_baseline_role": "drift-comparison-and-recovery-evidence-not-allowlist",
        "exact_version_match_required": False,
        "drift_action": "pending_validation_then_capability_probe",
        "available_requires": "typed_capability_probe_pass",
        "fail_closed": True,
        "auto_update": False,
        "auto_rollback": False,
        "auto_uninstall": False,
    }
    for key, expected in expected_sentinel_policy.items():
        if sentinel_policy.get(key) != expected:
            errors.append(f"update-sentinel: policy {key} expected={expected!r} actual={sentinel_policy.get(key)!r}")

    allowed_probe_kinds = {
        "streamable_registry",
        "standalone_cli",
        "adobe",
        "stdio",
        "corel_com",
        "fusion_native",
        "meshmixer_cli",
        "resolve_cli",
        "affinity_mcp",
    }
    integrated_hosts = [row for row in (sentinel.get("hosts") or []) if row.get("support") == "integrated"]
    if len(integrated_hosts) != 20:
        errors.append(f"update-sentinel: expected 20 integrated hosts, found {len(integrated_hosts)}")
    for host in integrated_hosts:
        host_id = str(host.get("id") or "<missing>")
        if "known_good_display_version" in host:
            errors.append(f"update-sentinel: {host_id} still uses known_good_display_version as an app-version concept")
        if not str(host.get("recovery_baseline_display_version") or "").strip():
            errors.append(f"update-sentinel: {host_id} missing recovery_baseline_display_version")
        probe_kind = str((host.get("probe") or {}).get("kind") or "")
        if probe_kind not in allowed_probe_kinds:
            errors.append(f"update-sentinel: {host_id} has missing/unsupported typed probe kind {probe_kind!r}")

    for required in (
        "classification=$(if($pass){'PASS_NEW_VERSION'}else{'NEEDS_COMPATIBILITY_REPAIR'})",
        "'PASS_COMPATIBILITY_CHECK'",
        "'pending_validation'",
        "'available'",
        "'post-update compatibility gate passed'",
        "'needs_compatibility_repair'",
        "version_policy='latest-compatible'",
        "recovery_baseline_role='drift-comparison-and-recovery-evidence-not-allowlist'",
        "exact_version_match_required=$false",
        "availability_basis='typed_capability_probe_pass'",
        "recovery baseline seeded after reviewed live capability evidence",
        "not an exact-version allowlist",
        "$probeProcessTimeout = $(if ([string]$probe.host -eq 'aftereffects')",
        "$stages.adobe_probe_process_timeout_seconds = $probeProcessTimeout",
        "$maxProbeAttempts = $(if ([string]$probe.host -eq 'aftereffects') { 1 } else { 2 })",
        "$stages.adobe_probe_max_attempts = $maxProbeAttempts",
    ):
        if required not in sentinel_text:
            errors.append(f"update-sentinel: missing Stage 6C contract fragment {required!r}")
    if "recovery_baseline_display_version" in sentinel_text:
        errors.append("update-sentinel: runtime gate must not compare routing against recovery display versions")
    if re.search(r"(?i)(invoke-expression|iex\s|powershell\s+-command\s+\$|cmd\.exe\s+/c\s+\$)", sentinel_text):
        errors.append("update-sentinel: arbitrary scripting escape hatch detected")

    overlay_ids: set[str] = set()
    for row in overlays.get("overlays") or []:
        overlay_id = str(row.get("id") or "")
        if not overlay_id:
            errors.append("overlay missing id")
            continue
        if overlay_id in overlay_ids:
            errors.append(f"duplicate overlay id: {overlay_id}")
        overlay_ids.add(overlay_id)
        patch = row.get("patch")
        expected = row.get("patch_sha256")
        if patch and expected:
            check_hash(ROOT / str(patch), str(expected), errors)

    record_ids: set[str] = set()
    for row in overlays.get("supporting_records") or []:
        record_id = str(row.get("id") or "")
        if not record_id:
            errors.append("supporting record missing id")
            continue
        if record_id in record_ids:
            errors.append(f"duplicate supporting record id: {record_id}")
        record_ids.add(record_id)
        record = row.get("record")
        expected = row.get("record_sha256")
        if record and expected:
            check_hash(ROOT / str(record), str(expected), errors)
        source_file = row.get("source_file")
        source_expected = row.get("source_sha256")
        if source_file or source_expected:
            if not source_file or not source_expected:
                errors.append(f"{record_id}: source_file/source_sha256 must be provided together")
            else:
                check_hash(ROOT / str(source_file), str(source_expected), errors)

    bridge_ids: set[str] = set()
    literal_secret = re.compile(r"""(?i)token\s*[:=]\s*["'][A-Za-z0-9_+/=-]{20,}["']""")
    for bridge in bridges.get("bridges") or []:
        bridge_id = str(bridge.get("id") or "")
        version = str(bridge.get("version") or "")
        if not bridge_id or not version:
            errors.append("bridge missing id/version")
            continue
        if bridge_id in bridge_ids:
            errors.append(f"duplicate bridge id: {bridge_id}")
        bridge_ids.add(bridge_id)

        source_dir = ROOT / str(bridge.get("source_dir") or "")
        if not source_dir.is_dir():
            errors.append(f"{bridge_id}: missing source_dir")
            continue
        if (source_dir / "adobepy.config.js").exists():
            errors.append(f"{bridge_id}: runtime secret config must not be committed")

        source_files = bridge.get("source_files") or {}
        for relative, expected in source_files.items():
            check_hash(source_dir / str(relative), str(expected), errors)

        manifest_path = source_dir / "manifest.json"
        main_path = source_dir / "main.js"
        if not manifest_path.is_file() or not main_path.is_file():
            continue
        manifest = load_json(manifest_path)
        main_text = main_path.read_text(encoding="utf-8")
        if str(manifest.get("version")) != version:
            errors.append(f"{bridge_id}: manifest version does not match registry")
        if manifest.get("id") != f"com.velvetos.{bridge_id}.bridge":
            errors.append(f"{bridge_id}: unexpected manifest id")
        if not re.search(r"""bridgeVersion\s*:\s*["']""" + re.escape(version) + r"""["']""", main_text):
            errors.append(f"{bridge_id}: main.js bridgeVersion does not match registry")
        permissions = manifest.get("requiredPermissions") or {}
        network = permissions.get("network") or {}
        if network.get("domains") != "all":
            errors.append(f"{bridge_id}: loopback broker network permission missing")
        if literal_secret.search(main_text):
            errors.append(f"{bridge_id}: literal token-like secret found in main.js")

        for candidate in source_dir.rglob("*"):
            if not candidate.is_file() or candidate.suffix.lower() not in {".js", ".json", ".html", ".md"}:
                continue
            if literal_secret.search(candidate.read_text(encoding="utf-8", errors="ignore")):
                errors.append(f"{bridge_id}: literal token-like secret found in {candidate.relative_to(source_dir)}")

        if bridge_id == "premiere":
            if version != "0.1.3":
                errors.append("premiere: canonical source must be 0.1.3")
            if "hostUIContext" in manifest or "hideFromMenu" in manifest:
                errors.append("premiere: 26.3.2 production source must not use invisible hideFromMenu route")
        if bridge_id == "photoshop":
            data = (manifest.get("host") or {}).get("data") or {}
            if data.get("loadEvent") != "startup":
                errors.append("photoshop: startup loadEvent missing")

    persistence_ids: set[str] = set()
    persistence_rows = persistence.get("files") or []
    persistence_text: dict[str, str] = {}
    for row in persistence_rows:
        runtime_id = str(row.get("id") or "")
        source = str(row.get("source") or "")
        expected = str(row.get("sha256") or "")
        if not runtime_id or not source or not expected:
            errors.append("runtime persistence row missing id/source/sha256")
            continue
        if runtime_id in persistence_ids:
            errors.append(f"duplicate runtime persistence id: {runtime_id}")
        persistence_ids.add(runtime_id)
        source_path = ROOT / source
        check_hash(source_path, expected, errors)
        if source_path.is_file():
            source_text = source_path.read_text(encoding="utf-8-sig", errors="ignore")
            persistence_text[runtime_id] = source_text
            if literal_secret.search(source_text):
                errors.append(f"{runtime_id}: literal token-like secret found in deployment source")

    gateway_text = persistence_text.get("dcc-gateway-wrapper", "")
    if gateway_text:
        if "$ErrorActionPreference = 'Continue'" not in gateway_text:
            errors.append("dcc-gateway-wrapper: native stderr compatibility guard missing")
        if "$ErrorActionPreference = $previousErrorActionPreference" not in gateway_text:
            errors.append("dcc-gateway-wrapper: ErrorActionPreference restore missing")
        if "--gateway-persist" not in gateway_text or "--port $Port" not in gateway_text:
            errors.append("dcc-gateway-wrapper: canonical gateway launch contract missing")

    photoshop_text = persistence_text.get("photoshop-broker-wrapper", "")
    if photoshop_text:
        if "--bind 127.0.0.1:47393" not in photoshop_text:
            errors.append("photoshop-broker-wrapper: canonical loopback broker binding missing")
        if "photoshop\\broker.token" not in photoshop_text:
            errors.append("photoshop-broker-wrapper: runtime token-file reference missing")

    desktop_text = persistence_text.get("dcc-desktop-host-wrapper", "")
    if desktop_text:
        for required in ("[switch]$HideAfterLaunch", "function Hide-App", "ShowWindow($proc.MainWindowHandle, 0)", "$OnlyAppId"):
            if required not in desktop_text:
                errors.append(f"dcc-desktop-host-wrapper: missing hidden on-demand contract fragment: {required}")

    manager_text = persistence_text.get("dcc-host-manager", "")
    if manager_text:
        for required in ("ValidateSet('start','stop','status')", "VelvetOS DCC OnDemand $AppId", "Stop-Process -Force"):
            if required not in manager_text:
                errors.append(f"dcc-host-manager: missing contract fragment: {required}")

    host_manifest_text = persistence_text.get("dcc-desktop-host-manifest", "")
    if host_manifest_text:
        try:
            host_manifest = json.loads(host_manifest_text.lstrip("﻿"))
        except json.JSONDecodeError as exc:
            errors.append(f"dcc-desktop-host-manifest: invalid JSON: {exc}")
        else:
            policy = host_manifest.get("policy") or {}
            if policy.get("launch_mode") != "on_demand_hidden":
                errors.append("dcc-desktop-host-manifest: launch_mode must be on_demand_hidden")
            if policy.get("launch_at_logon") is not False:
                errors.append("dcc-desktop-host-manifest: launch_at_logon must be false")
            if policy.get("agent_hidden_launch") is not True:
                errors.append("dcc-desktop-host-manifest: agent_hidden_launch must be true")

    installer_text = persistence_text.get("reboot-persistence-installer", "")
    if installer_text:
        for required in (
            "VelvetOS DCC Gateway",
            "New-ScheduledTaskTrigger -AtStartup",
            "VelvetOS AdobePy Broker Photoshop",
            "New-ScheduledTaskTrigger -AtLogOn -User $InteractiveUser",
            "New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount",
            "New-ScheduledTaskPrincipal -UserId $InteractiveUser -LogonType Interactive",
            "VelvetOS DCC Desktop Hosts",
            "Get-OnDemandTaskName",
            "-HideAfterLaunch",
            "$ObsoleteTasks",
        ):
            if required not in installer_text:
                errors.append(f"reboot-persistence-installer: missing contract fragment: {required}")

        if installer_text.count("New-ScheduledTaskTrigger -AtLogOn -User $InteractiveUser") != 1:
            errors.append("reboot-persistence-installer: AtLogOn trigger must be limited to the background Photoshop broker")

    if errors:
        for error in errors:
            print("DCC/ADOBE COMPAT FAIL: " + error, file=sys.stderr)
        return 1
    print(
        f"DCC/ADOBE COMPAT PASS overlays={len(overlay_ids)} "
        f"records={len(record_ids)} bridges={len(bridge_ids)} runtime_files={len(persistence_ids)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
