"""Drive adapters for media intake. No invented file ids."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Protocol


INBOX_ID = "1IG4zNTOuGgvPyhEbKQEKwjRjFD6BuUDJ"
SOURCE_ID = "1M0WY3iIKYOlqMPcBx5xctx8sr8xidnY6"
FOLDER_MIME = "application/vnd.google-apps.folder"


@dataclass
class DriveFile:
    id: str
    name: str
    mimeType: str
    createdTime: str = ""
    size: int = 0
    webViewLink: str = ""
    parents: list[str] = field(default_factory=list)
    localPath: str | None = None


@dataclass
class ListPage:
    files: list[DriveFile]
    nextPageToken: str | None = None


class DriveProvider(Protocol):
    name: str

    def list_inbox_page(self, page_token: str | None, page_size: int) -> ListPage: ...

    def download_bytes(self, file: DriveFile, max_bytes: int = 2_000_000) -> bytes: ...

    def move_to_source(self, file_id: str) -> None: ...


class AuthMissingError(RuntimeError):
    """Drive credentials unavailable for this runtime."""


class ListingProvider:
    """Read a pre-exported inbox listing (MCP / CI artifact). Optional localPath for verify."""

    name = "listing"

    def __init__(self, listing_path: Path, *, move_mode: str = "pending", pending_path: Path | None = None):
        self.listing_path = listing_path
        self.move_mode = move_mode  # pending | memory
        self.pending_path = pending_path
        self._moved: set[str] = set()
        raw = json.loads(listing_path.read_text(encoding="utf-8"))
        self._folder_id = raw.get("folderId") or INBOX_ID
        self._pages = raw.get("pages")
        if self._pages is None:
            self._pages = [
                {
                    "pageToken": raw.get("pageToken"),
                    "nextPageToken": raw.get("nextPageToken"),
                    "files": raw.get("files") or [],
                }
            ]

    def list_inbox_page(self, page_token: str | None, page_size: int) -> ListPage:
        page = None
        for row in self._pages:
            tok = row.get("pageToken")
            if (tok or None) == (page_token or None):
                page = row
                break
        if page is None:
            # First page fallback
            page = self._pages[0] if not page_token else {"files": [], "nextPageToken": None}
        files: list[DriveFile] = []
        for item in (page.get("files") or [])[:page_size]:
            if item.get("mimeType") == FOLDER_MIME:
                continue
            size = item.get("size") or 0
            if isinstance(size, str):
                size = int(size) if size.isdigit() else 0
            files.append(
                DriveFile(
                    id=str(item["id"]),
                    name=str(item.get("name") or item["id"]),
                    mimeType=str(item.get("mimeType") or "application/octet-stream"),
                    createdTime=str(item.get("createdTime") or item.get("uploadedAt") or ""),
                    size=int(size),
                    webViewLink=str(
                        item.get("webViewLink")
                        or f"https://drive.google.com/file/d/{item['id']}/view"
                    ),
                    parents=list(item.get("parents") or [self._folder_id]),
                    localPath=item.get("localPath"),
                )
            )
        return ListPage(files=files, nextPageToken=page.get("nextPageToken"))

    def download_bytes(self, file: DriveFile, max_bytes: int = 2_000_000) -> bytes:
        if file.localPath:
            path = Path(file.localPath)
            if not path.is_file():
                # Allow repo-relative
                alt = Path(__file__).resolve().parents[3] / file.localPath
                path = alt if alt.is_file() else path
            data = path.read_bytes()[:max_bytes]
            if not data:
                raise RuntimeError(f"empty local file for {file.id}")
            return data
        # Size-only verify when listing declares size > 0
        if file.size > 0:
            return b"\0" * min(file.size, 64)
        raise RuntimeError(f"listing file {file.id} has no localPath/size for download verify")

    def move_to_source(self, file_id: str) -> None:
        if self.move_mode == "memory":
            self._moved.add(file_id)
            return
        if self.move_mode != "pending":
            raise RuntimeError(f"unknown move_mode {self.move_mode}")
        if not self.pending_path:
            raise RuntimeError("pending_path required for move_mode=pending")
        self.pending_path.parent.mkdir(parents=True, exist_ok=True)
        pending = {"actions": []}
        if self.pending_path.is_file():
            try:
                pending = json.loads(self.pending_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pending = {"actions": []}
        actions = pending.setdefault("actions", [])
        if not any(a.get("fileId") == file_id and a.get("status") == "pending" for a in actions):
            actions.append(
                {
                    "op": "move",
                    "fileId": file_id,
                    "fromFolderId": INBOX_ID,
                    "toFolderId": SOURCE_ID,
                    "status": "pending",
                }
            )
        pending["updatedAt"] = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.pending_path.write_text(
            json.dumps(pending, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )


class MemoryFixtureProvider(ListingProvider):
    """Fixture listing with in-memory moves — for selftest / CI without Drive."""

    name = "fixture"

    def __init__(self, listing_path: Path):
        super().__init__(listing_path, move_mode="memory", pending_path=None)


class GoogleApiProvider:
    """Google Drive API v3 when credentials exist. Exit AUTH when missing."""

    name = "google"

    def __init__(self):
        creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or os.environ.get(
            "VFMEDIA_DRIVE_CREDENTIALS"
        )
        token = os.environ.get("GOOGLE_TOKEN") or os.environ.get("VFMEDIA_DRIVE_TOKEN")
        if not creds_path and not token:
            raise AuthMissingError(
                "חסר Drive auth לסביבת רקע: אין GOOGLE_APPLICATION_CREDENTIALS / "
                "VFMEDIA_DRIVE_CREDENTIALS / GOOGLE_TOKEN / VFMEDIA_DRIVE_TOKEN"
            )
        try:
            from google.oauth2 import service_account  # type: ignore
            from googleapiclient.discovery import build  # type: ignore
        except ImportError as exc:
            raise AuthMissingError(
                "חסר google-api-python-client / google-auth בסביבת הריצה"
            ) from exc

        scopes = ["https://www.googleapis.com/auth/drive"]
        if creds_path:
            path = Path(creds_path)
            if not path.is_file():
                raise AuthMissingError(f"credentials file missing: {creds_path}")
            creds = service_account.Credentials.from_service_account_file(str(path), scopes=scopes)
        else:
            # Token string as OAuth access token — limited; for workflow secrets
            from google.oauth2.credentials import Credentials  # type: ignore

            creds = Credentials(token=token)
        self._service = build("drive", "v3", credentials=creds, cache_discovery=False)

    def list_inbox_page(self, page_token: str | None, page_size: int) -> ListPage:
        q = f"'{INBOX_ID}' in parents and trashed=false"
        resp = (
            self._service.files()
            .list(
                q=q,
                pageSize=page_size,
                pageToken=page_token or None,
                fields="nextPageToken, files(id,name,mimeType,createdTime,size,webViewLink,parents)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        files: list[DriveFile] = []
        for item in resp.get("files") or []:
            if item.get("mimeType") == FOLDER_MIME:
                continue
            size = item.get("size") or 0
            if isinstance(size, str):
                size = int(size) if size.isdigit() else 0
            files.append(
                DriveFile(
                    id=item["id"],
                    name=item.get("name") or item["id"],
                    mimeType=item.get("mimeType") or "application/octet-stream",
                    createdTime=item.get("createdTime") or "",
                    size=int(size),
                    webViewLink=item.get("webViewLink")
                    or f"https://drive.google.com/file/d/{item['id']}/view",
                    parents=list(item.get("parents") or []),
                )
            )
        return ListPage(files=files, nextPageToken=resp.get("nextPageToken"))

    def download_bytes(self, file: DriveFile, max_bytes: int = 2_000_000) -> bytes:
        from io import BytesIO

        from googleapiclient.http import MediaIoBaseDownload  # type: ignore

        request = self._service.files().get_media(fileId=file.id, supportsAllDrives=True)
        buf = BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
            if buf.tell() > max_bytes:
                break
        data = buf.getvalue()[:max_bytes]
        if not data and file.size == 0:
            # Empty file still counts as accessible if metadata exists
            meta = (
                self._service.files()
                .get(fileId=file.id, fields="id,size", supportsAllDrives=True)
                .execute()
            )
            if not meta.get("id"):
                raise RuntimeError(f"download verify failed for {file.id}")
            return b""
        if not data and file.size > 0:
            raise RuntimeError(f"download returned empty for sized file {file.id}")
        return data

    def move_to_source(self, file_id: str) -> None:
        meta = (
            self._service.files()
            .get(fileId=file_id, fields="parents", supportsAllDrives=True)
            .execute()
        )
        prev = ",".join(meta.get("parents") or [])
        (
            self._service.files()
            .update(
                fileId=file_id,
                addParents=SOURCE_ID,
                removeParents=prev,
                fields="id,parents",
                supportsAllDrives=True,
            )
            .execute()
        )


def iter_inbox(provider: DriveProvider, *, page_size: int, start_token: str | None) -> Iterator[tuple[DriveFile, str | None]]:
    """Yield (file, next_token_after_this_page). Paginate until exhausted."""
    token = start_token
    while True:
        page = provider.list_inbox_page(token, page_size)
        for f in page.files:
            yield f, page.nextPageToken
        if not page.nextPageToken:
            break
        token = page.nextPageToken
