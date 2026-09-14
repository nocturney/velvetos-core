#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "packages" / "velvetos" / "chatgpt-project"
CONTRACT = BASE / "PROJECT-CONTRACT-v6.json"
INSTRUCTIONS = BASE / "PROJECT-INSTRUCTIONS-v6.txt"
AUTHORITY = BASE / "PROJECT-AUTHORITY-v6.txt"
CANARY = BASE / "COLD-START-CANARY.md"

EXPECTED_REF = "Velvet-Factory-APPROVED-Visual-Reference-v2.jpg"
EXPECTED_ASSET = "MAHVL7PKpvE"
EXPECTED_SHA = "df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897"


def fail(msg: str) -> None:
    print(f"FAIL chatgpt-project-contract: {msg}", file=sys.stderr)
    raise SystemExit(1)

for p in (CONTRACT, INSTRUCTIONS, AUTHORITY, CANARY):
    if not p.is_file():
        fail(f"missing {p.relative_to(ROOT)}")
data = json.loads(CONTRACT.read_text(encoding="utf-8"))
if data.get("contractVersion") != 6 or data.get("mode") != "fail_closed":
    fail("contract version/mode mismatch")
if data.get("visualReferenceSourceName") != EXPECTED_REF:
    fail("visual reference source name mismatch")
if data.get("visualReferenceCanvaAssetId") != EXPECTED_ASSET:
    fail("visual reference Canva asset mismatch")
if data.get("visualReferenceSha256") != EXPECTED_SHA:
    fail("visual reference SHA mismatch")
if data.get("projectAuthoritySourceName") != "Velvet-Factory-Project-Authority-v6.txt":
    fail("project authority source name mismatch")

instructions = INSTRUCTIONS.read_text(encoding="utf-8")
if len(instructions) > 5000:
    fail(f"Project Instructions too long for compact bootstrap: {len(instructions)} chars")
for needle in (
    "PROJECT BOOTSTRAP v6",
    "Velvet-Factory-Project-Authority-v6.txt",
    EXPECTED_REF,
    "project_preflight=PASS/BLOCKED",
    "Photo ranking/caption/planning alone is incomplete",
    "two tracks",
):
    if needle not in instructions:
        fail(f"Project Instructions missing {needle!r}")
authority = AUTHORITY.read_text(encoding="utf-8")
for needle in (
    "Contract version: 6",
    "Velvet-Factory-Project-Authority-v6.txt",
    EXPECTED_REF,
    EXPECTED_ASSET,
    EXPECTED_SHA,
    "מוצרים מוכנים",
    "הדפסה / מודל בהתאמה אישית",
    "COLD-START CANARY LAW",
    "MEMORY / PRECEDENCE",
):
    if needle not in authority:
        fail(f"Project Authority missing {needle!r}")

canary = CANARY.read_text(encoding="utf-8")
for needle in (
    "תכין פוסט לפרסום",
    "produces at least one genuinely edited visual artifact",
    "no invented logo/wordmark",
    "no public phone/WhatsApp/contact bar",
    "Canary C — missing authority",
    "Repository sensors validate contract wiring",
):
    if needle not in canary:
        fail(f"cold-start canary missing {needle!r}")

manifest = json.loads((ROOT / "packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json").read_text(encoding="utf-8"))
binding = manifest.get("chatgptProjectContract") or {}
if binding.get("version") != 6 or binding.get("mode") != "fail_closed":
    fail("authority manifest not bound to project contract v6")
if binding.get("visualReferenceSha256") != EXPECTED_SHA:
    fail("authority manifest visual reference SHA mismatch")
gate = (ROOT / "packages/velvetos/PROJECT-REQUEST-GATE.md").read_text(encoding="utf-8")
for needle in ("PROJECT-CONTRACT-v6.json", "Velvet-Factory-Project-Authority-v6.txt", EXPECTED_REF, "needs_sync"):
    if needle not in gate:
        fail(f"Project Request Gate missing {needle!r}")

for rel in ("AGENTS.md", "instances/velvet-factory/AGENTS.md", "instances/velvet-factory/.cursor/rules/velvetos-instance-desk.mdc"):
    body = (ROOT / rel).read_text(encoding="utf-8")
    for needle in ("PROJECT-CONTRACT-v6.json", "Velvet-Factory-Project-Authority-v6.txt", EXPECTED_REF, "needs_sync"):
        if needle not in body:
            fail(f"{rel} missing ChatGPT Project v6 binding {needle!r}")

profile = json.loads((ROOT / "packages/vfigos/PROFILE-DESIRED.json").read_text(encoding="utf-8"))
if profile.get("liveStatus") != "verified":
    fail("live Instagram profile cleanup is not verified")
if (profile.get("liveSnapshot") or {}).get("retiredOfferingPhrasePresent") is not False:
    fail("live Instagram profile still reports retired offering wording")

print(f"OK chatgpt-project-contract v6 instructions_chars={len(instructions)} visual=v2 live_profile=verified cold_start_canary=defined")
