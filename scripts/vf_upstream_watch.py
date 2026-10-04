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
import re
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


LOCAL_REF_VARS = ("USERPROFILE", "VELVET_ROOT", "VELVETOS_REPO_ROOT", "VELVETOS_RUNTIME_ROOT", "VELVETOS_STATE_ROOT")
LOCAL_REF_TOKEN = re.compile(r"%([A-Za-z_][A-Za-z0-9_]*)%")


def expand_local_ref(raw: str) -> str | None:
    """Expand %USERPROFILE% / %VELVET_ROOT% / %VELVETOS_*% host paths; None when not a local ref or unset."""
    names = [m.group(1).upper() for m in LOCAL_REF_TOKEN.finditer(raw)]
    if not names or any(name not in LOCAL_REF_VARS for name in names):
        return None
    values = {name: os.environ.get(name) for name in names}
    if any(not value for value in values.values()):
        return None
    expanded = LOCAL_REF_TOKEN.sub(lambda m: str(values[m.group(1).upper()]), raw)
    return expanded.replace("/", os.sep)


def local_refs(row: dict[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for raw in row.get("integration") or []:
        if not isinstance(raw, str):
            continue
        expanded = expand_local_ref(raw)
        if expanded is None:
            continue
        head = git_head(Path(expanded))
        if head:
            refs.append({"path": raw, "gitHead": head})
    return refs


LEGACY_CHANGED_STATES = {"upstream_changed", "release_changed"}


def derive_change_state(
    previous: dict[str, Any] | None,
    *,
    head: str,
    release_tag: str,
    checked_at: str,
) -> dict[str, Any]:
    """Keep detected upstream changes sticky until an explicit adoption acknowledgement."""
    prev = previous or {}
    if not previous:
        return {
            "baselineHead": head,
            "baselineRelease": release_tag or None,
            "pendingUpdate": False,
            "changeKinds": [],
            "firstDetectedAt": None,
            "newDetection": False,
            "state": "baseline",
        }

    legacy_pending = (
        str(prev.get("state") or "") in LEGACY_CHANGED_STATES
        and "pendingUpdate" not in prev
    )
    if legacy_pending:
        return {
            "baselineHead": prev.get("baselineHead"),
            "baselineRelease": prev.get("baselineRelease"),
            "pendingUpdate": True,
            "changeKinds": list(prev.get("changeKinds") or ["legacy_detected_change"]),
            "firstDetectedAt": prev.get("firstDetectedAt") or checked_at,
            "newDetection": False,
            "state": "pending_update",
        }

    baseline_head = str(prev.get("baselineHead") or prev.get("remoteHead") or head)
    if "baselineRelease" in prev:
        baseline_release = prev.get("baselineRelease")
        release_baseline_known = True
    else:
        baseline_release = prev.get("latestRelease") or release_tag or None
        release_baseline_known = False

    kinds: list[str] = []
    if baseline_head and head != baseline_head:
        kinds.append("head")
    if release_baseline_known:
        if baseline_release and release_tag and release_tag != baseline_release:
            kinds.append("release")
        elif baseline_release is None and release_tag:
            kinds.append("release")

    pending = bool(kinds)
    was_pending = bool(prev.get("pendingUpdate"))
    return {
        "baselineHead": baseline_head,
        "baselineRelease": baseline_release,
        "pendingUpdate": pending,
        "changeKinds": kinds,
        "firstDetectedAt": (
            (prev.get("firstDetectedAt") or checked_at) if pending and was_pending
            else checked_at if pending
            else None
        ),
        "newDetection": bool(pending and not was_pending),
        "state": "pending_update" if pending else "no_change",
    }


def inspect_repo(row: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    repo = str(row["repo"])
    branch, head = remote_head(repo)
    prior_release = str((previous or {}).get("latestRelease") or "")
    release_tag, release_lookup = latest_release_tag(repo, prior_release)
    checked_at = datetime.now(timezone.utc).isoformat()

    state_previous = dict(previous or {})
    adopted_head = str(row.get("adoptedHead") or "").strip()
    adopted_release = str(row.get("adoptedRelease") or "").strip()
    if state_previous:
        if adopted_head and not state_previous.get("baselineHead"):
            state_previous["baselineHead"] = adopted_head
        if adopted_release and not state_previous.get("baselineRelease"):
            state_previous["baselineRelease"] = adopted_release
    elif adopted_head or adopted_release:
        state_previous = {
            "remoteHead": adopted_head or head,
            "latestRelease": adopted_release or None,
            "baselineHead": adopted_head or head,
            "baselineRelease": adopted_release or None,
            "pendingUpdate": False,
            "state": "no_change",
        }

    change = derive_change_state(
        state_previous or None,
        head=head,
        release_tag=release_tag,
        checked_at=checked_at,
    )
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
        "lastCheckedAt": checked_at,
        **change,
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
    report_checked_at = datetime.now(timezone.utc).isoformat()
    report = {
        "schema": "velvetos.upstream-watch-report.v1",
        "checkedAt": report_checked_at,
        "artifactMeta": {
            "asOf": report_checked_at,
            "provenance": [
                "packages/velvetos/UPSTREAM-WATCH.json",
                "live GitHub default-branch HEAD and latest-release lookups",
            ],
            "uncertainty": "check_failed/unavailable rows and best-effort release lookup remain explicit; no auto-upgrade inference",
            "refreshTarget": "next Velvet Research Seat 02:00 upstream check or explicit upstream review task",
        },
        "policy": registry.get("policy"),
        "scheduler": registry.get("scheduler"),
        "summary": {
            "sources": len(rows),
            "changed": sum(bool(r.get("pendingUpdate")) for r in rows),
            "pendingUpdates": sum(bool(r.get("pendingUpdate")) for r in rows),
            "newDetections": sum(bool(r.get("newDetection")) for r in rows),
            "baseline": sum(r.get("state") == "baseline" for r in rows),
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
        target.write_bytes(text.encode("utf-8"))
    if errors:
        print(f"WARN upstream checks failed for {len(errors)} source(s); see report", file=sys.stderr)
    return 1 if strict and errors else 0


def _report_target(path: Path | None) -> Path:
    target = (path or DEFAULT_REPORT)
    target = target if target.is_absolute() else (ROOT / target)
    target = target.resolve()
    try:
        target.relative_to(ROOT.resolve())
    except ValueError:
        fail("report path must stay inside repository root")
    return target


def _apply_adoption_baseline(
    row: dict[str, Any],
    *,
    adopted_head: str | None,
    adopted_release: str | None,
    checked_at: str,
) -> None:
    """Record exactly what was adopted and preserve newer unreleased/release drift."""
    baseline_head = (adopted_head or str(row.get("remoteHead") or "")).strip()
    baseline_release = (
        adopted_release.strip() if adopted_release is not None
        else row.get("latestRelease")
    )
    row["baselineHead"] = baseline_head
    row["baselineRelease"] = baseline_release or None
    kinds: list[str] = []
    remote_head = str(row.get("remoteHead") or "").strip()
    latest_release = row.get("latestRelease")
    if remote_head and baseline_head and remote_head != baseline_head:
        kinds.append("head")
    if latest_release != (baseline_release or None):
        kinds.append("release")
    row["pendingUpdate"] = bool(kinds)
    row["changeKinds"] = kinds
    row["firstDetectedAt"] = (
        (row.get("firstDetectedAt") or checked_at) if kinds else None
    )
    row["newDetection"] = False
    row["state"] = "pending_update" if kinds else "no_change"


def acknowledge(
    repo: str,
    evidence: str,
    report_path: Path | None = None,
    *,
    adopted_head: str | None = None,
    adopted_release: str | None = None,
) -> int:
    """Advance only the reviewed adoption baseline; keep newer drift pending."""
    target = _report_target(report_path)
    data = load_json(target)
    rows = data.get("sources") or []
    wanted = repo.casefold()
    row = next((item for item in rows if str(item.get("repo") or "").casefold() == wanted), None)
    if not isinstance(row, dict):
        fail(f"repo not found in report: {repo}")
    if not row.get("pendingUpdate"):
        fail(f"repo has no pending update to acknowledge: {repo}")
    if not evidence.strip():
        fail("--evidence is required for adoption acknowledgement")
    if adopted_head is not None:
        value = adopted_head.strip().lower()
        if len(value) != 40 or any(ch not in "0123456789abcdef" for ch in value):
            fail("--adopted-head must be an exact 40-character Git SHA")
        adopted_head = value
    if adopted_release is not None and not adopted_release.strip():
        fail("--adopted-release cannot be empty")
    checked_at = datetime.now(timezone.utc).isoformat()
    _apply_adoption_baseline(
        row,
        adopted_head=adopted_head,
        adopted_release=adopted_release,
        checked_at=checked_at,
    )
    row["acknowledgedAt"] = checked_at
    row["adoptionEvidence"] = evidence.strip()
    summary = data.setdefault("summary", {})
    summary["changed"] = sum(bool(item.get("pendingUpdate")) for item in rows if isinstance(item, dict))
    summary["pendingUpdates"] = summary["changed"]
    summary["newDetections"] = sum(bool(item.get("newDetection")) for item in rows if isinstance(item, dict))
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    suffix = f" remaining={','.join(row['changeKinds'])}" if row["pendingUpdate"] else " remaining=none"
    print(f"ACK upstream baseline repo={row.get('repo')} evidence={evidence.strip()}{suffix}")
    return 0


def selftest() -> int:
    stamp = "2026-09-27T00:00:00+00:00"
    baseline = derive_change_state(None, head="a", release_tag="v1.0.0", checked_at=stamp)
    assert baseline["state"] == "baseline" and baseline["pendingUpdate"] is False
    previous = {
        "remoteHead": "a",
        "latestRelease": "v1.0.0",
        "baselineHead": "a",
        "baselineRelease": "v1.0.0",
        "pendingUpdate": False,
        "state": "no_change",
    }
    changed = derive_change_state(previous, head="b", release_tag="v1.1.0", checked_at=stamp)
    assert changed["pendingUpdate"] is True
    assert set(changed["changeKinds"]) == {"head", "release"}
    assert changed["newDetection"] is True
    repeated_previous = {
        **previous,
        **changed,
        "remoteHead": "b",
        "latestRelease": "v1.1.0",
    }
    repeated = derive_change_state(repeated_previous, head="b", release_tag="v1.1.0", checked_at=stamp)
    assert repeated["pendingUpdate"] is True
    assert repeated["newDetection"] is False
    legacy = derive_change_state(
        {"remoteHead": "legacy-new", "latestRelease": "v2.0.0", "state": "upstream_changed"},
        head="legacy-new",
        release_tag="v2.0.0",
        checked_at=stamp,
    )
    assert legacy["pendingUpdate"] is True and legacy["state"] == "pending_update"
    first_release = derive_change_state(
        {
            "remoteHead": "same",
            "latestRelease": None,
            "baselineHead": "same",
            "baselineRelease": None,
            "pendingUpdate": False,
            "state": "no_change",
        },
        head="same",
        release_tag="v1.0.0",
        checked_at=stamp,
    )
    assert first_release["pendingUpdate"] is True and "release" in first_release["changeKinds"]
    partial = {
        "remoteHead": "b" * 40,
        "latestRelease": "v2.0.0",
        "pendingUpdate": True,
        "changeKinds": ["head", "release"],
        "firstDetectedAt": stamp,
    }
    _apply_adoption_baseline(
        partial,
        adopted_head="a" * 40,
        adopted_release="v2.0.0",
        checked_at=stamp,
    )
    assert partial["pendingUpdate"] is True
    assert partial["changeKinds"] == ["head"]
    assert partial["baselineRelease"] == "v2.0.0"
    _apply_adoption_baseline(
        partial,
        adopted_head="b" * 40,
        adopted_release="v2.0.0",
        checked_at=stamp,
    )
    assert partial["pendingUpdate"] is False and partial["changeKinds"] == []
    print("OK upstream watch selftest sticky-pending + partial-adoption + first-release + legacy-migration")
    return 0


def inventory() -> int:
    registry = load_json(REGISTRY)
    print(json.dumps(registry, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("inventory", help="print the tracked upstream registry; no network")
    sub.add_parser("selftest", help="offline sticky-update behavior proof")
    check_parser = sub.add_parser("check", help="read GitHub upstream state; never install or upgrade")
    check_parser.add_argument("--write", type=Path, help="write report under the repository")
    check_parser.add_argument("--strict", action="store_true", help="return nonzero if any upstream cannot be checked")
    ack_parser = sub.add_parser("ack", help="advance baseline only after reviewed adoption")
    ack_parser.add_argument("--repo", required=True)
    ack_parser.add_argument("--evidence", required=True)
    ack_parser.add_argument("--report", type=Path, default=None)
    ack_parser.add_argument("--adopted-head", default=None)
    ack_parser.add_argument("--adopted-release", default=None)
    args = parser.parse_args()
    if args.command == "inventory":
        return inventory()
    if args.command == "selftest":
        return selftest()
    if args.command == "ack":
        return acknowledge(
            args.repo,
            args.evidence,
            args.report,
            adopted_head=args.adopted_head,
            adopted_release=args.adopted_release,
        )
    return check(args.write, strict=args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
