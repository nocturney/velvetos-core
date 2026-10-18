#!/usr/bin/env python3
"""Offline fixture tests for the Office 2.0 desk. No network."""
from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "scripts" / "fixtures" / "office_v2_mvp" / "api.json"
NOW = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "office_v2_mvp", ROOT / "scripts" / "office_v2_mvp.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MVP = load_module()


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def keys(rows: list[dict]) -> set[tuple]:
    found = set()
    for row in rows:
        found.add((row.get("kind"), row.get("repo"), row.get("number"), row.get("claim_key"), row.get("agent")))
    return found


class OfficeV2MvpFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        self.board = MVP.build_board(load_fixture(), NOW)
        self.sections = self.board["sections"]

    def test_sections_and_timezone(self) -> None:
        self.assertEqual(self.board["timezone"], "Asia/Jerusalem")
        self.assertEqual(self.board["generated_at_jerusalem"], "2026-10-18 15:00 Asia/Jerusalem")
        self.assertTrue(self.board["read_only"])
        self.assertFalse(self.board["writes_to_github"])
        self.assertFalse(self.board["llm_calls"])
        self.assertEqual(self.board["next_step"]["research_comment_id"], 6249011608)
        self.assertIn("6249011608", self.board["next_step"]["research_comment"])
        for name in ("waiting_on_christian", "waiting_on_qa", "in_progress", "blocked", "done_today"):
            self.assertIn(name, self.sections)
        for agent in ("cursor", "chatgpt", "claude", "gemini", "auditor"):
            self.assertIn(agent, self.sections["in_progress"])

    def test_pull_request_routing(self) -> None:
        progress = self.sections["in_progress"]
        self.assertEqual(
            keys(progress["cursor"]),
            {
                ("pull_request", "nocturney/velvetos-core", 10, None, "cursor"),
                ("claim", "nocturney/velvetos-core", 612, "nocturney/velvetos-core#700", "cursor"),
            },
        )
        self.assertTrue(progress["cursor"][0]["draft"])
        self.assertEqual(progress["cursor"][0]["head_sha"], "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        waiting_qa = keys(self.sections["waiting_on_qa"])
        self.assertIn(("pull_request", "nocturney/velvetos-core", 11, None, "claude"), waiting_qa)
        self.assertIn(("pull_request", "nocturney/velvetos-core", 13, None, "gemini"), waiting_qa)
        self.assertNotIn(("pull_request", "nocturney/velvetos-core", 10, None, "cursor"), waiting_qa)
        blocked = keys(self.sections["blocked"])
        self.assertIn(("pull_request", "nocturney/velvetos-core", 12, None, "chatgpt"), blocked)
        christian = keys(self.sections["waiting_on_christian"])
        self.assertIn(("pull_request", "nocturney/velvetos-core", 14, None, "auditor"), christian)
        self.assertEqual(
            progress["gemini"][0]["repo"],
            "nocturney/velvetos-velvet-factory",
        )
        self.assertEqual(keys(progress["unassigned"]), {
            ("pull_request", "nocturney/velvetos-velvet-factory", 4, None, None)
        })

    def test_queue_and_open_issues(self) -> None:
        done = self.sections["done_today"]
        done_keys = keys(done)
        self.assertIn(("claim", "nocturney/velvetos-core", 612, "CLQ-1", "cursor"), done_keys)
        self.assertIn(("pull_request", "nocturney/velvetos-core", 9, None, "cursor"), done_keys)
        self.assertNotIn(("pull_request", "nocturney/velvetos-core", 8, None, "cursor"), done_keys)
        clq1 = next(row for row in done if row.get("claim_key") == "CLQ-1")
        self.assertEqual(clq1["when_jerusalem"], "2026-10-18 01:30 Asia/Jerusalem")
        self.assertFalse(any(row.get("claim_key") == "CLQ-8" for row in done))
        claude = self.sections["in_progress"]["claude"]
        clq2 = next(row for row in claude if row.get("claim_key") == "CLQ-2")
        self.assertEqual([issue["number"] for issue in clq2["open_issues"]], [595])
        follow = next(row for row in self.sections["in_progress"]["cursor"] if row.get("claim_key"))
        self.assertEqual(follow["open_issues"], [])
        blocked = self.sections["blocked"]
        self.assertTrue(any(row.get("claim_key") == "CP099" and row.get("agent") == "chatgpt" for row in blocked))
        christian = self.sections["waiting_on_christian"]
        owner = next(row for row in christian if row.get("claim_key"))
        self.assertEqual(owner["agent"], "auditor")
        self.assertEqual([issue["number"] for issue in owner["open_issues"]], [604])

    def test_check_all_failure_is_blocked(self) -> None:
        snap = load_fixture()
        snap["check_all_runs"]["nocturney/velvetos-core"]["workflow_runs"][0]["conclusion"] = "failure"
        board = MVP.build_board(snap, NOW)
        runs = [row for row in board["sections"]["blocked"] if row["kind"] == "workflow_run"]
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["head_sha"], "fcd92ba4dc8892130e48f8bdf46acddd84d3ff2c")

    def test_denied_repo_invents_nothing(self) -> None:
        snap = load_fixture()
        snap["repo_access"]["nocturney/velvetos-velvet-factory"] = {"ok": False, "status": 403}
        board = MVP.build_board(snap, NOW)
        blob = json.dumps(board["sections"])
        self.assertNotIn("velvetos-velvet-factory", blob)
        text = MVP.render_markdown(board)
        self.assertIn("denied (HTTP 403)", text)
        self.assertIn("No rows invented", text)

    def test_scope_text_is_not_an_owner_wait(self) -> None:
        snap = load_fixture()
        snap["queue_comments"].append(
            {
                "id": 201,
                "body": (
                    "Cursor: CLAIM — office desk\n\n"
                    "The board has a section for items waiting on Christian."
                ),
                "created_at": "2026-10-18T11:00:00Z",
                "html_url": "https://github.com/nocturney/velvetos-core/issues/612#issuecomment-201",
            }
        )
        snap["pulls"]["nocturney/velvetos-core"].append(
            {
                "number": 15,
                "title": "Cursor: describe the desk",
                "body": "This pull request mentions waiting on Christian in the scope only.",
                "draft": False,
                "state": "open",
                "html_url": "https://github.com/nocturney/velvetos-core/pull/15",
                "updated_at": "2026-10-18T11:40:00Z",
                "head": {"sha": "2222222222222222222222222222222222222222"},
            }
        )
        board = MVP.build_board(snap, NOW)
        christian = board["sections"]["waiting_on_christian"]
        self.assertFalse(any(row.get("number") == 15 for row in christian))
        self.assertFalse(any("office desk" in (row.get("title") or "") for row in christian))
        self.assertTrue(
            any("office desk" in (row.get("title") or "") for row in board["sections"]["in_progress"]["cursor"])
        )

    def test_secret_is_redacted(self) -> None:
        snap = load_fixture()
        token = "ghp_" + ("a" * 36)
        snap["queue_comments"].append(
            {
                "id": 200,
                "body": f"Claude: CLAIM leak {token}",
                "created_at": "2026-10-18T06:00:00Z",
                "html_url": "https://github.com/nocturney/velvetos-core/issues/612#issuecomment-200",
            }
        )
        board = MVP.build_board(snap, NOW)
        rendered = MVP.render_markdown(board) + MVP.render_json(board)
        self.assertNotIn(token, rendered)
        self.assertIn("[redacted]", rendered)

    def test_markdown_has_bilingual_sections(self) -> None:
        text = MVP.render_markdown(self.board)
        for heading in (
            "מחכה לכריסטיאן · Waiting on Christian",
            "מחכה ל-QA · Waiting on QA",
            "בעבודה · In progress",
            "חסום · Blocked",
            "הושלם היום · Done today",
        ):
            self.assertIn(heading, text)
        self.assertIn("head `bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`", text)
        self.assertIn("QA please", text)
        self.assertIn("QA verdict", text)
        self.assertIn("חותמות מעבדה · Sealed labs", text)
        self.assertTrue(MVP.sealed_lab_text_ok(text))

    def test_lostack_seal_stays_red(self) -> None:
        row = self.board["sealed_labs"][0]
        self.assertEqual(row["label"], "SEALED_RED_ONLY")
        self.assertEqual(row["security_admission"], "RED")
        self.assertEqual(row["url"], MVP.LOSTACK_URL)
        self.assertEqual(row["hosts"], ["MacMiniOffice.local", "Mac-Bedroom.local"])
        promoted = dict(row)
        promoted["security_admission"] = "GREEN"
        promoted["status"] = MVP.LOSTACK_STATUS
        promoted["remote_github_writes"] = 0
        promoted["real_native_git_sqlite_receipts"] = 2
        promoted["distinct_hosts"] = 2
        self.assertIsNone(MVP.seal_row_from_result(promoted))
        self.assertFalse(MVP.sealed_lab_text_ok(MVP.render_markdown(self.board).replace(MVP.LOSTACK_URL, "")))

    def test_post_never_calls_runner(self) -> None:
        def boom(_path: str):
            raise AssertionError("runner was called")

        with self.assertRaises(MVP.ReadOnlyViolation):
            MVP.github_request("POST", "/repos/nocturney/velvetos-core/issues/1/comments", runner=boom)
        with self.assertRaises(MVP.ReadOnlyViolation):
            MVP.github_request("GET", "/repos/nocturney/velvetos-core/pulls/1/merge", runner=boom)

    def test_denied_check_all_is_not_no_run(self) -> None:
        snap = load_fixture()
        snap["check_all_runs"]["nocturney/velvetos-core"] = {"denied": True, "status": 403}
        board = MVP.build_board(snap, NOW)
        text = MVP.render_markdown(board)
        self.assertIn("check-all on main: denied (HTTP 403)", text)
        self.assertNotIn("no run", text)

    def test_active_issue_refs_skip_done_and_older_comments(self) -> None:
        comments = [
            {
                "body": "Cursor: CLAIM old work\n#111",
                "created_at": "2026-10-17T00:00:00Z",
            },
            {
                "body": "Cursor: CLAIM CLQ-9\n#222",
                "created_at": "2026-10-18T00:00:00Z",
            },
            {
                "body": "Cursor: DONE CLQ-9\n#333",
                "created_at": "2026-10-18T01:00:00Z",
            },
            {
                "body": "Claude: CLAIM CLQ-2\nsee #595",
                "created_at": "2026-10-18T02:00:00Z",
            },
        ]
        self.assertEqual(
            MVP.active_issue_refs(comments),
            [
                ("nocturney/velvetos-core", 111),
                ("nocturney/velvetos-core", 595),
            ],
        )

    def test_private_board_leak_mutation(self) -> None:
        clean = "core#10 synthetic desk row"
        self.assertFalse(MVP.board_text_leaks_private(clean))
        mutated = (
            clean
            + "\nhttps://github.com/nocturney/velvetos-velvet-factory/pull/1"
            + " — synthetic private title\n"
        )
        self.assertTrue(MVP.board_text_leaks_private(mutated))
        self.assertTrue(
            MVP.board_text_leaks_private(
                "- velvetos-velvet-factory#1 · draft — synthetic private title\n"
            )
        )
        sample = ROOT / "docs" / "office-v2" / "board" / "SAMPLE.md"
        committed = sample.read_text(encoding="utf-8")
        self.assertFalse(MVP.board_text_leaks_private(committed))
        self.assertTrue(MVP.board_text_leaks_private(committed + "\n" + mutated))

    def test_tracked_or_public_write_drops_factory_rows(self) -> None:
        self.assertIn("velvetos-velvet-factory", json.dumps(self.board))
        public = MVP.omit_private_rows(self.board)
        rendered = MVP.render_markdown(public) + MVP.render_json(public)
        self.assertFalse(MVP.board_text_leaks_private(rendered))
        self.assertIn("Private repository rows are omitted", rendered)
        self.assertIn("velvetos-core", rendered)
        outside = Path(tempfile.mkdtemp())
        try:
            md_path, json_path = MVP.write_board(self.board, ROOT, dest=outside, omit_private=True)
            blob = md_path.read_text(encoding="utf-8") + json_path.read_text(encoding="utf-8")
            self.assertFalse(MVP.board_text_leaks_private(blob))
        finally:
            shutil.rmtree(outside)
        self.assertFalse(MVP.private_rows_allowed([ROOT / "README.md"], ROOT))

    def test_gitignored_local_board_can_keep_factory_rows(self) -> None:
        latest_md = ROOT / "docs" / "office-v2" / "board" / "latest.md"
        latest_json = ROOT / "docs" / "office-v2" / "board" / "latest.json"
        self.assertTrue(MVP.private_rows_allowed([latest_md, latest_json], ROOT))
        try:
            md_path, json_path = MVP.write_board(self.board, ROOT)
            blob = md_path.read_text(encoding="utf-8") + json_path.read_text(encoding="utf-8")
            self.assertTrue(MVP.board_text_leaks_private(blob))
            self.assertIn("portal draft", blob)
        finally:
            latest_md.unlink(missing_ok=True)
            latest_json.unlink(missing_ok=True)

    def test_source_is_read_only_and_lockfile_plain(self) -> None:
        source = (ROOT / "scripts" / "office_v2_mvp.py").read_text(encoding="utf-8")
        for forbidden in ("gh pr create", "gh pr merge", "gh issue create", "--method POST", "import crewai", "import langgraph"):
            self.assertNotIn(forbidden, source)
        self.assertIn("6249011608", source)
        locks = [
            ROOT / "requirements-sensors.txt",
            ROOT / "requirements-sensors.py311.lock",
            ROOT / "requirements-sensors.py312.lock",
        ]
        blob = "\n".join(path.read_text(encoding="utf-8").lower() for path in locks)
        self.assertNotIn("crewai", blob)
        self.assertNotIn("langgraph", blob)


if __name__ == "__main__":
    unittest.main()
