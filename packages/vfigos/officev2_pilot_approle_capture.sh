#!/usr/bin/env bash
set -Eeuo pipefail
MODE="${1:-Read}"
RUN=/run/officev2/phase3b
META=/opt/officev2-phase3b-shadow/pilot-meta.json
SECRET="$RUN/openbao-pilot-secret-id"
case "$MODE" in
  Read)
    [ -s "$META" ] && [ -s "$SECRET" ] || { echo "PILOT_APPROLE_CAPTURE_MISSING" >&2; exit 371; }
    python3 - "$META" "$SECRET" <<'PY'
import json,sys
m=json.load(open(sys.argv[1]))
secret=open(sys.argv[2],encoding="utf-8").read().strip()
role=str(m.get("openbao_role_id") or "")
sha=str(m.get("credential_reference_sha256") or "")
if not role or not secret or not sha:
    raise SystemExit("pilot capture invalid")
print(json.dumps({"schema":"velvetos.office-v2.phase3b-pilot-approle-capture.v0","role_id":role,"secret_id":secret,"credential_reference_sha256":sha},separators=(",",":")))
PY
    ;;
  Cleanup)
    rm -f "$SECRET"
    echo "PASS PILOT_APPROLE_RUNTIME_PLAINTEXT_REMOVED"
    ;;
  *)
    echo "PILOT_APPROLE_CAPTURE_MODE_INVALID" >&2
    exit 372
    ;;
esac
