#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "packages" / "velvetos" / "UPSTREAM-WATCH.json"
DAILY = ROOT / "packages" / "vfresearch" / "DAILY.md"
REVIEW = ROOT / "packages" / "vfresearch" / "sources" / "upstream-review-latest.json"
REQUEST = ROOT / "packages" / "vfresearch" / "out" / "tool-updates-send-request.json"
VISIBLE = ROOT / "packages" / "vfresearch" / "out" / "tool-updates-latest.txt"
HTML = ROOT / "packages" / "vfresearch" / "out" / "tool-updates-latest.html"
WORKFLOW = ROOT / ".github" / "workflows" / "gmail-tool-updates-send.yml"
RENDERER = ROOT / "scripts" / "vf_upstream_email.py"
OFFICE = ROOT / "scripts" / "vfops_loop.py"


def fail(message: str) -> None:
    print(f"UPSTREAM EMAIL FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    for path in (REGISTRY, DAILY, REVIEW, REQUEST, VISIBLE, HTML, WORKFLOW, RENDERER, OFFICE):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    delivery = ((registry.get("scheduler") or {}).get("ownerDelivery") or {})
    if delivery.get("channel") != "separate-email":
        fail("owner delivery must be separate-email")
    if delivery.get("includeInMorningBrief") is not False:
        fail("tool update decisions must not be included in Morning Brief")
    if delivery.get("repeatUnchangedPending") is not False:
        fail("unchanged pending updates must not generate repeated email")
    if delivery.get("workflow") != ".github/workflows/gmail-tool-updates-send.yml":
        fail("dedicated workflow path mismatch")

    daily = DAILY.read_text(encoding="utf-8")
    required_daily = [
        "עדכוני toolchain / skills / agents **לא נכנסים ל־Morning Brief**",
        "vf_upstream_email.py render --arm --consume-notify",
        "אם אין עדכון חדש או שינוי החלטה — **לא נשלח מייל**",
        "אין להכניס לתמצית הזו רשימת עדכוני כלים",
    ]
    for marker in required_daily:
        if marker not in daily:
            fail(f"DAILY.md missing policy marker: {marker}")

    office = OFFICE.read_text(encoding="utf-8")
    if "changed={changed}" in office or "pendingUpdates" in office:
        fail("Office/Morning Brief path must not expose tool-update counts or decisions")
    if "decisions delivered separately by email" not in office:
        fail("Office verification line must document separate decision delivery")

    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    if review.get("schema") != "velvetos.upstream-review.v1":
        fail("review schema mismatch")
    valid = {"update", "wait", "review", "ignore"}
    for repo, row in (review.get("items") or {}).items():
        if not isinstance(row, dict) or row.get("verdict") not in valid:
            fail(f"invalid verdict for {repo}")
        if not str(row.get("reviewedRemoteHead") or "").strip():
            fail(f"review missing reviewedRemoteHead for {repo}")
        if "reviewedRelease" not in row:
            fail(f"review missing reviewedRelease for {repo}")

    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    if request.get("enabled") is not False:
        fail("repository baseline request must be disabled")
    if request.get("html") != "packages/vfresearch/out/tool-updates-latest.html":
        fail("request html path mismatch")
    if request.get("visibleText") != "packages/vfresearch/out/tool-updates-latest.txt":
        fail("request visibleText path mismatch")
    if not str(request.get("subject") or "").startswith("VelvetOS · עדכוני כלים"):
        fail("dedicated subject missing")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    for marker in (
        "packages/vfresearch/out/tool-updates-send-request.json",
        "gmail_apps_script_request",
        "GMAIL_APPS_SCRIPT_SECRET",
        "--surface owner-brief",
    ):
        if marker not in workflow:
            fail(f"workflow missing {marker}")
    if "packages/vfops/out/gmail-send-request.json" in workflow:
        fail("tool update workflow must not use Morning Brief request")

    proc = subprocess.run(
        [sys.executable, str(RENDERER), "selftest"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=20,
    )
    if proc.returncode != 0 or "separate-owner-email" not in (proc.stdout or ""):
        fail(f"renderer selftest failed: {proc.stderr or proc.stdout}")

    print("UPSTREAM EMAIL PASS separate-email no-brief decision-labels no-repeat sender=reused-apps-script")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
