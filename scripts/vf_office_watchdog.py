#!/usr/bin/env python3
"""Office publication + health watchdog. Disk only. No network. No send."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

OUTCOMES = (
    "OK",
    "AUTOFIXED",
    "PREPARED",
    "WAITING_EXTERNAL_TOOL",
    "DEAD_LETTER",
    "RED_BLOCKER",
)


def _load(path: Path):
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def inspect() -> dict:
    findings: list[dict] = []

    desk = _load(ROOT / ".cursor" / "vf-desk.json") or {}
    ig = (desk.get("tools") or {}).get("instagram") or {}
    ig_status = ig.get("status") or "unknown"
    if ig_status in {"needsAuth", "pending-connection", "down"}:
        findings.append(
            {
                "area": "instagram-tool",
                "outcome": "WAITING_EXTERNAL_TOOL",
                "detail": f"instagram.status={ig_status} — office continues offline prep",
            }
        )
    elif ig_status == "ready":
        findings.append(
            {
                "area": "instagram-tool",
                "outcome": "OK",
                "detail": "instagram.status=ready (desk claim; healthcheck still required before live)",
            }
        )
    else:
        findings.append(
            {
                "area": "instagram-tool",
                "outcome": "WAITING_EXTERNAL_TOOL",
                "detail": f"instagram.status={ig_status}",
            }
        )

    caps = _load(ROOT / "packages" / "vfigos" / "CAPABILITIES.json") or {}
    if caps.get("currentStatus") == "ready" and ig_status != "ready":
        findings.append(
            {
                "area": "instagram-capabilities",
                "outcome": "RED_BLOCKER",
                "detail": "CAPABILITIES claims ready while desk is not — refuse fake ready",
            }
        )
    else:
        findings.append(
            {
                "area": "instagram-capabilities",
                "outcome": "OK",
                "detail": "capability contract present; status not faked ready",
            }
        )

    profile = _load(ROOT / "packages" / "vfigos" / "PROFILE-DESIRED.json") or {}
    if profile.get("status") == "prepared" and profile.get("liveStatus") == "pending-live-tool":
        findings.append(
            {
                "area": "profile-desired",
                "outcome": "PREPARED",
                "detail": "bio prepared; pending live tool",
            }
        )

    pub = _load(ROOT / "packages" / "vfigos" / "PUBLICATION-STATES.json") or {}
    if "liveVerified" not in {s.get("id") for s in pub.get("states") or []}:
        findings.append(
            {
                "area": "publication-states",
                "outcome": "RED_BLOCKER",
                "detail": "PUBLICATION-STATES missing liveVerified",
            }
        )
    else:
        findings.append(
            {
                "area": "publication-states",
                "outcome": "OK",
                "detail": "publish≠scheduled≠live encoded",
            }
        )

    cta = (ROOT / "constitution" / "PUBLIC_CTA.md").read_text(encoding="utf-8")
    if "Instagram DM only" not in cta and "Instagram DM" not in cta:
        findings.append(
            {
                "area": "public-cta",
                "outcome": "RED_BLOCKER",
                "detail": "PUBLIC_CTA.md missing Instagram DM policy",
            }
        )
    else:
        findings.append({"area": "public-cta", "outcome": "OK", "detail": "IG-DM public CTA law present"})

    instance = _load(
        ROOT / "instances" / "velvet-factory" / "instance" / "velvet-factory.json"
    ) or {}
    primary = ((instance.get("cta") or {}).get("primary") or "").lower()
    if "050-2517000" in primary or "whatsapp" in primary and "instagram" not in primary:
        # allow businessContact separately; primary must not be WA
        if "instagram" not in primary and "הודעה" not in primary:
            findings.append(
                {
                    "area": "instance-cta",
                    "outcome": "RED_BLOCKER",
                    "detail": "instance cta.primary still WhatsApp-oriented",
                }
            )
        else:
            findings.append({"area": "instance-cta", "outcome": "OK", "detail": "primary CTA migrated"})
    else:
        findings.append({"area": "instance-cta", "outcome": "OK", "detail": "primary CTA not WhatsApp"})

    catalog = _load(ROOT / "packages" / "vfmedia" / "catalog.json")
    if catalog is None:
        findings.append(
            {
                "area": "media-vault",
                "outcome": "RED_BLOCKER",
                "detail": "canonical catalog.json missing",
            }
        )
    else:
        findings.append(
            {
                "area": "media-vault",
                "outcome": "OK",
                "detail": f"one catalog items={len(catalog.get('items') or [])}",
            }
        )

    dl = _load(ROOT / "packages" / "vfharness" / "dead-letter" / "queue.json") or {}
    open_dl = [i for i in dl.get("items") or [] if not i.get("resolved")]
    if open_dl:
        red = [i for i in open_dl if i.get("riskColor") == "RED" or i.get("christianRequired")]
        if red:
            findings.append(
                {
                    "area": "dead-letter",
                    "outcome": "RED_BLOCKER",
                    "detail": f"{len(red)} red dead-letter items",
                }
            )
        else:
            findings.append(
                {
                    "area": "dead-letter",
                    "outcome": "DEAD_LETTER",
                    "detail": f"{len(open_dl)} open dead-letter items",
                }
            )
    else:
        findings.append({"area": "dead-letter", "outcome": "OK", "detail": "no open dead-letter"})

    fu = _load(ROOT / "packages" / "vfgrowth" / "data" / "production-content-followups.json") or {}
    open_fu = [
        f
        for f in fu.get("followups") or []
        if f.get("status") in {"waiting_for_matching_print.done", "finished-media-required"}
    ]
    if open_fu:
        findings.append(
            {
                "area": "production-content",
                "outcome": "PREPARED",
                "detail": f"{len(open_fu)} open process→finish follow-ups",
            }
        )
    else:
        findings.append(
            {
                "area": "production-content",
                "outcome": "OK",
                "detail": "no open process follow-ups",
            }
        )

    audit = _load(ROOT / "packages" / "vfgrowth" / "data" / "feed-audit.json") or {}
    if audit.get("access") == "awaiting-live-audit":
        findings.append(
            {
                "area": "feed-audit",
                "outcome": "WAITING_EXTERNAL_TOOL",
                "detail": "feed audit prepared; awaiting live IG access",
            }
        )
    g004 = audit.get("g004Identity") or {}
    if g004.get("canonicalHe") != "מחזיק טבעות לזמן אימון":
        findings.append(
            {
                "area": "g004-identity",
                "outcome": "RED_BLOCKER",
                "detail": "G004 identity drift",
            }
        )
    else:
        findings.append({"area": "g004-identity", "outcome": "OK", "detail": "G004 identity locked"})

    # Summarize worst outcome
    rank = {o: i for i, o in enumerate(OUTCOMES)}
    worst = "OK"
    for f in findings:
        if rank.get(f["outcome"], 0) > rank.get(worst, 0):
            worst = f["outcome"]

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "summary": worst,
        "findings": findings,
        "spamChristian": False,
        "note": "Notify Christian only for RED_BLOCKER items that require owner action.",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", action="store_true")
    p.add_argument("--write", action="store_true", help="Write report under vfops/hq/")
    args = p.parse_args()
    report = inspect()
    if args.write:
        out = ROOT / "packages" / "vfops" / "hq" / "watchdog-latest.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"WROTE {out.relative_to(ROOT)}")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"WATCHDOG {report['summary']} findings={len(report['findings'])}")
        for f in report["findings"]:
            print(f"  {f['outcome']:24} {f['area']}: {f['detail']}")
    return 0 if report["summary"] != "RED_BLOCKER" else 2


if __name__ == "__main__":
    sys.exit(main())
