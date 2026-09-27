#!/usr/bin/env python3
"""Validate VelvetOS policy registries and optionally enforce the Stage 0 policy-creation freeze."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "packages" / "velvetos" / "policy"
POLICIES = POLICY_DIR / "policy-registry.json"
SENSORS = POLICY_DIR / "sensor-registry.json"
ARTIFACTS = POLICY_DIR / "artifact-retention.json"
SCHEMAS = POLICY_DIR / "schema"
REPORTS = POLICY_DIR / "reports"
EXPECTED_REPORTS = {
    "authority-graph.json",
    "sensor-coverage-graph.json",
    "coverage-report.json",
    "conflict-report.json",
    "artifact-inventory.json",
    "ci-baseline.json",
    "baseline-snapshot.json",
    "migration-map.json",
}

RISK = {"critical", "high", "medium", "low"}
STATUS = {"active", "conflicted", "deprecated", "temporary_hotfix"}
FALLBACK = {"FULL_SUITE", "FULL_DOMAIN", "ALWAYS_ON"}
MAPPING = {"broad_legacy_baseline", "mapped", "legacy", "deprecated"}
POLICY_REF = re.compile(r"policy_id\s*[:=]\s*([a-z0-9]+(?:[._-][a-z0-9]+)*)", re.I)
RESERVED = re.compile(
    r"authorized_for_tool_publish|approved_for_manual_posting|standingAuthorization|"
    r"publishAuthorized|publication_authorized|review_delivery_authorized",
    re.I,
)
NORMATIVE = re.compile(
    r"\b(?:ALLOW|DENY|MUST|REQUIRED|FORBIDDEN|AUTHORIZED|APPROVAL REQUIRED)\b|"
    r"(?:אסור|חובה|מותר|דורש(?:ת)? אישור|אישור בעלים)",
    re.I,
)
EXTERNAL = re.compile(
    r"publish|send|delete|payment|cost|billing|credential|permission|secret|boost|"
    r"whatsapp|instagram|gmail|פרסו|שליח|מחיק|מחוק|תשלו|עלות|הרשא|סוד|וואטסאפ|אינסטגרם|ג.?ימייל",
    re.I,
)

def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"{path.relative_to(ROOT)}: invalid JSON: {exc}") from exc


def existing_repo_path(value: str) -> bool:
    return bool(value) and (ROOT / value).exists()


def require(condition: bool, message: str, problems: list[str]) -> None:
    if not condition:
        problems.append(message)


def validate_registries() -> tuple[list[str], set[str]]:
    problems: list[str] = []
    policies = load(POLICIES)
    sensors = load(SENSORS)
    artifacts = load(ARTIFACTS)

    require(policies.get("schema_version") == 1, "policy registry schema_version", problems)
    require(
        policies.get("decision_ownership") == "REFERENCES_ONLY_DO_NOT_DUPLICATE_POLICY_DECISIONS",
        "policy registry must remain references-only",
        problems,
    )
    rows = policies.get("policies")
    require(isinstance(rows, list), "policy registry policies must be a list", problems)
    rows = rows if isinstance(rows, list) else []
    policy_ids = [row.get("policy_id") for row in rows if isinstance(row, dict)]
    require(len(policy_ids) == len(set(policy_ids)), "duplicate policy_id", problems)
    known_policies = {value for value in policy_ids if isinstance(value, str)}

    for row in rows:
        if not isinstance(row, dict):
            problems.append("policy row must be object")
            continue
        pid = row.get("policy_id")
        require(isinstance(pid, str) and bool(pid), "policy_id missing", problems)
        require(row.get("status") in STATUS, f"{pid}: invalid status", problems)
        require(row.get("risk_class") in RISK, f"{pid}: invalid risk_class", problems)
        authorities = row.get("authority_locations")
        require(isinstance(authorities, list) and bool(authorities), f"{pid}: authority_locations required", problems)
        if isinstance(authorities, list):
            for path in authorities:
                require(isinstance(path, str) and existing_repo_path(path), f"{pid}: missing authority {path}", problems)
        machine = row.get("machine_policy_locations")
        require(isinstance(machine, list), f"{pid}: machine_policy_locations must be list", problems)
        if isinstance(machine, list):
            for path in machine:
                require(isinstance(path, str) and existing_repo_path(path), f"{pid}: missing machine policy {path}", problems)
        if row.get("status") == "temporary_hotfix":
            meta = row.get("temporary_metadata")
            require(isinstance(meta, dict), f"{pid}: temporary_metadata required", problems)
            if isinstance(meta, dict):
                for key in ("source_authority", "migration_target", "review_at", "expiry_behavior"):
                    require(bool(meta.get(key)), f"{pid}: hotfix {key} required", problems)
                require(meta.get("review_at") != meta.get("expires_at"), f"{pid}: review_at must not be treated as expires_at", problems)

    sensor_rows = sensors.get("sensors")
    require(sensors.get("schema_version") == 1, "sensor registry schema_version", problems)
    require(sensors.get("suite_runner") == "scripts/check-all.py", "suite runner mismatch", problems)
    require(isinstance(sensor_rows, list), "sensor registry sensors must be list", problems)
    sensor_rows = sensor_rows if isinstance(sensor_rows, list) else []
    sensor_ids = [row.get("id") for row in sensor_rows if isinstance(row, dict)]
    require(len(sensor_ids) == len(set(sensor_ids)), "duplicate sensor id", problems)
    registered = {row.get("path") for row in sensor_rows if isinstance(row, dict)}
    live = {
        p.relative_to(ROOT).as_posix()
        for p in (ROOT / "scripts").glob("check-*.py")
        if p.name != "check-all.py"
    }
    require(registered == live, f"sensor registry mismatch missing={sorted(live-registered)} extra={sorted(registered-live)}", problems)

    sensor_id_set = {value for value in sensor_ids if isinstance(value, str)}
    for row in sensor_rows:
        if not isinstance(row, dict):
            problems.append("sensor row must be object")
            continue
        sid = row.get("id")
        path = row.get("path")
        require(isinstance(path, str) and existing_repo_path(path), f"{sid}: sensor path missing", problems)
        require(isinstance(path, str) and sid == Path(path).stem, f"{sid}: id/path mismatch", problems)
        require(isinstance(row.get("owns"), list) and bool(row.get("owns")), f"{sid}: owns required", problems)
        require(isinstance(row.get("triggered_by"), list) and bool(row.get("triggered_by")), f"{sid}: triggered_by required", problems)
        require(isinstance(row.get("depends_on"), list), f"{sid}: depends_on must be list", problems)
        require(isinstance(row.get("enforces"), list), f"{sid}: enforces must be list", problems)
        for policy_id in row.get("enforces") or []:
            require(policy_id in known_policies, f"{sid}: unknown enforced policy {policy_id}", problems)
        require(row.get("risk") in RISK, f"{sid}: invalid risk", problems)
        timeout = row.get("timeout_seconds")
        require(type(timeout) is int and 1 <= timeout <= 1800, f"{sid}: invalid timeout", problems)
        require(row.get("fallback_scope") in FALLBACK, f"{sid}: invalid fallback_scope", problems)
        require(row.get("mapping_state") in MAPPING, f"{sid}: invalid mapping_state", problems)
        if row.get("mapping_state") == "broad_legacy_baseline":
            require(row.get("triggered_by") == ["**"], f"{sid}: baseline sensor must fail broad", problems)

    for row in rows:
        for item in row.get("enforced_by") or []:
            require(isinstance(item, dict), f"{row.get('policy_id')}: invalid enforcer", problems)
            if not isinstance(item, dict):
                continue
            kind = item.get("kind")
            require(kind in {"sensor", "runtime", "workflow"}, f"{row.get('policy_id')}: invalid enforcer kind", problems)
            if kind == "sensor":
                require(item.get("id") in sensor_id_set, f"{row.get('policy_id')}: unknown sensor enforcer {item.get('id')}", problems)
            else:
                require(existing_repo_path(item.get("path", "")), f"{row.get('policy_id')}: missing enforcer path {item.get('path')}", problems)

    entries = artifacts.get("entries")
    require(artifacts.get("schema_version") == 1, "artifact registry schema_version", problems)
    require(isinstance(entries, list), "artifact retention entries must be list", problems)
    entries = entries if isinstance(entries, list) else []
    artifact_ids = [row.get("artifact_class_id") for row in entries if isinstance(row, dict)]
    require(len(artifact_ids) == len(set(artifact_ids)), "duplicate artifact_class_id", problems)

    for row in entries:
        if not isinstance(row, dict):
            problems.append("artifact row must be object")
            continue
        aid = row.get("artifact_class_id")
        require(isinstance(row.get("match"), list) and bool(row.get("match")), f"{aid}: match required", problems)
        require(bool(row.get("classification")), f"{aid}: classification required", problems)
        require(bool(row.get("current_storage")), f"{aid}: current_storage required", problems)
        require(bool(row.get("target_storage")), f"{aid}: target_storage required", problems)
        require(bool(row.get("retention_class")), f"{aid}: retention_class required", problems)
        require(row.get("deletion_authorized") is False, f"{aid}: Stage 0 cannot authorize deletion", problems)
        refs = row.get("policy_refs")
        require(isinstance(refs, list), f"{aid}: policy_refs must be list", problems)
        for policy_id in refs or []:
            require(policy_id in known_policies, f"{aid}: unknown policy ref {policy_id}", problems)

    expected_schemas = {
        "policy-registry.schema.json",
        "sensor-registry.schema.json",
        "artifact-retention.schema.json",
        "instagram-publish.schema.json",
        "instagram-publish-context.schema.json",
    }
    actual_schemas = {p.name for p in SCHEMAS.glob("*.json")}
    require(expected_schemas <= actual_schemas, f"missing schemas {sorted(expected_schemas-actual_schemas)}", problems)
    for name in expected_schemas:
        path = SCHEMAS / name
        if path.exists():
            schema = load(path)
            require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", f"{name}: draft mismatch", problems)

    instagram_policy_path = POLICY_DIR / "instagram.publish.json"
    require(instagram_policy_path.is_file(), "instagram.publish machine policy missing", problems)
    if instagram_policy_path.is_file():
        instagram_policy = load(instagram_policy_path)
        require(instagram_policy.get("policy_id") == "instagram.publish", "instagram.publish policy_id mismatch", problems)
        require(instagram_policy.get("version") == 1, "instagram.publish version mismatch", problems)
        require(instagram_policy.get("decision_values") == ["ALLOW", "DENY", "REQUIRE_OWNER_APPROVAL"], "instagram.publish decision values mismatch", problems)
        row = next((x for x in rows if x.get("policy_id") == "instagram.publish"), None)
        require(row is not None and "packages/velvetos/policy/instagram.publish.json" in row.get("machine_policy_locations", []), "instagram.publish registry binding missing", problems)
        for rel_path in (
            "packages/velvetos/policy/instagram-publish-evaluator.mjs",
            "packages/velvetos/policy/instagram-publish-test-vectors.json",
            "packages/velvetos/policy/test-instagram-publish-policy.mjs",
            "scripts/vf_instagram_publish_policy.mjs",
        ):
            require(existing_repo_path(rel_path), f"instagram.publish component missing: {rel_path}", problems)

    report_names = {p.name for p in REPORTS.glob("*.json")} if REPORTS.is_dir() else set()
    require(EXPECTED_REPORTS <= report_names, f"missing policy reports {sorted(EXPECTED_REPORTS-report_names)}", problems)
    if EXPECTED_REPORTS <= report_names:
        coverage = load(REPORTS / "coverage-report.json")
        require(
            coverage.get("runnable_sensor_count") == len(sensor_rows)
            and coverage.get("registered_sensor_count") == len(sensor_rows)
            and coverage.get("omitted_sensors") == [],
            "coverage report no longer matches sensor registry",
            problems,
        )
        authority = load(REPORTS / "authority-graph.json")
        require(authority.get("policy_count") == len(rows), "authority graph policy count mismatch", problems)
        sensor_graph = load(REPORTS / "sensor-coverage-graph.json")
        require(sensor_graph.get("sensor_count") == len(sensor_rows), "sensor coverage graph count mismatch", problems)
        conflicts = load(REPORTS / "conflict-report.json")
        conflict_ids = {x.get("id") for x in conflicts.get("conflicts", [])}
        require("instagram-publish-split-brain" in conflict_ids, "Stage 0 publish conflict report missing", problems)
        inventory = load(REPORTS / "artifact-inventory.json")
        require(inventory.get("stage0_action") == "CLASSIFICATION_ONLY_NO_MOVE_NO_DELETE", "Stage 0 artifact action drifted", problems)
        ci = load(REPORTS / "ci-baseline.json")
        require(bool(ci.get("cutoff_utc")) and bool(ci.get("runs")), "CI baseline cutoff/runs missing", problems)
        require(ci.get("branch_protection", {}).get("state") == "UNPROTECTED", "Stage 0 branch baseline changed in report", problems)
        migration = load(REPORTS / "migration-map.json")
        require([x.get("stage") for x in migration.get("stages", [])] == list(range(1, 10)), "migration map stages must be 1..9", problems)
        generator = ROOT / "scripts" / "generate-policy-reports.py"
        require(generator.is_file(), "policy report generator missing", problems)
        if generator.is_file():
            proc = subprocess.run(
                [sys.executable, str(generator), "--check"],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=60,
            )
            require(proc.returncode == 0, "policy reports not reproducible: " + (proc.stderr or proc.stdout).strip()[:500], problems)

    return problems, known_policies


def diff_added_markdown(base: str, head: str) -> dict[str, list[str]]:
    proc = subprocess.run(
        ["git", "diff", "--unified=0", "--no-color", base, head, "--", "*.md", "*.mdc"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise ValueError(proc.stderr.strip() or "git diff failed")
    current: str | None = None
    added: dict[str, list[str]] = {}
    for line in proc.stdout.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
            added.setdefault(current, [])
        elif current and line.startswith("+") and not line.startswith("+++"):
            added[current].append(line[1:])
    return added

def is_normative_external(line: str) -> bool:
    return bool(RESERVED.search(line) or (NORMATIVE.search(line) and EXTERNAL.search(line)))


def freeze_selftest() -> list[str]:
    problems: list[str] = []
    cases = {
        "ALLOW publish after all gates": True,
        "אסור למחוק ללא אישור בעלים": True,
        "authorized_for_tool_publish is the state": True,
        "This paragraph explains a registry field.": False,
    }
    for text, expected in cases.items():
        if is_normative_external(text) is not expected:
            problems.append(f"freeze classifier selftest mismatch: {text}")
    if POLICY_REF.findall("policy_id: instagram.publish") != ["instagram.publish"]:
        problems.append("policy_id parser selftest failed")
    return problems


def freeze_check(base: str, head: str, known_policies: set[str]) -> list[str]:
    problems: list[str] = []
    canonical_prefixes = ("constitution/", "packages/velvetos/policy/")
    canonical_exact = {"office/control/POLICY.md"}
    for path, lines in diff_added_markdown(base, head).items():
        if path in canonical_exact or path.startswith(canonical_prefixes):
            continue
        normative = [line for line in lines if is_normative_external(line)]
        if not normative:
            continue
        try:
            proc = subprocess.run(
                ["git", "show", f"{head}:{path}"],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=30,
            )
        except OSError as exc:
            problems.append(f"{path}: cannot read head file: {exc}")
            continue
        content = proc.stdout if proc.returncode == 0 else "\n".join(lines)
        refs = set(POLICY_REF.findall(content))
        valid = sorted(refs & known_policies)
        if not valid:
            sample = normative[0].strip()[:180]
            problems.append(f"{path}: new normative external-effect text lacks a valid policy_id reference: {sample}")
    return problems


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base")
    p.add_argument("--head")
    return p


def main() -> int:
    args = parser().parse_args()
    if bool(args.base) != bool(args.head):
        print("FAIL --base and --head must be supplied together", file=sys.stderr)
        return 2
    problems, known_policies = validate_registries()
    problems.extend(freeze_selftest())
    if args.base and args.head:
        problems.extend(freeze_check(args.base, args.head, known_policies))
    if problems:
        for problem in problems:
            print(f"FAIL {problem}", file=sys.stderr)
        return 1
    mode = " + policy-creation-freeze" if args.base else ""
    print(
        f"OK policy-architecture policies={len(known_policies)} "
        f"sensors={len(load(SENSORS)['sensors'])} "
        f"artifact_classes={len(load(ARTIFACTS)['entries'])}{mode}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
