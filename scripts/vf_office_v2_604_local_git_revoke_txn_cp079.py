#!/usr/bin/env python3
"""CP079: a disposable SQLite/real-local-Git test of revocation/admission ordering.

This is NOT an etcd, GitHub, remote-CAS, OS-UID, or source-execution sandbox.
Accepted invocation: selftest only. Creates short-lived local fixtures under /tmp.
No external credentials, network requests, remote Git refs, or host paths.
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import contextmanager
from pathlib import Path

SCHEMA = 'vf604.cp079.local-git-revoke-txn.lab.v1'
REF = 'refs/heads/vf604-cp079-disposable'
SCOPE = {'task': 'cp079-fixed-task', 'host': 'cp079-fixed-host',
         'gpu': 'NO_GPU', 'ref': REF}
TERMINAL = ('DENIED', 'VERIFIED_EFFECT', 'VERIFIED_NO_EFFECT')
GIT = '/usr/bin/git'


class Refuse(Exception):
    """Expected deny / freeze; fail closed rather than retry an ambiguous effect."""


def need(condition: bool, reason: str) -> None:
    if not condition:
        raise Refuse(reason)


class Fixture:
    """One credential-free per-test root: real SQLite transaction and local bare Git."""

    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix='vf604-cp079-', dir='/tmp'))
        self.root.chmod(0o700)
        (self.root / '.vf604-cp079-disposable').write_text('local-only\n')
        self.repo = self.root / 'local.git'
        self.dbfile = self.root / 'authority.sqlite3'
        self._git_raw('init', '--quiet', '--bare', str(self.repo))
        self.initial = self._commit(b'CP079_INITIAL_LOCAL_BYTES\n')
        self.candidate = self._commit(b'CP079_CANDIDATE_LOCAL_BYTES\n', self.initial)
        self.third_party = self._commit(b'CP079_THIRD_PARTY_LOCAL_BYTES\n', self.initial)
        self.git('update-ref', REF, self.initial)
        with self.tx() as db:
            db.execute('CREATE TABLE issuer ('
                       'id INTEGER PRIMARY KEY CHECK(id=1), epoch INTEGER NOT NULL, '
                       'revoke_requested INTEGER NOT NULL, revoke_effective INTEGER NOT NULL, '
                       'task TEXT NOT NULL, host TEXT NOT NULL, gpu TEXT NOT NULL, '
                       'ref TEXT NOT NULL)')
            db.execute('INSERT INTO issuer VALUES(1,7,0,0,?,?,?,?)',
                       (SCOPE['task'], SCOPE['host'], SCOPE['gpu'], REF))
            db.execute('CREATE TABLE intents ('
                       'id TEXT PRIMARY KEY, epoch INTEGER NOT NULL, phase TEXT NOT NULL, '
                       'old_oid TEXT NOT NULL, new_oid TEXT NOT NULL, '
                       'attempts INTEGER NOT NULL DEFAULT 0, effects INTEGER NOT NULL DEFAULT 0)')

    def close(self) -> None:
        need(self.root.is_dir() and self.root.parent == Path('/tmp')
             and self.root.name.startswith('vf604-cp079-')
             and (self.root / '.vf604-cp079-disposable').is_file(),
             'DISPOSABLE_ROOT_GUARD')
        shutil.rmtree(self.root)

    def _git_raw(self, *args: str, stdin: bytes | None = None,
                 check: bool = True) -> str | None:
        # Deliberately pass no inherited tokens, SSH agents, hooks or user config.
        env = {'PATH': '/usr/bin:/bin', 'HOME': str(self.root), 'LANG': 'C',
               'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
               'GIT_TERMINAL_PROMPT': '0', 'GIT_ALLOW_PROTOCOL': '',
               'GIT_AUTHOR_NAME': 'CP079 local lab',
               'GIT_AUTHOR_EMAIL': 'cp079@example.invalid',
               'GIT_COMMITTER_NAME': 'CP079 local lab',
               'GIT_COMMITTER_EMAIL': 'cp079@example.invalid'}
        p = subprocess.run([GIT, *args], input=stdin, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=8, env=env)
        if check:
            need(p.returncode == 0, 'LOCAL_GIT_COMMAND_FAILED_' +
                 str(p.returncode) + '_' + p.stderr.decode('utf-8', 'replace')[:160])
        return p.stdout.decode('utf-8').strip() if p.returncode == 0 else None

    def git(self, *args: str, stdin: bytes | None = None,
            check: bool = True) -> str | None:
        return self._git_raw('--git-dir', str(self.repo), *args, stdin=stdin,
                             check=check)

    def _commit(self, payload: bytes, parent: str | None = None) -> str:
        blob = self.git('hash-object', '-w', '--stdin', stdin=payload)
        tree = self.git('mktree', stdin=('100644 blob ' + blob + '\tproof.txt\n').encode())
        argv = ['commit-tree', tree]
        if parent is not None:
            argv += ['-p', parent]
        commit = self.git(*argv, stdin=b'CP079 disposable local commit\n')
        need(len(commit or '') == 40, 'INVALID_LOCAL_COMMIT_ID')
        return commit

    @contextmanager
    def tx(self):
        conn = sqlite3.connect(str(self.dbfile), isolation_level=None, timeout=5)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=FULL')
        conn.execute('PRAGMA busy_timeout=5000')
        conn.execute('BEGIN IMMEDIATE')
        try:
            yield conn
            conn.execute('COMMIT')
        except BaseException:
            conn.execute('ROLLBACK')
            raise
        finally:
            conn.close()

    def snapshot(self) -> dict:
        with self.tx() as db:
            i = db.execute('SELECT epoch,revoke_requested,revoke_effective,task,host,gpu,ref '
                           'FROM issuer WHERE id=1').fetchone()
            intents = db.execute('SELECT id,epoch,phase,old_oid,new_oid,attempts,effects '
                                 'FROM intents ORDER BY id').fetchall()
        return {'epoch': i[0], 'requested': bool(i[1]), 'effective': bool(i[2]),
                'task': i[3], 'host': i[4], 'gpu': i[5], 'ref': i[6],
                'intents': [{'id': r[0], 'epoch': r[1], 'phase': r[2],
                             'old_oid': r[3], 'new_oid': r[4],
                             'attempts': r[5], 'effects': r[6]} for r in intents]}

    def tip(self) -> str:
        return self.git('rev-parse', REF)

    def prepare(self, intent: str = 'intent-1', *, epoch: int = 7,
                scope: dict | None = None, expected: str | None = None) -> None:
        claim = SCOPE if scope is None else scope
        need(type(claim) is dict and claim == SCOPE, 'SCOPE_NOT_EXACT')
        expected = self.initial if expected is None else expected
        need(expected == self.initial, 'EXPECTED_OLD_OID_NOT_PINNED')
        need(isinstance(intent, str) and intent and len(intent) < 60,
             'INVALID_INTENT_ID')
        with self.tx() as db:
            gen, requested, effective, task, host, gpu, ref = db.execute(
                'SELECT epoch,revoke_requested,revoke_effective,task,host,gpu,ref '
                'FROM issuer WHERE id=1').fetchone()
            need(epoch == gen and not requested and not effective,
                 'OWNER_EPOCH_CLOSED_OR_REVOKED')
            need((task, host, gpu, ref) == tuple(SCOPE.values()), 'ISSUER_SCOPE_CHANGED')
            # A canonical resource reservation, not merely an intent-id check.
            active = db.execute('SELECT count(*) FROM intents WHERE phase NOT IN '
                                '(\'DENIED\',\'VERIFIED_EFFECT\',\'VERIFIED_NO_EFFECT\')').fetchone()[0]
            need(active == 0, 'OVERLAPPING_RESOURCE_RESERVED')
            db.execute('INSERT INTO intents VALUES(?,?,?,?,?,0,0)',
                       (intent, gen, 'PREPARED', expected, self.candidate))

    def admit(self, intent: str = 'intent-1') -> None:
        with self.tx() as db:
            epoch, requested, effective = db.execute(
                'SELECT epoch,revoke_requested,revoke_effective FROM issuer WHERE id=1').fetchone()
            row = db.execute('SELECT epoch,phase,old_oid,new_oid FROM intents '
                             'WHERE id=?', (intent,)).fetchone()
            need(row is not None and row[0] == epoch and row[1] == 'PREPARED'
                 and not requested and not effective and row[2] == self.initial
                 and row[3] == self.candidate, 'ATOMIC_ADMISSION_REFUSED')
            db.execute('UPDATE intents SET phase=\'COMMIT_ADMITTED\' WHERE id=?', (intent,))

    def request_revoke(self) -> None:
        with self.tx() as db:
            epoch, effective = db.execute(
                'SELECT epoch,revoke_effective FROM issuer WHERE id=1').fetchone()
            need(not effective, 'GENERATION_ALREADY_EFFECTIVE_REVOKED')
            db.execute('UPDATE issuer SET revoke_requested=1 WHERE id=1')
            # Pending but not admitted work has never obtained effect permission.
            db.execute('UPDATE intents SET phase=\'DENIED\' WHERE epoch=? '
                       'AND phase=\'PREPARED\'', (epoch,))

    def start_send(self, intent: str = 'intent-1') -> None:
        with self.tx() as db:
            row = db.execute('SELECT epoch,phase,attempts FROM intents WHERE id=?',
                             (intent,)).fetchone()
            epoch, effective = db.execute('SELECT epoch,revoke_effective FROM issuer '
                                          'WHERE id=1').fetchone()
            # Under Option A a pre-admitted effect may start after the revoke
            # REQUEST, but NEVER after REVOKED_EFFECTIVE has been acknowledged.
            need(row is not None and row[0] == epoch and not effective
                 and row[1] == 'COMMIT_ADMITTED' and row[2] == 0,
                 'SEND_NOT_ALLOWED_OR_REPLAY')
            db.execute('UPDATE intents SET phase=\'SEND_STARTED\', attempts=1 '
                       'WHERE id=?', (intent,))

    def deliver_local_git(self, intent: str = 'intent-1') -> bool:
        with self.tx() as db:
            row = db.execute('SELECT phase,attempts,old_oid,new_oid FROM intents '
                             'WHERE id=?', (intent,)).fetchone()
            need(row is not None and row[0] == 'SEND_STARTED' and row[1] == 1,
                 'NO_UNAMBIGUOUS_SEND_STARTED')
            old_oid, new_oid = row[2], row[3]
            # Only one thread/process can cross the native-Git effect boundary.
            # Durable pre-call marker also forbids blind replay after a crash.
            db.execute('UPDATE intents SET phase=\'GIT_CALL_STARTED\' WHERE id=?',
                       (intent,))
        # ONLY a synchronous, disposable, credential-free native local Git CAS.
        outcome = self.git('update-ref', REF, new_oid, old_oid, check=False)
        # git update-ref has no stdout even on success; inspect exact ref.
        if self.tip() == new_oid and outcome is not None:
            with self.tx() as db:
                row = db.execute('SELECT phase,effects FROM intents WHERE id=?',
                                 (intent,)).fetchone()
                need(row == ('GIT_CALL_STARTED', 0), 'INVALID_TERMINAL_LOCAL_EFFECT')
                db.execute('UPDATE intents SET phase=\'VERIFIED_EFFECT\', '
                           'effects=1 WHERE id=?', (intent,))
            return True
        with self.tx() as db:
            db.execute('UPDATE intents SET phase=\'FROZEN_UNKNOWN\' WHERE '
                       'id=? AND phase=\'GIT_CALL_STARTED\'', (intent,))
        return False

    def freeze_unknown(self, intent: str = 'intent-1') -> None:
        with self.tx() as db:
            row = db.execute('SELECT phase,attempts FROM intents WHERE id=?',
                             (intent,)).fetchone()
            need(row == ('SEND_STARTED', 1), 'UNKNOWN_REQUIRES_SENT_ATTEMPT')
            db.execute('UPDATE intents SET phase=\'FROZEN_UNKNOWN\' WHERE id=?',
                       (intent,))

    def recover_after_crash(self) -> None:
        # The absence of a success receipt cannot prove that a Git operation
        # did not reach the destination. This is intentionally conservative.
        with self.tx() as db:
            db.execute('UPDATE intents SET phase=\'FROZEN_UNKNOWN\' '
                       'WHERE phase IN (\'SEND_STARTED\',\'GIT_CALL_STARTED\')')

    def finish_revoke(self) -> None:
        with self.tx() as db:
            epoch, requested, effective = db.execute(
                'SELECT epoch,revoke_requested,revoke_effective FROM issuer WHERE id=1').fetchone()
            need(requested and not effective, 'NO_COMMITTED_REVOKE_TO_FINALIZE')
            pending = db.execute('SELECT count(*) FROM intents WHERE epoch=? '
                                 'AND phase NOT IN (\'DENIED\',\'VERIFIED_EFFECT\','
                                 '\'VERIFIED_NO_EFFECT\')', (epoch,)).fetchone()[0]
            need(pending == 0, 'REVOKE_DRAINING_OR_UNKNOWN')
            db.execute('UPDATE issuer SET revoke_effective=1 WHERE id=1')

    def successor(self) -> None:
        with self.tx() as db:
            epoch, effective = db.execute('SELECT epoch,revoke_effective '
                                          'FROM issuer WHERE id=1').fetchone()
            pending = db.execute('SELECT count(*) FROM intents WHERE '
                                 'phase NOT IN (\'DENIED\',\'VERIFIED_EFFECT\','
                                 '\'VERIFIED_NO_EFFECT\')').fetchone()[0]
            need(effective and pending == 0, 'UNRESOLVED_RESOURCE_PREVENTS_SUCCESSOR')
            db.execute('UPDATE issuer SET epoch=?,revoke_requested=0,'
                       'revoke_effective=0 WHERE id=1', (epoch + 1,))


def must_refuse(callable_obj, reason: str) -> None:
    try:
        callable_obj()
    except Refuse:
        return
    raise AssertionError('MISSING_DENIAL_' + reason)


class Tests(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()
        self.addCleanup(self.f.close)

    def test_01_revoke_before_prepare_or_admission(self):
        self.f.request_revoke()
        must_refuse(self.f.prepare, 'prepare_after_revoke')
        must_refuse(self.f.admit, 'admit_without_prepare')
        self.f.finish_revoke()
        self.assertEqual(self.f.tip(), self.f.initial)
        self.assertTrue(self.f.snapshot()['effective'])

    def test_02_revoke_between_prepare_and_admit(self):
        self.f.prepare()
        self.f.request_revoke()
        must_refuse(self.f.admit, 'admit_after_revoke')
        self.f.finish_revoke()
        self.assertEqual(self.f.snapshot()['intents'][0]['phase'], 'DENIED')
        self.assertEqual(self.f.tip(), self.f.initial)

    def test_03_pre_admitted_effect_after_committed_revoke_option_a(self):
        self.f.prepare()
        self.f.admit()
        self.f.request_revoke()
        must_refuse(self.f.finish_revoke, 'premature_ack')
        self.f.start_send()
        self.assertTrue(self.f.deliver_local_git())
        self.assertEqual(self.f.tip(), self.f.candidate)
        self.f.finish_revoke()
        self.assertTrue(self.f.snapshot()['effective'])
        must_refuse(self.f.start_send, 'post_effective_replay')

    def test_04_unknown_never_ack_or_replay_or_successor(self):
        self.f.prepare()
        self.f.admit()
        self.f.start_send()
        self.f.freeze_unknown()
        self.f.request_revoke()
        must_refuse(self.f.finish_revoke, 'unknown_effective_ack')
        must_refuse(self.f.successor, 'unknown_successor')
        must_refuse(self.f.start_send, 'unknown_retry')
        must_refuse(self.f.deliver_local_git, 'unknown_local_replay')
        self.assertEqual(self.f.snapshot()['intents'][0]['attempts'], 1)

    def test_05_late_wire_arrival_after_unknown_never_false_acks(self):
        self.f.prepare()
        self.f.admit()
        self.f.start_send()
        self.f.freeze_unknown()
        self.f.request_revoke()
        self.assertEqual(self.f.tip(), self.f.initial)  # snapshot alone proves little
        must_refuse(self.f.finish_revoke, 'ref_old_not_no_effect')
        # Simulate a previously sent request arriving late. NOT a second send.
        self.f.git('update-ref', REF, self.f.candidate, self.f.initial)
        self.assertEqual(self.f.tip(), self.f.candidate)
        must_refuse(self.f.finish_revoke, 'ref_new_not_proven_authorship')
        self.assertFalse(self.f.snapshot()['effective'])

    def test_06_ref_cas_competitor_fail_closed(self):
        self.f.prepare()
        self.f.admit()
        self.f.start_send()
        self.f.git('update-ref', REF, self.f.third_party, self.f.initial)
        self.assertFalse(self.f.deliver_local_git())
        self.assertEqual(self.f.tip(), self.f.third_party)
        self.assertEqual(self.f.snapshot()['intents'][0]['phase'], 'FROZEN_UNKNOWN')
        self.f.request_revoke()
        must_refuse(self.f.finish_revoke, 'competing_ref_unknown')

    def test_07_scope_mismatch_and_expected_old_oid_fail_closed(self):
        for bad in [{'task': 'other', 'host': SCOPE['host'],
                     'gpu': SCOPE['gpu'], 'ref': REF},
                    {'task': SCOPE['task'], 'host': SCOPE['host'],
                     'gpu': 'gpu0', 'ref': REF},
                    {'task': SCOPE['task'], 'host': SCOPE['host'],
                     'gpu': SCOPE['gpu'], 'ref': 'refs/heads/main'}]:
            must_refuse(lambda bad=bad: self.f.prepare(scope=bad), 'bad_scope')
        must_refuse(lambda: self.f.prepare(expected=self.f.third_party), 'wrong_old_oid')
        self.assertEqual(self.f.snapshot()['intents'], [])

    def test_08_reservation_and_replay_denial(self):
        self.f.prepare()
        must_refuse(lambda: self.f.prepare('another-intent'), 'duplicate_reservation')
        self.f.admit()
        must_refuse(self.f.admit, 'admission_replay')
        self.f.start_send()
        must_refuse(self.f.start_send, 'dispatch_replay')
        self.assertTrue(self.f.deliver_local_git())
        must_refuse(self.f.deliver_local_git, 'effect_replay')
        self.assertEqual(self.f.snapshot()['intents'][0]['effects'], 1)

    def test_09_restart_keeps_durable_unknown(self):
        self.f.prepare()
        self.f.admit()
        self.f.start_send()
        self.f.freeze_unknown()
        # Every operation opens a fresh real sqlite connection, simulating restart.
        snap = self.f.snapshot()
        self.assertEqual(snap['intents'][0]['phase'], 'FROZEN_UNKNOWN')
        must_refuse(self.f.start_send, 'durable_unknown_replay')

    def test_10_closed_generation_cannot_reopen_old_epoch(self):
        self.f.request_revoke()
        self.f.finish_revoke()
        self.f.successor()
        self.assertEqual(self.f.snapshot()['epoch'], 8)
        must_refuse(lambda: self.f.prepare(epoch=7), 'stale_epoch')

    def test_11_simultaneous_admit_and_revoke_transactions(self):
        # This is an actual two-thread SQLite BEGIN IMMEDIATE race, not just
        # a pre-recorded abstract trace. Each thread has its own DB connection.
        self.f.prepare()
        barrier = threading.Barrier(3)
        outcomes = []
        lock = threading.Lock()

        def go(name, fn):
            barrier.wait(timeout=3)
            try:
                fn()
                result = 'ok'
            except Refuse:
                result = 'denied'
            with lock:
                outcomes.append((name, result))

        a = threading.Thread(target=go, args=('admit', self.f.admit))
        b = threading.Thread(target=go, args=('revoke', self.f.request_revoke))
        a.start(); b.start(); barrier.wait(timeout=3)
        a.join(timeout=5); b.join(timeout=5)
        self.assertFalse(a.is_alive() or b.is_alive())
        self.assertIn(('revoke', 'ok'), outcomes)
        snap = self.f.snapshot()
        self.assertTrue(snap['requested'])
        if ('admit', 'ok') in outcomes:
            self.assertEqual(snap['intents'][0]['phase'], 'COMMIT_ADMITTED')
            must_refuse(self.f.finish_revoke, 'admit_wins_must_drain')
        else:
            self.assertIn(('admit', 'denied'), outcomes)
            self.assertEqual(snap['intents'][0]['phase'], 'DENIED')
            self.f.finish_revoke()

    def test_12_legacy_unguarded_last_read_is_observably_unsafe(self):
        self.assertFalse(self.f.snapshot()['requested'])
        # The deliberately UNSAFE legacy native Git sink reads provider before
        # the issuer commits revocation, and never does atomic COMMIT_ADMIT.
        self.f.request_revoke()
        self.f.finish_revoke()
        self.assertTrue(self.f.snapshot()['effective'])
        # NEVER permitted for the corrected path; isolated native local Git only.
        self.f.git('update-ref', REF, self.f.candidate, self.f.initial)
        self.assertEqual(self.f.tip(), self.f.candidate)
        self.assertTrue(self.f.snapshot()['effective'])


    def test_13_duplicate_concurrent_delivery_is_serialized(self):
        self.f.prepare()
        self.f.admit()
        self.f.start_send()
        barrier = threading.Barrier(3)
        results = []
        lock = threading.Lock()

        def issue_local_git():
            barrier.wait(timeout=3)
            try:
                outcome = 'effect' if self.f.deliver_local_git() else 'unknown'
            except Refuse:
                outcome = 'denied'
            with lock:
                results.append(outcome)

        threads = [threading.Thread(target=issue_local_git) for _ in range(2)]
        for thread in threads:
            thread.start()
        barrier.wait(timeout=3)
        for thread in threads:
            thread.join(timeout=5)
        self.assertEqual(sorted(results), ['denied', 'effect'])
        self.assertEqual(self.f.tip(), self.f.candidate)
        self.assertEqual(self.f.snapshot()['intents'][0]['effects'], 1)
        self.assertEqual(self.f.snapshot()['intents'][0]['attempts'], 1)

    def test_14_crash_recovery_freezes_pre_git_and_during_git_phases(self):
        self.f.prepare()
        self.f.admit()
        self.f.start_send()
        # Simulate a process death just before native local Git call; WAL
        # survives but absence of effect receipt is not enough for a replay.
        with self.f.tx() as db:
            db.execute('UPDATE intents SET phase=\'GIT_CALL_STARTED\' WHERE id=\'intent-1\'')
        self.f.recover_after_crash()
        snap = self.f.snapshot()['intents'][0]
        self.assertEqual(snap['phase'], 'FROZEN_UNKNOWN')
        must_refuse(self.f.deliver_local_git, 'crash_effect_replay')
        must_refuse(self.f.start_send, 'crash_send_replay')
        self.f.request_revoke()
        must_refuse(self.f.finish_revoke, 'crash_unknown_effective')
        self.assertEqual(self.f.tip(), self.f.initial)

    def test_15_successor_only_after_proven_terminal(self):
        self.f.prepare()
        self.f.admit()
        self.f.request_revoke()
        must_refuse(self.f.successor, 'successor_while_draining')
        self.f.start_send()
        self.assertTrue(self.f.deliver_local_git())
        self.f.finish_revoke()
        self.f.successor()
        self.assertEqual(self.f.snapshot()['epoch'], 8)
        self.assertFalse(self.f.snapshot()['requested'])
        must_refuse(lambda: self.f.prepare(epoch=7), 'retired_epoch')

    def test_16_no_git_remote_and_no_caller_selected_command(self):
        self.assertEqual(self.f.git('remote'), '')
        self.assertEqual(self.f.tip(), self.f.initial)
        self.assertEqual(main(['not-a-command']), 2)



def selftest() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=1).run(suite)
    if not result.wasSuccessful() or result.testsRun != 16:
        return 1
    print(json.dumps({
        'schema': SCHEMA,
        'status': 'PASS_DISPOSABLE_NATIVE_LOCAL_GIT_SQLITE_ONLY',
        'test_count': result.testsRun,
        'known_unsafe_legacy_witness': 'REPRODUCED_LOCAL_ONLY',
        'actual_sqlite_write_transactions': True,
        'actual_native_local_git_compare_and_swap': True,
        'real_etcd_provider': False,
        'real_github_api_or_credentials': False,
        'real_os_uid_separation': False,
        'model_authored_cp058_source_executed': False,
        'production_authority': False,
        'security_admission': 'RED',
    }, sort_keys=True))
    return 0


def main(argv: list[str]) -> int:
    if argv != ['selftest']:
        print('DENIED: only selftest in disposable /tmp fixture is permitted',
              file=sys.stderr)
        return 2
    return selftest()


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
