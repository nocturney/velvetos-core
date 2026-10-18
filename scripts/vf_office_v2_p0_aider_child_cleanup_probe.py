#!/usr/bin/env python3
"""#612 LAB-only real-process fault probes for Aider pre-guard cleanup.

No Aider/Ollama, production state, credentials, scheduler, GUI, or network.
Every child is a new bounded Python process owned by this probe. Original
worker attempts and historical journals are never opened or retried.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import vf_office_v2_p0_diverse_local_worker as worker


def require(condition, label):
    if not condition:
        raise AssertionError(label)


def spawn():
    options = {"stdin": subprocess.DEVNULL, "stdout": subprocess.PIPE,
               "stderr": subprocess.PIPE}
    if os.name == "nt":
        options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        options["start_new_session"] = True
    return subprocess.Popen([sys.executable, "-B", "-c",
                             "import time; time.sleep(12)"], **options)


def run():
    cases = []
    with tempfile.TemporaryDirectory(prefix="office612-owned-child-") as temp:
        # Separately owned sentinel must remain alive through ALL tested stops.
        sentinel = spawn()
        try:
            for stage in ("birth_pin", "pin_save", "communicate_io", "timeout"):
                out = Path(temp) / stage
                out.mkdir()
                original = b'{"state":"RUNNING","unknown_outcome_rule":"NO_BLIND_RETRY"}\n'
                (out / "receipt.json.running").write_bytes(original)
                env = {"task_id": "p0-diverse-run-child-fixture-0001"}
                child = spawn()
                reaped = False
                try:
                    def capture():
                        if stage == "birth_pin":
                            raise worker.Refused("injected OS birth pin failure")
                        if stage == "pin_save":
                            raise OSError("injected durable pin save failure")
                        return {"synthetic": True}

                    def wait():
                        if stage == "communicate_io":
                            raise OSError("injected communicate pipe failure")
                        raise subprocess.TimeoutExpired("owned fixture", 0.01)

                    try:
                        worker._guarded_capture_and_wait(child, capture, wait)
                    except (worker.Refused, OSError, subprocess.TimeoutExpired) as exc:
                        if isinstance(exc, subprocess.TimeoutExpired):
                            reaped = worker._stop_owned_direct_child(child)
                        else:
                            reaped = child.poll() is not None
                    else:
                        raise AssertionError("FAULT_WAS_NOT_REJECTED_" + stage)
                    worker._persist_unknown_child(out, env, child, stage, reaped)
                    require(reaped and child.poll() is not None,
                            "REAL_DIRECT_CHILD_NOT_REAPED_" + stage)
                    require((out / "receipt.json.running").read_bytes() == original,
                            "RUNNING_JOURNAL_OVERWRITTEN_" + stage)
                    require(not (out / "receipt.json").exists(),
                            "FALSE_SUCCESS_" + stage)
                    report = json.loads((out / "child-cleanup.unknown.json").read_text())
                    require(report["state"] == "UNKNOWN" and
                            report["direct_child_reaped"] is True and
                            report["all_orphans_excluded"] is False and
                            report["retry_permitted"] is False and
                            report["production_authority"] is False and
                            report["original_running_journal_preserved"] is True,
                            "WRONG_FAIL_CLOSED_RECEIPT_" + stage)
                    require(sentinel.poll() is None,
                            "UNRELATED_SENTINEL_KILLED_" + stage)
                    cases.append(stage + "_real_child_reaped_journal_unknown")
                finally:
                    if child.poll() is None:
                        worker._stop_owned_direct_child(child)
        finally:
            worker._stop_owned_direct_child(sentinel)
    require(len(cases) == 4, "PROBE_COUNT")
    return {"status": "PASS_LAB_ONLY", "host": os.name,
            "real_process_cases": len(cases), "cases": cases,
            "unrelated_sentinel_survived_all_faults": True,
            "all_orphans_excluded": False, "auto_retry": False,
            "model_invocations": 0, "external_effects": 0}


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))
