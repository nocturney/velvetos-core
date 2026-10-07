#!/usr/bin/env python3
"""AI3D Engineering Contract and common artifact-report protocol.

This module is a staging utility. It validates and hashes evidence but does not
route work, choose production authorities, control machines, or start prints.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs" / "implementation" / "ai-3d-modeling-engineering-core"
CONTRACT_SCHEMA = BASE / "engineering-contract-v1.schema.json"
REPORT_SCHEMA = BASE / "artifact-report-v1.schema.json"
CAPABILITY_REGISTRY = BASE / "cad-capability-registry-v1.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def emit(payload: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return code


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_ref(
    path: Path,
    *,
    artifact_id: str,
    role: str,
    uri_or_path: str | None = None,
    media_type: str | None = None,
) -> dict[str, Any]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    guessed = mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
    return {
        "artifact_id": artifact_id,
        "role": role,
        "uri_or_path": uri_or_path or str(path),
        "sha256": sha256_file(resolved),
        "bytes": resolved.stat().st_size,
        "media_type": media_type or guessed,
    }


def jsonschema_validate(instance: dict[str, Any], schema_path: Path) -> list[str]:
    schema = load_json(schema_path)
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema-not-installed: structural validation skipped"]
    validator = jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )
    return [
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(instance), key=lambda err: list(err.path))
    ]


def axis_family(axis: str) -> str:
    return axis.lstrip("-")


def contract_semantic_errors(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    coordinate = contract.get("coordinate_system", {})
    up = str(coordinate.get("up_axis", ""))
    forward = str(coordinate.get("forward_axis", ""))
    if up and forward and axis_family(up) == axis_family(forward):
        errors.append("coordinate_system: up_axis and forward_axis are collinear")

    datums = contract.get("datums", [])
    dimensions = contract.get("dimensions", [])
    bodies = contract.get("expected_bodies", [])
    interfaces = contract.get("functional_interfaces", [])

    datum_ids = [item.get("datum_id") for item in datums]
    dimension_ids = [item.get("dimension_id") for item in dimensions]
    body_ids = [item.get("body_id") for item in bodies]
    for label, ids in (
        ("datum", datum_ids),
        ("dimension", dimension_ids),
        ("body", body_ids),
    ):
        clean = [item for item in ids if item]
        if len(clean) != len(set(clean)):
            errors.append(f"{label}: duplicate id")

    datum_set = set(datum_ids)
    dimension_set = set(dimension_ids)
    for item in interfaces:
        interface_id = item.get("interface_id", "<unknown>")
        missing_datums = set(item.get("datum_refs", [])) - datum_set
        missing_dimensions = set(item.get("dimension_refs", [])) - dimension_set
        if missing_datums:
            errors.append(
                f"interface {interface_id}: unknown datum refs {sorted(missing_datums)}"
            )
        if missing_dimensions:
            errors.append(
                f"interface {interface_id}: unknown dimension refs {sorted(missing_dimensions)}"
            )

    for item in dimensions:
        if item.get("critical") and item.get("source_type") in {"assumed", "unknown"}:
            errors.append(
                f"dimension {item.get('dimension_id')}: critical dimension lacks evidence source"
            )

    safety = contract.get("safety", {})
    for key in (
        "hidden_dimensions_may_be_invented",
        "printer_network_control",
        "machine_control",
    ):
        if safety.get(key) is not False:
            errors.append(f"safety.{key}: must be false")

    registry = load_json(CAPABILITY_REGISTRY)
    known_records = {row["record_id"] for row in registry.get("records", [])}
    missing_records = set(contract.get("capability_record_ids", [])) - known_records
    if missing_records:
        errors.append(f"capability_record_ids: unknown records {sorted(missing_records)}")

    return errors


def readiness(contract: dict[str, Any]) -> dict[str, bool]:
    unknowns = contract.get("unknowns", [])
    return {
        "geometry_build": not any(
            item.get("blocking")
            and item.get("resolution_required_before") == "geometry_build"
            for item in unknowns
        ),
        "manufacturing_release": not any(
            item.get("blocking")
            and item.get("resolution_required_before") in {
                "geometry_build",
                "manufacturing_release",
            }
            for item in unknowns
        ),
        "slice": not any(
            item.get("blocking")
            and item.get("resolution_required_before") in {
                "geometry_build",
                "manufacturing_release",
                "slice",
            }
            for item in unknowns
        ),
        "export": not any(
            item.get("blocking")
            and item.get("resolution_required_before") in {
                "geometry_build",
                "manufacturing_release",
                "export",
            }
            for item in unknowns
        ),
    }


def validate_contract(path: Path) -> tuple[dict[str, Any], bool]:
    contract = load_json(path)
    schema_errors = jsonschema_validate(contract, CONTRACT_SCHEMA)
    schema_errors = [
        item
        for item in schema_errors
        if not item.startswith("jsonschema-not-installed:")
    ]
    semantic_errors = contract_semantic_errors(contract)
    errors = schema_errors + semantic_errors
    payload = {
        "schema": "velvetos.ai3d.contract-validation.v1",
        "status": "PASS" if not errors else "BLOCKED",
        "contract": str(path),
        "contract_sha256": sha256_file(path),
        "readiness": readiness(contract) if not schema_errors else {},
        "errors": errors,
    }
    return payload, not errors


def resolve_artifact_path(report_path: Path, uri_or_path: str) -> Path | None:
    if "://" in uri_or_path and not uri_or_path.startswith("file://"):
        return None
    raw = uri_or_path[7:] if uri_or_path.startswith("file://") else uri_or_path
    path = Path(raw)
    if not path.is_absolute():
        path = (report_path.parent / path).resolve()
    return path


def report_semantic_errors(report_path: Path, report: dict[str, Any], verify_files: bool) -> list[str]:
    errors: list[str] = []
    if report.get("status") == "PASS" and not report.get("outputs"):
        errors.append("PASS report requires at least one output")

    engine = report.get("engine", {})
    if not engine.get("version"):
        errors.append("engine.version is required")
    if not engine.get("profile_refs"):
        errors.append("engine.profile_refs must record an exact profile or explicit n/a profile")

    if verify_files:
        for group in ("inputs", "outputs"):
            for artifact in report.get(group, []):
                path = resolve_artifact_path(report_path, artifact.get("uri_or_path", ""))
                if path is None:
                    continue
                if not path.is_file():
                    errors.append(f"{group}:{artifact.get('artifact_id')}: file missing: {path}")
                    continue
                actual_size = path.stat().st_size
                actual_hash = sha256_file(path)
                if actual_size != artifact.get("bytes"):
                    errors.append(
                        f"{group}:{artifact.get('artifact_id')}: byte count mismatch"
                    )
                if actual_hash != artifact.get("sha256"):
                    errors.append(
                        f"{group}:{artifact.get('artifact_id')}: sha256 mismatch"
                    )
    return errors


def validate_report(path: Path, verify_files: bool) -> tuple[dict[str, Any], bool]:
    report = load_json(path)
    schema_errors = jsonschema_validate(report, REPORT_SCHEMA)
    schema_errors = [
        item
        for item in schema_errors
        if not item.startswith("jsonschema-not-installed:")
    ]
    semantic_errors = report_semantic_errors(path, report, verify_files)
    errors = schema_errors + semantic_errors
    payload = {
        "schema": "velvetos.ai3d.report-validation.v1",
        "status": "PASS" if not errors else "BLOCKED",
        "report": str(path),
        "report_sha256": sha256_file(path),
        "verified_files": verify_files,
        "errors": errors,
    }
    return payload, not errors


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    commands = root.add_subparsers(dest="cmd", required=True)

    command = commands.add_parser("contract-validate")
    command.add_argument("--input", type=Path, required=True)

    command = commands.add_parser("report-validate")
    command.add_argument("--input", type=Path, required=True)
    command.add_argument("--verify-files", action="store_true")

    command = commands.add_parser("artifact-ref")
    command.add_argument("--path", type=Path, required=True)
    command.add_argument("--artifact-id", required=True)
    command.add_argument(
        "--role",
        required=True,
        choices=["input", "source", "normalized", "intermediate", "output", "preview", "receipt"],
    )
    command.add_argument("--uri-or-path")
    command.add_argument("--media-type")

    return root


def main() -> int:
    args = parser().parse_args()
    if args.cmd == "contract-validate":
        payload, ok = validate_contract(args.input)
        return emit(payload, 0 if ok else 2)
    if args.cmd == "report-validate":
        payload, ok = validate_report(args.input, args.verify_files)
        return emit(payload, 0 if ok else 2)
    if args.cmd == "artifact-ref":
        return emit(
            artifact_ref(
                args.path,
                artifact_id=args.artifact_id,
                role=args.role,
                uri_or_path=args.uri_or_path,
                media_type=args.media_type,
            )
        )
    raise AssertionError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())
