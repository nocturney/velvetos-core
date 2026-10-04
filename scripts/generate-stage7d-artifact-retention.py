#!/usr/bin/env python3
"""Generate Reform v2 Stage 7D artifact-retention acceptance evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "packages" / "velvetos" / "policy"
RETENTION = POLICY / "artifact-retention.json"
RETENTION_SCHEMA = POLICY / "schema" / "artifact-retention.schema.json"
ARCHIVE_RECEIPT = POLICY / "reports" / "stage7d-morning-green-asset-archive.json"
POLICY_REGISTRY = POLICY / "policy-registry.json"
STATE_MODEL = POLICY / "state-evidence-model.json"
PREPARER = ROOT / "packages" / "vfbriefux" / "prepare_morning_green.py"
GMAIL_REQUEST = ROOT / "packages" / "vfops" / "out" / "gmail-send-request.json"
OUT_DIR = ROOT / "packages" / "vfops" / "out"
CANONICAL_ASSETS = ROOT / "packages" / "vfbriefux" / "assets" / "morning-green"
OUT = POLICY / "reports" / "stage7d-artifact-retention.json"

CURRENT_TRANSPORT = {
    "html": "packages/vfops/out/morning-green-current.html",
    "visible_text": "packages/vfops/out/morning-green-current.txt",
    "json": "packages/vfops/out/morning-green-current.json",
    "images": "packages/vfops/out/morning-green-assets-current/",
}
REMOVED_GLOBS = (
    "packages/vfops/out/morning-green-assets-20*/**",
    "packages/vfops/out/morning-green-assets-approved-mockup-*/**",
)
ACTIVE_CONSUMERS = (
    ROOT / "packages" / "vfbriefux" / "prepare_morning_green.py",
    ROOT / ".github" / "workflows" / "gmail-brief-send.yml",
    ROOT / "packages" / "vfops" / "gmail_apps_script_request.py",
    ROOT / "packages" / "vfops" / "gmail_brief_request.py",
    ROOT / "packages" / "vfops" / "gmail_brief_send.py",
)
DATED_ACTIVE_PATTERN = re.compile(
    r"morning-green-assets-(?:20\d{2}|approved-mockup)|"
    r"morning-green-20\d{2}-\d{2}-\d{2}\.(?:html|json|txt)"
)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_show(sha: str, rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{sha}:{rel}"], cwd=ROOT)


def base_tree_metrics(sha: str) -> dict[str, int]:
    text = subprocess.check_output(
        ["git", "ls-tree", "-r", "-l", sha], cwd=ROOT, text=True, encoding="utf-8"
    )
    files = 0
    total = 0
    for line in text.splitlines():
        if "\t" not in line:
            continue
        left, _path = line.split("\t", 1)
        parts = left.split()
        if len(parts) < 4 or parts[1] != "blob":
            continue
        try:
            size = int(parts[3])
        except ValueError:
            continue
        files += 1
        total += size
    return {"files": files, "bytes": total}


def projected_worktree_metrics() -> dict[str, int]:
    tracked = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=ROOT
    ).decode("utf-8", errors="surrogateescape").split("\0")
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=ROOT
    ).decode("utf-8", errors="surrogateescape").split("\0")
    rels = {item for item in tracked + untracked if item}
    # Exclude this generated acceptance receipt from its own footprint metric so
    # regeneration is byte-stable after the receipt has been committed.
    rels.discard(OUT.relative_to(ROOT).as_posix())
    files = 0
    total = 0
    for rel in rels:
        path = ROOT / rel
        if path.is_file():
            files += 1
            total += path.stat().st_size
    return {"files": files, "bytes": total}


def active_consumer_scan() -> dict[str, Any]:
    refs: list[dict[str, Any]] = []
    for path in ACTIVE_CONSUMERS:
        if not path.is_file():
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if DATED_ACTIVE_PATTERN.search(line):
                refs.append(
                    {
                        "path": path.relative_to(ROOT).as_posix(),
                        "line": line_no,
                        "text": line.strip()[:240],
                    }
                )
    return {
        "scanned": [path.relative_to(ROOT).as_posix() for path in ACTIVE_CONSUMERS if path.is_file()],
        "dated_transport_refs": refs,
        "pass": not refs,
    }


def current_asset_parity() -> dict[str, Any]:
    current = OUT_DIR / "morning-green-assets-current"
    rows: list[dict[str, Any]] = []
    for source in sorted(CANONICAL_ASSETS.glob("*")):
        if not source.is_file():
            continue
        target = current / source.name
        rows.append(
            {
                "name": source.name,
                "canonical_sha256": sha256(source),
                "current_sha256": sha256(target) if target.is_file() else None,
                "match": target.is_file() and sha256(source) == sha256(target),
            }
        )
    return {
        "files": len(rows),
        "all_match": bool(rows) and all(row["match"] for row in rows),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared-against", required=True)
    parser.add_argument("--captured-at", required=True)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    require(re.fullmatch(r"[0-9a-f]{40}", args.prepared_against) is not None,
            "--prepared-against must be a full lowercase Git SHA")

    retention = load(RETENTION)
    archive = load(ARCHIVE_RECEIPT)
    request = load(GMAIL_REQUEST)
    state_model = load(STATE_MODEL)

    stage7d = retention.get("stage7d") or {}
    require(stage7d.get("status") == "ACTIVE_STAGE7D", "Stage 7D retention registry is not active")
    require(stage7d.get("migration_mode") == "COPY_FIRST", "Stage 7D must remain copy-first")
    require(stage7d.get("source_commit") == args.prepared_against, "Stage 7D source commit drift")
    require(stage7d.get("consumer_scan_required_before_tree_removal") is True,
            "consumer scan is required before tree removal")
    require(stage7d.get("external_irreversible_delete_authority_added") is False,
            "Stage 7D may not add external irreversible delete authority")

    entries = retention.get("entries") or []
    require(len(entries) == 9, "Stage 7D must retain the nine Stage 7A artifact classes")
    require(all("CLASSIFY_IN_STAGE_7" not in str(row.get("retention_class")) for row in entries),
            "Stage 7D left an unclassified retention class")
    deletion_rows = [row for row in entries if row.get("deletion_authorized") is True]
    require(len(deletion_rows) == 1 and deletion_rows[0].get("artifact_class_id") == "office-generated-output",
            "only office-generated-output may have scoped tree-removal authorization")
    office = deletion_rows[0]
    require(tuple(office.get("deletion_scope") or []) == REMOVED_GLOBS,
            "Morning Green deletion scope drift")
    require(office.get("copy_first_receipt") == ARCHIVE_RECEIPT.relative_to(ROOT).as_posix(),
            "copy-first receipt binding drift")
    require((office.get("current_transport") or {}) == CURRENT_TRANSPORT,
            "rolling current transport mapping drift")

    require(archive.get("schema") == "velvetos.stage7d-local-artifact-archive.v1",
            "archive receipt schema drift")
    require(archive.get("source_commit") == args.prepared_against, "archive receipt source commit drift")
    require(archive.get("directory_count") == 18, "archive receipt directory count drift")
    require(archive.get("file_count") == 86, "archive receipt file count drift")
    require(archive.get("bytes") == 5953075, "archive receipt byte count drift")
    archive_entries = archive.get("entries") or []
    require(len(archive_entries) == 86, "archive receipt entry count drift")
    require(all(
        isinstance(row, dict)
        and re.fullmatch(r"[0-9a-f]{64}", str(row.get("sha256") or ""))
        and int(row.get("bytes") or 0) > 0
        for row in archive_entries
    ), "archive receipt entry/hash drift")

    historical_dirs = sorted(
        path.name for path in OUT_DIR.iterdir()
        if path.is_dir()
        and (
            re.fullmatch(r"morning-green-assets-20\d{2}-\d{2}-\d{2}", path.name)
            or path.name.startswith("morning-green-assets-approved-mockup-")
        )
    )
    require(not historical_dirs, f"historical Morning Green image bundles remain in tree: {historical_dirs}")

    for rel in CURRENT_TRANSPORT.values():
        path = ROOT / rel.rstrip("/")
        require(path.exists(), f"current transport path missing: {rel}")
    require(request.get("enabled") is False, "repository baseline Gmail request must remain disabled")
    require(request.get("html") == CURRENT_TRANSPORT["html"], "current Gmail html path drift")
    require(request.get("visibleText") == CURRENT_TRANSPORT["visible_text"], "current Gmail visible-text path drift")
    require(request.get("images") == CURRENT_TRANSPORT["images"].rstrip("/"), "current Gmail image path drift")
    require(request.get("retentionMode") == "rolling-current-transport", "current Gmail retention mode drift")

    preparer = PREPARER.read_text(encoding="utf-8")
    require("morning-green-current.html" in preparer
            and "morning-green-assets-current" in preparer
            and "rolling-current-transport" in preparer,
            "Morning Green producer is not rolling-current")
    require('f"morning-green-assets-{iso}"' not in preparer
            and 'f"morning-green-{iso}.html"' not in preparer,
            "Morning Green producer regained dated transport accumulation")

    scan = active_consumer_scan()
    require(scan["pass"], "active consumer still references removed dated Morning Green transport")

    parity = current_asset_parity()
    require(parity["all_match"], "current Morning Green asset bundle differs from canonical source assets")

    current_asset_bytes = sum((OUT_DIR / "morning-green-assets-current" / row["name"]).stat().st_size
                              for row in parity["rows"])
    removed_copy_bytes = int(archive["bytes"])
    image_noise_reduction = removed_copy_bytes - current_asset_bytes
    require(image_noise_reduction > 5_000_000, "Stage 7D did not materially reduce Morning Green image noise")

    work_ledger = state_model.get("work_ledger") or {}
    require(work_ledger.get("destination_stage") == "7D"
            and work_ledger.get("references_only") is True
            and work_ledger.get("policy_authority") is False
            and work_ledger.get("external_effect_authority") is False,
            "Stage 7A Work Ledger handoff drift")
    work_ledger_decision = {
        "decision": "NO_NEW_WORK_LEDGER_STORE",
        "reason": "office/control/HANDOFF.json already provides refs-only continuation; another ledger would duplicate state/index authority",
        "canonical_continuation_view": "office/control/HANDOFF.json",
        "new_store_created": False,
        "policy_authority": False,
        "external_effect_authority": False,
    }
    require((ROOT / work_ledger_decision["canonical_continuation_view"]).is_file(),
            "canonical continuation view missing")

    current_policy = POLICY_REGISTRY.read_bytes()
    baseline_policy = git_show(args.prepared_against, "packages/velvetos/policy/policy-registry.json")
    require(current_policy == baseline_policy, "Stage 7D changed external-effect policy registry")

    base_metrics = base_tree_metrics(args.prepared_against)
    projected_metrics = projected_worktree_metrics()
    criteria = {
        "all_nine_artifact_classes_have_concrete_retention": all(
            "CLASSIFY_IN_STAGE_7" not in str(row.get("retention_class")) for row in entries
        ),
        "morning_green_large_history_was_copy_first_archived": archive.get("file_count") == 86,
        "archive_receipt_has_per_file_sha256": len(archive_entries) == 86,
        "active_consumers_do_not_reference_removed_dated_bundles": scan["pass"],
        "rolling_current_transport_is_producer_and_request_contract": (
            request.get("retentionMode") == "rolling-current-transport"
        ),
        "current_transport_assets_match_canonical_assets": parity["all_match"],
        "git_image_noise_reduction_exceeds_5mb": image_noise_reduction > 5_000_000,
        "transient_state_classes_have_bounded_target_retention": all(
            row.get("retention_class") not in {"CLASSIFY_IN_STAGE_7", ""}
            for row in entries
            if row.get("artifact_class_id") in {"harness-checkpoints", "vfmedia-operational-data"}
        ),
        "work_ledger_resolved_without_new_store": work_ledger_decision["new_store_created"] is False,
        "no_external_effect_authority_change": current_policy == baseline_policy,
        "rollback_and_audit_chain_preserved": bool(stage7d.get("rollback")) and archive.get("file_count") == 86,
    }

    report = {
        "schema": "velvetos.stage7d-artifact-retention.v1",
        "stage": "7D",
        "behavior_change": True,
        "prepared_against_main_sha": args.prepared_against,
        "captured_at": args.captured_at,
        "purpose": "Bound artifact retention and reduce Git-generated-output noise without losing audit history or creating a second state store.",
        "retention_registry": {
            "path": RETENTION.relative_to(ROOT).as_posix(),
            "sha256": sha256(RETENTION),
            "artifact_class_count": len(entries),
            "unclassified_retention_count": sum(
                "CLASSIFY_IN_STAGE_7" in str(row.get("retention_class")) for row in entries
            ),
        },
        "copy_first_migration": {
            "source_scope": list(REMOVED_GLOBS),
            "archive_receipt": ARCHIVE_RECEIPT.relative_to(ROOT).as_posix(),
            "archive_receipt_sha256": sha256(ARCHIVE_RECEIPT),
            "archive_directories": archive.get("directory_count"),
            "archive_files": archive.get("file_count"),
            "archive_bytes": archive.get("bytes"),
            "historical_asset_dirs_remaining_in_tree": len(historical_dirs),
            "current_asset_files": parity["files"],
            "current_asset_bytes": current_asset_bytes,
            "generated_image_bytes_reduced": image_noise_reduction,
            "local_archive_path_recorded": archive.get("archive_root"),
        },
        "consumer_scan": scan,
        "current_transport": {
            **CURRENT_TRANSPORT,
            "asset_parity": parity,
            "request_enabled_on_main": bool(request.get("enabled")),
        },
        "repository_footprint": {
            "base_tree": base_metrics,
            "projected_worktree_before_report_commit": projected_metrics,
            "note": "Projected metrics include current untracked non-ignored files and exclude removed worktree files; report self-size is not used as a gate.",
        },
        "work_ledger": work_ledger_decision,
        "authority_baseline": {
            "policy_registry_sha256": sha256(POLICY_REGISTRY),
            "unchanged_from_prepared_against": current_policy == baseline_policy,
        },
        "acceptance": criteria,
        "repository_acceptance": "PASS" if all(criteria.values()) else "FAIL",
        "next_stage": "Stage 7 integrated acceptance gate" if all(criteria.values()) else None,
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        "STAGE7D_ARTIFACT_RETENTION "
        f"acceptance={report['repository_acceptance']} "
        f"criteria={sum(bool(v) for v in criteria.values())}/{len(criteria)} "
        f"archived={archive.get('file_count')} current_assets={parity['files']} "
        f"reduced_bytes={image_noise_reduction}"
    )
    return 0 if report["repository_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
