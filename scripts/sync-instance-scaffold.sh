#!/usr/bin/env bash
# CHECK-ONLY: compare instances/velvet-factory scaffold to the published repo.
# Never modifies either side and never pushes (read: ls-remote + shallow clone
# into a temp dir + diff). Publishing is a separate owner step (see hint below).
#
# Usage: ./scripts/sync-instance-scaffold.sh [--check] [--skip-if-inaccessible] [owner/repo]
#   --check                 exit 3 when drift is found (default: report only, exit 0)
#   --skip-if-inaccessible  exit 0 with SKIP when the remote cannot be read
#                           (nocturney/velvetos-velvet-factory is PRIVATE; CI's
#                           GITHUB_TOKEN cannot read it)
set -euo pipefail
export GIT_TERMINAL_PROMPT=0

CHECK=0
SKIP_INACCESSIBLE=0
REMOTE_SLUG="nocturney/velvetos-velvet-factory"
for arg in "$@"; do
  case "$arg" in
    --check) CHECK=1 ;;
    --skip-if-inaccessible) SKIP_INACCESSIBLE=1 ;;
    -*) echo "FAIL unknown flag $arg" >&2; exit 64 ;;
    *) REMOTE_SLUG="$arg" ;;
  esac
done

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ID="${INSTANCE_ID:-velvet-factory}"
SRC="$ROOT/instances/$ID"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/vf-instance-diff-XXXXXX")"

cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

if [[ ! -d "$SRC" ]]; then
  echo "FAIL missing $SRC" >&2
  exit 1
fi

echo "=== sync-instance-scaffold (check-only) ==="
echo "scaffold: $SRC"
echo "remote:   https://github.com/$REMOTE_SLUG.git"
echo

if ! timeout 60 git ls-remote --exit-code "https://github.com/${REMOTE_SLUG}.git" HEAD >/dev/null 2>&1; then
  if [[ "$SKIP_INACCESSIBLE" == 1 ]]; then
    echo "SKIP cannot read $REMOTE_SLUG (private or no access) — drift not checked"
    exit 0
  fi
  echo "FAIL cannot read remote (not found or token lacks access)" >&2
  exit 2
fi

timeout 120 git clone -q --depth 1 "https://github.com/${REMOTE_SLUG}.git" "$TMP/remote"
REMOTE_HEAD="$(git -C "$TMP/remote" rev-parse --short HEAD)"

set +o pipefail
DIFF="$(diff -rq -x .git "$SRC" "$TMP/remote" 2>/dev/null || true)"
set -o pipefail
DIFFER="$(printf '%s\n' "$DIFF" | grep '^Files ' || true)"
SCAFFOLD_ONLY="$(printf '%s\n' "$DIFF" | grep "^Only in $SRC" || true)"
REMOTE_ONLY_ALL="$(printf '%s\n' "$DIFF" | grep "^Only in $TMP/remote" || true)"
# Instance-only paths that legitimately live only in the published frontend repo
# (its own CI, desk MCP config, access-gap pointer, its own Control Center app).
# Reported, never counted as drift.
INSTANCE_ONLY_ALLOWED=(".github" "docs" ".cursor/mcp.json" "control-center")
is_allowed_remote_only() {
  local line="$1" rel dir name a
  dir="${line#Only in $TMP/remote}"; dir="${dir%%: *}"; dir="${dir#/}"
  name="${line##*: }"
  rel="${dir:+$dir/}$name"
  for a in "${INSTANCE_ONLY_ALLOWED[@]}"; do [[ "$rel" == "$a" ]] && return 0; done
  return 1
}
REMOTE_ONLY=""; INSTANCE_ONLY=""
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  if is_allowed_remote_only "$line"; then INSTANCE_ONLY+="$line"$'\n'; else REMOTE_ONLY+="$line"$'\n'; fi
done <<< "$REMOTE_ONLY_ALL"
REMOTE_ONLY="${REMOTE_ONLY%$'\n'}"; INSTANCE_ONLY="${INSTANCE_ONLY%$'\n'}"
count() { if [[ -z "$1" ]]; then echo 0; else printf '%s\n' "$1" | wc -l | tr -d ' '; fi; }
N_DIFF="$(count "$DIFFER")"; N_SRC="$(count "$SCAFFOLD_ONLY")"; N_REM="$(count "$REMOTE_ONLY")"

show() { if [[ -z "$1" ]]; then echo "(none)"; else printf '%s\n' "$1" | sed -e "s#$SRC/*#scaffold:/#g" -e "s#$TMP/remote/*#remote:/#g"; fi; }
echo "--- files that differ (scaffold vs remote $REMOTE_HEAD) ---"; show "$DIFFER"; echo
echo "--- only in scaffold ---"; show "$SCAFFOLD_ONLY"; echo
echo "--- only on remote ---"; show "$REMOTE_ONLY"; echo
echo "--- instance-only on remote (allowed, not drift) ---"; show "$INSTANCE_ONLY"; echo

if [[ "$N_DIFF$N_SRC$N_REM" == "000" ]]; then
  echo "OK scaffold in sync with $REMOTE_SLUG@$REMOTE_HEAD"
  exit 0
fi
echo "DRIFT differ=$N_DIFF scaffold_only=$N_SRC remote_only=$N_REM remote=$REMOTE_SLUG@$REMOTE_HEAD"
if [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
  echo "::warning::instance scaffold drift differ=$N_DIFF scaffold_only=$N_SRC remote_only=$N_REM"
fi
echo "Publishing is NOT done by this script. Owner step, after review:"
echo "  PUSH=1 ./scripts/publish-instance.sh $ID $REMOTE_SLUG   (write access; docs/OWNER-ACTIONS-he.md)"
[[ "$CHECK" == 1 ]] && exit 3
exit 0
