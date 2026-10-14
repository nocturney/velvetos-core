#!/usr/bin/env python3
"""Safe motion choice -> existing HyperFrames rough-render request.

No network, install, renderer, media catalog, approval database, or publisher.
The full creative/rights/copy/final/publish gates remain outside this adapter.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "packages/vfom/MOTION-LIBRARY.json"
SCHEMA = ROOT / "packages/vfom/hyperframes/MOTION-STORY-VARIABLES.schema.json"
MEDIA_CATALOG = "packages/vfmedia/catalog.json"
JOB_ID = re.compile(r"^[A-Za-z0-9._-]+$")
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".ogg"}
TRUTH_LEVELS = {"verified_real", "derived_real"}


class MotionInputError(ValueError):
    pass


def load_json(path: Path) -> dict:
    try:
        obj = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MotionInputError("cannot read JSON at " + str(path) + ": " + str(exc)) from exc
    if not isinstance(obj, dict):
        raise MotionInputError("JSON root must be an object: " + str(path))
    return obj


def contained(root: Path, value: str, *, must_exist: bool = False) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise MotionInputError("required path is empty")
    if "://" in value or value.startswith("//") or value.startswith("\\\\"):
        raise MotionInputError("remote/UNC media paths are not accepted; stage a local verified asset")
    candidate = Path(value)
    if candidate.is_absolute():
        raise MotionInputError("pass project-relative paths, not absolute machine paths")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise MotionInputError("path escapes projectDir: " + value) from exc
    if must_exist and not resolved.is_file():
        raise MotionInputError("required staged file is missing: " + value)
    return resolved


def check_local_media(root: Path, name: str, value: str, extensions: set[str]) -> None:
    candidate = contained(root, value, must_exist=True)
    if candidate.suffix.lower() not in extensions:
        raise MotionInputError(name + " has unsupported media extension: " + candidate.suffix)
    if candidate.stat().st_size <= 0:
        raise MotionInputError(name + " is empty")


def truth_level(row: dict) -> str:
    truth = row.get("truth")
    if isinstance(truth, str):
        return truth
    if isinstance(truth, dict):
        return str(truth.get("level") or truth.get("classification") or "")
    return ""


def require_real_media_ref(media: dict, ref: str) -> None:
    items = media.get("items") or []
    if not isinstance(items, list):
        raise MotionInputError("Media Vault catalog items are invalid")
    matching = [row for row in items if isinstance(row, dict) and row.get("id") == ref]
    if len(matching) != 1:
        raise MotionInputError("asset ref absent/ambiguous in canonical Media Vault: " + ref)
    if truth_level(matching[0]) not in TRUTH_LEVELS:
        raise MotionInputError("Media Vault asset lacks verified-real/derived-real truth: " + ref)


def validate_variables(root: Path, variables: dict, catalog: dict, schema: dict) -> dict:
    required = set(schema.get("required") or [])
    if set(variables) != required or not required:
        raise MotionInputError("motion variables keys must exactly match the declared schema")
    if any(not isinstance(value, str) for value in variables.values()):
        raise MotionInputError("motion variables must be strings (no unreviewed object/HTML payloads)")

    style = variables["motionStyle"]
    patterns = {row["id"]: row for row in catalog["patterns"]}
    if style not in patterns:
        raise MotionInputError("motionStyle is not allowlisted: " + style)
    if variables["variablesStatus"] != "ready" or variables["neededInputs"]:
        raise MotionInputError("motion job is needs_input; cannot route to render")
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", variables["accentHex"]):
        raise MotionInputError("invalid brand accent hex")
    if variables["accentId"] not in schema["properties"]["accentId"]["enum"]:
        raise MotionInputError("unknown brand accentId")

    for key in patterns[style]["requiredVariables"]:
        if not variables.get(key, "").strip():
            raise MotionInputError(style + " requires " + key)
    check_local_media(root, "heroImage", variables["heroImage"], IMAGE_EXTS)
    check_local_media(root, "audioFile", variables["audioFile"], AUDIO_EXTS)

    media_catalog = load_json(root / MEDIA_CATALOG)
    require_real_media_ref(media_catalog, variables["sourceAssetRef"])

    if style == "before_after":
        if variables["comparisonAssetRef"] == variables["sourceAssetRef"]:
            raise MotionInputError("comparison must use a distinct verified media source")
        if variables["comparisonImage"] == variables["heroImage"]:
            raise MotionInputError("comparison needs separate media bytes")
        check_local_media(root, "comparisonImage", variables["comparisonImage"], IMAGE_EXTS)
        require_real_media_ref(media_catalog, variables["comparisonAssetRef"])
        if not variables["comparisonEvidenceRef"].strip():
            raise MotionInputError("before_after needs external alignment/comparison evidence")
    if style == "shorts_hook":
        for key in ("beat1", "beat2", "beat3"):
            value = variables[key].strip()
            if not value or len(value) > 18:
                raise MotionInputError(key + " must be approved short copy (1..18 chars)")

    return patterns[style]


def prepare(variables_file: Path, project_dir: Path, job_id: str, output: str) -> dict:
    if not JOB_ID.fullmatch(job_id):
        raise MotionInputError("invalid job ID")
    project_dir = project_dir.expanduser().resolve()
    if not project_dir.is_dir():
        raise MotionInputError("projectDir does not exist")
    try:
        variables_rel = variables_file.resolve().relative_to(project_dir).as_posix()
    except ValueError as exc:
        raise MotionInputError("variables file must stay under projectDir") from exc
    output_path = contained(project_dir, output)
    if output_path.suffix.lower() != ".mp4":
        raise MotionInputError("output must be a project-local .mp4")
    if output_path == variables_file.resolve():
        raise MotionInputError("output cannot overwrite variables")

    catalog = load_json(CATALOG)
    schema = load_json(SCHEMA)
    if catalog.get("masterComposer") != "hyperframes" or catalog.get("noSecondRuntime") is not True:
        raise MotionInputError("motion catalog authority invalid")
    variables = load_json(variables_file)
    selected = validate_variables(project_dir, variables, catalog, schema)

    composition = str(catalog["template"])
    contained(project_dir, composition, must_exist=True)
    request = {
        "jobId": job_id,
        "backend": "hyperframes",
        "projectDir": str(project_dir),
        "composition": composition,
        "stage": "rough",
        "target": "review",
        "format": "mp4",
        "resolution": "portrait",
        "fps": 30,
        "quality": "draft",
        "output": output_path.relative_to(project_dir).as_posix(),
        "variablesFile": variables_rel,
        "audioRequired": True,
        "strictAll": False,
    }
    return {
        "schema": "velvetos.motion-plan.v1",
        "state": "rough_candidate_only",
        "jobId": job_id,
        "motionStyle": selected["id"],
        "sourceCommit": catalog["source"]["commit"],
        "sourceCards": selected["sourceCards"],
        "presets": selected["gsapPresets"],
        "renderRequest": request,
        "nextStep": "python3 scripts/vf_hyperframes.py plan <render-request.json>",
        "afterRough": [
            "verify Media Vault, Product Truth, comparison alignment when applicable",
            "run vfcopy final-copy lint and creative/reference/RTL/mobile/audio QA",
            "run canonical HyperFrames final render and independent publish preflight",
        ],
        "publicationAuthorized": False,
        "renderReceiptIsPublishReceipt": False,
    }


def selftest() -> None:
    with tempfile.TemporaryDirectory(prefix="vf-motion-selftest-") as tmp:
        root = Path(tmp)
        (root / "packages/vfmedia").mkdir(parents=True)
        (root / "packages/vfom/hyperframes/templates").mkdir(parents=True)
        (root / "packages/vfom/hyperframes/templates/motion-story-reel.html").write_text(
            "<html>selftest only</html>", encoding="utf-8"
        )
        (root / "input").mkdir()
        (root / "input/hero.png").write_bytes(b"structural-test-only")
        (root / "input/after.png").write_bytes(b"structural-test-only-after")
        (root / "input/audio.wav").write_bytes(b"structural-test-only")
        (root / MEDIA_CATALOG).write_text(json.dumps({"items": [
            {"id": "media-test-before", "truth": "verified_real"},
            {"id": "media-test-after", "truth": {"level": "derived_real"}},
            {"id": "media-test-unverified", "truth": "unverified"},
        ]}), encoding="utf-8")
        base = {key: "" for key in load_json(SCHEMA)["required"]}
        base.update({
            "motionStyle": "product_reveal", "variablesStatus": "ready", "neededInputs": "",
            "headline": "אותו מוצר בדיוק", "subhead": "",
            "heroImage": "input/hero.png", "sourceAssetRef": "media-test-before",
            "audioFile": "input/audio.wav", "accentId": "copper",
            "accentHex": "#a86838", "accentSource": "brand-tokens",
        })
        vars_path = root / "input/variables.json"

        def run_variant(v: dict, accepted: bool) -> None:
            vars_path.write_text(json.dumps(v, ensure_ascii=False), encoding="utf-8")
            try:
                plan = prepare(vars_path, root, "VF-TEST-MOTION", "output/rough.mp4")
            except MotionInputError:
                if accepted:
                    raise
            else:
                if not accepted:
                    raise AssertionError("unsafe motion variables were accepted")
                assert plan["publicationAuthorized"] is False
                assert plan["renderRequest"]["backend"] == "hyperframes"
                assert plan["renderRequest"]["stage"] == "rough"
                assert plan["renderRequest"]["audioRequired"] is True

        run_variant(dict(base), True)
        comparison = dict(base, motionStyle="before_after", comparisonImage="input/after.png",
                          comparisonAssetRef="media-test-after", comparisonEvidenceRef="review/compare.png")
        run_variant(comparison, True)
        run_variant(dict(comparison, comparisonEvidenceRef=""), False)
        run_variant(dict(comparison, comparisonAssetRef="media-test-before"), False)
        run_variant(dict(base, motionStyle="shorts_hook", beat1="צילום", beat2="הדפסה", beat3="מוצר"), True)
        run_variant(dict(base, motionStyle="shorts_hook"), False)
        run_variant(dict(base, motionStyle="unknown"), False)
        run_variant(dict(base, variablesStatus="needs_input", neededInputs="media missing"), False)
        run_variant(dict(base, heroImage="../../other.png"), False)
        run_variant(dict(base, heroImage="https://example.com/product.png"), False)
        run_variant(dict(base, sourceAssetRef="media-test-unverified"), False)
        run_variant(dict(base, audioFile="input/no-audio.wav"), False)
        run_variant(dict(base, extra="untracked"), False)
        print("OK motion-plan source-pinned candidates=3 truth+path+copy+audio gates fail-closed publish=false")


def main() -> int:
    parser = argparse.ArgumentParser(description="Select source-locked motion inside HyperFrames")
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="command")
    plan = sub.add_parser("plan", help="produce existing HyperFrames rough request (no render)")
    plan.add_argument("variables_file", type=Path)
    plan.add_argument("--project-dir", type=Path, required=True)
    plan.add_argument("--job-id", required=True)
    plan.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        if args.self_test:
            selftest()
        elif args.command == "plan":
            result = prepare(args.variables_file, args.project_dir, args.job_id, args.output)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            parser.print_help()
            return 2
    except (MotionInputError, AssertionError) as exc:
        print("FAIL motion-plan: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
