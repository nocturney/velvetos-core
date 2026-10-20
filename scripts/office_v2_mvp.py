#!/usr/bin/env python3
"""Read-only Office 2.0 desk.

Gathers open pull requests, the #612 claim queue, the latest check-all run on
main, and items waiting on the owner. Writes a Hebrew+English board. Never
writes to GitHub, never calls an LLM, and never prints credentials.

CrewAI and LangGraph are not in the sensor lockfile, so this desk is plain
Python. The next step, after a protected admission, is recorded in
docs/office-v2/NEXT.md and points at the verified research on
https://github.com/nocturney/velvetos-core/issues/595#issuecomment-6249011608
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import vf_subprocess_hygiene as hygiene

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
BOARD_DIR = ROOT / "docs" / "office-v2" / "board"
JERUSALEM = ZoneInfo("Asia/Jerusalem")
REPOS = ("nocturney/velvetos-core", "nocturney/velvetos-velvet-factory")
# The factory repo is private. Its rows may exist only in a gitignored local board.
PRIVATE_REPO_MARK = "velvetos-velvet-factory"
QUEUE_REPO = "nocturney/velvetos-core"
QUEUE_ISSUE = 612
CHECK_ALL_REPO = "nocturney/velvetos-core"
SCHEMA = "velvetos.office-v2.board.v0"
STALE_AFTER = timedelta(hours=24)
FRESHNESS_RANK = {"FRESH": 0, "STALE": 1, "UNKNOWN": 2}
PASSING_CONCLUSIONS = {"success", "skipped", "neutral"}
RESEARCH_COMMENT = (
    "https://github.com/nocturney/velvetos-core/issues/595#issuecomment-6249011608"
)
# #764 merge. The board cites this seal; it does not promote security admission.
LOSTACK_MERGE = "9c2f33474ab00007093c4e1913235004a4bc025d"
LOSTACK_DOC = (
    "docs/implementation/office-v2/phase2/"
    "p0-604-cp083-native-lostack-two-receipts-2026-10-18.md"
)
LOSTACK_URL = (
    "https://github.com/nocturney/velvetos-core/blob/"
    + LOSTACK_MERGE
    + "/"
    + LOSTACK_DOC
)
LOSTACK_STATUS = "PASS_TWO_NATIVE_LOCAL_RECEIPTS_SECURITY_RED"
LOSTACK_HOSTS = ("MacMiniOffice.local", "Mac-Bedroom.local")
AGENTS = ("cursor", "chatgpt", "claude", "gemini", "auditor")
AGENT_LABELS = {
    "cursor": "Cursor",
    "chatgpt": "ChatGPT",
    "claude": "Claude",
    "gemini": "Gemini",
    "auditor": "auditor",
    "unassigned": "unassigned",
}

SECRET_RE = re.compile(
    r"(?i)(?:ghp_|github_pat_|gho_|ghu_|ghs_|ghr_)[A-Za-z0-9_]{8,}"
    r"|bearer\s+[A-Za-z0-9._\-]{8,}"
    r"|(?:token|authorization|api[_-]?key)\s*[:=]\s*\S+"
)
OWNER_RE = re.compile(
    r"(?i)(?:waiting on (?:christian|the owner|owner)|needs owner|"
    r"owner gate|owner decision|מחכה לכריסטיאן|ממתין לבעלים)"
)
QUEUE_MARKER_RE = re.compile(
    r"(?im)^[ \t>*_-]*(?:[A-Za-z][A-Za-z0-9 _()/.-]{0,40}:\s*)?"
    r"(CLAIM|DONE|BLOCKED|WAITING|STATUS)\b"
)
AGENT_RES = (
    ("auditor", re.compile(r"(?i)\bauditor\b")),
    ("cursor", re.compile(r"(?i)\bcursor\b")),
    ("chatgpt", re.compile(r"(?i)\bchatgpt\b")),
    ("claude", re.compile(r"(?i)\bclaude\b")),
    ("gemini", re.compile(r"(?i)\bgemini\b")),
)
ISSUE_URL_RE = re.compile(
    r"github\.com/([\w.-]+)/([\w.-]+)/(?:issues|pull)/(\d+)"
)
BARE_ISSUE_RE = re.compile(r"(?<![A-Za-z0-9])#(\d+)\b")
FAIL_RE = re.compile(r"\bFAIL\b")


class ReadOnlyViolation(RuntimeError):
    """Raised when a caller asks the desk to do anything other than GET."""


class GitHubReadError(RuntimeError):
    """Raised when a required read fails and the board would be invented."""


def redact(text: str) -> str:
    if not text:
        return ""
    return SECRET_RE.sub("[redacted]", text)


def excerpt(text: str, limit: int = 180) -> str:
    flat = re.sub(r"\s+", " ", redact(text or "")).strip()
    if len(flat) <= limit:
        return flat
    return flat[: limit - 1] + "…"


def parse_time(value: str | None) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def jerusalem(value: str | None) -> str:
    moment = parse_time(value)
    if moment is None:
        return ""
    local = moment.astimezone(JERUSALEM)
    return local.strftime("%Y-%m-%d %H:%M") + " Asia/Jerusalem"


def jerusalem_date(moment: datetime) -> str:
    return moment.astimezone(JERUSALEM).date().isoformat()


def pull_agent(pull: dict) -> str | None:
    body_line = ((pull.get("body") or "").splitlines() or [""])[0]
    return detect_agent(f"{pull.get('title') or ''}\n{body_line}")


def detect_agent(text: str) -> str | None:
    head = text[:400]
    found: list[tuple[int, str]] = []
    for name, pattern in AGENT_RES:
        match = pattern.search(head)
        if match:
            found.append((match.start(), name))
    if not found:
        return None
    return min(found)[1]


def queue_marker(body: str) -> str | None:
    head = "\n".join((body or "").splitlines()[:12])[:500]
    match = QUEUE_MARKER_RE.search(head)
    return match.group(1).upper() if match else None


def issue_refs(body: str) -> list[tuple[str, int]]:
    """Issue numbers a queue comment assigns. #612 is the queue itself."""
    text = body or ""
    found: list[tuple[str, int]] = []
    seen: set[tuple[str, int]] = set()

    def add(repo: str, number: int) -> None:
        if number == QUEUE_ISSUE and repo == QUEUE_REPO:
            return
        key = (repo, number)
        if key in seen or number < 1:
            return
        seen.add(key)
        found.append(key)

    for match in ISSUE_URL_RE.finditer(text):
        if "/issues/" in match.group(0):
            add(f"{match.group(1)}/{match.group(2)}", int(match.group(3)))
    stripped = ISSUE_URL_RE.sub(" ", text)
    stripped = re.sub(r"issuecomment-\d+", " ", stripped)
    for match in BARE_ISSUE_RE.finditer(stripped):
        add(QUEUE_REPO, int(match.group(1)))
    return found


def board_text_leaks_private(text: str) -> bool:
    """True when board text contains the private factory repo, one of its URLs, or a row."""
    return PRIVATE_REPO_MARK in (text or "").casefold()


def active_issue_refs(comments: list[dict]) -> list[tuple[str, int]]:
    """Issue refs on the latest non-DONE claim only.

    Older comments and finished claims are not fetched. That keeps the #612
    read to the live queue instead of every historical issue number.
    """
    grouped: dict[str, list[dict]] = defaultdict(list)
    for comment in comments:
        body = comment.get("body") or ""
        if queue_marker(body) is None:
            continue
        grouped[claim_key(body)].append(comment)
    wanted: list[tuple[str, int]] = []
    seen: set[tuple[str, int]] = set()
    for group in grouped.values():
        group.sort(key=lambda comment: comment.get("created_at") or "")
        body = group[-1].get("body") or ""
        marker = queue_marker(body) or ""
        if marker in {"DONE", "STATUS"}:
            continue
        for ref in issue_refs(body):
            if ref not in seen:
                seen.add(ref)
                wanted.append(ref)
    return wanted


def claim_key(body: str) -> str:
    head = (body or "")[:800]
    match = re.search(r"\b(CLQ-\d+)\b", head, re.I)
    if match:
        return match.group(1).upper()
    match = re.search(r"\b(CP\d{3})\b", head)
    if match:
        return match.group(1)
    refs = issue_refs(head)
    if refs:
        return f"{refs[0][0]}#{refs[0][1]}"
    first = re.sub(r"\s+", " ", (body or "").strip().splitlines()[0] if body else "")
    slug = re.sub(r"[^a-z0-9]+", "-", first.lower()).strip("-")[:48]
    return "line:" + (slug or "empty")


def github_request(method: str, path: str, runner=None):
    """Perform one GitHub read. Any method other than GET is refused."""
    if method.upper() != "GET":
        raise ReadOnlyViolation(f"refusing non-GET GitHub call ({method})")
    if not path.startswith("/"):
        path = "/" + path
    lowered = path.lower()
    if any(token in lowered for token in ("/merge", "/dispatches", "method=post")):
        raise ReadOnlyViolation(f"refusing non-read GitHub path ({path})")
    if runner is not None:
        return runner(path)
    return _gh_get(path)


def _collection(path: str) -> bool:
    base = path.split("?", 1)[0].rstrip("/")
    if "state=closed" in path:
        return False
    return base.endswith("/pulls") or base.endswith("/comments")


def _gh_get(path: str) -> dict:
    api_path = path[1:] if path.startswith("/") else path
    if not api_path or api_path[:1] == "-":
        raise GitHubReadError("refusing a GitHub path that starts with a dash")
    cmd = ["api", "--method", "GET", "--hostname", "github.com"]
    if _collection(path):
        cmd.append("--paginate")
    cmd.append(api_path)
    try:
        proc = hygiene.run_pinned(
            "gh",
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=90,
            extra_keys=hygiene.GH_CONFIG_ENV_KEYS,
        )
    except (FileNotFoundError, hygiene.HygieneError) as exc:
        raise GitHubReadError("gh CLI is not installed") from exc
    except subprocess.TimeoutExpired as exc:
        raise GitHubReadError(f"GitHub read timed out for {path.split('?', 1)[0]}") from exc
    if proc.returncode != 0:
        detail = redact(proc.stderr or proc.stdout or "")
        status = 1
        match = re.search(r"\b(\d{3})\b", detail)
        if match:
            status = int(match.group(1))
        return {"ok": False, "status": status, "error": excerpt(detail, 240), "data": None}
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise GitHubReadError(f"GitHub returned non-JSON for {path.split('?', 1)[0]}") from exc
    return {"ok": True, "status": 200, "error": "", "data": data}


def _comment_view(comment: dict) -> dict:
    return {
        "id": comment.get("id"),
        "url": comment.get("html_url") or "",
        "created_at": comment.get("created_at") or "",
        "created_at_jerusalem": jerusalem(comment.get("created_at")),
        "excerpt": excerpt(comment.get("body") or ""),
    }


def qa_state(comments: list[dict]) -> dict:
    signals: list[tuple[dict, list[str]]] = []
    for comment in comments or []:
        body = comment.get("body") or ""
        low = body.lower()
        kinds = []
        if "qa verdict" in low:
            kinds.append("verdict")
        if "qa please" in low:
            kinds.append("please")
        if kinds:
            signals.append((comment, kinds))
    if not signals:
        return {"please": None, "verdict": None, "latest_kind": None, "latest_body": ""}
    latest, kinds = max(signals, key=lambda item: item[0].get("created_at") or "")
    latest_kind = "verdict" if "verdict" in kinds else "please"

    def last(kind: str) -> dict | None:
        hits = [comment for comment, found in signals if kind in found]
        if not hits:
            return None
        return _comment_view(max(hits, key=lambda comment: comment.get("created_at") or ""))

    return {
        "please": last("please"),
        "verdict": last("verdict"),
        "latest_kind": latest_kind,
        "latest_body": latest.get("body") or "",
    }


def _item(
    *,
    kind: str,
    repo: str,
    number: int | None,
    title: str,
    url: str,
    section: str,
    agent: str | None,
    status: str,
    when: str,
    draft: bool | None = None,
    head_sha: str = "",
    qa_please: dict | None = None,
    qa_verdict: dict | None = None,
    open_issues: list[dict] | None = None,
    extra: dict | None = None,
) -> dict:
    row = {
        "kind": kind,
        "repo": repo,
        "number": number,
        "title": excerpt(title, 160),
        "url": url,
        "section": section,
        "agent": agent,
        "status": status,
        "draft": draft,
        "head_sha": head_sha,
        "qa_please": qa_please,
        "qa_verdict": qa_verdict,
        "open_issues": open_issues or [],
        "when": when,
        "when_jerusalem": jerusalem(when),
    }
    if extra:
        row.update(extra)
    return row


def _open_issue_rows(refs: list[tuple[str, int]], issues: dict) -> list[dict]:
    rows = []
    for repo, number in refs:
        issue = issues.get(f"{repo}#{number}")
        if not isinstance(issue, dict):
            continue
        if issue.get("state") != "open":
            continue
        if issue.get("pull_request"):
            continue
        rows.append(
            {
                "repo": repo,
                "number": number,
                "title": excerpt(issue.get("title") or "", 160),
                "url": issue.get("html_url") or "",
                "state": "open",
            }
        )
    return rows


def _route_pr(pull: dict, qa: dict) -> str:
    draft = bool(pull.get("draft"))
    # Owner waits come from the title or the latest QA comment, not from a
    # pull-request body that merely describes the desk.
    owner = OWNER_RE.search(pull.get("title") or "") is not None or OWNER_RE.search(
        qa.get("latest_body") or ""
    ) is not None
    please_excerpt = ((qa.get("please") or {}) if qa.get("latest_kind") == "please" else {}).get(
        "excerpt"
    ) or ""
    fresh_please = (not draft) and qa.get("latest_kind") == "please"
    if fresh_please and not OWNER_RE.search(please_excerpt):
        return "waiting_on_qa"
    if owner:
        return "waiting_on_christian"
    if fresh_please:
        return "waiting_on_qa"
    if (not draft) and qa.get("latest_kind") == "verdict" and FAIL_RE.search(qa.get("latest_body") or ""):
        return "blocked"
    return "in_progress"


def _route_claim(marker: str, body: str) -> str | None:
    if marker == "STATUS":
        return None
    if marker == "DONE":
        return "done_today"
    if marker == "BLOCKED":
        return "blocked"
    # Only the opening line counts. A claim that describes the board must not
    # land in "waiting on Christian" just because those words appear in scope.
    first = (body or "").splitlines()[0][:240] if body else ""
    if marker == "WAITING" and OWNER_RE.search((body or "")[:400]):
        return "waiting_on_christian"
    if marker == "CLAIM" and OWNER_RE.search(first):
        return "waiting_on_christian"
    if marker in {"CLAIM", "WAITING"}:
        return "in_progress"
    return None


def _pr_item(repo: str, pull: dict, comments: list[dict], *, comments_unavailable: bool = False) -> dict:
    qa = qa_state(comments)
    agent = pull_agent(pull)
    head = pull.get("head") if isinstance(pull.get("head"), dict) else {}
    sha = head.get("sha") or ""
    if comments_unavailable:
        section = "blocked"
        status = "comments_unavailable"
    else:
        section = _route_pr(pull, qa)
        status = "draft" if pull.get("draft") else (qa.get("latest_kind") or "open")
        if section == "waiting_on_qa":
            status = "waiting_on_qa"
        elif section == "waiting_on_christian":
            status = "waiting_on_christian"
        elif section == "blocked":
            status = "qa_fail"
    return _item(
        kind="pull_request",
        repo=repo,
        number=pull.get("number"),
        title=pull.get("title") or "",
        url=pull.get("html_url") or "",
        section=section,
        agent=agent,
        status=status,
        when=pull.get("updated_at") or pull.get("created_at") or "",
        draft=bool(pull.get("draft")),
        head_sha=sha,
        qa_please=qa.get("please"),
        qa_verdict=qa.get("verdict"),
    )


def _check_all_view(payload: dict | None) -> dict | None:
    if not isinstance(payload, dict):
        return None
    if payload.get("denied"):
        return {
            "repo": CHECK_ALL_REPO,
            "name": "check-all",
            "denied": True,
            "status": "denied",
            "conclusion": "",
            "http_status": payload.get("status"),
            "event": "",
            "head_sha": "",
            "url": "",
            "created_at": "",
            "created_at_jerusalem": "",
        }
    runs = payload.get("workflow_runs") or []
    if not runs:
        return None
    run = runs[0]
    return {
        "repo": CHECK_ALL_REPO,
        "name": run.get("name") or "check-all",
        "status": run.get("status") or "",
        "conclusion": run.get("conclusion") or "",
        "event": run.get("event") or "",
        "head_sha": run.get("head_sha") or "",
        "url": run.get("html_url") or "",
        "created_at": run.get("created_at") or "",
        "created_at_jerusalem": jerusalem(run.get("created_at")),
    }


def _load_lostack_gate():
    path = ROOT / "scripts" / "vf_office_v2_604_cp083_native_lostack_receipt_gate.py"
    spec = importlib.util.spec_from_file_location("vf_cp083_lostack_gate", path)
    if spec is None or spec.loader is None:
        raise ImportError("lost-ACK receipt gate missing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def seal_row_from_result(result: dict) -> dict | None:
    """A board row exists only for the sealed RED result. GREEN is not a row."""
    if not isinstance(result, dict):
        return None
    if result.get("security_admission") != "RED":
        return None
    if result.get("status") != LOSTACK_STATUS:
        return None
    writes = result.get("remote_github_writes")
    if type(writes) is not int or writes != 0:
        return None
    if result.get("real_native_git_sqlite_receipts") != 2:
        return None
    if result.get("distinct_hosts") != 2:
        return None
    return {
        "lane": "CP083 lost-ACK receipts",
        "label": "SEALED_RED_ONLY",
        "security_admission": "RED",
        "url": LOSTACK_URL,
        "pr": 764,
        "merge": LOSTACK_MERGE,
    }


def cp083_lostack_view(evidence_path: Path | None = None) -> dict:
    """Seal the lost-ACK evidence, or drop only that row.

    A missing or unreadable file is EVIDENCE_MISSING. A gate that cannot be
    imported is GATE_IMPORT_FAILED. Readable evidence that fails the RED seal
    is OMITTED. None of these statuses crashes the rest of the board, and none
    of them publishes a seal row.
    """
    try:
        module = _load_lostack_gate()
    except (ImportError, OSError, SyntaxError):
        return {"status": "GATE_IMPORT_FAILED"}
    path = Path(evidence_path) if evidence_path is not None else module.EVIDENCE
    try:
        evidence = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return {"status": "EVIDENCE_MISSING"}
    if not isinstance(evidence, dict):
        return {"status": "EVIDENCE_MISSING"}
    try:
        result = module.validate(evidence)
    except (module.Refused, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return {"status": "OMITTED"}
    row = seal_row_from_result(result)
    if row is None:
        return {"status": "OMITTED"}
    hosts = []
    for item in evidence.get("receipts") or []:
        device = item.get("device") if isinstance(item, dict) else None
        if isinstance(device, str):
            hosts.append(device)
    if tuple(hosts) != LOSTACK_HOSTS:
        return {"status": "OMITTED"}
    row["hosts"] = hosts
    return {"status": "SEALED_RED_ONLY", "row": row}


def cp083_lostack_seal() -> dict | None:
    return cp083_lostack_view().get("row")


def sealed_lab_text_ok(text: str) -> bool:
    start = text.find("## חותמות מעבדה · Sealed labs")
    if start < 0:
        return False
    rest = text[start:]
    nxt = rest.find("\n## ", 3)
    section = rest if nxt < 0 else rest[:nxt]
    return (
        "SEALED_RED_ONLY" in section
        and "security_admission=RED" in section
        and LOSTACK_URL in section
        and "security_admission=GREEN" not in section
        and "ADMITTED" not in section
    )


def build_board(snapshot: dict, now: datetime) -> dict:
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    today = jerusalem_date(now)
    issues = snapshot.get("issues") or {}
    issue_comments = snapshot.get("issue_comments") or {}
    review_comments = snapshot.get("review_comments") or {}
    access = snapshot.get("repo_access") or {}
    items: list[dict] = []

    for repo in REPOS:
        repo_access = access.get(repo) or {"ok": True}
        if repo_access.get("ok") is False:
            continue
        for pull in snapshot.get("pulls", {}).get(repo) or []:
            if pull.get("state", "open") != "open":
                continue
            key = f"{repo}#{pull.get('number')}"
            unavailable = bool(pull.get("comments_unavailable"))
            comments = list(issue_comments.get(key) or []) + list(review_comments.get(key) or [])
            items.append(_pr_item(repo, pull, comments, comments_unavailable=unavailable))
        for pull in snapshot.get("merged_pulls", {}).get(repo) or []:
            merged_at = pull.get("merged_at") or ""
            moment = parse_time(merged_at)
            if moment is None or jerusalem_date(moment) != today:
                continue
            head = pull.get("head") if isinstance(pull.get("head"), dict) else {}
            agent = pull_agent(pull)
            items.append(
                _item(
                    kind="pull_request",
                    repo=repo,
                    number=pull.get("number"),
                    title=pull.get("title") or "",
                    url=pull.get("html_url") or "",
                    section="done_today",
                    agent=agent,
                    status="merged",
                    when=merged_at,
                    draft=False,
                    head_sha=head.get("sha") or "",
                )
            )

    grouped: dict[str, list[dict]] = defaultdict(list)
    for comment in snapshot.get("queue_comments") or []:
        body = comment.get("body") or ""
        marker = queue_marker(body)
        if marker is None:
            continue
        grouped[claim_key(body)].append(comment)

    for key, comments in grouped.items():
        comments.sort(key=lambda comment: comment.get("created_at") or "")
        latest = comments[-1]
        body = latest.get("body") or ""
        marker = queue_marker(body) or ""
        section = _route_claim(marker, body)
        if section is None:
            continue
        when = latest.get("created_at") or ""
        moment = parse_time(when)
        if section == "done_today":
            if moment is None or jerusalem_date(moment) != today:
                continue
        agent = detect_agent(body)
        refs = issue_refs(body)
        items.append(
            _item(
                kind="claim",
                repo=QUEUE_REPO,
                number=QUEUE_ISSUE,
                title=body.splitlines()[0] if body else key,
                url=latest.get("html_url") or "",
                section=section,
                agent=agent,
                status=marker.lower(),
                when=when,
                open_issues=_open_issue_rows(refs, issues),
                extra={"claim_key": key},
            )
        )

    check_all = _check_all_view((snapshot.get("check_all_runs") or {}).get(CHECK_ALL_REPO))
    if check_all and check_all.get("status") == "completed" and check_all.get("conclusion") not in {
        "success",
        "skipped",
        "neutral",
    }:
        items.append(
            _item(
                kind="workflow_run",
                repo=CHECK_ALL_REPO,
                number=None,
                title=f"check-all on main {check_all.get('conclusion') or check_all.get('status')}",
                url=check_all.get("url") or "",
                section="blocked",
                agent=None,
                status=check_all.get("conclusion") or "failure",
                when=check_all.get("created_at") or "",
                head_sha=check_all.get("head_sha") or "",
            )
        )

    items.sort(key=lambda row: row.get("when") or "", reverse=True)
    in_progress = {agent: [] for agent in (*AGENTS, "unassigned")}
    sections = {
        "waiting_on_christian": [],
        "waiting_on_qa": [],
        "in_progress": in_progress,
        "blocked": [],
        "done_today": [],
    }
    for row in items:
        if row["section"] == "in_progress":
            bucket = row.get("agent") or "unassigned"
            if bucket not in in_progress:
                bucket = "unassigned"
            in_progress[bucket].append(row)
        else:
            sections[row["section"]].append(row)

    generated = now.astimezone(JERUSALEM)
    lostack = cp083_lostack_view()
    board = {
        "schema": SCHEMA,
        "generated_at": generated.isoformat(timespec="minutes"),
        "generated_at_jerusalem": generated.strftime("%Y-%m-%d %H:%M") + " Asia/Jerusalem",
        "as_of": now.astimezone(timezone.utc).isoformat(timespec="seconds"),
        "fetched_at": snapshot.get("fetched_at"),
        "timezone": "Asia/Jerusalem",
        "read_only": True,
        "writes_to_github": False,
        "llm_calls": False,
        "repos": list(REPOS),
        "repo_access": access,
        "queue": {"repo": QUEUE_REPO, "issue": QUEUE_ISSUE},
        "check_all_main": check_all,
        "sections": sections,
        "sealed_labs": [lostack["row"]] if lostack.get("row") else [],
        "lostack_evidence_status": lostack.get("status") or "OMITTED",
        "next_step": {
            "framework": "plain-python",
            "reason": (
                "CrewAI and LangGraph are not in requirements-sensors.txt or the hashed lockfiles. "
                "Do not import them until a protected admission adds them."
            ),
            "research_comment": RESEARCH_COMMENT,
            "research_comment_id": 6249011608,
            "doc": "docs/office-v2/NEXT.md",
        },
    }
    board["overview"] = build_overview(board)
    return board


def freshness(stamp: str | None, as_of: str | None) -> str:
    """FRESH within STALE_AFTER of as_of, STALE when older, UNKNOWN when missing, naive, invalid or in the future."""
    moment = parse_time(stamp)
    reference = parse_time(as_of)
    if moment is None or reference is None or moment.tzinfo is None or reference.tzinfo is None:
        return "UNKNOWN"
    age = reference - moment
    if age < timedelta(0):
        return "UNKNOWN"
    return "STALE" if age > STALE_AFTER else "FRESH"


def _active_rows(board: dict) -> list[dict]:
    sections = board.get("sections") or {}
    rows: list[dict] = []
    for name, group in sections.items():
        if name == "done_today":
            continue
        if name == "in_progress" and isinstance(group, dict):
            for items in group.values():
                rows.extend(items)
        elif isinstance(group, list):
            rows.extend(group)
    return rows


def build_overview(board: dict) -> dict:
    """Summarise only the rows this board holds. Call it after any private-row filter."""
    as_of = board.get("as_of")
    fetched = board.get("fetched_at")
    read_state = freshness(fetched, as_of)
    access = board.get("repo_access") or {}
    denied = sum(1 for row in access.values() if isinstance(row, dict) and row.get("ok") is False)
    counts = {agent: 0 for agent in (*AGENTS, "unassigned")}
    for row in _active_rows(board):
        if row.get("kind") not in {"pull_request", "claim"}:
            continue
        agent = row.get("agent") if row.get("agent") in AGENTS else "unassigned"
        counts[agent] += 1
    if denied:
        agents = {"state": "UNKNOWN", "reason": f"{denied} repo read(s) denied", "counts": counts}
    elif read_state == "UNKNOWN":
        agents = {"state": "UNKNOWN", "reason": "last-verified timestamp missing or invalid", "counts": counts}
    else:
        reason = "last GitHub readback older than 24h" if read_state == "STALE" else ""
        agents = {"state": read_state, "reason": reason, "counts": counts}

    run = board.get("check_all_main") or {}
    if run.get("denied"):
        jobs = {"state": "UNKNOWN", "freshness": "UNKNOWN", "reason": f"denied (HTTP {run.get('http_status') or '?'})"}
    elif not run.get("status"):
        jobs = {"state": "UNKNOWN", "freshness": "UNKNOWN", "reason": "no check-all run read"}
    else:
        if run.get("status") != "completed":
            state = "IN_PROGRESS"
        else:
            state = "PASS" if run.get("conclusion") in PASSING_CONCLUSIONS else "FAIL"
        run_state = freshness(run.get("created_at"), as_of)
        jobs_state = max(read_state, run_state, key=FRESHNESS_RANK.get)
        jobs = {"state": state, "freshness": jobs_state, "reason": ""}
        if jobs_state == "UNKNOWN":
            jobs["reason"] = "run or readback timestamp missing or invalid"

    health = max(agents["state"], jobs["freshness"], key=FRESHNESS_RANK.get)
    return {
        "as_of": as_of,
        "last_verified": fetched,
        "agents": agents,
        "jobs": jobs,
        "machines": {"state": "UNKNOWN", "reason": "no verified public machine feed is wired into this board"},
        "health": {"state": health, "basis": "worst of agents and jobs freshness"},
    }


def _fmt_item(row: dict) -> str:
    repo = row.get("repo") or ""
    short = repo.split("/")[-1]
    number = row.get("number")
    label = f"{short}#{number}" if number else short
    url = row.get("url") or ""
    title = row.get("title") or ""
    bits = [f"[{label}]({url})" if url else label]
    if row.get("draft") is True and row.get("status") != "draft":
        bits.append("draft")
    if row.get("status"):
        bits.append(str(row["status"]))
    sha = row.get("head_sha") or ""
    if sha:
        bits.append(f"head `{sha}`")
    please = row.get("qa_please") or None
    verdict = row.get("qa_verdict") or None
    if please:
        bits.append(
            f"[QA please]({please.get('url')}) {please.get('created_at_jerusalem') or ''}".strip()
        )
    if verdict:
        bits.append(
            f"[QA verdict]({verdict.get('url')}) {verdict.get('created_at_jerusalem') or ''}".strip()
        )
    when = row.get("when_jerusalem") or ""
    if when:
        bits.append(when)
    issues = row.get("open_issues") or []
    if issues:
        linked = ", ".join(
            f"[#{issue['number']}]({issue['url']})" if issue.get("url") else f"#{issue['number']}"
            for issue in issues
        )
        bits.append(f"open issues {linked}")
    line = "- " + " · ".join(bit for bit in bits if bit)
    if title:
        line += f" — {title}"
    return line


def _overview_lines(board: dict) -> list[str]:
    overview = board.get("overview") or {}
    agents = overview.get("agents") or {}
    jobs = overview.get("jobs") or {}
    machines = overview.get("machines") or {}
    health = overview.get("health") or {}
    verified = jerusalem(overview.get("last_verified")) or "UNKNOWN"
    counts = " · ".join(f"{agent} {n}" for agent, n in (agents.get("counts") or {}).items() if n)
    agent_bits = [agents.get("state") or "UNKNOWN"]
    if agents.get("reason"):
        agent_bits.append(agents["reason"])
    if agents.get("state") != "UNKNOWN":
        agent_bits.append(counts or "0 active")
    agent_bits.append(f"verified {verified}")
    job_bits = [jobs.get("state") or "UNKNOWN"]
    if jobs.get("reason"):
        job_bits.append(jobs["reason"])
    run = board.get("check_all_main") or {}
    if run.get("status") and not run.get("denied"):
        sha = (run.get("head_sha") or "")[:12]
        job_bits.append(f"check-all on main {run.get('conclusion') or run.get('status')}")
        if sha:
            job_bits.append(f"[{sha}]({run['url']})" if run.get("url") else f"`{sha}`")
        job_bits.append(f"freshness {jobs.get('freshness') or 'UNKNOWN'}")
        if run.get("created_at_jerusalem"):
            job_bits.append(run["created_at_jerusalem"])
    machine_bits = [machines.get("state") or "UNKNOWN", machines.get("reason") or ""]
    health_bits = [health.get("state") or "UNKNOWN", health.get("basis") or "", f"verified {verified}"]
    return [
        "## סקירה · Overview",
        "",
        f"- סוכנים · Agents: {' · '.join(agent_bits)}",
        f"- עבודות · Jobs: {' · '.join(job_bits)}",
        f"- מכונות · Machines: {' · '.join(bit for bit in machine_bits if bit)}",
        f"- בריאות · Health: {' · '.join(bit for bit in health_bits if bit)}",
        "",
    ]


def render_markdown(board: dict) -> str:
    sections = board["sections"]
    lines = [
        "# לוח המשרד · Office board",
        "",
        f"- נוצר · generated: {board.get('generated_at_jerusalem')}",
        "- קריאה בלבד · read-only GitHub GET. No writes, no LLM, no secrets.",
        f"- תור · queue: [{QUEUE_REPO}#{QUEUE_ISSUE}](https://github.com/{QUEUE_REPO}/issues/{QUEUE_ISSUE})",
    ]
    check_all = board.get("check_all_main")
    if check_all and check_all.get("denied"):
        lines.append(
            "- check-all על main · check-all on main: "
            f"denied (HTTP {check_all.get('http_status') or '?'}). No run invented."
        )
    elif check_all:
        lines.append(
            "- check-all על main · check-all on main: "
            f"{check_all.get('conclusion') or check_all.get('status')} · "
            f"[{check_all.get('head_sha', '')[:12]}]({check_all.get('url')}) · "
            f"{check_all.get('created_at_jerusalem')}"
        )
    else:
        lines.append("- check-all על main · check-all on main: אין ריצה · no run")
    if board.get("private_rows_omitted"):
        lines.append(
            "- Private repository rows are omitted from this copy. No private titles, SHAs, or URLs."
        )
    access = board.get("repo_access") or {}
    shown = board.get("repos") if board.get("private_rows_omitted") else REPOS
    for repo in shown:
        row = access.get(repo) or {"ok": True}
        if row.get("ok") is False:
            lines.append(
                f"- גישה · access {repo}: denied (HTTP {row.get('status') or '?'}). No rows invented."
            )
        else:
            lines.append(f"- גישה · access {repo}: ok")
    lines.append("")
    lines.extend(_overview_lines(board))

    def block(title: str, rows: list[dict]) -> None:
        lines.append(f"## {title}")
        lines.append("")
        if not rows:
            lines.append("_אין פריטים · none_")
        else:
            lines.extend(_fmt_item(row) for row in rows)
        lines.append("")

    block("מחכה לכריסטיאן · Waiting on Christian", sections["waiting_on_christian"])
    block("מחכה ל-QA · Waiting on QA", sections["waiting_on_qa"])
    lines.append("## בעבודה · In progress")
    lines.append("")
    progress = sections["in_progress"]
    for agent in (*AGENTS, "unassigned"):
        rows = progress.get(agent) or []
        if agent == "unassigned" and not rows:
            continue
        lines.append(f"### {AGENT_LABELS[agent]}")
        lines.append("")
        if not rows:
            lines.append("_אין פריטים · none_")
        else:
            lines.extend(_fmt_item(row) for row in rows)
        lines.append("")
    block("חסום · Blocked", sections["blocked"])
    block("הושלם היום · Done today", sections["done_today"])
    lines.append("## חותמות מעבדה · Sealed labs")
    lines.append("")
    seal_lines = []
    for row in board.get("sealed_labs") or []:
        if row.get("label") != "SEALED_RED_ONLY" or row.get("security_admission") != "RED":
            continue
        if row.get("url") != LOSTACK_URL:
            continue
        hosts = ", ".join(row.get("hosts") or [])
        seal_lines.append(
            f"- {row.get('lane')} · SEALED_RED_ONLY · security_admission=RED · "
            f"[evidence]({row['url']}) · "
            f"[#764](https://github.com/nocturney/velvetos-core/pull/764) "
            f"`9c2f3347` · {hosts}"
        )
    status = board.get("lostack_evidence_status")
    if status == "EVIDENCE_MISSING":
        lines.append("- CP083 lost-ACK receipts · EVIDENCE_MISSING")
    elif status == "GATE_IMPORT_FAILED":
        lines.append("- CP083 lost-ACK receipts · GATE_IMPORT_FAILED")
    elif seal_lines:
        lines.extend(seal_lines)
    else:
        lines.append("_אין חותמת · none_")
    lines.append("")
    nxt = board.get("next_step") or {}
    lines.append("## הצעד הבא · Next step")
    lines.append("")
    lines.append(
        "Python רגיל · plain Python. CrewAI / LangGraph stay out until the lockfile admits them. "
        f"Verified research: {nxt.get('research_comment')}"
    )
    lines.append("")
    text = "\n".join(lines)
    if SECRET_RE.search(text):
        raise ReadOnlyViolation("refusing to render a board that still contains a secret")
    return text


def render_json(board: dict) -> str:
    text = json.dumps(board, ensure_ascii=False, indent=2) + "\n"
    if SECRET_RE.search(text):
        raise ReadOnlyViolation("refusing to write a board that still contains a secret")
    return text


def _git(args: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return hygiene.run_pinned(
        "git",
        args,
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def private_rows_allowed(paths: list[Path], root: Path) -> bool:
    """Private rows may be written only to a gitignored, untracked path inside this repo."""
    root = root.resolve()
    for path in paths:
        try:
            rel = path.resolve().relative_to(root).as_posix()
        except ValueError:
            return False
        if _git(["ls-files", "--error-unmatch", "--", rel], root).returncode == 0:
            return False
        if _git(["check-ignore", "--no-index", "-q", "--", rel], root).returncode != 0:
            return False
    return True


def omit_private_rows(board: dict) -> dict:
    """Drop private-repo rows, URLs, and titles before a tracked or public write."""
    board = json.loads(json.dumps(board))

    def keep(row: dict) -> bool:
        blob = "\n".join(
            str(row.get(key) or "") for key in ("repo", "url", "title", "html_url")
        )
        return not board_text_leaks_private(blob)

    def scrub(row: dict) -> dict:
        row["open_issues"] = [issue for issue in row.get("open_issues") or [] if keep(issue)]
        return row

    sections = board.get("sections") or {}
    for name, rows in list(sections.items()):
        if name == "in_progress" and isinstance(rows, dict):
            for agent, items in list(rows.items()):
                rows[agent] = [scrub(row) for row in items if keep(row)]
        elif isinstance(rows, list):
            sections[name] = [scrub(row) for row in rows if keep(row)]
    board["repos"] = [
        repo for repo in board.get("repos") or [] if not board_text_leaks_private(str(repo))
    ]
    access = board.get("repo_access") or {}
    for repo in list(access):
        if board_text_leaks_private(str(repo)):
            del access[repo]
    board["repo_access"] = access
    board["private_rows_omitted"] = True
    # Counts must come from the filtered rows, never from the pre-filter board.
    board["overview"] = build_overview(board)
    return board


def write_board(
    board: dict,
    root: Path = ROOT,
    dest: Path | None = None,
    omit_private: bool = False,
) -> tuple[Path, Path]:
    folder = dest if dest is not None else (root / "docs" / "office-v2" / "board")
    folder.mkdir(parents=True, exist_ok=True)
    md_path = folder / "latest.md"
    json_path = folder / "latest.json"
    public_copy = omit_private or not private_rows_allowed([md_path, json_path], root)
    if public_copy:
        board = omit_private_rows(board)
    markdown = render_markdown(board)
    payload = render_json(board)
    if public_copy and (
        board_text_leaks_private(markdown) or board_text_leaks_private(payload)
    ):
        raise ReadOnlyViolation(
            "refusing to write private repository rows into a tracked or public board path"
        )
    md_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(payload, encoding="utf-8")
    return md_path, json_path


def _require_data(response: dict, label: str) -> object:
    if not response.get("ok"):
        status = response.get("status")
        if status in {401, 403, 404}:
            return None
        raise GitHubReadError(f"{label} failed ({status}): {response.get('error') or 'read error'}")
    return response.get("data")


def fetch_snapshot() -> dict:
    snapshot: dict = {
        "pulls": {},
        "issue_comments": {},
        "review_comments": {},
        "queue_comments": [],
        "issues": {},
        "merged_pulls": {},
        "check_all_runs": {},
        "repo_access": {},
    }
    for repo in REPOS:
        opened = github_request("GET", f"/repos/{repo}/pulls?state=open&per_page=100")
        if not opened.get("ok"):
            if opened.get("status") in {401, 403, 404}:
                snapshot["repo_access"][repo] = {
                    "ok": False,
                    "status": opened.get("status"),
                }
                snapshot["pulls"][repo] = []
                snapshot["merged_pulls"][repo] = []
                continue
            raise GitHubReadError(
                f"open pulls for {repo} failed ({opened.get('status')}): {opened.get('error')}"
            )
        snapshot["repo_access"][repo] = {"ok": True}
        pulls = opened.get("data") or []
        if not isinstance(pulls, list):
            raise GitHubReadError(f"open pulls for {repo} were not a list")
        snapshot["pulls"][repo] = pulls
        closed = github_request(
            "GET", f"/repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=30"
        )
        merged = _require_data(closed, f"recent closed pulls for {repo}")
        snapshot["merged_pulls"][repo] = [
            row for row in (merged or []) if isinstance(merged, list) and row.get("merged_at")
        ] if isinstance(merged, list) else []
        for pull in pulls:
            number = pull.get("number")
            key = f"{repo}#{number}"
            issue_thread = github_request(
                "GET", f"/repos/{repo}/issues/{number}/comments?per_page=100"
            )
            review_thread = github_request(
                "GET", f"/repos/{repo}/pulls/{number}/comments?per_page=100"
            )
            if not issue_thread.get("ok") or not review_thread.get("ok"):
                pull["comments_unavailable"] = True
                snapshot["issue_comments"][key] = []
                snapshot["review_comments"][key] = []
                continue
            snapshot["issue_comments"][key] = issue_thread.get("data") or []
            snapshot["review_comments"][key] = review_thread.get("data") or []

    if snapshot["repo_access"].get(QUEUE_REPO, {}).get("ok") is not False:
        queue = github_request(
            "GET", f"/repos/{QUEUE_REPO}/issues/{QUEUE_ISSUE}/comments?per_page=100"
        )
        data = _require_data(queue, "issue 612 comments")
        if not isinstance(data, list):
            raise GitHubReadError("issue 612 comments were not a list")
        snapshot["queue_comments"] = data
        for repo, number in active_issue_refs(data):
            issue = github_request("GET", f"/repos/{repo}/issues/{number}")
            if not issue.get("ok"):
                continue
            payload = issue.get("data")
            if isinstance(payload, dict):
                snapshot["issues"][f"{repo}#{number}"] = payload

    runs = github_request(
        "GET",
        f"/repos/{CHECK_ALL_REPO}/actions/workflows/check-all.yml/runs?branch=main&per_page=1",
    )
    if not runs.get("ok"):
        if runs.get("status") in {401, 403, 404}:
            snapshot["check_all_runs"][CHECK_ALL_REPO] = {
                "denied": True,
                "status": runs.get("status"),
            }
        else:
            raise GitHubReadError(
                f"check-all runs failed ({runs.get('status')}): {runs.get('error') or 'read error'}"
            )
    elif isinstance(runs.get("data"), dict):
        snapshot["check_all_runs"][CHECK_ALL_REPO] = runs["data"]
    snapshot["fetched_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Office 2.0 board")
    parser.add_argument("--fixture", type=Path, help="recorded API JSON, offline")
    parser.add_argument(
        "--write",
        action="store_true",
        help="write latest.md and latest.json (gitignored by default; never a committed live snapshot)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="directory for latest.md and latest.json (default: docs/office-v2/board)",
    )
    parser.add_argument(
        "--omit-private",
        action="store_true",
        help="drop private repository rows, URLs, and titles before writing",
    )
    parser.add_argument("--now", help="override clock as ISO-8601 (tests)")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    if args.now:
        now = parse_time(args.now)
        if now is None:
            print("FAIL office-v2-mvp: --now is not ISO-8601", file=sys.stderr)
            return 2
    else:
        now = None
    if args.fixture:
        snapshot = json.loads(args.fixture.read_text(encoding="utf-8"))
    else:
        snapshot = fetch_snapshot()
    # The live readback records fetched_at at the END of GitHub GETs.
    # Capture as_of afterward, or every successful read appears to be
    # in the future and the published Health remains UNKNOWN.
    if now is None:
        now = datetime.now(timezone.utc)
    board = build_board(snapshot, now)
    if args.write:
        md_path, json_path = write_board(
            board, args.root, dest=args.out, omit_private=args.omit_private
        )

        def _shown(path: Path) -> str:
            try:
                return str(path.resolve().relative_to(args.root.resolve()))
            except ValueError:
                return str(path)

        print(f"OK office-v2-mvp wrote {_shown(md_path)} {_shown(json_path)}")
    else:
        sys.stdout.write(render_markdown(board))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
