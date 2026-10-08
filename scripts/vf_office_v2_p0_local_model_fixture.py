#!/usr/bin/env python3
"""Prepare a new, exclusive, synthetic P0 local-model envelope (never executes a model).

No production checkout, credentials, queue, auto-retry, API key, or extra spend.
Invoke the separately vetted local-model worker explicitly after reviewing envelope.
"""
from __future__ import annotations
import argparse
import json
import pathlib
import platform
import subprocess

import vf_office_v2_continuity as continuity
import vf_office_v2_p0_local_model_worker as worker

SOURCE = '''import re

def slugify(value: str) -> str:
    """Lowercase ASCII; collapse punctuation/whitespace to hyphens, strip, default untitled."""
    return value.lower().replace(" ", "-")
'''
TEST = '''import unittest
from slug import slugify

class SlugTests(unittest.TestCase):
    def test_basic(self): self.assertEqual(slugify("Hello   World!!"), "hello-world")
    def test_edges(self): self.assertEqual(slugify(" _ABC_ 42_ "), "abc-42")
    def test_empty(self): self.assertEqual(slugify("!?"), "untitled")
'''
PROMPT = """This is an isolated, synthetic, explicitly approved LAB Python coding task. Fix only slug.py to honor its docstring: lowercase ASCII; replace runs of non-alphanumeric characters with single hyphens, trim leading and trailing hyphens (the actual hyphen character, NOT just whitespace), and return untitled when the final slug is empty. Use read-only tests/test_slug.py as guidance. Do not modify tests, configuration, or anything other than slug.py. Do not execute shell commands. Preserve the slugify(value) signature."""
QA = '''from slug import slugify

cases = [
    ("a  b","a-b"), ("HELLO","hello"), ("!_A_-B!","a-b"),
    ("2026/Oct/08","2026-oct-08"), ("  ","untitled"),
    ("A..B","a-b"), ("A_B","a-b"), ("a---b","a-b"),
    ("mixed Case","mixed-case"), ("!?","untitled"), ("Hi!","hi"), ("42","42")
]
assert len(cases) == 12
for value, expected in cases:
    actual = slugify(value)
    assert actual == expected, (value, expected, actual)
print("QA_HIDDEN_12_PASS")
'''


def git(*cmd, cwd=None):
    p = subprocess.run(["git", *cmd], cwd=cwd, text=True, capture_output=True, timeout=18)
    if p.returncode:
        raise worker.Refuse("LAB_GIT_PREPARE_FAILED")
    return p.stdout.strip()


def make(args):
    if not args.task_id.startswith("p0-") or not worker.TASK_ID.fullmatch(args.task_id):
        raise worker.Refuse("LAB_TASK_ID_REQUIRED")
    root = pathlib.Path(args.lab_root)
    if not root.is_absolute() or "AgentEnvelopeLab" not in root.parts:
        raise worker.Refuse("EXPLICIT_AGENT_ENVELOPE_LAB_ROOT_REQUIRED")
    root = root.resolve()
    destination = root / args.task_id
    if destination.exists():
        raise worker.Refuse("EXCLUSIVE_TASK_DESTINATION_EXISTS")
    if args.model not in worker.MODELS or args.port not in (11555, 11556):
        raise worker.Refuse("LOCAL_MODEL_REQUIRED")
    binary = worker.abs_file(args.aider)
    if binary.name.lower() not in ("aider", "aider.exe"):
        raise worker.Refuse("PINNED_AIDER_REQUIRED")
    model_digest = worker.remote_model_tag(args.model, args.port)
    if not (25 <= args.timeout <= 180):
        raise worker.Refuse("BOUNDED_TIMEOUT_REQUIRED")
    if worker.hashlib.sha256(SOURCE.encode()).hexdigest() != worker.SOURCE_SHA256:
        raise worker.Refuse("SOURCE_FIXTURE_DRIFT")
    if worker.hashlib.sha256(TEST.encode()).hexdigest() != worker.TEST_SHA256:
        raise worker.Refuse("TEST_FIXTURE_DRIFT")
    destination.mkdir(parents=True)
    checkout = (destination / "repo").resolve()
    checkout.mkdir()
    (checkout / "tests").mkdir()
    (checkout / "slug.py").write_bytes(SOURCE.encode())
    (checkout / "tests" / "test_slug.py").write_bytes(TEST.encode())
    branch = "lab-p0-agent-" + args.task_id
    git("init", "-q", "-b", branch, str(checkout))
    git("-C", str(checkout), "config", "core.autocrlf", "false")
    git("-C", str(checkout), "add", "--", "slug.py", "tests/test_slug.py")
    git("-C", str(checkout), "-c", "user.name=LAB Fixture",
        "-c", "user.email=fixture@example.invalid", "commit", "-qm", "P0 local-only synthetic fixture")
    sha = git("-C", str(checkout), "rev-parse", "HEAD")
    if worker.modified(checkout):
        raise worker.Refuse("PREPARED_REPO_NOT_CLEAN")
    prompt = (destination / "task.prompt.txt")
    hidden = (destination / "hidden.qa.py")
    prompt.write_bytes(PROMPT.encode())
    hidden.write_bytes(QA.encode())
    before = continuity.self_test_manifest()
    before["active_external_effects"] = []
    before["code_baseline"] = {
        "repo": "nocturney/velvetos-core", "base_sha": sha, "branch": branch,
        "worktree_path": str(checkout),
    }
    checkpoint = (destination / "checkpoint.json").resolve()
    continuity.write(checkpoint, continuity.seal(before))
    envelope = {
        "schema": worker.SCHEMA, "task_id": args.task_id,
        "authority": worker.AUTHORITY, "issue_url": worker.ISSUE,
        "host": platform.node(), "worktree_path": str(checkout),
        "base_sha": sha, "branch": branch,
        "budget": {"timeout_seconds": args.timeout, "max_attempts": 1, "max_cost_usd": 0},
        "executor": {
            "kind": "LOCAL_AIDER_OLLAMA_SYNTHETIC_V1", "model": args.model,
            "ollama_port": args.port, "model_digest": model_digest,
            "aider_binary": str(binary), "aider_sha256": worker.hash_file(binary),
            "prompt_file": str(prompt.resolve()), "prompt_sha256": worker.hash_file(prompt),
            "hidden_qa_file": str(hidden.resolve()),
            "hidden_qa_sha256": worker.hash_file(hidden),
        },
        "context_checkpoint": str(checkpoint),
    }
    # Entire model+authority+checkpoint validation happens BEFORE any invocation.
    worker.preflight(envelope)
    file = destination / "envelope.json"
    worker.save_new(file, envelope)
    return {
        "status": "PREPARED_ONLY_NO_MODEL_RUN", "task_id": args.task_id,
        "host": platform.node(), "base_sha": sha, "model": args.model,
        "model_digest": model_digest, "source_sha256": worker.SOURCE_SHA256,
        "tests_sha256": worker.TEST_SHA256,
        "hidden_sha256": worker.hash_file(hidden),
        "envelope": str(file), "receipt": str(destination / "output" / "receipt.json"),
        "model_invocations": 0, "production_authority": "NONE",
    }


def main():
    p = argparse.ArgumentParser(description="Prepare pinned synthetic Aider/Ollama LAB task")
    p.add_argument("--lab-root", required=True)
    p.add_argument("--task-id", required=True)
    p.add_argument("--aider", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--timeout", type=int, default=170)
    args = p.parse_args()
    print(json.dumps(make(args), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (worker.Refuse, ValueError, OSError, RuntimeError, KeyError, AssertionError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)[:180]}))
        raise SystemExit(2)
