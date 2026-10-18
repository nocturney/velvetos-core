#!/usr/bin/env python3
"""P0 #612: immutable preparation-only catalog for TWO diverse coding fixtures.

This is NOT another Worker, scheduler, queue, Task Envelope issuer, or model
execution authority. It prepares new distinct canonical-style local Git
checkouts with pinned task inputs for a FUTURE generalized Worker admission.
The existing v1 Worker remains slug.py-only and must NOT run these fixtures.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import vf_office_v2_continuity as continuity

SCHEMA = "velvetos.office-v2.p0-two-diverse-fixtures-candidate.v0"
AUTHORITY = "PREPARATION_ONLY_NOT_A_MODEL_TASK_ENVELOPE"
ISSUE = "https://github.com/nocturney/velvetos-core/issues/612"
ID = re.compile(r"p0-diverse-[A-Za-z0-9_.-]{4,96}\Z")
BRANCH = "lab-p0-diverse-"
EXTERNAL_EFFECTS = 0

TAG_SOURCE = '''def canonical_tag(text: str) -> str:
    """ASCII lowercase alphanumerics, single underscore separators, default untitled."""
    return text.strip().lower().replace(" ", "_")
'''
TAG_TESTS = '''import unittest
from canonical_tag import canonical_tag

class TagTests(unittest.TestCase):
    def test_punctuation(self): self.assertEqual(canonical_tag("Mixed Name!"), "mixed_name")
    def test_collapse(self): self.assertEqual(canonical_tag("a__b"), "a_b")
    def test_empty(self): self.assertEqual(canonical_tag("!!!"), "untitled")
'''
TAG_PROMPT = '''A synthetic preparation-only coding task. In canonical_tag.py implement canonical_tag(text: str): lower ASCII a-z digits 0-9, replace each run of every other character by ONE underscore, remove leading/trailing underscores, and return "untitled" if nothing remains. Preserve the function name and signature. Do not modify or run tests, execute commands, access other code, or modify any file except canonical_tag.py.'''
TAG_HIDDEN = '''from canonical_tag import canonical_tag
cases = [
    ("Hello-World", "hello_world"), ("a...b", "a_b"),
    ("a___b", "a_b"), ("X/Y/Z", "x_y_z"), ("_a_", "a"),
    ("ONE TWO", "one_two"), ("42", "42"), ("A9", "a9"),
    ("", "untitled"), ("  ", "untitled"), ("A😀B", "a_b"),
    ("2026/10/09", "2026_10_09")
]
assert len(cases) == 12
for original, expected in cases:
    actual = canonical_tag(original)
    assert actual == expected, (original, expected, actual)
print("QA_HIDDEN_12_PASS")
'''
TAG_GOLD = '''import re

def canonical_tag(text: str) -> str:
    """ASCII lowercase alphanumerics, single underscore separators, default untitled."""
    cleaned = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return cleaned or "untitled"
'''

INTERVAL_SOURCE = '''def merge_windows(windows: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge sorted/unsorted overlapping or touching inclusive integer intervals."""
    return sorted(windows)
'''
INTERVAL_TESTS = '''import unittest
from windows_merge import merge_windows

class WindowTests(unittest.TestCase):
    def test_overlap(self):
        self.assertEqual(merge_windows([(1,3),(2,6)]), [(1,6)])
    def test_touching(self):
        self.assertEqual(merge_windows([(4,5),(1,3)]), [(1,5)])
    def test_invalid(self):
        with self.assertRaises(ValueError): merge_windows([(4,2)])
'''
INTERVAL_PROMPT = '''A synthetic preparation-only coding task. In windows_merge.py implement merge_windows(windows): input is a list of (start,end) tuples representing inclusive integer intervals. Reject malformed pairs, bool/non-int endpoints and reversed intervals by raising ValueError. Sort, merge overlapping OR directly adjacent integer intervals, return a NEW list of tuple pairs. Empty input returns []. Do not modify tests or other files, run shell commands or use network. Preserve function signature.'''
INTERVAL_HIDDEN = '''from windows_merge import merge_windows
good = [
    ([], []), ([(1,2)], [(1,2)]),
    ([(1,2),(3,4)], [(1,4)]),
    ([(1,2),(4,5)], [(1,2),(4,5)]),
    ([(-3,-1),(0,0)], [(-3,0)]),
    ([(9,10),(1,5),(4,9)], [(1,10)]),
    ([(4,4),(4,4)], [(4,4)]),
    ([(0,0),(-2,-2)], [(-2,-2),(0,0)]),
]
bad = [[(2,1)], [(True,2)], [(1,3.5)], [[1,2]]]
assert len(good) + len(bad) == 12
for value, expected in good:
    result = merge_windows(value)
    assert result == expected, (value, expected, result)
for value in bad:
    try:
        merge_windows(value)
    except ValueError:
        pass
    else:
        raise AssertionError(("EXPECTED_VALUE_ERROR", value))
print("QA_HIDDEN_12_PASS")
'''
INTERVAL_GOLD = '''def merge_windows(windows: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge sorted/unsorted overlapping or touching inclusive integer intervals."""
    validated = []
    for pair in windows:
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise ValueError("pair must be a tuple of 2 integers")
        lo, hi = pair
        if type(lo) is not int or type(hi) is not int or lo > hi:
            raise ValueError("invalid interval")
        validated.append((lo, hi))
    result = []
    for lo, hi in sorted(validated):
        if result and lo <= result[-1][1] + 1:
            result[-1] = (result[-1][0], max(result[-1][1], hi))
        else:
            result.append((lo, hi))
    return result
'''


def catalog():
    return {
        "canonical-tag-v1": {
            "target": "canonical_tag.py",
            "test": "tests/test_canonical_tag.py",
            "source": TAG_SOURCE,
            "visible": TAG_TESTS,
            "hidden": TAG_HIDDEN,
            "prompt": TAG_PROMPT,
            "golden": TAG_GOLD,
        },
        "merge-windows-v1": {
            "target": "windows_merge.py",
            "test": "tests/test_windows_merge.py",
            "source": INTERVAL_SOURCE,
            "visible": INTERVAL_TESTS,
            "hidden": INTERVAL_HIDDEN,
            "prompt": INTERVAL_PROMPT,
            "golden": INTERVAL_GOLD,
        },
    }


class Refused(Exception):
    pass


def require(ok, why):
    if not ok:
        raise Refused(why)


def sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canon(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False,
                        sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def git(*cmd):
    try:
        p = subprocess.run(["git", *cmd], text=True, capture_output=True,
                           timeout=18, encoding="utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired):
        raise Refused("GIT_PREPARE_UNAVAILABLE")
    require(p.returncode == 0, "GIT_PREPARE_FAILED")
    return p.stdout.strip()


def check_fixture(id_, row):
    require(id_ in ("canonical-tag-v1", "merge-windows-v1"),
            "UNREGISTERED_TASK_VARIANT")
    require(isinstance(row, dict) and set(row) ==
            {"target", "test", "source", "visible", "hidden", "prompt", "golden"},
            "VARIANT_ENTRY_DRIFT")
    require(row["target"] in ("canonical_tag.py", "windows_merge.py")
            and row["test"] in ("tests/test_canonical_tag.py",
                                "tests/test_windows_merge.py")
            and "PYTHON" not in row["target"]
            and len(row["source"]) < 1800
            and 80 < len(row["prompt"]) < 1000
            and "QA_HIDDEN_12_PASS" in row["hidden"]
            and row["source"] != row["golden"], "UNSAFE_OR_ALREADY_SOLVED_FIXTURE")
    return True


def replay(row, source, expected_pass):
    with tempfile.TemporaryDirectory(prefix="vf-office-p0-diverse-qa-") as td:
        root = Path(td)
        target = root / row["target"]
        test = root / row["test"]
        test.parent.mkdir()
        target.write_text(source, encoding="utf-8")
        test.write_text(row["visible"], encoding="utf-8")
        env = {key: os.environ[key] for key in
               ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "TMPDIR")
               if key in os.environ}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        try:
            unit = subprocess.run(
                [sys.executable, "-B", "-m", "unittest", "discover",
                 "-s", "tests", "-q"], cwd=root, env=env,
                capture_output=True, timeout=15)
            hidden = subprocess.run(
                [sys.executable, "-B", "-c", row["hidden"]], cwd=root,
                env=env, capture_output=True, timeout=15)
        except (OSError, subprocess.TimeoutExpired):
            raise Refused("QA_PROCESS_UNAVAILABLE")
        summary = unit.stderr.decode("utf-8", "replace")
        good = (unit.returncode == 0 and hidden.returncode == 0 and
                "Ran 3 tests" in summary and
                hidden.stdout.strip() == b"QA_HIDDEN_12_PASS")
        require(good is expected_pass, "GOLDEN_OR_SEED_QA_UNEXPECTED")
        return {"pass": good, "unit_exit": unit.returncode,
                "hidden_exit": hidden.returncode,
                "source_sha256": sha(source)}


def inspect():
    variants = catalog()
    require(len(variants) == 2, "TWO_DISTINCT_FAMILIES_REQUIRED")
    results = {}
    targets = set()
    for id_, row in variants.items():
        check_fixture(id_, row)
        require(row["target"] not in targets, "OVERLAPPING_TARGETS_DENIED")
        targets.add(row["target"])
        bad = replay(row, row["source"], expected_pass=False)
        good = replay(row, row["golden"], expected_pass=True)
        results[id_] = {
            "target": row["target"], "test": row["test"],
            "seed_sha256": sha(row["source"]),
            "visible_sha256": sha(row["visible"]),
            "hidden_sha256": sha(row["hidden"]),
            "prompt_sha256": sha(row["prompt"]),
            "golden_sha256_for_lab_selftest_only": sha(row["golden"]),
            "seed_fails_3_visible_or_12_hidden": not bad["pass"],
            "golden_passes_3_visible_and_12_hidden": good["pass"],
            "model_calls": 0,
        }
    require(len(targets) == len(variants), "TARGET_COLLISION")
    return {"schema": SCHEMA, "authority": AUTHORITY, "issue": ISSUE,
            "status": "PASS_TWO_DISTINCT_OFFLINE_QA_FIXTURES_ONLY",
            "fixtures": results, "model_invocations": 0,
            "production_authority": False,
            "real_coding_worker_or_pr_proven": False,
            "canonical_fleet_lease": False, "automatic_retry": False}


def allowed_root(raw, task):
    path = Path(raw)
    require(path.is_absolute() and path.name.startswith("p0-diverse-fixtures-")
            and path.parent.name == "AgentEnvelopeLab"
            and path.parent.is_dir() and not path.parent.is_symlink()
            and not path.is_symlink() and ".." not in path.parts,
            "EXCLUSIVE_LAB_DIRECTORY_REQUIRED")
    require(isinstance(task, str) and ID.fullmatch(task) is not None,
            "P0_DIVERSE_TASK_ID_REQUIRED")
    destination = path / task
    require(not destination.exists() and not destination.is_symlink(),
            "PREVIOUS_TASK_MUST_NOT_BE_REPREPARED")
    return path, destination


def prepare(root, task_id, fixture_id):
    variants = catalog()
    require(fixture_id in variants, "UNKNOWN_TASK_VARIANT")
    row = variants[fixture_id]
    check_fixture(fixture_id, row)
    home, dest = allowed_root(root, task_id)
    if not home.exists():
        home.mkdir(exist_ok=False)
    dest.mkdir(exist_ok=False)
    checkout = dest / "repo"
    checkout.mkdir()
    target, test = checkout / row["target"], checkout / row["test"]
    test.parent.mkdir()
    target.write_bytes(row["source"].encode("utf-8"))
    test.write_bytes(row["visible"].encode("utf-8"))
    branch = BRANCH + task_id
    git("init", "-q", "-b", branch, str(checkout))
    git("-C", str(checkout), "config", "core.autocrlf", "false")
    git("-C", str(checkout), "add", "--", row["target"], row["test"])
    git("-C", str(checkout), "-c", "user.name=LAB Fixture",
        "-c", "user.email=fixture@example.invalid",
        "commit", "-qm", "Diverse synthetic task preparation only")
    base = git("-C", str(checkout), "rev-parse", "HEAD")
    require(not git("-C", str(checkout), "status", "--porcelain=v1"),
            "PREPARED_REPO_DIRTY")
    prompt, hidden = dest / "task.prompt.txt", dest / "hidden.qa.py"
    prompt.write_bytes(row["prompt"].encode("utf-8"))
    hidden.write_bytes(row["hidden"].encode("utf-8"))
    before = continuity.self_test_manifest()
    before["active_external_effects"] = []
    before["code_baseline"] = {
        "repo": "nocturney/velvetos-core", "base_sha": base,
        "branch": branch, "worktree_path": str(checkout.resolve())}
    checkpoint = dest / "checkpoint.json"
    continuity.write(checkpoint, continuity.seal(before))
    proof = {
        "schema": SCHEMA, "authority": AUTHORITY, "issue": ISSUE,
        "status": "PREPARED_ONLY_NOT_EXECUTABLE_BY_V1_WORKER",
        "task_id": task_id, "fixture_id": fixture_id,
        "host": __import__("platform").node(),
        "worktree_path": str(checkout.resolve()), "base_sha": base,
        "branch": branch, "target_file": row["target"],
        "visible_test_file": row["test"], "target_seed_sha256": file_hash(target),
        "visible_test_sha256": file_hash(test),
        "prompt_file": str(prompt.resolve()),
        "prompt_sha256": file_hash(prompt),
        "hidden_qa_file": str(hidden.resolve()),
        "hidden_qa_sha256": file_hash(hidden),
        "context_checkpoint": str(checkpoint.resolve()),
        "checkpoint_sha256": file_hash(checkpoint),
        "model_invocations": 0, "approved_model_executor": None,
        "real_coding_worker_or_pr_proven": False,
        "autonomous_retry": False, "production_authority": False,
        "scheduler_or_fleet_lease_authority": False,
    }
    proof["proof_sha256"] = canon(proof)
    manifest = dest / "candidate.json"
    with manifest.open("x", encoding="utf-8") as f:
        json.dump(proof, f, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    return {"status": proof["status"], "task_id": task_id,
            "candidate": str(manifest),
            "proof_sha256": proof["proof_sha256"],
            "model_invocations": 0, "production_authority": False}



def verify_candidate(raw):
    """Independent read-only prepared fixture readback. Never runs a model."""
    file = Path(raw)
    require(file.is_absolute() and file.name == "candidate.json"
            and not file.is_symlink() and file.is_file()
            and file.parent.is_dir()
            and ID.fullmatch(file.parent.name) is not None
            and file.parent.parent.name.startswith("p0-diverse-fixtures-")
            and file.parent.parent.parent.name == "AgentEnvelopeLab",
            "ONLY_EXPLICIT_PREPARED_CANDIDATE")
    require(all(not p.is_symlink() for p in
                (file.parent, file.parent.parent, file.parent.parent.parent)),
            "SYMLINK_REPOINTING_DENIED")
    data = json.loads(file.read_text(encoding="utf-8"))
    require(isinstance(data, dict) and data.get("schema") == SCHEMA
            and data.get("authority") == AUTHORITY
            and data.get("issue") == ISSUE
            and data.get("status") == "PREPARED_ONLY_NOT_EXECUTABLE_BY_V1_WORKER",
            "HISTORIC_CANDIDATE_SHAPE_DRIFT")
    seal = data.get("proof_sha256")
    require(isinstance(seal, str) and len(seal) == 64
            and seal == canon({k:v for k,v in data.items() if k!="proof_sha256"}),
            "CANDIDATE_MANIFEST_HASH_DRIFT")
    fixture = data.get("fixture_id")
    rows = catalog()
    require(fixture in rows and data.get("task_id") == file.parent.name
            and data.get("host") == __import__("platform").node(),
            "WRONG_LAB_FIXTURE_HOST_OR_TASK")
    spec = rows[fixture]
    root = file.parent / "repo"
    require(root.is_dir() and (root / ".git").is_dir()
            and not root.is_symlink() and
            data.get("worktree_path") == str(root.resolve()),
            "ORIGINAL_CHECKOUT_MISSING")
    require(Path(git("-C", str(root), "rev-parse", "--show-toplevel")).resolve() == root.resolve()
            and git("-C", str(root), "rev-parse", "HEAD") == data.get("base_sha")
            and git("-C", str(root), "branch", "--show-current") == data.get("branch")
            and not git("-C", str(root), "status", "--porcelain=v1"),
            "FIXTURE_GIT_BASE_BRANCH_OR_DIRTY_DRIFT")
    require(data["branch"] == BRANCH + data["task_id"]
            and data.get("target_file") == spec["target"]
            and data.get("visible_test_file") == spec["test"],
            "UNREGISTERED_TARGET_OR_BRANCH")
    target = root / spec["target"]
    visible = root / spec["test"]
    prompt = file.parent / "task.prompt.txt"
    hidden = file.parent / "hidden.qa.py"
    cp = file.parent / "checkpoint.json"
    for actual in (target, visible, prompt, hidden, cp):
        require(actual.is_file() and not actual.is_symlink(),
                "PREPARED_SOURCE_TAMPER_OR_MISSING")
    require(
        file_hash(target) == data.get("target_seed_sha256") == sha(spec["source"])
        and file_hash(visible) == data.get("visible_test_sha256") == sha(spec["visible"])
        and file_hash(prompt) == data.get("prompt_sha256") == sha(spec["prompt"])
        and file_hash(hidden) == data.get("hidden_qa_sha256") == sha(spec["hidden"])
        and file_hash(cp) == data.get("checkpoint_sha256"),
        "PREPARED_SOURCE_BYTES_CHANGED")
    require(
        data.get("prompt_file") == str(prompt.resolve())
        and data.get("hidden_qa_file") == str(hidden.resolve())
        and data.get("context_checkpoint") == str(cp.resolve()),
        "PREPARED_PATH_BINDING_DRIFT")
    before = json.loads(cp.read_text(encoding="utf-8"))
    baseline = before.get("code_baseline") or {}
    require(not continuity.required_shape(before)
            and before.get("active_external_effects") == []
            and baseline.get("repo") == "nocturney/velvetos-core"
            and baseline.get("base_sha") == data["base_sha"]
            and baseline.get("branch") == data["branch"]
            and baseline.get("worktree_path") == str(root.resolve()),
            "CONTEXT_OR_BASELINE_MISMATCH")
    for key in ("real_coding_worker_or_pr_proven", "autonomous_retry",
                "production_authority", "scheduler_or_fleet_lease_authority"):
        require(data.get(key) is False, "CANDIDATE_AUTHORITY_ESCALATION_"+key)
    require(data.get("approved_model_executor") is None
            and data.get("model_invocations") == 0,
            "UNAUTHORIZED_PREPARED_EXECUTOR")
    replay(spec, target.read_text(encoding="utf-8"), expected_pass=False)
    return {"status":"PASS_PREPARED_ONLY_INDEPENDENT_BYTE_GIT_QA_READBACK",
            "task_id":data["task_id"],"fixture":fixture,
            "base_sha":data["base_sha"],"proof_sha256":seal,
            "model_invocations":0,"v1_worker_ready":False,
            "production_authority":False}

def selftest():
    out = inspect()
    assert out["status"] == "PASS_TWO_DISTINCT_OFFLINE_QA_FIXTURES_ONLY"
    scenarios = [
        ("wrong_fixture", lambda row: check_fixture("customer", row)),
        ("wrong_seed_entry", lambda row: check_fixture("canonical-tag-v1", dict(row, target="safe.py"))),
        ("wrong_prompt", lambda row: check_fixture("canonical-tag-v1", dict(row, prompt="."))),
        ("already_solved", lambda row: check_fixture("canonical-tag-v1", dict(row, source=row["golden"]))),
        ("not_absolute", lambda row: allowed_root("relative", "p0-diverse-selftest")),
        ("wrong_name", lambda row: allowed_root("/tmp/random", "p0-diverse-selftest")),
        ("wrong_task", lambda row: allowed_root("/tmp/p0-diverse-fixtures-lab", "../outside")),
        ("wrong_path", lambda row: allowed_root("/tmp/p0-diverse-fixtures-lab", "not-a-task")),
        ("relative_candidate", lambda row: verify_candidate("candidate.json")),
    ]
    checks = ["two_different_seed_targets", "seed_fails_and_golden_passes_both_families"]
    canonical = catalog()["canonical-tag-v1"]
    for label, attack in scenarios:
        try:
            attack(canonical)
        except (Refused, ValueError):
            checks.append(label+"_DENIED")
        else:
            raise AssertionError("UNSAFE_FIXTURE_REQUEST_ACCEPTED:"+label)
    require(len(checks) == 11, "SELFTEST_COUNT_DRIFT")
    return {"status":"PASS_OFFLINE","tests":len(checks),
            "fixture_count":2,"model_calls":0,
            "external_effects":0,"production_authority":False,
            "v1_worker_ready":False, "different_live_coding_tasks_proven":False,
            "fixtures":out["fixtures"]}


def main():
    p=argparse.ArgumentParser()
    subs=p.add_subparsers(dest="mode",required=True)
    subs.add_parser("selftest")
    prep=subs.add_parser("prepare")
    prep.add_argument("--root",required=True)
    prep.add_argument("--task-id",required=True)
    prep.add_argument("--fixture",choices=list(catalog()),required=True)
    verify=subs.add_parser("verify")
    verify.add_argument("--candidate",required=True)
    args=p.parse_args()
    if args.mode=="selftest":
        result=selftest()
    elif args.mode=="verify":
        result=verify_candidate(args.candidate)
    else:
        result=prepare(args.root,args.task_id,args.fixture)
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    try: main()
    except (Refused,OSError,ValueError,KeyError,TypeError,AssertionError,
            subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(exc)[:150],
                          "no_model_execution":True,
                          "no_auto_retry":True},sort_keys=True))
        raise SystemExit(2)
