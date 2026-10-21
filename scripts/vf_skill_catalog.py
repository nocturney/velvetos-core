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
# Source-only curation, deliberately not another Skill registry or an execution surface.
UI_SOURCES = "docs/implementation/office-v2/phase2/ui-ecosystem-sources-2026-10-20.json"
SOURCES = (".cursor/skills", ".agents/skills", ".grok/skills", ".claude/skills", "packages")
STOPWORDS = {"the", "for", "and", "with", "this", "that", "from", "use", "skill", "skills", "into", "all", "not", "are"}
HE_TO_EN = {
    "ממשק": "ui", "ממשקים": "ui", "עיצוב": "design", "נגישות": "accessibility",
    "בדיקות": "test", "ביקורת": "review", "תלת": "3d", "ייצור": "production",
    "מדפסת": "printer", "מדפסות": "printer", "גלילה": "scroll", "אינדקס": "index",
    "מחקר": "research", "דשבורד": "dashboard", "צבעים": "color",
    # UI resource facets; "components" is the catalog's category token for every component source.
    "ממשקי": "ui", "משתמש": "user", "משתמשים": "user", "אנימציה": "animation", "אנימציות": "animation",
    "אייקון": "icon", "אייקונים": "icon", "רכיב": "components", "רכיבים": "components",
}
# Inseparable one/two-letter Hebrew prefixes: ו and, ב in, ל to, ה the, מ from, ש that, כ as.
HE_PREFIXES = "ובלהמשכ"
UI_RIGHTS_STATES = {"REVIEW_REQUIRED", "VERIFIED_UPSTREAM_SCOPE_ONLY"}


def _he_term(word: str) -> str:
    """A prefixed Hebrew form maps only when its bare remainder is a known term; English is untouched."""
    if word in HE_TO_EN:
        return HE_TO_EN[word]
    for size in (1, 2):
        if len(word) > size + 1 and all(c in HE_PREFIXES for c in word[:size]) and word[size:] in HE_TO_EN:
            return HE_TO_EN[word[size:]]
    return word


def _tokens(value: str) -> set[str]:
    base = re.findall(r"[a-z0-9\u0590-\u05ff]+", value.casefold().replace("\u05be", " "))
    return {_he_term(x) for x in base if len(x) >= 2 and x not in STOPWORDS}


def _frontmatter(text: str) -> dict[str, str]:
    # Decode metadata consistently from LF, CRLF and classic CR Skill files.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
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


def _contained(path: Path, scope: Path) -> bool:
    """Fail closed: the fully resolved target (through file or directory symlinks) must stay inside scope.
    Dangling links and anything that cannot be resolved are treated as outside. Reads no content."""
    try:
        return path.resolve(strict=True).is_relative_to(scope)
    except (OSError, RuntimeError, ValueError):
        return False


def _repo_skill_scan(root: Path) -> tuple[list[Path], list[str]]:
    """Return (in-root skill sources, repo-relative paths rejected for resolving outside root)."""
    scope = root.resolve()
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
    accepted = {p for p in rows if _contained(p, scope)}
    rejected = sorted(p.relative_to(root).as_posix() for p in set(rows) - accepted)
    return sorted(accepted, key=lambda p: _canonical_priority(p.relative_to(root).as_posix())), rejected


def _repo_skill_files(root: Path) -> list[Path]:
    return _repo_skill_scan(root)[0]


def discover(root: Path = ROOT, *, parsed_cache: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Metadata only. Optional cache reuses parsed unchanged inputs, never executes tools."""
    identities: dict[tuple[str, str], dict[str, Any]] = {}
    names: dict[str, set[str]] = defaultdict(set)
    for path in _repo_skill_files(root):
        rel = path.relative_to(root).as_posix()
        st = path.stat()
        signature = {"size": st.st_size, "mtime_ns": st.st_mtime_ns}
        cached = parsed_cache.get(rel) if parsed_cache is not None else None
        # Hash comparison closes same-size / restored-mtime stale-cache ambiguity.
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if cached and cached.get("fingerprint") == signature and cached.get("sha256") == digest:
            meta = cached["frontmatter"]
            negative = cached["negative_triggers"]
        else:
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
            "authority_role": "NONE",
            "capability_tags": [],
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
                "authority_role": entry.get("authority_role", "NONE"),
                "capability_tags": entry.get("capability_tags") or [],
                "source_refs": ([ref] if ref else []) + [CANDIDATES],
                "upstream": (entry.get("evidence_refs") or [None])[0],
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


def ui_resources(root: Path = ROOT) -> list[dict[str, Any]]:
    """Read curated, non-executable UI references through the shared catalog interface.
    Fail closed: an invalid or out-of-root source raises ValueError; mixed commands use ui_resources_status."""
    path = root / UI_SOURCES
    if not path.exists() and not path.is_symlink():
        return []
    if not _contained(path, root.resolve()) or not path.is_file():
        raise ValueError("UI source must be a regular file inside the root")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "velvetos.ui-ecosystem-source-intake.v1":
        raise ValueError("unsupported UI source intake schema")
    rows = data.get("sources")
    if not isinstance(rows, list) or len(rows) != data.get("source_count"):
        raise ValueError("UI resource count mismatch")
    ids, urls = set(), set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("UI resource is not an object")
        identifier, url = row.get("id"), row.get("url")
        if not isinstance(identifier, str) or not re.fullmatch(r"[a-z0-9-]+", identifier):
            raise ValueError("invalid UI resource id")
        if not isinstance(url, str) or not url.startswith("https://"):
            raise ValueError("invalid UI resource URL")
        if identifier in ids or url in urls:
            raise ValueError("duplicate UI resource ID/URL")
        if row.get("runtime") != "NOT_INSTALLED_OR_VERIFIED" or row.get("installed") is not False:
            raise ValueError("resource cannot imply runtime admission or installation")
        if row.get("stage") not in {"DISCOVERED", "RESEARCHED"}:
            raise ValueError("resource status must not imply benchmark or production admission")
        rights = row.get("usage_rights")
        if not isinstance(rights, dict) or rights.get("state") not in UI_RIGHTS_STATES:
            raise ValueError("missing explicit UI resource rights status")
        if rights["state"] == "VERIFIED_UPSTREAM_SCOPE_ONLY":
            if not isinstance(rights.get("license"), str) or not rights["license"].strip():
                raise ValueError("verified UI resource rights require a nonempty license")
            if not isinstance(rights.get("evidence_url"), str) or not rights["evidence_url"].startswith("https://"):
                raise ValueError("verified UI resource rights require an https evidence_url")
        # Optional per row; the whole intake is SOURCE_ONLY, so no row may approve source code integration.
        fit = row.get("slicebridge_fit")
        if fit is not None:
            if not isinstance(fit, dict):
                raise ValueError("invalid UI resource slicebridge_fit")
            if fit.get("source_code_integration_approved", False) is not False:
                raise ValueError("SOURCE_ONLY UI resource cannot approve source code integration")
        ids.add(identifier)
        urls.add(url)
    return rows


def ui_resources_status(root: Path = ROOT) -> tuple[list[dict[str, Any]], str | None]:
    """Non-raising view for mixed Skill commands: an invalid UI source yields no rows plus an explicit error."""
    try:
        return ui_resources(root), None
    except (OSError, ValueError) as exc:
        return [], f"{type(exc).__name__}: {exc}"


def _rank_ui(items: list[dict[str, Any]], query: str, *, limit: int, stack: str | None) -> list[dict[str, Any]]:
    q = query.casefold().strip()
    tokens = _tokens(query)
    ranked: list[tuple[int, dict[str, Any]]] = []
    for item in items:
        technologies = [s.casefold() for s in item.get("tech", [])]
        if stack and not any(stack.casefold() in t for t in technologies):
            continue
        identity = item["id"].casefold()
        name = item["name"].casefold()
        name_tokens = _tokens(item["id"] + " " + item["name"])
        capability_tokens = _tokens(" ".join([
            item.get("category", ""), item.get("kind", ""),
            item.get("distinctive", ""), " ".join(item.get("tech", []))
        ]))
        score = 150 if q and q in {identity, name} else (
            25 * len(tokens & name_tokens) + 8 * len(tokens & capability_tokens))
        if score:
            ranked.append((score, item))
    ranked.sort(key=lambda found: (-found[0], found[1]["id"]))
    return [{"score": score, **item} for score, item in ranked[:limit]]


def ui_resource_search(query: str, root: Path = ROOT, *, limit: int = 12,
                       stack: str | None = None) -> list[dict[str, Any]]:
    """Return resource suggestions, not executable Skills or install approvals."""
    return _rank_ui(ui_resources(root), query, limit=limit, stack=stack)


def _ui_source_hash(root: Path) -> str | None:
    path = root / UI_SOURCES
    if not path.exists() and not path.is_symlink():
        return None
    if not _contained(path, root.resolve()) or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_fingerprint(root: Path) -> dict[str, list[Any]]:
    """Content-verified freshness, including same-size or restored-mtime edits."""
    found = {}
    for path in _repo_skill_files(root):
        st = path.stat()
        found[path.relative_to(root).as_posix()] = [st.st_size, st.st_mtime_ns,
                                                   hashlib.sha256(path.read_bytes()).hexdigest()]
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
    ui_source_sha = _ui_source_hash(root)
    ui_refs, ui_error = ui_resources_status(root)
    ui_resource_count = len(ui_refs)
    data = {"schema": "velvetos.derived-skill-index.v1", "root": str(root),
            "sources": fingerprint, "candidate_sha256": candidate_sha,
            "ui_source_sha256": ui_source_sha, "ui_resource_count": ui_resource_count,
            "ui_resources_error": ui_error,
            "parsed_cache": cache, "records": records}
    updated = old.get("sources") != fingerprint or old.get("candidate_sha256") != candidate_sha or old.get("ui_source_sha256") != ui_source_sha or old.get("root") != str(root)
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
            "removed_sources": deleted, "ui_resource_count": ui_resource_count,
            "ui_resources_changed": old.get("ui_source_sha256") != ui_source_sha,
            "ui_resources_error": ui_error,
            "candidate_registry_changed":
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
    unreadable = []
    outside_root = []
    for provider in (".cursor", ".agents", ".grok", ".claude", ".codex"):
        base = home / provider / "skills"
        # Claude synced and Codex .system skills are nested; one-level glob misses them.
        try:
            paths = sorted(base.rglob("SKILL.md")) if base.is_dir() else []
            scope = base.resolve() if base.is_dir() else None
            for path in paths:
                # Each adapter's own skills directory is its root; a link escaping it is not inventoried.
                if scope is None or not _contained(path, scope):
                    outside_root.append({"adapter": provider, "path": str(path), "reason": "OUTSIDE_SKILL_ROOT"})
                    continue
                try:
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                except OSError as exc:
                    unreadable.append({"adapter": provider, "path": str(path), "reason": type(exc).__name__})
                    continue
                found.append({"adapter": provider, "skill": path.parent.name,
                              "path": str(path), "sha256": digest})
        except OSError as exc:
            unreadable.append({"adapter": provider, "path": str(base), "reason": type(exc).__name__})
    return {"hostname": socket.gethostname(), "platform": platform.system(),
            "local_skills": found, "source_present_count": len(found),
            "unreadable": unreadable,
            "outside_root": outside_root,
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
        if "web-ui" in record.get("capability_tags", []):
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
    ui_refs, ui_error = ui_resources_status(root)
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
        "supporting_resources": [
            {"id": r["id"], "name": r["name"], "category": r["category"],
             "match_score": r["score"], "rights": r["usage_rights"]["state"],
             "source": r["url"], "execution": "NOT_APPLICABLE_SOURCE_ONLY"}
            for r in _rank_ui(ui_refs, query, limit=8, stack=None)
        ],
        "ui_resources_error": ui_error,
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
                    "authority_role": x.get("authority_role", "NONE"),
                    "requires_admission": x["origin"] == "EXTERNAL_CANDIDATE" and
                    x["status"] not in {"ADMITTED", "ACTIVE", "PRODUCTION"}} for x in matches],
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
    ui_refs, ui_error = ui_resources_status(root)
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
        "ui_resource_suggestions": [
            {"id": r["id"], "kind": r["kind"], "rights": r["usage_rights"]["state"],
             "source": r["url"], "installed": False}
            for r in _rank_ui(ui_refs, query, limit=6, stack=None)
        ],
        "ui_resources_error": ui_error,
        "host": {"local": socket.gethostname(),
                 "repo_source_present": bool(ranked and ranked[0]["canonical_file"]),
                 "machine_specific_access": "UNVERIFIED", "agent_execution": "UNVERIFIED"},
        "composition": "Evaluate complementary/competitive steps; no forced chain or automatic winner",
        "next": "Authorize execution via existing Office task envelope / Core lease; run relevant checks; independent QA on exact head",
        "execution": "NOT_STARTED", "receipt": None,
    }


def audit(root: Path = ROOT) -> dict[str, Any]:
    items = catalog(root)
    counts = defaultdict(int)
    for item in items:
        counts[item["origin"]] += 1
    accepted, rejected = _repo_skill_scan(root)
    ui_refs, ui_error = ui_resources_status(root)
    ui_counts = defaultdict(int)
    for ref in ui_refs:
        ui_counts[ref["category"]] += 1
    return {"source_files": len(accepted), "unique_records": len(items),
            "ui_resources": len(ui_refs), "ui_resource_categories": dict(ui_counts),
            "ui_resources_error": ui_error,
            "ui_rights_review_required": sum(r["usage_rights"]["state"] == "REVIEW_REQUIRED" for r in ui_refs),
            "rejected_outside_root": rejected,
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
    sub.add_parser("sources")
    src = sub.add_parser("source-search")
    src.add_argument("query", nargs="+")
    src.add_argument("--stack", default=None, help="Filter source stack, e.g. Angular, React, JavaScript")
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
    elif args.command in {"sources", "source-search"}:
        # UI-specific commands stay fail-closed: an invalid or out-of-root source is an error, not empty results.
        try:
            value = (ui_resources(root) if args.command == "sources"
                     else ui_resource_search(" ".join(args.query), root, stack=args.stack))
        except (OSError, ValueError) as exc:
            value = {"error": "ui_resources_invalid", "detail": str(exc), "executable": False}
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
