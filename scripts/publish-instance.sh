#!/usr/bin/env bash
# Publish an instance scaffold to a NEW empty GitHub repo.
# Usage: ./scripts/publish-instance.sh velvet-factory nocturney/velvetos-velvet-factory
# Requires: git, and a GitHub repo that already exists (empty). This Cloud Agent cannot create repos.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ID="${1:-}"
REMOTE_SLUG="${2:-}"
if [[ -z "$ID" || -z "$REMOTE_SLUG" ]]; then
  echo "usage: $0 <instance-id> <owner/repo>" >&2
  echo "example: $0 velvet-factory nocturney/velvetos-velvet-factory" >&2
  exit 1
fi
SRC="$ROOT/instances/$ID"
if [[ ! -d "$SRC" ]]; then
  echo "FAIL missing scaffold $SRC" >&2
  exit 1
fi
if [[ ! -f "$SRC/.cursor/environment.json" ]]; then
  echo "FAIL missing $SRC/.cursor/environment.json (Cloud attach-core on boot)" >&2
  exit 1
fi
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
if command -v rsync >/dev/null 2>&1; then
  rsync -a --exclude '.git' "$SRC/" "$TMP/"
else
  # Cloud images may lack rsync
  cp -a "$SRC"/. "$TMP"/
  rm -rf "$TMP/.git" 2>/dev/null || true
fi
cd "$TMP"
git init -b main
git add -A
git -c user.email="$(git -C "$ROOT" config user.email)" -c user.name="$(git -C "$ROOT" config user.name)" commit -m "VelvetOS instance scaffold: $ID

Frontend office for one business. Attach VelvetOS Core with ./scripts/attach-core.sh."
git remote add origin "https://github.com/${REMOTE_SLUG}.git"
echo "Ready to push from: $TMP"
echo "  git push -u origin main"
echo "(Script will push now if PUSH=1)"
if [[ "${PUSH:-0}" == "1" ]]; then
  git push -u origin main
  echo "OK published $REMOTE_SLUG"
fi
# also write a stamp in core for humans
mkdir -p "$ROOT/packages/vfharness/state"
python3 - <<PY
import json
from datetime import date
from pathlib import Path
Path("$ROOT/packages/vfharness/state/publish-instance-$ID.json").write_text(json.dumps({
  "task_id": f"publish-instance-$ID",
  "status": "ready",
  "pack": "velvetos",
  "remote": "$REMOTE_SLUG",
  "scaffold": "instances/$ID",
  "last_updated": str(date.today()),
  "completed_steps": ["scaffold built", "publish script staged"],
  "next_step": "Owner creates empty GitHub repo then PUSH=1 ./scripts/publish-instance.sh $ID $REMOTE_SLUG",
  "artifacts": ["instances/$ID"],
  "unresolved": ["GitHub createRepository not allowed from this Cloud Agent token"]
}, indent=2) + "\n")
print("stamp written")
PY
