#!/usr/bin/env python3
"""Validate the six-layer VF harness against AGENTS.md and existing packs. No network. No send."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYERS = ROOT / "packages" / "vfharness" / "layers.json"
MANIFEST = ROOT / "packages" / "manifest.json"
AGENTS = ROOT / "AGENTS.md"
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

    spec = json.loads(LAYERS.read_text())
    manifest = json.loads(MANIFEST.read_text())
    pack_names = {p["name"] for p in manifest.get("packs", [])}
    agents_text = AGENTS.read_text()

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

    schema_path = ROOT / "packages/vfharness/templates/checkpoint.schema.json"
    schema = json.loads(schema_path.read_text())
    required = set(schema.get("required") or [])
    if not CHECKPOINT_REQUIRED <= required:
        fail(f"checkpoint schema missing {sorted(CHECKPOINT_REQUIRED - required)}")

    example_path = ROOT / "packages/vfharness/templates/checkpoint.example.json"
    if not example_path.is_file():
        fail("missing checkpoint example")
    example = json.loads(example_path.read_text())
    missing_ex = CHECKPOINT_REQUIRED - set(example)
    if missing_ex:
        fail(f"checkpoint example missing {sorted(missing_ex)}")
    if example.get("status") not in {"running", "blocked", "escalated", "done"}:
        fail("checkpoint example has invalid status")

    run_example_path = ROOT / "packages/vfharness/templates/checkpoint.example-run.json"
    if not run_example_path.is_file():
        fail("missing checkpoint example-run")
    run_example = json.loads(run_example_path.read_text())
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

    checklist = spec.get("checklist") or []
    if len(checklist) != 12:
        fail(f"expected 12 checklist items, got {len(checklist)}")

    if "vfharness" not in pack_names:
        fail("vfharness missing from packages/manifest.json")

    tools_map = ROOT / "packages/vfharness/playbooks/grok-outage-tools.md"
    if not tools_map.is_file():
        fail("missing packages/vfharness/playbooks/grok-outage-tools.md")
    tools_text = tools_map.read_text()
    for needle in ("create_draft", "Canva", "render.py", "אין MCP", "send_message"):
        if needle not in tools_text:
            fail(f"grok-outage-tools.md missing {needle!r}")
    failover = ROOT / "packages/vfharness/playbooks/grok-failover.md"
    if not failover.is_file():
        fail("missing packages/vfharness/playbooks/grok-failover.md")
    failover_text = failover.read_text()
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
    for path in (queue, live, docs_fo):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")
    queue_text = queue.read_text()
    for needle in ("#מוכן-ל-Grok", "#פרסום-חי-דחוף", "#נשלח-מ-HQ", "#ממתין-ל-כלי-IG"):
        if needle not in queue_text:
            fail(f"vfigos/QUEUE.md missing {needle!r}")
    live_text = live.read_text()
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
    fo_text = full_output.read_text()
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
        text = path.read_text()
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
