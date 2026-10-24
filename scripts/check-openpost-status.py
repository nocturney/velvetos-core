#!/usr/bin/env python3
"""OpenPost retirement sensor: OpenPost must stay absent and non-runnable.

Owner decision (2026-10-23): OpenPost is retired from active VelvetOS source.
Cloudflare Instagram Publisher is the only scheduling, queue and retry path.
This sensor fails if an obsolete OpenPost runner, failover file or scheduled
hook reappears in active source, if the retired registry regains an executable
or authority flag, or if the Morning Green feed treats OpenPost as active.
Read-only.
"""

from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "openpost-status"
UNK = "unknown_not_verified"

REMOVED_PATHS = (
    "packages/vfigos/openpost",
    "packages/vfigos/openpost_morning_snapshot.py",
    "packages/vfigos/run_openpost_morning_snapshot.ps1",
    "packages/vfigos/materialize_openpost_morning_thumbnails.ps1",
    "packages/vfigos/failover/grok_client.py",
    "packages/vfigos/failover/grok_instagram_failover.py",
    "packages/vfigos/failover/failover_watch.py",
    "packages/vfigos/failover/openpost_failover_state.py",
    "packages/vfigos/failover/prepare_manifest.py",
    "packages/vfigos/failover/trusted_dispatch.py",
    "packages/vfigos/failover/instagram_mcp_remote.py",
    "packages/vfigos/failover/README.md",
    "packages/vfigos/failover/windows/grok_boot_supervisor.py",
)
# Tokens that only appear in the removed runners, their deploy scripts and their
# scheduled hooks. Any hit in active executable source means a runner came back.
OBSOLETE_TOKENS = (
    "grok_instagram_failover",
    "failover_watch",
    "openpost_failover_state",
    "prepare_manifest",
    "trusted_dispatch",
    "grok_client",
    "instagram_mcp_remote",
    "openpost_morning_snapshot",
    "materialize_openpost_morning",
    "run_openpost_morning",
    "grok_boot_supervisor",
    "vfbridge6",
    "vf-openpost-token",
    "openpost-prod",
)
SCAN_SUFFIXES = (".py", ".ps1", ".sh", ".yml", ".yaml")
SCAN_SKIP_DIRS = {".git", "state", "evidence", "out", "reports", "node_modules"}
# These two sensors name the obsolete tokens on purpose to assert their absence.
SCAN_EXEMPT = {"scripts/check-openpost-status.py", "scripts/check-grok-boot-hardening.py"}
AUTHORITY_FLAGS = (
    "creativeAuthority",
    "qualityGateAuthority",
    "routingAuthority",
    "newSchedulesAllowed",
    "queueAuthority",
    "retryAuthority",
    "failoverTarget",
    "releaseWatchEnabled",
    "healthDependency",
    "credentialsMaintenance",
    "monitoringEnabled",
    "upgradeWorkAllowed",
)


def _live_true_paths(obj, path="$"):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "liveVerified" and v is True:
                out.append(f"{path}.{k}")
            out.extend(_live_true_paths(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(_live_true_paths(v, f"{path}[{i}]"))
    return out


def problems_for(op: dict, playbook: str, feed: dict) -> list[str]:
    p: list[str] = []
    st = op.get("status") or {}
    if st.get("state") != "retired":
        p.append("OPENPOST.json status.state must be 'retired'")
    if st.get("runnable") is not False:
        p.append("OPENPOST.json status.runnable must be false")
    if st.get("publishingFrozen") is not True:
        p.append("OPENPOST.json status.publishingFrozen must be true")
    if st.get("liveStatus") != UNK:
        p.append(f"OPENPOST.json status.liveStatus must be {UNK}")
    if st.get("productionVersion") != UNK:
        p.append(f"OPENPOST.json status.productionVersion must be {UNK}")
    if op.get("integrationMode") != "retired":
        p.append("OPENPOST.json integrationMode must be 'retired' (not a send route)")
    for key in AUTHORITY_FLAGS:
        if op.get(key) is not False:
            p.append(f"OPENPOST.json {key} must be false")
    if "runtime" in op or "deliveryApproval" in op:
        p.append("retired OpenPost record must not carry runtime or delivery state")
    stray = _live_true_paths(op)
    if stray:
        p.append(f"liveVerified=true must not appear in OPENPOST.json: {stray}")
    if "RETIRED" not in playbook:
        p.append("OPENPOST.md must state RETIRED")
    if "Cloudflare" not in playbook:
        p.append("OPENPOST.md must name Cloudflare Instagram Publisher as the replacement")
    if ((feed.get("openpost") or {}).get("state")) != "retired":
        p.append("packages/vfbriefux/FEED-SOURCE.json openpost.state must be 'retired'")
    return p


def removed_present(root: Path) -> list[str]:
    return [f"removed OpenPost artifact is present: {rel}" for rel in REMOVED_PATHS if (root / rel).exists()]


def obsolete_references(root: Path) -> list[str]:
    hits: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SCAN_SKIP_DIRS]
        for name in filenames:
            if not name.endswith(SCAN_SUFFIXES):
                continue
            path = Path(dirpath) / name
            rel = path.relative_to(root).as_posix()
            if rel in SCAN_EXEMPT:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for token in OBSOLETE_TOKENS:
                if token in text:
                    hits.append(f"{rel} references obsolete OpenPost runner token {token!r}")
    return hits


def main() -> int:
    op = json.loads((ROOT / "packages/vfigos/OPENPOST.json").read_text(encoding="utf-8"))
    playbook = (ROOT / "packages/vfigos/OPENPOST.md").read_text(encoding="utf-8")
    feed = json.loads((ROOT / "packages/vfbriefux/FEED-SOURCE.json").read_text(encoding="utf-8"))

    probs = problems_for(op, playbook, feed) + removed_present(ROOT) + obsolete_references(ROOT)
    if probs:
        for x in probs:
            print(f"FAIL {NAME}: {x}", file=sys.stderr)
        return 1

    # Negative controls: each reintroduced OpenPost claim or runner must be caught.
    cases = 0
    for label, mutate in (
        ("state active", lambda o: o["status"].__setitem__("state", "active")),
        ("runnable true", lambda o: o["status"].__setitem__("runnable", True)),
        ("primary mode", lambda o: o.__setitem__("integrationMode", "primary-control-plane")),
        ("scheduler authority", lambda o: o.__setitem__("newSchedulesAllowed", True)),
        ("failover target", lambda o: o.__setitem__("failoverTarget", True)),
        ("host live", lambda o: o.__setitem__("runtime", {"productionHost": {"status": "HOST_READY_LIVE_VERIFIED"}})),
        ("nested live", lambda o: o.__setitem__("liveEvidence", {"liveVerified": True})),
    ):
        bad = copy.deepcopy(op)
        mutate(bad)
        if not problems_for(bad, playbook, feed):
            print(f"FAIL {NAME}: negative control not caught: {label}", file=sys.stderr)
            return 1
        cases += 1
    if not problems_for(op, playbook.replace("RETIRED", "PAUSED"), feed):
        print(f"FAIL {NAME}: negative control not caught: playbook not retired", file=sys.stderr)
        return 1
    if not problems_for(op, playbook, {"openpost": {"state": "paused"}}):
        print(f"FAIL {NAME}: negative control not caught: feed not retired", file=sys.stderr)
        return 1
    cases += 2
    with tempfile.TemporaryDirectory() as tmp:
        fixture = Path(tmp)
        (fixture / "packages/vfigos/failover").mkdir(parents=True)
        (fixture / "packages/vfigos/failover/failover_watch.py").write_text("# failover_watch runner\n", encoding="utf-8")
        if not removed_present(fixture) or not obsolete_references(fixture):
            print(f"FAIL {NAME}: negative control not caught: reintroduced runner", file=sys.stderr)
            return 1
        cases += 1
    print(f"OK {NAME} state=retired runnable=false live={UNK} removed_paths={len(REMOVED_PATHS)} tokens={len(OBSOLETE_TOKENS)} negative_controls={cases}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
