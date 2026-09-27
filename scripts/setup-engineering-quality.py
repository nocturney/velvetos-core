#!/usr/bin/env python3
"""Install/remove Phase 4 local engineering-quality sources and diagram profiles."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "packages" / "vfharness" / "devtools" / "components.json"
LOCAL = ROOT / ".local-devtools" / "phase4"
PROFILE_DIR = Path.home() / ".diagram-design" / "profiles"

ACTIVE = ("impeccable", "diagram-design")


def run(*args: str, cwd: Path | None = None) -> str:
    proc = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if proc.returncode:
        raise SystemExit(f"FAIL {' '.join(args)}\n{proc.stdout}{proc.stderr}")
    return proc.stdout.strip()


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8-sig"))


def remove_tree(path: Path) -> None:
    def clear_readonly(func, target, _exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)

    shutil.rmtree(path, onexc=clear_readonly)


def ensure_clone(component: dict) -> None:
    target = ROOT / component["local_source"]
    pin = component["pin"]
    if (target / ".git").is_dir():
        head = run("git", "rev-parse", "HEAD", cwd=target)
        if head == pin:
            print(f"OK source {component['id']} {pin[:12]}")
            return
        remove_tree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.mkdir(parents=True, exist_ok=True)
    run("git", "init", "-q", cwd=target)
    run("git", "remote", "add", "origin", component["source"], cwd=target)
    run("git", "fetch", "-q", "--depth", "1", "origin", pin, cwd=target)
    run("git", "checkout", "-q", "--detach", "FETCH_HEAD", cwd=target)
    head = run("git", "rev-parse", "HEAD", cwd=target)
    if head != pin:
        raise SystemExit(f"FAIL pin mismatch {component['id']}: {head}")
    print(f"OK source {component['id']} {pin[:12]}")


ROLE_OVERRIDES = {
    "velvetos": {
        "paper": ("#F4F6FB", "#101828"),
        "paper-2": ("#FFFFFF", "#151D2E"),
        "ink": ("#171D2C", "#F4F6FB"),
        "ink-strong": ("#101828", "#FFFFFF"),
        "muted": ("#697287", "#BFC6D4"),
        "soft": ("#8A94A8", "#ADB7C9"),
        "rule": ("rgba(16,24,40,0.12)", "rgba(244,246,251,0.12)"),
        "rule-solid": ("#C6CDDC", "rgba(244,246,251,0.25)"),
        "accent": ("#6C7CFF", "#8794FF"),
        "accent-tint": ("rgba(108,124,255,0.10)", "rgba(135,148,255,0.12)"),
        "link": ("#45D7FF", "#78E4FF"),
    },
    "velvet-factory": {
        "paper": ("#F4F6FB", "#101828"),
        "paper-2": ("#FFFFFF", "#151D2E"),
        "ink": ("#171D2C", "#F4F6FB"),
        "ink-strong": ("#101828", "#FFFFFF"),
        "muted": ("#697287", "#BFC6D4"),
        "soft": ("#8A94A8", "#ADB7C9"),
        "rule": ("rgba(16,24,40,0.12)", "rgba(244,246,251,0.12)"),
        "rule-solid": ("#C6CDDC", "rgba(244,246,251,0.25)"),
        "accent": ("#FF4F91", "#FF7AAF"),
        "accent-tint": ("rgba(255,79,145,0.10)", "rgba(255,122,175,0.12)"),
        "link": ("#6C7CFF", "#8794FF"),
    },
}

PURPOSES = {
    "paper": "Page background, default node fill",
    "paper-2": "Diagram container bg, secondary fill",
    "ink": "Primary text, primary stroke",
    "ink-strong": "High-contrast text on accent fills",
    "muted": "Secondary text, default arrow stroke",
    "soft": "Sublabels, boundary labels",
    "rule": "Hairline borders",
    "rule-solid": "Stronger borders, baselines",
    "accent": "Focal / 1-2 max per diagram",
    "accent-tint": "Fill for accent-bordered boxes",
    "link": "HTTP/API calls, external arrows",
}
def render_profile(source: str, slug: str) -> str:
    overrides = ROLE_OVERRIDES[slug]
    tick = chr(96)
    lines = source.splitlines()
    out: list[str] = []
    for line in lines:
        replaced = False
        for role, (light, dark) in overrides.items():
            if line.startswith(f"| {tick}{role}{tick} |"):
                out.append(f"| {tick}{role}{tick} | {PURPOSES[role]} | {tick}{light}{tick} | {tick}{dark}{tick} |")
                replaced = True
                break
        if not replaced:
            out.append(line)
    display = "VelvetOS" if slug == "velvetos" else "Velvet Factory"
    header = (
        "<!-- diagram-design-profile\n"
        f"name: {display}\n"
        f"slug: {slug}\n"
        "source-url: none\n"
        f"created: {date.today().isoformat()}\n"
        f"updated: {date.today().isoformat()}\n"
        "notes: Generated from VelvetOS canonical Ink & Candy documentation tokens\n"
        "-->\n"
    )
    return header + "\n".join(out).rstrip() + "\n"


def install_profiles(diagram: dict) -> None:
    source_path = ROOT / diagram["local_source"] / "skills" / "diagram-design" / "references" / "style-guide.md"
    source = source_path.read_text(encoding="utf-8")
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    for slug in diagram["profiles"]:
        target = PROFILE_DIR / f"{slug}.md"
        target.write_text(render_profile(source, slug), encoding="utf-8")
        print(f"OK profile {slug} {target}")
def uninstall() -> None:
    if LOCAL.exists():
        remove_tree(LOCAL)
        print(f"OK removed {LOCAL}")
    for slug in ("velvetos", "velvet-factory"):
        target = PROFILE_DIR / f"{slug}.md"
        if target.exists():
            text = target.read_text(encoding="utf-8", errors="replace")
            if f"slug: {slug}" in text[:500]:
                target.unlink()
                print(f"OK removed {target}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args()
    registry = load_registry()
    by_id = {row["id"]: row for row in registry["components"]}
    if args.uninstall:
        uninstall()
        return
    for component_id in ACTIVE:
        ensure_clone(by_id[component_id])
    install_profiles(by_id["diagram-design"])
    print("OK engineering-quality local install cost=0 hooks=disabled")


if __name__ == "__main__":
    main()
