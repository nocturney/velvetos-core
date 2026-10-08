#!/usr/bin/env python3
"""Offline negative controls for the Phase 3B Morning Green production-read cutover."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import types
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "packages" / "vfigos" / "cloudflare_publisher_snapshot.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def fixture(folder: Path, checkpoint_id: str, phase: str) -> Path:
    name = (
        "checkpoint-016-v0-phase3b-pilot-active.json"
        if checkpoint_id.endswith("cp016-pilot-active")
        else "checkpoint-017-v0-phase3b-production-read-active.json"
    )
    cp = {
        "schema_version": "velvetos.office-v2.project-state.v0",
        "checkpoint_id": checkpoint_id,
        "migration_phase": phase,
        "gate_status": {"verdict": "GREEN"},
    }
    cp["content_hash"] = hashlib.sha256(
        json.dumps(cp, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    cp_path = folder / name
    cp_path.write_text(json.dumps(cp), encoding="utf-8")
    pointer = {
        "schema": "velvetos.office-v2.project-state-pointer.v0",
        "current_checkpoint_ref": str(cp_path),
        "checkpoint_id": checkpoint_id,
        "content_hash": cp["content_hash"],
        "phase": phase,
        "gate": "GREEN",
    }
    pointer_path = folder / "CURRENT.json"
    pointer_path.write_text(json.dumps(pointer), encoding="utf-8")
    return pointer_path


def expect_denied(operation, label: str) -> None:
    try:
        operation()
    except (RuntimeError, ValueError, OSError, json.JSONDecodeError):
        return
    raise AssertionError(f"{label}: expected fail-closed exception")


def main() -> None:
    spec = importlib.util.spec_from_file_location("vf_phase3b_publisher_router", ADAPTER)
    require(spec is not None and spec.loader is not None, "router import unavailable")
    router = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(router)
    sample = {
        "schema": "vf.instagram.schedule-snapshot.v1",
        "source": "cloudflare-instagram-publisher",
        "scheduled": [],
    }
    with tempfile.TemporaryDirectory(prefix="vf_phase3b_reader_") as tmp:
        folder = Path(tmp)
        require(router.snapshot_route(folder / "missing.json") == "INCUMBENT", "absent Office v2 runtime must preserve incumbent")
        cp16 = fixture(folder, router.PILOT_CHECKPOINT, "PHASE_3B_PILOT_ACTIVE")
        require(router.snapshot_route(cp16) == "INCUMBENT", "cp016 must remain incumbent")
        cp17 = fixture(folder, router.PRODUCTION_CHECKPOINT, "PHASE_3B_PRODUCTION_READ_ACTIVE")
        require(router.snapshot_route(cp17) == "OFFICEV2_PRODUCTION_READ", "cp017 must select secure read")
        pointer = json.loads(cp17.read_text(encoding="utf-8"))
        malformed = dict(pointer, phase="PHASE_3B_PILOT_ACTIVE")
        cp17.write_text(json.dumps(malformed), encoding="utf-8")
        expect_denied(lambda: router.snapshot_route(cp17), "phase/checkpoint mismatch")
        cp17.write_text(json.dumps(pointer), encoding="utf-8")
        wrong_ref = dict(pointer, current_checkpoint_ref=str(folder / "other.json"))
        cp17.write_text(json.dumps(wrong_ref), encoding="utf-8")
        expect_denied(lambda: router.snapshot_route(cp17), "checkpoint ref tampering")
        cp17.write_text(json.dumps(pointer), encoding="utf-8")
        cp_path = folder / "checkpoint-017-v0-phase3b-production-read-active.json"
        original_cp = cp_path.read_text(encoding="utf-8")
        tampered = json.loads(original_cp)
        tampered["gate_status"]["verdict"] = "RED"
        cp_path.write_text(json.dumps(tampered), encoding="utf-8")
        expect_denied(lambda: router.snapshot_route(cp17), "checkpoint hash tampering")
        cp_path.write_text(original_cp, encoding="utf-8")
        require(router.snapshot_route(cp17) == "OFFICEV2_PRODUCTION_READ", "restored fixture must validate")
        cp17.write_text("{bad json", encoding="utf-8")
        expect_denied(lambda: router.snapshot_route(cp17), "corrupted pointer")
        cp17.write_text(json.dumps(pointer), encoding="utf-8")

        stub = types.ModuleType("officev2_secure_publisher_snapshot")
        stub.DEFAULT_RESOLVER = Path("test-resolver")
        called = []
        def secure_ok(resolver, mode):
            called.append((resolver, mode))
            return sample
        stub.secure_snapshot = secure_ok
        prod_file = folder / "production.json"
        env = {"VELVET_INSTAGRAM_PUBLISHER_URL": router.DEFAULT_URL}
        with (mock.patch.dict(sys.modules, {"officev2_secure_publisher_snapshot": stub}),
              mock.patch.dict(os.environ, env),
              mock.patch.object(router, "snapshot_route", return_value="OFFICEV2_PRODUCTION_READ"),
              mock.patch.object(router, "resolve_token", side_effect=AssertionError("legacy credential read forbidden")),
              mock.patch.object(sys, "argv", ["reader", "--output", str(prod_file)])):
            require(router.main() == 0, "secure production route failed")
        require(called == [(stub.DEFAULT_RESOLVER, "Production")], "secure Production resolver was not selected exactly")
        require(json.loads(prod_file.read_text()) == sample, "production payload mismatch")

        def secure_fail(*_):
            raise RuntimeError("secure reader intentionally denied")
        stub.secure_snapshot = secure_fail
        failed_out = folder / "failclosed.json"
        with (mock.patch.dict(sys.modules, {"officev2_secure_publisher_snapshot": stub}),
              mock.patch.dict(os.environ, env),
              mock.patch.object(router, "snapshot_route", return_value="OFFICEV2_PRODUCTION_READ"),
              mock.patch.object(router, "resolve_token", side_effect=AssertionError("legacy credential fallback forbidden")),
              mock.patch.object(sys, "argv", ["reader", "--output", str(failed_out)])):
            expect_denied(router.main, "secure reader failed")
        require(not failed_out.exists(), "secure failure must never emit a snapshot")

        overridden = folder / "override.json"
        with (mock.patch.dict(sys.modules, {"officev2_secure_publisher_snapshot": stub}),
              mock.patch.dict(os.environ, env),
              mock.patch.object(router, "snapshot_route", return_value="OFFICEV2_PRODUCTION_READ"),
              mock.patch.object(router, "resolve_token", side_effect=AssertionError("legacy credential fallback forbidden")),
              mock.patch.object(sys, "argv", ["reader", "--output", str(overridden), "--base-url", "https://unrelated.example"])):
            expect_denied(router.main, "production endpoint override")
        require(not overridden.exists(), "forbidden endpoint override must not produce output")

        incumbent_file = folder / "incumbent.json"
        with (mock.patch.object(router, "snapshot_route", return_value="INCUMBENT"),
              mock.patch.object(router, "resolve_token", return_value="fixture-token") as legacy,
              mock.patch.object(router, "snapshot", return_value=sample) as old_snapshot,
              mock.patch.object(sys, "argv", ["reader", "--output", str(incumbent_file)])):
            require(router.main() == 0, "cp016 incumbent route failed")
            legacy.assert_called_once()
            old_snapshot.assert_called_once()
        require(incumbent_file.is_file(), "incumbent route must remain functional")

    print("OK phase3b production-reader-route cases=11 cp016=incumbent cp017=secure failclosed=PASS admin-fallback=FORBIDDEN")


if __name__ == "__main__":
    main()
