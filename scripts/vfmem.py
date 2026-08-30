#!/usr/bin/env python3
"""HQ knowledge graph — CBM-style queries over Velvet Factory maps.

Builds the graph each run from packages/manifest.json, .cursor/vf-desk.json,
.cursor/agency-agents.json, and .cursor/skills. No SQLite. No network. No send.

Pattern source: https://github.com/DeusData/codebase-memory-mcp
Do not install their binary from this repo.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "packages" / "manifest.json"
DESK = ROOT / ".cursor" / "vf-desk.json"
AGENCY = ROOT / ".cursor" / "agency-agents.json"
CATALOG = ROOT / "packages" / "vfmem" / "catalog.json"
SKILLS = ROOT / ".cursor" / "skills"

LABELS = (
    "Pack",
    "Seat",
    "Specialist",
    "Tool",
    "Skill",
    "Law",
    "Stage",
    "Route",
)


@dataclass
class Node:
    id: str
    label: str
    name: str
    text: str = ""
    props: dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    src: str
    rel: str
    dst: str


@dataclass
class Graph:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    out: dict[str, list[Edge]] = field(default_factory=lambda: defaultdict(list))
    inn: dict[str, list[Edge]] = field(default_factory=lambda: defaultdict(list))

    def add(self, node: Node) -> None:
        self.nodes[node.id] = node

    def link(self, src: str, rel: str, dst: str) -> None:
        edge = Edge(src, rel, dst)
        self.edges.append(edge)
        self.out[src].append(edge)
        self.inn[dst].append(edge)

    def neighbors(self, nid: str, *, both: bool = True) -> list[tuple[str, str, str]]:
        rows: list[tuple[str, str, str]] = []
        for e in self.out.get(nid, []):
            rows.append((e.src, e.rel, e.dst))
        if both:
            for e in self.inn.get(nid, []):
                rows.append((e.src, e.rel, e.dst))
        return rows


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[0-9A-Za-z\u0590-\u05FF]+", text.lower()) if len(t) > 1}


def _nid(label: str, key: str) -> str:
    return f"{label}:{key}"


def build_graph(root: Path = ROOT) -> Graph:
    manifest = _load_json(root / "packages" / "manifest.json")
    desk = _load_json(root / ".cursor" / "vf-desk.json")
    agency = _load_json(root / ".cursor" / "agency-agents.json")
    catalog = _load_json(root / "packages" / "vfmem" / "catalog.json")
    g = Graph()

    pack_summaries = {p["name"]: p for p in manifest.get("packs", [])}
    for name, row in pack_summaries.items():
        g.add(
            Node(
                id=_nid("Pack", name),
                label="Pack",
                name=name,
                text=f"{name} {row.get('summary', '')}",
                props={
                    "summary": row.get("summary", ""),
                    "vendorStatus": row.get("vendorStatus", ""),
                    "bcId": row.get("bcId", ""),
                },
            )
        )

    for tool_id, tool in (desk.get("tools") or {}).items():
        g.add(
            Node(
                id=_nid("Tool", tool_id),
                label="Tool",
                name=tool_id,
                text=f"{tool_id} {tool.get('useWhen', '')} {tool.get('mode', '')} {tool.get('status', '')}",
                props=dict(tool),
            )
        )

    desk_slugs = {row["slug"] for row in desk.get("desk", []) if row.get("slug")}
    for agent in agency.get("agents", []):
        slug = agent["slug"]
        on_desk = slug in desk_slugs
        g.add(
            Node(
                id=_nid("Specialist", slug),
                label="Specialist",
                name=slug,
                text=f"{slug} {agent.get('name', '')} {agent.get('description', '')} {agent.get('division', '')}",
                props={
                    "title": agent.get("name", ""),
                    "division": agent.get("division", ""),
                    "onDesk": on_desk,
                    "ruleFile": agent.get("ruleFile", ""),
                },
            )
        )

    for row in desk.get("desk", []):
        slug = row["slug"]
        node = g.nodes[_nid("Specialist", slug)]
        job = row.get("job", "")
        node.text = f"{node.text} {job} {' '.join(row.get('packs', []))}"
        node.props["job"] = job
        node.props["deskPacks"] = list(row.get("packs", []))
        for pack in row.get("packs", []):
            if _nid("Pack", pack) in g.nodes:
                g.link(_nid("Specialist", slug), "ON_PACK", _nid("Pack", pack))
        for tool in row.get("tools", []):
            if _nid("Tool", tool) in g.nodes:
                g.link(_nid("Specialist", slug), "USES_TOOL", _nid("Tool", tool))

    for seat in desk.get("seats", []):
        sid = seat["id"]
        g.add(
            Node(
                id=_nid("Seat", sid),
                label="Seat",
                name=seat.get("he") or sid,
                text=f"{sid} {seat.get('he', '')} {seat.get('decides', '')} {' '.join(seat.get('packs', []))}",
                props={"he": seat.get("he", ""), "decides": seat.get("decides", "")},
            )
        )
        for pack in seat.get("packs", []):
            if _nid("Pack", pack) in g.nodes:
                g.link(_nid("Seat", sid), "HAS_PACK", _nid("Pack", pack))
        for slug in seat.get("specialists", []):
            if _nid("Specialist", slug) in g.nodes:
                g.link(_nid("Seat", sid), "HAS_SPECIALIST", _nid("Specialist", slug))
        for tool in seat.get("tools", []):
            if _nid("Tool", tool) in g.nodes:
                g.link(_nid("Seat", sid), "USES_TOOL", _nid("Tool", tool))

    skills_dir = root / ".cursor" / "skills"
    listed_skills = list(desk.get("skills") or [])
    seen_skills: set[str] = set()
    for rel in listed_skills:
        path = root / rel
        key = Path(rel).parent.name
        seen_skills.add(key)
        body = path.read_text(encoding="utf-8") if path.is_file() else ""
        g.add(
            Node(
                id=_nid("Skill", key),
                label="Skill",
                name=key,
                text=f"{key} {body[:800]}",
                props={"path": rel, "onDesk": True},
            )
        )

    if skills_dir.is_dir():
        for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
            key = skill_md.parent.name
            if key in seen_skills:
                continue
            body = skill_md.read_text(encoding="utf-8")
            rel = str(skill_md.relative_to(root))
            g.add(
                Node(
                    id=_nid("Skill", key),
                    label="Skill",
                    name=key,
                    text=f"{key} {body[:800]}",
                    props={"path": rel, "onDesk": False},
                )
            )

    stages = list(desk.get("pipeline") or [])
    for i, stage in enumerate(stages):
        g.add(
            Node(
                id=_nid("Stage", stage),
                label="Stage",
                name=stage,
                text=stage,
                props={"index": i},
            )
        )
        if i > 0:
            g.link(_nid("Stage", stages[i - 1]), "NEXT", _nid("Stage", stage))

    for adr in catalog.get("adrs", []):
        aid = adr["id"]
        g.add(
            Node(
                id=_nid("Law", aid),
                label="Law",
                name=aid,
                text=f"{aid} {adr.get('text', '')}",
                props={"text": adr.get("text", ""), "source": adr.get("source", "")},
            )
        )

    for i, route in enumerate(catalog.get("routes", [])):
        rid = f"r{i}"
        g.add(
            Node(
                id=_nid("Route", rid),
                label="Route",
                name=route["pack"],
                text=" ".join(route.get("q", [])),
                props=dict(route),
            )
        )
        if _nid("Pack", route["pack"]) in g.nodes:
            g.link(_nid("Route", rid), "ROUTES_PACK", _nid("Pack", route["pack"]))
        if _nid("Specialist", route["slug"]) in g.nodes:
            g.link(_nid("Route", rid), "ROUTES_SPECIALIST", _nid("Specialist", route["slug"]))
        if route.get("tool") and _nid("Tool", route["tool"]) in g.nodes:
            g.link(_nid("Route", rid), "ROUTES_TOOL", _nid("Tool", route["tool"]))

    return g


def score_node(node: Node, query: str) -> int:
    q = query.strip().lower()
    if not q:
        return 0
    score = 0
    ident = node.id.lower()
    name = node.name.lower()
    if q == name or q == ident or ident.endswith(":" + q):
        score += 100
    if q in name or q in ident:
        score += 40
    qt = _tokens(query)
    nt = _tokens(f"{node.id} {node.name} {node.text}")
    if qt:
        score += 12 * len(qt & nt)
    return score


def search(
    graph: Graph, query: str, *, labels: Iterable[str] | None = None, limit: int = 8
) -> list[tuple[int, Node]]:
    want = set(labels) if labels else None
    hits: list[tuple[int, Node]] = []
    for node in graph.nodes.values():
        if want and node.label not in want:
            continue
        s = score_node(node, query)
        if s > 0:
            hits.append((s, node))
    hits.sort(key=lambda x: (-x[0], x[1].label, x[1].id))
    return hits[:limit]


def match_routes(catalog: dict[str, Any], query: str) -> list[dict[str, Any]]:
    qt = _tokens(query)
    raw = query.strip().lower()
    hits: list[dict[str, Any]] = []
    for route in catalog.get("routes", []):
        phrases = [p.lower() for p in route.get("q", [])]
        if any(p == raw or p in raw or raw in p for p in phrases):
            hits.append(route)
            continue
        for phrase in phrases:
            if _tokens(phrase) & qt:
                hits.append(route)
                break
    return hits


def resolve_node(graph: Graph, key: str) -> Node | None:
    if key in graph.nodes:
        return graph.nodes[key]
    for label in LABELS:
        nid = _nid(label, key)
        if nid in graph.nodes:
            return graph.nodes[nid]
    hits = search(graph, key, limit=1)
    return hits[0][1] if hits else None


def blast_radius(graph: Graph, start: Node, depth: int = 2) -> list[tuple[int, str, str, str]]:
    seen = {start.id}
    frontier = [start.id]
    out: list[tuple[int, str, str, str]] = []
    for d in range(1, depth + 1):
        nxt: list[str] = []
        for nid in frontier:
            for src, rel, dst in graph.neighbors(nid, both=True):
                other = dst if src == nid else src
                if other in seen:
                    continue
                seen.add(other)
                nxt.append(other)
                out.append((d, src, rel, dst))
        frontier = nxt
    return out


def git_changed_files(root: Path = ROOT) -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "diff", "--name-only", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def map_path_to_nodes(graph: Graph, rel: str) -> list[Node]:
    found: list[Node] = []
    parts = Path(rel).parts
    if len(parts) >= 2 and parts[0] == "packages":
        node = graph.nodes.get(_nid("Pack", parts[1]))
        if node:
            found.append(node)
    if len(parts) >= 3 and parts[0] == ".cursor" and parts[1] == "rules":
        slug = Path(parts[2]).stem
        node = graph.nodes.get(_nid("Specialist", slug))
        if node:
            found.append(node)
    if len(parts) >= 3 and parts[0] == ".cursor" and parts[1] == "skills":
        node = graph.nodes.get(_nid("Skill", parts[2]))
        if node:
            found.append(node)
    if rel.startswith("constitution/"):
        for node in graph.nodes.values():
            if node.label == "Law":
                found.append(node)
    return found


def emit(obj: Any, *, as_json: bool) -> None:
    if as_json:
        json.dump(obj, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return
    if isinstance(obj, str):
        sys.stdout.write(obj)
        if not obj.endswith("\n"):
            sys.stdout.write("\n")
        return
    sys.stdout.write(format_human(obj))
    if not str(obj).endswith("\n"):
        sys.stdout.write("\n")


def format_human(obj: Any) -> str:
    if isinstance(obj, dict) and "lines" in obj:
        return "\n".join(obj["lines"])
    return json.dumps(obj, ensure_ascii=False, indent=2)


def cmd_architecture(graph: Graph, catalog: dict[str, Any]) -> dict[str, Any]:
    counts = {label: 0 for label in LABELS}
    for node in graph.nodes.values():
        counts[node.label] = counts.get(node.label, 0) + 1
    desk_n = sum(1 for n in graph.nodes.values() if n.label == "Specialist" and n.props.get("onDesk"))
    warehouse_n = counts["Specialist"] - desk_n
    seats = [n for n in graph.nodes.values() if n.label == "Seat"]
    stages = [n.name for n in graph.nodes.values() if n.label == "Stage"]
    stages.sort(key=lambda s: graph.nodes[_nid("Stage", s)].props.get("index", 0))
    tools = sorted(n.name for n in graph.nodes.values() if n.label == "Tool")
    unseated = sorted(
        n.name
        for n in graph.nodes.values()
        if n.label == "Pack" and not graph.inn.get(n.id)
    )
    lines = [
        "VF HQ architecture (from maps, not invented)",
        f"nodes={len(graph.nodes)} edges={len(graph.edges)}",
        f"seats={counts['Seat']} desk={desk_n} warehouse={warehouse_n} packs={counts['Pack']}",
        f"tools={', '.join(tools)}",
        f"pipeline={' → '.join(stages)}",
        "seats:",
    ]
    for seat in sorted(seats, key=lambda n: n.id):
        packs = [e.dst.split(":", 1)[1] for e in graph.out[seat.id] if e.rel == "HAS_PACK"]
        lines.append(f"  {seat.props.get('he') or seat.name}: {', '.join(packs)}")
    lines.append("unseated packs (research / HQ-native, not a sixth seat):")
    for name in unseated:
        lines.append(f"  {name}")
    lines.append(f"laws={counts['Law']} routes={counts['Route']}")
    lines.append("query first: python3 scripts/vfmem.py who <job>")
    return {
        "counts": counts,
        "desk": desk_n,
        "warehouse": warehouse_n,
        "tools": tools,
        "pipeline": stages,
        "unseated": unseated,
        "source": catalog["source"]["url"],
        "lines": lines,
    }


def cmd_schema(graph: Graph) -> dict[str, Any]:
    rels: dict[str, int] = defaultdict(int)
    for e in graph.edges:
        rels[e.rel] += 1
    lines = ["graph schema", f"labels: {', '.join(LABELS)}"]
    for rel, n in sorted(rels.items()):
        lines.append(f"  {rel} {n}")
    return {"labels": list(LABELS), "rels": dict(rels), "lines": lines}


def cmd_who(graph: Graph, catalog: dict[str, Any], query: str) -> dict[str, Any]:
    routes = match_routes(catalog, query)
    hits = search(graph, query, labels=("Specialist", "Pack", "Skill", "Seat", "Tool"), limit=16)
    qnorm = query.strip().lower().lstrip("@")
    filtered: list[tuple[int, Node]] = []
    for score, node in hits:
        if node.label == "Specialist" and not node.props.get("onDesk"):
            if qnorm not in {node.name.lower(), node.id.lower()}:
                continue
        filtered.append((score, node))
    hits = filtered[:8]
    lines = [f"who: {query}"]
    if routes:
        lines.append("desk route (from vfmem catalog = desk table):")
        for r in routes:
            lines.append(f"  pack={r['pack']} @{r['slug']} tool={r.get('tool', '')}")
    lines.append("graph hits:")
    for score, node in hits:
        extra = node.props.get("job") or node.props.get("summary") or node.props.get("he") or ""
        extra = extra[:80]
        lines.append(f"  {score:>3} {node.label}:{node.name} {extra}")
    lines.append("do not dump the 273-rule warehouse. mention only the slug above.")
    return {
        "query": query,
        "routes": routes,
        "hits": [{"score": s, "id": n.id, "label": n.label, "name": n.name} for s, n in hits],
        "lines": lines,
    }


def cmd_search(graph: Graph, query: str) -> dict[str, Any]:
    hits = search(graph, query, limit=12)
    lines = [f"search: {query}"]
    for score, node in hits:
        lines.append(f"  {score:>3} {node.id}")
    return {
        "query": query,
        "hits": [{"score": s, "id": n.id} for s, n in hits],
        "lines": lines,
    }


def cmd_impact(graph: Graph, key: str) -> dict[str, Any]:
    node = resolve_node(graph, key)
    if node is None:
        return {"error": f"unknown node {key}", "lines": [f"impact: unknown {key}"]}
    rows = blast_radius(graph, node, depth=2)
    lines = [f"impact: {node.id}"]
    for depth, src, rel, dst in rows:
        lines.append(f"  d{depth} {src} -[{rel}]- {dst}")
    return {
        "start": node.id,
        "edges": [{"d": d, "src": s, "rel": r, "dst": t} for d, s, r, t in rows],
        "lines": lines,
    }


def cmd_impact_git(graph: Graph, root: Path = ROOT) -> dict[str, Any]:
    files = git_changed_files(root)
    mapped: dict[str, list[str]] = defaultdict(list)
    for rel in files:
        for node in map_path_to_nodes(graph, rel):
            mapped[node.id].append(rel)
    lines = ["impact --git (unstaged+staged vs HEAD)"]
    if not files:
        lines.append("  no local diff vs HEAD")
    for nid, paths in sorted(mapped.items()):
        lines.append(f"  {nid}")
        for p in paths:
            lines.append(f"    {p}")
    orphan = [f for f in files if not map_path_to_nodes(graph, f)]
    if orphan:
        lines.append("  unmapped:")
        for p in orphan:
            lines.append(f"    {p}")
    return {"files": files, "mapped": dict(mapped), "unmapped": orphan, "lines": lines}


def cmd_route(graph: Graph, catalog: dict[str, Any], query: str) -> dict[str, Any]:
    stages = [n for n in graph.nodes.values() if n.label == "Stage"]
    stages.sort(key=lambda n: n.props.get("index", 0))
    names = [n.name for n in stages]
    picked = None
    ql = query.strip()
    for n in stages:
        if ql == n.name or ql in n.name or n.name in ql:
            picked = n
            break
    if picked is None:
        routes = match_routes(catalog, query)
        lines = [f"route: {query} (not a pipeline stage name)"]
        if routes:
            lines.append("closest desk route:")
            for r in routes:
                lines.append(f"  {r['pack']} @{r['slug']}")
        lines.append("pipeline: " + " → ".join(names))
        return {"query": query, "pipeline": names, "routes": routes, "lines": lines}
    idx = picked.props["index"]
    prev_s = names[idx - 1] if idx > 0 else None
    next_s = names[idx + 1] if idx + 1 < len(names) else None
    lines = [
        f"route: {picked.name}",
        f"  prev={prev_s or '—'}",
        f"  next={next_s or '—'}",
        "  full: " + " → ".join(names),
        "  pickup Sderot only. HQ does not send.",
    ]
    return {
        "stage": picked.name,
        "prev": prev_s,
        "next": next_s,
        "pipeline": names,
        "lines": lines,
    }


def cmd_dead(graph: Graph) -> dict[str, Any]:
    warehouse = [
        n.name
        for n in graph.nodes.values()
        if n.label == "Specialist" and not n.props.get("onDesk")
    ]
    unseated = [
        n.name
        for n in graph.nodes.values()
        if n.label == "Pack" and not graph.inn.get(n.id)
    ]
    missing_rules = [
        n.name
        for n in graph.nodes.values()
        if n.label == "Specialist"
        and n.props.get("onDesk")
        and n.props.get("ruleFile")
        and not (ROOT / n.props["ruleFile"]).is_file()
    ]
    off_desk_skills = [
        n.name
        for n in graph.nodes.values()
        if n.label == "Skill" and not n.props.get("onDesk")
    ]
    lines = [
        "dead / warehouse (warehouse is intentional, not delete)",
        f"  warehouse specialists={len(warehouse)} (stay off desk unless asked)",
        f"  unseated packs={', '.join(unseated) or '—'}",
        f"  missing desk rule files={', '.join(missing_rules) or 'none'}",
        f"  skills on disk not in desk.skills={', '.join(off_desk_skills) or 'none'}",
    ]
    return {
        "warehouseCount": len(warehouse),
        "unseated": unseated,
        "missingRules": missing_rules,
        "offDeskSkills": off_desk_skills,
        "lines": lines,
    }


def cmd_adr(catalog: dict[str, Any]) -> dict[str, Any]:
    lines = ["standing ADRs (already written — not invented)"]
    for adr in catalog.get("adrs", []):
        lines.append(f"  {adr['id']}: {adr['text']}")
        lines.append(f"    source={adr['source']}")
    return {"adrs": catalog.get("adrs", []), "lines": lines}


def cmd_dump(graph: Graph) -> dict[str, Any]:
    return {
        "nodes": [
            {"id": n.id, "label": n.label, "name": n.name, "props": n.props}
            for n in graph.nodes.values()
        ],
        "edges": [{"src": e.src, "rel": e.rel, "dst": e.dst} for e in graph.edges],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="vfmem",
        description="Query the Velvet Factory office graph. No send. No invented ₪.",
    )
    parser.add_argument("--json", action="store_true", help="machine output")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("architecture")
    sub.add_parser("schema")
    p_who = sub.add_parser("who")
    p_who.add_argument("query", nargs="+")
    p_search = sub.add_parser("search")
    p_search.add_argument("query", nargs="+")
    p_impact = sub.add_parser("impact")
    p_impact.add_argument("target", nargs="?", default="")
    p_impact.add_argument("--git", action="store_true")
    p_route = sub.add_parser("route")
    p_route.add_argument("query", nargs="+")
    sub.add_parser("dead")
    sub.add_parser("adr")
    sub.add_parser("dump")

    args = parser.parse_args(argv)
    for path in (MANIFEST, DESK, AGENCY, CATALOG):
        if not path.is_file():
            print(f"FAIL missing {path}", file=sys.stderr)
            return 1

    graph = build_graph(ROOT)
    catalog = _load_json(CATALOG)
    as_json = args.json

    if args.cmd == "architecture":
        emit(cmd_architecture(graph, catalog), as_json=as_json)
    elif args.cmd == "schema":
        emit(cmd_schema(graph), as_json=as_json)
    elif args.cmd == "who":
        emit(cmd_who(graph, catalog, " ".join(args.query)), as_json=as_json)
    elif args.cmd == "search":
        emit(cmd_search(graph, " ".join(args.query)), as_json=as_json)
    elif args.cmd == "impact":
        if args.git:
            emit(cmd_impact_git(graph, ROOT), as_json=as_json)
        elif not args.target:
            print("usage: vfmem.py impact <pack-or-slug> | --git", file=sys.stderr)
            return 2
        else:
            emit(cmd_impact(graph, args.target), as_json=as_json)
    elif args.cmd == "route":
        emit(cmd_route(graph, catalog, " ".join(args.query)), as_json=as_json)
    elif args.cmd == "dead":
        emit(cmd_dead(graph), as_json=as_json)
    elif args.cmd == "adr":
        emit(cmd_adr(catalog), as_json=as_json)
    elif args.cmd == "dump":
        emit(cmd_dump(graph), as_json=True)
    else:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
