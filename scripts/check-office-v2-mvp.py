#!/usr/bin/env python3
"""Sensor: Office 2.0 read-only desk stays offline, fixture-tested, and manual-dispatch only."""
from __future__ import annotations

import importlib.util
import re
import subprocess
import sys

import vf_subprocess_hygiene as hygiene
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "office_v2_mvp.py"
TEST = ROOT / "scripts" / "test_office_v2_mvp.py"
FIXTURE = ROOT / "scripts" / "fixtures" / "office_v2_mvp" / "api.json"
NEXT = ROOT / "docs" / "office-v2" / "NEXT.md"
WORKFLOW = ROOT / ".github" / "workflows" / "office-v2-board.yml"
LOCKS = (
    ROOT / "requirements-sensors.txt",
    ROOT / "requirements-sensors.py311.lock",
    ROOT / "requirements-sensors.py312.lock",
)


def fail(message: str) -> None:
    print(f"FAIL office-v2-mvp: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_mvp():
    spec = importlib.util.spec_from_file_location("office_v2_mvp_sensor", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git_ok(args: list[str]) -> bool:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    return proc.returncode == 0


def publishable_board_files() -> list[Path]:
    """Tracked board files, plus any board file that is not gitignored."""
    folder = ROOT / "docs" / "office-v2" / "board"
    found: list[Path] = []
    if not folder.is_dir():
        return found
    for path in sorted(folder.iterdir()):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        tracked = _git_ok(["ls-files", "--error-unmatch", "--", rel])
        ignored = _git_ok(["check-ignore", "--no-index", "-q", "--", rel])
        if tracked or not ignored:
            found.append(path)
    return found


def prove_spawn_hygiene(mvp) -> None:
    with hygiene.record_pinned_spawn("gh") as (calls, short):
        row = mvp._gh_get("/repos/nocturney/velvetos-core")
    hygiene.expect_pinned(calls, short, timeout=90, keep_gh_token=True)
    if not row.get("ok"):
        fail("pinned gh read did not parse")
    try:
        mvp._gh_get("-evil")
    except mvp.GitHubReadError as exc:
        if "dash" not in str(exc):
            fail("dash path refusal changed: " + str(exc))
    else:
        fail("a GitHub path that starts with a dash was accepted")
    with hygiene.record_pinned_spawn("git") as (calls, short):
        mvp._git(["status"], ROOT)
    hygiene.expect_pinned(calls, short, timeout=30, keep_gh_token=False)


def main() -> int:
    for path in (SCRIPT, TEST, FIXTURE, NEXT, WORKFLOW):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")
    source = SCRIPT.read_text(encoding="utf-8")
    for forbidden in (
        "gh pr create",
        "gh pr merge",
        "gh issue create",
        "--method POST",
        "import crewai",
        "import langgraph",
    ):
        if forbidden in source:
            fail(f"script contains forbidden text: {forbidden}")
    if "6249011608" not in source or "Asia/Jerusalem" not in source:
        fail("script missing research comment or Jerusalem clock")
    if "--method\", \"GET\"" not in source and '"GET"' not in source:
        fail("script does not pin GitHub reads to GET")
    next_doc = NEXT.read_text(encoding="utf-8")
    if "6249011608" not in next_doc:
        fail("next-step doc missing verified research comment 6249011608")
    lock_blob = "\n".join(path.read_text(encoding="utf-8").lower() for path in LOCKS)
    if "crewai" in lock_blob or "langgraph" in lock_blob:
        fail("lockfile now contains an agent framework; update the desk admission before importing it")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    if "workflow_dispatch:" not in workflow:
        fail("workflow is not manual-dispatch")
    if re.search(r"(?m)^\s*schedule:\s*$", workflow) or "cron:" in workflow:
        fail("workflow must not schedule; ChatGPT automations own the clock")
    if re.search(r"(?m)^\s*contents:\s*write\s*$", workflow):
        fail("workflow must not request contents: write")
    if "contents: read" not in workflow:
        fail("workflow missing contents: read")
    for needle in ("office_v2_mvp.py", "actions/upload-artifact@", "persist-credentials: false"):
        if needle not in workflow:
            fail(f"workflow missing {needle}")
    if "git push" in workflow or "gh pr" in workflow or "git add" in workflow:
        fail("workflow must not write to GitHub")
    if "--omit-private" not in workflow:
        fail("workflow must omit private repository rows before upload")
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    for line in ("docs/office-v2/board/latest.md", "docs/office-v2/board/latest.json"):
        if line not in ignore:
            fail(f"gitignore missing {line}")
    for live in ("docs/office-v2/board/latest.md", "docs/office-v2/board/latest.json"):
        if _git_ok(["ls-files", "--error-unmatch", "--", live]):
            fail(f"live board is tracked: {live}")
    sample = ROOT / "docs" / "office-v2" / "board" / "SAMPLE.md"
    if not sample.is_file():
        fail("committed fixture sample board is missing")
    mvp = load_mvp()
    probe = (
        "https://github.com/nocturney/velvetos-velvet-factory/pull/1"
        " — synthetic private title"
    )
    if mvp.board_text_leaks_private("core#10 synthetic desk row"):
        fail("private-board check false-positived a synthetic public row")
    if not mvp.board_text_leaks_private(probe):
        fail("mutation probe with a private factory URL was not detected")
    boards = publishable_board_files()
    if not boards:
        fail("committed fixture sample board is missing")
    for path in boards:
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT).as_posix()
        if mvp.board_text_leaks_private(text):
            fail(f"committed board contains private factory rows: {rel}")
        if not mvp.board_text_leaks_private(text + "\n" + probe):
            fail(f"mutating {rel} with a private factory URL was not detected")
    board = mvp.build_board({}, datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc))
    text = mvp.render_markdown(board)
    if not mvp.sealed_lab_text_ok(text):
        fail("board does not show CP083 lost-ACK receipts as SEALED_RED_ONLY with a link")
    if mvp.sealed_lab_text_ok(text.replace("SEALED_RED_ONLY", "ADMITTED")):
        fail("mutation: a promoted seal label was accepted")
    if mvp.sealed_lab_text_ok(text.replace(mvp.LOSTACK_URL, "")):
        fail("mutation: a seal without the evidence link was accepted")
    if mvp.sealed_lab_text_ok(text.replace("security_admission=RED", "security_admission=GREEN")):
        fail("mutation: GREEN admission was accepted on the board")
    gate_result = {
        "security_admission": "RED",
        "status": mvp.LOSTACK_STATUS,
        "remote_github_writes": 0,
        "real_native_git_sqlite_receipts": 2,
        "distinct_hosts": 2,
    }
    if mvp.seal_row_from_result(gate_result) is None:
        fail("RED lost-ACK gate result did not become a board row")
    false_writes = dict(gate_result)
    false_writes["remote_github_writes"] = False
    if mvp.seal_row_from_result(false_writes) is not None:
        fail("mutation: bool False counted as zero remote_github_writes")
    one_write = dict(gate_result)
    one_write["remote_github_writes"] = 1
    if mvp.seal_row_from_result(one_write) is not None:
        fail("mutation: remote_github_writes 1 became a board row")
    gate_result["security_admission"] = "GREEN"
    if mvp.seal_row_from_result(gate_result) is not None:
        fail("mutation: a GREEN gate result became a board row")
    missing = ROOT / "docs" / "implementation" / "office-v2" / "phase2" / "missing-lostack-evidence.json"
    missing_view = mvp.cp083_lostack_view(evidence_path=missing)
    if missing_view.get("status") != "EVIDENCE_MISSING" or missing_view.get("row"):
        fail("mutation: missing evidence did not drop the row as EVIDENCE_MISSING")
    with tempfile.TemporaryDirectory() as tmp:
        bad = Path(tmp) / "corrupt.json"
        bad.write_text("{", encoding="utf-8")
        corrupt_view = mvp.cp083_lostack_view(evidence_path=bad)
    if corrupt_view.get("status") != "EVIDENCE_MISSING" or corrupt_view.get("row"):
        fail("mutation: corrupt evidence did not drop the row as EVIDENCE_MISSING")
    original_view = mvp.cp083_lostack_view

    def _missing_view(evidence_path=None):
        return {"status": "EVIDENCE_MISSING"}

    mvp.cp083_lostack_view = _missing_view
    try:
        broken = mvp.build_board({}, datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc))
        broken_text = mvp.render_markdown(broken)
    finally:
        mvp.cp083_lostack_view = original_view
    if "EVIDENCE_MISSING" not in broken_text or "SEALED_RED_ONLY" in broken_text:
        fail("mutation: missing evidence crashed the board or kept a sealed row")
    if "מחכה לכריסטיאן" not in broken_text:
        fail("mutation: missing evidence dropped sections other than the seal row")
    evidence = mvp._load_lostack_gate().EVIDENCE
    evidence_before = evidence.read_bytes()
    original_loader = mvp._load_lostack_gate

    def _gate_import_failed():
        raise ImportError("lost-ACK receipt gate missing")

    mvp._load_lostack_gate = _gate_import_failed
    try:
        failed = mvp.cp083_lostack_view()
        failed_board = mvp.build_board({}, datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc))
        failed_text = mvp.render_markdown(failed_board)
    finally:
        mvp._load_lostack_gate = original_loader
    if evidence.read_bytes() != evidence_before:
        fail("gate import mutation touched the CP083 evidence file")
    if failed.get("status") != "GATE_IMPORT_FAILED" or failed.get("row"):
        fail("mutation: gate import failure was not GATE_IMPORT_FAILED")
    if failed.get("status") == "EVIDENCE_MISSING":
        fail("mutation: gate import failure was labeled EVIDENCE_MISSING")
    if "GATE_IMPORT_FAILED" not in failed_text or "SEALED_RED_ONLY" in failed_text:
        fail("mutation: gate import failure kept a sealed row")
    if "EVIDENCE_MISSING" in failed_text:
        fail("mutation: gate import failure was rendered as EVIDENCE_MISSING")
    if "מחכה לכריסטיאן" not in failed_text:
        fail("mutation: gate import failure dropped sections other than the seal row")
    sample_text = sample.read_text(encoding="utf-8")
    if not mvp.sealed_lab_text_ok(sample_text):
        fail("committed sample board is missing the SEALED_RED_ONLY lost-ACK link")
    evidence_for_test = mvp._load_lostack_gate().EVIDENCE
    evidence_bytes = evidence_for_test.read_bytes()
    proc = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=60,
    )
    if evidence_for_test.read_bytes() != evidence_bytes:
        fail("fixture unit test mutated the CP083 evidence file")
    if proc.returncode != 0:
        detail = (proc.stdout + "\n" + proc.stderr).strip()
        fail("fixture unit test failed\n" + detail[-2000:])
    prove_spawn_hygiene(mvp)
    print("OK office-v2-mvp offline fixture read_only=GET schedule=none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
