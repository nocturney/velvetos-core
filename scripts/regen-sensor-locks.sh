#!/usr/bin/env bash
# Regenerate the hashed sensor lock files from requirements-sensors.txt.
#
#   requirements-sensors.txt       human-edited input (direct + transitive pins)
#   requirements-sensors.py311.lock  CI Python 3.11 (check-all, instagram-read-smoke)
#   requirements-sensors.py312.lock  CI Python 3.12 (velvetos-research)
#
# CI installs with: python3 -m pip install --require-hashes -r requirements-sensors.py3XX.lock
# Run after any change to requirements-sensors.txt, then commit all three files;
# scripts/check-sensor-locks.py fails CI if they drift apart.
#
# Usage: scripts/regen-sensor-locks.sh
#        PY311=/path/to/python3.11 PY312=/path/to/python3.12 scripts/regen-sensor-locks.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PIP_TOOLS_VERSION="7.6.1"
PY311="${PY311:-python3.11}"
PY312="${PY312:-python3.12}"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
for pair in "311:$PY311" "312:$PY312"; do
  tag="${pair%%:*}"; py="${pair#*:}"
  command -v "$py" >/dev/null || { echo "missing interpreter: $py (set PY$tag)" >&2; exit 2; }
  "$py" -m venv "$tmp/v$tag"
  "$tmp/v$tag/bin/python" -m pip install -q --disable-pip-version-check "pip-tools==$PIP_TOOLS_VERSION"
  CUSTOM_COMPILE_COMMAND="scripts/regen-sensor-locks.sh" \
    "$tmp/v$tag/bin/pip-compile" --quiet --generate-hashes --no-emit-index-url --strip-extras \
    --resolver=backtracking --output-file "requirements-sensors.py$tag.lock" requirements-sensors.txt
  echo "OK requirements-sensors.py$tag.lock"
done
