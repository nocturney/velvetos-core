#!/usr/bin/env bash
set -euo pipefail

MANIM_MINIMUM_VERSION="0.21.0"
MANIM_RECOVERY_VERSION="0.21.0"
PYTHON_VERSION="3.12"
HOST_ID="sderot-mac"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$HOME/.local/bin:$PATH"
TOOLCHAIN="$HOME/.velvetos/toolchain/manim-py312"
STATE_DIR="$HOME/.velvetos"
STATE_FILE="$STATE_DIR/manim-host.json"
SMOKE_ROOT="$HOME/.velvetos/tmp/manim-smoke"

fail() { printf 'FAIL %s\n' "$*" >&2; exit 1; }
say() { printf '%s\n' "$*"; }

[[ "$(uname -s)" == "Darwin" ]] || fail "this bootstrap is for the canonical macOS host only"
command -v ffmpeg >/dev/null 2>&1 || fail "ffmpeg required; run bootstrap-hyperframes-host-macos.sh first"
command -v ffprobe >/dev/null 2>&1 || fail "ffprobe required; run bootstrap-hyperframes-host-macos.sh first"

if ! command -v uv >/dev/null 2>&1; then
  say "Installing uv user-locally..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

uv python install "$PYTHON_VERSION"
if [[ ! -x "$TOOLCHAIN/bin/python" ]]; then
  uv venv --python "$PYTHON_VERSION" "$TOOLCHAIN"
fi
uv pip install --python "$TOOLCHAIN/bin/python" "manim>=$MANIM_MINIMUM_VERSION"

MANIM="$TOOLCHAIN/bin/manim"
CURRENT="$("$MANIM" --version | sed -nE 's/.*v([0-9]+\.[0-9]+\.[0-9]+).*/\1/p' | head -n1)"
[[ -n "$CURRENT" ]] || fail "could not determine Manim version"
"$TOOLCHAIN/bin/python" - "$CURRENT" "$MANIM_MINIMUM_VERSION" <<'PY'
import sys
def ver(v): return tuple(int(x) for x in v.split("."))
if ver(sys.argv[1]) < ver(sys.argv[2]):
    raise SystemExit(1)
PY

rm -rf "$SMOKE_ROOT"
mkdir -p "$SMOKE_ROOT"
cat > "$SMOKE_ROOT/scene.py" <<'PY'
from manim import *
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16

class VelvetSmoke(Scene):
    def construct(self):
        title = Text("VF technical slot", font_size=42).to_edge(UP)
        line = Line(LEFT * 2.5, RIGHT * 2.5)
        dot = Dot(line.get_start())
        label = Text("5.0 mm", font_size=34).next_to(line, DOWN)
        self.add(title, line, dot, label)
        self.play(dot.animate.move_to(line.get_end()), run_time=1.2)
        self.wait(0.3)
PY

"$MANIM" -ql --disable_caching --format mp4 --media_dir "$SMOKE_ROOT/media" "$SMOKE_ROOT/scene.py" VelvetSmoke
OUTPUT="$(find "$SMOKE_ROOT/media" -name VelvetSmoke.mp4 -print -quit)"
[[ -n "$OUTPUT" && -s "$OUTPUT" ]] || fail "Manim smoke output missing"

PROBE="$(ffprobe -v error -show_entries stream=codec_type,width,height -show_entries format=duration -of json "$OUTPUT")"
python3 - "$PROBE" <<'PY'
import json, sys
p=json.loads(sys.argv[1])
v=next((x for x in p.get("streams",[]) if x.get("codec_type")=="video"), None)
if not v or int(v.get("width",0)) != 1080 or int(v.get("height",0)) != 1920:
    raise SystemExit("invalid Manim smoke dimensions")
if float((p.get("format") or {}).get("duration") or 0) <= 0:
    raise SystemExit("invalid Manim smoke duration")
PY

SHA="$(shasum -a 256 "$OUTPUT" | awk '{print $1}')"
mkdir -p "$STATE_DIR"
python3 - "$STATE_FILE" "$HOST_ID" "$CURRENT" "$TOOLCHAIN" "$OUTPUT" "$SHA" <<'PY'
import json, sys
from datetime import datetime, timezone
from pathlib import Path
path, host, version, toolchain, output, sha = sys.argv[1:]
Path(path).write_text(json.dumps({
  "schemaVersion": 1,
  "hostId": host,
  "engine": "manim",
  "version": version,
  "versionPolicy": "latest-compatible",
  "minimumVersion": "0.21.0",
  "recoveryVersion": "0.21.0",
  "python": "3.12",
  "platform": "macOS arm64",
  "toolchain": toolchain,
  "smoke": "pass",
  "width": 1080,
  "height": 1920,
  "output": output,
  "sha256": sha,
  "verifiedAt": datetime.now(timezone.utc).isoformat()
}, indent=2) + "\n", encoding="utf-8")
PY

say "OK Manim macOS host smoke verified"
say "  host=$HOST_ID"
say "  version=$CURRENT"
say "  sha256=$SHA"
say "  state=$STATE_FILE"
