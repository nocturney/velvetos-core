#!/usr/bin/env python3
"""Render a separate owner email for upstream/toolchain update decisions.

This command never installs or upgrades anything and never sends mail itself.
It consumes the upstream watch report plus an optional review artifact, renders
owner-visible text/HTML, and writes a dedicated Gmail send request. The request
is armed only when there is a new detection or an explicit review notification.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "packages" / "vfresearch" / "sources" / "upstream-watch-latest.json"
REGISTRY = ROOT / "packages" / "velvetos" / "UPSTREAM-WATCH.json"
REVIEW = ROOT / "packages" / "vfresearch" / "sources" / "upstream-review-latest.json"
OUT_DIR = ROOT / "packages" / "vfresearch" / "out"
REQUEST = OUT_DIR / "tool-updates-send-request.json"
VISIBLE = OUT_DIR / "tool-updates-latest.txt"
HTML = OUT_DIR / "tool-updates-latest.html"
OWNER = "nocturney@gmail.com"

VERDICT_HE = {
    "update": "מומלץ לעדכן",
    "wait": "להמתין",
    "review": "לבדוק לפני החלטה",
    "ignore": "אין פעולה כרגע",
}


def load_json(path: Path, *, optional: bool = False) -> dict[str, Any]:
    if optional and not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"JSON root must be object: {path}")
    return data


def review_map(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = data.get("items") or {}
    if isinstance(raw, dict):
        return {str(k).casefold(): v for k, v in raw.items() if isinstance(v, dict)}
    if isinstance(raw, list):
        return {
            str(item.get("repo") or "").casefold(): item
            for item in raw
            if isinstance(item, dict) and item.get("repo")
        }
    raise RuntimeError("upstream review items must be object or list")


def default_decision(row: dict[str, Any], registry_row: dict[str, Any]) -> dict[str, Any]:
    kind = str(row.get("kind") or registry_row.get("kind") or "")
    adoption_class = str(registry_row.get("adoptionClass") or "")
    if adoption_class == "staged-stability-pin":
        return {
            "verdict": "wait",
            "reasonHe": "הגרסה הנוכחית מוחזקת בכוונה כ־staged stability; לעדכן רק אחרי בדיקת תאימות ו־smoke.",
            "evidence": [],
            "notifyOwner": False,
        }
    runtime_kinds = {
        "runtime-source",
        "runtime-toolchain",
        "cad-runtime-source",
        "slicer-runtime-source",
        "cad-agent-source",
    }
    if kind in runtime_kinds:
        return {
            "verdict": "review",
            "reasonHe": "זהו מקור runtime פעיל; נדרשת בדיקת release notes ותאימות לפני אימוץ.",
            "evidence": [],
            "notifyOwner": False,
        }
    return {
        "verdict": "review",
        "reasonHe": "זהו מקור skills/agents/pattern/catalog; בודקים אם השינוי רלוונטי למה שהוטמע לפני שמעדכנים.",
        "evidence": [],
        "notifyOwner": False,
    }


def decision_for(
    row: dict[str, Any],
    registry_row: dict[str, Any],
    reviews: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    repo = str(row.get("repo") or "")
    decision = default_decision(row, registry_row)
    override = reviews.get(repo.casefold()) or {}
    reviewed_head = str(override.get("reviewedRemoteHead") or "")
    current_head = str(row.get("remoteHead") or "")
    reviewed_release = str(override.get("reviewedRelease") or "")
    current_release = str(row.get("latestRelease") or "")
    review_ready = bool(
        override
        and reviewed_head
        and reviewed_head == current_head
        and reviewed_release == current_release
    )
    if review_ready:
        decision.update(override)
    else:
        decision["notifyOwner"] = False
        decision["reasonHe"] = (
            "ממתין ל־review מפורש של ה־HEAD/release הנוכחי לפני שניתן לשלוח המלצה לבעלים."
        )
    verdict = str(decision.get("verdict") or "review")
    if verdict not in VERDICT_HE:
        raise RuntimeError(f"invalid review verdict for {repo}: {verdict}")
    decision["verdict"] = verdict
    decision["labelHe"] = VERDICT_HE[verdict]
    decision["reviewReady"] = review_ready
    return decision


def short_sha(value: Any) -> str:
    text = str(value or "")
    return text[:10] if text else "—"


def version_line(row: dict[str, Any]) -> str:
    baseline_release = row.get("baselineRelease")
    latest_release = row.get("latestRelease")
    if baseline_release or latest_release:
        return f"{baseline_release or 'ללא release baseline'} → {latest_release or 'ללא release חדש'}"
    return f"{short_sha(row.get('baselineHead'))} → {short_sha(row.get('remoteHead'))}"


def integration_line(registry_row: dict[str, Any]) -> str:
    values = [str(x) for x in (registry_row.get("integration") or []) if str(x).strip()]
    return " · ".join(values[:3]) if values else "לא תועד integration path"


def make_payload(
    report: dict[str, Any],
    registry: dict[str, Any],
    review: dict[str, Any],
) -> tuple[list[dict[str, Any]], bool, str]:
    registry_rows = {
        str(item.get("repo") or "").casefold(): item
        for item in (registry.get("sources") or [])
        if isinstance(item, dict) and item.get("repo")
    }
    reviews = review_map(review)
    items: list[dict[str, Any]] = []
    for row in report.get("sources") or []:
        if not isinstance(row, dict) or not row.get("pendingUpdate"):
            continue
        repo = str(row.get("repo") or "")
        registry_row = registry_rows.get(repo.casefold(), {})
        decision = decision_for(row, registry_row, reviews)
        items.append(
            {
                "repo": repo,
                "kind": row.get("kind"),
                "version": version_line(row),
                "changeKinds": list(row.get("changeKinds") or []),
                "newDetection": bool(row.get("newDetection")),
                "integration": integration_line(registry_row),
                "decision": decision,
            }
        )
    all_reviewed = bool(items) and all(bool(item["decision"].get("reviewReady")) for item in items)
    notify = bool(
        all_reviewed
        and any(item["newDetection"] or bool(item["decision"].get("notifyOwner")) for item in items)
    )
    digest_body = [
        {
            "repo": item["repo"],
            "version": item["version"],
            "changeKinds": item["changeKinds"],
            "verdict": item["decision"]["verdict"],
            "reasonHe": item["decision"].get("reasonHe"),
        }
        for item in items
    ]
    digest = hashlib.sha256(
        json.dumps(digest_body, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return items, notify, digest


def render_text(items: list[dict[str, Any]], checked_at: str) -> str:
    lines = [
        "VelvetOS · עדכוני כלים",
        "",
        f"נמצאו {len(items)} עדכונים ממתינים. לא בוצע שום שדרוג אוטומטי.",
        f"בדיקת upstream אחרונה: {checked_at or 'לא ידוע'}",
        "",
    ]
    for index, item in enumerate(items, start=1):
        decision = item["decision"]
        lines.extend(
            [
                f"{index}. {item['repo']}",
                f"   מצב: {decision['labelHe']}",
                f"   גרסה/מקור: {item['version']}",
                f"   שינוי: {', '.join(item['changeKinds']) or 'לא סווג'}",
                f"   שימוש אצלנו: {item['integration']}",
                f"   למה: {decision.get('reasonHe') or 'לא תועד נימוק'}",
            ]
        )
        evidence = [str(x) for x in (decision.get("evidence") or []) if str(x).strip()]
        if evidence:
            lines.append("   ראיות: " + " · ".join(evidence[:4]))
        lines.append(f"   מקור: https://github.com/{item['repo']}")
        lines.append("")
    lines.extend(
        [
            "כלל פעולה:",
            "מומלץ לעדכן = יש מספיק ראיות לאימוץ; להמתין = נשארים בגרסה הנוכחית; לבדוק = נדרשת בדיקת תאימות; אין פעולה = שינוי לא רלוונטי כרגע.",
            "",
            "ה־ack מתבצע רק אחרי אימוץ שנבדק. עצם קבלת המייל אינה משנה שום גרסה.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_html(items: list[dict[str, Any]], checked_at: str) -> str:
    cards: list[str] = []
    for item in items:
        d = item["decision"]
        source = f"https://github.com/{item['repo']}"
        evidence = [str(x) for x in (d.get("evidence") or []) if str(x).strip()]
        evidence_html = ""
        if evidence:
            evidence_html = (
                '<div style="margin-top:8px;color:#555"><strong>ראיות:</strong> '
                + html.escape(" · ".join(evidence[:4]))
                + "</div>"
            )
        cards.append(
            f"""
            <section style="border:1px solid #e5e5e5;border-radius:14px;padding:18px;margin:14px 0;background:#fff">
              <div style="font-size:18px;font-weight:700">{html.escape(item['repo'])}</div>
              <div style="margin-top:8px"><strong>המלצה:</strong> {html.escape(d['labelHe'])}</div>
              <div style="margin-top:6px"><strong>גרסה/מקור:</strong> {html.escape(item['version'])}</div>
              <div style="margin-top:6px"><strong>שינוי:</strong> {html.escape(', '.join(item['changeKinds']) or 'לא סווג')}</div>
              <div style="margin-top:6px"><strong>שימוש אצלנו:</strong> {html.escape(item['integration'])}</div>
              <div style="margin-top:8px"><strong>למה:</strong> {html.escape(str(d.get('reasonHe') or 'לא תועד נימוק'))}</div>
              {evidence_html}
              <div style="margin-top:12px"><a href="{html.escape(source)}">פתיחת ה־upstream ב־GitHub</a></div>
            </section>
            """
        )
    return f"""<!doctype html>
<html lang="he" dir="rtl">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;background:#f6f6f4;font-family:Arial,Helvetica,sans-serif;color:#1d1d1f">
  <main style="max-width:720px;margin:0 auto;padding:28px 18px">
    <div style="font-size:13px;color:#777">VelvetOS · Toolchain Release Watch</div>
    <h1 style="margin:8px 0 6px;font-size:28px">עדכוני כלים</h1>
    <p style="margin:0 0 8px">נמצאו {len(items)} עדכונים ממתינים. לא בוצע שום שדרוג אוטומטי.</p>
    <p style="margin:0 0 18px;color:#666">בדיקת upstream אחרונה: {html.escape(checked_at or 'לא ידוע')}</p>
    {''.join(cards)}
    <div style="margin-top:20px;padding:14px;border-radius:12px;background:#efefec;font-size:13px;line-height:1.55">
      ה־ack מתבצע רק אחרי אימוץ שנבדק. עצם קבלת המייל אינה משנה שום גרסה.
    </div>
  </main>
</body>
</html>
"""


def consume_notifications(review_path: Path, review: dict[str, Any], digest: str) -> None:
    items = review.get("items")
    if isinstance(items, dict):
        for value in items.values():
            if isinstance(value, dict):
                value["notifyOwner"] = False
    elif isinstance(items, list):
        for value in items:
            if isinstance(value, dict):
                value["notifyOwner"] = False
    review["notificationPreparedAt"] = datetime.now(timezone.utc).isoformat()
    review["notificationDigest"] = digest
    review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render(*, arm: bool, consume_notify: bool) -> int:
    report = load_json(REPORT)
    registry = load_json(REGISTRY)
    review = load_json(REVIEW, optional=True)
    items, notify, digest = make_payload(report, registry, review)
    checked_at = str(report.get("checkedAt") or "")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    visible = render_text(items, checked_at)
    html_body = "\n".join(line.rstrip() for line in render_html(items, checked_at).splitlines()) + "\n"
    VISIBLE.write_text(visible, encoding="utf-8")
    HTML.write_text(html_body, encoding="utf-8")
    review_ready = bool(items) and all(bool(item["decision"].get("reviewReady")) for item in items)
    unreviewed = [item["repo"] for item in items if not item["decision"].get("reviewReady")]
    enabled = bool(arm and items and notify and review_ready)
    request = {
        "enabled": enabled,
        "requestId": f"tool-updates-{digest[:16]}",
        "to": OWNER,
        "subject": f"VelvetOS · עדכוני כלים · {len(items)} ממתינים",
        "html": str(HTML.relative_to(ROOT)).replace("\\", "/"),
        "visibleText": str(VISIBLE.relative_to(ROOT)).replace("\\", "/"),
        "images": "",
        "embedRemoteImages": False,
        "remoteImageLimit": 0,
        "notificationDigest": digest,
        "pendingCount": len(items),
        "reviewReady": review_ready,
        "unreviewedCount": len(unreviewed),
        "unreviewedRepos": unreviewed,
    }
    REQUEST.write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if enabled and consume_notify and REVIEW.is_file():
        consume_notifications(REVIEW, review, digest)
    print(
        f"UPSTREAM EMAIL rendered pending={len(items)} reviewed={len(items)-len(unreviewed)}/{len(items)} "
        f"notify={str(notify).lower()} armed={str(arm).lower()} enabled={str(enabled).lower()} "
        f"digest={digest[:16]}"
    )
    if arm and items and unreviewed:
        print(
            "BLOCK tool-update email: explicit current review missing for "
            + ", ".join(unreviewed),
            file=sys.stderr,
        )
        return 2
    return 0


def selftest() -> int:
    report = {
        "checkedAt": "2026-09-27T00:00:00+00:00",
        "sources": [
            {
                "repo": "example/runtime",
                "kind": "runtime-source",
                "pendingUpdate": True,
                "newDetection": True,
                "baselineRelease": "v1.0.0",
                "latestRelease": "v1.1.0",
                "changeKinds": ["release"],
            }
        ],
    }
    registry = {
        "sources": [
            {
                "repo": "example/runtime",
                "kind": "runtime-source",
                "integration": ["runtime"],
            }
        ]
    }
    items, notify, digest = make_payload(report, registry, {"items": {}})
    assert len(items) == 1 and not notify and len(digest) == 64
    assert items[0]["decision"]["verdict"] == "review"
    assert items[0]["decision"]["reviewReady"] is False

    reviewed = {
        "items": {
            "example/runtime": {
                "verdict": "update",
                "reasonHe": "בדיקות התאימות עברו.",
                "evidence": ["smoke-pass"],
                "notifyOwner": True,
                "reviewedRemoteHead": "abc123",
                "reviewedRelease": "v1.1.0",
            }
        }
    }
    report["sources"][0]["remoteHead"] = "abc123"
    items, notify, digest = make_payload(report, registry, reviewed)
    assert notify and items[0]["decision"]["reviewReady"] is True
    assert items[0]["decision"]["verdict"] == "update"
    assert "מומלץ לעדכן" in render_text(items, report["checkedAt"])
    print("OK upstream-email selftest separate-owner-email + current-review gate + decision labels")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    render_parser = sub.add_parser("render")
    render_parser.add_argument(
        "--arm",
        action="store_true",
        help="enable the send request only when a new detection/review notification exists",
    )
    render_parser.add_argument(
        "--consume-notify",
        action="store_true",
        help="clear review notifyOwner flags after an enabled request is prepared",
    )
    sub.add_parser("selftest")
    args = parser.parse_args()
    if args.command == "selftest":
        return selftest()
    return render(arm=bool(args.arm), consume_notify=bool(args.consume_notify))


if __name__ == "__main__":
    raise SystemExit(main())
