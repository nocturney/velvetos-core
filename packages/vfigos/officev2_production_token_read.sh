#!/usr/bin/env bash
set -Eeuo pipefail
TMP="$(mktemp -d)"
APP_TOKEN=""
cleanup(){ set +e; [ -n "$APP_TOKEN" ] && [ -n "${BAO_API:-}" ] && curl -sS -o /dev/null -H "X-Vault-Token: $APP_TOKEN" -X POST "$BAO_API/v1/auth/token/revoke-self" >/dev/null 2>&1 || true; rm -rf "$TMP"; unset INPUT ROLE_ID SECRET_ID APP_TOKEN VALUE; }
trap cleanup EXIT
INPUT="$(cat)"
ROLE_ID="$(printf '%s' "$INPUT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("role_id",""))')"
SECRET_ID="$(printf '%s' "$INPUT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("secret_id",""))')"
[ -n "$ROLE_ID" ] && [ -n "$SECRET_ID" ] || { echo "PROD_APPROLE_INPUT_INVALID" >&2; exit 311; }
BAO_IP="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' officev2-p3b-shadow-openbao 2>/dev/null || true)"
[ -n "$BAO_IP" ] || { echo "PROD_BROKER_IP_MISSING" >&2; exit 312; }
BAO_API="http://$BAO_IP:8200"
LOGIN="$(python3 -c 'import json,sys; print(json.dumps({"role_id":sys.argv[1],"secret_id":sys.argv[2]}))' "$ROLE_ID" "$SECRET_ID")"
LOGIN_HTTP="$(printf '%s' "$LOGIN" | curl -sS -o "$TMP/login.json" -w '%{http_code}' -H 'Content-Type: application/json' -X POST --data-binary @- "$BAO_API/v1/auth/approle/login" || true)"
[ "$LOGIN_HTTP" = 200 ] || { echo "PROD_BROKER_LOGIN_FAIL=$LOGIN_HTTP" >&2; exit 313; }
APP_TOKEN="$(python3 -c 'import json,sys; print((json.load(open(sys.argv[1])).get("auth") or {}).get("client_token",""))' "$TMP/login.json")"
[ -n "$APP_TOKEN" ] || { echo "PROD_BROKER_TOKEN_MISSING" >&2; exit 314; }
READ_HTTP="$(curl -sS -o "$TMP/value.json" -w '%{http_code}' -H "X-Vault-Token: $APP_TOKEN" "$BAO_API/v1/secret/data/officev2-prod/instagram-publisher-snapshot" || true)"
[ "$READ_HTTP" = 200 ] || { echo "PROD_BROKER_READ_FAIL=$READ_HTTP" >&2; exit 315; }
VALUE="$(python3 - "$TMP/value.json" <<'PY'
import json,sys
print((((json.load(open(sys.argv[1])).get("data") or {}).get("data") or {}).get("value","")))
PY
)"
[ -n "$VALUE" ] || { echo "PROD_BROKER_VALUE_EMPTY" >&2; exit 316; }
printf '%s' "$VALUE"
