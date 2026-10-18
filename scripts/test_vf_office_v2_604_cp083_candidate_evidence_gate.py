#!/usr/bin/env python3
"""Synthetic format/mutation tests ONLY; no runtime full-chain or QA claim."""
from __future__ import annotations

import hashlib
import json
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

    def assert_refused(self):
        with self.assertRaises(gate.Refused):
            gate.verify(self.manifest_path)

    def test_01_synthetic_positive_format_only_never_security_pass(self):
        result = gate.verify(self.manifest_path)
        self.assertEqual(result["status"],
                         "OFFLINE_BYTE_CONSISTENCY_ONLY_NOT_RUNTIME_QA")
        self.assertEqual(result["raw_receipt_files"], 2)
        self.assertEqual(result["security_admission"], "RED")
        self.assertFalse(result["independent_runtime_provenance_verified"])
        self.assertFalse(result["production_authority"])

    def test_02_missing_manifest_is_refused(self):
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
        link.symlink_to(self.base / "run-1/receipt.jsonl")
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


if __name__ == "__main__":
    unittest.main()
