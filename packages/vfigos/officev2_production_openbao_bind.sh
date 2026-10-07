#!/usr/bin/env bash
set -Eeuo pipefail

MODE="${1:-Rotate}"
case "$MODE" in Rotate|Cleanup) ;; *) echo "PROD_OPENBAO_MODE_INVALID" >&2; exit 351;; esac
TMP="$(mktemp -d)"
BAO_API=""
ADMIN_TOKEN=""
READ_TOKEN=""
INPUT=""
PROVIDER_TOKEN=""

cleanup(){
  rc=$?
  set +e
  if [ -n "$READ_TOKEN" ] && [ -n "$BAO_API" ]; then
    curl -sS -o /dev/null -H "X-Vault-Token: $READ_TOKEN" -X POST "$BAO_API/v1/auth/token/revoke-self" >/dev/null 2>&1 || true
  fi
  if [ -n "$ADMIN_TOKEN" ] && [ -n "$BAO_API" ]; then
    curl -sS -o /dev/null -H "X-Vault-Token: $ADMIN_TOKEN" -X POST "$BAO_API/v1/auth/token/revoke-self" >/dev/null 2>&1 || true
  fi
  rm -rf "$TMP"
  unset INPUT PROVIDER_TOKEN ADMIN_TOKEN READ_TOKEN
  exit "$rc"
}
trap cleanup EXIT

INPUT="$(cat)"
[ -n "$INPUT" ] || { echo "PROD_OPENBAO_ADMIN_INPUT_MISSING" >&2; exit 352; }
readarray -t FIELDS < <(printf '%s' "$INPUT" | python3 -c '
import json,sys
d=json.load(sys.stdin)
for k in ("admin_role_id","admin_secret_id","role_id","secret_id","provider_token"):
 print(d.get(k,""))
')
ADMIN_ROLE_ID="${FIELDS[0]:-}"
ADMIN_SECRET_ID="${FIELDS[1]:-}"
READ_ROLE_ID="${FIELDS[2]:-}"
READ_SECRET_ID="${FIELDS[3]:-}"
PROVIDER_TOKEN="${FIELDS[4]:-}"
[ -n "$ADMIN_ROLE_ID" ] && [ -n "$ADMIN_SECRET_ID" ] || { echo "PROD_OPENBAO_ADMIN_APPROLE_INPUT_INVALID" >&2; exit 353; }

BAO_IP="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' officev2-p3b-shadow-openbao 2>/dev/null || true)"
[ -n "$BAO_IP" ] || { echo "PROD_OPENBAO_IP_MISSING" >&2; exit 354; }
BAO_API="http://$BAO_IP:8200"
HEALTH="$(curl -sS -o /dev/null -w '%{http_code}' "$BAO_API/v1/sys/health" || true)"
[ "$HEALTH" = 200 ] || { echo "PROD_OPENBAO_NOT_ACTIVE=$HEALTH" >&2; exit 355; }

login(){
  local role="$1" secret="$2" outfile="$3"
  python3 -c 'import json,sys; print(json.dumps({"role_id":sys.argv[1],"secret_id":sys.argv[2]}))' "$role" "$secret" |
    curl -sS -o "$outfile" -w '%{http_code}' -H 'Content-Type: application/json' -X POST --data-binary @- "$BAO_API/v1/auth/approle/login"
}
ADMIN_LOGIN_HTTP="$(login "$ADMIN_ROLE_ID" "$ADMIN_SECRET_ID" "$TMP/admin-login.json")"
[ "$ADMIN_LOGIN_HTTP" = 200 ] || { echo "PROD_OPENBAO_ADMIN_LOGIN_FAIL=$ADMIN_LOGIN_HTTP" >&2; exit 356; }
ADMIN_TOKEN="$(python3 -c 'import json,sys; print((json.load(open(sys.argv[1])).get("auth") or {}).get("client_token",""))' "$TMP/admin-login.json")"
[ -n "$ADMIN_TOKEN" ] || { echo "PROD_OPENBAO_ADMIN_TOKEN_MISSING" >&2; exit 357; }

ADMIN_UNRELATED="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $ADMIN_TOKEN" "$BAO_API/v1/secret/data/alpha" || true)"
[ "$ADMIN_UNRELATED" = 403 ] || { echo "PROD_OPENBAO_ADMIN_SCOPE_TOO_BROAD=$ADMIN_UNRELATED" >&2; exit 358; }

if [ "$MODE" = Cleanup ]; then
  read_role_del="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $ADMIN_TOKEN" -X DELETE "$BAO_API/v1/auth/approle/role/officev2-prod-publisher-snapshot" || true)"
  read_policy_del="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $ADMIN_TOKEN" -X DELETE "$BAO_API/v1/sys/policies/acl/officev2-prod-publisher-snapshot" || true)"
  secret_del="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $ADMIN_TOKEN" -X DELETE "$BAO_API/v1/secret/metadata/officev2-prod/instagram-publisher-snapshot" || true)"
  admin_role_del="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $ADMIN_TOKEN" -X DELETE "$BAO_API/v1/auth/approle/role/officev2-prod-broker-admin" || true)"
  admin_policy_del="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $ADMIN_TOKEN" -X DELETE "$BAO_API/v1/sys/policies/acl/officev2-prod-broker-admin" || true)"
  for code in "$read_role_del" "$read_policy_del" "$secret_del" "$admin_role_del" "$admin_policy_del"; do
    [[ "$code" =~ ^(200|204)$ ]] || { echo "PROD_OPENBAO_CLEANUP_DENIED" >&2; exit 359; }
  done
  printf '{"schema":"velvetos.office-v2.phase3b-production-openbao-cleanup.v1","status":"PASS","admin_auth":"APPROLE_NARROW","admin_unrelated_scope_http":403,"root_used":false,"root_token_persisted":false}\n'
  exit 0
fi

[ -n "$READ_ROLE_ID" ] && [ -n "$READ_SECRET_ID" ] && [ -n "$PROVIDER_TOKEN" ] || { echo "PROD_OPENBAO_ROTATE_INPUT_INVALID" >&2; exit 360; }
PROVIDER_SHA="$(printf '%s' "$PROVIDER_TOKEN" | sha256sum | awk '{print $1}')"
write_http="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $ADMIN_TOKEN" -H 'Content-Type: application/json' -X POST -d "$(python3 -c 'import json,sys; print(json.dumps({"data":{"value":sys.argv[1]}}))' "$PROVIDER_TOKEN")" "$BAO_API/v1/secret/data/officev2-prod/instagram-publisher-snapshot" || true)"
[[ "$write_http" =~ ^(200|204)$ ]] || { echo "PROD_OPENBAO_SECRET_WRITE_FAIL=$write_http" >&2; exit 361; }

READ_LOGIN_HTTP="$(login "$READ_ROLE_ID" "$READ_SECRET_ID" "$TMP/read-login.json")"
[ "$READ_LOGIN_HTTP" = 200 ] || { echo "PROD_OPENBAO_READ_LOGIN_FAIL=$READ_LOGIN_HTTP" >&2; exit 362; }
READ_TOKEN="$(python3 -c 'import json,sys; print((json.load(open(sys.argv[1])).get("auth") or {}).get("client_token",""))' "$TMP/read-login.json")"
[ -n "$READ_TOKEN" ] || { echo "PROD_OPENBAO_READ_TOKEN_MISSING" >&2; exit 363; }

EXACT_HTTP="$(curl -sS -o "$TMP/exact.json" -w '%{http_code}' -H "X-Vault-Token: $READ_TOKEN" "$BAO_API/v1/secret/data/officev2-prod/instagram-publisher-snapshot" || true)"
UNRELATED_HTTP="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $READ_TOKEN" "$BAO_API/v1/secret/data/alpha" || true)"
MATCH="$(python3 - "$TMP/exact.json" "$PROVIDER_SHA" <<'PY'
import hashlib,json,sys
try:
 d=json.load(open(sys.argv[1]))
 v=((d.get("data") or {}).get("data") or {}).get("value","")
 print(str(hashlib.sha256(v.encode()).hexdigest()==sys.argv[2]).lower())
except Exception:
 print("false")
PY
)"
[ "$EXACT_HTTP" = 200 ] && [ "$UNRELATED_HTTP" = 403 ] && [ "$MATCH" = true ] || { echo "PROD_OPENBAO_SCOPE_PROOF_FAIL exact=$EXACT_HTTP unrelated=$UNRELATED_HTTP match=$MATCH" >&2; exit 364; }

python3 - "$PROVIDER_SHA" "$write_http" <<'PY'
import json,sys
print(json.dumps({
 "schema":"velvetos.office-v2.phase3b-production-openbao-rotate.v1",
 "status":"PASS",
 "credential_reference_sha256":sys.argv[1],
 "admin_write_http":int(sys.argv[2]),
 "read_exact_scope_http":200,
 "read_unrelated_scope_http":403,
 "admin_unrelated_scope_http":403,
 "admin_auth":"APPROLE_NARROW",
 "root_used":False,
 "root_token_persisted":False
},separators=(",",":")))
PY
