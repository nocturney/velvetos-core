#!/usr/bin/env python3
"""ChatGPT-069 gaps. No guest, no remote GitHub.

GAP_4 is a passing gate refusal: a hardlinked SQLite journal and a non-regular
evidence file fail closed. GAP_9 is a passing wire/evidence refusal. The sealed
native engine is not edited. GAP_6 stays an expected failure. The pinned
identity helper is not edited here. Benign fake variables only.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


class ChatGPT069ExpectedGaps(unittest.TestCase):
    def test_crlf_and_duplicate_wire_fields_rejected(self):
        """GAP_9: the socket parsers no longer take the first LF split via json.loads."""
        source = (SCRIPTS / (
            "vf_office_v2_604_cp083_hardened_candidate.py")).read_text(
                encoding="utf-8")
        self.assertNotIn(
            'reply = json.loads(bytes(buffer.split(b"\\n", 1)[0]))',
            source,
            "GAP_9",
        )
        self.assertNotIn(
            'req = json.loads(bytes(incoming.split(b"\\n", 1)[0]))',
            source,
            "GAP_9",
        )
        self.assertIn("read_json_frame(", source)

    @unittest.expectedFailure
    def test_controller_env_import_and_helper_spawn_canaries_refused(self):
        """GAP_6: imports before guard, and helper children inherit the controller.

        PYTHONPATH, OPENSSL_CONF, PATH, and VF_FAKE_SECRET_CANARY are benign
        fakes. No real credential is introduced.
        """
        marker_dir = tempfile.TemporaryDirectory(prefix="vf604-cp083-canary-")
        self.addCleanup(marker_dir.cleanup)
        root = Path(marker_dir.name)
        marker = root / "canary-imported"
        canary = root / "vf_office_v2_604_real_etcd_mtls_rbac_identity_lab.py"
        canary.write_text(
            "import os\n"
            "from pathlib import Path\n"
            "Path(os.environ['VF_FAKE_CANARY_MARKER']).write_text('executed\\n')\n",
            encoding="utf-8",
        )
        env = {
            "PYTHONPATH": str(root) + os.pathsep + str(SCRIPTS),
            "OPENSSL_CONF": "/tmp/vf-fake-openssl.cnf",
            "PATH": "/tmp/vf-fake-bin",
            "VF_FAKE_SECRET_CANARY": "benign-not-a-secret",
            "VF_FAKE_CANARY_MARKER": str(marker),
            "LANG": "C",
            "LC_ALL": "C",
        }
        mod = "vf_office_v2_604_cp083_hardened_" + "candidate"
        proc = subprocess.run(
            [sys.executable, "-B", "-c", "import " + mod],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertFalse(marker.exists(), "GAP_6 import canary executed")
        self.assertEqual(proc.returncode, 0, proc.stderr[-400:])

        import vf_office_v2_604_real_etcd_mtls_rbac_identity_lab as identity
        poison = {
            "PYTHONPATH": str(root),
            "OPENSSL_CONF": "/tmp/vf-fake-openssl.cnf",
            "PATH": "/tmp/vf-fake-bin",
            "VF_FAKE_SECRET_CANARY": "benign-not-a-secret",
        }
        captured = {}

        def fake_run(args, **kwargs):
            captured["env"] = kwargs.get("env") or {}

            class Done:
                returncode = 0
                stdout = ""
                stderr = ""

            return Done()

        with mock.patch.dict(os.environ, poison, clear=False):
            with mock.patch.object(identity.subprocess, "run", fake_run):
                identity.subprocess_safe(["openssl", "version"])
        for key in poison:
            self.assertNotIn(key, captured["env"], "GAP_6")
        start = Path(identity.__file__).read_text(encoding="utf-8")
        body = start.split("def start(self):", 1)[1].split("\n    def health", 1)[0]
        self.assertIn("env=", body, "GAP_6")

    def test_hardlinked_sqlite_alias_rejected(self):
        """GAP_4: a hardlinked journal is not evidence, and neither is a non-file.

        The sealed native engine still path-checks the lab. Rewriting it would
        move the lost-ACK pin. The evidence gate refuses the inode instead.
        """
        import vf_office_v2_604_native_git_crash_reconcile_offline as offline
        import vf_office_v2_604_cp083_candidate_evidence_gate as gate
        import vf_office_v2_604_cp083_native_lostack_receipt_gate as lostack
        lab_dir = tempfile.TemporaryDirectory(prefix="vf604-cp083-sqlite-alias-")
        self.addCleanup(lab_dir.cleanup)
        root = Path(lab_dir.name)
        lab = offline.OfflineLab.create(root / "lab")
        alias = root / "alias.sqlite3"
        os.link(lab.db, alias)
        self.assertEqual(lab.db.stat().st_ino, alias.stat().st_ino)
        self.assertGreater(lab.db.stat().st_nlink, 1)
        with self.assertRaises(gate.Refused) as caught:
            gate.read_bounded(lab.db, 8 * 1024 * 1024)
        self.assertEqual(str(caught.exception), "HARDLINK_ALIAS_REFUSED")
        evidence = root / "evidence.json"
        evidence.write_bytes(b'{"schema":"synthetic"}\n')
        os.link(evidence, root / "evidence-alias.json")
        self.assertGreater(evidence.stat().st_nlink, 1)
        with self.assertRaises(gate.Refused) as caught:
            lostack.read_evidence(evidence)
        self.assertEqual(str(caught.exception), "HARDLINK_ALIAS_REFUSED")
        live = lostack.read_evidence(lostack.EVIDENCE)
        self.assertEqual(live.get("security_admission"), "RED")
        if os.name == "posix" and hasattr(os, "mkfifo"):
            fifo = root / "not-regular"
            os.mkfifo(fifo)
            with self.assertRaises(gate.Refused) as caught:
                gate.read_anchored(root, "not-regular", 1024)
            self.assertEqual(str(caught.exception), "NONREGULAR_FILE")
            with self.assertRaises(gate.Refused) as caught:
                gate.read_bounded(fifo, 1024)
            self.assertEqual(str(caught.exception), "NONREGULAR_FILE")

    def test_lostack_main_refuses_hardlinked_evidence(self):
        """main() itself must refuse a hardlinked evidence JSON.

        A copy of the sealed evidence would otherwise validate. The extra
        link is the only defect. Reading the path with read_text would accept it.
        """
        import vf_office_v2_604_cp083_candidate_evidence_gate as gate
        import vf_office_v2_604_cp083_native_lostack_receipt_gate as lostack
        lab_dir = tempfile.TemporaryDirectory(prefix="vf604-cp083-lostack-main-")
        self.addCleanup(lab_dir.cleanup)
        root = Path(lab_dir.name)
        evidence = root / "evidence.json"
        evidence.write_bytes(lostack.EVIDENCE.read_bytes())
        alias = root / "evidence-alias.json"
        os.link(evidence, alias)
        self.assertEqual(evidence.stat().st_ino, alias.stat().st_ino)
        self.assertGreater(evidence.stat().st_nlink, 1)
        with mock.patch.object(lostack, "EVIDENCE", evidence):
            with self.assertRaises(gate.Refused) as caught:
                lostack.main([])
        self.assertEqual(str(caught.exception), "HARDLINK_ALIAS_REFUSED")


if __name__ == "__main__":
    unittest.main()
