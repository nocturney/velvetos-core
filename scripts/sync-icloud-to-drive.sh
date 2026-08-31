#!/usr/bin/env bash
# Mirror Velvet Factory iCloud folder → Google Drive (Mac only).
# Cloud Agent reads the Drive copy via Google-drive MCP.
# Docs: packages/vfmcp/ICLOUD-DRIVE-SYNC.md

set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "sync-icloud-to-drive.sh: macOS only (iCloud + Google Drive for desktop)." >&2
  exit 1
fi

ICLOUD_ROOT="${VF_ICLOUD_ROOT:-$HOME/Library/Mobile Documents/com~apple~CloudDocs/Velvet Factory}"
GDRIVE_MIRROR="${VF_GDRIVE_MIRROR:-$HOME/Library/CloudStorage/GoogleDrive-nocturney@gmail.com/My Drive/Velvet Factory/iCloud mirror}"
LOG="${VF_ICLOUD_SYNC_LOG:-$HOME/Library/Logs/velvet-factory-icloud-sync.log}"
RSYNC_DELETE="${VF_ICLOUD_RSYNC_DELETE:-0}"

log() {
  printf '%s %s\n' "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$*" | tee -a "$LOG"
}

if [[ ! -d "$ICLOUD_ROOT" ]]; then
  log "ERROR: iCloud root missing: $ICLOUD_ROOT"
  exit 1
fi

if [[ ! -d "$(dirname "$GDRIVE_MIRROR")" ]]; then
  log "ERROR: Google Drive parent missing. Install Drive for desktop and set VF_GDRIVE_MIRROR."
  log "  tried: $GDRIVE_MIRROR"
  exit 1
fi

mkdir -p "$GDRIVE_MIRROR"

if command -v brctl >/dev/null 2>&1; then
  log "Downloading iCloud placeholders under $ICLOUD_ROOT"
  brctl download "$ICLOUD_ROOT" 2>/dev/null || true
else
  log "WARN: brctl not found — skipping placeholder download"
fi

RSYNC_OPTS=(-a -v --human-readable)
if [[ "$RSYNC_DELETE" == "1" ]]; then
  RSYNC_OPTS+=(--delete)
  log "WARN: rsync --delete enabled (VF_ICLOUD_RSYNC_DELETE=1)"
fi

log "rsync: $ICLOUD_ROOT/ -> $GDRIVE_MIRROR/"
rsync "${RSYNC_OPTS[@]}" "$ICLOUD_ROOT/" "$GDRIVE_MIRROR/" 2>&1 | tee -a "$LOG"
log "done"
