#!/usr/bin/env python3
"""vf_relevant_agents.py — filters .cursor/rules/*.mdc to Velvet Factory-relevant subset.
Read-only: does not delete or move any original rule file, only writes an index.
"""
import json, re
from pathlib import Path

RULES_DIR = Path(__file__).resolve().parent.parent / ".cursor" / "rules"
OUT_JSON = Path(__file__).resolve().parent.parent / "packages" / "velvetos" / "relevant-agents.json"
OUT_MD = Path(__file__).resolve().parent.parent / "packages" / "velvetos" / "RELEVANT-AGENTS.md"

RELEVANT_KEYWORDS = {
    "3d-printing-core": ["3d print", "3d-print", "slicer", "g-code", "gcode", "filament", "cad", "blender", "3d model", "stl"],
    "social-marketing": ["instagram", "social media", "content creator", "content strategist", "brand", "caption", "copywrit", "growth hack", "paid social", "influencer", "carousel", "reel"],
    "sales-ops": ["customer service", "sales", "quote", "pricing", "lead gen", "crm", "inquiry"],
    "finance-lite": ["bookkeep", "invoice", "finance tracker", "pricing analyst"],
    "automation-devops": ["automation", "workflow", "n8n", "mcp", "agent orchestrat", "devops", "api tester"],
    "web-dashboard": ["frontend", "dashboard", "web development", "react", "ui design", "data visualization"],
}
EXCLUDE_HINTS = ["gis", "geograph", "healthcare", "clinical", "legal", "medical", "game", "godot", "blockchain", "fedramp", "drupal", "korean", "chinese", "china-", "japan", "baidu", "douyin", "kuaishou", "bilibili", "feishu", "hospitality", "aging-parent"]

def load_description(path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"description:\s*'(.*?)'", text, re.DOTALL)
    return m.group(1).strip() if m else ""

def classify(slug, description):
    hay = f"{slug} {description}".lower()
    if any(x in hay for x in EXCLUDE_HINTS):
        return None
    for bucket, kws in RELEVANT_KEYWORDS.items():
        if any(kw in hay for kw in kws):
            return bucket
    return None

def main():
    files = sorted(RULES_DIR.glob("*.mdc"))
    results = []
    for f in files:
        slug = f.stem
        desc = load_description(f)
        bucket = classify(slug, desc)
        if bucket:
            results.append({"slug": slug, "bucket": bucket, "description": desc})
    by_bucket = {}
    for r in results:
        by_bucket.setdefault(r["bucket"], []).append(r)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps({"generatedFrom": ".cursor/rules/*.mdc", "totalRules": len(files), "relevantCount": len(results), "buckets": by_bucket}, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Relevant Agents — Velvet Factory filter", "", f"Generated from {len(files)} `.cursor/rules/*.mdc` files. {len(results)} classified as relevant to a solo 3D-printing + Instagram-led business. Keyword-based — review before deleting anything.", "", "Regenerate: `python3 scripts/vf_relevant_agents.py`", ""]
    for bucket, items in sorted(by_bucket.items()):
        lines.append(f"## {bucket} ({len(items)})")
        lines.append("")
        lines.append("| agent | description |")
        lines.append("|---|---|")
        for it in sorted(items, key=lambda x: x["slug"]):
            desc = it["description"][:140].replace("|", "/")
            lines.append(f"| `{it['slug']}` | {desc} |")
        lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"total_rules={len(files)} relevant={len(results)}")

if __name__ == "__main__":
    main()
