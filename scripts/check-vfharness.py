#!/usr/bin/env python3
"""Validate the six-layer VF harness against AGENTS.md and existing packs. No network. No send."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYERS = ROOT / "packages" / "vfharness" / "layers.json"
MANIFEST = ROOT / "packages" / "manifest.json"
AGENTS = ROOT / "packages" / "vfharness" / "AGENTS.md"
CONSTITUTION = ROOT / "constitution" / "CONSTITUTION.md"
PERMISSIONS = ROOT / "packages" / "vfharness" / "PERMISSIONS.md"
STAGE5B_REPORT = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage5b-harness-consolidation.json"
STAGE5B_GENERATOR = ROOT / "scripts" / "generate-stage5b-harness-consolidation-report.py"
STAGE6C_REPORT = ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage6c-dcc-capability-gating.json"
STAGE6C_GENERATOR = ROOT / "scripts" / "generate-stage6c-dcc-capability-gating-report.py"
DCC_ADOBE_VALIDATOR = ROOT / "scripts" / "validate-dcc-adobe-compat.py"
ALLOWED_LAYER_NAMES = {
    "guides",
    "sensors",
    "loop",
    "memory",
    "permissions",
    "observability",
}
REQUIRED_LOCKS = {
    "hq-send-via-tools",
    "no-auto-dm",
    "no-boost",
    "no-invented-prices",
    "no-invented-insights",
    "no-second-runtime",
    "no-core-as-nervous-runtime",
    "human-gate-money-send",
}
AGENTS_NEEDLES = (
    "PROJECT:",
    "TEST:",
    "LINT:",
    "RULES",
    "ANTI-PATTERNS",
    "send_message",
    "X ₪",
    "python3 scripts/check-all.py",
)
CHECKPOINT_REQUIRED = {
    "task_id",
    "status",
    "pack",
    "completed_steps",
    "next_step",
    "artifacts",
    "unresolved",
    "last_updated",
}


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not LAYERS.is_file():
        fail(f"missing {LAYERS.relative_to(ROOT)}")
    if not MANIFEST.is_file():
        fail(f"missing {MANIFEST.relative_to(ROOT)}")
    if not AGENTS.is_file():
        fail("missing AGENTS.md (layer 1 guide)")
    if not CONSTITUTION.is_file() or not PERMISSIONS.is_file():
        fail("missing canonical constitution/permissions surface")
    for path in (STAGE5B_REPORT, STAGE5B_GENERATOR, STAGE6C_REPORT, STAGE6C_GENERATOR, DCC_ADOBE_VALIDATOR):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    spec = json.loads(LAYERS.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    pack_names = {p["name"] for p in manifest.get("packs", [])}
    agents_text = AGENTS.read_text(encoding="utf-8")
    constitution_text = CONSTITUTION.read_text(encoding="utf-8")
    permissions_text = PERMISSIONS.read_text(encoding="utf-8")

    for needle in (
        "Standing implementation authorization — Git delivery",
        "אין לבקש מהבעלים אישור נוסף רק עבור push או merge",
        "force-push",
        "branch protection",
    ):
        if needle not in constitution_text:
            fail(f"constitution missing Git delivery authority marker {needle!r}")
    for needle in (
        "ALLOW git delivery",
        "owner already approved the implementation scope",
        "Push / PR / Merge",
        "ללא force-push",
    ):
        if needle not in permissions_text:
            fail(f"PERMISSIONS.md missing Git delivery authority marker {needle!r}")
    if "ASK before: git push" in permissions_text:
        fail("PERMISSIONS.md reintroduced redundant owner approval for git push")

    if spec.get("name") != "vfharness":
        fail("layers.json name must be vfharness")
    if "existing packs" not in (spec.get("rule") or ""):
        fail("layers.json rule must say embed onto existing packs")
    if spec.get("formula") != "Agent = Model + Harness":
        fail("layers.json missing formula")

    locks = set(spec.get("locks") or [])
    for need in REQUIRED_LOCKS:
        if need not in locks:
            fail(f"missing lock {need}")

    layers = spec.get("layers") or []
    if len(layers) != 6:
        fail(f"expected 6 layers, got {len(layers)}")
    names = [row.get("name") for row in layers]
    if set(names) != ALLOWED_LAYER_NAMES:
        fail(f"layer names {names} != {sorted(ALLOWED_LAYER_NAMES)}")
    ids = [row.get("id") for row in layers]
    if ids != [1, 2, 3, 4, 5, 6]:
        fail(f"layer ids must be 1..6, got {ids}")

    for row in layers:
        files = row.get("files") or []
        if not files:
            fail(f"layer {row.get('name')} has no files")
        for rel in files:
            path = ROOT / rel
            if not path.is_file():
                fail(f"layer {row.get('name')} missing {rel}")

    for needle in AGENTS_NEEDLES:
        if needle not in agents_text:
            fail(f"AGENTS.md missing {needle!r}")

    deny = spec.get("permissions", {}).get("deny") or []
    for need in ("instagram:boost", "auto-dm", "invented-ils"):
        if need not in deny:
            fail(f"permissions.deny missing {need}")
    for banned in ("gmail:send_message", "gmail:reply", "gmail:forward", "instagram:send"):
        if banned in deny:
            fail(f"permissions.deny must not block HQ send tool {banned}")

    sensors = spec.get("sensors") or []
    if len(sensors) < 5:
        fail(f"expected at least 5 sensors, got {len(sensors)}")
    for sensor in sensors:
        rel = sensor.get("script")
        if not rel:
            fail(f"sensor {sensor.get('id')} missing script")
        if not (ROOT / rel).is_file():
            fail(f"sensor script missing {rel}")
        if sensor.get("type") != "computational":
            fail(f"sensor {sensor.get('id')} must be computational")

    loop = spec.get("loop") or {}
    if int(loop.get("maxRetries") or 0) < 1:
        fail("loop.maxRetries must be >= 1")
    if loop.get("stoppingCondition") != "best-artifact-plus-unresolved":
        fail("loop must return best artifact plus unresolved")

    execution = spec.get("executionContract") or {}
    if execution.get("canonical") != "packages/vfharness/LOOP.md":
        fail("executionContract canonical path must be packages/vfharness/LOOP.md")
    if execution.get("state") != "packages/vfharness/playbooks/skillstate.md":
        fail("executionContract state path drift")
    if execution.get("secondaryMode") != "pointer_only" or execution.get("secondOrchestrator") != "FORBIDDEN":
        fail("executionContract must stay pointer-only with second orchestrator forbidden")
    expected_handoff = ["office/control/HANDOFF.json", "packages/vfmem/HANDOFF.md"]
    if execution.get("crossToolHandoff") != expected_handoff:
        fail("executionContract cross-tool handoff drift")
    canonical_path = ROOT / execution["canonical"]
    if not canonical_path.is_file():
        fail("canonical LOOP.md missing")
    canonical_text = canonical_path.read_text(encoding="utf-8")
    for needle in ("Canonical execution contract", "retry(step, budget=2)", "fallback(step)", "downgrade_scope(step)", "safe ruling", "skillstate.md", "office/control/HANDOFF.json", "packages/vfmem/HANDOFF.md"):
        if needle not in canonical_text:
            fail(f"canonical LOOP.md missing {needle!r}")
    secondary = execution.get("secondarySurfaces") or []
    if len(secondary) != 5 or len(secondary) != len(set(secondary)):
        fail("executionContract secondary surfaces must contain five unique active pointers")
    duplicate_signatures = ("retry → fallback → downgrade", "retry(step, budget=2)", "downgrade_scope(step)")
    for rel in secondary:
        path = ROOT / rel
        if not path.is_file():
            fail(f"executionContract secondary surface missing {rel}")
        body = path.read_text(encoding="utf-8")
        if "LOOP.md" not in body:
            fail(f"secondary harness surface must point to LOOP.md: {rel}")
        for signature in duplicate_signatures:
            if signature in body:
                fail(f"secondary harness surface restates canonical loop via {signature!r}: {rel}")
    for rel in expected_handoff:
        if not (ROOT / rel).is_file():
            fail(f"cross-tool handoff artifact missing {rel}")

    stage5b = json.loads(STAGE5B_REPORT.read_text(encoding="utf-8"))
    if stage5b.get("schema") != "velvetos.stage5b-harness-consolidation.v1" or stage5b.get("stage") != "5B":
        fail("Stage 5B report schema/stage drift")
    if stage5b.get("prepared_against_main_sha") != "daf5092fbf3a4de9bbaa1623a68efe9b24b8a3b5":
        fail("Stage 5B base SHA drift")
    if stage5b.get("repository_acceptance") != "PASS":
        fail("Stage 5B repository acceptance is not PASS")
    before5b = stage5b.get("before") or {}
    after5b = stage5b.get("after") or {}
    if before5b.get("secondary_restating_count") != 1 or before5b.get("secondary_pointer_count") != 3:
        fail("Stage 5B before snapshot drift")
    if after5b.get("secondary_restating_count") != 0 or after5b.get("secondary_pointer_count") != 5:
        fail("Stage 5B after snapshot drift")
    if after5b.get("secondary_restating_surfaces") != []:
        fail("Stage 5B secondary surface still restates global loop")
    acceptance5b = stage5b.get("acceptance") or {}
    if not acceptance5b or not all(value is True for value in acceptance5b.values()):
        fail("Stage 5B acceptance criteria drift")
    scope5b = stage5b.get("scope") or {}
    if scope5b.get("historical_state_modified") is not False or scope5b.get("specialized_playbooks_removed") is not False or scope5b.get("second_orchestrator_created") is not False:
        fail("Stage 5B consolidation scope drift")
    with tempfile.TemporaryDirectory(prefix="stage5b-harness-") as td:
        regenerated = Path(td) / "stage5b.json"
        proc = subprocess.run(
            [
                sys.executable, str(STAGE5B_GENERATOR),
                "--prepared-against", stage5b["prepared_against_main_sha"],
                "--captured-at", stage5b["captured_at"],
                "--output", str(regenerated),
            ],
            cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace", timeout=90,
        )
        if proc.returncode != 0:
            fail("Stage 5B report regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()))
        if regenerated.read_bytes() != STAGE5B_REPORT.read_bytes():
            fail("Stage 5B report is not reproducible")

    stage6c = json.loads(STAGE6C_REPORT.read_text(encoding="utf-8"))
    if stage6c.get("schema") != "velvetos.stage6c-dcc-capability-gating.v1" or stage6c.get("stage") != "6C":
        fail("Stage 6C report schema/stage drift")
    if stage6c.get("prepared_against_main_sha") != "64425e329320ea20c7446860c1ff9548918c3744":
        fail("Stage 6C entry SHA drift")
    if stage6c.get("repository_acceptance") != "PASS":
        fail("Stage 6C repository acceptance is not PASS")
    acceptance6c = stage6c.get("acceptance") or {}
    if not acceptance6c or not all(value is True for value in acceptance6c.values()):
        fail("Stage 6C acceptance criteria drift")
    live6c = stage6c.get("live_evidence") or {}
    illustrator6c = live6c.get("illustrator") or {}
    aftereffects6c = live6c.get("aftereffects") or {}
    if (
        illustrator6c.get("classification") != "PASS_COMPATIBILITY_CHECK"
        or illustrator6c.get("routing_status") != "available"
        or illustrator6c.get("newer_than_recovery_baseline") is not True
    ):
        fail("Stage 6C Illustrator newer-version proof drift")
    if (
        aftereffects6c.get("classification") != "PASS_COMPATIBILITY_CHECK"
        or aftereffects6c.get("routing_status") != "available"
        or aftereffects6c.get("newer_than_recovery_baseline") is not True
        or aftereffects6c.get("probe_status") != "PASS"
        or aftereffects6c.get("transport") != "adobepy-cep-typed-readonly"
        or aftereffects6c.get("operations") != ["app.getVersion", "project.getActive"]
        or aftereffects6c.get("final_result") != "typed_capability_pass"
    ):
        fail("Stage 6C After Effects typed capability proof drift")
    premiere6c = live6c.get("premiere_regression") or {}
    photoshop6c = live6c.get("photoshop_regression") or {}
    if (
        premiere6c.get("classification") != "PASS_COMPATIBILITY_CHECK"
        or premiere6c.get("routing_status") != "available"
        or photoshop6c.get("classification") != "PASS_COMPATIBILITY_CHECK"
        or photoshop6c.get("routing_status") != "available"
    ):
        fail("Stage 6C shared Adobe regression proof drift")
    ccc6c = stage6c.get("creative_control_center_runtime_receipt") or {}
    ccc_files6c = ccc6c.get("files") or {}
    ccc_ae6c = ccc6c.get("aftereffects_live_api") or {}
    if (
        ccc6c.get("mode") != "source-controlled-receipt-local-runtime-not-authority"
        or ccc6c.get("runtime_authority") is not False
        or set(ccc_files6c) != {"server.mjs", "public/app.js", "public/i18n.js"}
        or any(re.fullmatch(r"[0-9A-F]{64}", str(value or "")) is None for value in ccc_files6c.values())
        or ccc_ae6c.get("route_status") != "available"
        or ccc_ae6c.get("display_status") != "available"
        or ccc_ae6c.get("recovery_baseline_version") != "After Effects 26.3"
        or ccc_ae6c.get("recovery_baseline_role") != "drift-comparison-and-recovery-evidence-not-allowlist"
        or ccc_ae6c.get("version_policy") != "latest-compatible"
        or ccc_ae6c.get("availability_basis") != "typed_capability_probe_pass"
        or ccc_ae6c.get("repair_request_guard_http_status") != 409
    ):
        fail("Stage 6C Creative Control Center runtime receipt drift")
    if not (stage6c.get("validator") or {}).get("pass"):
        fail("Stage 6C DCC/Adobe validator evidence is not PASS")
    parity6c = stage6c.get("source_runtime_parity") or {}
    if parity6c.get("pass") is not True:
        fail("Stage 6C source/runtime parity evidence is not PASS")
    with tempfile.TemporaryDirectory(prefix="stage6c-dcc-") as td:
        regenerated6c = Path(td) / "stage6c.json"
        proc = subprocess.run(
            [
                sys.executable, str(STAGE6C_GENERATOR),
                "--prepared-against", stage6c["prepared_against_main_sha"],
                "--captured-at", stage6c["captured_at"],
                "--illustrator-receipt-sha256", illustrator6c["receipt_sha256"],
                "--illustrator-version", illustrator6c["installed_version"],
                "--illustrator-classification", illustrator6c["classification"],
                "--illustrator-routing-status", illustrator6c["routing_status"],
                "--aftereffects-receipt-sha256", aftereffects6c["receipt_sha256"],
                "--aftereffects-version", aftereffects6c["installed_version"],
                "--aftereffects-classification", aftereffects6c["classification"],
                "--aftereffects-routing-status", aftereffects6c["routing_status"],
                "--aftereffects-probe-timeout", str(aftereffects6c["probe_timeout_seconds"]),
                "--aftereffects-max-attempts", str(aftereffects6c["max_probe_attempts"]),
                "--aftereffects-attempts", str(aftereffects6c["probe_attempts"]),
                "--aftereffects-probe-status", aftereffects6c["probe_status"],
                "--aftereffects-transport", aftereffects6c["transport"],
                "--aftereffects-operations", ",".join(aftereffects6c["operations"]),
                "--premiere-receipt-sha256", premiere6c["receipt_sha256"],
                "--premiere-classification", premiere6c["classification"],
                "--premiere-routing-status", premiere6c["routing_status"],
                "--photoshop-receipt-sha256", photoshop6c["receipt_sha256"],
                "--photoshop-classification", photoshop6c["classification"],
                "--photoshop-routing-status", photoshop6c["routing_status"],
                "--runtime-sentinel-sha256", parity6c["sentinel_runtime_sha256"],
                "--runtime-config-sha256", parity6c["config_runtime_sha256"],
                "--runtime-adobe-probe-sha256", parity6c["adobe_probe_runtime_sha256"],
                "--ccc-server-sha256", ccc_files6c["server.mjs"],
                "--ccc-app-sha256", ccc_files6c["public/app.js"],
                "--ccc-i18n-sha256", ccc_files6c["public/i18n.js"],
                "--ccc-aftereffects-route-status", ccc_ae6c["route_status"],
                "--ccc-aftereffects-display-status", ccc_ae6c["display_status"],
                "--ccc-recovery-baseline-version", ccc_ae6c["recovery_baseline_version"],
                "--ccc-recovery-baseline-role", ccc_ae6c["recovery_baseline_role"],
                "--ccc-version-policy", ccc_ae6c["version_policy"],
                "--ccc-availability-basis", ccc_ae6c["availability_basis"],
                "--ccc-repair-guard-http-status", str(ccc_ae6c["repair_request_guard_http_status"]),
                "--output", str(regenerated6c),
            ],
            cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace", timeout=180,
        )
        if proc.returncode != 0:
            fail("Stage 6C report regeneration failed: " + (proc.stderr.strip() or proc.stdout.strip()))
        if regenerated6c.read_bytes() != STAGE6C_REPORT.read_bytes():
            fail("Stage 6C report is not reproducible")

    schema_path = ROOT / "packages/vfharness/templates/checkpoint.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    required = set(schema.get("required") or [])
    if not CHECKPOINT_REQUIRED <= required:
        fail(f"checkpoint schema missing {sorted(CHECKPOINT_REQUIRED - required)}")

    example_path = ROOT / "packages/vfharness/templates/checkpoint.example.json"
    if not example_path.is_file():
        fail("missing checkpoint example")
    example = json.loads(example_path.read_text(encoding="utf-8"))
    missing_ex = CHECKPOINT_REQUIRED - set(example)
    if missing_ex:
        fail(f"checkpoint example missing {sorted(missing_ex)}")
    if example.get("status") not in {"running", "blocked", "escalated", "done"}:
        fail("checkpoint example has invalid status")

    run_example_path = ROOT / "packages/vfharness/templates/checkpoint.example-run.json"
    if not run_example_path.is_file():
        fail("missing checkpoint example-run")
    run_example = json.loads(run_example_path.read_text(encoding="utf-8"))
    missing_run = CHECKPOINT_REQUIRED - set(run_example)
    if missing_run:
        fail(f"checkpoint example-run missing {sorted(missing_run)}")
    if run_example.get("status") != "blocked" or not run_example.get("gate"):
        fail("checkpoint example-run must demonstrate blocked + gate")
    oma_playbook = ROOT / "packages/vfharness/playbooks/oma-patterns.md"
    if not oma_playbook.is_file():
        fail("missing packages/vfharness/playbooks/oma-patterns.md")
    receipt = ROOT / "packages/vfharness/templates/run-receipt.md"
    if not receipt.is_file():
        fail("missing packages/vfharness/templates/run-receipt.md")

    skillstate = ROOT / "packages/vfharness/playbooks/skillstate.md"
    if not skillstate.is_file():
        fail("missing packages/vfharness/playbooks/skillstate.md")
    skillstate_text = skillstate.read_text(encoding="utf-8")
    for needle in (
        "2608.26263",
        "execution_state",
        "latest_observation",
        "second agent runtime",
        "context-thrift",
    ):
        if needle not in skillstate_text:
            fail(f"skillstate.md missing {needle!r}")
    schema_text = schema_path.read_text(encoding="utf-8")
    for needle in ("execution_state", "latest_observation", "SKILLSTATE", "component_state", "Degraded"):
        if needle not in schema_text:
            fail(f"checkpoint.schema.json missing SKILLSTATE field {needle!r}")
    if "skillstate.md" not in (ROOT / "packages/vfharness/EMBED.md").read_text(encoding="utf-8"):
        fail("EMBED.md must reference skillstate.md")

    degraded = ROOT / "packages/vfharness/playbooks/degraded-mode.md"
    if not degraded.is_file():
        fail("missing packages/vfharness/playbooks/degraded-mode.md")
    degraded_text = degraded.read_text(encoding="utf-8")
    for needle in ("Degraded", "component_state", "ORCHESTRA", "failover", "broker"):
        if needle not in degraded_text:
            fail(f"degraded-mode.md missing {needle!r}")
    orch = (ROOT / "constitution" / "ORCHESTRA.md").read_text(encoding="utf-8")
    if "Degraded Mode" not in orch:
        fail("ORCHESTRA.md must name Degraded Mode")
    if example.get("component_state") not in {
        "Idle",
        "Processing",
        "Degraded",
        "Syncing",
        "Blocked",
        None,
    }:
        fail("checkpoint example component_state invalid when present")
    if example.get("component_state") != "Idle":
        fail("checkpoint example should demonstrate component_state Idle")
    if run_example.get("component_state") != "Blocked":
        fail("checkpoint example-run should demonstrate component_state Blocked")
    skillstate_text = skillstate.read_text(encoding="utf-8")
    for needle in ("component_state", "degraded-mode", "events.catalog"):
        if needle not in skillstate_text:
            fail(f"skillstate.md missing three-layer needle {needle!r}")

    thrift = ROOT / "packages/vfharness/playbooks/context-thrift.md"
    if not thrift.is_file():
        fail("missing packages/vfharness/playbooks/context-thrift.md")
    thrift_text = thrift.read_text(encoding="utf-8")
    for needle in (
        "phase-boundary",
        "באמצע ביצוע",
        "strategic-compact",
        "לא מתקינים",
        "/compact",
    ):
        if needle not in thrift_text:
            fail(f"context-thrift.md missing phase-boundary needle {needle!r}")
    embed_text = (ROOT / "packages/vfharness/EMBED.md").read_text(encoding="utf-8")
    if "phase-boundary" not in embed_text:
        fail("EMBED.md must reference phase-boundary compaction")
    if "skillstate.md" not in (ROOT / "packages/vfharness/LOOP.md").read_text(encoding="utf-8"):
        fail("LOOP.md must reference skillstate.md")
    if "SKILLSTATE" not in agents_text and "skillstate" not in agents_text:
        fail("AGENTS.md MEMORY must mention SKILLSTATE / skillstate")

    checklist = spec.get("checklist") or []
    if len(checklist) != 12:
        fail(f"expected 12 checklist items, got {len(checklist)}")

    if "vfharness" not in pack_names:
        fail("vfharness missing from packages/manifest.json")

    tools_map = ROOT / "packages/vfharness/playbooks/grok-outage-tools.md"
    if not tools_map.is_file():
        fail("missing packages/vfharness/playbooks/grok-outage-tools.md")
    tools_text = tools_map.read_text(encoding="utf-8")
    for needle in ("create_draft", "Cloudflare Instagram Publisher", "Meta Instagram Graph", "אין MCP", "send_message"):
        if needle not in tools_text:
            fail(f"grok-outage-tools.md missing {needle!r}")
    failover = ROOT / "packages/vfharness/playbooks/grok-failover.md"
    if not failover.is_file():
        fail("missing packages/vfharness/playbooks/grok-failover.md")

    four_axes = ROOT / "packages/vfharness/playbooks/core-stability-four-axes.md"
    if not four_axes.is_file():
        fail("missing packages/vfharness/playbooks/core-stability-four-axes.md")
    axes = four_axes.read_text(encoding="utf-8")
    for needle in (
        "atomic",
        "vf_send_preflight.py",
        "owner-memory",
        "attach-core",
        "repository_dispatch",
    ):
        if needle not in axes:
            fail(f"core-stability-four-axes.md must mention {needle}")
    failover_text = failover.read_text(encoding="utf-8")
    for needle in (
        "מוכן-ל-Grok",
        "פרסום-חי-דחוף",
        "LIVE-PACKET",
        "לא מחכים לגרוק",
        "SEND.md",
    ):
        if needle not in failover_text:
            fail(f"grok-failover.md missing {needle!r}")
    if "Publish מ־HQ" in failover_text and "אדם" not in failover_text:
        fail("grok-failover.md must keep human live-publish path")
    queue = ROOT / "packages/vfigos/QUEUE.md"
    live = ROOT / "packages/vfigos/LIVE-PACKET.md"
    docs_fo = ROOT / "docs/GROK-FAILOVER.md"
    docs_office_fo = ROOT / "docs/FAILOVER.md"
    for path in (queue, live, docs_fo, docs_office_fo):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")
    office_fo_text = docs_office_fo.read_text(encoding="utf-8")
    for needle in (
        "דוח השתלטות",
        "ChatGPT",
        "Perplexity",
        "Gemini",
        "Grok",
        "Cursor",
        "SHARED-WORK-COORDINATION.md",
        "MEDIA-VAULT.md",
        "תהליך → מוכן → צילום סופי → פרסום",
        "passwords",
    ):
        if needle not in office_fo_text:
            fail(f"docs/FAILOVER.md missing {needle!r}")
    if "docs/FAILOVER.md" not in agents_text and "Office-manager failover" not in agents_text:
        fail("AGENTS.md must mention office-manager failover / docs/FAILOVER.md")
    queue_text = queue.read_text(encoding="utf-8")
    for needle in ("#מוכן-ל-Grok", "#פרסום-חי-דחוף", "#נשלח-מ-HQ", "#ממתין-ל-כלי-IG"):
        if needle not in queue_text:
            fail(f"vfigos/QUEUE.md missing {needle!r}")
    live_text = live.read_text(encoding="utf-8")
    for needle in ("אדם", "מעלה", "050-2517000", "אין Publish מ־HQ"):
        if needle not in live_text:
            fail(f"LIVE-PACKET.md missing {needle!r}")
    if "פרסום חי" not in agents_text and "Grok Bot quota failover" not in agents_text:
        fail("AGENTS.md must mention Grok Bot quota failover")
    if "LIVE-PACKET" not in agents_text and "פרסום-חי-דחוף" not in agents_text:
        fail("AGENTS.md must mention live-publish urgent path")

    full_output = ROOT / "packages/vfharness/playbooks/full-output-enforcement.md"
    if not full_output.is_file():
        fail("missing packages/vfharness/playbooks/full-output-enforcement.md")
    fo_text = full_output.read_text(encoding="utf-8")
    for needle in ("[PAUSED", "taste-skill", "Scope", "checkpoint"):
        if needle not in fo_text:
            fail(f"full-output-enforcement.md missing {needle!r}")

    allowed_embed = pack_names | {"constitution"}
    embeds = spec.get("embed") or []
    if len(embeds) < 8:
        fail(f"expected at least 8 embed rows, got {len(embeds)}")
    for row in embeds:
        pack = row.get("pack")
        if pack not in allowed_embed:
            fail(f"embed unknown pack {pack!r}")
        if not row.get("how"):
            fail(f"embed {pack} missing how")

    ils = re.compile(r"(?<!050-251)(?<!050–251)\d[\d.,]*\s*₪|₪\s*\d")
    for path in (ROOT / "packages/vfharness").rglob("*"):
        if path.suffix not in {".md", ".json"}:
            continue
        text = path.read_text(encoding="utf-8")
        for m in ils.finditer(text):
            snippet = text[max(0, m.start() - 20) : m.end() + 8]
            if "X ₪" in snippet:
                continue
            if re.search(r"(בלי|אין|לא)\s*₪|₪\s*רק", snippet):
                continue
            fail(f"possible invented ILS in {path.relative_to(ROOT)}: {snippet!r}")

    print(
        f"OK harness layers=6 sensors={len(sensors)} "
        f"embeds={len(embeds)} locks={len(locks)} packs={len(pack_names)}"
    )


if __name__ == "__main__":
    main()
