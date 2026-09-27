#!/usr/bin/env python3
"""Sensor: Living Studio connective tissue — no duplicate SoTs, registry, behavioral CLI."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LS = ROOT / "packages" / "velvetos" / "living-studio"
REGISTRY = LS / "REGISTRY.json"
README = LS / "README.md"
CLI = ROOT / "scripts" / "vf_living_studio.py"
CONTROL_PLANE = ROOT / "office" / "control-plane.json"
DECISIONS = ROOT / "office" / "control" / "decisions.jsonl"
EVENTS = ROOT / "packages" / "velvetos" / "schema" / "events.catalog.json"
CHECK_ALL = ROOT / "scripts" / "check-all.py"
MANIFEST = ROOT / "packages" / "manifest.json"
AGENTS = ROOT / "AGENTS.md"
VFCOPY_HE = ROOT / "packages" / "vfcopy" / "skills" / "velvet-hebrew-copy" / "SKILL.md"
INTAKE = ROOT / "packages" / "vfmedia" / "INTAKE.md"
WRITING_PLANS = ROOT / "packages" / "vfharness" / "playbooks" / "writing-plans.md"


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in (LS, REGISTRY, README, CLI, CONTROL_PLANE, DECISIONS, EVENTS, INTAKE, WRITING_PLANS, VFCOPY_HE):
        if not path.exists():
            fail(f"missing {path.relative_to(ROOT)}")

    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    skills = reg.get("skills") or []
    if len(skills) != 23:
        fail(f"REGISTRY skills must be 23, got {len(skills)}")
    living = reg.get("livingCapabilities") or []
    if len(living) < 10:
        fail("REGISTRY livingCapabilities too thin")

    # No competing SoT declarations
    for path in reg.get("doNotDuplicate") or []:
        p = ROOT / path
        if not p.exists():
            fail(f"canonical SoT missing (must reuse, not replace): {path}")

    # Forbid a second decision journal / world-model DB
    banned = [
        ROOT / "office" / "control" / "decision-journal.json",
        ROOT / "office" / "world-model.db",
        ROOT / "packages" / "world-model",
        ROOT / "packages" / "living-studio-db",
    ]
    for b in banned:
        if b.exists():
            fail(f"forbidden duplicate store {b.relative_to(ROOT)}")

    plane = json.loads(CONTROL_PLANE.read_text(encoding="utf-8"))
    sots = plane.get("sourcesOfTruth") or {}
    if sots.get("decisions") != "office/control/decisions.jsonl":
        fail("control-plane decisions SoT must stay decisions.jsonl")
    if "vfmedia/catalog.json" not in (sots.get("media") or ""):
        fail("control-plane media SoT must stay vfmedia catalog")

    # Brand voice must route to velvet-hebrew-copy
    brand = next(s for s in skills if s["id"] == "brand-voice-guardian")
    if "velvet-hebrew-copy" not in json.dumps(brand):
        fail("Brand Voice Guardian must route to velvet-hebrew-copy")

    # Projections must not become competing SoTs
    projections = plane.get("projections") or {}
    for key, path in projections.items():
        if path in (sots.values() if isinstance(sots, dict) else []):
            fail(f"projection {key} collides with sourcesOfTruth")

    # Control SoTs must not contain selftest pollution
    inbox = json.loads((ROOT / "office" / "control" / "inbox.json").read_text(encoding="utf-8"))
    blob = json.dumps(inbox, ensure_ascii=False)
    if "idempotency probe" in blob or "unique living studio idempotency" in blob:
        fail("inbox.json contains selftest pollution — selftest must be non-mutating")

    # Events for living studio / media intake present
    ev = json.loads(EVENTS.read_text(encoding="utf-8"))
    ids = {e.get("id") for e in ev.get("events") or []}
    for need in (
        "media.intake.registered",
        "media.intake.verified",
        "studio.pulse.generated",
        "intake.universal.routed",
        "intake.universal.dispatched",
        "invisible.work.detected",
        "failure.museum.recorded",
        "lab.experiment.recorded",
    ):
        if need not in ids:
            fail(f"events.catalog missing {need}")

    # Manifest / AGENTS must mention Living Studio
    manifest = MANIFEST.read_text(encoding="utf-8")
    if "living-studio" not in manifest and "Living Studio" not in manifest:
        fail("packages/manifest.json must mention Living Studio after unification")

    # Skill verify-all + non-mutating selftest. Keep both in-process so
    # check-all does not create a Python -> Python -> Python pipe chain on Windows.
    import vf_living_studio as living_studio_cli

    verify = living_studio_cli.skill_verify_all()
    if not verify.get("ok"):
        fail(f"skill verify-all: {verify}")

    # Run the Living Studio selftest in-process. On Windows this sensor is
    # itself launched by check-all; spawning the CLI again creates a nested
    # Python pipe-capture chain that can stall even though the selftest passes
    # when invoked directly.
    import contextlib
    import io

    selftest_out = io.StringIO()
    selftest_err = io.StringIO()
    with contextlib.redirect_stdout(selftest_out), contextlib.redirect_stderr(selftest_err):
        selftest_rc = living_studio_cli.selftest()
    if selftest_rc != 0:
        fail(f"vf_living_studio.py selftest: {selftest_err.getvalue() or selftest_out.getvalue()}")
    if "non-mutating" not in selftest_out.getvalue():
        fail("selftest must declare non-mutating")

    # Unit tests
    tests = LS / "tests" / "test_living_studio.py"
    if not tests.is_file():
        fail("missing living-studio tests")
    import importlib.util
    import unittest

    test_spec = importlib.util.spec_from_file_location("living_studio_tests", tests)
    if test_spec is None or test_spec.loader is None:
        fail("could not load living-studio tests")
    test_module = importlib.util.module_from_spec(test_spec)
    test_spec.loader.exec_module(test_module)
    suite = unittest.defaultTestLoader.loadTestsFromModule(test_module)
    test_out = io.StringIO()
    result = unittest.TextTestRunner(stream=test_out, verbosity=2).run(suite)
    if not result.wasSuccessful():
        fail(f"living-studio tests: {test_out.getvalue()}")

    print("OK living-studio registry+projection+skills+selftest")


# Sensors only read: undo writes made by the office CLIs this sensor smoke-tests
# (see scripts/sensor_isolation.py).
SIDE_EFFECT_PATHS = (
    "packages/velvetos/living-studio/data",
)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from sensor_isolation import preserve_repo_files  # noqa: E402

    with preserve_repo_files(ROOT, SIDE_EFFECT_PATHS):
        main()
