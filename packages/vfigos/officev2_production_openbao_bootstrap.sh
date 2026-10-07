#!/usr/bin/env bash
set -Eeuo pipefail

EXPECTED_SHA="${1:-}"
RUN=/run/officev2/phase3b
BASE=/opt/officev2-phase3b-shadow
TOKEN_FILE="$RUN/pilot-snapshot-token"
SHADOW_META="$BASE/shadow-meta.json"
PILOT_META="$BASE/pilot-meta.json"
PGIMG='postgres@sha256:a02db8cac496f15b094798a38254f14d6e00741f709360e5e00bb6668ea31636'
BAOVOL=officev2_p3b_shadow_bao
TMP="$(mktemp -d)"
PILOT_VALUE=""
ROOT_TOKEN=""
SHADOW_APP_TOKEN=""
PILOT_APP_TOKEN=""
PROD_APP_TOKEN=""
ADMIN_TOKEN=""
RESET_STARTED=false
SUCCESS=false
BAO_API=""

hash_text(){ printf '%s' "$1" | sha256sum | awk '{print $1}'; }

recreate_openbao(){
  systemctl stop officev2-phase3b-shadow-health.service officev2-phase3b-openbao.service >/dev/null 2>&1 || true
  docker rm -f officev2-p3b-shadow-openbao >/dev/null 2>&1 || true
  docker volume rm "$BAOVOL" >/dev/null 2>&1 || true
  docker volume create "$BAOVOL" >/dev/null
  docker run --rm --user root -v "$BAOVOL:/openbao-data" --entrypoint bash "$PGIMG" -lc 'chown 100:1000 /openbao-data && chmod 0700 /openbao-data' >/dev/null
  rm -f "$RUN/openbao-unseal.key" "$RUN/openbao-approle-secret-id" "$RUN/openbao-pilot-secret-id" "$SHADOW_META" "$PILOT_META"
  systemctl reset-failed officev2-phase3b-openbao.service officev2-phase3b-shadow-health.service >/dev/null 2>&1 || true
  systemctl start officev2-phase3b-openbao.service
}

restore_pilot_only(){
  set +e
  recreate_openbao
  umask 077
  printf '%s' "$PILOT_VALUE" >"$TOKEN_FILE"
  chmod 0600 "$TOKEN_FILE"
  BOOT="$(bash /var/officev2/artifacts/phase3b-security/shadow-bootstrap.sh 2>&1)"
  brc=$?
  systemctl start officev2-phase3b-shadow-health.service >/dev/null 2>&1 || true
  bash /var/officev2/artifacts/phase3b-security/shadow-health-once.sh >/dev/null 2>&1 || true
  if [ "$brc" -eq 0 ] && printf '%s' "$BOOT" | grep -q 'root_revoked=true'; then
    echo "PROD_BOOTSTRAP_ROLLBACK=PASS_PILOT_ONLY_ROOT_REVOKED" >&2
  else
    echo "PROD_BOOTSTRAP_ROLLBACK=FAIL" >&2
  fi
}

cleanup(){
  rc=$?
  set +e
  for tok in "$SHADOW_APP_TOKEN" "$PILOT_APP_TOKEN" "$PROD_APP_TOKEN" "$ADMIN_TOKEN"; do
    if [ -n "$tok" ] && [ -n "$BAO_API" ]; then
      curl -sS -o /dev/null -H "X-Vault-Token: $tok" -X POST "$BAO_API/v1/auth/token/revoke-self" >/dev/null 2>&1 || true
    fi
  done
  if [ -n "$ROOT_TOKEN" ] && [ -n "$BAO_API" ]; then
    curl -sS -o /dev/null -H "X-Vault-Token: $ROOT_TOKEN" -X POST "$BAO_API/v1/auth/token/revoke-self" >/dev/null 2>&1 || true
  fi
  if [ "$SUCCESS" != true ] && [ "$RESET_STARTED" = true ] && [ -n "$PILOT_VALUE" ]; then
    restore_pilot_only || true
  fi
  rm -rf "$TMP"
  rm -f "$TOKEN_FILE"
  unset PILOT_VALUE ROOT_TOKEN SHADOW_APP_TOKEN PILOT_APP_TOKEN PROD_APP_TOKEN ADMIN_TOKEN
  exit "$rc"
}
trap cleanup EXIT

[ "$(id -u)" -eq 0 ] || { echo "PROD_BOOTSTRAP_ROOT_REQUIRED" >&2; exit 321; }
[ -n "$EXPECTED_SHA" ] || { echo "PROD_BOOTSTRAP_EXPECTED_SHA_MISSING" >&2; exit 322; }
PILOT_VALUE="$(cat)"
[ -n "$PILOT_VALUE" ] || { echo "PROD_BOOTSTRAP_PILOT_TOKEN_MISSING" >&2; exit 323; }
PILOT_SHA="$(hash_text "$PILOT_VALUE")"
[ "$PILOT_SHA" = "$EXPECTED_SHA" ] || { echo "PROD_BOOTSTRAP_PILOT_HASH_MISMATCH" >&2; exit 324; }

RESET_STARTED=true
recreate_openbao

BAO_IP=""
HEALTH=""
for _ in $(seq 1 120); do
  BAO_IP="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' officev2-p3b-shadow-openbao 2>/dev/null || true)"
  if [ -n "$BAO_IP" ]; then
    HEALTH="$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 1 "http://$BAO_IP:8200/v1/sys/health" || true)"
    [ "$HEALTH" = 501 ] && break
  fi
  sleep .25
done
[ "$HEALTH" = 501 ] || { echo "PROD_BOOTSTRAP_OPENBAO_NOT_FRESH=$HEALTH" >&2; exit 325; }
BAO_API="http://$BAO_IP:8200"

INIT_HTTP="$(curl -sS -o "$TMP/init.json" -w '%{http_code}' -H 'Content-Type: application/json' -X PUT -d '{"secret_shares":1,"secret_threshold":1}' "$BAO_API/v1/sys/init" || true)"
[ "$INIT_HTTP" = 200 ] || { echo "PROD_BOOTSTRAP_INIT_FAIL=$INIT_HTTP" >&2; exit 326; }
readarray -t INIT_PARTS < <(python3 - "$TMP/init.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
keys=d.get("keys_base64") or d.get("keys") or []
print(keys[0] if keys else "")
print(d.get("root_token",""))
PY
)
UNSEAL="${INIT_PARTS[0]}"
ROOT_TOKEN="${INIT_PARTS[1]}"
[ -n "$UNSEAL" ] && [ -n "$ROOT_TOKEN" ] || { echo "PROD_BOOTSTRAP_INIT_MATERIAL_MISSING" >&2; exit 327; }
printf '%s' "$UNSEAL" >"$RUN/openbao-unseal.key"
chmod 0600 "$RUN/openbao-unseal.key"

UNSEAL_HTTP="$(curl -sS -o /dev/null -w '%{http_code}' -H 'Content-Type: application/json' -X PUT -d "$(python3 -c 'import json,sys; print(json.dumps({"key":sys.argv[1]}))' "$UNSEAL")" "$BAO_API/v1/sys/unseal" || true)"
[ "$UNSEAL_HTTP" = 200 ] || { echo "PROD_BOOTSTRAP_UNSEAL_FAIL=$UNSEAL_HTTP" >&2; exit 328; }
for _ in $(seq 1 40); do
  HEALTH="$(curl -sS -o /dev/null -w '%{http_code}' "$BAO_API/v1/sys/health" || true)"
  [ "$HEALTH" = 200 ] && break
  sleep .25
done
[ "$HEALTH" = 200 ] || { echo "PROD_BOOTSTRAP_ACTIVE_FAIL=$HEALTH" >&2; exit 329; }
RH=(-H "X-Vault-Token: $ROOT_TOKEN" -H 'Content-Type: application/json')

mount_http="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d '{"type":"kv","options":{"version":"2"}}' "$BAO_API/v1/sys/mounts/secret" || true)"
auth_http="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d '{"type":"approle"}' "$BAO_API/v1/sys/auth/approle" || true)"
[[ "$mount_http" =~ ^(200|204)$ ]] && [[ "$auth_http" =~ ^(200|204)$ ]] || { echo "PROD_BOOTSTRAP_MOUNTS_FAIL secret=$mount_http approle=$auth_http" >&2; exit 330; }

ALPHA="$(openssl rand -hex 24)"
ALPHA_SHA="$(hash_text "$ALPHA")"
write_alpha="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d "$(python3 -c 'import json,sys; print(json.dumps({"data":{"value":sys.argv[1]}}))' "$ALPHA")" "$BAO_API/v1/secret/data/alpha" || true)"
write_beta="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d '{"data":{"value":"synthetic-unrelated-shadow"}}' "$BAO_API/v1/secret/data/beta" || true)"
shadow_policy="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d '{"policy":"path \"secret/data/alpha\" { capabilities = [\"read\"] }"}' "$BAO_API/v1/sys/policies/acl/officev2-shadow-alpha" || true)"
shadow_role="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d '{"policies":"officev2-shadow-alpha","token_ttl":"5m","token_max_ttl":"10m","secret_id_ttl":"0"}' "$BAO_API/v1/auth/approle/role/officev2-shadow-health" || true)"
for code in "$write_alpha" "$write_beta" "$shadow_policy" "$shadow_role"; do [[ "$code" =~ ^(200|204)$ ]] || { echo "PROD_BOOTSTRAP_SHADOW_CONFIG_FAIL" >&2; exit 331; }; done
SHADOW_ROLE_ID="$(curl -fsS "${RH[@]}" "$BAO_API/v1/auth/approle/role/officev2-shadow-health/role-id" | python3 -c 'import json,sys; print((json.load(sys.stdin).get("data") or {}).get("role_id",""))')"
SHADOW_SECRET_ID="$(curl -fsS "${RH[@]}" -X POST "$BAO_API/v1/auth/approle/role/officev2-shadow-health/secret-id" | python3 -c 'import json,sys; print((json.load(sys.stdin).get("data") or {}).get("secret_id",""))')"
[ -n "$SHADOW_ROLE_ID" ] && [ -n "$SHADOW_SECRET_ID" ] || { echo "PROD_BOOTSTRAP_SHADOW_APPROLE_FAIL" >&2; exit 332; }
printf '%s' "$SHADOW_SECRET_ID" >"$RUN/openbao-approle-secret-id"; chmod 0600 "$RUN/openbao-approle-secret-id"
python3 - "$SHADOW_META" "$SHADOW_ROLE_ID" "$ALPHA_SHA" <<'PY'
import datetime,json,sys
out,role_id,alpha_sha=sys.argv[1:]
d={"schema":"velvetos.office-v2.phase3b-shadow-runtime-meta.v0","captured_at":datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z"),"status":"BOOTSTRAPPED","openbao_role_id":role_id,"expected_alpha_sha256":alpha_sha,"production_authority_change":False,"external_effects_allowed":False}
open(out,"w",encoding="utf-8").write(json.dumps(d,indent=2,sort_keys=True)+"\n")
PY
chmod 0644 "$SHADOW_META"

pilot_write="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d "$(python3 -c 'import json,sys; print(json.dumps({"data":{"value":sys.argv[1]}}))' "$PILOT_VALUE")" "$BAO_API/v1/secret/data/officev2-pilot/instagram-publisher-snapshot" || true)"
pilot_policy="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d '{"policy":"path \"secret/data/officev2-pilot/instagram-publisher-snapshot\" { capabilities = [\"read\"] }"}' "$BAO_API/v1/sys/policies/acl/officev2-pilot-publisher-snapshot" || true)"
pilot_role="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d '{"policies":"officev2-pilot-publisher-snapshot","token_ttl":"5m","token_max_ttl":"10m","secret_id_ttl":"0","secret_id_num_uses":0,"token_no_default_policy":true}' "$BAO_API/v1/auth/approle/role/officev2-pilot-publisher-snapshot" || true)"
for code in "$pilot_write" "$pilot_policy" "$pilot_role"; do [[ "$code" =~ ^(200|204)$ ]] || { echo "PROD_BOOTSTRAP_PILOT_CONFIG_FAIL" >&2; exit 333; }; done
PILOT_ROLE_ID="$(curl -fsS "${RH[@]}" "$BAO_API/v1/auth/approle/role/officev2-pilot-publisher-snapshot/role-id" | python3 -c 'import json,sys; print((json.load(sys.stdin).get("data") or {}).get("role_id",""))')"
PILOT_SECRET_ID="$(curl -fsS "${RH[@]}" -X POST "$BAO_API/v1/auth/approle/role/officev2-pilot-publisher-snapshot/secret-id" | python3 -c 'import json,sys; print((json.load(sys.stdin).get("data") or {}).get("secret_id",""))')"
[ -n "$PILOT_ROLE_ID" ] && [ -n "$PILOT_SECRET_ID" ] || { echo "PROD_BOOTSTRAP_PILOT_APPROLE_FAIL" >&2; exit 334; }
printf '%s' "$PILOT_SECRET_ID" >"$RUN/openbao-pilot-secret-id"; chmod 0600 "$RUN/openbao-pilot-secret-id"
python3 - "$PILOT_META" "$PILOT_ROLE_ID" "$PILOT_SHA" <<'PY'
import datetime,json,sys
out,role_id,sha=sys.argv[1:]
d={"schema":"velvetos.office-v2.phase3b-pilot-openbao-meta.v0","captured_at":datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z"),"status":"BOUND","scope_id":"instagram-publisher-snapshot-read","openbao_role_id":role_id,"credential_reference_sha256":sha,"exact_scope_read_http":200,"unrelated_scope_http":403,"raw_secret_recorded":False,"production_writer_change":False,"production_authority_change":False}
open(out,"w",encoding="utf-8").write(json.dumps(d,indent=2,sort_keys=True)+"\n")
PY
chmod 0644 "$PILOT_META"

prod_write="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d "$(python3 -c 'import json,sys; print(json.dumps({"data":{"value":sys.argv[1]}}))' "$PILOT_VALUE")" "$BAO_API/v1/secret/data/officev2-prod/instagram-publisher-snapshot" || true)"
prod_policy="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d '{"policy":"path \"secret/data/officev2-prod/instagram-publisher-snapshot\" { capabilities = [\"read\"] }"}' "$BAO_API/v1/sys/policies/acl/officev2-prod-publisher-snapshot" || true)"
prod_role="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d '{"policies":"officev2-prod-publisher-snapshot","token_ttl":"5m","token_max_ttl":"10m","secret_id_ttl":"0","secret_id_num_uses":0,"token_no_default_policy":true}' "$BAO_API/v1/auth/approle/role/officev2-prod-publisher-snapshot" || true)"
for code in "$prod_write" "$prod_policy" "$prod_role"; do [[ "$code" =~ ^(200|204)$ ]] || { echo "PROD_BOOTSTRAP_PROD_READ_CONFIG_FAIL" >&2; exit 335; }; done
PROD_ROLE_ID="$(curl -fsS "${RH[@]}" "$BAO_API/v1/auth/approle/role/officev2-prod-publisher-snapshot/role-id" | python3 -c 'import json,sys; print((json.load(sys.stdin).get("data") or {}).get("role_id",""))')"
PROD_SECRET_ID="$(curl -fsS "${RH[@]}" -X POST "$BAO_API/v1/auth/approle/role/officev2-prod-publisher-snapshot/secret-id" | python3 -c 'import json,sys; print((json.load(sys.stdin).get("data") or {}).get("secret_id",""))')"
[ -n "$PROD_ROLE_ID" ] && [ -n "$PROD_SECRET_ID" ] || { echo "PROD_BOOTSTRAP_PROD_READ_APPROLE_FAIL" >&2; exit 336; }

cat >"$TMP/admin-policy.hcl" <<'EOF'
path "secret/data/officev2-prod/instagram-publisher-snapshot" { capabilities = ["create","update","read"] }
path "secret/metadata/officev2-prod/instagram-publisher-snapshot" { capabilities = ["read","delete"] }
path "auth/approle/role/officev2-prod-publisher-snapshot" { capabilities = ["read","delete"] }
path "sys/policies/acl/officev2-prod-publisher-snapshot" { capabilities = ["read","delete"] }
path "auth/approle/role/officev2-prod-broker-admin" { capabilities = ["read","delete"] }
path "sys/policies/acl/officev2-prod-broker-admin" { capabilities = ["read","delete"] }
EOF
ADMIN_POLICY_JSON="$(python3 - "$TMP/admin-policy.hcl" <<'PY'
import json,sys
print(json.dumps({"policy":open(sys.argv[1]).read()}))
PY
)"
admin_policy="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d "$ADMIN_POLICY_JSON" "$BAO_API/v1/sys/policies/acl/officev2-prod-broker-admin" || true)"
admin_role="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d '{"policies":"officev2-prod-broker-admin","token_ttl":"5m","token_max_ttl":"10m","secret_id_ttl":"0","secret_id_num_uses":0,"token_no_default_policy":true}' "$BAO_API/v1/auth/approle/role/officev2-prod-broker-admin" || true)"
[[ "$admin_policy" =~ ^(200|204)$ ]] && [[ "$admin_role" =~ ^(200|204)$ ]] || { echo "PROD_BOOTSTRAP_ADMIN_CONFIG_FAIL policy=$admin_policy role=$admin_role" >&2; exit 337; }
ADMIN_ROLE_ID="$(curl -fsS "${RH[@]}" "$BAO_API/v1/auth/approle/role/officev2-prod-broker-admin/role-id" | python3 -c 'import json,sys; print((json.load(sys.stdin).get("data") or {}).get("role_id",""))')"
ADMIN_SECRET_ID="$(curl -fsS "${RH[@]}" -X POST "$BAO_API/v1/auth/approle/role/officev2-prod-broker-admin/secret-id" | python3 -c 'import json,sys; print((json.load(sys.stdin).get("data") or {}).get("secret_id",""))')"
[ -n "$ADMIN_ROLE_ID" ] && [ -n "$ADMIN_SECRET_ID" ] || { echo "PROD_BOOTSTRAP_ADMIN_APPROLE_FAIL" >&2; exit 338; }

login_token(){
  local role="$1" secret="$2" out="$3"
  python3 -c 'import json,sys; print(json.dumps({"role_id":sys.argv[1],"secret_id":sys.argv[2]}))' "$role" "$secret" |
    curl -fsS -H 'Content-Type: application/json' -X POST --data-binary @- "$BAO_API/v1/auth/approle/login" |
    python3 -c 'import json,sys; print((json.load(sys.stdin).get("auth") or {}).get("client_token",""))' >"$out"
}
login_token "$SHADOW_ROLE_ID" "$SHADOW_SECRET_ID" "$TMP/shadow-token"; SHADOW_APP_TOKEN="$(cat "$TMP/shadow-token")"
login_token "$PILOT_ROLE_ID" "$PILOT_SECRET_ID" "$TMP/pilot-token"; PILOT_APP_TOKEN="$(cat "$TMP/pilot-token")"
login_token "$PROD_ROLE_ID" "$PROD_SECRET_ID" "$TMP/prod-token"; PROD_APP_TOKEN="$(cat "$TMP/prod-token")"
login_token "$ADMIN_ROLE_ID" "$ADMIN_SECRET_ID" "$TMP/admin-token"; ADMIN_TOKEN="$(cat "$TMP/admin-token")"
[ -n "$SHADOW_APP_TOKEN" ] && [ -n "$PILOT_APP_TOKEN" ] && [ -n "$PROD_APP_TOKEN" ] && [ -n "$ADMIN_TOKEN" ] || { echo "PROD_BOOTSTRAP_LOGIN_FAIL" >&2; exit 339; }

shadow_exact="$(curl -sS -o "$TMP/shadow.json" -w '%{http_code}' -H "X-Vault-Token: $SHADOW_APP_TOKEN" "$BAO_API/v1/secret/data/alpha" || true)"
shadow_unrelated="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $SHADOW_APP_TOKEN" "$BAO_API/v1/secret/data/beta" || true)"
pilot_exact="$(curl -sS -o "$TMP/pilot.json" -w '%{http_code}' -H "X-Vault-Token: $PILOT_APP_TOKEN" "$BAO_API/v1/secret/data/officev2-pilot/instagram-publisher-snapshot" || true)"
pilot_unrelated="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $PILOT_APP_TOKEN" "$BAO_API/v1/secret/data/alpha" || true)"
prod_exact="$(curl -sS -o "$TMP/prod.json" -w '%{http_code}' -H "X-Vault-Token: $PROD_APP_TOKEN" "$BAO_API/v1/secret/data/officev2-prod/instagram-publisher-snapshot" || true)"
prod_unrelated="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $PROD_APP_TOKEN" "$BAO_API/v1/secret/data/alpha" || true)"
admin_write="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $ADMIN_TOKEN" -H 'Content-Type: application/json' -X POST -d "$(python3 -c 'import json,sys; print(json.dumps({"data":{"value":sys.argv[1]}}))' "$PILOT_VALUE")" "$BAO_API/v1/secret/data/officev2-prod/instagram-publisher-snapshot" || true)"
admin_unrelated="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $ADMIN_TOKEN" "$BAO_API/v1/secret/data/alpha" || true)"
MATCHES="$(python3 - "$TMP/shadow.json" "$ALPHA_SHA" "$TMP/pilot.json" "$PILOT_SHA" "$TMP/prod.json" "$PILOT_SHA" <<'PY'
import hashlib,json,sys
def value(p):
 d=json.load(open(p)); return ((d.get("data") or {}).get("data") or {}).get("value","")
print("|".join([
 str(hashlib.sha256(value(sys.argv[1]).encode()).hexdigest()==sys.argv[2]).lower(),
 str(hashlib.sha256(value(sys.argv[3]).encode()).hexdigest()==sys.argv[4]).lower(),
 str(hashlib.sha256(value(sys.argv[5]).encode()).hexdigest()==sys.argv[6]).lower(),
]))
PY
)"
IFS='|' read -r shadow_match pilot_match prod_match <<<"$MATCHES"
[ "$shadow_exact" = 200 ] && [ "$shadow_unrelated" = 403 ] && [ "$shadow_match" = true ] || { echo "PROD_BOOTSTRAP_SHADOW_SCOPE_FAIL" >&2; exit 340; }
[ "$pilot_exact" = 200 ] && [ "$pilot_unrelated" = 403 ] && [ "$pilot_match" = true ] || { echo "PROD_BOOTSTRAP_PILOT_SCOPE_FAIL" >&2; exit 341; }
[ "$prod_exact" = 200 ] && [ "$prod_unrelated" = 403 ] && [ "$prod_match" = true ] || { echo "PROD_BOOTSTRAP_PROD_SCOPE_FAIL" >&2; exit 342; }
[[ "$admin_write" =~ ^(200|204)$ ]] && [ "$admin_unrelated" = 403 ] || { echo "PROD_BOOTSTRAP_ADMIN_SCOPE_FAIL write=$admin_write unrelated=$admin_unrelated" >&2; exit 343; }

for tokvar in SHADOW_APP_TOKEN PILOT_APP_TOKEN PROD_APP_TOKEN ADMIN_TOKEN; do
  tok="${!tokvar}"
  if [ -n "$tok" ]; then curl -sS -o /dev/null -H "X-Vault-Token: $tok" -X POST "$BAO_API/v1/auth/token/revoke-self" >/dev/null 2>&1 || true; fi
  printf -v "$tokvar" '%s' ""
done

revoke_root="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $ROOT_TOKEN" -X POST "$BAO_API/v1/auth/token/revoke-self" || true)"
[[ "$revoke_root" =~ ^(200|204)$ ]] || { echo "PROD_BOOTSTRAP_ROOT_REVOKE_FAIL=$revoke_root" >&2; exit 344; }
root_after="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $ROOT_TOKEN" "$BAO_API/v1/auth/token/lookup-self" || true)"
[ "$root_after" = 403 ] || { echo "PROD_BOOTSTRAP_ROOT_REVOKE_PROOF_FAIL=$root_after" >&2; exit 345; }
ROOT_TOKEN=""

systemctl start officev2-phase3b-shadow-health.service >/dev/null
bash /var/officev2/artifacts/phase3b-security/shadow-health-once.sh >/dev/null
SUCCESS=true
RESET_STARTED=false

python3 - "$PROD_ROLE_ID" "$PROD_SECRET_ID" "$ADMIN_ROLE_ID" "$ADMIN_SECRET_ID" "$PILOT_SHA" "$admin_write" <<'PY'
import json,sys
print(json.dumps({
 "schema":"velvetos.office-v2.phase3b-production-openbao-bootstrap.v0",
 "status":"PASS",
 "read_role_id":sys.argv[1],
 "read_secret_id":sys.argv[2],
 "admin_role_id":sys.argv[3],
 "admin_secret_id":sys.argv[4],
 "credential_reference_sha256":sys.argv[5],
 "broker_path":"officev2-prod/data/instagram-publisher-snapshot",
 "broker_role":"officev2-prod-publisher-snapshot",
 "admin_role":"officev2-prod-broker-admin",
 "read_exact_scope_http":200,
 "read_unrelated_scope_http":403,
 "admin_write_http":int(sys.argv[6]),
 "admin_unrelated_scope_http":403,
 "root_token_persisted":False,
 "generated_root_revoked":True
},separators=(",",":")))
PY
