#!/usr/bin/env python3
"""#604: REAL local bare-Git + SQLite crash/UNKNOWN LAB (OFFLINE ONLY).

This is NOT an exclusive GitHub credential-owning sink, live provider, broker,
scheduler, source of truth, or production admission. Every Git call is confined
to a newly created bare repository inside a temporary offline test directory.
A fixture-only provider JSON file is NOT an authenticated live lease. Real
native local-Git ref CAS and durable SQLite intent commits exercise gaps that
the preceding #671 in-memory model could not demonstrate.
"""
import contextlib
import dataclasses
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

SCHEMA = "vf604.native-git-crash-reconcile-offline.v1"
REPO = "nocturney/velvetos-core"
REF = "refs/heads/vf604-offline-local-only"
ZERO = "0" * 40
BLOCKING = ("EFFECT_IN_FLIGHT", "UNKNOWN_EFFECT_RECONCILE")
MARKER = ".vf604-offline-no-network"
ENV = dict(os.environ)
ENV.update({
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "VF604 isolated local Git LAB",
    "GIT_AUTHOR_EMAIL": "vf604@example.invalid",
    "GIT_COMMITTER_NAME": "VF604 isolated local Git LAB",
    "GIT_COMMITTER_EMAIL": "vf604@example.invalid",
})


def sha(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{40}", value))


def git_raw(args, *, stdin=None):
    return subprocess.run(["git"] + list(args), input=stdin, capture_output=True,
                          text=True, env=ENV, timeout=15)


@dataclasses.dataclass(frozen=True)
class Intent:
    key: str
    actor: str
    epoch: int
    expected: str
    candidate: str
    repo: str = REPO
    ref: str = REF


class OfflineLab:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.repo = self.root / "scratch.git"
        self.db = self.root / "receipt.sqlite3"
        self.provider = self.root / "provider.json"
        self.requests = self.root / "requests"

    def verified(self):
        return (self.root.is_dir() and not self.root.is_symlink()
                and (self.root / MARKER).is_file()
                and self.repo.is_dir() and not self.repo.is_symlink()
                and (self.repo / "HEAD").is_file()
                and self.db.is_file())

    def git(self, *args, stdin=None, allow_error=False):
        if not self.verified():
            raise ValueError("NOT_ISOLATED_OFFLINE_REPOSITORY")
        p = git_raw(["--git-dir", str(self.repo)] + list(args), stdin=stdin)
        if p.returncode and not allow_error:
            raise ValueError("NATIVE_LOCAL_GIT_COMMAND_FAILED")
        return p

    @contextlib.contextmanager
    def connect(self):
        if not self.verified():
            raise sqlite3.DatabaseError("OFFLINE_LAB_NOT_VERIFIED")
        c = sqlite3.connect(str(self.db), timeout=0.1, isolation_level=None)
        try:
            c.row_factory = sqlite3.Row
            c.execute("PRAGMA synchronous=FULL")
            with c:
                yield c
        finally:
            c.close()

    @classmethod
    def create(cls, root):
        r = Path(root)
        r.mkdir(parents=True, exist_ok=False)
        (r / MARKER).write_text("temporary fixture; no remote; no secrets\n")
        (r / "requests").mkdir()
        p = git_raw(["init", "--bare", "--quiet", str(r / "scratch.git")])
        if p.returncode:
            raise RuntimeError("CANNOT_CREATE_ISOLATED_BARE_REPO")
        db = sqlite3.connect(str(r / "receipt.sqlite3"))
        db.execute("PRAGMA synchronous=FULL")
        db.executescript("""
          CREATE TABLE attempts (
            key TEXT PRIMARY KEY, actor TEXT NOT NULL, epoch INTEGER NOT NULL,
            expected TEXT NOT NULL, candidate TEXT NOT NULL,
            provider_revision INTEGER NOT NULL, state TEXT NOT NULL,
            observation TEXT NOT NULL DEFAULT '',
            before_sha TEXT NOT NULL DEFAULT '', after_sha TEXT NOT NULL DEFAULT ''
          );
          CREATE TABLE freeze (id INTEGER PRIMARY KEY CHECK(id=1),
                               locked INTEGER NOT NULL);
          INSERT INTO freeze(id, locked) VALUES(1, 0);
        """)
        db.commit()
        db.close()
        lab = cls(r)
        lab.set_provider(actor="worker-a", epoch=7, phase="ACTIVE",
                         ttl=20, revision=10)
        empty_tree = lab.git("mktree", stdin="").stdout.strip()
        seed = lab.git("commit-tree", empty_tree, "-m",
                       "VF604_SYNTHETIC_LOCAL_SEED").stdout.strip()
        if not sha(seed):
            raise RuntimeError("SEED_NOT_A_SHA")
        lab.git("update-ref", REF, seed, ZERO)
        return lab

    def set_provider(self, *, actor="worker-a", epoch=7, phase="ACTIVE",
                     ttl=20, revision=10):
        data = {"actor": actor, "epoch": epoch, "phase": phase,
                "ttl_seconds": ttl, "revision": revision}
        temp = self.root / "provider.json.partial"
        with temp.open("w", encoding="utf-8") as f:
            json.dump(data, f, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(str(temp), str(self.provider))

    def observe(self):
        try:
            obj = json.loads(self.provider.read_text(encoding="utf-8"))
            if type(obj) is not dict or set(obj) != {
                "actor", "epoch", "phase", "ttl_seconds", "revision"
            }:
                raise ValueError("INVALID_PROVIDER_OBSERVATION")
            if type(obj["revision"]) is not int or obj["revision"] < 1:
                raise ValueError("INVALID_REVISION")
            return obj
        except (OSError, ValueError, KeyError, TypeError):
            raise ValueError("SYNTHETIC_PROVIDER_UNAVAILABLE")

    def remote_sha(self):
        p = self.git("rev-parse", "--verify", REF, allow_error=True)
        x = p.stdout.strip()
        if p.returncode != 0 or not sha(x):
            raise ValueError("LOCAL_REMOTE_REF_UNREADABLE")
        return x

    def candidate(self, key, expected=None, epoch=7, actor="worker-a"):
        if not re.fullmatch(r"[a-z0-9-]{1,32}", key):
            raise ValueError("INVALID_KEY")
        old = expected or self.remote_sha()
        tree = self.git("rev-parse", old + "^{tree}").stdout.strip()
        message = ("VF604_LOCAL_INTENT=" + key + ";ACTOR=" + actor
                   + ";EPOCH=" + str(epoch) + ";NO_REMOTE_GIT\n")
        new = self.git("commit-tree", tree, "-p", old,
                       "-m", message).stdout.strip()
        if not sha(new):
            raise ValueError("CANDIDATE_NOT_SHA")
        return Intent(key=key, actor=actor, epoch=epoch,
                      expected=old, candidate=new)

    def marker_valid(self, intent):
        p = self.git("cat-file", "-p", intent.candidate, allow_error=True)
        if p.returncode:
            return False
        body = p.stdout
        expected = ("VF604_LOCAL_INTENT=" + intent.key
                    + ";ACTOR=" + intent.actor + ";EPOCH="
                    + str(intent.epoch) + ";NO_REMOTE_GIT")
        return ("parent " + intent.expected + "\n") in body and expected in body

    def save_request(self, intent):
        if not isinstance(intent, Intent) or not re.fullmatch(
                r"[a-z0-9-]{1,32}", intent.key):
            raise ValueError("INVALID_REQUEST_FILENAME")
        f = self.requests / (intent.key + ".json")
        with f.open("x", encoding="utf-8") as out:
            json.dump(dataclasses.asdict(intent), out, sort_keys=True)
        return f

    def load_request(self, key):
        if not re.fullmatch(r"[a-z0-9-]{1,32}", key):
            raise ValueError("INVALID_REQUEST_ID")
        j = json.loads((self.requests / (key + ".json")).read_text())
        return Intent(**j)

    def status(self, key):
        with self.connect() as c:
            x = c.execute("SELECT * FROM attempts WHERE key=?", (key,)).fetchone()
            return dict(x) if x else None

    def frozen(self):
        with self.connect() as c:
            x = c.execute("SELECT locked FROM freeze WHERE id=1").fetchone()
            return bool(x[0])

    @staticmethod
    def live_match(observation, intent):
        return (type(observation["epoch"]) is int
                and observation["epoch"] == intent.epoch
                and observation["actor"] == intent.actor
                and observation["phase"] == "ACTIVE"
                and type(observation["ttl_seconds"]) is int
                and observation["ttl_seconds"] > 0)

    @staticmethod
    def valid_intent(intent):
        return (type(intent) is Intent
                and re.fullmatch(r"[a-z0-9-]{1,32}", intent.key)
                and intent.repo == REPO and intent.ref == REF
                and type(intent.epoch) is int and intent.epoch > 0
                and sha(intent.expected) and sha(intent.candidate)
                and intent.expected != intent.candidate)

    def claim(self, intent):
        if not self.valid_intent(intent):
            return "NOT_ADMITTED"
        try:
            with self.connect() as c:
                c.execute("BEGIN IMMEDIATE")
                if c.execute("SELECT locked FROM freeze WHERE id=1").fetchone()[0]:
                    return "NOT_ADMITTED"
                if c.execute("SELECT 1 FROM attempts WHERE key=?",
                             (intent.key,)).fetchone():
                    return "NOT_ADMITTED"
                active = c.execute("SELECT 1 FROM attempts WHERE state IN (?,?) LIMIT 1",
                                   BLOCKING).fetchone()
                if active:
                    return "NOT_ADMITTED"
                try:
                    first = self.observe()
                    remote = self.remote_sha()
                    second = self.observe()
                except ValueError:
                    c.execute("UPDATE freeze SET locked=1 WHERE id=1")
                    return "FROZEN_PROVIDER_UNKNOWN"
                if (first != second or not self.live_match(first, intent)
                        or remote != intent.expected
                        or not self.marker_valid(intent)):
                    return "DENIED_STALE"
                c.execute(
                    """INSERT INTO attempts(key, actor, epoch, expected, candidate,
                           provider_revision, state, before_sha)
                           VALUES (?,?,?,?,?,?,?,?)""",
                    (intent.key, intent.actor, intent.epoch, intent.expected,
                     intent.candidate, second["revision"], "EFFECT_IN_FLIGHT",
                     remote))
                return "PREPARED_DURABLE"
        except (sqlite3.Error, OSError, ValueError):
            return "FROZEN_JOURNAL_UNAVAILABLE"

    def mark_unknown(self, key, reason):
        try:
            with self.connect() as c:
                c.execute("BEGIN IMMEDIATE")
                c.execute("""UPDATE attempts SET state=?, observation=?
                           WHERE key=? AND state IN (?,?)""",
                          ("UNKNOWN_EFFECT_RECONCILE", reason, key,
                           "EFFECT_IN_FLIGHT", "UNKNOWN_EFFECT_RECONCILE"))
                c.execute("UPDATE freeze SET locked=1 WHERE id=1")
            return "UNKNOWN_EFFECT_RECONCILE"
        except (sqlite3.Error, OSError):
            return "FROZEN_JOURNAL_UNAVAILABLE"

    def mark_committed(self, key, after):
        try:
            with self.connect() as c:
                c.execute("BEGIN IMMEDIATE")
                r = c.execute("""UPDATE attempts
                                 SET state=?, after_sha=?, observation=?
                                 WHERE key=? AND state='EFFECT_IN_FLIGHT'""",
                              ("COMMITTED_READBACK", after,
                               "LOCAL_GIT_SHA_AND_PROVIDER_READBACK",
                               key))
                if r.rowcount != 1:
                    c.execute("UPDATE freeze SET locked=1 WHERE id=1")
                    return "UNKNOWN_EFFECT_RECONCILE"
            return "COMMITTED_READBACK"
        except (sqlite3.Error, OSError):
            return "FROZEN_JOURNAL_UNAVAILABLE"

    def attempt(self, intent, *, fault="none", barrier=False):
        admission = self.claim(intent)
        if admission != "PREPARED_DURABLE":
            return admission
        if fault == "crash_after_prepare":
            os._exit(91)
        if barrier:
            (self.root / "holding.ready").write_text("prepared\n")
            release = self.root / "holding.release"
            until = time.monotonic() + 7
            while not release.exists() and time.monotonic() < until:
                time.sleep(0.025)
            if not release.exists():
                return self.mark_unknown(intent.key, "BARRIER_TIMEOUT")
        if fault == "provider_revoked_before_git":
            self.set_provider(phase="NOT_ADMITTED", ttl=0, revision=11)
        try:
            current = self.observe()
            if (not self.live_match(current, intent) or
                    current["revision"] != self.status(intent.key)["provider_revision"]):
                return self.mark_unknown(intent.key, "PRE_NATIVE_PROVIDER_CHANGED")
            if fault == "lost_ack_before_git":
                return self.mark_unknown(intent.key, "SIMULATED_BEFORE_NATIVE_OUTCOME_UNKNOWN")
            before = self.remote_sha()
            if before != intent.expected:
                return self.mark_unknown(intent.key, "REMOTE_REF_CHANGED_AFTER_PREPARE")
            result = self.git("update-ref", REF, intent.candidate,
                              intent.expected, allow_error=True)
            if result.returncode:
                return self.mark_unknown(intent.key, "NATIVE_LOCAL_CAS_REJECTED")
            if fault == "crash_after_native_git":
                os._exit(92)
            if fault == "lost_ack_after_git":
                return self.mark_unknown(intent.key, "SIMULATED_AFTER_NATIVE_ACK_LOST")
            if fault == "provider_revoked_after_git":
                self.set_provider(phase="NOT_ADMITTED", ttl=0, revision=11)
            after = self.remote_sha()
            final = self.observe()
            if (after != intent.candidate or not self.marker_valid(intent)
                    or not self.live_match(final, intent)
                    or final["revision"] != current["revision"]):
                return self.mark_unknown(intent.key, "AFTER_NATIVE_READBACK_MISMATCH")
            return self.mark_committed(intent.key, after)
        except (ValueError, sqlite3.Error, OSError, subprocess.TimeoutExpired):
            return self.mark_unknown(intent.key, "EFFECT_OR_PROVIDER_OUTCOME_UNKNOWN")

    def reconcile(self, key, *, process_terminated):
        try:
            record = self.status(key)
        except (sqlite3.Error, ValueError):
            return "JOURNAL_UNREADABLE_REVIEW_REQUIRED"
        if not record or record["state"] not in BLOCKING:
            return "NO_PENDING_UNKNOWN"
        if not process_terminated:
            return "PROCESS_MAY_STILL_WRITE_REVIEW_REQUIRED"
        try:
            after = self.remote_sha()
            self.observe()
        except ValueError:
            self.mark_unknown(key, "RECONCILE_READBACK_UNAVAILABLE")
            return "READBACK_UNAVAILABLE_REVIEW_REQUIRED"
        if after == record["candidate"]:
            classification = "REMOTE_ADVANCED_REVIEW_REQUIRED"
        elif after == record["expected"]:
            classification = "REMOTE_UNCHANGED_REVIEW_REQUIRED"
        else:
            classification = "REMOTE_CONFLICT_REVIEW_REQUIRED"
        self.mark_unknown(key, classification)
        try:
            with self.connect() as c:
                c.execute("UPDATE attempts SET after_sha=?, observation=? WHERE key=?",
                          (after, classification, key))
        except sqlite3.Error:
            return "JOURNAL_UNREADABLE_REVIEW_REQUIRED"
        return classification


class DurableGitOfflineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="vf604-native-local-only-")
        root = Path(self.tmp.name) / "lab"
        self.lab = OfflineLab.create(root)
        self.seed = self.lab.remote_sha()

    def tearDown(self):
        self.tmp.cleanup()

    def request(self, key="t1", **kwargs):
        it = self.lab.candidate(key, **kwargs)
        self.lab.save_request(it)
        return it

    def child(self, key="t1", fault="none", barrier=False):
        args = [sys.executable, str(Path(__file__).resolve()),
                "worker", str(self.lab.root), key, fault]
        if barrier:
            args.append("barrier")
        return subprocess.run(args, text=True, capture_output=True,
                              timeout=12)

    def test_01_local_native_git_exact_cas_with_readback(self):
        it = self.request()
        p = self.child()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)["state"], "COMMITTED_READBACK")
        self.assertEqual(self.lab.remote_sha(), it.candidate)
        self.assertEqual(self.lab.status("t1")["state"], "COMMITTED_READBACK")
        self.assertFalse(self.lab.frozen())

    def test_02_process_crash_after_sqlite_prepare_before_git(self):
        self.request()
        p = self.child(fault="crash_after_prepare")
        self.assertEqual(p.returncode, 91)
        self.assertEqual(self.lab.remote_sha(), self.seed)
        self.assertEqual(self.lab.status("t1")["state"], "EFFECT_IN_FLIGHT")
        self.assertEqual(self.lab.reconcile("t1", process_terminated=False),
                         "PROCESS_MAY_STILL_WRITE_REVIEW_REQUIRED")
        self.assertEqual(self.lab.reconcile("t1", process_terminated=True),
                         "REMOTE_UNCHANGED_REVIEW_REQUIRED")
        self.assertTrue(self.lab.frozen())

    def test_03_process_crash_after_native_git_before_receipt(self):
        it = self.request()
        p = self.child(fault="crash_after_native_git")
        self.assertEqual(p.returncode, 92)
        self.assertEqual(self.lab.remote_sha(), it.candidate)
        self.assertEqual(self.lab.status("t1")["state"], "EFFECT_IN_FLIGHT")
        self.assertEqual(self.lab.reconcile("t1", process_terminated=True),
                         "REMOTE_ADVANCED_REVIEW_REQUIRED")
        self.assertNotEqual(self.lab.status("t1")["state"], "COMMITTED_READBACK")
        self.assertTrue(self.lab.frozen())

    def test_04_lost_ack_before_local_git_no_blind_retry(self):
        self.request()
        p = self.child(fault="lost_ack_before_git")
        self.assertEqual(json.loads(p.stdout)["state"], "UNKNOWN_EFFECT_RECONCILE")
        self.assertEqual(self.lab.remote_sha(), self.seed)
        self.assertEqual(self.lab.reconcile("t1", process_terminated=True),
                         "REMOTE_UNCHANGED_REVIEW_REQUIRED")
        self.assertEqual(json.loads(self.child().stdout)["state"], "NOT_ADMITTED")

    def test_05_lost_ack_after_git_remains_unknown(self):
        it = self.request()
        self.assertEqual(json.loads(self.child(fault="lost_ack_after_git").stdout)["state"],
                         "UNKNOWN_EFFECT_RECONCILE")
        self.assertEqual(self.lab.remote_sha(), it.candidate)
        self.assertEqual(self.lab.reconcile("t1", process_terminated=True),
                         "REMOTE_ADVANCED_REVIEW_REQUIRED")
        self.assertEqual(self.lab.status("t1")["state"], "UNKNOWN_EFFECT_RECONCILE")

    def test_06_old_epoch_with_current_sha_is_denied(self):
        it = self.request(epoch=6)
        self.assertEqual(json.loads(self.child().stdout)["state"], "DENIED_STALE")
        self.assertEqual(self.lab.remote_sha(), it.expected)
        self.assertIsNone(self.lab.status("t1"))

    def test_07_expired_revoked_pending_all_denied(self):
        for phase, ttl in (("ACTIVE", 0), ("NOT_ADMITTED", 20),
                           ("PENDING_CUTOVER", 20)):
            self.lab.set_provider(phase=phase, ttl=ttl, revision=11)
            i = self.lab.candidate("test-" + phase.lower().replace("_", "-") + str(ttl))
            self.assertEqual(self.lab.claim(i), "DENIED_STALE")
            self.assertIsNone(self.lab.status(i.key))

    def test_08_missing_provider_freezes_without_effect(self):
        it = self.request()
        self.lab.provider.unlink()
        self.assertEqual(json.loads(self.child().stdout)["state"],
                         "FROZEN_PROVIDER_UNKNOWN")
        self.assertTrue(self.lab.frozen())
        self.assertEqual(self.lab.remote_sha(), it.expected)

    def test_09_provider_revoked_after_prepare_before_git(self):
        it = self.request()
        self.assertEqual(json.loads(self.child(fault="provider_revoked_before_git").stdout)["state"],
                         "UNKNOWN_EFFECT_RECONCILE")
        self.assertEqual(self.lab.remote_sha(), it.expected)
        self.assertEqual(self.lab.status("t1")["state"], "UNKNOWN_EFFECT_RECONCILE")

    def test_10_provider_revoked_after_native_effect(self):
        it = self.request()
        self.assertEqual(json.loads(self.child(fault="provider_revoked_after_git").stdout)["state"],
                         "UNKNOWN_EFFECT_RECONCILE")
        self.assertEqual(self.lab.remote_sha(), it.candidate)
        self.assertTrue(self.lab.frozen())

    def test_11_actual_cross_process_pending_blocks_second(self):
        it = self.request()
        args = [sys.executable, str(Path(__file__).resolve()), "worker",
                str(self.lab.root), "t1", "none", "barrier"]
        first = subprocess.Popen(args, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 6
            while not (self.lab.root / "holding.ready").exists():
                if first.poll() is not None or time.monotonic() > deadline:
                    self.fail("FIRST_PROCESS_DID_NOT_PERSIST_PREPARE")
                time.sleep(0.02)
            self.assertEqual(self.lab.status("t1")["state"], "EFFECT_IN_FLIGHT")
            other = self.lab.candidate("t2")
            self.lab.save_request(other)
            p2 = self.child("t2")
            self.assertEqual(json.loads(p2.stdout)["state"], "NOT_ADMITTED")
        finally:
            (self.lab.root / "holding.release").write_text("release")
            out, err = first.communicate(timeout=10)
        self.assertEqual(first.returncode, 0, err)
        self.assertEqual(json.loads(out)["state"], "COMMITTED_READBACK")
        self.assertEqual(self.lab.remote_sha(), it.candidate)
        self.assertIsNone(self.lab.status("t2"))

    def test_12_duplicate_intent_after_commit_is_refused(self):
        self.request()
        self.assertEqual(json.loads(self.child().stdout)["state"], "COMMITTED_READBACK")
        self.assertEqual(json.loads(self.child().stdout)["state"], "NOT_ADMITTED")

    def test_13_wrong_repo_ref_or_sha_cannot_enter(self):
        i = self.lab.candidate("t1")
        for override in ({"repo": "other/repo"},
                         {"ref": "refs/heads/main"},
                         {"expected": "not-a-sha"},
                         {"epoch": True}):
            broken = dataclasses.replace(i, **override)
            self.assertEqual(self.lab.claim(broken), "NOT_ADMITTED")
        self.assertIsNone(self.lab.status("t1"))

    def test_14_third_party_local_git_ref_bypass_is_not_protected(self):
        self.request()
        outside = self.lab.candidate("outsider")
        self.lab.git("update-ref", REF, outside.candidate, outside.expected)
        self.assertEqual(self.lab.remote_sha(), outside.candidate)
        self.assertIsNone(self.lab.status("outsider"))
        # Proof of lack of credential/OS isolation, NOT proof of production fencing.
        self.assertFalse(verdict()["credential_exclusivity_proven"])
        self.assertEqual(json.loads(self.child().stdout)["state"], "DENIED_STALE")

    def test_15_unknown_remote_conflict_keeps_freeze(self):
        self.request()
        self.child(fault="lost_ack_before_git")
        outside = self.lab.candidate("outsider")
        self.lab.git("update-ref", REF, outside.candidate, outside.expected)
        self.assertEqual(self.lab.reconcile("t1", process_terminated=True),
                         "REMOTE_CONFLICT_REVIEW_REQUIRED")
        self.assertTrue(self.lab.frozen())

    def test_16_unknown_provider_outage_at_reconciliation(self):
        self.request()
        self.child(fault="lost_ack_after_git")
        self.lab.provider.unlink()
        self.assertEqual(self.lab.reconcile("t1", process_terminated=True),
                         "READBACK_UNAVAILABLE_REVIEW_REQUIRED")
        self.assertEqual(self.lab.status("t1")["state"], "UNKNOWN_EFFECT_RECONCILE")

    def test_17_restart_with_unknown_blocks_different_intent(self):
        self.request()
        self.child(fault="crash_after_prepare")
        restarted = OfflineLab(self.lab.root)
        i2 = restarted.candidate("t2")
        self.assertEqual(restarted.claim(i2), "NOT_ADMITTED")
        self.assertEqual(restarted.reconcile("t1", process_terminated=True),
                         "REMOTE_UNCHANGED_REVIEW_REQUIRED")
        self.assertEqual(restarted.claim(i2), "NOT_ADMITTED")

    def test_18_corrupted_durable_journal_fails_closed(self):
        it = self.request()
        self.lab.db.write_bytes(b"deliberately corrupted disposable SQLite lab\n")
        self.assertEqual(self.lab.claim(it), "FROZEN_JOURNAL_UNAVAILABLE")
        self.assertEqual(self.lab.remote_sha(), it.expected)

    def test_19_verified_scope_is_nonproduction_and_zero_network(self):
        v = verdict()
        self.assertTrue(v["synthetic_provider_only"])
        self.assertTrue(v["native_local_git_only"])
        self.assertEqual(v["external_git_writes"], 0)
        self.assertFalse(v["live_github_credential_in_use"])
        self.assertFalse(v["production_authority"])
        self.assertFalse(v["mid_push_lease_expiry_fenced"])
        self.assertFalse(v["exactly_once_across_git_provider_proven"])


def verdict():
    return {
        "schema": SCHEMA,
        "scope": "OFFLINE_TEMP_BARE_GIT_AND_SQLITE_RECEIPT_FIXTURE",
        "synthetic_provider_only": True,
        "native_local_git_only": True,
        "external_git_writes": 0,
        "live_github_credential_in_use": False,
        "credential_exclusivity_proven": False,
        "durable_fixture_intent_commit": True,
        "provider_authoritative_journal_proven": False,
        "mid_push_lease_expiry_fenced": False,
        "exactly_once_across_git_provider_proven": False,
        "unknown_auto_retries": 0,
        "production_authority": False,
        "scheduler_created": False,
        "paid_model_calls": 0,
        "canonical_provider_owner": "#604",
        "agent_consumer": "#612",
    }


def main(argv):
    if len(argv) == 2 and argv[1] == "verify":
        print(json.dumps(dict(verdict(), status="DESIGN_ONLY_NOT_ADMITTED"),
                         sort_keys=True))
        return 0
    if len(argv) == 2 and argv[1] == "selftest":
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(DurableGitOfflineTests)
        import io
        trace = io.StringIO()
        r = unittest.TextTestRunner(stream=trace, verbosity=1).run(suite)
        if not r.wasSuccessful():
            print(trace.getvalue(), file=sys.stderr)
            return 1
        print(json.dumps(dict(verdict(), status="PASS_OFFLINE",
                              tests=r.testsRun), sort_keys=True))
        return 0
    if len(argv) in (5, 6) and argv[1] == "worker":
        root, key, fault = argv[2:5]
        lab = OfflineLab(root)
        if not lab.verified():
            print("REFUSE_NON_LOCAL_LAB", file=sys.stderr)
            return 2
        # All worker inputs are synthetic, controller-authored fixtures.
        intent = lab.load_request(key)
        state = lab.attempt(intent, fault=fault,
                            barrier=(len(argv) == 6 and argv[5] == "barrier"))
        print(json.dumps({"state": state, "key": key}, sort_keys=True))
        return 0
    print("OFFLINE ONLY: selftest | verify", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
