#!/usr/bin/env bash
set -Eeuo pipefail
MODE="${1:-Init}"
case "$MODE" in Init|Rotate|Cleanup) ;; *) echo "PROD_OPENBAO_MODE_INVALID" >&2; exit 231;; esac

BASE=/opt/officev2-phase3b-prod
RUN=/run/officev2/phase3b
CONTAINER=officev2-p3b-prod-openbao
VOLUME=officev2_p3b_prod_bao
NETWORK=officev2-phase3b-shadow
SERVICE=officev2-phase3b-prod-openbao.service
UNIT=/etc/systemd/system/$SERVICE
CONFIG=$BASE/openbao.hcl
UNSEAL_FILE=$BASE/unseal.key
ROTATOR_FILE=$BASE/rotator.json
UNSEAL_HELPER=$BASE/openbao-unseal.sh
IMAGE='ghcr.io/openbao/openbao@sha256:a36ea8c27f0dcff5757664ad080425f96d3b6b2f33db3e76c4e2d3112fb17005'
READ_ROLE=officev2-prod-publisher-snapshot
ROTATOR_ROLE=officev2-prod-publisher-snapshot-rotator
SECRET_PATH=officev2-prod/instagram-publisher-snapshot
TMP="$(mktemp -d)"
ROOT_TOKEN=""
APP_TOKEN=""
ROTATOR_TOKEN=""
BAO_API=""
cleanup(){
  rc=$?
  set +e
  if [ -n "$APP_TOKEN" ] && [ -n "$BAO_API" ]; then
    curl -sS -o /dev/null -H "X-Vault-Token: $APP_TOKEN" -X POST "$BAO_API/v1/auth/token/revoke-self" >/dev/null 2>&1 || true
  fi
  if [ -n "$ROTATOR_TOKEN" ] && [ -n "$BAO_API" ]; then
    curl -sS -o /dev/null -H "X-Vault-Token: $ROTATOR_TOKEN" -X POST "$BAO_API/v1/auth/token/revoke-self" >/dev/null 2>&1 || true
  fi
  if [ -n "$ROOT_TOKEN" ] && [ -n "$BAO_API" ]; then
    curl -sS -o /dev/null -H "X-Vault-Token: $ROOT_TOKEN" -X POST "$BAO_API/v1/auth/token/revoke-self" >/dev/null 2>&1 || true
  fi
  rm -rf "$TMP"
  unset INPUT PROVIDER_TOKEN ROOT_TOKEN APP_TOKEN ROTATOR_TOKEN UNSEAL_KEY READ_SECRET_ID ROTATOR_SECRET_ID
  exit "$rc"
}
trap cleanup EXIT

cip(){ docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$1" 2>/dev/null || true; }
wait_health(){
  local want="$1" ip="" code=""
  for _ in $(seq 1 100); do
    ip="$(cip "$CONTAINER")"
    if [ -n "$ip" ]; then
      code="$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 1 "http://$ip:8200/v1/sys/health" 2>/dev/null || true)"
      [ "$code" = "$want" ] && { printf '%s' "$ip"; return 0; }
    fi
    sleep .25
  done
  return 1
}
install_runtime(){
  install -d -m 0700 "$BASE"
  cat >"$CONFIG" <<'HCL'
ui = false

storage "raft" {
  path = "/openbao/data"
  node_id = "officev2-prod-node-1"
}

listener "tcp" {
  address = "0.0.0.0:8200"
  tls_disable = true
}

api_addr = "http://prod-openbao:8200"
cluster_addr = "http://prod-openbao:8201"
HCL
  # The config contains no secret material; OpenBao may drop privileges before reading it.
  # Keep it world-readable but root-owned while secrets remain in dedicated 0600 files.
  chmod 0644 "$CONFIG"
  cat >"$UNSEAL_HELPER" <<'SH'
#!/usr/bin/env bash
set -Eeuo pipefail
C=officev2-p3b-prod-openbao
KEY=/opt/officev2-phase3b-prod/unseal.key
for _ in $(seq 1 100); do
  ip="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$C" 2>/dev/null || true)"
  if [ -n "$ip" ]; then
    h="$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 1 "http://$ip:8200/v1/sys/health" 2>/dev/null || true)"
    case "$h" in
      200|501) exit 0 ;;
      503)
        [ -s "$KEY" ] || exit 0
        key="$(cat "$KEY")"
        code="$(curl -sS -o /dev/null -w '%{http_code}' -H 'Content-Type: application/json' -X PUT -d "$(python3 -c 'import json,sys; print(json.dumps({"key":sys.argv[1]}))' "$key")" "http://$ip:8200/v1/sys/unseal" || true)"
        unset key
        [ "$code" = 200 ] || exit 1
        exit 0
        ;;
    esac
  fi
  sleep .25
done
exit 1
SH
  chmod 0700 "$UNSEAL_HELPER"
  cat >"$UNIT" <<EOF
[Unit]
Description=Office v2 Phase3B Production Read OpenBao
After=docker.service officev2-phase3b-openbao.service
Requires=docker.service
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=simple
ExecStartPre=-/usr/bin/docker rm -f $CONTAINER
ExecStart=/usr/bin/docker run --rm --name $CONTAINER --network $NETWORK --hostname prod-openbao --user root -v $VOLUME:/openbao/data -v $CONFIG:/tmp/officev2-prod-bao.hcl:ro $IMAGE server -config=/tmp/officev2-prod-bao.hcl
ExecStartPost=$UNSEAL_HELPER
ExecStop=-/usr/bin/docker stop -t 15 $CONTAINER
Restart=on-failure
RestartSec=5

[Install]
WantedBy=officev2-phase3b-shadow.target
EOF
  systemctl daemon-reload
}

if [ "$MODE" = Cleanup ]; then
  systemctl disable --now "$SERVICE" >/dev/null 2>&1 || true
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  docker volume rm "$VOLUME" >/dev/null 2>&1 || true
  rm -rf "$BASE"
  rm -f "$UNIT"
  systemctl daemon-reload
  printf '{"schema":"velvetos.office-v2.phase3b-production-openbao-cleanup.v1","status":"PASS","container":"%s","volume":"%s","production_writer_change":false}\n' "$CONTAINER" "$VOLUME"
  exit 0
fi

if [ "$MODE" = Init ]; then
  [ ! -e "$UNIT" ] || { echo "PROD_OPENBAO_ALREADY_CONFIGURED" >&2; exit 232; }
  docker volume inspect "$VOLUME" >/dev/null 2>&1 && { echo "PROD_OPENBAO_VOLUME_ALREADY_EXISTS" >&2; exit 233; }
  PROVIDER_TOKEN="$(cat)"
  [ -n "$PROVIDER_TOKEN" ] || { echo "PROD_OPENBAO_PROVIDER_TOKEN_MISSING" >&2; exit 234; }
  PROVIDER_SHA="$(printf '%s' "$PROVIDER_TOKEN" | sha256sum | awk '{print $1}')"

  install_runtime
  docker volume create "$VOLUME" >/dev/null
  # OpenBao's image entrypoint drops to uid 100 / gid 1000 even when Docker starts as root.
  # Prepare the fresh isolated volume for that runtime identity before first boot.
  docker run --rm --user root -v "$VOLUME:/openbao/data" --entrypoint sh "$IMAGE" -lc 'chown 100:1000 /openbao/data && chmod 0700 /openbao/data' >/dev/null
  systemctl enable "$SERVICE" >/dev/null
  systemctl start "$SERVICE"
  BAO_IP="$(wait_health 501)" || { echo "PROD_OPENBAO_INIT_HEALTH_TIMEOUT" >&2; exit 235; }
  BAO_API="http://$BAO_IP:8200"

  INIT_HTTP="$(curl -sS -o "$TMP/init.json" -w '%{http_code}' -H 'Content-Type: application/json' -X PUT -d '{"secret_shares":1,"secret_threshold":1}' "$BAO_API/v1/sys/init" || true)"
  [ "$INIT_HTTP" = 200 ] || { echo "PROD_OPENBAO_INIT_FAIL=$INIT_HTTP" >&2; exit 236; }
  readarray -t INIT_PARTS < <(python3 - "$TMP/init.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
keys=d.get("keys_base64") or d.get("keys") or []
print(keys[0] if keys else "")
print(d.get("root_token",""))
PY
)
  UNSEAL_KEY="${INIT_PARTS[0]}"; ROOT_TOKEN="${INIT_PARTS[1]}"
  [ -n "$UNSEAL_KEY" ] && [ -n "$ROOT_TOKEN" ] || { echo "PROD_OPENBAO_INIT_MATERIAL_MISSING" >&2; exit 237; }
  printf '%s' "$UNSEAL_KEY" >"$UNSEAL_FILE"
  chmod 0600 "$UNSEAL_FILE"

  UNSEAL_HTTP="$(curl -sS -o /dev/null -w '%{http_code}' -H 'Content-Type: application/json' -X PUT -d "$(python3 -c 'import json,sys; print(json.dumps({"key":sys.argv[1]}))' "$UNSEAL_KEY")" "$BAO_API/v1/sys/unseal" || true)"
  [ "$UNSEAL_HTTP" = 200 ] || { echo "PROD_OPENBAO_UNSEAL_FAIL=$UNSEAL_HTTP" >&2; exit 238; }
  BAO_IP="$(wait_health 200)" || { echo "PROD_OPENBAO_ACTIVE_TIMEOUT" >&2; exit 239; }
  BAO_API="http://$BAO_IP:8200"
  RH=(-H "X-Vault-Token: $ROOT_TOKEN" -H 'Content-Type: application/json')

  mount_http="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d '{"type":"kv","options":{"version":"2"}}' "$BAO_API/v1/sys/mounts/secret" || true)"
  auth_http="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d '{"type":"approle"}' "$BAO_API/v1/sys/auth/approle" || true)"
  [[ "$mount_http" =~ ^(200|204)$ ]] && [[ "$auth_http" =~ ^(200|204)$ ]] || { echo "PROD_OPENBAO_BOOTSTRAP_FAIL mount=$mount_http auth=$auth_http" >&2; exit 240; }

  write_http="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d "$(python3 -c 'import json,sys; print(json.dumps({"data":{"value":sys.argv[1]}}))' "$PROVIDER_TOKEN")" "$BAO_API/v1/secret/data/$SECRET_PATH" || true)"
  read_policy="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d '{"policy":"path \"secret/data/officev2-prod/instagram-publisher-snapshot\" { capabilities = [\"read\"] }"}' "$BAO_API/v1/sys/policies/acl/$READ_ROLE" || true)"
  read_role="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d '{"policies":"officev2-prod-publisher-snapshot","token_ttl":"5m","token_max_ttl":"10m","secret_id_ttl":"0","secret_id_num_uses":0,"token_no_default_policy":true}' "$BAO_API/v1/auth/approle/role/$READ_ROLE" || true)"
  rot_policy="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d '{"policy":"path \"secret/data/officev2-prod/instagram-publisher-snapshot\" { capabilities = [\"create\",\"update\",\"read\"] }"}' "$BAO_API/v1/sys/policies/acl/$ROTATOR_ROLE" || true)"
  rot_role="$(curl -sS -o /dev/null -w '%{http_code}' "${RH[@]}" -X POST -d '{"policies":"officev2-prod-publisher-snapshot-rotator","token_ttl":"2m","token_max_ttl":"5m","secret_id_ttl":"0","secret_id_num_uses":0,"token_no_default_policy":true}' "$BAO_API/v1/auth/approle/role/$ROTATOR_ROLE" || true)"
  for code in "$write_http" "$read_policy" "$read_role" "$rot_policy" "$rot_role"; do [[ "$code" =~ ^(200|204)$ ]] || { echo "PROD_OPENBAO_SCOPE_CONFIG_FAIL" >&2; exit 241; }; done

  READ_ROLE_ID="$(curl -fsS "${RH[@]}" "$BAO_API/v1/auth/approle/role/$READ_ROLE/role-id" | python3 -c 'import json,sys; print((json.load(sys.stdin).get("data") or {}).get("role_id",""))')"
  READ_SECRET_ID="$(curl -fsS "${RH[@]}" -X POST "$BAO_API/v1/auth/approle/role/$READ_ROLE/secret-id" | python3 -c 'import json,sys; print((json.load(sys.stdin).get("data") or {}).get("secret_id",""))')"
  ROTATOR_ROLE_ID="$(curl -fsS "${RH[@]}" "$BAO_API/v1/auth/approle/role/$ROTATOR_ROLE/role-id" | python3 -c 'import json,sys; print((json.load(sys.stdin).get("data") or {}).get("role_id",""))')"
  ROTATOR_SECRET_ID="$(curl -fsS "${RH[@]}" -X POST "$BAO_API/v1/auth/approle/role/$ROTATOR_ROLE/secret-id" | python3 -c 'import json,sys; print((json.load(sys.stdin).get("data") or {}).get("secret_id",""))')"
  [ -n "$READ_ROLE_ID" ] && [ -n "$READ_SECRET_ID" ] && [ -n "$ROTATOR_ROLE_ID" ] && [ -n "$ROTATOR_SECRET_ID" ] || { echo "PROD_OPENBAO_APPROLE_MATERIAL_MISSING" >&2; exit 242; }
  python3 - "$ROTATOR_FILE" "$ROTATOR_ROLE_ID" "$ROTATOR_SECRET_ID" <<'PY'
import json,sys
open(sys.argv[1],"w",encoding="utf-8").write(json.dumps({"role_id":sys.argv[2],"secret_id":sys.argv[3]},separators=(",",":"))+"\n")
PY
  chmod 0600 "$ROTATOR_FILE"

  LOGIN="$(python3 -c 'import json,sys; print(json.dumps({"role_id":sys.argv[1],"secret_id":sys.argv[2]}))' "$READ_ROLE_ID" "$READ_SECRET_ID")"
  LOGIN_HTTP="$(printf '%s' "$LOGIN" | curl -sS -o "$TMP/login.json" -w '%{http_code}' -H 'Content-Type: application/json' -X POST --data-binary @- "$BAO_API/v1/auth/approle/login" || true)"
  [ "$LOGIN_HTTP" = 200 ] || { echo "PROD_OPENBAO_READ_LOGIN_FAIL=$LOGIN_HTTP" >&2; exit 243; }
  APP_TOKEN="$(python3 -c 'import json,sys; print((json.load(open(sys.argv[1])).get("auth") or {}).get("client_token",""))' "$TMP/login.json")"
  EXACT_HTTP="$(curl -sS -o "$TMP/exact.json" -w '%{http_code}' -H "X-Vault-Token: $APP_TOKEN" "$BAO_API/v1/secret/data/$SECRET_PATH" || true)"
  UNRELATED_HTTP="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $APP_TOKEN" "$BAO_API/v1/secret/data/unrelated" || true)"
  MATCH="$(python3 - "$TMP/exact.json" "$PROVIDER_SHA" <<'PY'
import hashlib,json,sys
try:
 d=json.load(open(sys.argv[1])); v=((d.get("data") or {}).get("data") or {}).get("value","")
 print(str(hashlib.sha256(v.encode()).hexdigest()==sys.argv[2]).lower())
except Exception: print("false")
PY
)"
  [ "$EXACT_HTTP" = 200 ] && [ "$UNRELATED_HTTP" = 403 ] && [ "$MATCH" = true ] || { echo "PROD_OPENBAO_SCOPE_PROOF_FAIL exact=$EXACT_HTTP unrelated=$UNRELATED_HTTP match=$MATCH" >&2; exit 244; }

  revoke="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $ROOT_TOKEN" -X POST "$BAO_API/v1/auth/token/revoke-self" || true)"
  [[ "$revoke" =~ ^(200|204)$ ]] || { echo "PROD_OPENBAO_ROOT_REVOKE_FAIL=$revoke" >&2; exit 245; }
  root_after="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $ROOT_TOKEN" "$BAO_API/v1/auth/token/lookup-self" || true)"
  ROOT_TOKEN=""
  [ "$root_after" = 403 ] || { echo "PROD_OPENBAO_ROOT_REVOKE_PROOF_FAIL=$root_after" >&2; exit 246; }

  python3 - "$READ_ROLE_ID" "$READ_SECRET_ID" "$ROTATOR_ROLE_ID" "$ROTATOR_SECRET_ID" "$PROVIDER_SHA" <<'PY'
import json,sys
print(json.dumps({
 "schema":"velvetos.office-v2.phase3b-production-openbao-bundle.v1",
 "role_id":sys.argv[1],"secret_id":sys.argv[2],
 "rotator_role_id":sys.argv[3],"rotator_secret_id":sys.argv[4],
 "credential_reference_sha256":sys.argv[5],
 "broker_path":"officev2-prod/data/instagram-publisher-snapshot",
 "broker_role":"officev2-prod-publisher-snapshot",
 "rotator_role":"officev2-prod-publisher-snapshot-rotator",
 "broker_instance":"officev2-p3b-prod-openbao",
 "broker_volume":"officev2_p3b_prod_bao",
 "root_revoked":True,"root_token_persisted":False,
 "unseal_key_storage":"runtime_root_only"
},separators=(",",":")))
PY
  exit 0
fi

# Rotate: stdin is a small in-memory JSON object containing the new provider value
# and the scoped rotator AppRole material. No root/admin token is used.
INPUT="$(cat)"
if printf '%s' "$INPUT" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert isinstance(d,dict) and d.get("provider_token")' >/dev/null 2>&1; then
  readarray -t PARTS < <(printf '%s' "$INPUT" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("provider_token","")); print(d.get("rotator_role_id","")); print(d.get("rotator_secret_id",""))')
  PROVIDER_TOKEN="${PARTS[0]}"; ROTATOR_ROLE_ID="${PARTS[1]}"; ROTATOR_SECRET_ID="${PARTS[2]}"
else
  PROVIDER_TOKEN="$INPUT"
  [ -s "$ROTATOR_FILE" ] || { echo "PROD_OPENBAO_ROTATOR_FILE_MISSING" >&2; exit 247; }
  readarray -t PARTS < <(python3 - "$ROTATOR_FILE" <<'PY'
import json,sys
d=json.load(open(sys.argv[1],encoding='utf-8'))
print(d.get('role_id','')); print(d.get('secret_id',''))
PY
)
  ROTATOR_ROLE_ID="${PARTS[0]}"; ROTATOR_SECRET_ID="${PARTS[1]}"
fi
[ -n "$PROVIDER_TOKEN" ] && [ -n "$ROTATOR_ROLE_ID" ] && [ -n "$ROTATOR_SECRET_ID" ] || { echo "PROD_OPENBAO_ROTATE_INPUT_INVALID" >&2; exit 247; }
PROVIDER_SHA="$(printf '%s' "$PROVIDER_TOKEN" | sha256sum | awk '{print $1}')"
BAO_IP="$(cip "$CONTAINER")"
[ -n "$BAO_IP" ] || { echo "PROD_OPENBAO_PROD_INSTANCE_MISSING" >&2; exit 248; }
BAO_API="http://$BAO_IP:8200"
HEALTH="$(curl -sS -o /dev/null -w '%{http_code}' "$BAO_API/v1/sys/health" || true)"
[ "$HEALTH" = 200 ] || { echo "PROD_OPENBAO_PROD_INSTANCE_NOT_ACTIVE=$HEALTH" >&2; exit 249; }

LOGIN="$(python3 -c 'import json,sys; print(json.dumps({"role_id":sys.argv[1],"secret_id":sys.argv[2]}))' "$ROTATOR_ROLE_ID" "$ROTATOR_SECRET_ID")"
LOGIN_HTTP="$(printf '%s' "$LOGIN" | curl -sS -o "$TMP/rot-login.json" -w '%{http_code}' -H 'Content-Type: application/json' -X POST --data-binary @- "$BAO_API/v1/auth/approle/login" || true)"
[ "$LOGIN_HTTP" = 200 ] || { echo "PROD_OPENBAO_ROTATOR_LOGIN_FAIL=$LOGIN_HTTP" >&2; exit 250; }
ROTATOR_TOKEN="$(python3 -c 'import json,sys; print((json.load(open(sys.argv[1])).get("auth") or {}).get("client_token",""))' "$TMP/rot-login.json")"
[ -n "$ROTATOR_TOKEN" ] || { echo "PROD_OPENBAO_ROTATOR_TOKEN_MISSING" >&2; exit 251; }
write_http="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $ROTATOR_TOKEN" -H 'Content-Type: application/json' -X POST -d "$(python3 -c 'import json,sys; print(json.dumps({"data":{"value":sys.argv[1]}}))' "$PROVIDER_TOKEN")" "$BAO_API/v1/secret/data/$SECRET_PATH" || true)"
[[ "$write_http" =~ ^(200|204)$ ]] || { echo "PROD_OPENBAO_ROTATOR_WRITE_FAIL=$write_http" >&2; exit 252; }
read_http="$(curl -sS -o "$TMP/rot-read.json" -w '%{http_code}' -H "X-Vault-Token: $ROTATOR_TOKEN" "$BAO_API/v1/secret/data/$SECRET_PATH" || true)"
MATCH="$(python3 - "$TMP/rot-read.json" "$PROVIDER_SHA" <<'PY'
import hashlib,json,sys
try:
 d=json.load(open(sys.argv[1])); v=((d.get("data") or {}).get("data") or {}).get("value","")
 print(str(hashlib.sha256(v.encode()).hexdigest()==sys.argv[2]).lower())
except Exception: print("false")
PY
)"
[ "$read_http" = 200 ] && [ "$MATCH" = true ] || { echo "PROD_OPENBAO_ROTATOR_READBACK_FAIL read=$read_http match=$MATCH" >&2; exit 253; }
printf '{"schema":"velvetos.office-v2.phase3b-production-openbao-rotate.v1","status":"PASS","credential_reference_sha256":"%s","broker_instance":"%s","rotator_role":"%s","root_used":false,"root_revoked":true,"root_token_persisted":false}\n' "$PROVIDER_SHA" "$CONTAINER" "$ROTATOR_ROLE"
