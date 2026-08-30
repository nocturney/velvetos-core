#!/usr/bin/env python3
"""Check vfgraft office graph: nodes, wikilinks, sources on disk. No network. No send."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "manifest.json"
GRAPH = ROOT / "packages" / "vfgraft" / "graph.json"
GRAPH_DIR = ROOT / "packages" / "vfgraft" / "graph"
WIKI = re.compile(r"\[\[([a-z0-9-]+)\]\]")
LINK_LINE = re.compile(r"^-\s+([a-z_]+)\s+\[\[([a-z0-9-]+)\]\]\s*$")
REQUIRED_LOCKS = {
    "no-npm-graft",
    "no-graft-mcp",
    "no-second-coding-agent",
    "no-send-instagram",
    "no-send-gmail",
    "no-invented-prices",
}
REQUIRED_FILES = (
    "packages/vfgraft/MAP.md",
    "packages/vfgraft/EMBED.md",
    "packages/vfgraft/LOCK.md",
    "packages/vfgraft/README.md",
    "packages/vfgraft/SKILL.md",
    "packages/vfgraft/ORIGIN.md",
    "docs/GRAFT.md",
    ".cursor/skills/vf-graft-map/SKILL.md",
    ".cursor/rules/vfgraft.mdc",
)


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not MANIFEST.is_file():
        fail(f"missing {MANIFEST}")
    if not GRAPH.is_file():
        fail(f"missing {GRAPH}")

    manifest = json.loads(MANIFEST.read_text())
    graph = json.loads(GRAPH.read_text())
    pack_names = {p["name"] for p in manifest["packs"]}

    if graph.get("name") != "vfgraft":
        fail("graph name must be vfgraft")
    if graph.get("verdict") != "embed-pattern-skip-runtime":
        fail("verdict must be embed-pattern-skip-runtime")
    if graph.get("source", {}).get("url") != "https://github.com/trailhq/Graft":
        fail("source url must be trailhq/Graft")
    if "vfgraft" not in pack_names:
        fail("vfgraft missing from packages/manifest.json")

    locks = set(graph.get("locks") or [])
    for need in REQUIRED_LOCKS:
        if need not in locks:
            fail(f"missing lock {need}")

    verbs = set(graph.get("verbs") or [])
    nodes = graph.get("nodes") or []
    if len(nodes) < 8:
        fail(f"expected at least 8 nodes, got {len(nodes)}")

    ids = [n.get("id") for n in nodes]
    if len(ids) != len(set(ids)):
        fail("duplicate node ids")
    id_set = set(ids)

    for rel in REQUIRED_FILES:
        if not (ROOT / rel).is_file():
            fail(f"missing {rel}")

    on_disk = {p.name[:-3] for p in GRAPH_DIR.glob("*.md")}
    if on_disk != id_set:
        fail(f"graph/ files mismatch json ids disk={sorted(on_disk)} json={sorted(id_set)}")

    link_count = 0
    source_count = 0
    for node in nodes:
        nid = node["id"]
        rel = node.get("file")
        if rel != f"graph/{nid}.md":
            fail(f"{nid}: file must be graph/{nid}.md")
        path = ROOT / "packages" / "vfgraft" / rel
        if not path.is_file():
            fail(f"{nid}: missing {rel}")
        if not node.get("summary"):
            fail(f"{nid}: missing summary")
        if node.get("type") not in {
            "constraint",
            "flow",
            "system",
            "boundary",
            "job",
            "impact",
        }:
            fail(f"{nid}: bad type {node.get('type')!r}")

        text = path.read_text()
        if f"# {nid}" not in text.splitlines()[:3]:
            fail(f"{nid}: markdown title must start with # {nid}")

        sources = node.get("sources") or []
        if len(sources) < 2:
            fail(f"{nid}: need at least 2 sources")
        for src in sources:
            source_count += 1
            if not (ROOT / src).is_file():
                fail(f"{nid}: source missing {src}")
            if src not in text:
                fail(f"{nid}: source {src} not listed in markdown")

        json_links = {(row["verb"], row["to"]) for row in node.get("links") or []}
        if not json_links:
            fail(f"{nid}: no links")
        md_links: set[tuple[str, str]] = set()
        in_links = False
        for line in text.splitlines():
            if line.strip() == "## Links":
                in_links = True
                continue
            if in_links and line.startswith("## "):
                break
            if in_links:
                m = LINK_LINE.match(line.strip())
                if line.startswith("-") and not m:
                    fail(f"{nid}: bad link line {line!r}")
                if m:
                    md_links.add((m.group(1), m.group(2)))

        if json_links != md_links:
            fail(f"{nid}: links json={sorted(json_links)} md={sorted(md_links)}")

        for verb, dest in json_links:
            link_count += 1
            if verb not in verbs:
                fail(f"{nid}: verb {verb!r} not in graph.verbs")
            if dest not in id_set:
                fail(f"{nid}: link to unknown node {dest}")
            if dest == nid:
                fail(f"{nid}: self-link")

        extras = set(WIKI.findall(text)) - id_set
        if extras:
            fail(f"{nid}: wikilink to unknown {sorted(extras)}")

    map_text = (ROOT / "packages/vfgraft/MAP.md").read_text()
    for nid in ids:
        if nid not in map_text:
            fail(f"MAP.md missing node {nid}")

    desk_rule = (ROOT / ".cursor/rules/velvet-factory-desk.mdc").read_text()
    if "packages/vfgraft/MAP.md" not in desk_rule:
        fail("desk rule must point at packages/vfgraft/MAP.md")

    print(
        f"OK nodes={len(nodes)} links={link_count} "
        f"sources={source_count} packs={len(pack_names)}"
    )


if __name__ == "__main__":
    main()
