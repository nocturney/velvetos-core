#!/usr/bin/env python3
"""
vf_insights_loop.py — Closed measurement-to-learning loop for VelvetOS.
Reads verified numbers from packages/vfinsights/data/posts.csv.
Preferred source: Instagram MCP Insights via scripts/vf_insights_ingest.py.
Owner paste remains a backup. Never invents a number that isn't in the source file.

Usage:
    python3 vf_insights_loop.py --init
    python3 vf_insights_loop.py --data packages/vfinsights/data/posts.csv
"""
import argparse, csv, json, statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "data"
TEMPLATE_PATH = DATA_DIR / "posts.csv"
LEARNINGS_PATH = HERE.parent / "LEARNINGS.md"
FIELDS = ["post_id", "date", "type", "reach", "likes", "saves", "comments", "caption_style", "views", "shares", "source"]

# Do not recommend a format/style winner below this measured-post sample size.
MIN_MEASURED_POSTS_FOR_RECOMMENDATION = 3
MIN_STYLES_OR_DISTINCT = 3  # at least 3 measured posts before any "favor style" recommendation

def init_template():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if TEMPLATE_PATH.exists():
        print(f"already exists: {TEMPLATE_PATH}")
        return
    with open(TEMPLATE_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(FIELDS)
        w.writerow(["DcqkjOLlYVX", "2026-08-30", "reel", "", "", "", "", "תהליך-קצר", "", "", ""])
    print(f"wrote template: {TEMPLATE_PATH}")
    print("Fill via Instagram MCP (scripts/vf_insights_ingest.py) or owner paste. Leave blank if unknown — do not guess.")

def load_rows(path):
    """Load CSV rows. Preserve explicit 0 vs blank: blank → None metric; '0' stays 0."""
    rows = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            # Keep raw cell text so analyze can distinguish "" (unknown) from "0" (measured zero).
            rows.append({k: (v if v is not None else "") for k, v in row.items()})
            for k, v in list(rows[-1].items()):
                if isinstance(v, str):
                    rows[-1][k] = v.strip()
    return rows

def to_float(v):
    """Blank/missing → None (אין ספירה). Explicit '0' → 0.0 (preserved measured zero from MCP)."""
    if v is None:
        return None
    s = str(v).strip()
    if s == "":
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None

def analyze(rows):
    measured = [r for r in rows if to_float(r.get("reach")) is not None]
    unmeasured = [r for r in rows if to_float(r.get("reach")) is None]
    by_style = {}
    for r in measured:
        style = r.get("caption_style") or "unknown"
        reach = to_float(r["reach"])
        if reach is None:
            continue
        saves = to_float(r.get("saves"))
        # missing saves ≠ 0 for rate; only compute when saves present (including explicit 0)
        engagement = (saves / reach) if (saves is not None and reach) else None
        by_style.setdefault(style, []).append({"reach": reach, "engagement_rate": engagement})
    style_summary = []
    for style, items in by_style.items():
        reaches = [i["reach"] for i in items]
        rates = [i["engagement_rate"] for i in items if i["engagement_rate"] is not None]
        style_summary.append({"style": style, "n_posts": len(items),
                               "avg_reach": round(statistics.mean(reaches), 1) if reaches else None,
                               "avg_engagement_rate": round(statistics.mean(rates), 4) if rates else None})
    style_summary.sort(
        key=lambda s: (
            s["avg_engagement_rate"] is not None,
            s["avg_engagement_rate"] or 0,
            s["avg_reach"] or 0,
        ),
        reverse=True,
    )
    n_measured = len(measured)
    can_recommend = n_measured >= MIN_MEASURED_POSTS_FOR_RECOMMENDATION and n_measured >= MIN_STYLES_OR_DISTINCT
    return {
        "n_total": len(rows),
        "n_measured": n_measured,
        "n_unmeasured": len(unmeasured),
        "unmeasured_ids": [r["post_id"] for r in unmeasured],
        "style_ranking": style_summary,
        "can_recommend": can_recommend,
        "min_measured_for_recommendation": MIN_MEASURED_POSTS_FOR_RECOMMENDATION,
    }

def write_learnings(result):
    lines = ["# Learnings — closed measurement loop", "",
              f"Measured {result['n_measured']} of {result['n_total']} posts. "
              f"{result['n_unmeasured']} still have no real number (excluded from ranking, not guessed).", "",
              "Source preference: Instagram MCP verified Insights → `scripts/vf_insights_ingest.py` → `data/posts.csv`.",
              "Missing metric = אין ספירה / blank — never invent, never coerce unavailable → 0.",
              "Explicit CSV `0` is preserved as measured zero (MCP returned 0); blank cell stays unknown.",
              "The `source` column proves MCP origin when set to `instagram_mcp` (vs owner paste / blank).", ""]
    if result["n_unmeasured"]:
        lines.append("## Missing data (fetch via Instagram MCP before next brief)")
        for pid in result["unmeasured_ids"]:
            lines.append(f"- `{pid}` — אין ספירה (run get_media_insights / vf_insights_ingest)")
        lines.append("")
    if result["style_ranking"]:
        lines.append("## Caption/format style ranked by engagement rate")
        lines.append("")
        lines.append("| style | posts | avg reach | avg engagement rate |")
        lines.append("|---|---|---|---|")
        for s in result["style_ranking"]:
            er = s["avg_engagement_rate"] if s["avg_engagement_rate"] is not None else "אין ספירה"
            lines.append(f"| {s['style']} | {s['n_posts']} | {s['avg_reach']} | {er} |")
        lines.append("")
        if result.get("can_recommend"):
            best = result["style_ranking"][0]
            if best.get("avg_engagement_rate") is not None:
                lines.append(
                    f"**Recommendation for next post:** favor style `{best['style']}` "
                    f"(highest measured engagement rate so far: {best['avg_engagement_rate']})."
                )
            else:
                lines.append(
                    f"**Recommendation for next post:** favor style `{best['style']}` "
                    f"(highest measured avg reach so far: {best['avg_reach']}; engagement rate אין ספירה)."
                )
        else:
            lines.append(
                f"**Recommendation:** insufficient evidence — no format/style winner yet "
                f"(need ≥{result.get('min_measured_for_recommendation', MIN_MEASURED_POSTS_FOR_RECOMMENDATION)} "
                f"measured posts; have {result['n_measured']}). Ranking table kept for transparency."
            )
    else:
        lines.append("No measured posts yet — ingest Instagram MCP Insights first.")
        lines.append("")
        lines.append("**Recommendation:** insufficient evidence — no format/style winner yet")
    LEARNINGS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {LEARNINGS_PATH}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(TEMPLATE_PATH))
    ap.add_argument("--init", action="store_true")
    args = ap.parse_args()
    if args.init:
        init_template()
        return
    path = Path(args.data)
    if not path.exists():
        print(f"no data file at {path} — run with --init first")
        return
    rows = load_rows(path)
    result = analyze(rows)
    write_learnings(result)
    print(json.dumps({k: v for k, v in result.items() if k != "style_ranking"}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
