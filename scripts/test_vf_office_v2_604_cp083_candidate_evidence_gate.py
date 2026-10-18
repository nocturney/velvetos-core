#!/usr/bin/env python3
"""Synthetic format/mutation tests ONLY; no runtime full-chain or QA claim."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import stat
import sys
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import vf_office_v2_604_cp083_candidate_evidence_gate as gate


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def jsonbytes(obj, *, lf=False):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode() + (
        b"\n" if lf else b"")


class CandidateEvidenceNegativeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="vf604-cp083-evidence-synth-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.source = self.base / "synthetic-candidate.py"
        self.source.write_bytes(b"# harmless synthetic source for unit tests\n")
        self.source_sha = sha(self.source.read_bytes())
        patch1 = mock.patch.object(gate, "SOURCE", self.source)
        patch2 = mock.patch.object(gate, "SOURCE_SHA", self.source_sha)
        patch1.start()
        patch2.start()
        self.addCleanup(patch2.stop)
        self.addCleanup(patch1.stop)
        self.manifest = {
            "schema": gate.SCHEMA,
            "security_admission": "RED",
            "production_authority": False,
            "real_protected_core_issuer": False,
            "independent_security_review_completed": False,
            "remote_github_writes": 0,
            "candidate_commit_sha": gate.SOURCE_COMMIT,
            "candidate_source_sha256": self.source_sha,
            "runs": [],
        }
        for index in (1, 2):
            run = "run-" + str(index)
            folder = self.base / run
            folder.mkdir()
            receipt = self._receipt(index)
            guest = self._guest(run, index)
            r_path = folder / "receipt.jsonl"
            g_path = folder / "guest.json"
            r_path.write_bytes(jsonbytes(receipt, lf=True))
            g_path.write_bytes(jsonbytes(guest))
            self.manifest["runs"].append({
                "run_id": run,
                "receipt_path": f"{run}/receipt.jsonl",
                "receipt_sha256": sha(r_path.read_bytes()),
                "guest_path": f"{run}/guest.json",
                "guest_sha256": sha(g_path.read_bytes()),
            })
        self.manifest_path = self.base / "manifest.json"
        self._save_manifest()

    def _receipt(self, index):
        labels = sorted(gate.REQUIRED_CASES) + [
            "synthetic_extra_check_" + str(i) for i in range(
                59 - len(gate.REQUIRED_CASES))]
        obj = {
            "schema": gate.RUN_SCHEMA,
            "status": "PASS_CP083_TEST_ONLY",
            "checks": labels,
            "check_count": len(labels),
            "fixture_prefix_sha256": sha(f"synthetic-new-provider-{index}".encode()),
            "security_admission": "RED",
            "real_external_github_writes": 0,
        }
        obj.update({key: True for key in gate.TRUE_FLAGS})
        obj.update({key: False for key in gate.FALSE_FLAGS})
        return obj

    def _guest(self, run, index):
        return {
            "schema": gate.GUEST_SCHEMA,
            "run_id": run,
            "platform": "linux",
            "architecture": "aarch64",
            "controller_uid": 0,
            "sink_uid": 62001,
            "worker_uid": 62002,
            "attacker_uid": 62004,
            "candidate_source_sha256": self.source_sha,
            "no_host_home_mounts_observed": True,
            "no_ambient_credentials_observed": True,
            "mountinfo_sha256": sha(f"synthetic mountinfo {index}".encode()),
            "etcd_sha256": gate.PIN_ETCD,
            "etcdctl_sha256": gate.PIN_CTL,
            "etcd_version": "3.6.15",
            "kernel_uid_observation_method": "getresuid+SO_PEERCRED",
        }

    def _save_manifest(self):
        self.manifest_path.write_bytes(jsonbytes(self.manifest))

    def _change(self, index, kind, mutate):
        entry = self.manifest["runs"][index]
        relkey = kind + "_path"
        shkey = kind + "_sha256"
        artifact = self.base / entry[relkey]
        old = json.loads(artifact.read_bytes())
        mutate(old)
        new = jsonbytes(old, lf=(kind == "receipt"))
        artifact.write_bytes(new)
        entry[shkey] = sha(new)
        self._save_manifest()

    def _skip_if_directory_open_unavailable(self):
        """File opens need a real POSIX directory flag. Decoder cases do not."""
        flag = getattr(os, "O_DIRECTORY", 0)
        if os.name != "posix" or type(flag) is not int or flag == 0:
            print("SKIP_NON_POSIX", flush=True)
            self.skipTest("SKIP_NON_POSIX")

    def assert_refused(self):
        self._skip_if_directory_open_unavailable()
        with self.assertRaises(gate.Refused):
            gate.verify(self.manifest_path)

    def test_01_synthetic_positive_format_only_never_security_pass(self):
        self._skip_if_directory_open_unavailable()
        result = gate.verify(self.manifest_path)
        self.assertEqual(result["status"],
                         "OFFLINE_BYTE_CONSISTENCY_ONLY_NOT_RUNTIME_QA")
        self.assertEqual(result["raw_receipt_files"], 2)
        self.assertEqual(result["security_admission"], "RED")
        self.assertFalse(result["independent_runtime_provenance_verified"])
        self.assertFalse(result["production_authority"])

    def test_02_missing_manifest_is_refused(self):
        self._skip_if_directory_open_unavailable()
        self.manifest_path.unlink()
        with self.assertRaises(OSError):
            gate.verify(self.manifest_path)

    def test_03_wrong_candidate_source_bytes_refused(self):
        self.source.write_bytes(b"changed synthetic candidate\n")
        self.assert_refused()

    def test_04_no_second_new_receipt_refused(self):
        self.manifest["runs"].pop()
        self._save_manifest()
        self.assert_refused()

    def test_05_identical_provider_prefix_with_rehashed_receipt_refused(self):
        first = json.loads((self.base / "run-1/receipt.jsonl").read_bytes())
        self._change(1, "receipt", lambda r: r.update(
            fixture_prefix_sha256=first["fixture_prefix_sha256"]))
        self.assert_refused()

    def test_06_historical_provider_with_rehashed_receipt_refused(self):
        old = sorted(gate.OLD_PROVIDER_PREFIXES)[0]
        self._change(0, "receipt", lambda r: r.update(fixture_prefix_sha256=old))
        self.assert_refused()

    def test_07_changed_receipt_bytes_without_hash_update_refused(self):
        path = self.base / "run-1/receipt.jsonl"
        path.write_bytes(path.read_bytes() + b" ")
        self.assert_refused()

    def test_08_rehashed_green_receipt_refused(self):
        self._change(0, "receipt", lambda r: r.update(security_admission="GREEN"))
        self.assert_refused()

    def test_09_rehashed_false_guest_no_host_mount_claim_refused(self):
        self._change(1, "guest", lambda g: g.update(
            no_host_home_mounts_observed=False))
        self.assert_refused()

    def test_10_duplicate_json_key_refused(self):
        path = self.base / "run-1/receipt.jsonl"
        raw = path.read_bytes().removesuffix(b"\n")
        altered = raw[:-1] + b',"status":"COMMITTED_READBACK"}\n'
        path.write_bytes(altered)
        self.manifest["runs"][0]["receipt_sha256"] = sha(altered)
        self._save_manifest()
        self.assert_refused()

    def test_11_unsafe_relative_parent_path_refused(self):
        self.manifest["runs"][0]["receipt_path"] = "../run-1/receipt.jsonl"
        self._save_manifest()
        self.assert_refused()

    def test_12_symlink_receipt_refused(self):
        link = self.base / "run-1/symlink.jsonl"
        try:
            link.symlink_to(self.base / "run-1/receipt.jsonl")
        except (OSError, NotImplementedError):
            # A Windows host without symlink permission cannot run this case.
            # Never hide a failure to create the same fixture on Linux/macOS.
            if sys.platform == "win32":
                self.skipTest("Windows symlink creation not permitted by OS")
            raise
        self.manifest["runs"][0]["receipt_path"] = "run-1/symlink.jsonl"
        self._save_manifest()
        self.assert_refused()

    def test_13_manifest_claim_of_independent_qa_refused(self):
        self.manifest["independent_security_review_completed"] = True
        self._save_manifest()
        self.assert_refused()

    def test_14_duplicate_run_id_refused(self):
        self.manifest["runs"][1]["run_id"] = "run-1"
        self._save_manifest()
        self.assert_refused()

    def test_15_guest_with_wrong_actual_uid_claim_refused(self):
        self._change(0, "guest", lambda g: g.update(worker_uid=0))
        self.assert_refused()

    def test_16_missing_fault_or_assertion_refused(self):
        def remove_mid(r):
            r["checks"].remove("mid_no_blind_retry")
            r["checks"].append("synthetic_wrong_untrusted_assertion")
        self._change(0, "receipt", remove_mid)
        self.assert_refused()

    def test_17_root_production_claim_refused(self):
        self.manifest["production_authority"] = True
        self._save_manifest()
        self.assert_refused()

    def test_18_oversized_input_refused(self):
        path = self.base / "run-1/guest.json"
        path.write_bytes(b" " * (16 * 1024 + 1))
        self.manifest["runs"][0]["guest_sha256"] = sha(path.read_bytes())
        self._save_manifest()
        self.assert_refused()

    def test_19_crlf_receipt_line_refused(self):
        self._skip_if_directory_open_unavailable()
        path = self.base / "run-1/receipt.jsonl"
        raw = path.read_bytes()
        self.assertTrue(raw.endswith(b"\n") and b"\r" not in raw)
        altered = raw.replace(b"\n", b"\r\n")
        self.assertTrue(altered.endswith(b"\r\n") and altered.count(b"\n") == 1)
        path.write_bytes(altered)
        self.manifest["runs"][0]["receipt_sha256"] = sha(altered)
        self._save_manifest()
        with self.assertRaises(gate.Refused) as caught:
            gate.verify(self.manifest_path)
        self.assertEqual(str(caught.exception), "RECEIPT_MUST_BE_ORIGINAL_ONE_LINE_LF")

    def test_20_cr_inside_json_refused(self):
        self._skip_if_directory_open_unavailable()
        path = self.base / "run-1/receipt.jsonl"
        raw = path.read_bytes()
        self.assertTrue(raw.startswith(b"{") and raw.endswith(b"\n") and b"\r" not in raw)
        altered = raw[:1] + b"\r" + raw[1:]
        self.assertEqual(altered.count(b"\n"), 1)
        self.assertTrue(altered.endswith(b"\n") and not altered.endswith(b"\r\n"))
        self.assertEqual(altered.count(b"\r"), 1)
        self.assertEqual(json.loads(altered.decode()), json.loads(raw.decode()))
        path.write_bytes(altered)
        self.manifest["runs"][0]["receipt_sha256"] = sha(altered)
        self._save_manifest()
        with self.assertRaises(gate.Refused) as caught:
            gate.verify(self.manifest_path)
        self.assertEqual(str(caught.exception), "RECEIPT_MUST_BE_ORIGINAL_ONE_LINE_LF")

    def test_21_hardlinked_receipt_alias_rejected(self):
        self._skip_if_directory_open_unavailable()
        # GAP_4 on an unfixed gate: nlink is unchecked, so a same-bytes alias verifies.
        receipt = self.base / "run-1" / "receipt.jsonl"
        alias = self.base / "run-1" / "receipt-alias.jsonl"
        os.link(receipt, alias)
        self.assertEqual(receipt.stat().st_ino, alias.stat().st_ino)
        self.assertGreater(receipt.stat().st_nlink, 1)
        with self.assertRaises(gate.Refused) as caught:
            gate.verify(self.manifest_path)
        self.assertEqual(str(caught.exception), "HARDLINK_ALIAS_REFUSED")

    def test_22_evidence_parent_swap_race_cannot_escape_root(self):
        self._skip_if_directory_open_unavailable()
        # GAP_3 on an unfixed gate: a parent swap between the path check and
        # open still feeds the outside inode when the bytes match.
        receipt = self.base / "run-1" / "receipt.jsonl"
        original_ino = receipt.stat().st_ino
        outside = self.base / "outside-evidence"
        outside.mkdir()
        for name in ("receipt.jsonl", "guest.json"):
            (outside / name).write_bytes((self.base / "run-1" / name).read_bytes())
        planted_ino = (outside / "receipt.jsonl").stat().st_ino
        self.assertNotEqual(planted_ino, original_ino)
        opened = {"inos": [], "swapped": False}
        real_open = os.open

        def opening(path, flags, mode=0o777, *, dir_fd=None):
            target = str(path)
            if (dir_fd is None and not opened["swapped"]
                    and target.endswith("run-1/receipt.jsonl")):
                held = self.base / "run-1.held"
                os.rename(self.base / "run-1", held)
                (self.base / "run-1").symlink_to(outside, target_is_directory=True)
                opened["swapped"] = True
            fd = real_open(path, flags, mode, dir_fd=dir_fd)
            try:
                info = os.fstat(fd)
            except OSError:
                return fd
            if (not opened["swapped"] and dir_fd is not None
                    and target == "run-1" and stat.S_ISDIR(info.st_mode)):
                held = self.base / "run-1.held"
                os.rename(self.base / "run-1", held)
                (self.base / "run-1").symlink_to(outside, target_is_directory=True)
                opened["swapped"] = True
            if stat.S_ISREG(info.st_mode) and target.endswith("receipt.jsonl"):
                opened["inos"].append(info.st_ino)
            return fd

        with mock.patch.object(gate.os, "open", opening):
            try:
                gate.verify(self.manifest_path)
            except gate.Refused:
                pass
        # A later refusal does not excuse having already opened the swapped inode.
        self.assertTrue(opened["swapped"])
        self.assertNotIn(planted_ino, opened["inos"])
        self.assertIn(original_ino, opened["inos"])

    def test_23_guest_manifest_cr_canonical_policy(self):
        self._skip_if_directory_open_unavailable()
        # CR is refused in guest and manifest JSON, same canonical rule as receipts.
        guest = self.base / "run-1" / "guest.json"
        raw = guest.read_bytes()
        altered = raw.replace(b"{", b"{\r", 1)
        self.assertEqual(json.loads(altered.decode()), json.loads(raw.decode()))
        guest.write_bytes(altered)
        self.manifest["runs"][0]["guest_sha256"] = sha(altered)
        self._save_manifest()
        with self.assertRaises(gate.Refused) as caught:
            gate.verify(self.manifest_path)
        self.assertEqual(str(caught.exception), "CR_IN_CANONICAL_JSON")
        guest.write_bytes(raw)
        self.manifest["runs"][0]["guest_sha256"] = sha(raw)
        self._save_manifest()
        manifest_raw = self.manifest_path.read_bytes()
        self.manifest_path.write_bytes(manifest_raw.replace(b"{", b"{\r", 1))
        with self.assertRaises(gate.Refused) as caught:
            gate.verify(self.manifest_path)
        self.assertEqual(str(caught.exception), "CR_IN_CANONICAL_JSON")

    def test_24_self_issued_two_receipts_not_accepted_as_host_attestation(self):
        self._skip_if_directory_open_unavailable()
        result = gate.verify(self.manifest_path)
        self.assertEqual(result["status"],
                         "OFFLINE_BYTE_CONSISTENCY_ONLY_NOT_RUNTIME_QA")
        self.assertEqual(result["security_admission"], "RED")
        self.assertIs(result["independent_runtime_provenance_verified"], False)
        self.assertEqual(result["host_attestation"], "REFUSED_UNSIGNED_SELF_ISSUED")
        with self.assertRaises(gate.Refused) as caught:
            gate.refuse_host_attestation(result)
        self.assertEqual(str(caught.exception),
                         "SELF_ISSUED_RECEIPTS_NOT_HOST_ATTESTATION")
        forged = dict(result, security_admission="GREEN")
        with self.assertRaises(gate.Refused) as caught:
            gate.refuse_host_attestation(forged)
        self.assertEqual(str(caught.exception), "NOT_HOST_ATTESTATION")

    def test_guest_and_manifest_cr_or_duplicate_keys_refused(self):
        # Same decoder as wire frames. Python's json.loads would accept these.
        samples = (
            (b'{"a":{"b":1,"b":2}}', "DUPLICATE_JSON_KEY"),
            (b'{"a":[{"b":1,"b":2}]}', "DUPLICATE_JSON_KEY"),
            (b'{"a":NaN}', "NON_FINITE_JSON"),
            (b'{"a":Infinity}', "NON_FINITE_JSON"),
            (b'{"a":-Infinity}', "NON_FINITE_JSON"),
            (b'{"a":1}{"b":2}', "INVALID_UTF8_OR_JSON"),
            (b"[1]", "JSON_OBJECT_REQUIRED"),
            (b'{"a":"\xff"}', "INVALID_UTF8_OR_JSON"),
            (b'{"a":1}\r\n', "CR_IN_CANONICAL_JSON"),
        )
        for raw, reason in samples:
            with self.subTest(reason=reason, raw=raw):
                with self.assertRaises(gate.Refused) as caught:
                    gate.decode(raw)
                self.assertEqual(str(caught.exception), reason)

    def test_guest_and_manifest_file_bytes_refused(self):
        self._skip_if_directory_open_unavailable()
        guest = self.base / "run-1" / "guest.json"
        original = json.loads(guest.read_bytes())
        pretty = json.dumps(original, indent=2).encode()
        self.assertIn(b"\n", pretty)
        self.assertNotIn(b"\r", pretty)
        guest.write_bytes(pretty)
        self.manifest["runs"][0]["guest_sha256"] = sha(pretty)
        self._save_manifest()
        result = gate.verify(self.manifest_path)
        self.assertEqual(result["status"],
                         "OFFLINE_BYTE_CONSISTENCY_ONLY_NOT_RUNTIME_QA")
        self.assertEqual(result["security_admission"], "RED")
        self.assertEqual(result["host_attestation"],
                         "REFUSED_UNSIGNED_SELF_ISSUED")

        def plant(path, mutated):
            path.write_bytes(mutated)
            return mutated

        guest_raw = guest.read_bytes()
        duplicated_guest = guest_raw[:-1] + b',"run_id":"run-1"}'
        self.assertEqual(
            json.loads(duplicated_guest.decode())["run_id"], "run-1")
        plant(guest, duplicated_guest)
        self.manifest["runs"][0]["guest_sha256"] = sha(duplicated_guest)
        self._save_manifest()
        with self.assertRaises(gate.Refused) as caught:
            gate.verify(self.manifest_path)
        self.assertEqual(str(caught.exception), "DUPLICATE_JSON_KEY")

        guest.write_bytes(guest_raw)
        self.manifest["runs"][0]["guest_sha256"] = sha(guest_raw)
        self._save_manifest()
        cr_guest = guest_raw.replace(b"{", b"{\r", 1)
        self.assertEqual(json.loads(cr_guest.decode()), json.loads(guest_raw.decode()))
        plant(guest, cr_guest)
        self.manifest["runs"][0]["guest_sha256"] = sha(cr_guest)
        self._save_manifest()
        with self.assertRaises(gate.Refused) as caught:
            gate.verify(self.manifest_path)
        self.assertEqual(str(caught.exception), "CR_IN_CANONICAL_JSON")

        manifest_raw = self.manifest_path.read_bytes()
        duplicated = manifest_raw[:-1] + b',"security_admission":"RED"}'
        self.assertEqual(json.loads(duplicated.decode())["security_admission"], "RED")
        self.manifest_path.write_bytes(duplicated)
        with self.assertRaises(gate.Refused) as caught:
            gate.verify(self.manifest_path)
        self.assertEqual(str(caught.exception), "DUPLICATE_JSON_KEY")
        self.manifest_path.write_bytes(manifest_raw.replace(b"{", b"{\r", 1))
        with self.assertRaises(gate.Refused) as caught:
            gate.verify(self.manifest_path)
        self.assertEqual(str(caught.exception), "CR_IN_CANONICAL_JSON")

    def test_25_posix_directory_flag_and_inode_mutation(self):
        """POSIX still requires O_DIRECTORY and still refuses alias inodes.

        Zero is not a directory flag. A copy that ORs getattr(..., 0) would
        open without that requirement. Dropping the nlink check would accept
        a hardlinked receipt. The real functions still refuse both.
        """
        source = Path(gate.__file__).read_text(encoding="utf-8")
        self.assertNotIn("os.O_DIRECTORY", source)
        self._skip_if_directory_open_unavailable()
        flags = gate.directory_open_flags()
        self.assertNotEqual(os.O_DIRECTORY, 0)
        self.assertEqual(flags & os.O_DIRECTORY, os.O_DIRECTORY)
        with mock.patch.object(gate.os, "O_DIRECTORY", 0, create=True):
            weakened = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            self.assertEqual(weakened & getattr(os, "O_DIRECTORY", 0), 0)
            with self.assertRaises(gate.Refused) as caught:
                gate.directory_open_flags()
            self.assertEqual(str(caught.exception), "SKIP_NON_POSIX")
        with mock.patch.object(gate.os, "name", "nt"):
            with self.assertRaises(gate.Refused) as caught:
                gate.directory_open_flags()
            self.assertEqual(str(caught.exception), "SKIP_NON_POSIX")

        fifo = self.base / "run-1" / "not-regular"
        os.mkfifo(fifo)
        with self.assertRaises(gate.Refused) as caught:
            gate.read_anchored(self.base, "run-1/not-regular", 1024)
        self.assertEqual(str(caught.exception), "NONREGULAR_FILE")

        link = self.base / "run-1" / "linked.jsonl"
        link.symlink_to(self.base / "run-1" / "receipt.jsonl")
        with self.assertRaises(gate.Refused) as caught:
            gate.read_anchored(self.base, "run-1/linked.jsonl", 16 * 1024)
        self.assertEqual(str(caught.exception), "SYMLINK_FILE_REFUSED")

        receipt = self.base / "run-1" / "receipt.jsonl"
        alias = self.base / "run-1" / "receipt-alias.jsonl"
        os.link(receipt, alias)
        self.assertEqual(receipt.stat().st_ino, alias.stat().st_ino)
        self.assertGreater(receipt.stat().st_nlink, 1)

        def drop_nlink(info, limit):
            gate.require(stat.S_ISREG(info.st_mode), "NONREGULAR_FILE")
            gate.require(info.st_size <= limit, "OVERSIZED_FILE")

        with mock.patch.object(gate, "require_evidence_inode", drop_nlink):
            mutated = gate.verify(self.manifest_path)
        self.assertEqual(mutated["security_admission"], "RED")
        self.assertIs(mutated["production_authority"], False)
        with self.assertRaises(gate.Refused) as caught:
            gate.require_evidence_inode(receipt.stat(), 16 * 1024)
        self.assertEqual(str(caught.exception), "HARDLINK_ALIAS_REFUSED")
        with self.assertRaises(gate.Refused) as caught:
            gate.verify(self.manifest_path)
        self.assertEqual(str(caught.exception), "HARDLINK_ALIAS_REFUSED")

    def test_overflow_float_refused_in_guest_and_manifest(self):
        for raw in (b'{"a":1e999}', b'{"a":-1e999}'):
            with self.subTest(raw=raw):
                loaded = json.loads(raw.decode())
                self.assertTrue(loaded["a"] == float("inf") or loaded["a"] == float("-inf"))
                with self.assertRaises(gate.Refused) as caught:
                    gate.decode(raw)
                self.assertEqual(str(caught.exception), "NON_FINITE_JSON")

    def test_overflow_float_in_guest_and_manifest_files(self):
        self._skip_if_directory_open_unavailable()
        guest = self.base / "run-1" / "guest.json"
        guest_raw = guest.read_bytes()
        overflow_guest = guest_raw[:-1] + b',"n":1e999}'
        self.assertEqual(json.loads(overflow_guest.decode())["n"], float("inf"))
        guest.write_bytes(overflow_guest)
        self.manifest["runs"][0]["guest_sha256"] = sha(overflow_guest)
        self._save_manifest()
        with self.assertRaises(gate.Refused) as caught:
            gate.verify(self.manifest_path)
        self.assertEqual(str(caught.exception), "NON_FINITE_JSON")
        guest.write_bytes(guest_raw)
        self.manifest["runs"][0]["guest_sha256"] = sha(guest_raw)
        self._save_manifest()
        manifest_raw = self.manifest_path.read_bytes()
        overflow_manifest = manifest_raw[:-1] + b',"n":-1e999}'
        self.assertEqual(json.loads(overflow_manifest.decode())["n"], float("-inf"))
        self.manifest_path.write_bytes(overflow_manifest)
        with self.assertRaises(gate.Refused) as caught:
            gate.verify(self.manifest_path)
        self.assertEqual(str(caught.exception), "NON_FINITE_JSON")


    def test_read_anchored_calls_directory_open_flags(self):
        def boom():
            raise gate.Refused("DIRECTORY_OPEN_FLAGS_NOT_USED")

        with mock.patch.object(gate, "directory_open_flags", boom):
            with self.assertRaises(gate.Refused) as caught:
                gate.read_anchored(self.base, "run-1/receipt.jsonl", 4096)
            self.assertEqual(str(caught.exception), "DIRECTORY_OPEN_FLAGS_NOT_USED")

    def test_read_anchored_refuses_zero_directory_flag(self):
        with mock.patch.object(gate.os, "O_DIRECTORY", 0, create=True):
            with self.assertRaises(gate.Refused) as caught:
                gate.read_anchored(self.base, "run-1/receipt.jsonl", 4096)
            self.assertEqual(str(caught.exception), "SKIP_NON_POSIX")

    def test_symlink_directory_anchor_requires_nofollow(self):
        self._skip_if_directory_open_unavailable()
        outside = self.base / "outside-anchor"
        outside.mkdir()
        secret = b'{"outside":true}\n'
        (outside / "receipt.jsonl").write_bytes(secret)
        link = self.base / "linked-run"
        link.symlink_to(outside, target_is_directory=True)
        try:
            got = gate.read_anchored(self.base, "linked-run/receipt.jsonl", 4096)
        except gate.Refused as exc:
            self.assertEqual(str(exc), "ARTIFACT_PARENT_NOT_REAL_DIRECTORY")
        else:
            self.fail("symlink directory anchor was followed: " + repr(got))

    def _load_gate_copy(self, source: str):
        path = self.base / "cp083_root_open_mutant.py"
        path.write_text(source, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("cp083_root_open_mutant", path)
        if spec is None or spec.loader is None:
            self.fail("cannot load root-open mutant")
        mutant = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mutant
        try:
            spec.loader.exec_module(mutant)
        except Exception:
            sys.modules.pop(spec.name, None)
            raise
        return mutant

    def test_symlinked_evidence_root_requires_directory_flags(self):
        """The caller-supplied root is opened with O_DIRECTORY|O_NOFOLLOW.

        Replacing that root with a symlink must be refused. A copy that opens
        the root with O_RDONLY follows the link and reads the file.
        """
        self._skip_if_directory_open_unavailable()
        source = Path(gate.__file__).read_text(encoding="utf-8")
        live_open = "        base_fd = os.open(base, flags_dir)\n"
        weak_open = "        base_fd = os.open(base, os.O_RDONLY)\n"
        anchor = "    refuse_symlinked_anchor(base)\n"
        self.assertEqual(source.count(live_open), 1)
        self.assertEqual(source.count(anchor), 1)
        mutated = source.replace(anchor, "", 1).replace(live_open, weak_open, 1)
        self.assertNotIn(live_open, mutated)
        self.assertNotIn(anchor, mutated)
        real = self.base / "real-root"
        (real / "run-1").mkdir(parents=True)
        secret = b'{"root":"followed"}\n'
        (real / "run-1" / "receipt.jsonl").write_bytes(secret)
        link = self.base / "linked-root"
        link.symlink_to(real, target_is_directory=True)
        with self.assertRaises(gate.Refused) as caught:
            gate.read_anchored(link, "run-1/receipt.jsonl", 4096)
        self.assertEqual(str(caught.exception), "ANCHORED_OPEN_REFUSED")
        mutant = self._load_gate_copy(mutated)
        try:
            followed = mutant.read_anchored(link, "run-1/receipt.jsonl", 4096)
        finally:
            sys.modules.pop(getattr(mutant, "__name__", ""), None)
        self.assertEqual(followed, secret)

    def test_base_anchor_itself_symlink_refused(self):
        """The final component of base is already refused. Pin that without a mutant."""
        self._skip_if_directory_open_unavailable()
        real = self.base / "real-anchor"
        (real / "run-1").mkdir(parents=True)
        (real / "run-1" / "receipt.jsonl").write_bytes(b'{"anchor":"self"}\n')
        link = self.base / "base-link"
        link.symlink_to(real, target_is_directory=True)
        with self.assertRaises(gate.Refused) as caught:
            gate.read_anchored(link, "run-1/receipt.jsonl", 4096)
        self.assertEqual(str(caught.exception), "ANCHORED_OPEN_REFUSED")

    def test_symlinked_ancestor_of_base_refused(self):
        """O_NOFOLLOW does not see a symlink above base. realpath must refuse it.

        A copy that drops refuse_symlinked_anchor follows the ancestor and
        returns the other tree's bytes.
        """
        self._skip_if_directory_open_unavailable()
        foreign = self.base / "foreign"
        (foreign / "subdir" / "run-1").mkdir(parents=True)
        secret = b'{"secret":"reached-via-intermediate-symlink"}\n'
        (foreign / "subdir" / "run-1" / "receipt.jsonl").write_bytes(secret)
        mid = self.base / "mid"
        mid.symlink_to(foreign, target_is_directory=True)
        base = mid / "subdir"
        with self.assertRaises(gate.Refused) as caught:
            gate.read_anchored(base, "run-1/receipt.jsonl", 4096)
        self.assertEqual(str(caught.exception), "ANCHORED_OPEN_REFUSED")
        source = Path(gate.__file__).read_text(encoding="utf-8")
        anchor = "    refuse_symlinked_anchor(base)\n"
        self.assertEqual(source.count(anchor), 1)
        mutated = source.replace(anchor, "", 1)
        self.assertNotIn("refuse_symlinked_anchor(base)", mutated)
        mutant = self._load_gate_copy(mutated)
        try:
            followed = mutant.read_anchored(base, "run-1/receipt.jsonl", 4096)
        finally:
            sys.modules.pop(getattr(mutant, "__name__", ""), None)
        self.assertEqual(followed, secret)


if __name__ == "__main__":
    unittest.main()
