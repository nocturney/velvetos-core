#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vf_runtime_receipt_policy import build_runtime_proof_request, proof_scope_line  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "automation/grok/manifest.json"
RUNTIME = ROOT / "packages/vfharness/state/runtime/grok-production-scheduler.json"

# Current protected set size. 8 -> 9 on 2026-09-29 (Runtime Receipts Refresh,
# owner-approved). A readback is compared against the routines that were
# protected at its observedAt (manifest routine protectedFrom), so a real
# pre-change readback stays valid and no readback is ever back-filled.
PROTECTED_ROUTINE_COUNT = 9


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def fail(message: str) -> None:
    raise SystemExit(f"GROK PROVIDER READBACK FAIL: {message}")


def parse_time(value: object, label: str = "runtime receipt observed_at") -> datetime:
    if not isinstance(value, str):
        fail(f"{label} missing")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        fail(f"{label} invalid")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def main() -> int:
    try:
        proof = build_runtime_proof_request()
    except ValueError as exc:
        fail(str(exc))
    require_runtime = proof.requires_component("grok-production-scheduler", implied_if_live=True)

    manifest = load(MANIFEST)
    latest = manifest.get("latestProviderReadback") or {}
    if latest.get("status") != "live_verified":
        fail("manifest latestProviderReadback is not live_verified")
    artifact_rel = latest.get("artifact")
    if not isinstance(artifact_rel, str) or not artifact_rel:
        fail("manifest readback artifact missing")
    artifact = ROOT / artifact_rel
    if not artifact.is_file():
        fail(f"readback artifact missing: {artifact_rel}")

    readback = load(artifact)
    if readback.get("schema") != "vf.grok.provider-readback.v1":
        fail("unexpected readback schema")
    if readback.get("status") != "LIVE_PROVIDER_READBACK_PASS":
        fail("provider readback not PASS")
    if readback.get("signedIn") is not True:
        fail("Grok Bot renderer was not signed in")
    if readback.get("rendererTimeZone") != manifest.get("timezone"):
        fail("renderer timezone differs from manifest")
    if (readback.get("transport") or {}).get("modelPromptSent") is not False:
        fail("readback must not rely on a model prompt")
    if (readback.get("verificationScope") or {}).get("promptBodyParity") is not False:
        fail("readback must not overclaim prompt-body parity")

    readback_at = parse_time(readback.get("observedAt"), "readback observedAt")
    now = datetime.now(timezone.utc)
    rows = manifest.get("routines") or []
    expected_all = {}
    required = {}
    pending = []
    for row in rows:
        rid = row["id"]
        spec = (row["title"], row["cadence"], bool(row["enabled"]))
        expected_all[rid] = spec
        since = row.get("protectedFrom")
        if since is None:
            required[rid] = spec
            continue
        since_at = parse_time(since, f"{rid} protectedFrom")
        if since_at > now:
            fail(f"{rid} protectedFrom is in the future")
        if since_at <= readback_at:
            required[rid] = spec
        else:
            pending.append(rid)

    if len(expected_all) != PROTECTED_ROUTINE_COUNT:
        fail(f"manifest must list {PROTECTED_ROUTINE_COUNT} protected routines, got {len(expected_all)}")
    if (manifest.get("protectedSet") or {}).get("count") != PROTECTED_ROUTINE_COUNT:
        fail("manifest protectedSet.count differs from the current protected routine count")

    observed = {}
    for row in readback.get("protectedRoutines") or []:
        rid = row.get("providerRoutineId")
        observed[rid] = (
            row.get("title"),
            row.get("expectedCadence"),
            bool(row.get("enabled")),
            bool(row.get("matchesCanonicalClock")),
        )
    if set(required) != set(observed):
        fail(
            "protected routine IDs differ from the set protected at readback time: "
            f"required={sorted(required)} observed={sorted(observed)}"
        )
    for rid, (title, cadence, enabled) in required.items():
        actual = observed[rid]
        if actual[:3] != (title, cadence, enabled) or actual[3] is not True:
            fail(f"protected routine drift: {rid}")
    if readback.get("protectedRoutineCount") != len(required):
        fail("readback protectedRoutineCount differs from its protected routine list")
    if latest.get("protectedRoutineCount") != len(required):
        fail("manifest latestProviderReadback.protectedRoutineCount differs from the readback artifact")

    retired_expected = {
        row["id"]: bool(row.get("desiredEnabled"))
        for row in manifest.get("retiredRoutines") or []
    }
    retired_observed = {
        row.get("providerRoutineId"): bool(row.get("enabled"))
        for row in readback.get("retiredRoutines") or []
    }
    if retired_expected.get("openpost-release-watch") is not False:
        fail("manifest must keep OpenPost watch retired")
    if retired_observed.get("openpost-release-watch") is not False:
        fail("live OpenPost Release Watch is not disabled")

    runtime_state = "NOT_REQUIRED"
    if require_runtime:
        if not RUNTIME.is_file():
            fail("runtime Grok scheduler receipt missing for required dependency")
        try:
            runtime = load(RUNTIME)
        except Exception as exc:
            fail(f"runtime Grok scheduler receipt invalid: {exc}")
        if runtime.get("component_id") != "grok-production-scheduler" or runtime.get("state") != "healthy":
            fail("runtime Grok scheduler receipt is not healthy")
        if (runtime.get("evidence") or {}).get("artifact") != artifact_rel:
            fail("runtime receipt does not point to provider readback artifact")
        age_hours = (now - parse_time(runtime.get("observed_at"))).total_seconds() / 3600
        if age_hours < -0.25 or age_hours > 24:
            fail(f"runtime receipt freshness invalid: {age_hours:.1f}h")
        runtime_state = "PASS"

    print(proof_scope_line(proof))
    print(
        "GROK PROVIDER READBACK PASS "
        f"protected={len(expected_all)} readback-verified={len(required)} "
        f"pending-first-readback={','.join(pending) or 'none'} "
        f"openpost=disabled timezone={readback.get('rendererTimeZone')} "
        f"proof={proof.status} runtime_health={runtime_state} "
        "prompt-body-parity=not-claimed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
