#!/usr/bin/env python3
"""Read-only checkpoint audit. No network, execution, state writes or publication.

Uses the existing checkpoint schema, with a fail-closed stdlib interpreter for
its current vocabulary. Local digest evidence verifies bytes, not task quality
or delivery. See vfharness/playbooks/skillstate.md for the report contract.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path, PureWindowsPath
import re
import stat
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = Path("packages/vfharness/templates/checkpoint.schema.json")
STATE_PATH = Path("packages/vfharness/state")
VOCABULARY = {
    "$schema", "$id", "title", "description", "type", "required",
    "additionalProperties", "properties", "items", "enum", "minLength", "maxItems",
}
TYPES = {"object", "array", "string", "null", "boolean", "integer", "number"}
DIGEST = re.compile(r"[0-9a-fA-F]{64}\Z")
URI = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
ARTIFACT_ERRORS = {"missing", "digest_mismatch", "invalid_reference", "invalid_evidence", "unreadable"}


class StateError(ValueError):
    """Invalid input or an unsupported schema, with no implicit fallback."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise StateError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise StateError(f"non-JSON numeric constant: {value}")


def _float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise StateError("JSON numeric value exceeds finite float range")
    return parsed


def read_json(path: Path) -> tuple[Any, str]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant, parse_float=_float)
    return value, hashlib.sha256(raw).hexdigest()


def check_schema(schema: Any, path: str = "$") -> None:
    """Reject unsupported keywords instead of silently weakening validation."""
    if not isinstance(schema, dict):
        raise StateError(f"{path}: expected schema object")
    unknown = set(schema) - VOCABULARY
    if unknown:
        raise StateError(f"{path}: unsupported schema keywords: {', '.join(sorted(unknown))}")
    if "$schema" in schema and schema["$schema"] != "https://json-schema.org/draft/2020-12/schema":
        raise StateError(f"{path}: unsupported schema dialect")
    types = schema.get("type", [])
    types = [types] if isinstance(types, str) else types
    if not isinstance(types, list) or any(not isinstance(t, str) or t not in TYPES for t in types):
        raise StateError(f"{path}: unsupported schema type")
    for key in ("minLength", "maxItems"):
        if key in schema and (type(schema[key]) is not int or schema[key] < 0):
            raise StateError(f"{path}.{key}: expected nonnegative integer")
    if "enum" in schema and (not isinstance(schema["enum"], list) or not schema["enum"]):
        raise StateError(f"{path}.enum: expected nonempty array")
    required = schema.get("required", [])
    if not isinstance(required, list) or any(not isinstance(k, str) for k in required):
        raise StateError(f"{path}.required: expected string array")
    props = schema.get("properties", {})
    if not isinstance(props, dict):
        raise StateError(f"{path}.properties: expected object")
    for key, child in props.items():
        check_schema(child, f"{path}.properties.{key}")
    if "items" in schema:
        check_schema(schema["items"], f"{path}.items")
    if "additionalProperties" in schema and type(schema["additionalProperties"]) is not bool:
        raise StateError(f"{path}.additionalProperties: only boolean supported")


def _is_type(value: Any, kind: str) -> bool:
    return {
        "object": isinstance(value, dict), "array": isinstance(value, list),
        "string": isinstance(value, str), "null": value is None,
        "boolean": type(value) is bool,
        "integer": type(value) is int or (type(value) is float and value.is_integer()),
        "number": type(value) in (int, float),
    }[kind]


def validate(value: Any, schema: dict, path: str = "$") -> list[str]:
    """Validate against a schema that has passed check_schema()."""
    errors: list[str] = []
    kinds = schema.get("type", [])
    kinds = [kinds] if isinstance(kinds, str) else kinds
    if kinds and not any(_is_type(value, kind) for kind in kinds):
        return [f"{path}: expected {' or '.join(kinds)}"]
    if "enum" in schema and not any(
        value == item and (type(value) is bool) == (type(item) is bool) for item in schema["enum"]
    ):
        errors.append(f"{path}: value is outside enum")
    if isinstance(value, str) and len(value) < schema.get("minLength", 0):
        errors.append(f"{path}: shorter than minLength")
    if isinstance(value, list):
        if len(value) > schema.get("maxItems", len(value)):
            errors.append(f"{path}: exceeds maxItems")
        if "items" in schema:
            for index, item in enumerate(value):
                errors.extend(validate(item, schema["items"], f"{path}[{index}]"))
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}.{key}: required field missing")
        props = schema.get("properties", {})
        for key, item in value.items():
            if key in props:
                errors.extend(validate(item, props[key], f"{path}.{key}"))
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}.{key}: additional property not allowed")
    return errors


def _display(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def inspect_artifact(reference: Any, evidence: Any, root: Path) -> dict:
    row: dict = {"reference": reference, "status": "invalid_reference"}
    if not isinstance(reference, str) or not reference.strip() or "\0" in reference:
        row["reason"] = "expected a nonempty file path or URI"
        return row
    # No stat or open outside the explicitly selected checkout root.
    if PureWindowsPath(reference).drive or reference.startswith("~"):
        row.update(status="unverified_other_environment", reason="path belongs to another environment")
        return row
    if URI.match(reference):
        row.update(status="unverified_external", reason="external reference; no network check performed")
        return row
    if re.search(r"\s--[A-Za-z]", reference) or any(mark in reference for mark in ("*", "?")):
        row.update(status="unverified_reference", reason="command or pattern is not an exact artifact path; not executed or expanded")
        return row
    try:
        path = Path(reference)
        path = (path if path.is_absolute() else root / path).resolve()
        if not path.is_relative_to(root):
            row.update(status="unverified_other_environment", reason="path is outside selected checkout")
            return row
        row["local_path"] = path.relative_to(root).as_posix()
        info = path.stat()
        if not stat.S_ISREG(info.st_mode):
            row.update(status="present_unverified", reason="not an individual regular file")
            return row
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        after = path.stat()
        if (info.st_ino, info.st_size, info.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
            row.update(status="unreadable", reason="file changed during inspection; retry a fresh read")
            return row
        actual = digest.hexdigest()
        row.update(sha256=actual, bytes=info.st_size)
        if evidence is None:
            row.update(status="present_unverified", reason="no expected SHA-256 recorded for this artifact")
        elif not isinstance(evidence, dict) or not isinstance(evidence.get("sha256"), str) or not DIGEST.fullmatch(evidence["sha256"]):
            row.update(status="invalid_evidence", reason="expected artifact_evidence entry with a 64-hex sha256")
        else:
            row["expected_sha256"] = evidence["sha256"].lower()
            row["status"] = "digest_verified" if actual == row["expected_sha256"] else "digest_mismatch"
    except FileNotFoundError:
        if evidence is None and "/" not in reference and not Path(reference).suffix:
            row.update(status="unverified_reference", reason="opaque identifier or filename without local evidence; not resolved")
        else:
            row.update(status="missing", reason="local file absent in selected checkout")
    except (OSError, ValueError, RuntimeError) as exc:
        row.update(status="unreadable", reason=str(exc))
    return row


def inspect_checkpoint(path: Path, root: Path, schema: dict) -> dict:
    row: dict = {
        "record_kind": "checkpoint",
        "source": _display(path, root), "source_sha256": None,
        "task_id": None, "reported_status": None, "last_updated": None,
        "schema_errors": [], "state_errors": [], "artifacts": [],
        "completion": "invalid", "verification_scope": "local artifact bytes only",
    }
    try:
        value, digest = read_json(path)
        row["source_sha256"] = digest
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        row["schema_errors"] = [f"cannot read checkpoint JSON: {exc}"]
        return row
    # Escalation histories share this folder but are not task checkpoints.
    if path.name.startswith("ladder-") and isinstance(value, list):
        errors = []
        rungs = {"retry_as_is", "retry_with_fallback", "downgrade_scope", "escalate_to_human"}
        for index, event in enumerate(value):
            prefix = f"$[{index}]"
            if not isinstance(event, dict):
                errors.append(f"{prefix}: expected ladder event object")
                continue
            rung = event.get("rung")
            if not isinstance(rung, str) or rung not in rungs:
                errors.append(f"{prefix}.rung: unknown ladder rung")
            try:
                timestamp = event.get("ts")
                if not isinstance(timestamp, str) or datetime.fromisoformat(timestamp).tzinfo is None:
                    raise ValueError("timestamp needs timezone")
            except ValueError:
                errors.append(f"{prefix}.ts: expected ISO timestamp with timezone")
            if rung == "escalate_to_human":
                if not isinstance(event.get("escalation_file"), str) or not event["escalation_file"].strip():
                    errors.append(f"{prefix}.escalation_file: required")
            elif type(event.get("ok")) is not bool:
                errors.append(f"{prefix}.ok: expected boolean")
            if rung == "retry_as_is" and (type(event.get("attempt")) is not int or event["attempt"] < 1):
                errors.append(f"{prefix}.attempt: expected positive integer")
        return {
            "record_kind": "ladder_event_log", "source": row["source"],
            "source_sha256": digest, "event_count": len(value), "event_errors": errors,
            "observation": "invalid" if errors else "observed",
            "verification_scope": "event log structure only; does not establish task completion",
        }
    row["schema_errors"] = validate(value, schema)
    if not isinstance(value, dict):
        return row
    row.update(task_id=value.get("task_id"), reported_status=value.get("status"), last_updated=value.get("last_updated"))
    status = value.get("status")
    if status == "done":
        for key, blocked in (
            ("gate", value.get("gate") is not None),
            ("unresolved", bool(value.get("unresolved"))),
            ("pulse", value.get("pulse") == "blocked"),
            ("outcome", value.get("outcome") in ("decision_gate", "escalation")),
        ):
            if blocked:
                row["state_errors"].append(f"$.{key}: incompatible with reported done")
    execution = value.get("execution_state")
    evidence = execution.get("artifact_evidence", {}) if isinstance(execution, dict) else {}
    if not isinstance(evidence, dict):
        row["state_errors"].append("$.execution_state.artifact_evidence: expected object keyed by artifact reference")
        evidence = {}
    artifacts = value.get("artifacts")
    if isinstance(artifacts, list):
        for ref in artifacts:
            row["artifacts"].append(inspect_artifact(ref, evidence.get(ref) if isinstance(ref, str) else None, root))
        for ref in evidence:
            if ref not in artifacts:
                row["state_errors"].append(f"artifact_evidence key is not a listed artifact: {ref}")
    if row["schema_errors"] or row["state_errors"]:
        return row
    if status in ("blocked", "escalated") or value.get("gate") is not None:
        row["completion"] = "blocked"
    elif status != "done":
        row["completion"] = "not_done"
    elif (row["artifacts"] and all(a["status"] == "digest_verified" for a in row["artifacts"])
          and isinstance(value.get("verification"), str) and value["verification"].strip()):
        row["completion"] = "local_artifacts_verified"
    else:
        row["completion"] = "unverified"
    return row


def audit(root: Path, paths: list[Path] | None = None) -> dict:
    root = root.resolve()
    schema_path = root / SCHEMA_PATH
    schema, schema_digest = read_json(schema_path)
    check_schema(schema)
    if paths is None:
        directory = root / STATE_PATH
        if not directory.is_dir():
            raise StateError(f"checkpoint directory missing: {STATE_PATH}")
        # Flat checkpoints and state/<task>/checkpoint.json are both in use.
        paths = sorted(directory.rglob("*.json"))
    if not paths:
        raise StateError("no checkpoint files selected")
    paths = sorted(set(p if p.is_absolute() else root / p for p in paths))
    records = [inspect_checkpoint(path, root, schema) for path in paths]
    rows = [r for r in records if r["record_kind"] == "checkpoint"]
    logs = [r for r in records if r["record_kind"] == "ladder_event_log"]
    ids = Counter(r["task_id"] for r in rows if isinstance(r["task_id"], str))
    for row in rows:
        if isinstance(row["task_id"], str) and ids[row["task_id"]] > 1:
            row["state_errors"].append("duplicate task_id in selected checkpoints")
            row["completion"] = "invalid"
    return {
        "report_version": 1,
        "observed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "root": str(root), "schema_source": str(SCHEMA_PATH), "schema_sha256": schema_digest,
        "verification_scope": "Local artifact integrity only; no business quality, approval, send or publication verification.",
        "summary": {
            "records_total": len(records), "event_logs": len(logs),
            "event_logs_invalid": sum(bool(r["event_errors"]) for r in logs),
            "total": len(rows), "schema_invalid": sum(bool(r["schema_errors"]) for r in rows),
            "state_invalid": sum(bool(r["state_errors"]) for r in rows),
            "artifact_errors": sum(a["status"] in ARTIFACT_ERRORS for r in rows for a in r["artifacts"]),
            "completion": dict(Counter(r["completion"] for r in rows)),
        },
        "tasks": rows,
        "event_logs": logs,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoints", nargs="*", type=Path, help="paths relative to --root; default: all state JSON")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--require-verified", action="store_true", help="also fail unless every selected task has verified local artifacts")
    args = parser.parse_args(argv)
    try:
        report = audit(args.root, args.checkpoints or None)
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        print(json.dumps({"report_version": 1, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    summary = report["summary"]
    failed = summary["schema_invalid"] or summary["state_invalid"] or summary["artifact_errors"] or summary["event_logs_invalid"]
    if args.require_verified:
        failed = failed or bool(report["event_logs"]) or any(r["completion"] != "local_artifacts_verified" for r in report["tasks"])
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
