"""Durable auto-intake runner for the single vfmedia catalog."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import lock as lockmod
from .drive import (
    AuthMissingError,
    DriveFile,
    GoogleApiProvider,
    ListingProvider,
    MemoryFixtureProvider,
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

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_BUSY = 2
EXIT_AUTH = 3

MAX_ATTEMPTS = 3


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def default_runner_state() -> dict:
    return {
        "name": "vfmedia-intake-runner",
        "component_state": "Idle",
        "updatedAt": _now(),
        "pagination": {"pageToken": None, "pageSize": 50},
        "lastRunAt": None,
        "lastSuccessAt": None,
        "lastError": None,
        "auth": {"ready": False, "detail": "not checked"},
        "stats": {
            "runs": 0,
            "registered": 0,
            "verified": 0,
            "skipped": 0,
            "failed": 0,
            "duplicates": 0,
        },
        "retries": {},
        "activation": {
            "proven": False,
            "evidence": None,
            "note": "Do not mark auto-intake complete without a live activation proof",
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
        # Legacy source row without intake block — catalogued + folder-moved earlier
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
        vr = (item.get("visualReview") or {}).get("state")
        if vr == "done":
            visual += 1
    return {
        "registered_in_catalog": registered + verified,  # all rows
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


def update_inbox_queue(summary: dict) -> None:
    inbox = load_json(INBOX_QUEUE, {"buckets": {}, "updatedAt": _today()})
    buckets = inbox.setdefault("buckets", {})
    prod = buckets.setdefault("production", [])
    # Replace prior auto-intake card
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
    write_json(INBOX_QUEUE, inbox)


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


def _retry_ok(state: dict, file_id: str) -> bool:
    row = (state.get("retries") or {}).get(file_id) or {}
    return int(row.get("attempts") or 0) < MAX_ATTEMPTS


def _bump_retry(state: dict, file_id: str, err: str) -> None:
    retries = state.setdefault("retries", {})
    row = retries.get(file_id) or {"attempts": 0}
    row["attempts"] = int(row.get("attempts") or 0) + 1
    row["lastError"] = err
    row["updatedAt"] = _now()
    retries[file_id] = row


def _clear_retry(state: dict, file_id: str) -> None:
    (state.get("retries") or {}).pop(file_id, None)


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
    """Return action: registered|verified|skipped|duplicate|failed|pending_move."""
    item = by_id.get(file.id)
    if item and phase_of(item) == "verified":
        state["stats"]["duplicates"] = int(state["stats"].get("duplicates") or 0) + 1
        return "duplicate"

    if not item:
        item = new_catalog_item(file)
        catalog.setdefault("items", []).append(item)
        by_id[file.id] = item
        catalog["updatedAt"] = _today()
        state["stats"]["registered"] = int(state["stats"].get("registered") or 0) + 1
        append_event(
            "media.intake.registered",
            {
                "fileId": file.id,
                "catalogId": item["id"],
                "name": file.name,
                "mimeType": file.mimeType,
                "phase": "registered",
            },
            correlation_id=item["id"],
        )
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
        },
    )
    item.setdefault(
        "visualReview",
        {"state": "none", "reviewedAt": None, "note": "visual review does not block intake"},
    )

    if register_only:
        return "registered"

    if not _retry_ok(state, file.id):
        return "failed"

    try:
        data = provider.download_bytes(file)
        intake["downloadBytes"] = len(data)
        intake["attempts"] = int(intake.get("attempts") or 0) + 1
        provider.move_to_source(file.id)
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
                },
                correlation_id=item["id"],
            )
            _clear_retry(state, file.id)
            return "pending_move"

        # Immediate verify (memory / google)
        item["status"] = "source"
        intake["phase"] = "verified"
        intake["verifiedAt"] = _now()
        intake["movedToSourceAt"] = intake["verifiedAt"]
        intake["lastError"] = None
        catalog["updatedAt"] = _today()
        state["stats"]["verified"] = int(state["stats"].get("verified") or 0) + 1
        append_event(
            "media.intake.verified",
            {
                "fileId": file.id,
                "catalogId": item["id"],
                "name": file.name,
                "phase": "verified",
                "downloadBytes": intake["downloadBytes"],
            },
            correlation_id=item["id"],
        )
        _clear_retry(state, file.id)
        return "verified"
    except Exception as exc:  # noqa: BLE001 — durable retry path
        err = str(exc)
        intake["lastError"] = err
        intake["attempts"] = int(intake.get("attempts") or 0) + 1
        _bump_retry(state, file.id, err)
        state["stats"]["failed"] = int(state["stats"].get("failed") or 0) + 1
        append_event(
            "media.intake.failed",
            {
                "fileId": file.id,
                "catalogId": item.get("id"),
                "error": err,
                "attempts": intake["attempts"],
            },
            correlation_id=item.get("id"),
        )
        return "failed"


def apply_confirmed_moves(confirmed_path: Path) -> int:
    """Mark pending moves verified after external Drive MCP/API confirmation."""
    confirmed = load_json(confirmed_path, {})
    ids = set(confirmed.get("movedFileIds") or [])
    if not ids and confirmed.get("fileId"):
        ids.add(confirmed["fileId"])
    if not ids:
        print("FAIL apply-moves: no movedFileIds", file=sys.stderr)
        return EXIT_FAIL

    catalog = load_json(CATALOG, {"items": []})
    by_id = catalog_index(catalog)
    state = load_runner_state()
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
        _clear_retry(state, fid)
        for action in pending.get("actions") or []:
            if action.get("fileId") == fid:
                action["status"] = "done"
                action["doneAt"] = _now()

    catalog["updatedAt"] = _today()
    write_json(CATALOG, catalog)
    write_json(PENDING_MOVES, pending)
    phases = count_phases(catalog)
    state["component_state"] = "Idle"
    state["lastSuccessAt"] = _now()
    if n and not state.get("activation", {}).get("proven"):
        state["activation"] = {
            "proven": True,
            "evidence": str(confirmed_path),
            "provenAt": _now(),
            "note": "live move confirmed via apply-moves",
        }
    save_runner_state(state)
    summary = {
        **phases,
        "component_state": state["component_state"],
        "lastRunAt": state.get("lastRunAt"),
        "lastError": None,
        "activation_proven": state["activation"].get("proven"),
        "auth": state.get("auth"),
        "pending_moves": sum(
            1 for a in (pending.get("actions") or []) if a.get("status") == "pending"
        ),
    }
    update_inbox_queue(summary)
    write_brief_signal(summary)
    print(f"OK apply-moves verified={n}")
    return EXIT_OK


def run_intake(args: argparse.Namespace) -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    state = load_runner_state()

    handle = lockmod.acquire(LOCK_PATH)
    if handle is None:
        state["component_state"] = "Processing"
        state["lastError"] = "overlapping run skipped"
        save_runner_state(state)
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
            phases = count_phases(load_json(CATALOG, {"items": []}))
            summary = {
                **phases,
                "component_state": "Blocked",
                "lastRunAt": state["lastRunAt"],
                "lastError": str(exc),
                "activation_proven": state["activation"].get("proven"),
                "auth": state["auth"],
                "pending_moves": 0,
            }
            update_inbox_queue(summary)
            write_brief_signal(summary)
            print(f"AUTH {exc}", file=sys.stderr)
            return EXIT_AUTH

        catalog = load_json(CATALOG)
        if not isinstance(catalog, dict) or catalog.get("oneCatalog") is not True:
            print("FAIL catalog.json oneCatalog lock broken", file=sys.stderr)
            return EXIT_FAIL
        by_id = catalog_index(catalog)

        state["component_state"] = "Processing"
        state["lastRunAt"] = _now()
        state["lastError"] = None
        state["stats"]["runs"] = int(state["stats"].get("runs") or 0) + 1
        save_runner_state(state)

        page_size = int(args.page_size or state["pagination"].get("pageSize") or 50)
        start_token = args.page_token
        if start_token is None and not args.reset_pagination:
            start_token = state["pagination"].get("pageToken")

        max_files = int(args.max_files or 0) or 10**9
        processed = 0
        actions: dict[str, int] = {}
        last_next = None
        defer = args.move_mode == "pending"

        for file, next_token in iter_inbox(provider, page_size=page_size, start_token=start_token):
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

        # Persist pagination: if we stopped early keep token; else advance
        if processed >= max_files and last_next:
            state["pagination"]["pageToken"] = start_token  # same page resume for next slice
        else:
            state["pagination"]["pageToken"] = last_next
        state["pagination"]["pageSize"] = page_size

        write_json(CATALOG, catalog)

        pending = load_json(PENDING_MOVES, {"actions": []})
        pending_n = sum(1 for a in (pending.get("actions") or []) if a.get("status") == "pending")
        phases = count_phases(catalog)

        # Activation: fixture/selftest or live detection of a new file
        if actions.get("registered") or actions.get("verified") or actions.get("pending_move"):
            if args.mark_activation or args.provider == "fixture":
                state["activation"] = {
                    "proven": True,
                    "evidence": f"provider={provider.name}; actions={actions}",
                    "provenAt": _now(),
                    "note": "runner detected and processed new inbox file without manual catalog edit",
                }

        state["component_state"] = "Degraded" if actions.get("failed") else "Idle"
        if not actions.get("failed"):
            state["lastSuccessAt"] = _now()
        else:
            state["lastError"] = f"failed={actions.get('failed')}"
        save_runner_state(state)

        summary = {
            **phases,
            "component_state": state["component_state"],
            "lastRunAt": state["lastRunAt"],
            "lastError": state.get("lastError"),
            "activation_proven": state["activation"].get("proven"),
            "auth": state.get("auth"),
            "pending_moves": pending_n,
        }
        update_inbox_queue(summary)
        write_brief_signal(summary)

        print(
            "OK intake "
            f"provider={provider.name} processed={processed} actions={actions} "
            f"phases={phases} pending_moves={pending_n} "
            f"activation={state['activation'].get('proven')}"
        )
        return EXIT_OK
    except Exception as exc:  # noqa: BLE001
        state = load_runner_state()
        state["component_state"] = "Degraded"
        state["lastError"] = str(exc)
        state["lastRunAt"] = _now()
        save_runner_state(state)
        print(f"FAIL intake: {exc}", file=sys.stderr)
        return EXIT_FAIL
    finally:
        handle.release()


def run_selftest(_args: argparse.Namespace | None = None) -> int:
    """Offline proof: detect new fixture file, verify+move in memory, dedupe second run."""
    import shutil
    import tempfile

    global CATALOG, STATE_DIR, DATA_DIR, RUNNER_STATE, LOCK_PATH, PENDING_MOVES, EVENTS
    global BRIEF_SIGNAL, INBOX_QUEUE

    if not FIXTURE_LISTING.is_file():
        print("FAIL missing fixtures/inbox-listing.json", file=sys.stderr)
        return EXIT_FAIL

    with tempfile.TemporaryDirectory(prefix="vfmedia-intake-") as tmp:
        tmp_path = Path(tmp)
        # Isolate catalog/state/events
        cat = load_json(CATALOG)
        # Work on a copy of catalog without the fixture file ids
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
        )
        CATALOG = work_pack / "catalog.json"
        STATE_DIR = work_pack / "state"
        DATA_DIR = work_pack / "data"
        RUNNER_STATE = STATE_DIR / "intake-runner.json"
        LOCK_PATH = STATE_DIR / "intake.lock"
        PENDING_MOVES = STATE_DIR / "pending-drive-actions.json"
        EVENTS = DATA_DIR / "intake-events.jsonl"
        BRIEF_SIGNAL = DATA_DIR / "intake-brief.json"
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
            events = EVENTS.read_text(encoding="utf-8").splitlines()
            names = [json.loads(x)["name"] for x in events if x.strip()]
            if "media.intake.registered" not in names or "media.intake.verified" not in names:
                print(f"FAIL selftest events missing: {names}", file=sys.stderr)
                return EXIT_FAIL

            # Second run — dedupe / no duplicate rows
            before = len(cat1["items"])
            rc2 = run_intake(ns)
            if rc2 != EXIT_OK:
                print(f"FAIL selftest second run rc={rc2}", file=sys.stderr)
                return EXIT_FAIL
            cat2 = load_json(CATALOG)
            if len(cat2["items"]) != before:
                print("FAIL selftest duplicated catalog rows", file=sys.stderr)
                return EXIT_FAIL

            # Overlap lock
            handle = lockmod.acquire(LOCK_PATH)
            assert handle is not None
            rc3 = run_intake(ns)
            handle.release()
            if rc3 != EXIT_BUSY:
                print(f"FAIL selftest expected BUSY got {rc3}", file=sys.stderr)
                return EXIT_FAIL

            phases = count_phases(cat2)
            print(
                "OK intake selftest "
                f"verified={item['id']} phases={phases} events={len(names)}"
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
            ) = old


def cmd_status(_args: argparse.Namespace) -> int:
    state = load_runner_state()
    catalog = load_json(CATALOG, {"items": []})
    phases = count_phases(catalog)
    pending = load_json(PENDING_MOVES, {"actions": []})
    pending_n = sum(1 for a in (pending.get("actions") or []) if a.get("status") == "pending")
    out = {
        "component_state": state.get("component_state"),
        "auth": state.get("auth"),
        "lastRunAt": state.get("lastRunAt"),
        "lastSuccessAt": state.get("lastSuccessAt"),
        "lastError": state.get("lastError"),
        "pagination": state.get("pagination"),
        "stats": state.get("stats"),
        "activation": state.get("activation"),
        "phases": phases,
        "pending_moves": pending_n,
        "note": {
            "registered": "שורת קטלוג קיימת",
            "verified": "הורדה אומתה + הועבר למקור",
            "visually_reviewed": "ניתוח חזותי (לא חוסם קליטה)",
            "validate": "vfmedia.py validate הוא validator בלבד — לא מנגנון ניטור",
        },
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return EXIT_OK
