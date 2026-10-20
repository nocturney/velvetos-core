#!/usr/bin/env python3
"""Derived Skill discovery and routing over VelvetOS' existing canonical sources.

No second authority, installation, model call, process launch, or automatic execution.
Only source files plus Office v2's already-canonical Candidate Registry are read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import socket
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = "docs/implementation/office-v2/phase2/candidate-registry-v0.json"
SOURCES = (".cursor/skills", ".agents/skills", ".grok/skills", ".claude/skills", "packages")
STOPWORDS = {"the", "for", "and", "with", "this", "that", "from", "use", "skill", "skills", "into", "all", "not", "are"}
HE_TO_EN = {
    "ממשק": "ui", "ממשקים": "ui", "עיצוב": "design", "נגישות": "accessibility",
    "בדיקות": "test", "ביקורת": "review", "תלת": "3d", "ייצור": "production",
    "מדפסת": "printer", "מדפסות": "printer", "גלילה": "scroll", "אינדקס": "index",
    "מחקר": "research", "דשבורד": "dashboard", "צבעים": "color",
}


def _tokens(value: str) -> set[str]:
    base = re.findall(r"[a-z0-9\u0590-\u05ff]+", value.casefold())
    return {HE_TO_EN.get(x, x) for x in base if len(x) >= 2 and x not in STOPWORDS}


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    match = re.match(r"\A---\s*\n(.*?)\n---(?:\s*\n|\Z)", text, re.S)
    if not match:
        return {}
    rows: dict[str, str] = {}
    for line in match.group(1).splitlines():
        m = re.match(r"^([a-zA-Z_-]+):\s*(.*)$", line)
        if m:
            rows[m.group(1)] = m.group(2).strip().strip("'\"")
    return rows


def _negative(text: str) -> list[str]:
    found = re.findall(r"(?im)^\s*(?:[-*]\s*)?(Never use\b[^\n]*|Do not use\b[^\n]*)", text)
    return [v.strip()[:200] for v in found[:12]]


def _canonical_priority(path: str) -> tuple[int, str]:
    priority = next((i for i, prefix in enumerate(SOURCES) if path.startswith(prefix + "/")), len(SOURCES))
    return priority, path


def _repo_skill_files(root: Path) -> list[Path]:
    rows: list[Path] = []
    for prefix in SOURCES:
        base = root / prefix
        if not base.is_dir():
            continue
        # Vendor caches are not traversed: only the repository's declared source roots.
        # Package skills may be nested arbitrarily under packages/**.
        if prefix == "packages":
            rows += sorted(p for p in base.rglob("SKILL.md") if p.is_file()
                           and not any(s in {".git", "node_modules", ".venv", "__pycache__"} for s in p.parts))
        else:
            rows += sorted(p for p in base.glob("*/SKILL.md") if p.is_file())
            rows += sorted(p for p in base.glob("*/*/SKILL.md") if p.is_file())
    return sorted(set(rows), key=lambda p: _canonical_priority(p.relative_to(root).as_posix()))


def discover(root: Path = ROOT, *, parsed_cache: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Metadata only. Optional cache reuses parsed unchanged inputs, never executes tools."""
    identities: dict[tuple[str, str], dict[str, Any]] = {}
    names: dict[str, set[str]] = defaultdict(set)
    for path in _repo_skill_files(root):
        rel = path.relative_to(root).as_posix()
        st = path.stat()
        signature = {"size": st.st_size, "mtime_ns": st.st_mtime_ns}
        cached = parsed_cache.get(rel) if parsed_cache is not None else None
        if cached and cached.get("fingerprint") == signature:
            digest = cached["sha256"]
            meta = cached["frontmatter"]
            negative = cached["negative_triggers"]
        else:
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            body = raw.decode("utf-8", errors="replace")
            meta = _frontmatter(body)
            negative = _negative(body)
            if parsed_cache is not None:
                parsed_cache[rel] = {"fingerprint": signature, "sha256": digest,
                                     "frontmatter": meta, "negative_triggers": negative}
        slug = meta.get("name") or path.parent.name
        slug = re.sub(r"[^a-z0-9-]+", "-", slug.casefold()).strip("-") or path.parent.name
        names[slug].add(digest)
        identity = (slug, digest)
        if identity in identities:
            identities[identity]["alternate_paths"].append(rel)
            continue
        desc = meta.get("description") or ""
        identities[identity] = {
            "id": slug,
            "name": meta.get("name") or slug,
            "description": desc,
            "use_cases": desc,
            "origin": "REPO",
            "canonical_file": rel,
            "alternate_paths": [],
            "source_refs": [rel],
            "upstream": None,
            "license": None,
            "version": None,
            "commit": None,
            "sha256": digest,
            "positive_triggers": desc,
            "negative_triggers": negative,
            "inputs": None,
            "outputs": None,
            "required_tools": [],
            "required_permissions": [],
            "compatible_agents": ["prompt-portable; runtime adapter not verified"],
            "available_hosts": [],
            "runtime_dependencies": [],
            "related_skills": [],
            "status": "SOURCE_PRESENT",
            "availability": {
                "cataloged": True,
                "source_in_repository": True,
                "installed_on_host": "UNKNOWN",
                "execution_ready": False,
                "executed_and_verified": False,
            },
            "quality_evidence": [],
            "last_verified": None,
            "discovery_evidence": {"path": rel, "sha256": digest},
        }
    out: list[dict[str, Any]] = []
    for (slug, digest), row in identities.items():
        if len(names[slug]) > 1:
            row["id"] = slug + "~" + digest[:10]
            row["variant_of"] = slug
        out.append(row)

    candidate_file = root / CANDIDATES
    if candidate_file.is_file():
        registry = json.loads(candidate_file.read_text(encoding="utf-8"))
        for entry in registry.get("items", []):
            if entry.get("category") != "EXTERNAL_SKILL":
                continue
            name = entry["name"]
            ref = next((ref for ref in entry.get("evidence_refs", []) if "/blob/" in ref and "/SKILL.md" in ref), None)
            if not ref:
                ref = (entry.get("evidence_refs") or [None])[0]
            parts = name.rsplit(":", 1)
            slug = parts[-1]
            desc = next((note.split("DESCRIPTION: ", 1)[1] for note in entry.get("notes", [])
                         if note.startswith("DESCRIPTION: ")), "")
            out.append({
                "id": entry["candidate_id"], "name": slug, "description": desc, "use_cases": desc,
                "origin": "EXTERNAL_CANDIDATE", "canonical_file": None, "alternate_paths": [],
                "source_refs": [ref, CANDIDATES], "upstream": entry.get("evidence_refs", [None])[0],
                "license": next((x.split(": ", 1)[1] for x in entry.get("notes", []) if x.startswith("LICENSE: ")), None),
                "version": next((x.split(": ", 1)[1] for x in entry.get("notes", []) if x.startswith("VERSION: ")), None),
                "commit": next((x.split(": ", 1)[1] for x in entry.get("notes", []) if x.startswith("COMMIT: ")), None),
                "sha256": None, "positive_triggers": desc, "negative_triggers": [],
                "inputs": None, "outputs": None, "required_tools": [], "required_permissions": [],
                "compatible_agents": ["provider-neutral instructions; adapter unverified"],
                "available_hosts": [], "runtime_dependencies": [], "related_skills": [],
                "status": entry.get("lifecycle_state", "DISCOVERED"),
                "availability": {
                    "cataloged": True, "source_in_repository": False,
                    "installed_on_host": "UNKNOWN", "execution_ready": False, "executed_and_verified": False,
                },
                "quality_evidence": [], "last_verified": None,
                "discovery_evidence": {"candidate_id": entry["candidate_id"], "registry": CANDIDATES},
            })
    return sorted(out, key=lambda x: x["id"])


def _source_fingerprint(root: Path) -> dict[str, list[int]]:
    """Stat-only hot-path validation; update_index re-hashes every changed file."""
    found = {}
    for path in _repo_skill_files(root):
        st = path.stat()
        found[path.relative_to(root).as_posix()] = [st.st_size, st.st_mtime_ns]
    return found


def _candidate_hash(root: Path) -> str | None:
    path = root / CANDIDATES
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _index_path() -> Path:
    return Path.home() / ".cache" / "velvetos" / "skill-catalog.json"


def _read_index(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if data.get("schema") == "velvetos.derived-skill-index.v1" else {}
    except (OSError, ValueError, AttributeError):
        return {}


def update_index(root: Path = ROOT, path: Path | None = None) -> dict[str, Any]:
    """Explicit, atomic, incremental metadata cache; no new source of truth."""
    root = root.resolve()
    path = path or _index_path()
    old = _read_index(path)
    previous = old.get("parsed_cache", {}) if old.get("root") == str(root) else {}
    cache = dict(previous)
    records = discover(root, parsed_cache=cache)
    fingerprint = _source_fingerprint(root)
    cache = {k: v for k, v in cache.items() if k in fingerprint}
    revised = [k for k in fingerprint if k not in previous or
               previous[k].get("sha256") != cache[k].get("sha256")]
    deleted = sorted(set(previous) - set(fingerprint))
    candidate_sha = _candidate_hash(root)
    data = {"schema": "velvetos.derived-skill-index.v1", "root": str(root),
            "sources": fingerprint, "candidate_sha256": candidate_sha,
            "parsed_cache": cache, "records": records}
    updated = old.get("sources") != fingerprint or old.get("candidate_sha256") != candidate_sha or old.get("root") != str(root)
    if updated or not path.is_file():
        import tempfile
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent),
                                             prefix=".skills-", delete=False) as stream:
                tmp = Path(stream.name)
                json.dump(data, stream, ensure_ascii=False)
                stream.write("\n")
            os.replace(str(tmp), str(path))
        finally:
            if tmp is not None and tmp.exists():
                tmp.unlink()
    return {"index": str(path), "derived_only": True, "source_files": len(fingerprint),
            "records": len(records), "updated": updated, "changed_hashes": revised,
            "removed_sources": deleted, "candidate_registry_changed":
            old.get("candidate_sha256") != candidate_sha}


def catalog(root: Path = ROOT) -> list[dict[str, Any]]:
    """Use verified local derived index when fresh; never silently return stale rows."""
    root = root.resolve()
    data = _read_index(_index_path())
    if data.get("root") == str(root) and data.get("sources") == _source_fingerprint(root) and (
            data.get("candidate_sha256") == _candidate_hash(root)):
        return data["records"]
    return discover(root)


def host_probe() -> dict[str, Any]:
    """Read-only local evidence, no inference about other computers or tool authority."""
    home = Path.home()
    found = []
    for provider in (".cursor", ".agents", ".grok", ".claude", ".codex"):
        base = home / provider / "skills"
        for path in sorted(base.glob("*/SKILL.md")) if base.is_dir() else []:
            found.append({"adapter": provider, "skill": path.parent.name,
                          "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return {"hostname": socket.gethostname(), "platform": platform.system(),
            "local_skills": found, "source_present_count": len(found),
            "agent_binary_presence": {"claude": bool(shutil.which("claude")),
                                      "cursor": bool(shutil.which("cursor")),
                                      "codex": bool(shutil.which("codex"))},
            "execution_readiness": "NOT_ASSESSED", "execution_verified": False,
            "meaning": "SKILL.md presence is not proof of CLI availability, permissions or successful run"}


def get_skill(name: str, root: Path = ROOT) -> dict[str, Any] | None:
    query = name.casefold().strip()
    hits = [x for x in catalog(root) if query in (x["id"].casefold(), x["name"].casefold())]
    if len(hits) == 1:
        return hits[0]
    # Deliberately do not collapse different implementations onto one name.
    return {"error": "ambiguous_skill", "matches": [x["id"] for x in hits]} if hits else None


def _rank(record: dict[str, Any], query: str) -> int:
    q = query.strip().casefold()
    if not q:
        return 0
    if q in (record["id"].casefold(), record["name"].casefold()):
        return 150
    tokens = _tokens(query)
    if not tokens:
        return 0
    # Domain exclusions prevent incidental words like "design" from routing
    # a CAD specialist into UI work (or a UI-only external skill into CAD).
    request_ui = bool(tokens & {"ui", "web", "dashboard", "accessibility", "screen"})
    request_cad = bool(tokens & {"cad", "openscad", "blender", "3d", "mesh", "stl"})
    candidate_name = _tokens(record["id"] + " " + record["name"])
    if request_ui and not request_cad and candidate_name & {"cad", "openscad", "blender"}:
        return 0
    if request_cad and not request_ui and record["origin"] == "EXTERNAL_CANDIDATE":
        if record.get("upstream") == "https://github.com/plugin87/ux-ui-agent-skills":
            return 0
    for negative in record.get("negative_triggers", []):
        # Explicit exclusions win over incidental matches in negative text.
        neg = _tokens(negative)
        if len(tokens & neg) >= 2 or (len(tokens) == 1 and tokens <= neg):
            return 0
    name = _tokens(record["id"] + " " + record["name"])
    positive = _tokens(record.get("positive_triggers") or "")
    common = tokens & (name | positive)
    return (30 * len(common & name) + 8 * len(common & positive)) if common else 0


def search(query: str, root: Path = ROOT, limit: int = 12) -> list[dict[str, Any]]:
    scored = [(_rank(item, query), item) for item in catalog(root)]
    scored = [(score, item) for score, item in scored if score > 0]
    scored.sort(key=lambda r: (-r[0], r[1]["id"]))
    return [{"score": score, **record} for score, record in scored[:limit]]


def compare(query: str, root: Path = ROOT) -> dict[str, Any]:
    found = search(query, root)
    return {
        "query": query,
        "candidates": [
            {"id": r["id"], "match_score": r["score"], "status": r["status"],
             "origin": r["origin"], "evidence": r["source_refs"],
             "quality": "NOT_BENCHMARKED", "run_ready": r["availability"]["execution_ready"]}
            for r in found
        ],
        "decision": "BENCHMARK_REQUIRED; no automatic winner; complementary candidates retained",
        "benchmark_gate": "Use shared Golden Fixtures and independent QA before replace/combine verdicts",
    }


def route(query: str, root: Path = ROOT) -> dict[str, Any]:
    exact = get_skill(query, root)
    if exact and "error" not in exact:
        matches = [{"score": 150, **exact}]
    else:
        matches = search(query, root, limit=6)
    return {
        "query": query,
        "skills": [{"id": x["id"], "score": x["score"], "source": x["canonical_file"],
                    "candidate": x["origin"] == "EXTERNAL_CANDIDATE",
                    "run_ready": x["availability"]["execution_ready"],
                    "requires_admission": x["origin"] == "EXTERNAL_CANDIDATE"} for x in matches],
        "execution": "NOT_STARTED",
        "dispatch": "Manual/authorized agent selection only; require host facts and matching permissions",
        "progressive_loading": "Read selected canonical_file when needed, then only its relevant references",
        "qa": "Not executed; no PASS without deterministic check and independent review",
    }


def plan(query: str, root: Path = ROOT) -> dict[str, Any]:
    """Suggest grounded specialists and existing validators; this is NOT a worker launcher."""
    ranked = search(query, root, 12)
    agency_file = root / ".cursor" / "agency-agents.json"
    agents = json.loads(agency_file.read_text(encoding="utf-8")).get("agents", []) if agency_file.is_file() else []
    tok = _tokens(query)
    specialist_hits: list[tuple[int, dict[str, Any]]] = []
    for agent in agents:
        rule = agent.get("ruleFile")
        if not rule or not (root / rule).is_file():
            continue
        title = _tokens(agent.get("slug", "") + " " + agent.get("name", ""))
        desc = _tokens(agent.get("description", ""))
        score = 4 * len(tok & title) + len(tok & desc)
        if score:
            specialist_hits.append((score, agent))
    specialist_hits.sort(key=lambda p: (-p[0], p[1]["slug"]))
    matched_agents = [{"slug": a["slug"], "rule_file": a["ruleFile"], "match_score": score,
                       "runtime_ready": "UNVERIFIED"} for score, a in specialist_hits[:6]]
    checks = []
    if any("ui" in _tokens(x["description"] + " " + x["name"]) for x in ranked):
        checks = [x for x in ("scripts/check-engineering-quality.py",
                              "scripts/check-living-studio.py") if (root / x).is_file()]
    if any("cad" in _tokens(x["name"]) for x in ranked):
        checks.extend(x for x in ("scripts/check-vfmem.py", "scripts/check-office-v2-phase2.py")
                      if (root / x).is_file() and x not in checks)
    return {
        "task": query,
        "candidate_skills": [{"id": x["id"], "role_fit_score": x["score"],
                              "origin": x["origin"], "canonical_file": x["canonical_file"],
                              "run_ready": False, "evidence": x["source_refs"]} for x in ranked],
        "agent_candidates": matched_agents,
        "existing_deterministic_checks": checks,
        "host": {"local": socket.gethostname(),
                 "skill_source_present": bool(ranked and ranked[0]["canonical_file"]),
                 "agent_execution": "UNVERIFIED"},
        "composition": "Evaluate complementary/competitive steps; no forced chain or automatic winner",
        "next": "Authorize execution via existing Office task envelope / Core lease; run relevant checks; independent QA on exact head",
        "execution": "NOT_STARTED", "receipt": None,
    }


def audit(root: Path = ROOT) -> dict[str, Any]:
    items = catalog(root)
    counts = defaultdict(int)
    for item in items:
        counts[item["origin"]] += 1
    return {"source_files": len(_repo_skill_files(root)), "unique_records": len(items),
            "by_origin": dict(counts), "duplicate_paths": sum(len(x["alternate_paths"]) for x in items),
            "colliding_variants": [x["id"] for x in items if "variant_of" in x],
            "uninstalled_candidates": [x["id"] for x in items if x["origin"] == "EXTERNAL_CANDIDATE"],
            "host_availability": "UNVERIFIED; local inventory is not execution evidence"}


def main() -> int:
    p = argparse.ArgumentParser(description="Provider-neutral, derived VelvetOS Skill catalog")
    p.add_argument("--root", type=Path, default=ROOT)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    sub.add_parser("audit")
    sub.add_parser("index")
    sub.add_parser("host")
    for cmd in ("search", "route", "compare", "plan", "show"):
        sp = sub.add_parser(cmd)
        sp.add_argument("query", nargs="+")
    args = p.parse_args()
    root = args.root.resolve()
    if args.command == "list":
        value = [{"id": x["id"], "origin": x["origin"], "status": x["status"], "path": x["canonical_file"]}
                 for x in discover(root)]
    elif args.command == "audit":
        value = audit(root)
    elif args.command == "index":
        value = update_index(root)
    elif args.command == "host":
        value = host_probe()
    else:
        query = " ".join(args.query)
        if args.command == "search":
            value = search(query, root)
        elif args.command == "route":
            value = route(query, root)
        elif args.command == "compare":
            value = compare(query, root)
        elif args.command == "plan":
            value = plan(query, root)
        else:
            value = get_skill(query, root) or {"error": "unknown_skill", "name": query}
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return 0 if not isinstance(value, dict) or "error" not in value else 2


if __name__ == "__main__":
    raise SystemExit(main())
