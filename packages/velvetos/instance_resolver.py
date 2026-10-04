#!/usr/bin/env python3
"""Generic VelvetOS instance/surface resolver.

The resolver is deliberately read-only and has no Velvet Factory default.
When called from a Core checkout, callers must provide an instance id
explicitly or via VELVETOS_INSTANCE_ID. When called from an instance checkout
whose root contains INSTANCE.json, that manifest is the current workspace
identity and an explicit/env id, if supplied, must match it.

Stage 8B adds the resolver foundation only. Legacy consumers are not cut over
by this module and existing compatibility paths remain in place until later
parity/consumer-scan gates.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

INSTANCE_ID_RE = re.compile(r"^[a-z0-9-]+$")
ENV_INSTANCE_ID = "VELVETOS_INSTANCE_ID"


class InstanceResolutionError(ValueError):
    """Fail-closed instance resolution error."""


@dataclass(frozen=True)
class ResolvedInstance:
    instance_id: str
    repository_root: Path
    instance_root: Path
    manifest_path: Path
    manifest: dict
    surfaces: dict[str, Path]
    mode: str

    def surface(self, name: str) -> Path:
        try:
            return self.surfaces[name]
        except KeyError as exc:
            raise InstanceResolutionError(
                f"instance {self.instance_id!r} has no declared surface {name!r}"
            ) from exc

    def to_public_dict(self) -> dict:
        """Metadata/path projection only; never emits surface file contents."""
        return {
            "instanceId": self.instance_id,
            "mode": self.mode,
            "manifest": _portable_path(self.repository_root, self.manifest_path),
            "instanceRoot": _portable_path(self.repository_root, self.instance_root),
            "surfaces": {
                key: _portable_path(self.repository_root, value)
                for key, value in sorted(self.surfaces.items())
            },
        }


def _portable_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _read_json_object(path: Path) -> dict:
    if not path.is_file():
        raise InstanceResolutionError(f"instance manifest not found: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstanceResolutionError(f"invalid JSON at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise InstanceResolutionError(f"instance manifest must be an object: {path}")
    return value


def _validated_instance_id(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if not INSTANCE_ID_RE.fullmatch(value):
        raise InstanceResolutionError(f"invalid instance id: {value!r}")
    return value


def _validate_relative_contract_path(rel: object, *, label: str) -> str:
    if not isinstance(rel, str) or not rel.strip():
        raise InstanceResolutionError(f"{label}: path must be a non-empty string")
    raw = Path(rel)
    if raw.is_absolute() or re.match(r"^[A-Za-z]:", rel):
        raise InstanceResolutionError(f"{label}: absolute paths are forbidden")
    normalized = Path(*[part for part in raw.parts if part not in ("", ".")])
    if ".." in normalized.parts:
        raise InstanceResolutionError(f"{label}: parent traversal is forbidden")
    return rel


def _validate_manifest_contract(manifest: dict) -> None:
    if manifest.get("product") != "VelvetOS" or manifest.get("role") != "instance":
        raise InstanceResolutionError("manifest must declare product=VelvetOS and role=instance")

    modern = "surfaces" in manifest or "surfaceContractVersion" in manifest
    if not modern:
        # Compatibility-only read path for pre-Stage-8 manifests.
        legacy_profile = manifest.get("profile")
        _validate_relative_contract_path(legacy_profile, label="legacy profile")
        return

    if manifest.get("surfaceContractVersion") != 1:
        raise InstanceResolutionError("modern instance manifest surfaceContractVersion must be 1")
    if not isinstance(manifest.get("displayName"), str) or not manifest["displayName"].strip():
        raise InstanceResolutionError("modern instance manifest requires non-empty displayName")

    core = manifest.get("core")
    if not isinstance(core, dict):
        raise InstanceResolutionError("modern instance manifest requires core object")
    if not isinstance(core.get("github"), str) or not core["github"].strip():
        raise InstanceResolutionError("modern instance manifest requires core.github")
    _validate_relative_contract_path(core.get("vendorPath"), label="core.vendorPath")
    _validate_relative_contract_path(core.get("attach"), label="core.attach")


def _safe_surface_path(instance_root: Path, rel: str, *, label: str) -> Path:
    if not isinstance(rel, str) or not rel.strip():
        raise InstanceResolutionError(f"{label}: surface path must be a non-empty string")
    raw = Path(rel)
    if raw.is_absolute() or re.match(r"^[A-Za-z]:", rel):
        raise InstanceResolutionError(f"{label}: absolute surface paths are forbidden")
    normalized = Path(*[part for part in raw.parts if part not in ("", ".")])
    if ".." in normalized.parts:
        raise InstanceResolutionError(f"{label}: parent traversal is forbidden")
    candidate = (instance_root / normalized).resolve()
    root_resolved = instance_root.resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise InstanceResolutionError(f"{label}: surface escapes instance root") from exc
    if not candidate.is_file():
        raise InstanceResolutionError(f"{label}: declared surface file missing: {candidate}")
    return candidate


def _manifest_surfaces(manifest: dict) -> dict[str, str]:
    raw = manifest.get("surfaces")
    if raw is None:
        # Compatibility alias for pre-Stage-8 manifests. Profile only; no hidden
        # business-specific defaults for other surfaces.
        legacy_profile = manifest.get("profile")
        if isinstance(legacy_profile, str) and legacy_profile:
            return {"profile": legacy_profile}
        raise InstanceResolutionError("instance manifest has no surfaces map")
    if not isinstance(raw, dict) or not raw:
        raise InstanceResolutionError("instance manifest surfaces must be a non-empty object")
    surfaces: dict[str, str] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not key:
            raise InstanceResolutionError("instance surface names must be non-empty strings")
        if not isinstance(value, str) or not value:
            raise InstanceResolutionError(f"surface {key!r} path must be a non-empty string")
        surfaces[key] = value
    legacy_profile = manifest.get("profile")
    if legacy_profile is not None and surfaces.get("profile") != legacy_profile:
        raise InstanceResolutionError("manifest profile alias must match surfaces.profile")
    return surfaces


def resolve_instance(
    repository_root: str | Path,
    *,
    instance_id: str | None = None,
    env: Mapping[str, str] | None = None,
) -> ResolvedInstance:
    """Resolve one instance without inventing a business default."""
    root = Path(repository_root).resolve()
    if not root.is_dir():
        raise InstanceResolutionError(f"repository root not found: {root}")

    env_map = os.environ if env is None else env
    explicit = _validated_instance_id(instance_id)
    from_env = _validated_instance_id(env_map.get(ENV_INSTANCE_ID))

    current_manifest = root / "INSTANCE.json"
    if current_manifest.is_file():
        manifest_path = current_manifest
        instance_root = root
        manifest = _read_json_object(manifest_path)
        manifest_id = _validated_instance_id(str(manifest.get("instanceId") or ""))
        if manifest_id is None:
            raise InstanceResolutionError("current instance manifest missing instanceId")
        requested = explicit or from_env
        if requested is not None and requested != manifest_id:
            raise InstanceResolutionError(
                f"requested instance {requested!r} does not match current workspace {manifest_id!r}"
            )
        resolved_id = manifest_id
        mode = "current-instance-workspace"
    else:
        requested = explicit or from_env
        if requested is None:
            raise InstanceResolutionError(
                f"Core checkout requires --instance-id or {ENV_INSTANCE_ID}; "
                "silent business defaults are forbidden"
            )
        resolved_id = requested
        instance_root = (root / "instances" / resolved_id).resolve()
        instances_root = (root / "instances").resolve()
        try:
            instance_root.relative_to(instances_root)
        except ValueError as exc:
            raise InstanceResolutionError("resolved instance path escapes instances root") from exc
        manifest_path = instance_root / "INSTANCE.json"
        manifest = _read_json_object(manifest_path)
        manifest_id = _validated_instance_id(str(manifest.get("instanceId") or ""))
        if manifest_id != resolved_id:
            raise InstanceResolutionError(
                f"manifest instanceId {manifest_id!r} does not match requested {resolved_id!r}"
            )
        mode = "core-explicit-instance"

    _validate_manifest_contract(manifest)
    raw_surfaces = _manifest_surfaces(manifest)
    resolved_surfaces = {
        name: _safe_surface_path(instance_root, rel, label=f"surface {name!r}")
        for name, rel in raw_surfaces.items()
    }
    if "profile" not in resolved_surfaces:
        raise InstanceResolutionError("instance manifest must declare profile surface")

    return ResolvedInstance(
        instance_id=resolved_id,
        repository_root=root,
        instance_root=instance_root,
        manifest_path=manifest_path.resolve(),
        manifest=manifest,
        surfaces=resolved_surfaces,
        mode=mode,
    )


def resolve_surface(
    repository_root: str | Path,
    surface: str,
    *,
    instance_id: str | None = None,
    env: Mapping[str, str] | None = None,
) -> Path:
    return resolve_instance(
        repository_root,
        instance_id=instance_id,
        env=env,
    ).surface(surface)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Core checkout root or instance workspace root")
    parser.add_argument("--instance-id", help=f"instance id; otherwise {ENV_INSTANCE_ID}")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("show", help="print resolved metadata/path map only")
    surface = sub.add_parser("surface", help="print one resolved surface path")
    surface.add_argument("name")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    try:
        resolved = resolve_instance(
            args.root,
            instance_id=args.instance_id,
        )
        if args.command == "show":
            print(json.dumps(resolved.to_public_dict(), ensure_ascii=False, indent=2))
        elif args.command == "surface":
            print(resolved.surface(args.name))
        return 0
    except InstanceResolutionError as exc:
        print(f"FAIL {exc}", file=os.sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
