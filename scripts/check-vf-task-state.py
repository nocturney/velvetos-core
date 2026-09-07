#!/usr/bin/env python3
"""Behavioral sensor for the read-only task-state report. Temporary fixtures only.

The suite gates the reader and its owned checkpoint. Historical records are
audited separately by vf_task_state.py, whose nonzero exit must be reported.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import vf_task_state as state

ROOT = Path(__file__).resolve().parents[1]


class TaskStateTests(unittest.TestCase):
    def test_ladder_logs_are_observed_separately_and_never_complete_tasks(self) -> None:
        self.write()
        log = self.directory / "ladder-test.json"
        log.write_text(json.dumps([
            {"rung": "retry_as_is", "attempt": 1, "ok": False, "ts": "2026-09-07T11:00:00+00:00"},
            {"rung": "downgrade_scope", "ok": True, "ts": "2026-09-07T11:01:00+00:00"},
        ]), encoding="utf-8")
        report = state.audit(self.root)
        self.assertEqual(report["summary"]["records_total"], 2)
        self.assertEqual(report["summary"]["total"], 1)
        self.assertEqual(report["summary"]["event_logs"], 1)
        self.assertEqual(report["summary"]["event_logs_invalid"], 0)
        self.assertNotIn("completion", report["event_logs"][0])
        self.assertEqual(self.cli(str(log)).returncode, 0)
        self.assertEqual(self.cli(str(log), "--require-verified").returncode, 1)

    def test_malformed_ladder_log_is_reported_instead_of_ignored(self) -> None:
        log = self.directory / "ladder-bad.json"
        log.write_text('[{"rung":"unknown","ok":"true"}]', encoding="utf-8")
        report = state.audit(self.root)
        self.assertEqual(report["summary"]["event_logs_invalid"], 1)
        self.assertGreaterEqual(len(report["event_logs"][0]["event_errors"]), 2)
        self.assertEqual(self.cli().returncode, 1)

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        schema_path = self.root / state.SCHEMA_PATH
        schema_path.parent.mkdir(parents=True)
        schema_path.write_bytes((ROOT / state.SCHEMA_PATH).read_bytes())
        self.schema = json.loads(schema_path.read_text(encoding="utf-8"))
        state.check_schema(self.schema)
        self.directory = self.root / state.STATE_PATH
        self.directory.mkdir(parents=True)
        self.path = self.directory / "task.json"
        self.artifact = self.root / "out" / "result.txt"
        self.artifact.parent.mkdir()
        self.artifact.write_text("תוצר שנבדק\n", encoding="utf-8")
        self.record = {
            "task_id": "test-task", "status": "done", "pack": "vfharness",
            "completed_steps": ["produce result"], "next_step": "",
            "artifacts": ["out/result.txt"], "unresolved": [],
            "last_updated": "2026-09-07", "verification": "local fixture reviewed",
            "execution_state": {"artifact_evidence": {"out/result.txt": {
                "sha256": hashlib.sha256(self.artifact.read_bytes()).hexdigest(),
            }}},
        }

    def write(self) -> None:
        self.path.write_text(json.dumps(self.record, ensure_ascii=False), encoding="utf-8")

    def inspect(self) -> dict:
        self.write()
        return state.inspect_checkpoint(self.path, self.root, self.schema)

    def cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/vf_task_state.py"), "--root", str(self.root), *args],
            capture_output=True, text=True, timeout=15,
        )

    def test_matching_digest_verifies_bytes_with_source_provenance(self) -> None:
        row = self.inspect()
        self.assertEqual(row["completion"], "local_artifacts_verified")
        self.assertEqual(row["source"], str(state.STATE_PATH / "task.json"))
        self.assertEqual(row["source_sha256"], hashlib.sha256(self.path.read_bytes()).hexdigest())
        self.assertEqual(row["artifacts"][0]["status"], "digest_verified")
        self.assertEqual(row["reported_status"], "done")

    def test_changed_artifact_invalidates_previous_evidence(self) -> None:
        self.artifact.write_text("changed", encoding="utf-8")
        row = self.inspect()
        self.assertEqual(row["completion"], "unverified")
        self.assertEqual(row["artifacts"][0]["status"], "digest_mismatch")
        self.assertEqual(self.cli().returncode, 1)

    def test_existence_or_free_text_does_not_prove_completion(self) -> None:
        self.record.pop("execution_state")
        row = self.inspect()
        self.assertEqual(row["artifacts"][0]["status"], "present_unverified")
        self.assertEqual(row["completion"], "unverified")
        self.assertEqual(self.cli().returncode, 0)
        self.assertEqual(self.cli("--require-verified").returncode, 1)

    def test_missing_local_artifact_is_explicit_failure(self) -> None:
        self.artifact.unlink()
        row = self.inspect()
        self.assertEqual(row["artifacts"][0]["status"], "missing")
        self.assertNotEqual(row["completion"], "local_artifacts_verified")
        self.assertEqual(self.cli().returncode, 1)

    def test_remote_and_other_machine_paths_are_unverified_not_missing(self) -> None:
        self.record["artifacts"] = ["https://example.invalid/item", "/opt/other-machine/output.png", r"C:\Grok\output.png", "../outside.txt"]
        self.record.pop("execution_state")
        row = self.inspect()
        self.assertEqual([a["status"] for a in row["artifacts"]], [
            "unverified_external", "unverified_other_environment", "unverified_other_environment", "unverified_other_environment",
        ])
        self.assertEqual(row["completion"], "unverified")
        self.assertEqual(self.cli().returncode, 0)
        self.assertEqual(self.cli("--require-verified").returncode, 1)

    def test_symlink_outside_checkout_and_directory_do_not_verify(self) -> None:
        self.artifact.unlink()
        self.artifact.symlink_to(self.root.parent / "foreign-output.txt")
        self.assertEqual(self.inspect()["artifacts"][0]["status"], "unverified_other_environment")
        self.artifact.unlink()
        self.artifact.mkdir()
        self.assertEqual(self.inspect()["artifacts"][0]["status"], "present_unverified")

    def test_opaque_ids_commands_and_patterns_are_not_missing_local_files(self) -> None:
        self.record["artifacts"] = ["DAHUaelaug0", "packages/vfbriefux/render_mail.py --diagram", "out/*.png"]
        self.record.pop("execution_state")
        row = self.inspect()
        self.assertTrue(all(a["status"] == "unverified_reference" for a in row["artifacts"]))
        self.assertEqual(row["completion"], "unverified")
        self.assertEqual(self.cli().returncode, 0)

    def test_blocked_and_running_are_not_completed_even_with_matching_artifacts(self) -> None:
        for reported, expected in [("blocked", "blocked"), ("escalated", "blocked"), ("running", "not_done")]:
            with self.subTest(reported=reported):
                self.record["status"] = reported
                row = self.inspect()
                self.assertEqual(row["completion"], expected)
                self.assertEqual(row["artifacts"][0]["status"], "digest_verified")

    def test_done_with_blocker_or_unresolved_work_is_inconsistent(self) -> None:
        for key, value in [
            ("gate", {"kind": "approval", "waiting_for": "Cursor"}),
            ("unresolved", ["review pending"]), ("pulse", "blocked"), ("outcome", "decision_gate"),
        ]:
            with self.subTest(key=key):
                record = copy.deepcopy(self.record)
                self.record[key] = value
                row = self.inspect()
                self.assertEqual(row["completion"], "invalid")
                self.assertTrue(row["state_errors"])
                self.record = record

    def test_schema_rejects_legacy_aliases_null_crew_and_unknown_fields(self) -> None:
        for key, value in [("status", "worker_done"), ("crew", None), ("taskId", "legacy-id"), ("artifacts", "not-an-array")]:
            with self.subTest(key=key):
                record = copy.deepcopy(self.record)
                self.record[key] = value
                row = self.inspect()
                self.assertEqual(row["completion"], "invalid")
                self.assertTrue(any(key in error for error in row["schema_errors"]))
                self.record = record

    def test_schema_nested_requirements_lengths_and_additional_properties(self) -> None:
        self.record["events"] = [{"name": "", "extra": True}]
        self.record["planned_steps"] = ["step"] * 9
        row = self.inspect()
        errors = "\n".join(row["schema_errors"])
        for expected in ["events[0].name", "events[0].producedAt", "events[0].extra", "planned_steps"]:
            self.assertIn(expected, errors)

    def test_invalid_json_and_nonobject_records_fail_without_traceback(self) -> None:
        for raw in ['{"status":"done","status":"running"}', '{broken', '[]', '{"x":NaN}', '{"x":1e400}']:
            with self.subTest(raw=raw):
                self.path.write_text(raw, encoding="utf-8")
                row = state.inspect_checkpoint(self.path, self.root, self.schema)
                self.assertEqual(row["completion"], "invalid")
                self.assertTrue(row["schema_errors"])
                result = self.cli()
                self.assertEqual(result.returncode, 1)
                self.assertNotIn("Traceback", result.stderr)

    def test_unknown_schema_keywords_fail_closed(self) -> None:
        self.write()
        self.schema["properties"]["task_id"]["pattern"] = "^approved-"
        (self.root / state.SCHEMA_PATH).write_text(json.dumps(self.schema), encoding="utf-8")
        result = self.cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("unsupported schema keywords", json.loads(result.stdout)["error"])

    def test_bad_and_orphaned_digest_evidence_is_not_accepted(self) -> None:
        for evidence in [{"out/result.txt": {"sha256": "bad"}}, ["not-a-map"], {"other.txt": {"sha256": "a" * 64}}]:
            with self.subTest(evidence=evidence):
                self.record["execution_state"]["artifact_evidence"] = evidence
                row = self.inspect()
                self.assertNotEqual(row["completion"], "local_artifacts_verified")
                self.assertEqual(self.cli().returncode, 1)

    def test_no_artifacts_or_verification_record_does_not_verify(self) -> None:
        self.record.pop("verification")
        self.assertEqual(self.inspect()["completion"], "unverified")
        self.record["artifacts"] = []
        self.record.pop("execution_state")
        self.assertEqual(self.inspect()["completion"], "unverified")

    def test_duplicate_task_ids_and_nested_checkpoints_are_reported(self) -> None:
        self.write()
        nested = self.directory / "nested" / "checkpoint.json"
        nested.parent.mkdir()
        nested.write_bytes(self.path.read_bytes())
        report = state.audit(self.root)
        self.assertEqual(report["summary"]["total"], 2)
        self.assertEqual(report["summary"]["state_invalid"], 2)
        self.assertTrue(all(row["completion"] == "invalid" for row in report["tasks"]))

    def test_cli_selection_exit_codes_and_read_only_operation(self) -> None:
        self.write()
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        result = self.cli(str(state.STATE_PATH / "task.json"), "--require-verified")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["summary"]["total"], 1)
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()})
        self.assertEqual(self.cli("missing-checkpoint.json").returncode, 1)
        self.path.unlink()
        self.assertEqual(self.cli().returncode, 2)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TaskStateTests)
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=1).run(suite)
    if not result.wasSuccessful():
        return 1
    # This owned checkpoint must be compatible. No blanket legacy whitelist.
    report = state.audit(ROOT, [state.STATE_PATH / "swc-codex-001.json"])
    summary = report["summary"]
    if summary["schema_invalid"] or summary["state_invalid"] or summary["artifact_errors"]:
        print(json.dumps(report, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    print(f"OK task-state behavioral tests={result.testsRun}; owned checkpoint valid; historical audit is separate (vf_task_state.py)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
