#!/usr/bin/env bash
# Compare instances/velvet-factory scaffold to the published GitHub repo.
# Usage: ./scripts/sync-instance-scaffold.sh [owner/repo]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ID="${INSTANCE_ID:-velvet-factory}"
REMOTE_SLUG="${1:-nocturney/velvetos-velvet-factory}"
SRC="$ROOT/instances/$ID"
TMP="${TMPDIR:-/tmp}/vf-instance-diff-$$"

cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

if [[ ! -d "$SRC" ]]; then
  echo "FAIL missing $SRC" >&2
  exit 1
fi

echo "=== sync-instance-scaffold ==="
echo "scaffold: $SRC"
echo "remote:   https://github.com/$REMOTE_SLUG.git"
echo

if ! git ls-remote --exit-code "https://github.com/${REMOTE_SLUG}.git" HEAD >/dev/null 2>&1; then
  echo "FAIL cannot read remote (not found or token lacks access)" >&2
  exit 2
fi

rm -rf "$TMP"
git clone --depth 1 "https://github.com/${REMOTE_SLUG}.git" "$TMP" >/dev/null

echo "--- files that differ (scaffold vs remote main) ---"
diff -rq "$SRC" "$TMP" 2>/dev/null | grep -v 'Only in '"$TMP" || true
echo
echo "--- only on remote (not in scaffold) ---"
diff -rq "$SRC" "$TMP" 2>/dev/null | grep "Only in $TMP" || echo "(none)"
echo
echo "To publish scaffold → remote:"
echo "  PUSH=1 ./scripts/publish-instance.sh $ID $REMOTE_SLUG"
echo "(Requires write access; see docs/OWNER-ACTIONS-he.md)"
