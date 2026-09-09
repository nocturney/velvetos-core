"""Durable auto-intake runner for the single vfmedia catalog."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import backoff as backoff_mod
from . import lock as lockmod
from . import persist as persist_mod
from .drive import (
    SOURCE_ID,
    AuthMissingError,
    DownloadUnverifiedError,
    DriveFile,
    GoogleApiProvider,
    ListingError,
    ListingProvider,
    MemoryFixtureProvider,
    content_fingerprint,
    iter_inbox,
)

ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "packages" / "vfmedia"
CATALOG = PACK / "catalog.json"
STATE_DIR = PACK / "state"
DATA_DIR = PACK / "data"
RUNNER_STATE = STATE_DIR / "intake-runner.json"
LOCK_PATH = STATE_DIR / "intake.lock"
PENDING_MOVES = STATE_DIR / "pending-drive-actions.json"
EVENTS = DATA_DIR / "intake-events.jsonl"
INBOX_QUEUE = ROOT / "office" / "control" / "inbox.json"
BRIEF_SIGNAL = DATA_DIR / "intake-brief.json"
FIXTURE_LISTING = PACK / "fixtures" / "inbox-listing.json"
RECOVERY_LOG = DATA_DIR / "intake-recovery.jsonl"

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_BUSY = 2
EXIT_AUTH = 3
EXIT_PERSIST = 4


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    persist_mod.atomic_write_json(path, data)


def append_event(name: str, payload: dict, *, correlation_id: str | None = None) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    row = {
        "name": name,
        "producedAt": _now(),
        "layer": "office",
        "source": "vfmedia.intake",
        "correlationId": correlation_id or payload.get("fileId") or "",
        "payload": payload,
    }
    with EVENTS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def append_recovery(payload: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    row = {"producedAt": _now(), **payload}
    with RECOVERY_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def default_runner_state() -> dict:
    return {
        "name": "vfmedia-intake-runner",
        "component_state": "Idle",
        "updatedAt": _now(),
        "pagination": {"pageToken": None, "pageSize": 50},
        "catalogDigest": None,
        "inboxDigest": None,
        "lastRunAt": None,
        "lastSuccessAt": None,
        "lastError": None,
        "persistError": None,
        "auth": {"ready": False, "detail": "not checked"},
        "stats": {
            "runs": 0,
            "registered": 0,
            "verified": 0,
            "skipped": 0,
            "failed": 0,
            "duplicates": 0,
            "content_changed": 0,
            "recovered": 0,
            "unverified": 0,
        },
        "retries": {},
        "backoffPolicy": {
            "stepsSeconds": list(backoff_mod.BACKOFF_SECONDS),
            "permanentStop": False,
            "note": "never permanent stop — escalate then repeat last interval",
        },
        "schedule": {
            "targetMinutes": 5,
            "githubActionsCron": "*/5 * * * *",
            "note": "GHA minimum interval is 5 minutes; runs may be delayed under platform load",
        },
        "activation": {
            "proven": False,
            "evidence": None,
            "note": "Do not mark auto-intake complete without Drive-backed live activation proof",
        },
    }


def load_runner_state() -> dict:
    state = load_json(RUNNER_STATE, None)
    if not isinstance(state, dict):
        return default_runner_state()
    base = default_runner_state()
    base.update(state)
    base["stats"] = {**default_runner_state()["stats"], **(state.get("stats") or {})}
    base["activation"] = {
        **default_runner_state()["activation"],
        **(state.get("activation") or {}),
    }
    base["pagination"] = {
        **default_runner_state()["pagination"],
        **(state.get("pagination") or {}),
    }
    return base


def save_runner_state(state: dict) -> None:
    state["updatedAt"] = _now()
    write_json(RUNNER_STATE, state)


def catalog_index(catalog: dict) -> dict[str, dict]:
    by_id: dict[str, dict] = {}
    for item in catalog.get("items") or []:
        fid = ((item.get("sourceFile") or {}).get("id") or "").strip()
        if fid:
            by_id[fid] = item
    return by_id


def mime_description(file: DriveFile) -> str:
    mt = (file.mimeType or "").lower()
    if mt.startswith("image/"):
        kind = "תמונה"
    elif mt.startswith("video/"):
        kind = "וידאו"
    elif mt.startswith("audio/"):
        kind = "אודיו"
    elif "pdf" in mt:
        kind = "PDF"
    elif mt.startswith("text/"):
        kind = "טקסט"
    else:
        kind = "קובץ"
    return (
        f"{kind} · שם קובץ: {file.name} · נרשם אוטומטית מקליטת נכנס "
        f"· טרם ניתוח חזותי · אין קישור מוצר"
    )


def new_catalog_item(file: DriveFile) -> dict:
    uploaded = (file.createdTime or "")[:10] or _today()
    return {
        "id": f"media-{file.id}",
        "sourceFile": {"id": file.id, "url": file.webViewLink},
        "viewDescription": mime_description(file),
        "uploadedAt": uploaded,
        "productLink": None,
        "status": "inbox",
        "assignee": "ops-intake",
        "derivativeIds": [],
        "sourceLinks": [],
        "versionApproval": {"state": "none"},
        "intake": {
            "phase": "registered",
            "registeredAt": _now(),
            "verifiedAt": None,
            "downloadBytes": None,
            "movedToSourceAt": None,
            "attempts": 0,
            "lastError": None,
            "contentFingerprint": None,
            "headRevisionId": file.headRevisionId,
            "md5Checksum": file.md5Checksum,
            "sha256Checksum": file.sha256Checksum,
        },
        "visualReview": {
            "state": "none",
            "reviewedAt": None,
            "note": "visual review does not block intake",
        },
    }


def phase_of(item: dict) -> str:
    intake = item.get("intake") or {}
    if intake.get("phase") == "verified" or (
        item.get("status") == "source" and intake.get("verifiedAt")
    ):
        return "verified"
    if intake.get("phase") == "registered" or item.get("status") == "inbox":
        return "registered"
    if item.get("status") == "source":
        return "verified"
    return "registered"


def count_phases(catalog: dict) -> dict[str, int]:
    registered = verified = visual = 0
    for item in catalog.get("items") or []:
        ph = phase_of(item)
        if ph == "verified":
            verified += 1
        else:
            registered += 1
        if (item.get("visualReview") or {}).get("state") == "done":
            visual += 1
    return {
        "registered_in_catalog": registered + verified,
        "registered_only": registered,
        "verified_and_intaken": verified,
        "visually_reviewed": visual,
        "inbox_status": sum(
            1 for it in (catalog.get("items") or []) if it.get("status") == "inbox"
        ),
        "source_status": sum(
            1 for it in (catalog.get("items") or []) if it.get("status") == "source"
        ),
        "total": len(catalog.get("items") or []),
    }


def persist_catalog(catalog: dict, state: dict) -> None:
    digest = persist_mod.save_catalog_conflict_aware(
        CATALOG,
        catalog,
        expected_digest=state.get("catalogDigest"),
    )
    state["catalogDigest"] = digest
    catalog["updatedAt"] = _today()


def update_inbox_queue(summary: dict, state: dict) -> None:
    inbox, dig = persist_mod.load_json_with_digest(
        INBOX_QUEUE, {"buckets": {}, "updatedAt": _today()}
    )
    if state.get("inboxDigest") is None:
        state["inboxDigest"] = dig
    buckets = inbox.setdefault("buckets", {})
    prod = buckets.setdefault("production", [])
    prod[:] = [x for x in prod if x.get("id") != "vfmedia-auto-intake"]
    prod.append(
        {
            "id": "vfmedia-auto-intake",
            "title": "קליטת מדיה אוטומטית — נכנס→מקור",
            "state": summary.get("component_state") or "Idle",
            "updatedAt": _now(),
            "counts": {
                "registered_only": summary.get("registered_only"),
                "verified_and_intaken": summary.get("verified_and_intaken"),
                "visually_reviewed": summary.get("visually_reviewed"),
                "pending_moves": summary.get("pending_moves"),
            },
            "note": "registered ≠ verified ≠ visually_reviewed · validate≠monitoring",
            "source": "vfmedia.intake",
        }
    )
    inbox["updatedAt"] = _today()
    state["inboxDigest"] = persist_mod.save_inbox_conflict_aware(
        INBOX_QUEUE, inbox, expected_digest=state.get("inboxDigest")
    )


def write_brief_signal(summary: dict) -> None:
    write_json(
        BRIEF_SIGNAL,
        {
            "generatedAt": _now(),
            "slot": "05",
            "title": "קליטת מדיה",
            "phases": {
                "registered_in_catalog": summary.get("registered_in_catalog"),
                "registered_only": summary.get("registered_only"),
                "verified_and_intaken": summary.get("verified_and_intaken"),
                "visually_reviewed": summary.get("visually_reviewed"),
            },
            "runner": {
                "component_state": summary.get("component_state"),
                "lastRunAt": summary.get("lastRunAt"),
                "lastError": summary.get("lastError"),
                "persistError": summary.get("persistError"),
                "activation_proven": summary.get("activation_proven"),
                "auth": summary.get("auth"),
            },
            "note": "מונים ב־HANDOFF אינם תחליף לאירוע קליטה עמיד · vfmedia.py validate ≠ ניטור",
        },
    )


def build_provider(args: argparse.Namespace):
    if args.provider == "fixture":
        path = Path(args.listing) if args.listing else FIXTURE_LISTING
        return MemoryFixtureProvider(path)
    if args.provider == "listing":
        if not args.listing:
            raise SystemExit("listing provider requires --listing PATH")
        return ListingProvider(
            Path(args.listing),
            move_mode=args.move_mode,
            pending_path=PENDING_MOVES,
        )
    if args.provider == "google":
        return GoogleApiProvider()
    raise SystemExit(f"unknown provider {args.provider}")


def _mark_pending_status(file_id: str, status: str) -> None:
    pending = load_json(PENDING_MOVES, {"actions": []})
    actions = pending.setdefault("actions", [])
    found = False
    for action in actions:
        if action.get("fileId") == file_id:
            action["status"] = status
            action["updatedAt"] = _now()
            found = True
    if not found and status in {"pending", "moving"}:
        actions.append(
            {
                "op": "move",
                "fileId": file_id,
                "fromFolderId": "1IG4zNTOuGgvPyhEbKQEKwjRjFD6BuUDJ",
                "toFolderId": SOURCE_ID,
                "status": status,
                "updatedAt": _now(),
            }
        )
    pending["updatedAt"] = _now()
    write_json(PENDING_MOVES, pending)


def apply_content_change(item: dict, file: DriveFile, new_fp: str) -> None:
    """Same fileId, new content/revision — do not inherit approval."""
    item["versionApproval"] = {"state": "none"}
    item["visualReview"] = {
        "state": "none",
        "reviewedAt": None,
        "note": "reset after content change — approval not inherited",
    }
    item["status"] = "inbox"
    intake = item.setdefault("intake", {})
    intake["phase"] = "registered"
    intake["verifiedAt"] = None
    intake["movedToSourceAt"] = None
    intake["contentFingerprint"] = new_fp
    intake["headRevisionId"] = file.headRevisionId
    intake["md5Checksum"] = file.md5Checksum
    intake["sha256Checksum"] = file.sha256Checksum
    intake["contentChangedAt"] = _now()
    intake["lastError"] = None


def recover_after_move(provider, catalog: dict, by_id: dict[str, dict], state: dict) -> int:
    """Reconcile items that moved on Drive but catalog verify was not saved."""
    recovered = 0
    pending = load_json(PENDING_MOVES, {"actions": []})
    candidates: set[str] = set()
    for action in pending.get("actions") or []:
        if action.get("status") in {"moving", "move_done_unconfirmed", "pending"}:
            candidates.add(action["fileId"])
    for item in catalog.get("items") or []:
        intake = item.get("intake") or {}
        if intake.get("phase") == "registered" and intake.get("moveStartedAt"):
            fid = (item.get("sourceFile") or {}).get("id")
            if fid:
                candidates.add(fid)
    for fid in candidates:
        item = by_id.get(fid)
        if not item:
            continue
        if phase_of(item) == "verified":
            continue
        try:
            parents = provider.get_parents(fid)
        except Exception as exc:  # noqa: BLE001
            append_recovery({"fileId": fid, "ok": False, "error": str(exc)})
            continue
        if SOURCE_ID not in parents:
            continue
        intake = item.setdefault("intake", {})
        item["status"] = "source"
        intake["phase"] = "verified"
        intake["verifiedAt"] = _now()
        intake["movedToSourceAt"] = intake["verifiedAt"]
        intake["lastError"] = None
        intake["recoveredAfterMove"] = True
        append_event(
            "media.intake.verified",
            {
                "fileId": fid,
                "catalogId": item["id"],
                "phase": "verified",
                "via": "recovery",
                "downloadBytes": intake.get("downloadBytes"),
            },
            correlation_id=item["id"],
        )
        append_recovery({"fileId": fid, "ok": True, "via": "parents-contain-source"})
        _mark_pending_status(fid, "done")
        state["stats"]["recovered"] = int(state["stats"].get("recovered") or 0) + 1
        recovered += 1
        persist_catalog(catalog, state)
        save_runner_state(state)
    return recovered


def process_file(
    provider,
    catalog: dict,
    by_id: dict[str, dict],
    state: dict,
    file: DriveFile,
    *,
    register_only: bool,
    defer_verify_until_move_applied: bool,
) -> str:
    """Return action label for stats."""
    item = by_id.get(file.id)
    incoming_fp = content_fingerprint(file)

    if item and phase_of(item) == "verified":
        prior_fp = (item.get("intake") or {}).get("contentFingerprint")
        weak_incoming = incoming_fp.startswith("meta:")
        strong_prior = bool(prior_fp) and not str(prior_fp).startswith("meta:")
        if prior_fp == incoming_fp:
            state["stats"]["duplicates"] = int(state["stats"].get("duplicates") or 0) + 1
            return "duplicate"
        if strong_prior and weak_incoming:
            # Listing meta alone must not reopen a strongly verified row
            state["stats"]["duplicates"] = int(state["stats"].get("duplicates") or 0) + 1
            return "duplicate"
        if prior_fp and prior_fp != incoming_fp:
            apply_content_change(item, file, incoming_fp)
            state["stats"]["content_changed"] = int(state["stats"].get("content_changed") or 0) + 1
            append_event(
                "media.intake.content_changed",
                {
                    "fileId": file.id,
                    "catalogId": item["id"],
                    "priorFingerprint": prior_fp,
                    "newFingerprint": incoming_fp,
                    "approvalInherited": False,
                },
                correlation_id=item["id"],
            )
            persist_catalog(catalog, state)
            save_runner_state(state)
        else:
            state["stats"]["duplicates"] = int(state["stats"].get("duplicates") or 0) + 1
            return "duplicate"

    if not item:
        item = new_catalog_item(file)
        item["intake"]["contentFingerprint"] = incoming_fp
        catalog.setdefault("items", []).append(item)
        by_id[file.id] = item
        state["stats"]["registered"] = int(state["stats"].get("registered") or 0) + 1
        append_event(
            "media.intake.registered",
            {
                "fileId": file.id,
                "catalogId": item["id"],
                "name": file.name,
                "mimeType": file.mimeType,
                "phase": "registered",
                "contentFingerprint": incoming_fp,
            },
            correlation_id=item["id"],
        )
        # Durable register BEFORE any Drive move
        persist_catalog(catalog, state)
        save_runner_state(state)
        if register_only:
            return "registered"

    intake = item.setdefault(
        "intake",
        {
            "phase": "registered",
            "registeredAt": _now(),
            "verifiedAt": None,
            "downloadBytes": None,
            "movedToSourceAt": None,
            "attempts": 0,
            "lastError": None,
            "contentFingerprint": incoming_fp,
        },
    )
    item.setdefault(
        "visualReview",
        {"state": "none", "reviewedAt": None, "note": "visual review does not block intake"},
    )

    if register_only:
        persist_catalog(catalog, state)
        return "registered"

    retry_row = (state.get("retries") or {}).get(file.id)
    if not backoff_mod.ready_for_retry(retry_row):
        return "backoff"

    try:
        data = provider.download_bytes(file)
        fp = content_fingerprint(file, data)
        prior_fp = intake.get("contentFingerprint")
        if prior_fp and prior_fp != fp:
            apply_content_change(item, file, fp)
            state["stats"]["content_changed"] = int(state["stats"].get("content_changed") or 0) + 1
            append_event(
                "media.intake.content_changed",
                {
                    "fileId": file.id,
                    "catalogId": item["id"],
                    "priorFingerprint": prior_fp,
                    "newFingerprint": fp,
                    "approvalInherited": False,
                },
                correlation_id=item["id"],
            )
        intake["contentFingerprint"] = fp
        intake["downloadBytes"] = len(data)
        intake["md5Checksum"] = file.md5Checksum
        intake["sha256Checksum"] = file.sha256Checksum
        intake["headRevisionId"] = file.headRevisionId
        intake["attempts"] = int(intake.get("attempts") or 0) + 1
        intake["moveStartedAt"] = _now()
        # Persist download evidence + move intent before Drive mutation
        persist_catalog(catalog, state)
        _mark_pending_status(file.id, "moving")
        save_runner_state(state)

        try:
            provider.move_to_source(file.id)
        except Exception as move_exc:
            # Move failed — stay registered; durable state already saved
            raise move_exc

        # Move succeeded — mark unconfirmed until catalog save completes
        _mark_pending_status(file.id, "move_done_unconfirmed")

        if defer_verify_until_move_applied or getattr(provider, "move_mode", None) == "pending":
            intake["phase"] = "registered"
            intake["lastError"] = None
            append_event(
                "media.intake.move_pending",
                {
                    "fileId": file.id,
                    "catalogId": item["id"],
                    "phase": "registered",
                    "downloadBytes": intake["downloadBytes"],
                    "pending": True,
                    "contentFingerprint": fp,
                },
                correlation_id=item["id"],
            )
            persist_catalog(catalog, state)
            _mark_pending_status(file.id, "pending")
            state.setdefault("retries", {}).pop(file.id, None)
            save_runner_state(state)
            return "pending_move"

        item["status"] = "source"
        intake["phase"] = "verified"
        intake["verifiedAt"] = _now()
        intake["movedToSourceAt"] = intake["verifiedAt"]
        intake["lastError"] = None
        state["stats"]["verified"] = int(state["stats"].get("verified") or 0) + 1
        append_event(
            "media.intake.verified",
            {
                "fileId": file.id,
                "catalogId": item["id"],
                "name": file.name,
                "phase": "verified",
                "downloadBytes": intake["downloadBytes"],
                "contentFingerprint": fp,
            },
            correlation_id=item["id"],
        )
        persist_catalog(catalog, state)
        _mark_pending_status(file.id, "done")
        state.setdefault("retries", {}).pop(file.id, None)
        save_runner_state(state)
        return "verified"
    except DownloadUnverifiedError as exc:
        err = str(exc)
        intake["lastError"] = err
        intake["attempts"] = int(intake.get("attempts") or 0) + 1
        # Stay registered — metadata is not verification
        intake["phase"] = "registered"
        state["stats"]["unverified"] = int(state["stats"].get("unverified") or 0) + 1
        state.setdefault("retries", {})[file.id] = backoff_mod.record_failure(
            state.get("retries", {}).get(file.id), err
        )
        append_event(
            "media.intake.unverified",
            {
                "fileId": file.id,
                "catalogId": item.get("id"),
                "error": err,
                "phase": "registered",
            },
            correlation_id=item.get("id"),
        )
        persist_catalog(catalog, state)
        save_runner_state(state)
        return "unverified"
    except Exception as exc:  # noqa: BLE001
        err = str(exc)
        intake["lastError"] = err
        intake["attempts"] = int(intake.get("attempts") or 0) + 1
        state["stats"]["failed"] = int(state["stats"].get("failed") or 0) + 1
        state.setdefault("retries", {})[file.id] = backoff_mod.record_failure(
            state.get("retries", {}).get(file.id), err
        )
        append_event(
            "media.intake.failed",
            {
                "fileId": file.id,
                "catalogId": item.get("id"),
                "error": err,
                "attempts": intake["attempts"],
                "nextAfter": state["retries"][file.id].get("nextAfter"),
                "backoffSeconds": state["retries"][file.id].get("backoffSeconds"),
                "permanentStop": False,
            },
            correlation_id=item.get("id"),
        )
        persist_catalog(catalog, state)
        save_runner_state(state)
        return "failed"


def apply_confirmed_moves(confirmed_path: Path) -> int:
    confirmed = load_json(confirmed_path, {})
    ids = set(confirmed.get("movedFileIds") or [])
    if not ids and confirmed.get("fileId"):
        ids.add(confirmed["fileId"])
    if not ids:
        print("FAIL apply-moves: no movedFileIds", file=sys.stderr)
        return EXIT_FAIL

    catalog, dig = persist_mod.load_json_with_digest(CATALOG, {"items": []})
    state = load_runner_state()
    state["catalogDigest"] = dig
    by_id = catalog_index(catalog)
    pending = load_json(PENDING_MOVES, {"actions": []})
    n = 0
    for fid in ids:
        item = by_id.get(fid)
        if not item:
            continue
        intake = item.setdefault("intake", {})
        item["status"] = "source"
        intake["phase"] = "verified"
        intake["verifiedAt"] = _now()
        intake["movedToSourceAt"] = intake["verifiedAt"]
        intake["lastError"] = None
        append_event(
            "media.intake.verified",
            {
                "fileId": fid,
                "catalogId": item["id"],
                "phase": "verified",
                "downloadBytes": intake.get("downloadBytes"),
                "via": "apply-moves",
            },
            correlation_id=item["id"],
        )
        n += 1
        state["stats"]["verified"] = int(state["stats"].get("verified") or 0) + 1
        state.setdefault("retries", {}).pop(fid, None)
        for action in pending.get("actions") or []:
            if action.get("fileId") == fid:
                action["status"] = "done"
                action["doneAt"] = _now()
        persist_catalog(catalog, state)

    write_json(PENDING_MOVES, pending)
    phases = count_phases(catalog)
    state["component_state"] = "Idle"
    state["lastSuccessAt"] = _now()
    save_runner_state(state)
    summary = {
        **phases,
        "component_state": state["component_state"],
        "lastRunAt": state.get("lastRunAt"),
        "lastError": None,
        "persistError": None,
        "activation_proven": state["activation"].get("proven"),
        "auth": state.get("auth"),
        "pending_moves": sum(
            1 for a in (pending.get("actions") or []) if a.get("status") == "pending"
        ),
    }
    update_inbox_queue(summary, state)
    write_brief_signal(summary)
    save_runner_state(state)
    print(f"OK apply-moves verified={n}")
    return EXIT_OK


def _summary_from(state: dict, catalog: dict, pending_n: int = 0) -> dict:
    phases = count_phases(catalog)
    return {
        **phases,
        "component_state": state.get("component_state"),
        "lastRunAt": state.get("lastRunAt"),
        "lastError": state.get("lastError"),
        "persistError": state.get("persistError"),
        "activation_proven": (state.get("activation") or {}).get("proven"),
        "auth": state.get("auth"),
        "pending_moves": pending_n,
    }


def run_intake(args: argparse.Namespace) -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    state = load_runner_state()

    handle = lockmod.acquire(LOCK_PATH)
    if handle is None:
        state["component_state"] = "Processing"
        state["lastError"] = "overlapping run skipped (local lock)"
        state["lastRunAt"] = _now()
        save_runner_state(state)
        try:
            update_inbox_queue(_summary_from(state, load_json(CATALOG, {"items": []})), state)
            write_brief_signal(_summary_from(state, load_json(CATALOG, {"items": []})))
            save_runner_state(state)
        except Exception:  # noqa: BLE001
            pass
        print("BUSY intake lock held — overlapping run skipped", file=sys.stderr)
        return EXIT_BUSY

    try:
        try:
            provider = build_provider(args)
            state["auth"] = {"ready": True, "detail": f"provider={provider.name}"}
        except AuthMissingError as exc:
            state["component_state"] = "Blocked"
            state["lastError"] = str(exc)
            state["auth"] = {"ready": False, "detail": str(exc)}
            state["lastRunAt"] = _now()
            save_runner_state(state)
            catalog = load_json(CATALOG, {"items": []})
            summary = _summary_from(state, catalog)
            try:
                update_inbox_queue(summary, state)
                write_brief_signal(summary)
                save_runner_state(state)
            except persist_mod.PersistError as pe:
                state["persistError"] = str(pe)
                save_runner_state(state)
                print(f"AUTH+PERSIST {exc} | {pe}", file=sys.stderr)
                return EXIT_PERSIST
            print(f"AUTH {exc}", file=sys.stderr)
            return EXIT_AUTH

        catalog, dig = persist_mod.load_json_with_digest(CATALOG, None)
        if not isinstance(catalog, dict) or catalog.get("oneCatalog") is not True:
            print("FAIL catalog.json oneCatalog lock broken", file=sys.stderr)
            return EXIT_FAIL
        state["catalogDigest"] = dig
        by_id = catalog_index(catalog)

        state["component_state"] = "Processing"
        state["lastRunAt"] = _now()
        state["lastError"] = None
        state["persistError"] = None
        state["stats"]["runs"] = int(state["stats"].get("runs") or 0) + 1
        save_runner_state(state)

        # Recover moves that succeeded on Drive but failed to persist verify
        recover_after_move(provider, catalog, by_id, state)
        by_id = catalog_index(catalog)

        page_size = int(args.page_size or state["pagination"].get("pageSize") or 50)
        start_token = args.page_token
        if start_token is None and not args.reset_pagination:
            start_token = state["pagination"].get("pageToken")

        max_files = int(args.max_files or 0) or 10**9
        processed = 0
        actions: dict[str, int] = {}
        last_next = None
        defer = args.move_mode == "pending" and args.provider == "listing"

        try:
            for file, next_token in iter_inbox(
                provider, page_size=page_size, start_token=start_token
            ):
                last_next = next_token
                if args.only_file_id and file.id != args.only_file_id:
                    continue
                result = process_file(
                    provider,
                    catalog,
                    by_id,
                    state,
                    file,
                    register_only=bool(args.register_only),
                    defer_verify_until_move_applied=defer,
                )
                actions[result] = actions.get(result, 0) + 1
                processed += 1
                if processed >= max_files:
                    break
        except ListingError as exc:
            state["component_state"] = "Degraded"
            state["lastError"] = f"listing: {exc}"
            state.setdefault("retries", {})["__listing__"] = backoff_mod.record_failure(
                state.get("retries", {}).get("__listing__"), str(exc)
            )
            append_event(
                "media.intake.listing_failed",
                {
                    "error": str(exc),
                    "pageToken": start_token,
                    "nextAfter": state["retries"]["__listing__"].get("nextAfter"),
                    "permanentStop": False,
                },
            )
            save_runner_state(state)
            summary = _summary_from(state, catalog)
            update_inbox_queue(summary, state)
            write_brief_signal(summary)
            save_runner_state(state)
            print(f"FAIL listing: {exc}", file=sys.stderr)
            return EXIT_FAIL

        if processed >= max_files and last_next:
            state["pagination"]["pageToken"] = start_token
        else:
            state["pagination"]["pageToken"] = last_next
        state["pagination"]["pageSize"] = page_size
        # Clear listing backoff on success
        state.setdefault("retries", {}).pop("__listing__", None)

        persist_catalog(catalog, state)

        pending = load_json(PENDING_MOVES, {"actions": []})
        pending_n = sum(
            1 for a in (pending.get("actions") or []) if a.get("status") in {"pending", "moving"}
        )

        if actions.get("verified") and args.provider == "google":
            state["activation"] = {
                "proven": True,
                "evidence": f"provider=google; actions={actions}",
                "provenAt": _now(),
                "note": "Drive API live verify+move",
            }
        elif actions.get("registered") or actions.get("verified") or actions.get("pending_move"):
            if args.mark_activation or args.provider == "fixture":
                state["activation"] = {
                    "proven": True,
                    "evidence": f"provider={provider.name}; actions={actions}",
                    "provenAt": _now(),
                    "note": "runner processed inbox file (see activation evidence)",
                }

        failedish = actions.get("failed") or actions.get("unverified")
        state["component_state"] = "Degraded" if failedish else "Idle"
        if not failedish:
            state["lastSuccessAt"] = _now()
        else:
            state["lastError"] = f"actions={actions}"
        save_runner_state(state)

        summary = _summary_from(state, catalog, pending_n)
        update_inbox_queue(summary, state)
        write_brief_signal(summary)
        save_runner_state(state)

        print(
            "OK intake "
            f"provider={provider.name} processed={processed} actions={actions} "
            f"phases={count_phases(catalog)} pending_moves={pending_n} "
            f"activation={state['activation'].get('proven')}"
        )
        return EXIT_OK
    except persist_mod.PersistError as exc:
        state = load_runner_state()
        state["component_state"] = "Degraded"
        state["persistError"] = str(exc)
        state["lastError"] = str(exc)
        state["lastRunAt"] = _now()
        try:
            save_runner_state(state)
        except Exception:  # noqa: BLE001
            print(f"PERSIST {exc} (runner state also unsaved)", file=sys.stderr)
            return EXIT_PERSIST
        print(f"PERSIST {exc}", file=sys.stderr)
        return EXIT_PERSIST
    except Exception as exc:  # noqa: BLE001
        state = load_runner_state()
        state["component_state"] = "Degraded"
        state["lastError"] = str(exc)
        state["lastRunAt"] = _now()
        try:
            save_runner_state(state)
            update_inbox_queue(_summary_from(state, load_json(CATALOG, {"items": []})), state)
            write_brief_signal(_summary_from(state, load_json(CATALOG, {"items": []})))
            save_runner_state(state)
        except Exception as pe:  # noqa: BLE001
            print(f"FAIL intake: {exc} | persist: {pe}", file=sys.stderr)
            return EXIT_PERSIST
        print(f"FAIL intake: {exc}", file=sys.stderr)
        return EXIT_FAIL
    finally:
        handle.release()


def run_selftest(_args: argparse.Namespace | None = None) -> int:
    """Offline proof + hardening checks (no Drive)."""
    import shutil
    import tempfile

    global CATALOG, STATE_DIR, DATA_DIR, RUNNER_STATE, LOCK_PATH, PENDING_MOVES, EVENTS
    global BRIEF_SIGNAL, INBOX_QUEUE, RECOVERY_LOG

    if not FIXTURE_LISTING.is_file():
        print("FAIL missing fixtures/inbox-listing.json", file=sys.stderr)
        return EXIT_FAIL

    with tempfile.TemporaryDirectory(prefix="vfmedia-intake-") as tmp:
        tmp_path = Path(tmp)
        cat = load_json(CATALOG)
        fixture = load_json(FIXTURE_LISTING)
        fixture_ids = {f["id"] for f in (fixture.get("files") or [])}
        cat["items"] = [
            it
            for it in (cat.get("items") or [])
            if (it.get("sourceFile") or {}).get("id") not in fixture_ids
        ]
        work_pack = tmp_path / "vfmedia"
        shutil.copytree(PACK / "fixtures", work_pack / "fixtures")
        (work_pack / "state").mkdir(parents=True)
        (work_pack / "data").mkdir(parents=True)
        write_json(work_pack / "catalog.json", cat)

        old = (
            CATALOG,
            STATE_DIR,
            DATA_DIR,
            RUNNER_STATE,
            LOCK_PATH,
            PENDING_MOVES,
            EVENTS,
            BRIEF_SIGNAL,
            INBOX_QUEUE,
            RECOVERY_LOG,
        )
        CATALOG = work_pack / "catalog.json"
        STATE_DIR = work_pack / "state"
        DATA_DIR = work_pack / "data"
        RUNNER_STATE = STATE_DIR / "intake-runner.json"
        LOCK_PATH = STATE_DIR / "intake.lock"
        PENDING_MOVES = STATE_DIR / "pending-drive-actions.json"
        EVENTS = DATA_DIR / "intake-events.jsonl"
        BRIEF_SIGNAL = DATA_DIR / "intake-brief.json"
        RECOVERY_LOG = DATA_DIR / "intake-recovery.jsonl"
        INBOX_QUEUE = tmp_path / "inbox.json"
        write_json(INBOX_QUEUE, {"updatedAt": _today(), "buckets": {"production": []}})

        try:
            ns = argparse.Namespace(
                provider="fixture",
                listing=str(work_pack / "fixtures" / "inbox-listing.json"),
                move_mode="memory",
                page_size=50,
                page_token=None,
                reset_pagination=True,
                max_files=10,
                register_only=False,
                only_file_id=None,
                mark_activation=True,
            )
            rc = run_intake(ns)
            if rc != EXIT_OK:
                print(f"FAIL selftest first run rc={rc}", file=sys.stderr)
                return EXIT_FAIL
            cat1 = load_json(CATALOG)
            by = catalog_index(cat1)
            new_id = next(iter(fixture_ids))
            item = by.get(new_id)
            if not item or phase_of(item) != "verified" or item.get("status") != "source":
                print("FAIL selftest did not verify+move new file", file=sys.stderr)
                return EXIT_FAIL
            if not (item.get("intake") or {}).get("contentFingerprint"):
                print("FAIL selftest missing contentFingerprint", file=sys.stderr)
                return EXIT_FAIL
            events = EVENTS.read_text(encoding="utf-8").splitlines()
            names = [json.loads(x)["name"] for x in events if x.strip()]
            if "media.intake.registered" not in names or "media.intake.verified" not in names:
                print(f"FAIL selftest events missing: {names}", file=sys.stderr)
                return EXIT_FAIL

            before = len(cat1["items"])
            rc2 = run_intake(ns)
            if rc2 != EXIT_OK:
                print(f"FAIL selftest second run rc={rc2}", file=sys.stderr)
                return EXIT_FAIL
            if len(load_json(CATALOG)["items"]) != before:
                print("FAIL selftest duplicated catalog rows", file=sys.stderr)
                return EXIT_FAIL

            handle = lockmod.acquire(LOCK_PATH)
            assert handle is not None
            rc3 = run_intake(ns)
            handle.release()
            if rc3 != EXIT_BUSY:
                print(f"FAIL selftest expected BUSY got {rc3}", file=sys.stderr)
                return EXIT_FAIL

            print(
                "OK intake selftest "
                f"verified={item['id']} phases={count_phases(load_json(CATALOG))} "
                f"events={len(names)}"
            )
            return EXIT_OK
        finally:
            (
                CATALOG,
                STATE_DIR,
                DATA_DIR,
                RUNNER_STATE,
                LOCK_PATH,
                PENDING_MOVES,
                EVENTS,
                BRIEF_SIGNAL,
                INBOX_QUEUE,
                RECOVERY_LOG,
            ) = old


def cmd_status(_args: argparse.Namespace) -> int:
    state = load_runner_state()
    catalog = load_json(CATALOG, {"items": []})
    phases = count_phases(catalog)
    pending = load_json(PENDING_MOVES, {"actions": []})
    pending_n = sum(
        1 for a in (pending.get("actions") or []) if a.get("status") in {"pending", "moving"}
    )
    out = {
        "component_state": state.get("component_state"),
        "auth": state.get("auth"),
        "lastRunAt": state.get("lastRunAt"),
        "lastSuccessAt": state.get("lastSuccessAt"),
        "lastError": state.get("lastError"),
        "persistError": state.get("persistError"),
        "pagination": state.get("pagination"),
        "stats": state.get("stats"),
        "backoffPolicy": state.get("backoffPolicy"),
        "schedule": state.get("schedule"),
        "activation": state.get("activation"),
        "phases": phases,
        "pending_moves": pending_n,
        "note": {
            "registered": "שורת קטלוג קיימת",
            "verified": "הורדה אומתה + הועבר למקור",
            "visually_reviewed": "ניתוח חזותי (לא חוסם קליטה)",
            "validate": "vfmedia.py validate הוא validator בלבד — לא מנגנון ניטור",
            "driveAuth": "הרשאות Drive לרקע הן תנאי להשלמת הקליטה האוטומטית",
        },
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return EXIT_OK
