#!/usr/bin/env python3
"""
vf_insights_loop.py — Closed measurement-to-learning loop for VelvetOS.
No API key required, no paid tier required. Reads real numbers from a local
CSV (manual entry from Instagram Professional Dashboard, or a free-tier
export from any analytics tool) and ranks content styles by measured
engagement — never invents a number that isn't in the source file.

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
FIELDS = ["post_id", "date", "type", "reach", "likes", "saves", "comments", "caption_style"]

def init_template():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if TEMPLATE_PATH.exists():
        print(f"already exists: {TEMPLATE_PATH}")
        return
    with open(TEMPLATE_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(FIELDS)
        w.writerow(["DcqkjOLlYVX", "2026-08-30", "reel", "", "", "", "", "תהליך-קצר"])
    print(f"wrote template: {TEMPLATE_PATH}")
    print("Fill real numbers from Instagram Professional Dashboard. Leave blank if unknown — do not guess.")

def load_rows(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append({k: (v or "").strip() for k, v in row.items()})
    return rows

def to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def analyze(rows):
    measured = [r for r in rows if to_float(r.get("reach")) is not None]
    unmeasured = [r for r in rows if to_float(r.get("reach")) is None]
    by_style = {}
    for r in measured:
        style = r.get("caption_style") or "unknown"
        reach = to_float(r["reach"]) or 0
        saves = to_float(r.get("saves")) or 0
        engagement = reach and (saves / reach) or 0
        by_style.setdefault(style, []).append({"reach": reach, "engagement_rate": engagement})
    style_summary = []
    for style, items in by_style.items():
        reaches = [i["reach"] for i in items]
        rates = [i["engagement_rate"] for i in items]
        style_summary.append({"style": style, "n_posts": len(items),
                               "avg_reach": round(statistics.mean(reaches), 1) if reaches else None,
                               "avg_engagement_rate": round(statistics.mean(rates), 4) if rates else None})
    style_summary.sort(key=lambda s: (s["avg_engagement_rate"] or 0), reverse=True)
    return {"n_total": len(rows), "n_measured": len(measured), "n_unmeasured": len(unmeasured),
            "unmeasured_ids": [r["post_id"] for r in unmeasured], "style_ranking": style_summary}

def write_learnings(result):
    lines = ["# Learnings — closed measurement loop", "",
              f"Measured {result['n_measured']} of {result['n_total']} posts. "
              f"{result['n_unmeasured']} still have no real number (excluded from ranking, not guessed).", ""]
    if result["n_unmeasured"]:
        lines.append("## Missing data (fill before next brief)")
        for pid in result["unmeasured_ids"]:
            lines.append(f"- `{pid}` — open Instagram Professional Dashboard")
        lines.append("")
    if result["style_ranking"]:
        lines.append("## Caption/format style ranked by engagement rate")
        lines.append("")
        lines.append("| style | posts | avg reach | avg engagement rate |")
        lines.append("|---|---|---|---|")
        for s in result["style_ranking"]:
            lines.append(f"| {s['style']} | {s['n_posts']} | {s['avg_reach']} | {s['avg_engagement_rate']} |")
        lines.append("")
        best = result["style_ranking"][0]
        lines.append(f"**Recommendation for next post:** favor style `{best['style']}` "
                      f"(highest measured engagement rate so far: {best['avg_engagement_rate']}).")
    else:
        lines.append("No measured posts yet — fill `data/posts.csv` first.")
    LEARNINGS_PATH.write_text("\n".join(lines), encoding="utf-8")
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
