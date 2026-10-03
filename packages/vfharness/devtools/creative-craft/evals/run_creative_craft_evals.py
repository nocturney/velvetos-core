#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
from pathlib import Path

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def aggregate_markdown(skill_dir):
    parts = []
    for path in sorted(skill_dir.rglob("*.md")):
        parts.append(path.read_text(encoding="utf-8-sig", errors="replace"))
    return "\n".join(parts).lower()

def description(skill_file):
    text = skill_file.read_text(encoding="utf-8-sig", errors="replace")
    match = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
    return (match.group(1).strip() if match else "").lower()

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--skills-root", required=True)
    ap.add_argument("--registry", required=True)
    ap.add_argument("--mode", choices=["baseline", "candidate"], required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cases", default=str(here / "cases.json"))
    ap.add_argument("--fixtures", default=str(here / "fixtures" / "manifest.json"))
    args = ap.parse_args()

    cases_doc = load_json(args.cases)
    fixture_doc = load_json(args.fixtures)
    registry = load_json(args.registry)
    skills_root = Path(args.skills_root)
    fixture_root = Path(args.fixtures).parent
    fixtures = {x["id"]: x for x in fixture_doc["fixtures"]}
    rows = []
    total = 0

    for case in cases_doc["cases"]:
        skill_id = case[f"{args.mode}_specialist"]
        skill_dir = skills_root / skill_id
        skill_file = skill_dir / "SKILL.md"
        aggregate = aggregate_markdown(skill_dir) if skill_file.exists() else ""
        desc = description(skill_file) if skill_file.exists() else ""
        checks = {}

        fx = fixtures.get(case["fixture"])
        fx_path = fixture_root / fx["file"] if fx else None
        checks["fixture_hash"] = bool(fx and fx_path.exists() and sha256(fx_path) == fx["sha256"])
        checks["specialist_exists"] = skill_file.exists()
        checks["trigger_coverage"] = bool(skill_file.exists() and all(term.lower() in desc for term in case["trigger_terms"]))
        checks["required_references"] = bool(skill_file.exists() and all((skill_dir / "references" / name).exists() for name in case["required_references"]))
        checks["concept_coverage"] = bool(skill_file.exists() and all(term.lower() in aggregate for term in case["required_concepts"]))
        checks["contracts"] = bool(skill_file.exists() and "hard stops" in aggregate and "completion contract" in aggregate)
        pipeline = registry.get("pipelines", {}).get(case["pipeline"])
        checks["pipeline_binding"] = bool(pipeline and skill_id in pipeline.get("skills", []))
        score = sum(1 for value in checks.values() if value)
        total += score
        rows.append({
            "id": case["id"],
            "specialist": skill_id,
            "pipeline": case["pipeline"],
            "score": score,
            "max_score": len(checks),
            "checks": checks,
            "manual_criteria": case["manual_criteria"],
        })

    result = {
        "schema": "velvetos.creative-craft.eval-result.v1",
        "mode": args.mode,
        "version": cases_doc[f"{args.mode}_version"],
        "cases": rows,
        "score": total,
        "max_score": sum(row["max_score"] for row in rows),
        "all_structural_pass": all(row["score"] == row["max_score"] for row in rows),
        "manual_artifact_review": "required separately; this runner does not pretend perceptual review happened",
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
