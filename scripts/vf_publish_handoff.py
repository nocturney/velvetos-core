#!/usr/bin/env python3
"""Durable approved-export handoff into the VelvetOS Publish Bridge.

Problem this closes: Cursor can write approved delivery exports under
`/opt/cursor/artifacts/...`, but ChatGPT/HQ cannot read that ephemeral path later.
Missing bridge assets must trigger recovery — not an immediate
`blocked_publish_transport`.

Flow:
  approved Canva/export
    → register handoff manifest (git, no binaries on main)
    → Publish Bridge normalize + stage (publish-bridge branch only)
    → public fetch verify
    → Instagram publisher
    → live verification → published_verified

This is not a second approval system. PREFLIGHT / versionApproval remain SoT.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import vf_publish_bridge as bridge  # noqa: E402

HANDOFF_DIR = ROOT / "packages" / "vfigos" / "handoff"
PUBLICATIONS_DIR = ROOT / "packages" / "vfigos" / "data" / "publications"
STATES_PATH = ROOT / "packages" / "vfigos" / "PUBLICATION-STATES.json"

# Delivery sources that must never become the current approved package.
FORBIDDEN_SOURCE_PATTERNS = (
    re.compile(r"packages/vfcanva/jobs/", re.I),
    re.compile(r"packages/vfcovers/.*/out/", re.I),
    re.compile(r"/story-[0-9]+\.png$", re.I),
    re.compile(r"wsrv\.nl", re.I),
    re.compile(r"drive\.google\.com", re.I),
    re.compile(r"docs\.google\.com", re.I),
    re.compile(r"thumbnail", re.I),
    re.compile(r"canva\.com/.*/preview", re.I),
    re.compile(r"media-private\.canva\.com", re.I),
)

FORBIDDEN_PUBLIC_TEXT = (
    "whatsapp",
    "וואטסאפ",
    "wa.me",
    "050-",
    "97250",
    "₪",
    "shekel",
)

TRANSPORT_STATES = (
    "approved",
    "approved_export_local",
    "staged",
    "fetch_verified",
    "publish_requested",
    "published",
    "published_verified",
)

BLOCKERS = (
    "blocked_creative_preflight",
    "blocked_artifact_retrieval",
    "blocked_bridge_staging",
    "blocked_public_fetch",
    "blocked_instagram_publisher",
    "blocked_live_verification",
)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def package_fingerprint(correlation: str, source_refs: list[str], sha256_list: list[str]) -> str:
    material = "|".join([correlation, *source_refs, *sha256_list])
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def reject_source_path(path_or_url: str) -> None:
    text = path_or_url.strip()
    for pat in FORBIDDEN_SOURCE_PATTERNS:
        if pat.search(text):
            raise ValueError(f"rejected delivery source ({pat.pattern}): {text}")
    # Never treat anything on main as a binary staging root.
    resolved = Path(text).expanduser()
    try:
        resolved = resolved.resolve()
    except Exception:
        resolved = Path(text)
    rel = str(resolved)
    if "/publish-bridge/" not in rel and str(ROOT) in rel:
        # Repo-local historical assets are forbidden as current source.
        if any(seg in rel for seg in ("/jobs/", "/vfcovers/", "/out/story-")):
            raise ValueError(f"historical repo asset rejected as current source: {rel}")


def validate_public_cta_text(text: str, *, frame_role: str = "cta") -> None:
    lowered = text.lower()
    for needle in FORBIDDEN_PUBLIC_TEXT:
        if needle.lower() in lowered:
            raise ValueError(f"public {frame_role} contains forbidden token {needle!r}")
    if frame_role == "cta":
        # Instagram-message CTA must remain the public path.
        if "אינסטגרם" not in text and "instagram" not in lowered:
            raise ValueError("CTA frame must keep Instagram-message public CTA")


def publication_path(correlation: str) -> Path:
    PUBLICATIONS_DIR.mkdir(parents=True, exist_ok=True)
    return PUBLICATIONS_DIR / f"{correlation}.json"


def load_publication(correlation: str) -> dict[str, Any]:
    path = publication_path(correlation)
    if not path.is_file():
        return {
            "schemaVersion": 1,
            "correlation": correlation,
            "state": "approved",
            "frames": [],
            "receipts": [],
            "history": [],
        }
    return json.loads(path.read_text(encoding="utf-8"))


def save_publication(doc: dict[str, Any]) -> Path:
    path = publication_path(doc["correlation"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def set_state(doc: dict[str, Any], state: str, *, note: str = "") -> None:
    if state not in TRANSPORT_STATES and state not in BLOCKERS:
        raise ValueError(f"unknown publication state {state!r}")
    # Hard gate: published_verified requires receipt + live verification evidence.
    if state == "published_verified":
        if not doc.get("receipts"):
            raise ValueError("published_verified requires publish receipts")
        if not doc.get("liveVerification"):
            raise ValueError("published_verified requires liveVerification evidence")
    prev = doc.get("state")
    doc["state"] = state
    doc.setdefault("history", []).append(
        {"at": utc_now(), "from": prev, "to": state, "note": note}
    )


def handoff_manifest_path(correlation: str) -> Path:
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    return HANDOFF_DIR / f"{correlation}.json"


def register_local_export(
    *,
    correlation: str,
    file_path: Path,
    approval_ref: str,
    source_ref: str,
    frame_index: int,
    public_release_approved: bool,
    cta_text: str | None = None,
) -> dict[str, Any]:
    reject_source_path(str(file_path))
    reject_source_path(source_ref)
    if not public_release_approved:
        raise ValueError("unapproved assets fail closed — pass --public-release-approved")
    if not file_path.is_file():
        raise FileNotFoundError(file_path)
    if cta_text is not None:
        validate_public_cta_text(cta_text, frame_role="cta")

    digest = bridge.sha256_file(file_path)
    frame = {
        "frameIndex": frame_index,
        "localPath": str(file_path),
        "sourceSha256": digest,
        "sourceRef": source_ref,
        "approvalRef": approval_ref,
        "approvedForPublicRelease": True,
        "registeredAt": utc_now(),
    }
    man_path = handoff_manifest_path(correlation)
    if man_path.is_file():
        man = json.loads(man_path.read_text(encoding="utf-8"))
    else:
        man = {
            "schemaVersion": 1,
            "correlation": correlation,
            "approvalRef": approval_ref,
            "frames": [],
            "note": "Manifest only on main — binaries stage exclusively on publish-bridge",
        }
    # Replace same frame index if re-registered.
    man["frames"] = [f for f in man["frames"] if f.get("frameIndex") != frame_index]
    man["frames"].append(frame)
    man["frames"].sort(key=lambda f: int(f["frameIndex"]))
    man["updatedAt"] = utc_now()
    man_path.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    doc = load_publication(correlation)
    doc["approvalRef"] = approval_ref
    set_state(doc, "approved_export_local", note=f"registered frame {frame_index}")
    save_publication(doc)
    return {"ok": True, "manifest": str(man_path.relative_to(ROOT)), "frame": frame, "state": doc["state"]}


def recover_and_stage_frame(
    *,
    correlation: str,
    file_path: Path,
    approval_ref: str,
    source_ref: str,
    frame_index: int,
    public_release_approved: bool,
    do_stage: bool,
) -> dict[str, Any]:
    """Recovery path: local approved export exists → stage → fetch verify.

    Never collapses every failure into blocked_publish_transport.
    """
    attempts: list[dict[str, Any]] = []
    doc = load_publication(correlation)

    try:
        reject_source_path(str(file_path))
        reject_source_path(source_ref)
    except ValueError as exc:
        set_state(doc, "blocked_artifact_retrieval", note=str(exc))
        save_publication(doc)
        return {"ok": False, "blocker": "blocked_artifact_retrieval", "error": str(exc)}

    if not public_release_approved:
        set_state(doc, "blocked_creative_preflight", note="missing public-release approval")
        save_publication(doc)
        return {"ok": False, "blocker": "blocked_creative_preflight", "error": "unapproved"}

    if not file_path.is_file():
        # Attempt Canva re-export is an orchestration step; here we only record the blocker layer.
        set_state(doc, "blocked_artifact_retrieval", note=f"missing local export {file_path}")
        save_publication(doc)
        return {
            "ok": False,
            "blocker": "blocked_artifact_retrieval",
            "error": f"missing {file_path}",
            "recoveryHint": "re-export from sourceRef via Canva MCP, then re-run handoff",
        }

    register_local_export(
        correlation=correlation,
        file_path=file_path,
        approval_ref=approval_ref,
        source_ref=source_ref,
        frame_index=frame_index,
        public_release_approved=True,
    )
    attempts.append({"step": "approved_export_local", "ok": True})

    cfg = bridge.load_config()
    with tempfile.TemporaryDirectory(prefix="vf-handoff-") as tmp_name:
        tmp = Path(tmp_name)
        try:
            normalized, content_type, details = bridge.normalize(file_path, cfg, tmp)
        except Exception as exc:
            set_state(doc, "blocked_bridge_staging", note=str(exc))
            save_publication(doc)
            return {"ok": False, "blocker": "blocked_bridge_staging", "error": str(exc), "attempts": attempts}

        metadata = bridge.build_metadata(
            normalized,
            content_type,
            details,
            cfg,
            correlation,
            approval_ref,
            source_ref,
        )
        # Idempotency: if this exact sha20 object is already the recorded staged asset, skip restage.
        existing = next(
            (f for f in doc.get("frames", []) if f.get("frameIndex") == frame_index),
            None,
        )
        if (
            existing
            and existing.get("sha256") == metadata["sha256"]
            and existing.get("publicUrl")
            and existing.get("fetchVerified")
        ):
            attempts.append({"step": "idempotent_skip_stage", "ok": True, "sha256": metadata["sha256"]})
            return {
                "ok": True,
                "idempotent": True,
                "frame": existing,
                "state": doc.get("state"),
                "attempts": attempts,
            }

        result_frame: dict[str, Any] = {
            "frameIndex": frame_index,
            "sourceRef": source_ref,
            "approvalRef": approval_ref,
            "sha256": metadata["sha256"],
            "contentType": content_type,
            **details,
            "path": metadata["path"],
            "publicUrl": metadata["publicUrl"],
        }

        if not do_stage:
            set_state(doc, "approved_export_local", note="prepared only")
            doc.setdefault("frames", [])
            doc["frames"] = [f for f in doc["frames"] if f.get("frameIndex") != frame_index]
            doc["frames"].append(result_frame)
            doc["frames"].sort(key=lambda f: int(f["frameIndex"]))
            save_publication(doc)
            return {"ok": True, "mode": "prepare", "frame": result_frame, "attempts": attempts}

        try:
            public_url, commit = bridge.stage_to_github(normalized, metadata, cfg)
            result_frame["publicUrl"] = public_url
            result_frame["bridgeCommit"] = commit
            set_state(doc, "staged", note=f"frame {frame_index} staged")
            attempts.append({"step": "bridge_staging", "ok": True, "commit": commit})
        except Exception as exc:
            set_state(doc, "blocked_bridge_staging", note=str(exc))
            save_publication(doc)
            return {"ok": False, "blocker": "blocked_bridge_staging", "error": str(exc), "attempts": attempts}

        try:
            fetch_verify = bridge.verify_public_url(
                public_url,
                metadata["sha256"],
                content_type,
                int(details["sizeBytes"]),
            )
            result_frame["fetchVerified"] = fetch_verify
            set_state(doc, "fetch_verified", note=f"frame {frame_index} fetch ok")
            attempts.append({"step": "public_fetch", "ok": True})
        except Exception as exc:
            set_state(doc, "blocked_public_fetch", note=str(exc))
            save_publication(doc)
            return {"ok": False, "blocker": "blocked_public_fetch", "error": str(exc), "attempts": attempts}

        doc.setdefault("frames", [])
        doc["frames"] = [f for f in doc["frames"] if f.get("frameIndex") != frame_index]
        doc["frames"].append(result_frame)
        doc["frames"].sort(key=lambda f: int(f["frameIndex"]))
        fps = package_fingerprint(
            correlation,
            [f.get("sourceRef", "") for f in doc["frames"]],
            [f.get("sha256", "") for f in doc["frames"]],
        )
        doc["packageFingerprint"] = fps
        save_publication(doc)
        return {"ok": True, "mode": "stage", "frame": result_frame, "state": doc["state"], "attempts": attempts}


def record_publish_receipt(correlation: str, receipt: dict[str, Any]) -> dict[str, Any]:
    doc = load_publication(correlation)
    # Idempotency: same media_id / package fingerprint must not duplicate.
    media_id = str(receipt.get("media_id") or "")
    existing_ids = {str(r.get("media_id")) for r in doc.get("receipts", [])}
    if media_id and media_id in existing_ids:
        return {"ok": True, "idempotent": True, "state": doc.get("state"), "media_id": media_id}
    doc.setdefault("receipts", []).append({**receipt, "recordedAt": utc_now()})
    set_state(doc, "published" if receipt.get("ok") else "blocked_instagram_publisher", note="publish receipt")
    if not receipt.get("ok"):
        save_publication(doc)
        return {"ok": False, "blocker": "blocked_instagram_publisher", "state": doc["state"]}
    set_state(doc, "publish_requested", note="publish tool accepted")
    # publish_* success alone is not live — stay pending until liveVerification.
    doc["state"] = "published"
    doc.setdefault("history", []).append(
        {"at": utc_now(), "from": "publish_requested", "to": "published", "note": "receipt captured; await live verify"}
    )
    save_publication(doc)
    return {"ok": True, "state": doc["state"], "media_id": media_id}


def record_live_verification(correlation: str, evidence: dict[str, Any]) -> dict[str, Any]:
    doc = load_publication(correlation)
    if not doc.get("receipts"):
        set_state(doc, "blocked_live_verification", note="no publish receipts")
        save_publication(doc)
        return {"ok": False, "blocker": "blocked_live_verification", "error": "missing receipts"}
    if not evidence.get("media_id") or not evidence.get("verified"):
        set_state(doc, "blocked_live_verification", note="incomplete evidence")
        save_publication(doc)
        return {"ok": False, "blocker": "blocked_live_verification", "error": "incomplete evidence"}
    doc.setdefault("liveVerification", []).append({**evidence, "verifiedAt": utc_now()})
    # Only mark published_verified when every receipt media_id has live evidence.
    receipt_ids = {str(r.get("media_id")) for r in doc["receipts"] if r.get("media_id")}
    verified_ids = {str(v.get("media_id")) for v in doc["liveVerification"] if v.get("verified")}
    if receipt_ids and receipt_ids <= verified_ids:
        set_state(doc, "published_verified", note="all receipts live-verified")
    else:
        set_state(doc, "published", note="partial live verification")
    save_publication(doc)
    return {"ok": True, "state": doc["state"], "verifiedIds": sorted(verified_ids)}


def cmd_register(args: argparse.Namespace) -> int:
    out = register_local_export(
        correlation=args.correlation,
        file_path=Path(args.file).expanduser().resolve(),
        approval_ref=args.approval_ref,
        source_ref=args.source_ref,
        frame_index=int(args.frame_index),
        public_release_approved=bool(args.public_release_approved),
        cta_text=args.cta_text,
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_recover(args: argparse.Namespace) -> int:
    out = recover_and_stage_frame(
        correlation=args.correlation,
        file_path=Path(args.file).expanduser().resolve(),
        approval_ref=args.approval_ref,
        source_ref=args.source_ref,
        frame_index=int(args.frame_index),
        public_release_approved=bool(args.public_release_approved),
        do_stage=bool(args.stage),
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get("ok") else 2


def cmd_receipt(args: argparse.Namespace) -> int:
    receipt = json.loads(Path(args.receipt_json).read_text(encoding="utf-8"))
    out = record_publish_receipt(args.correlation, receipt)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get("ok") else 2


def cmd_verify(args: argparse.Namespace) -> int:
    evidence = json.loads(Path(args.evidence_json).read_text(encoding="utf-8"))
    out = record_live_verification(args.correlation, evidence)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get("ok") else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("register", help="register an approved local export into the handoff manifest")
    p.add_argument("--file", required=True)
    p.add_argument("--correlation", required=True)
    p.add_argument("--approval-ref", required=True)
    p.add_argument("--source-ref", required=True)
    p.add_argument("--frame-index", required=True, type=int)
    p.add_argument("--public-release-approved", action="store_true")
    p.add_argument("--cta-text", default=None)

    p = sub.add_parser("recover", help="recover: local approved export → bridge stage → fetch verify")
    p.add_argument("--file", required=True)
    p.add_argument("--correlation", required=True)
    p.add_argument("--approval-ref", required=True)
    p.add_argument("--source-ref", required=True)
    p.add_argument("--frame-index", required=True, type=int)
    p.add_argument("--public-release-approved", action="store_true")
    p.add_argument("--stage", action="store_true", help="actually stage to publish-bridge (needs GH_TOKEN)")

    p = sub.add_parser("receipt", help="record a publish_* receipt")
    p.add_argument("--correlation", required=True)
    p.add_argument("--receipt-json", required=True)

    p = sub.add_parser("verify-live", help="record live get_media/list_media verification")
    p.add_argument("--correlation", required=True)
    p.add_argument("--evidence-json", required=True)

    args = parser.parse_args()
    try:
        if args.command == "register":
            return cmd_register(args)
        if args.command == "recover":
            return cmd_recover(args)
        if args.command == "receipt":
            return cmd_receipt(args)
        if args.command == "verify-live":
            return cmd_verify(args)
        raise SystemExit(f"unknown command {args.command}")
    except Exception as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
