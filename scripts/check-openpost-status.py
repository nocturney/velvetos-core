#!/usr/bin/env python3
"""OpenPost status sensor: records must say PAUSED / LIVE not verified.

Owner freeze (2026-09-26): OpenPost publishing is paused, staging is v6.2.0
(PR #342 evidence), production runtime and LIVE status are unknown / not
verified. This sensor fails if any record, README row or brief feed source
drifts back to treating OpenPost as LIVE or as an active send route. Read-only.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "openpost-status"
UNK = "unknown_not_verified"
ACTIVE_MODES = {"primary-control-plane", "staging", "shadow", "degraded"}


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


def problems_for(op: dict, readme: str, playbook: str, feed: dict) -> list[str]:
    p: list[str] = []
    st = op.get("status") or {}
    if st.get("state") != "paused":
        p.append("OPENPOST.json status.state must be 'paused'")
    if st.get("publishingFrozen") is not True:
        p.append("OPENPOST.json status.publishingFrozen must be true")
    if st.get("liveStatus") != UNK:
        p.append(f"OPENPOST.json status.liveStatus must be {UNK}")
    if st.get("productionVersion") != UNK:
        p.append(f"OPENPOST.json status.productionVersion must be {UNK}")
    if st.get("stagingVersion") != "v6.2.0":
        p.append("OPENPOST.json status.stagingVersion must be v6.2.0 (PR #342 evidence)")
    if op.get("integrationMode") in ACTIVE_MODES or op.get("integrationMode") != "paused":
        p.append("OPENPOST.json integrationMode must be 'paused' (not a send route)")
    rt = op.get("runtime") or {}
    if rt.get("liveVerified") is not False or "liveVerifiedAt" in rt:
        p.append("runtime.liveVerified must be false with no liveVerifiedAt")
    if rt.get("liveStatus") != UNK:
        p.append(f"runtime.liveStatus must be {UNK}")
    ph = rt.get("productionHost") or {}
    if "LIVE" in str(ph.get("status", "")) or ph.get("version") != UNK:
        p.append("runtime.productionHost status/version must be unknown_not_verified")
    fo = rt.get("grokInstagramFailover") or {}
    if str(fo.get("status", "")).startswith("READY"):
        p.append("grokInstagramFailover must not claim READY while OpenPost is frozen")
    if str((op.get("releasePolicy") or {}).get("currentBaseline")) != UNK:
        p.append("releasePolicy.currentBaseline must not claim a verified runtime version")
    stray = _live_true_paths(op)
    if stray:
        p.append(f"liveVerified=true must not appear in OPENPOST.json: {stray}")
    rows = [l for l in readme.splitlines() if l.startswith("<tr><td><strong>OpenPost Publishing Control Plane</strong>")]
    if len(rows) != 2:
        p.append(f"README must have 2 OpenPost capability rows (he/en), found {len(rows)}")
    for row in rows:
        if "PAUSED (PUBLISHING FROZEN) / LIVE NOT VERIFIED" not in row:
            p.append("README OpenPost row must say PAUSED (PUBLISHING FROZEN) / LIVE NOT VERIFIED")
        for bad in ("v4.35.0 runs", "v4.35.0 רץ", "LIVE_VERIFIED", "PROD OAUTH READY"):
            if bad in row:
                p.append(f"README OpenPost row carries stale claim {bad!r}")
    if "PAUSED (publishing frozen)" not in playbook:
        p.append("OPENPOST.md must state PAUSED (publishing frozen)")
    if "## Current runtime decision" in playbook:
        p.append("OPENPOST.md must not present the 2026-09-20 record as the current runtime decision")
    if ((feed.get("openpost") or {}).get("state")) != "paused":
        p.append("packages/vfbriefux/FEED-SOURCE.json openpost.state must be 'paused'")
    return p


def main() -> int:
    op = json.loads((ROOT / "packages/vfigos/OPENPOST.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    playbook = (ROOT / "packages/vfigos/OPENPOST.md").read_text(encoding="utf-8")
    feed = json.loads((ROOT / "packages/vfbriefux/FEED-SOURCE.json").read_text(encoding="utf-8"))

    probs = problems_for(op, readme, playbook, feed)
    if probs:
        for x in probs:
            print(f"FAIL {NAME}: {x}", file=sys.stderr)
        return 1

    # Negative controls: each stale claim must be caught.
    cases = 0
    for label, mutate in (
        ("liveVerified true", lambda o: o["runtime"].__setitem__("liveVerified", True)),
        ("primary mode", lambda o: o.__setitem__("integrationMode", "primary-control-plane")),
        ("host live", lambda o: o["runtime"]["productionHost"].__setitem__("status", "HOST_READY_LIVE_VERIFIED")),
        ("state active", lambda o: o["status"].__setitem__("state", "active")),
        ("nested live", lambda o: o["deliveryApproval"]["liveEvidence"].__setitem__("liveVerified", True)),
    ):
        bad = copy.deepcopy(op)
        mutate(bad)
        if not problems_for(bad, readme, playbook, feed):
            print(f"FAIL {NAME}: negative control not caught: {label}", file=sys.stderr)
            return 1
        cases += 1
    stale_row = readme.replace("PAUSED (PUBLISHING FROZEN) / LIVE NOT VERIFIED", "PROD OAUTH READY / LIVE BLOCKED", 1)
    if not problems_for(op, stale_row, playbook, feed):
        print(f"FAIL {NAME}: negative control not caught: stale README row", file=sys.stderr)
        return 1
    if not problems_for(op, readme, playbook, {"openpost": {"state": "active"}}):
        print(f"FAIL {NAME}: negative control not caught: feed active", file=sys.stderr)
        return 1
    cases += 2
    print(f"OK {NAME} state=paused live={UNK} staging=v6.2.0 integrationMode=paused negative_controls={cases}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
