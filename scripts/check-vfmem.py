#!/usr/bin/env python3
"""Validate vfmem catalog + live office graph. No network. No send."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from vfmem import (  # noqa: E402
    CATALOG,
    DESK,
    MANIFEST,
    build_graph,
    cmd_who,
    match_routes,
)

ALLOWED_STATUS = {"embed", "skip", "later"}
REQUIRED_PLAYBOOKS = {
    "queries/architecture.md",
    "queries/who.md",
    "queries/impact.md",
    "queries/route.md",
    "queries/dead.md",
    "queries/adr.md",
}
NEED_LOCKS = {
    "no-send-instagram",
    "no-send-gmail",
    "no-invented-prices",
    "no-invented-insights",
    "no-cbm-binary-from-hq",
}


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in (MANIFEST, DESK, CATALOG):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    desk = json.loads(DESK.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    packs = {p["name"] for p in manifest["packs"]}

    if catalog.get("name") != "vfmem":
        fail("catalog name must be vfmem")
    if "vfmem" not in packs:
        fail("vfmem missing from packages/manifest.json")
    if catalog.get("verdict") != "embed-pattern":
        fail("verdict must be embed-pattern (pattern only, no CBM binary)")
    if catalog.get("binary") != "later-if-lead-asks":
        fail("binary must stay later-if-lead-asks")

    for lock in NEED_LOCKS:
        if lock not in catalog.get("locks", []):
            fail(f"missing lock {lock}")

    tools = catalog.get("cbmTools") or []
    if len(tools) < 12:
        fail(f"expected at least 12 CBM tool rows, got {len(tools)}")
    embed = 0
    for row in tools:
        status = row.get("status")
        if status not in ALLOWED_STATUS:
            fail(f"{row.get('cbm')}: bad status {status!r}")
        if status == "embed":
            embed += 1
            rel = row.get("playbook")
            if not rel:
                fail(f"{row.get('cbm')}: embed needs playbook")
            if not (ROOT / "packages" / "vfmem" / rel).is_file():
                fail(f"missing playbook {rel}")
        elif status == "skip" and not row.get("reason"):
            fail(f"{row.get('cbm')}: skip needs reason")
        elif status == "later" and not row.get("note"):
            fail(f"{row.get('cbm')}: later needs note")
    if embed < 8:
        fail(f"expected at least 8 embed rows, got {embed}")

    on_disk = {f"queries/{p.name}" for p in (ROOT / "packages" / "vfmem" / "queries").glob("*.md")}
    if on_disk != REQUIRED_PLAYBOOKS:
        fail(f"query files mismatch disk={sorted(on_disk)}")

    slugs = {row["slug"] for row in desk.get("desk", [])}
    for route in catalog.get("routes", []):
        if route["pack"] not in packs:
            fail(f"route unknown pack {route['pack']}")
        if route["slug"] not in slugs:
            fail(f"route slug not on desk: {route['slug']}")

    graph = build_graph(ROOT)
    pack_nodes = [n for n in graph.nodes.values() if n.label == "Pack"]
    if len(pack_nodes) != len(packs):
        fail(f"graph packs {len(pack_nodes)} != manifest {len(packs)}")
    desk_n = sum(1 for n in graph.nodes.values() if n.label == "Specialist" and n.props.get("onDesk"))
    if desk_n != len(desk.get("desk", [])):
        fail(f"desk specialists {desk_n} != desk list {len(desk.get('desk', []))}")
    if sum(1 for n in graph.nodes.values() if n.label == "Seat") != 5:
        fail("expected 5 seats")
    if sum(1 for n in graph.nodes.values() if n.label == "Law") != len(catalog.get("adrs", [])):
        fail("law nodes != catalog adrs")

    inquiry = cmd_who(graph, catalog, "inquiry")
    route_packs = {r["pack"] for r in inquiry["routes"]}
    if "vfconvert" not in route_packs:
        fail("who inquiry must route to vfconvert")
    brief = match_routes(catalog, "בריף בוקר")
    if not any(r["pack"] == "vfops" for r in brief):
        fail("who בריף בוקר must route to vfops")

    writeup = ROOT / catalog.get("writeup", "docs/VFMEM.md")
    if not writeup.is_file():
        fail(f"missing writeup {writeup}")
    skill = ROOT / catalog.get("skill", "")
    if not skill.is_file():
        fail(f"missing skill {skill}")
    for name in ("ORIGIN.md", "README.md", "EMBED.md", "LOCK.md", "SKILL.md"):
        if not (ROOT / "packages" / "vfmem" / name).is_file():
            fail(f"missing packages/vfmem/{name}")

    print(
        f"OK vfmem embed={embed} packs={len(packs)} "
        f"nodes={len(graph.nodes)} edges={len(graph.edges)} desk={desk_n}"
    )


if __name__ == "__main__":
    main()
