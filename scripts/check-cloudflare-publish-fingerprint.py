#!/usr/bin/env python3
"""Offline regression sensor for the Cloudflare scheduled-publisher fingerprint guard."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

from vf_spawn import SpawnRefusal, resolve_executable, run_tool, same_pinned_directory

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "packages" / "vfigos" / "cloudflare-publisher"
PY_FP = ROOT / "packages" / "vfigos" / "approval" / "publish_fingerprint.py"


def fail(message: str) -> None:
    print(f"FAIL cloudflare-publish-fingerprint {message}", file=sys.stderr)
    raise SystemExit(1)


def load_python_fingerprint():
    spec = importlib.util.spec_from_file_location("vf_publish_fingerprint", PY_FP)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.publish_fingerprint


NODE_TIMEOUT_SECONDS = 30


def prove_node_hygiene() -> None:
    """node is absolute, timed, and does not inherit NODE_OPTIONS."""
    import vf_spawn

    sentinel = "VF_SPAWN_SENTINEL"
    os.environ[sentinel] = "nope"
    os.environ["NODE_OPTIONS"] = "--experimental-permission"
    root = Path(os.environ.get("TEMP") or os.environ.get("TMPDIR") or "/tmp")
    node = root / "node"
    captured: list[tuple[list[str], dict]] = []
    original_run = vf_spawn.subprocess.run
    original_which = vf_spawn.shutil.which

    def fake_run(argv, **kwargs):
        captured.append((list(argv), kwargs))
        return vf_spawn.subprocess.CompletedProcess(argv, 0, stdout='{"ok":true}\n', stderr="")

    vf_spawn.subprocess.run = fake_run
    vf_spawn.shutil.which = lambda name: str(node) if name == "node" else original_which(name)
    try:
        run_tool(["node", "test-fingerprint.mjs"], timeout=NODE_TIMEOUT_SECONDS, cwd=ROOT)
    except SpawnRefusal as exc:
        fail(f"node spawn refused: {exc}")
    finally:
        vf_spawn.subprocess.run = original_run
        vf_spawn.shutil.which = original_which
        os.environ.pop(sentinel, None)
        os.environ.pop("NODE_OPTIONS", None)
    if len(captured) != 1:
        fail("node spawn did not run")
    argv, kwargs = captured[0]
    if argv[0] != str(Path(node).resolve()) or not os.path.isabs(argv[0]):
        fail(f"node was not absolute: {argv}")
    if kwargs.get("timeout") != NODE_TIMEOUT_SECONDS:
        fail("node timeout missing")
    env = kwargs.get("env")
    if not isinstance(env, dict) or sentinel in env or "NODE_OPTIONS" in env:
        fail(f"node environment was not allowlisted: {env}")
    if not same_pinned_directory(env.get("PATH", ""), str(Path(argv[0]).resolve().parent)):
        fail(f"node PATH was not the executable directory: {env.get('PATH')}")
    short = "C:\\Users\\RUNNER~1\\AppData\\Local\\Temp\\node-abc"
    long = "C:\\Users\\runneradmin\\AppData\\Local\\Temp\\node-abc"

    def expand_short(path: str) -> str:
        return str(path).replace("/", "\\").replace("RUNNER~1", "runneradmin")

    if not same_pinned_directory(short, long, realpath=expand_short, fold_case=True, separator=";"):
        fail("8.3 node directory did not match its long path")
    if not same_pinned_directory(short, long.upper(), realpath=expand_short, fold_case=True, separator=";"):
        fail("node pin comparison stayed case-sensitive")
    if same_pinned_directory(long + ";" + short, long, realpath=expand_short, fold_case=True, separator=";"):
        fail("a search PATH was accepted as the node pin")
    vf_spawn.shutil.which = lambda name: "node" if name == "node" else None
    try:
        try:
            resolve_executable("node")
        except SpawnRefusal as exc:
            if str(exc) != "SPAWN_PATH_LOOKUP_REFUSED":
                fail(f"relative node refused as {exc}")
        else:
            fail("relative node was accepted")
    finally:
        vf_spawn.shutil.which = original_which


def main() -> int:
    prove_node_hygiene()
    try:
        node = resolve_executable("node")
    except SpawnRefusal as exc:
        fail(str(exc))
    proc = run_tool(
        [node, str(WORKER / "test-fingerprint.mjs")],
        cwd=ROOT,
        timeout=NODE_TIMEOUT_SECONDS,
    )
    if proc.returncode != 0:
        fail(proc.stderr or proc.stdout or f"node exit {proc.returncode}")
    try:
        result = json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception as exc:
        fail(f"invalid node regression output: {exc}: {proc.stdout!r}")

    if result.get("incident") != "2026-09-13":
        fail(f"wrong incident fixture: {result}")
    if result.get("repeats_blocked") != 5 or result.get("extra_publishes") != 0:
        fail(f"incident replay regression: {result}")

    py_fingerprint = load_python_fingerprint()
    expected = py_fingerprint(
        ig_user_id="17841400000000000",
        media_sha256s=["a" * 64],
        caption="  Velvet\n  Factory   ",
    )
    if result.get("fingerprint") != expected:
        fail("Cloudflare fingerprint definition differs from approval/publish_fingerprint.py")


    src = (WORKER / "src" / "index.js").read_text(encoding="utf-8")
    check_at = src.find("checkRecentFingerprint(env.DB,fingerprint,t)")
    publish_at = src.find("const live=await publishJob(env,j)")
    if check_at < 0 or publish_at < 0 or check_at > publish_at:
        fail("fingerprint check must occur before publishJob / any Meta write")
    for token in (
        'outcome:"published_verified"',
        'outcome:"reconcile_required"',
        '"publish_fingerprint_blocked"',
        '"publish_fingerprint_recorded"',
    ):
        if token not in src:
            fail(f"worker missing {token}")

    schema = (WORKER / "schema.sql").read_text(encoding="utf-8")
    for token in (
        "CREATE TABLE IF NOT EXISTS publish_fingerprints",
        "fingerprint TEXT NOT NULL",
        "recorded_at INTEGER NOT NULL",
        "publish_fingerprints_lookup_idx",
    ):
        if token not in schema:
            fail(f"schema missing {token}")

    migration = WORKER / "migrations" / "d1" / "0001_publish_fingerprints.sql"
    if not migration.is_file():
        fail("missing D1 migration migrations/d1/0001_publish_fingerprints.sql")
    block = schema[schema.index("CREATE TABLE IF NOT EXISTS publish_fingerprints"):].strip()
    if block not in migration.read_text(encoding="utf-8"):
        fail("D1 migration differs from schema.sql publish_fingerprints block")
    readme = (WORKER / "README.md").read_text(encoding="utf-8")
    if "0001_publish_fingerprints.sql" not in readme or "live in production" not in readme:
        fail("README must document migration-before-deploy order and live production status")

    print(
        "OK cloudflare-publish-fingerprint "
        "incident=2026-09-13 repeats_blocked=5 extra_publishes=0 "
        "window=72h python_definition_match=YES"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
