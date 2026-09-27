#!/usr/bin/env python3
"""Validate Phase 4 engineering-quality integrations without granting authority."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "packages" / "vfharness" / "devtools" / "components.json"
PROFILE_DIR = Path.home() / ".diagram-design" / "profiles"


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        fail(f"missing {rel}")
    return path.read_text(encoding="utf-8-sig")


def git_head(path: Path) -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=path, text=True, capture_output=True)
    if proc.returncode:
        fail(f"cannot read git head for {path}")
    return proc.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    data = json.loads(read("packages/vfharness/devtools/components.json"))
    rows = {row["id"]: row for row in data.get("components", [])}
    expected = {"ponytail", "gstack", "impeccable", "diagram-design"}
    if set(rows) != expected:
        fail("engineering-quality component set mismatch")
    for row in rows.values():
        if row.get("runtime_authority") is not False:
            fail(f"{row['id']} gained runtime authority")
        preflight = json.loads(read(row["cost_preflight"]))
        if preflight.get("expected_recurring_cost") != "0 ILS/month incremental":
            fail(f"{row['id']} recurring cost changed")

    pony = read("packages/vfharness/playbooks/implementation-discipline.md")
    for phrase in ("Does this need to be built at all?", "Existing capability?", "Never simplify away"):
        if phrase not in pony:
            fail(f"Ponytail embed missing: {phrase}")

    gstack = read("packages/vfharness/devtools/gstack-safe-subset.md")
    for allowed in rows["gstack"]["allowlist"]:
        if allowed not in gstack:
            fail(f"gstack allowlist mapping missing {allowed}")
    for denied in ("GBrain", "ship", "land-and-deploy", "setup-deploy"):
        if denied not in gstack:
            fail(f"gstack denylist missing {denied}")

    web = read(".cursor/skills/vf-web-ui-quality/SKILL.md")
    for phrase in ("packages/vfom", "Do not run Impeccable", "Web/UI"):
        if phrase not in web:
            fail(f"Impeccable scope guard missing: {phrase}")

    diagram = read(".cursor/skills/vf-diagram-design/SKILL.md")
    if "architecture" not in diagram or "Instagram posts" not in diagram:
        fail("diagram-design wrapper scope incomplete")

    if read(".diagram-design").strip() != "profile: velvetos":
        fail("root diagram profile marker mismatch")
    if read("instances/velvet-factory/.diagram-design").strip() != "profile: velvet-factory":
        fail("Velvet Factory diagram profile marker mismatch")
    forbidden_hooks = [
        ROOT / ".cursor" / "hooks" / "impeccable.json",
        ROOT / ".claude" / "settings.local.json",
        ROOT / ".github" / "hooks" / "impeccable.json",
    ]
    if any(path.exists() for path in forbidden_hooks):
        fail("broad Impeccable hook detected")

    if args.strict:
        for component_id in ("impeccable", "diagram-design"):
            row = rows[component_id]
            local = ROOT / row["local_source"]
            if not (local / ".git").is_dir():
                fail(f"{component_id} local source not installed")
            if git_head(local) != row["pin"]:
                fail(f"{component_id} local pin mismatch")
        for slug in rows["diagram-design"]["profiles"]:
            profile = PROFILE_DIR / f"{slug}.md"
            if not profile.is_file():
                fail(f"missing diagram profile {slug}")
            text = profile.read_text(encoding="utf-8", errors="replace")
            if f"slug: {slug}" not in text[:500]:
                fail(f"diagram profile header mismatch {slug}")
            if "#101828" not in text:
                fail(f"diagram profile missing canonical Ink token {slug}")

    mode = "strict" if args.strict else "offline"
    print(
        f"OK engineering-quality mode={mode} ponytail=EMBEDDED "
        "gstack=SAFE_SUBSET impeccable=WEB_UI_ONLY diagram=DOCS_ONLY cost=0"
    )


if __name__ == "__main__":
    main()
