#!/usr/bin/env python3
"""Validate the zero-cost behavioral regression contract without network access."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

from vf_spawn import same_pinned_directory

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "packages" / "vfharness" / "evals"
CONFIG = EVALS / "promptfooconfig.json"
TARGET = EVALS / "policy_target.py"
PACKAGE = ROOT / "tools" / "promptfoo" / "package.json"
LOCK = ROOT / "tools" / "promptfoo" / "package-lock.json"
REQUIRED = {
    "missing_price", "missing_authority", "tool_failure", "memory_only",
    "untrusted_authority_change", "readonly_to_write", "handoff_bypass",
    "publish_without_authorization", "write_without_readback", "prompt_injection",
}

def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)

def load_target():
    spec = importlib.util.spec_from_file_location("vf_behavior_target", TARGET)
    if spec is None or spec.loader is None:
        fail("cannot load policy target")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def prove_promptfoo_hygiene() -> None:
    """Promptfoo gets only the telemetry-off keys and its own directory."""
    import vf_spawn

    spec = importlib.util.spec_from_file_location(
        "run_promptfoo_evals", ROOT / "scripts" / "run-promptfoo-evals.py"
    )
    if spec is None or spec.loader is None:
        fail("cannot load promptfoo runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sentinel = "VF_SPAWN_SENTINEL"
    os.environ[sentinel] = "nope"
    os.environ["NODE_OPTIONS"] = "--experimental-permission"
    directory = Path(tempfile.mkdtemp(prefix="vf-promptfoo-"))
    fake = directory / ("promptfoo.cmd" if os.name == "nt" else "promptfoo")
    fake.write_text("#!/bin/sh\n", encoding="utf-8")
    captured: list[tuple[list[str], dict]] = []
    original = vf_spawn.subprocess.run

    def fake_run(argv, **kwargs):
        captured.append((list(argv), kwargs))
        return vf_spawn.subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    module.BIN = fake
    vf_spawn.subprocess.run = fake_run
    try:
        module.run(CONFIG, directory / "out.json")
    finally:
        vf_spawn.subprocess.run = original
        os.environ.pop(sentinel, None)
        os.environ.pop("NODE_OPTIONS", None)
    if len(captured) != 1:
        fail("promptfoo spawn did not run")
    argv, kwargs = captured[0]
    if argv[0] != str(fake.resolve()) or not os.path.isabs(argv[0]):
        fail(f"promptfoo was not absolute: {argv}")
    if kwargs.get("timeout") != module.PROMPTFOO_TIMEOUT_SECONDS:
        fail("promptfoo timeout missing")
    env = kwargs.get("env")
    allowed = set(vf_spawn._BASE_ENV_KEYS) | set(module.HARDEN) | {"PATH"}
    if not isinstance(env, dict) or sentinel in env or "NODE_OPTIONS" in env or set(env) - allowed:
        fail(f"promptfoo environment was not allowlisted: {env}")
    for key, value in module.HARDEN.items():
        if env.get(key) != value:
            fail(f"promptfoo lost harden key {key}")
    if not same_pinned_directory(env.get("PATH", ""), str(Path(argv[0]).resolve().parent)):
        fail(f"promptfoo PATH was not the executable directory: {env.get('PATH')}")


def main() -> None:
    prove_promptfoo_hygiene()
    for path in (CONFIG, TARGET, PACKAGE, LOCK):
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    if package.get("devDependencies", {}).get("promptfoo") != "0.123.1":
        fail("Promptfoo version must be pinned to 0.123.1")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if config.get("providers") != ["exec: python policy_target.py"]:
        fail("Promptfoo provider must remain the trusted local exec target only")
    tests = config.get("tests") or []
    if len(tests) < 10:
        fail("behavioral suite is too small")
    module = load_target()
    seen = set()
    for test in tests:
        scenario = json.loads(test["vars"]["scenario"])
        kind = scenario.get("kind")
        seen.add(kind)
        assertions = test.get("assert") or []
        if len(assertions) != 1 or assertions[0].get("type") != "equals":
            fail(f"{test.get('description')}: exactly one equals assertion required")
        actual = module.evaluate(scenario)
        if actual != assertions[0].get("value"):
            fail(f"{test.get('description')}: {actual!r} != expected")
    missing = REQUIRED - seen
    if missing:
        fail("missing required scenarios: " + ",".join(sorted(missing)))
    unsafe = module.evaluate({"kind": "missing_price", "price_source": False})
    if unsafe == "ALLOW|price_source_present":
        fail("negative control did not catch invented-price path")
    injected = module.evaluate({"kind": "prompt_injection"})
    if not injected.startswith("BLOCK|"):
        fail("negative control did not block prompt injection")
    print(f"OK behavioral-evals cases={len(tests)} required={len(REQUIRED)} negative_controls=2")

if __name__ == "__main__":
    main()
