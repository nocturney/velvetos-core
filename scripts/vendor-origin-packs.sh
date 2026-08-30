#!/usr/bin/env bash
# Vendor Velvet Factory Cursor packs from Origin into packages/<name>/.
# Requires `origin auth login` or CURSOR_API_KEY. Does not send Instagram.
# Preserves HQ overlay: ORIGIN.md, SKILL.md, hq/.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$ROOT/packages/manifest.json"
DEST="$ROOT/packages"
WORKDIR="${TMPDIR:-/tmp}/vf-hq-vendor-$$"

cleanup() { rm -rf "$WORKDIR"; }
trap cleanup EXIT

if ! command -v git >/dev/null 2>&1; then
  echo "need git" >&2
  exit 1
fi

if command -v origin >/dev/null 2>&1; then
  if [[ -z "${CURSOR_API_KEY:-}" ]]; then
    echo "Hint: origin auth login  OR  export CURSOR_API_KEY=..." >&2
  fi
  echo "=== origin repo list (discovery) ==="
  origin repo list --namespace christian-velvet 2>/dev/null || origin repo list 2>/dev/null || true
fi

mkdir -p "$WORKDIR"

vendor_one() {
  local name="$1" slug="$2"
  local dest="$DEST/$name"
  if [[ -z "$slug" ]]; then
    echo "SKIP $name: no Origin slug in manifest"
    return 0
  fi
  echo "=== $name  $slug ==="
  local tmp="$WORKDIR/$name"
  rm -rf "$tmp"
  local cloned=0
  if command -v origin >/dev/null 2>&1; then
    if origin repo clone "$slug" "$tmp"; then
      cloned=1
    fi
  fi
  if [[ "$cloned" -eq 0 ]]; then
    if GIT_TERMINAL_PROMPT=0 git clone --depth 1 "https://origin.cursor.com/${slug}.git" "$tmp"; then
      cloned=1
    fi
  fi
  if [[ "$cloned" -eq 0 ]]; then
    echo "FAIL $name: could not clone $slug" >&2
    return 1
  fi

  local sha=""
  if [[ -d "$tmp/.git" ]]; then
    sha="$(git -C "$tmp" rev-parse HEAD 2>/dev/null || true)"
    rm -rf "$tmp/.git"
  fi

  mkdir -p "$dest"
  local overlay
  overlay="$(mktemp -d)"
  [[ -f "$dest/ORIGIN.md" ]] && cp "$dest/ORIGIN.md" "$overlay/ORIGIN.md"
  [[ -f "$dest/SKILL.md" ]] && cp "$dest/SKILL.md" "$overlay/SKILL.md"
  [[ -d "$dest/hq" ]] && cp -a "$dest/hq" "$overlay/hq"
  find "$dest" -mindepth 1 -maxdepth 1 ! -name ORIGIN.md ! -name SKILL.md ! -name hq -exec rm -rf {} +
  shopt -s dotglob nullglob
  cp -a "$tmp"/* "$dest/" 2>/dev/null || true
  shopt -u dotglob nullglob
  # HQ overlay wins: constitution playbooks stay when Origin trees land.
  [[ -f "$overlay/ORIGIN.md" ]] && cp "$overlay/ORIGIN.md" "$dest/ORIGIN.md"
  [[ -f "$overlay/SKILL.md" ]] && cp "$overlay/SKILL.md" "$dest/SKILL.md"
  if [[ -d "$overlay/hq" ]]; then
    rm -rf "$dest/hq"
    cp -a "$overlay/hq" "$dest/hq"
  fi
  rm -rf "$overlay"
  if [[ -n "$sha" ]]; then
    if ! grep -q "Vendored commit:" "$dest/ORIGIN.md" 2>/dev/null; then
      printf '\nVendored commit: `%s`\n' "$sha" >> "$dest/ORIGIN.md"
    fi
  fi
  echo "OK $name"
}

failed=0
while IFS=$'\t' read -r name slug; do
  [[ -z "$name" ]] && continue
  vendor_one "$name" "$slug" || failed=$((failed + 1))
done < <(python3 - "$MANIFEST" <<'PY'
import json, sys
with open(sys.argv[1]) as f:
    data = json.load(f)
for p in data["packs"]:
    print("%s\t%s" % (p["name"], p.get("originSlug") or ""))
PY
)

echo
if [[ "$failed" -gt 0 ]]; then
  echo "Vendor finished with $failed clone failure(s)."
  exit 1
fi
echo "Vendor finished."
