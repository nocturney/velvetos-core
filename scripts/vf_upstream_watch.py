#!/usr/bin/env python3
"""Read-only upstream update observer for VelvetOS tools, skills, agents and pattern repos.

This script never installs, upgrades, checks out, mutates or vendors an upstream.
It compares registry entries with current GitHub state and writes evidence only when
--write is explicitly supplied.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "packages" / "velvetos" / "UPSTREAM-WATCH.json"
DEFAULT_REPORT = ROOT / "packages" / "vfresearch" / "sources" / "upstream-watch-latest.json"


def fail(message: str, code: int = 2) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(code)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing JSON: {path}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON {path}: {exc}")
    if not isinstance(value, dict):
        fail(f"JSON root must be object: {path}")
    return value


def gh_json(route: str) -> dict[str, Any] | None:
    """Optional authenticated metadata/release lookup; never required for HEAD tracking."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        return None
    url = f"https://api.github.com{route}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "VelvetOS-Upstream-Watch/1",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {token}",
    }
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise RuntimeError(f"GitHub HTTP {exc.code} for {route}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"GitHub unavailable for {route}: {exc}") from exc
    return body if isinstance(body, dict) else None


def latest_release_tag(repo: str, previous: str = "") -> tuple[str, str]:
    """Best-effort release lookup without requiring a GitHub token or API quota."""
    if os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"):
        try:
            release = gh_json(f"/repos/{repo}/releases/latest")
        except RuntimeError as exc:
            return previous, f"unavailable_api:{exc}"
        tag = str((release or {}).get("tag_name") or "")
        return tag, "checked_api" if tag else "checked_no_release"

    request = urllib.request.Request(
        f"https://github.com/{repo}/releases/latest",
        method="HEAD",
        headers={"User-Agent": "VelvetOS-Upstream-Watch/1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            final_url = unquote(response.geturl())
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return "", "checked_no_release"
        return previous, f"unavailable_http_{exc.code}"
    except (urllib.error.URLError, TimeoutError) as exc:
        return previous, f"unavailable_web:{type(exc).__name__}"
    marker = "/releases/tag/"
    if marker not in final_url:
        return "", "checked_no_release"
    return final_url.split(marker, 1)[1].split("?", 1)[0].strip("/"), "checked_web"


def remote_head(repo: str) -> tuple[str, str]:
    """Resolve default branch + HEAD without consuming GitHub REST rate limit."""
    url = f"https://github.com/{repo}.git"
    try:
        proc = subprocess.run(
            ["git", "ls-remote", "--symref", url, "HEAD"],
            text=True,
            capture_output=True,
            timeout=25,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"git ls-remote failed for {repo}: {exc}") from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        raise RuntimeError(f"git ls-remote failed for {repo}: {(detail[-1] if detail else 'unknown error')[:300]}")
    branch = "HEAD"
    head = ""
    for line in (proc.stdout or "").splitlines():
        if line.startswith("ref:") and line.endswith("\tHEAD"):
            ref = line.split()[1]
            branch = ref.removeprefix("refs/heads/")
        elif line.endswith("\tHEAD"):
            head = line.split()[0]
    if not head:
        raise RuntimeError(f"git ls-remote returned no HEAD for {repo}")
    return branch, head


def git_head(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        proc = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            text=True,
            capture_output=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = (proc.stdout or "").strip()
    return value if proc.returncode == 0 and value else None


def local_refs(row: dict[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for raw in row.get("integration") or []:
        if not isinstance(raw, str) or "%USERPROFILE%" not in raw.upper():
            continue
        expanded = os.path.expandvars(raw.replace("/", os.sep))
        head = git_head(Path(expanded))
        if head:
            refs.append({"path": raw, "gitHead": head})
    return refs


def inspect_repo(row: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    repo = str(row["repo"])
    branch, head = remote_head(repo)
    prior_head = str((previous or {}).get("remoteHead") or "")
    prior_release = str((previous or {}).get("latestRelease") or "")
    release_tag, release_lookup = latest_release_tag(repo, prior_release)
    if not prior_head:
        state = "baseline"
    elif head != prior_head:
        state = "upstream_changed"
    elif release_tag and prior_release and release_tag != prior_release:
        state = "release_changed"
    elif release_tag and not prior_release:
        state = "release_baseline"
    else:
        state = "no_change"
    return {
        "repo": repo,
        "kind": row.get("kind"),
        "tracking": row.get("tracking"),
        "updatePolicy": row.get("updatePolicy"),
        "autoUpgrade": False,
        "defaultBranch": branch,
        "remoteHead": head,
        "latestRelease": release_tag or None,
        "releaseLookup": release_lookup,
        "localRefs": local_refs(row),
        "state": state,
    }


def check(write: Path | None, *, strict: bool = False) -> int:
    registry = load_json(REGISTRY)
    sources = registry.get("sources") or []
    if not isinstance(sources, list) or not sources:
        fail("upstream registry has no sources")
    previous_path = write or DEFAULT_REPORT
    previous_data = load_json(previous_path) if previous_path.is_file() else {}
    previous = {
        str(row.get("repo")): row
        for row in (previous_data.get("sources") or [])
        if isinstance(row, dict) and row.get("repo")
    }
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    valid_sources: list[dict[str, Any]] = []
    order: dict[str, int] = {}
    for index, source in enumerate(sources):
        if not isinstance(source, dict) or not source.get("repo"):
            errors.append("registry row missing repo")
            continue
        valid_sources.append(source)
        order[str(source["repo"])] = index

    max_workers = max(1, min(10, len(valid_sources)))
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(inspect_repo, source, previous.get(str(source["repo"]))): source
            for source in valid_sources
        }
        for future in as_completed(futures):
            source = futures[future]
            try:
                rows.append(future.result())
            except RuntimeError as exc:
                rows.append({
                    "repo": source.get("repo"),
                    "kind": source.get("kind"),
                    "state": "check_failed",
                    "error": str(exc),
                    "autoUpgrade": False,
                })
                errors.append(str(exc))
    rows.sort(key=lambda row: order.get(str(row.get("repo") or ""), 10**9))
    report = {
        "schema": "velvetos.upstream-watch-report.v1",
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "policy": registry.get("policy"),
        "scheduler": registry.get("scheduler"),
        "summary": {
            "sources": len(rows),
            "changed": sum(r.get("state") in {"upstream_changed", "release_changed"} for r in rows),
            "baseline": sum(r.get("state") in {"baseline", "release_baseline"} for r in rows),
            "failed": sum(r.get("state") in {"check_failed", "unavailable"} for r in rows),
            "autoUpgrade": False,
        },
        "sources": rows,
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    print(text, end="")
    if write:
        target = write if write.is_absolute() else (ROOT / write)
        target = target.resolve()
        try:
            target.relative_to(ROOT.resolve())
        except ValueError:
            fail("--write must stay inside repository root")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    if errors:
        print(f"WARN upstream checks failed for {len(errors)} source(s); see report", file=sys.stderr)
    return 1 if strict and errors else 0


def inventory() -> int:
    registry = load_json(REGISTRY)
    print(json.dumps(registry, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("inventory", help="print the tracked upstream registry; no network")
    check_parser = sub.add_parser("check", help="read GitHub upstream state; never install or upgrade")
    check_parser.add_argument("--write", type=Path, help="write report under the repository")
    check_parser.add_argument("--strict", action="store_true", help="return nonzero if any upstream cannot be checked")
    args = parser.parse_args()
    if args.command == "inventory":
        return inventory()
    return check(args.write, strict=args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
