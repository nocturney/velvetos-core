#!/usr/bin/env bash
# Publish an instance scaffold to a GitHub repo (empty or existing main).
# Usage: ./scripts/publish-instance.sh velvet-factory nocturney/velvetos-velvet-factory
# Requires: git, and a GitHub repo that already exists. This Cloud Agent cannot create repos.
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

overlay_scaffold() {
  local dest="$1"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --exclude '.git' "$SRC/" "$dest/"
  else
    cp -a "$SRC"/. "$dest"/
  fi
}

write_stamp() {
  local status="$1"
  local next_step="$2"
  local unresolved_json="$3"
  mkdir -p "$ROOT/packages/vfharness/state"
  local py=""
  if command -v python3 >/dev/null 2>&1; then
    py=python3
  elif command -v python >/dev/null 2>&1; then
    py=python
  fi
  if [[ -z "$py" ]]; then
    echo "WARN python not found — skipping packages/vfharness/state/publish-instance-$ID.json" >&2
    return 0
  fi
  STATUS="$status" NEXT_STEP="$next_step" UNRESOLVED_JSON="$unresolved_json" \
    ROOT="$ROOT" ID="$ID" REMOTE_SLUG="$REMOTE_SLUG" REMOTE_URL="$REMOTE_URL" \
    "$py" - <<'PY'
import json
import os
from datetime import date
from pathlib import Path

status = os.environ["STATUS"]
unresolved = json.loads(os.environ["UNRESOLVED_JSON"])
Path(f"{os.environ['ROOT']}/packages/vfharness/state/publish-instance-{os.environ['ID']}.json").write_text(
    json.dumps(
        {
            "task_id": f"publish-instance-{os.environ['ID']}",
            "status": status,
            "pack": "velvetos",
            "remote": os.environ["REMOTE_SLUG"],
            "remote_url": os.environ["REMOTE_URL"],
            "scaffold": f"instances/{os.environ['ID']}",
            "last_updated": str(date.today()),
            "completed_steps": ["scaffold built", "publish script staged"],
            "next_step": os.environ["NEXT_STEP"],
            "artifacts": [f"instances/{os.environ['ID']}"],
            "unresolved": unresolved,
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
print("stamp written")
PY
}

REMOTE_URL="${REMOTE_URL:-https://github.com/${REMOTE_SLUG}.git}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
STATUS="ready"
REMOTE_HAS_MAIN=0

if ! git ls-remote --exit-code "$REMOTE_URL" HEAD >/dev/null 2>&1; then
  echo "FAIL cannot reach $REMOTE_URL (not found or token lacks access)" >&2
  echo "If the repo exists: grant this GitHub App/integration access to the repo, or run locally:" >&2
  echo "  PUSH=1 ./scripts/publish-instance.sh $ID $REMOTE_SLUG" >&2
  write_stamp "blocked" \
    "Grant GitHub App access to remote repo OR run locally: PUSH=1 ./scripts/publish-instance.sh $ID $REMOTE_SLUG" \
    '["remote not reachable from this token"]'
  exit 2
fi

if git ls-remote --exit-code "$REMOTE_URL" refs/heads/main >/dev/null 2>&1; then
  REMOTE_HAS_MAIN=1
fi

if [[ "$REMOTE_HAS_MAIN" == "1" ]]; then
  echo "Remote has main — clone + overlay scaffold (keeps remote-only files like docs/)"
  git clone "$REMOTE_URL" "$TMP"
  cd "$TMP"
  overlay_scaffold "$TMP"
else
  echo "Remote empty — init from scaffold"
  overlay_scaffold "$TMP"
  cd "$TMP"
  rm -rf "$TMP/.git" 2>/dev/null || true
  git init -b main
fi

git add -A
if git diff --staged --quiet; then
  echo "OK scaffold already matches remote — nothing to commit"
  STATUS="synced"
else
  git -c user.email="$(git -C "$ROOT" config user.email 2>/dev/null || echo cursoragent@cursor.com)" \
      -c user.name="$(git -C "$ROOT" config user.name 2>/dev/null || echo 'Cursor Agent')" \
      commit -m "VelvetOS instance scaffold: $ID

Sync from Core instances/$ID. Attach VelvetOS Core with ./scripts/attach-core.sh."
fi

echo "Remote: $REMOTE_URL"
echo "Working tree: $TMP"
echo "(Script will push now if PUSH=1)"

if [[ "${PUSH:-0}" == "1" ]]; then
  PUSH_ERR="$(mktemp)"
  if git push -u origin main 2>"$PUSH_ERR"; then
    STATUS="published"
    echo "OK published $REMOTE_SLUG"
  else
    ERR="$(cat "$PUSH_ERR")"
    if grep -qiE 'authentication failed|403|denied|401|bad credentials' <<<"$ERR"; then
      STATUS="push_denied"
      echo "FAIL push denied — check GitHub auth / App write on $REMOTE_SLUG" >&2
      write_stamp "$STATUS" \
        "Fix GitHub auth, then: PUSH=1 ./scripts/publish-instance.sh $ID $REMOTE_SLUG" \
        '["git push auth denied — owner PAT or GitHub App write"]'
    elif grep -qiE 'rejected|non-fast-forward|fetch first' <<<"$ERR"; then
      STATUS="push_rejected"
      echo "FAIL push rejected — remote moved during publish; re-run the script" >&2
      write_stamp "$STATUS" \
        "Re-run: PUSH=1 ./scripts/publish-instance.sh $ID $REMOTE_SLUG" \
        '["non-fast-forward — re-run publish (script now clones before push)"]'
    else
      STATUS="push_failed"
      echo "FAIL push failed:" >&2
      cat "$PUSH_ERR" >&2
      write_stamp "$STATUS" "Check git push output; re-run PUSH=1 ./scripts/publish-instance.sh $ID $REMOTE_SLUG" \
        '["git push failed — see script output"]'
    fi
    rm -f "$PUSH_ERR"
    exit 3
  fi
  rm -f "$PUSH_ERR"
fi

case "$STATUS" in
  published)
    write_stamp "$STATUS" "Instance published — open remote repo in Cursor; run ./scripts/attach-core.sh" "[]"
    ;;
  synced)
    write_stamp "$STATUS" "Scaffold matches remote — edit instances/$ID then re-run with PUSH=1 if needed" "[]"
    ;;
  ready)
    write_stamp "$STATUS" "PUSH=1 ./scripts/publish-instance.sh $ID $REMOTE_SLUG" "[]"
    ;;
esac
