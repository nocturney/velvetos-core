#!/usr/bin/env python3
"""#604 OFFLINE design probe: exclusive credential-owning Git effect sink.

NO Git client, network, credentials, scheduler, files, or live provider access.
This model is deliberately NOT a production sink. A provider observation and a
Git ref update cannot be made atomic by preflight, TTL or SHA compare. A push
may still finish after lease expiry. UNKNOWN is never blindly replayed.
"""
import json
import re
import sys
import threading
import unittest
from dataclasses import dataclass
from io import StringIO

REPO = "nocturney/velvetos-core"
REF = "refs/heads/office-v2-lab-604-exclusive-sink-offline-only"
ZERO = "0" * 40
A = "a" * 40
B = "b" * 40
C = "c" * 40

NOT_ADMITTED = "NOT_ADMITTED"
PENDING_CUTOVER = "PENDING_CUTOVER"
ACTIVE = "ACTIVE"
FROZEN_PROVIDER_UNKNOWN = "FROZEN_PROVIDER_UNKNOWN"
UNKNOWN_EFFECT_RECONCILE = "UNKNOWN_EFFECT_RECONCILE"
COMMITTED_READBACK = "COMMITTED_READBACK"
DENIED_STALE = "DENIED_STALE"


class ProviderUnavailable(Exception):
    pass


class RemoteUnknown(Exception):
    pass


@dataclass(frozen=True)
class Lease:
    actor: str
    epoch: int
    phase: str
    ttl_seconds: int
    revision: int


@dataclass(frozen=True)
class Intent:
    key: str
    actor: str = "worker-a"
    epoch: int = 7
    expected: str = A
    candidate: str = B
    repo: str = REPO
    ref: str = REF


class Provider:
    """Trusted-provider fixture, NOT worker-supplied JSON or real etcd."""

    def __init__(self):
        self.lease = Lease("worker-a", 7, ACTIVE, 30, 10)
        self.fail = False
        self.calls = 0
        self.on_observe = None

    def observe(self):
        self.calls += 1
        if self.on_observe:
            self.on_observe(self.calls, self)
        if self.fail:
            raise ProviderUnavailable()
        return self.lease


class Remote:
    """In-memory Git ref CAS. May lose ack before or after the effect."""

    def __init__(self):
        self.sha = A
        self.pushes = 0
        self.read_fail = False
        self.ack = "ok"
        self.on_push = None

    def read(self):
        if self.read_fail:
            raise RemoteUnknown()
        return self.sha

    def push_cas(self, expected, candidate):
        self.pushes += 1
        if self.on_push:
            self.on_push()
        if self.ack == "lost_before":
            raise RemoteUnknown()
        if self.sha != expected:
            return "stale"
        self.sha = candidate
        if self.ack == "lost_after":
            raise RemoteUnknown()
        return "ok"


class Sink:
    """Synthetic single-writer gate, no credential or privilege isolation.

    journal is a caller-provided in-memory fixture. Real recovery REQUIRES a
    durable authoritative intent ledger owned by #604, not this dict.
    """

    def __init__(self, provider, remote, journal=None):
        self.provider = provider
        self.remote = remote
        self.journal = journal if journal is not None else {}
        self.pending = None
        self.lock = threading.Lock()
        # Never clear an unresolved effect merely by restarting the process.
        self.frozen = any(v.get("state") == UNKNOWN_EFFECT_RECONCILE
                          for v in self.journal.values())

    @staticmethod
    def _sha(value):
        return isinstance(value, str) and bool(re.fullmatch("[0-9a-f]{40}", value))

    @classmethod
    def _valid(cls, intent):
        return (type(intent) is Intent
                and isinstance(intent.key, str)
                and bool(re.fullmatch("[a-z0-9-]{1,64}", intent.key))
                and intent.repo == REPO and intent.ref == REF
                and type(intent.epoch) is int and intent.epoch > 0
                and cls._sha(intent.expected) and cls._sha(intent.candidate)
                and intent.expected != intent.candidate)

    @staticmethod
    def _current(lease, intent):
        return (type(lease) is Lease and lease.phase == ACTIVE
                and lease.actor == intent.actor and lease.epoch == intent.epoch
                and type(lease.ttl_seconds) is int and lease.ttl_seconds > 0
                and type(lease.revision) is int and lease.revision >= 1)

    def _unknown(self, key):
        self.frozen = True
        if key in self.journal:
            self.journal[key]["state"] = UNKNOWN_EFFECT_RECONCILE
        return UNKNOWN_EFFECT_RECONCILE

    def submit(self, intent):
        if not self.lock.acquire(blocking=False):
            return NOT_ADMITTED
        try:
            return self._submit_locked(intent)
        finally:
            self.lock.release()

    def _submit_locked(self, intent):
        if not self._valid(intent):
            return NOT_ADMITTED
        if self.frozen or self.pending is not None or intent.key in self.journal:
            return NOT_ADMITTED
        try:
            first = self.provider.observe()
            current_sha = self.remote.read()
            second = self.provider.observe()
        except (ProviderUnavailable, RemoteUnknown):
            self.frozen = True
            return FROZEN_PROVIDER_UNKNOWN
        if not self._current(first, intent) or not self._current(second, intent):
            return DENIED_STALE
        if first != second:
            return DENIED_STALE
        if current_sha != intent.expected:
            return DENIED_STALE
        # Write-ahead evidence BEFORE the external effect. In the fixture this
        # dict is not crash-durable; a real sink must replace it with #604's
        # single-provider authoritative intent/receipt contract.
        self.journal[intent.key] = {
            "state": UNKNOWN_EFFECT_RECONCILE,
            "intent": intent,
            "provider_revision": second.revision,
            "readback": None,
        }
        self.pending = intent.key
        try:
            result = self.remote.push_cas(intent.expected, intent.candidate)
            after = self.remote.read()
            final = self.provider.observe()
        except (ProviderUnavailable, RemoteUnknown):
            return self._unknown(intent.key)
        if result == "stale" and after != intent.candidate:
            self.journal[intent.key]["state"] = DENIED_STALE
            self.journal[intent.key]["readback"] = after
            self.pending = None
            return DENIED_STALE
        if (result == "ok" and after == intent.candidate
                and self._current(final, intent) and final == second):
            self.journal[intent.key]["state"] = COMMITTED_READBACK
            self.journal[intent.key]["readback"] = after
            self.pending = None
            return COMMITTED_READBACK
        # Even if Git accepted, an expired lease DURING push is NOT fenced.
        return self._unknown(intent.key)

    def reconcile(self, key, *, process_terminated):
        if key not in self.journal:
            return "NO_UNKNOWN_RECORD"
        rec = self.journal[key]
        if rec["state"] != UNKNOWN_EFFECT_RECONCILE:
            return "NO_UNKNOWN_RECORD"
        if not process_terminated:
            return "PROCESS_MAY_STILL_WRITE_REVIEW_REQUIRED"
        try:
            after = self.remote.read()
            self.provider.observe()
        except (ProviderUnavailable, RemoteUnknown):
            self.frozen = True
            return "READBACK_UNAVAILABLE_REVIEW_REQUIRED"
        intent = rec["intent"]
        rec["readback"] = after
        if after == intent.candidate:
            return "REMOTE_MATCHES_CANDIDATE_REVIEW_REQUIRED"
        if after == intent.expected:
            return "REMOTE_UNCHANGED_REVIEW_REQUIRED"
        return "REMOTE_CONFLICT_REVIEW_REQUIRED"


class Tests(unittest.TestCase):
    def setUp(self):
        self.p, self.r = Provider(), Remote()
        self.s = Sink(self.p, self.r)

    def req(self, key="t1", **kwargs):
        return Intent(key=key, **kwargs)

    def test_01_current_owner_synthetic_commit(self):
        self.assertEqual(self.s.submit(self.req()), COMMITTED_READBACK)
        self.assertEqual(self.r.sha, B)

    def test_02_expired_owner_denied(self):
        self.p.lease = Lease("worker-a", 7, ACTIVE, 0, 11)
        self.assertEqual(self.s.submit(self.req()), DENIED_STALE)
        self.assertEqual(self.r.pushes, 0)

    def test_03_revoked_owner_denied(self):
        self.p.lease = Lease("", 7, NOT_ADMITTED, 0, 11)
        self.assertEqual(self.s.submit(self.req()), DENIED_STALE)

    def test_04_old_epoch_current_remote_sha_denied(self):
        self.p.lease = Lease("worker-b", 8, ACTIVE, 20, 11)
        self.assertEqual(self.s.submit(self.req()), DENIED_STALE)
        self.assertEqual(self.r.sha, A)

    def test_05_pending_cutover_not_active(self):
        self.p.lease = Lease("worker-a", 7, PENDING_CUTOVER, 30, 10)
        self.assertEqual(self.s.submit(self.req()), DENIED_STALE)

    def test_06_provider_outage_before_preflight(self):
        self.p.fail = True
        self.assertEqual(self.s.submit(self.req()), FROZEN_PROVIDER_UNKNOWN)
        self.assertTrue(self.s.frozen)
        self.assertEqual(self.r.pushes, 0)

    def test_07_expiry_after_preflight_read(self):
        self.p.on_observe = lambda n, p: setattr(
            p, "lease", Lease("worker-a", 7, ACTIVE, 0, 11)) if n == 2 else None
        self.assertEqual(self.s.submit(self.req()), DENIED_STALE)
        self.assertEqual(self.r.pushes, 0)

    def test_08_provider_outage_on_second_read(self):
        self.p.on_observe = lambda n, p: setattr(p, "fail", True) if n == 2 else None
        self.assertEqual(self.s.submit(self.req()), FROZEN_PROVIDER_UNKNOWN)
        self.assertEqual(self.r.pushes, 0)

    def test_09_mid_push_expiry_is_not_fenced(self):
        self.r.on_push = lambda: setattr(
            self.p, "lease", Lease("worker-a", 7, ACTIVE, 0, 11))
        self.assertEqual(self.s.submit(self.req()), UNKNOWN_EFFECT_RECONCILE)
        self.assertEqual(self.r.sha, B)
        self.assertTrue(self.s.frozen)

    def test_10_ack_lost_after_remote_advanced(self):
        self.r.ack = "lost_after"
        self.assertEqual(self.s.submit(self.req()), UNKNOWN_EFFECT_RECONCILE)
        self.assertEqual(self.r.sha, B)

    def test_11_ack_lost_before_effect(self):
        self.r.ack = "lost_before"
        self.assertEqual(self.s.submit(self.req()), UNKNOWN_EFFECT_RECONCILE)
        self.assertEqual(self.r.sha, A)

    def test_12_unknown_advanced_needs_terminated_process(self):
        self.r.ack = "lost_after"
        self.s.submit(self.req())
        self.assertEqual(self.s.reconcile("t1", process_terminated=False),
                         "PROCESS_MAY_STILL_WRITE_REVIEW_REQUIRED")
        self.assertEqual(self.s.reconcile("t1", process_terminated=True),
                         "REMOTE_MATCHES_CANDIDATE_REVIEW_REQUIRED")

    def test_13_unknown_unchanged_no_auto_retry(self):
        self.r.ack = "lost_before"
        self.s.submit(self.req())
        self.assertEqual(self.s.reconcile("t1", process_terminated=True),
                         "REMOTE_UNCHANGED_REVIEW_REQUIRED")
        self.assertEqual(self.s.submit(self.req()), NOT_ADMITTED)
        self.assertEqual(self.r.pushes, 1)

    def test_14_pending_unknown_blocks_other_work(self):
        self.r.ack = "lost_after"
        self.s.submit(self.req())
        self.assertEqual(self.s.submit(self.req(key="t2", expected=B, candidate=C)),
                         NOT_ADMITTED)

    def test_15_protected_main_never_allowlisted(self):
        self.assertEqual(self.s.submit(self.req(ref="refs/heads/main")), NOT_ADMITTED)
        self.assertEqual(self.r.pushes, 0)

    def test_16_wrong_repository_denied(self):
        self.assertEqual(self.s.submit(self.req(repo="wrong/repo")), NOT_ADMITTED)

    def test_17_malformed_expected_denied(self):
        self.assertEqual(self.s.submit(self.req(expected="A")), NOT_ADMITTED)

    def test_18_remote_sha_mismatch_without_push(self):
        self.r.sha = C
        self.assertEqual(self.s.submit(self.req()), DENIED_STALE)
        self.assertEqual(self.r.pushes, 0)

    def test_19_competing_ref_advance_during_push(self):
        self.r.on_push = lambda: setattr(self.r, "sha", C)
        self.assertEqual(self.s.submit(self.req()), DENIED_STALE)
        self.assertEqual(self.r.sha, C)

    def test_20_remote_readback_unavailable_after_push(self):
        self.r.on_push = lambda: setattr(self.r, "read_fail", True)
        self.assertEqual(self.s.submit(self.req()), UNKNOWN_EFFECT_RECONCILE)

    def test_21_provider_unavailable_after_push(self):
        self.r.on_push = lambda: setattr(self.p, "fail", True)
        self.assertEqual(self.s.submit(self.req()), UNKNOWN_EFFECT_RECONCILE)

    def test_22_same_key_not_replayed_even_if_committed(self):
        self.assertEqual(self.s.submit(self.req()), COMMITTED_READBACK)
        self.assertEqual(self.s.submit(self.req()), NOT_ADMITTED)
        self.assertEqual(self.r.pushes, 1)

    def test_23_unknown_survives_fixture_sink_recreation(self):
        shared = {}
        self.s = Sink(self.p, self.r, shared)
        self.r.ack = "lost_after"
        self.s.submit(self.req())
        restarted = Sink(self.p, self.r, shared)
        self.assertEqual(restarted.submit(self.req()), NOT_ADMITTED)
        self.assertEqual(restarted.reconcile("t1", process_terminated=True),
                         "REMOTE_MATCHES_CANDIDATE_REVIEW_REQUIRED")

    def test_24_remote_conflict_on_reconcile(self):
        self.r.ack = "lost_before"
        self.s.submit(self.req())
        self.r.sha = C
        self.assertEqual(self.s.reconcile("t1", process_terminated=True),
                         "REMOTE_CONFLICT_REVIEW_REQUIRED")

    def test_25_reconcile_fail_closed_on_provider_outage(self):
        self.r.ack = "lost_after"
        self.s.submit(self.req())
        self.p.fail = True
        self.assertEqual(self.s.reconcile("t1", process_terminated=True),
                         "READBACK_UNAVAILABLE_REVIEW_REQUIRED")

    def test_26_invalid_boolean_epoch_denied(self):
        self.assertEqual(self.s.submit(self.req(epoch=True)), NOT_ADMITTED)

    def test_27_unexpected_provider_revision_change(self):
        self.p.on_observe = lambda n, p: setattr(
            p, "lease", Lease("worker-a", 7, ACTIVE, 30, 11)) if n == 2 else None
        self.assertEqual(self.s.submit(self.req()), DENIED_STALE)

    def test_28_no_credential_exclusivity_or_global_atomicity_claim(self):
        report = verdict()
        self.assertFalse(report["credential_exclusivity_verified"])
        self.assertFalse(report["mid_push_expiry_fenced"])
        self.assertFalse(report["cross_store_atomicity_proven"])
        self.assertFalse(report["production_authority"])

    def test_29_readback_conflict_after_apparent_success(self):
        original = self.r.push_cas
        def changed(expected, candidate):
            answer = original(expected, candidate)
            self.r.sha = C
            return answer
        self.r.push_cas = changed
        self.assertEqual(self.s.submit(self.req()), UNKNOWN_EFFECT_RECONCILE)

    def test_30_successful_readback_not_production_admission(self):
        self.assertEqual(self.s.submit(self.req()), COMMITTED_READBACK)
        self.assertFalse(verdict()["production_authority"])
        self.assertTrue(verdict()["manual_lab_only"])

    def test_31_unknown_restart_blocks_different_key(self):
        shared = {}
        first = Sink(self.p, self.r, shared)
        self.r.ack = "lost_after"
        self.assertEqual(first.submit(self.req()), UNKNOWN_EFFECT_RECONCILE)
        restarted = Sink(self.p, self.r, shared)
        self.assertTrue(restarted.frozen)
        self.assertEqual(restarted.submit(self.req(key="t2", expected=B, candidate=C)),
                         NOT_ADMITTED)
        self.assertEqual(self.r.pushes, 1)

    def test_32_concurrent_requests_serialized(self):
        entered, release = threading.Event(), threading.Event()
        output = []
        def stall():
            entered.set()
            release.wait(2)
        self.r.on_push = stall
        thread = threading.Thread(target=lambda: output.append(self.s.submit(self.req())))
        thread.start()
        try:
            self.assertTrue(entered.wait(2))
            self.assertEqual(self.s.submit(self.req(key="t2")), NOT_ADMITTED)
        finally:
            release.set()
            thread.join(3)
        self.assertEqual(output, [COMMITTED_READBACK])
        self.assertEqual(self.r.pushes, 1)


def verdict():
    return {
        "schema": "vf604-exclusive-sink-offline.v1",
        "manual_lab_only": True,
        "synthetic_provider_and_git_only": True,
        "production_authority": False,
        "credential_exclusivity_verified": False,
        "mid_push_expiry_fenced": False,
        "cross_store_atomicity_proven": False,
        "production_effects": 0,
        "network_git_writes": 0,
        "paid_api_calls": 0,
        "unknown_auto_replays": 0,
        "canonical_authority_owner": "#604",
        "consumer_issue": "#612",
        "states": [NOT_ADMITTED, PENDING_CUTOVER, ACTIVE,
                   FROZEN_PROVIDER_UNKNOWN, UNKNOWN_EFFECT_RECONCILE,
                   COMMITTED_READBACK, DENIED_STALE],
    }


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("selftest", "verify"):
        print("OFFLINE ONLY: selftest | verify", file=sys.stderr)
        return 2
    if sys.argv[1] == "selftest":
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        output = StringIO()
        result = unittest.TextTestRunner(stream=output, verbosity=1).run(suite)
        if not result.wasSuccessful():
            print(output.getvalue(), file=sys.stderr)
            return 1
        print(json.dumps(dict(verdict(), status="PASS_OFFLINE",
                              tests=result.testsRun), sort_keys=True))
    else:
        print(json.dumps(dict(verdict(), status="DESIGN_ONLY_NOT_ADMITTED"),
                         sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
