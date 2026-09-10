#!/usr/bin/env python3
"""Jobs ledger adapter — Google Sheet is canonical; local CSV is cache.

Authority (option A):
  Google Sheet ``VF HQ · jobs`` via ``office/ledger/bindings.json``.
Local consumers (Living Studio / Autonomy / World Model) read the cache at
``office/ledger/live/jobs.csv`` after ``jobs pull``.

Pull sources (first that works):
  1. ``--from-csv PATH`` / stdin (agent exported via Drive MCP)
  2. Google Drive API when GOOGLE_TOKEN / credentials exist (same as vfmedia)
  3. Else status ``needs_sheet_sync`` — never invent rows

Write path (write-through when Google Sheets/Drive write auth exists):
  Mutate cache → push_write_through → verify Sheet → refresh cache → clear dirty.
  If provider cannot write: keep dirty + pending-push.csv; never claim Sheet changed.

Consumers must call ``ensure_hydrated`` / ``consumer_view`` — empty/unhydrated
cache is ``jobs_state=needs_sync``, never silent zero jobs.

No second job ledger. No invented ₪.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any

from vf_paths import OFFICE_ROOT, ROOT  # noqa: E402

BINDINGS = ROOT / "office" / "ledger" / "bindings.json"
LIVE_DIR = OFFICE_ROOT / "office" / "ledger" / "live"
CACHE = LIVE_DIR / "jobs.csv"
TEMPLATE = ROOT / "office" / "ledger" / "templates" / "jobs.csv"
RECEIPT = LIVE_DIR / "sync-receipt.json"
PENDING_PUSH = LIVE_DIR / "pending-push.csv"

# Canonical columns used by vf_office / consumers. Extra Sheet columns are ignored.
JOB_FIELDS = [
    "job_id",
    "opened",
    "channel",
    "client_label",
    "phone",
    "what_asked",
    "sku",
    "qty",
    "size",
    "color",
    "material",
    "file_status",
    "modeling",
    "due",
    "stage",
    "price",
    "notes",
]


class JobsAdapterError(ValueError):
    pass


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_bindings() -> dict[str, Any]:
    if not BINDINGS.is_file():
        raise JobsAdapterError("חסר גיליון — missing office/ledger/bindings.json")
    data = json.loads(BINDINGS.read_text(encoding="utf-8"))
    jobs = (data.get("workbooks") or {}).get("jobs") or {}
    if not jobs.get("spreadsheetId"):
        raise JobsAdapterError("חסר גיליון — bindings.workbooks.jobs.spreadsheetId missing")
    return data


def _rel(path: Path) -> str:
    for base in (OFFICE_ROOT, ROOT):
        try:
            return str(path.relative_to(base))
        except ValueError:
            continue
    return str(path)


def sheet_meta() -> dict[str, str]:
    jobs = (load_bindings().get("workbooks") or {}).get("jobs") or {}
    return {
        "spreadsheetId": jobs["spreadsheetId"],
        "title": jobs.get("title") or "VF HQ · jobs",
        "viewUrl": jobs.get("viewUrl") or "",
        "canonical": "google_sheet",
        "localCache": _rel(CACHE),
    }


def ensure_cache_header() -> Path:
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    if not CACHE.is_file():
        if TEMPLATE.is_file():
            CACHE.write_text(TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            with CACHE.open("w", encoding="utf-8", newline="") as fh:
                csv.DictWriter(fh, fieldnames=JOB_FIELDS).writeheader()
    return CACHE


def parse_jobs_csv(text: str) -> list[dict[str, str]]:
    """Parse Sheet/CSV export into normalized job rows. Preserves Sheet stages/prices as-is."""
    text = text.lstrip("\ufeff")
    if not text.strip():
        return []
    reader = csv.DictReader(StringIO(text))
    if not reader.fieldnames:
        return []
    rows: list[dict[str, str]] = []
    for raw in reader:
        cleaned = {k: (raw.get(k) or "").strip() for k in JOB_FIELDS}
        # tolerate BOM / trailing empty headers from Sheets
        if not cleaned["job_id"]:
            # try alternate keys
            for key, val in (raw or {}).items():
                if key and key.strip().lstrip("\ufeff") == "job_id" and (val or "").strip():
                    cleaned["job_id"] = (val or "").strip()
                    break
        if cleaned["job_id"]:
            rows.append(cleaned)
    return rows


def rows_digest(rows: list[dict[str, str]]) -> str:
    blob = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


def read_cache() -> list[dict[str, str]]:
    if not CACHE.is_file():
        return []
    with CACHE.open(encoding="utf-8-sig", newline="") as fh:
        return parse_jobs_csv(fh.read())


def write_cache(rows: list[dict[str, str]]) -> None:
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    with CACHE.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=JOB_FIELDS)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in JOB_FIELDS})


def load_receipt() -> dict[str, Any]:
    if RECEIPT.is_file():
        return json.loads(RECEIPT.read_text(encoding="utf-8"))
    return {}


def save_receipt(data: dict[str, Any]) -> Path:
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return RECEIPT


def mark_local_dirty(reason: str) -> dict[str, Any]:
    receipt = load_receipt()
    receipt.update(
        {
            "dirty": True,
            "dirtyReason": reason,
            "dirtyAt": now_utc(),
            "localDigest": rows_digest(read_cache()),
            "localRowCount": len(read_cache()),
        }
    )
    save_receipt(receipt)
    return receipt


def export_csv(rows: list[dict[str, str]] | None = None) -> str:
    rows = rows if rows is not None else read_cache()
    buf = StringIO()
    w = csv.DictWriter(buf, fieldnames=JOB_FIELDS)
    w.writeheader()
    for row in rows:
        w.writerow({k: row.get(k, "") for k in JOB_FIELDS})
    return buf.getvalue()


def reconcile(
    local: list[dict[str, str]], remote: list[dict[str, str]]
) -> dict[str, Any]:
    local_map = {r["job_id"]: r for r in local}
    remote_map = {r["job_id"]: r for r in remote}
    only_local = sorted(set(local_map) - set(remote_map))
    only_remote = sorted(set(remote_map) - set(local_map))
    conflicts: list[dict[str, Any]] = []
    for jid in sorted(set(local_map) & set(remote_map)):
        if local_map[jid] != remote_map[jid]:
            conflicts.append(
                {
                    "job_id": jid,
                    "local_stage": local_map[jid].get("stage"),
                    "remote_stage": remote_map[jid].get("stage"),
                    "local_digest": hashlib.sha256(
                        json.dumps(local_map[jid], sort_keys=True).encode()
                    ).hexdigest()[:12],
                    "remote_digest": hashlib.sha256(
                        json.dumps(remote_map[jid], sort_keys=True).encode()
                    ).hexdigest()[:12],
                }
            )
    return {
        "only_local": only_local,
        "only_remote": only_remote,
        "conflicts": conflicts,
        "identical": not only_local and not only_remote and not conflicts,
        "localCount": len(local),
        "remoteCount": len(remote),
        "localDigest": rows_digest(local),
        "remoteDigest": rows_digest(remote),
    }


def apply_remote_rows(
    remote: list[dict[str, str]],
    *,
    source: str,
    force: bool = False,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write remote Sheet rows into local cache with conflict/idempotency handling."""
    meta = sheet_meta()
    ensure_cache_header()
    local = read_cache()
    receipt = load_receipt()
    dirty = bool(receipt.get("dirty"))
    recon = reconcile(local, remote)
    idempotency_key = f"pull|{meta['spreadsheetId']}|{recon['remoteDigest']}"

    if receipt.get("lastPullDigest") == recon["remoteDigest"] and not dirty and not force:
        return {
            "status": "idempotent_skip",
            "reason": "cache already matches remote digest",
            "idempotency_key": idempotency_key,
            "rowCount": len(remote),
            "canonical": meta,
            "reconciliation": recon,
            "receiptPath": _rel(RECEIPT),
        }

    if dirty and not force and not recon["identical"]:
        conflict_receipt = {
            "status": "conflict",
            "at": now_utc(),
            "canonical": meta,
            "source": source,
            "dirty": True,
            "idempotency_key": idempotency_key,
            "reconciliation": recon,
            "resolution": "refuse_overwrite — use --force to take Sheet, or jobs push then pull",
            "evidence": evidence or {},
        }
        save_receipt({**receipt, **conflict_receipt})
        return conflict_receipt

    write_cache(remote)
    out = {
        "status": "pulled",
        "at": now_utc(),
        "canonical": meta,
        "source": source,
        "dirty": False,
        "dirtyReason": None,
        "rowCount": len(remote),
        "idempotency_key": idempotency_key,
        "lastPullDigest": recon["remoteDigest"],
        "reconciliation": recon,
        "evidence": evidence or {},
        "sampleJobIds": [r["job_id"] for r in remote[:5]],
        "rule": "Google Sheet canonical; local CSV is adapter cache only",
    }
    save_receipt(out)
    return out


def pull_from_csv_text(
    text: str, *, source: str = "csv_text", force: bool = False
) -> dict[str, Any]:
    rows = parse_jobs_csv(text)
    if not rows:
        raise JobsAdapterError("Sheet/CSV export had no job rows — refusing empty overwrite")
    return apply_remote_rows(
        rows,
        source=source,
        force=force,
        evidence={"bytes": len(text.encode()), "parser": "vf_jobs_adapter.parse_jobs_csv"},
    )


def pull_from_path(path: Path, *, force: bool = False) -> dict[str, Any]:
    if not path.is_file():
        raise JobsAdapterError(f"missing csv path {path}")
    return pull_from_csv_text(
        path.read_text(encoding="utf-8"),
        source=f"file:{path}",
        force=force,
    )


def _google_creds(scopes: list[str]):
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or os.environ.get(
        "VFMEDIA_DRIVE_CREDENTIALS"
    )
    token = os.environ.get("GOOGLE_TOKEN") or os.environ.get("VFMEDIA_DRIVE_TOKEN")
    if not creds_path and not token:
        return None, "חסר Google auth — GOOGLE_TOKEN / GOOGLE_APPLICATION_CREDENTIALS"
    try:
        from google.oauth2 import service_account  # type: ignore
    except ImportError:
        return None, "חסר google-api-python-client / google-auth"
    if creds_path:
        path = Path(creds_path)
        if not path.is_file():
            return None, f"credentials file missing: {creds_path}"
        return service_account.Credentials.from_service_account_file(str(path), scopes=scopes), None
    from google.oauth2.credentials import Credentials  # type: ignore

    return Credentials(token=token), None


def _drive_service(*, write: bool = False):
    scopes = (
        ["https://www.googleapis.com/auth/drive"]
        if write
        else ["https://www.googleapis.com/auth/drive.readonly"]
    )
    creds, err = _google_creds(scopes)
    if err or creds is None:
        return None, err
    try:
        from googleapiclient.discovery import build  # type: ignore
    except ImportError:
        return None, "חסר google-api-python-client — use jobs pull --from-csv"
    return build("drive", "v3", credentials=creds, cache_discovery=False), None


def _sheets_service():
    """Sheets API for cell write-through. Requires spreadsheets scope + library."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds, err = _google_creds(scopes)
    if err or creds is None:
        return None, err
    try:
        from googleapiclient.discovery import build  # type: ignore
    except ImportError:
        return None, "חסר google-api-python-client (Sheets write)"
    return build("sheets", "v4", credentials=creds, cache_discovery=False), None


def pull_from_google_api(*, force: bool = False) -> dict[str, Any]:
    meta = sheet_meta()
    service, err = _drive_service(write=False)
    if err or service is None:
        return {
            "status": "needs_sheet_sync",
            "at": now_utc(),
            "canonical": meta,
            "reason": err or "no Drive service",
            "hint": (
                "Drive MCP: download_file_content fileId=<spreadsheetId> "
                "exportMimeType=text/csv → python3 scripts/vf_office.py jobs pull --from-csv PATH"
            ),
            "cacheRowCount": len(read_cache()) if CACHE.is_file() else 0,
            "jobs_state": "needs_sync",
        }
    file_id = meta["spreadsheetId"]
    try:
        content = (
            service.files()
            .export(fileId=file_id, mimeType="text/csv")
            .execute()
        )
    except Exception as exc:  # noqa: BLE001
        raise JobsAdapterError(f"Drive export failed: {exc}") from exc
    if isinstance(content, bytes):
        text = content.decode("utf-8")
    else:
        text = str(content)
    return pull_from_csv_text(
        text,
        source="google_drive_api_export",
        force=force,
    )


def pull(*, from_csv: Path | None = None, force: bool = False) -> dict[str, Any]:
    if from_csv is not None:
        return pull_from_path(from_csv, force=force)
    env_path = os.environ.get("VF_JOBS_CSV_EXPORT")
    if env_path:
        return pull_from_path(Path(env_path), force=force)
    return pull_from_google_api(force=force)


def _rows_to_values(rows: list[dict[str, str]]) -> list[list[str]]:
    return [JOB_FIELDS] + [[row.get(k, "") for k in JOB_FIELDS] for row in rows]


def push_write_through() -> dict[str, Any]:
    """Attempt real Sheet write → verify → refresh cache → clear dirty.

    If auth/libs cannot write, leave dirty + pending CSV and return
    ``write_pending_provider`` — never claim canonical Sheet changed.
    """
    meta = sheet_meta()
    rows = read_cache()
    text = export_csv(rows)
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    PENDING_PUSH.write_text(text, encoding="utf-8")
    digest = rows_digest(rows)
    sheets, err = _sheets_service()
    if err or sheets is None:
        receipt = load_receipt()
        out = {
            "status": "write_pending_provider",
            "at": now_utc(),
            "canonical": meta,
            "rowCount": len(rows),
            "digest": digest,
            "dirty": True,
            "pendingPath": _rel(PENDING_PUSH),
            "provider_boundary": err or "Sheets API unavailable on this host",
            "hint": (
                "Cloud/Agent without Sheets write auth cannot close the loop. "
                "Desktop mcp-gsheets or GOOGLE_TOKEN with spreadsheets scope + "
                "google-api-python-client required. Local cache remains dirty."
            ),
            "canonical_changed": False,
        }
        receipt.update(
            {
                "dirty": True,
                "dirtyReason": "write_pending_provider",
                "dirtyAt": now_utc(),
                "lastPushDigest": digest,
                "lastPushAt": now_utc(),
                "pendingPath": out["pendingPath"],
                "lastWriteStatus": out["status"],
            }
        )
        save_receipt(receipt)
        return out

    sheet_title = ((load_bindings().get("workbooks") or {}).get("jobs") or {}).get(
        "sheetName"
    ) or "jobs"
    range_a1 = f"'{sheet_title}'!A1"
    try:
        sheets.spreadsheets().values().update(
            spreadsheetId=meta["spreadsheetId"],
            range=range_a1,
            valueInputOption="RAW",
            body={"values": _rows_to_values(rows)},
        ).execute()
    except Exception as exc:  # noqa: BLE001
        receipt = load_receipt()
        out = {
            "status": "write_pending_provider",
            "at": now_utc(),
            "canonical": meta,
            "rowCount": len(rows),
            "digest": digest,
            "dirty": True,
            "pendingPath": _rel(PENDING_PUSH),
            "provider_boundary": f"Sheets values.update failed: {exc}",
            "canonical_changed": False,
        }
        receipt.update({**out, "lastWriteStatus": out["status"]})
        save_receipt(receipt)
        return out

    # Verify by re-export
    verify = pull_from_google_api(force=True)
    if verify.get("status") not in {"pulled", "idempotent_skip"}:
        return {
            "status": "write_verify_failed",
            "at": now_utc(),
            "canonical": meta,
            "dirty": True,
            "verify": verify,
            "canonical_changed": False,
            "pendingPath": _rel(PENDING_PUSH),
        }
    remote_rows = read_cache()
    if rows_digest(remote_rows) != digest and not all(
        r["job_id"] in {x["job_id"] for x in remote_rows} for r in rows if r.get("job_id")
    ):
        # soft check: every local job_id must appear after write
        missing = [r["job_id"] for r in rows if r["job_id"] not in {x["job_id"] for x in remote_rows}]
        if missing:
            return {
                "status": "write_verify_failed",
                "at": now_utc(),
                "canonical": meta,
                "dirty": True,
                "missing_after_write": missing,
                "canonical_changed": False,
            }
    receipt = {
        "status": "written",
        "at": now_utc(),
        "canonical": meta,
        "rowCount": len(remote_rows),
        "digest": rows_digest(remote_rows),
        "dirty": False,
        "dirtyReason": None,
        "lastPullDigest": rows_digest(remote_rows),
        "lastWriteStatus": "written",
        "canonical_changed": True,
        "verifiedFrom": verify.get("source"),
        "rule": "Sheet write-through verified; cache refreshed from Sheet",
    }
    save_receipt(receipt)
    if PENDING_PUSH.is_file():
        PENDING_PUSH.unlink()
    return receipt


def push(*, write_pending: bool = True, write_through: bool = True) -> dict[str, Any]:
    """Prefer write-through; fall back to pending CSV when provider cannot write."""
    if write_through:
        return push_write_through()
    meta = sheet_meta()
    rows = read_cache()
    text = export_csv(rows)
    if write_pending:
        PENDING_PUSH.write_text(text, encoding="utf-8")
    digest = rows_digest(rows)
    receipt = load_receipt()
    out = {
        "status": "push_ready",
        "at": now_utc(),
        "canonical": meta,
        "rowCount": len(rows),
        "digest": digest,
        "pendingPath": _rel(PENDING_PUSH) if write_pending else None,
        "dirty": True,
        "canonical_changed": False,
        "hint": "write_through=False — pending CSV only; Sheet not updated",
    }
    receipt.update(
        {
            "dirty": True,
            "dirtyReason": "local_push_pending",
            "dirtyAt": now_utc(),
            "lastPushDigest": digest,
            "lastPushAt": now_utc(),
            "pendingPath": out["pendingPath"],
        }
    )
    save_receipt(receipt)
    return out


def cache_hydrated() -> bool:
    receipt = load_receipt()
    if receipt.get("status") in {"pulled", "written", "idempotent_skip"} and receipt.get(
        "lastPullDigest"
    ):
        return CACHE.is_file()
    return False


def ensure_hydrated(*, force: bool = False) -> dict[str, Any]:
    """Hydrate cache from Sheet when possible. Never treat missing cache as zero jobs."""
    meta = sheet_meta()
    if CACHE.is_file() and cache_hydrated() and not force:
        rows = read_cache()
        return {
            "jobs_state": "ready",
            "jobs": rows,
            "rowCount": len(rows),
            "canonical": meta,
            "source": "cache",
        }
    pulled = pull(force=force)
    if pulled.get("status") in {"pulled", "idempotent_skip"}:
        rows = read_cache()
        return {
            "jobs_state": "ready",
            "jobs": rows,
            "rowCount": len(rows),
            "canonical": meta,
            "source": pulled.get("source"),
            "pull": pulled,
        }
    if pulled.get("status") == "conflict":
        return {
            "jobs_state": "conflict",
            "jobs": [],
            "rowCount": 0,
            "canonical": meta,
            "pull": pulled,
            "rule": "dirty local vs Sheet — refuse silent consumer view",
        }
    return {
        "jobs_state": "needs_sync",
        "jobs": [],
        "rowCount": 0,
        "canonical": meta,
        "pull": pulled,
        "rule": "unhydrated cache ≠ zero jobs",
    }


def consumer_view() -> dict[str, Any]:
    view = ensure_hydrated()
    return {
        **status(),
        "jobs_state": view["jobs_state"],
        "readyForConsumers": view["jobs_state"] == "ready",
        "jobs": view.get("jobs") or [],
        "hydration": {k: v for k, v in view.items() if k != "jobs"},
    }


def status() -> dict[str, Any]:
    meta = sheet_meta()
    receipt = load_receipt()
    exists = CACHE.is_file()
    rows = read_cache() if exists else []
    hydrated = cache_hydrated()
    jobs_state = "ready" if hydrated and exists else ("unknown" if not exists else "needs_sync")
    if receipt.get("status") == "conflict":
        jobs_state = "conflict"
    if receipt.get("status") == "needs_sheet_sync":
        jobs_state = "needs_sync"
    return {
        "canonical": meta,
        "cachePath": _rel(CACHE),
        "cacheExists": exists,
        "rowCount": len(rows) if hydrated else None,
        "cacheRowCountUntrusted": len(rows),
        "sampleJobIds": [r["job_id"] for r in rows[:8]] if hydrated else [],
        "dirty": bool(receipt.get("dirty")),
        "lastPullAt": receipt.get("at") if receipt.get("status") in {"pulled", "written"} else receipt.get("lastPullAt"),
        "lastPullDigest": receipt.get("lastPullDigest"),
        "lastStatus": receipt.get("status"),
        "lastWriteStatus": receipt.get("lastWriteStatus"),
        "conflict": receipt.get("status") == "conflict",
        "jobs_state": jobs_state,
        "readyForConsumers": jobs_state == "ready",
        "rule": "Sheet canonical; unhydrated/empty cache is needs_sync — never silent zero jobs",
    }


def get_job(job_id: str) -> dict[str, str] | None:
    for row in read_cache():
        if row["job_id"] == job_id:
            return row
    return None


_JOB_ID_RE = re.compile(r"\bVF-\d{8}-\d{3}\b")


def extract_job_ids(text: str) -> list[str]:
    return _JOB_ID_RE.findall(text or "")
