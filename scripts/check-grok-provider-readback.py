#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "automation/grok/manifest.json"
RUNTIME = ROOT / "packages/vfharness/state/runtime/grok-production-scheduler.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def fail(message: str) -> None:
    raise SystemExit(f"GROK PROVIDER READBACK FAIL: {message}")


def parse_time(value: object) -> datetime:
    if not isinstance(value, str):
        fail("runtime receipt observed_at missing")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        fail("runtime receipt observed_at invalid")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def main() -> int:
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

    expected = {
        row["id"]: (row["title"], row["cadence"], bool(row["enabled"]))
        for row in manifest.get("routines") or []
    }
    observed = {}
    for row in readback.get("protectedRoutines") or []:
        rid = row.get("providerRoutineId")
        observed[rid] = (
            row.get("title"),
            row.get("expectedCadence"),
            bool(row.get("enabled")),
            bool(row.get("matchesCanonicalClock")),
        )
    if set(expected) != set(observed):
        fail(f"protected routine IDs differ: expected={sorted(expected)} observed={sorted(observed)}")
    for rid, (title, cadence, enabled) in expected.items():
        actual = observed[rid]
        if actual[:3] != (title, cadence, enabled) or actual[3] is not True:
            fail(f"protected routine drift: {rid}")
    if len(expected) != 8 or readback.get("protectedRoutineCount") != 8:
        fail("protected routine count must remain eight")

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

    runtime = load(RUNTIME)
    if runtime.get("component_id") != "grok-production-scheduler" or runtime.get("state") != "healthy":
        fail("runtime Grok scheduler receipt is not healthy")
    if (runtime.get("evidence") or {}).get("artifact") != artifact_rel:
        fail("runtime receipt does not point to provider readback artifact")
    age_hours = (datetime.now(timezone.utc) - parse_time(runtime.get("observed_at"))).total_seconds() / 3600
    if age_hours < -0.25 or age_hours > 24:
        fail(f"runtime receipt freshness invalid: {age_hours:.1f}h")

    print(
        "GROK PROVIDER READBACK PASS "
        f"protected={len(expected)} openpost=disabled timezone={readback.get('rendererTimeZone')} "
        "prompt-body-parity=not-claimed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
