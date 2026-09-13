#!/usr/bin/env bash
set -euo pipefail

HOST_ID="sderot-mac"
APP_USER="$HOME/Applications/VoiceStudio.app"
APP_SYSTEM="/Applications/VoiceStudio.app"
STATE_DIR="$HOME/.velvetos"
STATE_FILE="$STATE_DIR/speech-host.json"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VOICE_VERSION="$(python3 "$ROOT/scripts/vf_toolchain.py" get components.voicestudio.version)"
VOICE_COMMIT="$(python3 "$ROOT/scripts/vf_toolchain.py" get components.voicestudio.commit)"

fail() { printf 'FAIL %s\n' "$*" >&2; exit 1; }
say() { printf '%s\n' "$*"; }

[[ "$(uname -s)" == "Darwin" ]] || fail "speech bootstrap is for macOS"
[[ "$(uname -m)" == "arm64" ]] || fail "VoiceStudio local backend requires Apple Silicon"

APP=""
[[ -d "$APP_USER" ]] && APP="$APP_USER"
[[ -z "$APP" && -d "$APP_SYSTEM" ]] && APP="$APP_SYSTEM"
[[ -n "$APP" ]] || fail "VoiceStudio $VOICE_VERSION is not installed"

PLIST="$APP/Contents/Info.plist"
APP_VERSION="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$PLIST" 2>/dev/null || true)"
[[ "$APP_VERSION" == "$VOICE_VERSION" ]] || fail "VoiceStudio version mismatch: expected $VOICE_VERSION, found ${APP_VERSION:-unknown}"

if ! curl -fsS --max-time 3 http://127.0.0.1:3900/.well-known/voicestudio-speech >/dev/null 2>&1; then
  say "VoiceStudio API not ready; launching pinned app..."
  /usr/bin/open -a "$APP" || true
  for _ in 1 2 3 4 5 6; do
    sleep 3
    curl -fsS --max-time 3 http://127.0.0.1:3900/.well-known/voicestudio-speech >/dev/null 2>&1 && break
  done
fi

if ! curl -fsS --max-time 3 http://127.0.0.1:3900/.well-known/voicestudio-speech >/dev/null 2>&1; then
  fail "VoiceStudio API did not become ready on loopback port 3900; complete first-run setup once and rerun"
fi

python3 "$ROOT/scripts/vf_speech.py" doctor
mkdir -p "$STATE_DIR"
python3 - "$STATE_FILE" "$HOST_ID" "$VOICE_VERSION" "$VOICE_COMMIT" <<'PY'
import json, socket, sys
from datetime import datetime, timezone
from pathlib import Path
state_path, host_id, version, commit = sys.argv[1:]
state = {"schemaVersion":1,"hostId":host_id,"hostname":socket.gethostname(),"role":"velvetos-speech-host","provider":"voicestudio","providerVersion":version,"providerCommit":commit,"serviceRoot":"http://127.0.0.1:3900","status":"provider-api-verified","verifiedAt":datetime.now(timezone.utc).isoformat()}
Path(state_path).write_text(json.dumps(state, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
PY
say "OK VoiceStudio speech host verified host=$HOST_ID version=$VOICE_VERSION"
