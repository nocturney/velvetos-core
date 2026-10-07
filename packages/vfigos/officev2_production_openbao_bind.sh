#!/usr/bin/env bash
set -Eeuo pipefail
MODE="${1:-Init}"
case "$MODE" in Init|Rotate|Cleanup) ;; *) echo "PROD_OPENBAO_MODE_INVALID" >&2; exit 231;; esac
RUN=/run/officev2/phase3b
UNSEAL_FILE="$RUN/openbao-unseal.key"
TMP="$(mktemp -d)"
ROOT_TOKEN=""
OTP=""
NONCE=""
GEN_ACTIVE=false
APP_TOKEN=""
BAO_API=""
cleanup(){
  rc=$?
  set +e
  if [ -n "$APP_TOKEN" ] && [ -n "$BAO_API" ]; then
    curl -sS -o /dev/null -H "X-Vault-Token: $APP_TOKEN" -X POST "$BAO_API/v1/auth/token/revoke-self" >/dev/null 2>&1 || true
  fi
  if [ -n "$ROOT_TOKEN" ] && [ -n "$BAO_API" ]; then
    curl -sS -o /dev/null -H "X-Vault-Token: $ROOT_TOKEN" -X POST "$BAO_API/v1/auth/token/revoke-self" >/dev/null 2>&1 || true
  elif [ "$GEN_ACTIVE" = true ]; then
    docker exec officev2-p3b-shadow-openbao env BAO_ADDR=http://127.0.0.1:8200 bao operator generate-root -cancel >/dev/null 2>&1 || true
  fi
  rm -rf "$TMP"
  unset ROOT_TOKEN OTP NONCE APP_TOKEN INPUT PROVIDER_TOKEN
  exit "$rc"
}
trap cleanup EXIT

[ -s "$UNSEAL_FILE" ] || { echo "PROD_OPENBAO_UNSEAL_KEY_MISSING" >&2; exit 232; }
BAO_IP="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' officev2-p3b-shadow-openbao 2>/dev/null || true)"
[ -n "$BAO_IP" ] || { echo "PROD_OPENBAO_IP_MISSING" >&2; exit 233; }
BAO_API="http://$BAO_IP:8200"
HEALTH="$(curl -sS -o /dev/null -w '%{http_code}' "$BAO_API/v1/sys/health" || true)"
[ "$HEALTH" = 200 ] || { echo "PROD_OPENBAO_NOT_ACTIVE=$HEALTH" >&2; exit 234; }

# Clear only a stale generate-root attempt. No root token is created by cancel.
docker exec officev2-p3b-shadow-openbao env BAO_ADDR=http://127.0.0.1:8200 bao operator generate-root -cancel >/dev/null 2>&1 || true
OTP="$(docker exec officev2-p3b-shadow-openbao env BAO_ADDR=http://127.0.0.1:8200 bao operator generate-root -generate-otp)"
[ -n "$OTP" ] || { echo "PROD_OPENBAO_OTP_FAIL" >&2; exit 235; }
INIT_JSON="$(docker exec officev2-p3b-shadow-openbao env BAO_ADDR=http://127.0.0.1:8200 bao operator generate-root -format=json -init -otp="$OTP")"
GEN_ACTIVE=true
NONCE="$(printf '%s' "$INIT_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("nonce",""))')"
[ -n "$NONCE" ] || { echo "PROD_OPENBAO_NONCE_FAIL" >&2; exit 236; }
UNSEAL="$(cat "$UNSEAL_FILE")"
UPDATE_JSON="$(printf '%s' "$UNSEAL" | docker exec -i officev2-p3b-shadow-openbao env BAO_ADDR=http://127.0.0.1:8200 bao operator generate-root -format=json -nonce="$NONCE" -)"
COMPLETE="$(printf '%s' "$UPDATE_JSON" | python3 -c 'import json,sys; print(str(json.load(sys.stdin).get("complete") is True).lower())')"
ENCODED="$(printf '%s' "$UPDATE_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("encoded_token",""))')"
[ "$COMPLETE" = true ] && [ -n "$ENCODED" ] || { echo "PROD_OPENBAO_GENERATE_ROOT_INCOMPLETE" >&2; exit 237; }
ROOT_TOKEN="$(docker exec officev2-p3b-shadow-openbao env BAO_ADDR=http://127.0.0.1:8200 bao operator generate-root -decode="$ENCODED" -otp="$OTP")"
GEN_ACTIVE=false
[ -n "$ROOT_TOKEN" ] || { echo "PROD_OPENBAO_ROOT_DECODE_FAIL" >&2; exit 238; }
RH=(-H "X-Vault-Token: $ROOT_TOKEN" -H 'Content-Type: application/json')

if [ "$MODE" = Cleanup ]; then
  role_del="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X DELETE "$BAO_API/v1/auth/approle/role/officev2-prod-publisher-snapshot" || true)"
  policy_del="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X DELETE "$BAO_API/v1/sys/policies/acl/officev2-prod-publisher-snapshot" || true)"
  secret_del="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X DELETE "$BAO_API/v1/secret/metadata/officev2-prod/instagram-publisher-snapshot" || true)"
  revoke="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $ROOT_TOKEN" -X POST "$BAO_API/v1/auth/token/revoke-self" || true)"
  ROOT_TOKEN=""
  [[ "$revoke" =~ ^(200|204)$ ]] || { echo "PROD_OPENBAO_ROOT_REVOKE_FAIL=$revoke" >&2; exit 239; }
  printf 'PASS OPENBAO_CLEANUP role=%s policy=%s secret=%s root_revoked=true\n' "$role_del" "$policy_del" "$secret_del"
  exit 0
fi

PROVIDER_TOKEN="$(cat)"
[ -n "$PROVIDER_TOKEN" ] || { echo "PROD_OPENBAO_PROVIDER_TOKEN_MISSING" >&2; exit 240; }
PROVIDER_SHA="$(printf '%s' "$PROVIDER_TOKEN" | sha256sum | awk '{print $1}')"
write_http="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d "$(python3 -c 'import json,sys; print(json.dumps({"data":{"value":sys.argv[1]}}))' "$PROVIDER_TOKEN")" "$BAO_API/v1/secret/data/officev2-prod/instagram-publisher-snapshot" || true)"
[[ "$write_http" =~ ^(200|204)$ ]] || { echo "PROD_OPENBAO_SECRET_WRITE_FAIL=$write_http" >&2; exit 241; }

if [ "$MODE" = Init ]; then
  policy_http="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d '{"policy":"path \"secret/data/officev2-prod/instagram-publisher-snapshot\" { capabilities = [\"read\"] }"}' "$BAO_API/v1/sys/policies/acl/officev2-prod-publisher-snapshot" || true)"
  role_http="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d '{"policies":"officev2-prod-publisher-snapshot","token_ttl":"5m","token_max_ttl":"10m","secret_id_ttl":"0","secret_id_num_uses":0,"token_no_default_policy":true}' "$BAO_API/v1/auth/approle/role/officev2-prod-publisher-snapshot" || true)"
  [[ "$policy_http" =~ ^(200|204)$ ]] && [[ "$role_http" =~ ^(200|204)$ ]] || { echo "PROD_OPENBAO_ROLE_CONFIG_FAIL policy=$policy_http role=$role_http" >&2; exit 242; }
fi

ROLE_ID="$(curl -fsS "${RH[@]}" "$BAO_API/v1/auth/approle/role/officev2-prod-publisher-snapshot/role-id" | python3 -c 'import json,sys; print((json.load(sys.stdin).get("data") or {}).get("role_id",""))')"
[ -n "$ROLE_ID" ] || { echo "PROD_OPENBAO_ROLE_ID_MISSING" >&2; exit 243; }

if [ "$MODE" = Init ]; then
  SECRET_ID="$(curl -fsS "${RH[@]}" -X POST "$BAO_API/v1/auth/approle/role/officev2-prod-publisher-snapshot/secret-id" | python3 -c 'import json,sys; print((json.load(sys.stdin).get("data") or {}).get("secret_id",""))')"
  [ -n "$SECRET_ID" ] || { echo "PROD_OPENBAO_SECRET_ID_MISSING" >&2; exit 244; }
  LOGIN="$(python3 -c 'import json,sys; print(json.dumps({"role_id":sys.argv[1],"secret_id":sys.argv[2]}))' "$ROLE_ID" "$SECRET_ID")"
  LOGIN_HTTP="$(printf '%s' "$LOGIN" | curl -sS -o "$TMP/login.json" -w '%{http_code}' -H 'Content-Type: application/json' -X POST --data-binary @- "$BAO_API/v1/auth/approle/login" || true)"
  [ "$LOGIN_HTTP" = 200 ] || { echo "PROD_OPENBAO_APPROLE_LOGIN_FAIL=$LOGIN_HTTP" >&2; exit 245; }
  APP_TOKEN="$(python3 -c 'import json,sys; print((json.load(open(sys.argv[1])).get("auth") or {}).get("client_token",""))' "$TMP/login.json")"
  [ -n "$APP_TOKEN" ] || { echo "PROD_OPENBAO_APP_TOKEN_MISSING" >&2; exit 246; }
  EXACT_HTTP="$(curl -sS -o "$TMP/exact.json" -w '%{http_code}' -H "X-Vault-Token: $APP_TOKEN" "$BAO_API/v1/secret/data/officev2-prod/instagram-publisher-snapshot" || true)"
  UNRELATED_HTTP="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $APP_TOKEN" "$BAO_API/v1/secret/data/alpha" || true)"
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
  [ "$EXACT_HTTP" = 200 ] && [ "$UNRELATED_HTTP" = 403 ] && [ "$MATCH" = true ] || { echo "PROD_OPENBAO_SCOPE_PROOF_FAIL exact=$EXACT_HTTP unrelated=$UNRELATED_HTTP match=$MATCH" >&2; exit 247; }
fi

revoke="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $ROOT_TOKEN" -X POST "$BAO_API/v1/auth/token/revoke-self" || true)"
[[ "$revoke" =~ ^(200|204)$ ]] || { echo "PROD_OPENBAO_ROOT_REVOKE_FAIL=$revoke" >&2; exit 248; }
root_after="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $ROOT_TOKEN" "$BAO_API/v1/auth/token/lookup-self" || true)"
ROOT_TOKEN=""
[ "$root_after" = 403 ] || { echo "PROD_OPENBAO_ROOT_REVOKE_PROOF_FAIL=$root_after" >&2; exit 249; }

if [ "$MODE" = Init ]; then
  python3 - "$ROLE_ID" "$SECRET_ID" "$PROVIDER_SHA" <<'PY'
import json,sys
print(json.dumps({
 "schema":"velvetos.office-v2.phase3b-production-openbao-bundle.v0",
 "role_id":sys.argv[1],
 "secret_id":sys.argv[2],
 "credential_reference_sha256":sys.argv[3],
 "broker_path":"officev2-prod/data/instagram-publisher-snapshot",
 "broker_role":"officev2-prod-publisher-snapshot"
},separators=(",",":")))
PY
else
  printf '{"schema":"velvetos.office-v2.phase3b-production-openbao-rotate.v0","status":"PASS","credential_reference_sha256":"%s","root_revoked":true}\n' "$PROVIDER_SHA"
fi
