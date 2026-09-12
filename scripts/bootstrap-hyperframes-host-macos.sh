#!/usr/bin/env bash
set -euo pipefail

HYPERFRAMES_VERSION="0.8.34"
NODE_VERSION_PIN="22.22.0"
FFMPEG_STATIC_PACKAGE="ffmpeg-ffprobe-static@6.1.2-rc.1"
HOST_ID="sderot-mac"
START_WORKER=0

if [[ "${1:-}" == "--start-worker" ]]; then
  START_WORKER=1
elif [[ $# -gt 0 ]]; then
  echo "Usage: $0 [--start-worker]" >&2
  exit 2
fi

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "FAIL this bootstrap is for the canonical Mac-Office host only" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

export HYPERFRAMES_NO_UPDATE_CHECK=1
export HYPERFRAMES_NO_AUTO_INSTALL=1
export NPM_CONFIG_PREFIX="$HOME/.local"
export PATH="$HOME/.local/bin:$PATH"

say() { printf '%s\n' "$*"; }
fail() { say "FAIL $*" >&2; exit 1; }

version_major() {
  printf '%s' "$1" | sed -E 's/^v?([0-9]+).*/\1/'
}

persist_user_path() {
  mkdir -p "$HOME/.local/bin"
  local line='export PATH="$HOME/.local/bin:$PATH"'
  local profile
  for profile in "$HOME/.zprofile" "$HOME/.zshrc"; do
    touch "$profile"
    if ! grep -Fqx "$line" "$profile" 2>/dev/null; then
      printf '\n%s\n' "$line" >> "$profile"
      say "Persisted user-local PATH in $profile"
    fi
  done
}

install_user_node() {
  command -v curl >/dev/null 2>&1 || fail "curl is required for user-local Node installation"
  command -v tar >/dev/null 2>&1 || fail "tar is required for user-local Node installation"
  command -v shasum >/dev/null 2>&1 || fail "shasum is required to verify the Node download"

  local machine arch artifact base toolchain node_dir tmp sums
  machine="$(uname -m)"
  case "$machine" in
    arm64) arch="arm64" ;;
    x86_64) arch="x64" ;;
    *) fail "unsupported macOS architecture: $machine" ;;
  esac

  artifact="node-v${NODE_VERSION_PIN}-darwin-${arch}.tar.gz"
  base="https://nodejs.org/dist/v${NODE_VERSION_PIN}"
  toolchain="$HOME/.velvetos/toolchain"
  node_dir="$toolchain/node-v${NODE_VERSION_PIN}-darwin-${arch}"
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/velvet-node.XXXXXX")"
  trap 'rm -rf "${tmp:-}"' RETURN

  say "Installing Node v${NODE_VERSION_PIN} user-locally (no sudo)..."
  curl -fL "$base/$artifact" -o "$tmp/$artifact"
  curl -fL "$base/SHASUMS256.txt" -o "$tmp/SHASUMS256.txt"
  sums="$(grep "  $artifact$" "$tmp/SHASUMS256.txt" || true)"
  [[ -n "$sums" ]] || fail "Node checksum entry not found for $artifact"
  (cd "$tmp" && printf '%s\n' "$sums" | shasum -a 256 -c -)

  mkdir -p "$toolchain" "$HOME/.local/bin"
  rm -rf "$node_dir"
  tar -xzf "$tmp/$artifact" -C "$toolchain"
  [[ -x "$node_dir/bin/node" ]] || fail "Node binary missing after extraction"

  ln -sf "$node_dir/bin/node" "$HOME/.local/bin/node"
  ln -sf "$node_dir/bin/npm" "$HOME/.local/bin/npm"
  ln -sf "$node_dir/bin/npx" "$HOME/.local/bin/npx"
  if [[ -x "$node_dir/bin/corepack" ]]; then
    ln -sf "$node_dir/bin/corepack" "$HOME/.local/bin/corepack"
  fi
  export PATH="$HOME/.local/bin:$node_dir/bin:$PATH"
}

install_user_ffmpeg() {
  local toolchain package_root ffmpeg_bin ffprobe_bin
  toolchain="$HOME/.velvetos/toolchain"
  package_root="$toolchain/ffmpeg-ffprobe-static"
  mkdir -p "$package_root" "$HOME/.local/bin"

  say "Installing FFmpeg + ffprobe user-locally (no sudo)..."
  npm install --prefix "$package_root" --no-audit --no-fund "$FFMPEG_STATIC_PACKAGE"
  ffmpeg_bin="$package_root/node_modules/ffmpeg-ffprobe-static/ffmpeg"
  ffprobe_bin="$package_root/node_modules/ffmpeg-ffprobe-static/ffprobe"
  [[ -x "$ffmpeg_bin" ]] || fail "user-local ffmpeg binary missing after npm install"
  [[ -x "$ffprobe_bin" ]] || fail "user-local ffprobe binary missing after npm install"
  ln -sf "$ffmpeg_bin" "$HOME/.local/bin/ffmpeg"
  ln -sf "$ffprobe_bin" "$HOME/.local/bin/ffprobe"
  export PATH="$HOME/.local/bin:$PATH"
}

persist_user_path

NODE_VERSION="$(node --version 2>/dev/null || true)"
NODE_MAJOR="$(version_major "$NODE_VERSION")"
if [[ -z "$NODE_VERSION" || -z "$NODE_MAJOR" || "$NODE_MAJOR" -lt 22 ]]; then
  install_user_node
fi

command -v node >/dev/null 2>&1 || fail "node missing after bootstrap"
command -v npm >/dev/null 2>&1 || fail "npm missing after bootstrap"
NODE_VERSION="$(node --version)"
NODE_MAJOR="$(version_major "$NODE_VERSION")"
[[ "$NODE_MAJOR" -ge 22 ]] || fail "Node >=22 required; found $NODE_VERSION"

if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
  install_user_ffmpeg
fi

command -v ffmpeg >/dev/null 2>&1 || fail "ffmpeg missing after bootstrap"
command -v ffprobe >/dev/null 2>&1 || fail "ffprobe missing after bootstrap"

CURRENT_HF="$(hyperframes --version 2>/dev/null | head -n 1 | tr -d '[:space:]' || true)"
if [[ "$CURRENT_HF" != "$HYPERFRAMES_VERSION" && "$CURRENT_HF" != "v$HYPERFRAMES_VERSION" ]]; then
  say "Installing pinned HyperFrames $HYPERFRAMES_VERSION user-locally..."
  npm install -g --no-audit --no-fund "hyperframes@$HYPERFRAMES_VERSION"
fi

command -v hyperframes >/dev/null 2>&1 || fail "hyperframes CLI not found after install"
CURRENT_HF="$(hyperframes --version | head -n 1 | tr -d '[:space:]')"
if [[ "$CURRENT_HF" != "$HYPERFRAMES_VERSION" && "$CURRENT_HF" != "v$HYPERFRAMES_VERSION" ]]; then
  fail "HyperFrames version mismatch after install: expected $HYPERFRAMES_VERSION, got $CURRENT_HF"
fi

say "Ensuring HyperFrames browser runtime..."
hyperframes browser ensure

say "Running VelvetOS host doctor..."
python3 scripts/vf_hyperframes.py doctor

SMOKE_ROOT="${TMPDIR:-/tmp}/velvet-hyperframes-host-smoke"
rm -rf "$SMOKE_ROOT"
mkdir -p "$SMOKE_ROOT/renders"

cat > "$SMOKE_ROOT/index.html" <<'HTML'
<!doctype html>
<html lang="he">
<head>
  <meta charset="utf-8" />
  <style>
    html, body { margin: 0; width: 100%; height: 100%; overflow: hidden; background: #000; }
    .frame { width: 1080px; height: 1920px; display: flex; align-items: center; justify-content: center; background: #000; color: #fff; font-family: system-ui, sans-serif; }
    .label { font-size: 76px; font-weight: 700; direction: rtl; text-align: center; }
  </style>
</head>
<body>
  <div class="frame" data-composition-id="main" data-width="1080" data-height="1920" data-start="0" data-duration="2" data-no-timeline>
    <div class="label" dir="rtl">בדיקת מנוע וידאו</div>
  </div>
</body>
</html>
HTML

cat > "$SMOKE_ROOT/request.json" <<JSON
{
  "jobId": "host-smoke",
  "backend": "hyperframes",
  "projectDir": "$SMOKE_ROOT",
  "composition": "index.html",
  "stage": "review",
  "target": "review",
  "format": "mp4",
  "resolution": "portrait",
  "fps": 30,
  "quality": "standard",
  "output": "renders/host-smoke.mp4",
  "audioRequired": false,
  "strictAll": false
}
JSON

say "Planning smoke render..."
python3 scripts/vf_hyperframes.py plan "$SMOKE_ROOT/request.json"
say "Rendering smoke video..."
python3 scripts/vf_hyperframes.py run "$SMOKE_ROOT/request.json"

RECEIPT="$SMOKE_ROOT/renders/host-smoke.mp4.receipt.json"
[[ -s "$RECEIPT" ]] || fail "smoke render receipt missing"

STATE_DIR="$HOME/.velvetos"
STATE_FILE="$STATE_DIR/render-host.json"
mkdir -p "$STATE_DIR"
python3 - "$STATE_FILE" "$HOST_ID" "$HYPERFRAMES_VERSION" "$ROOT" "$RECEIPT" <<'PY'
import json
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

state_path, host_id, version, root, receipt_path = sys.argv[1:]
try:
    commit = subprocess.check_output(["git", "-C", root, "rev-parse", "HEAD"], text=True).strip()
except Exception:
    commit = "unknown"
receipt = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
state = {
    "schemaVersion": 1,
    "hostId": host_id,
    "hostname": socket.gethostname(),
    "role": "velvetos-render-host",
    "backend": "hyperframes",
    "hyperframesVersion": version,
    "repoCommit": commit,
    "smokeReceiptSha256": receipt.get("sha256"),
    "smokeVerifiedAt": receipt.get("verifiedAt"),
    "registeredAt": datetime.now(timezone.utc).isoformat(),
    "status": "host-smoke-verified"
}
Path(state_path).write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"OK local host state written: {state_path}")
PY

say "OK HyperFrames host smoke verified"
say "  host=$HOST_ID"
say "  hyperframes=$HYPERFRAMES_VERSION"
say "  output=$SMOKE_ROOT/renders/host-smoke.mp4"
say "  receipt=$RECEIPT"
say "  state=$STATE_FILE"

if command -v agent >/dev/null 2>&1; then
  say "Checking Cursor worker login..."
  agent status || fail "Cursor agent is installed but not logged in; run 'agent login' and rerun bootstrap"
else
  fail "Cursor agent CLI missing. Install it per packages/vfmcp/HOST.md, then rerun so the render host is reachable by the existing Edge route."
fi

if pgrep -f "agent worker.*${HOST_ID}" >/dev/null 2>&1; then
  say "OK Cursor worker '$HOST_ID' is already running"
  exit 0
fi

if [[ "$START_WORKER" -eq 1 ]]; then
  say "Starting canonical Cursor worker '$HOST_ID'. This terminal will remain attached."
  exec env PATH="$HOME/.local/bin:$PATH" HYPERFRAMES_NO_UPDATE_CHECK=1 HYPERFRAMES_NO_AUTO_INSTALL=1 NPM_CONFIG_PREFIX="$HOME/.local" agent worker --name "$HOST_ID" start
fi

say "HOST READY, WORKER NOT RUNNING"
say "Start the existing Edge route with:"
say "  cd $ROOT && PATH=\"$HOME/.local/bin:$PATH\" HYPERFRAMES_NO_UPDATE_CHECK=1 HYPERFRAMES_NO_AUTO_INSTALL=1 NPM_CONFIG_PREFIX=\"$HOME/.local\" agent worker --name \"$HOST_ID\" start"
