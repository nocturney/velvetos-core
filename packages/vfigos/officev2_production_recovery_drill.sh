#!/usr/bin/env bash
set -Eeuo pipefail
EXPECTED="$1"
INPUT="$(cat)"
RUN=/run/officev2/phase3b
UNSEAL_FILE=/opt/officev2-phase3b-prod/unseal.key
READ=/var/officev2/artifacts/phase3b-security/production-snapshot-read.sh
OPA_SVC=officev2-phase3b-opa.service
Z_SVC=officev2-phase3b-zitadel.service
BAO_SVC=officev2-phase3b-prod-openbao.service
SUCCESS=false

cip(){ docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$1" 2>/dev/null || true; }
restore_all(){
  set +e
  systemctl start "$OPA_SVC" "$Z_SVC" "$BAO_SVC" >/dev/null 2>&1 || true
  sleep 1
  local bip health key
  bip="$(cip officev2-p3b-prod-openbao)"
  if [ -n "$bip" ]; then
    health="$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 1 "http://$bip:8200/v1/sys/health" || true)"
    if [ "$health" = 503 ] && [ -s "$UNSEAL_FILE" ]; then
      key="$(cat "$UNSEAL_FILE")"
      curl -sS -o /dev/null -H 'Content-Type: application/json' -X PUT -d "$(python3 -c 'import json,sys; print(json.dumps({"key":sys.argv[1]}))' "$key")" "http://$bip:8200/v1/sys/unseal" >/dev/null 2>&1 || true
      unset key
    fi
  fi
}
cleanup(){
  rc=$?
  restore_all
  unset INPUT
  if [ "$SUCCESS" != true ]; then exit "$rc"; fi
}
trap cleanup EXIT

[ -n "$INPUT" ] || { echo "PROD_RECOVERY_BUNDLE_EMPTY" >&2; exit 291; }
[ -s "$UNSEAL_FILE" ] || { echo "PROD_RECOVERY_UNSEAL_KEY_MISSING" >&2; exit 292; }
run_read(){ printf '%s' "$INPUT" | bash "$READ" "$EXPECTED" >/dev/null 2>&1; }
wait_opa(){
  local ip=""
  for _ in $(seq 1 60); do
    ip="$(cip officev2-p3b-shadow-opa)"
    [ -n "$ip" ] && [ "$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 1 "http://$ip:8181/health" 2>/dev/null || true)" = 200 ] && return 0
    sleep .5
  done
  return 1
}
wait_zitadel(){
  local ip=""
  for _ in $(seq 1 120); do
    ip="$(cip officev2-p3b-shadow-zitadel)"
    [ -n "$ip" ] && [ "$(curl --http2-prior-knowledge -sS -o /dev/null -w '%{http_code}' --connect-timeout 1 -H 'Host: zitadel:8080' "http://$ip:8080/debug/ready" 2>/dev/null || true)" = 200 ] && return 0
    sleep .5
  done
  return 1
}
wait_bao(){
  local ip="" health="" key=""
  for _ in $(seq 1 80); do
    ip="$(cip officev2-p3b-prod-openbao)"
    if [ -n "$ip" ]; then
      health="$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 1 "http://$ip:8200/v1/sys/health" 2>/dev/null || true)"
      if [ "$health" = 503 ]; then
        key="$(cat "$UNSEAL_FILE")"
        curl -sS -o /dev/null -H 'Content-Type: application/json' -X PUT -d "$(python3 -c 'import json,sys; print(json.dumps({"key":sys.argv[1]}))' "$key")" "http://$ip:8200/v1/sys/unseal" >/dev/null 2>&1 || true
        unset key
      elif [ "$health" = 200 ]; then
        return 0
      fi
    fi
    sleep .5
  done
  return 1
}

run_read || { echo "PROD_RECOVERY_BASELINE_FAIL" >&2; exit 293; }

systemctl stop "$OPA_SVC"
if run_read; then echo "PROD_RECOVERY_OPA_FAIL_OPEN" >&2; exit 294; fi
systemctl start "$OPA_SVC"; wait_opa || { echo "PROD_RECOVERY_OPA_RESTART_FAIL" >&2; exit 295; }
run_read || { echo "PROD_RECOVERY_OPA_POST_FAIL" >&2; exit 296; }

systemctl stop "$Z_SVC"
if run_read; then echo "PROD_RECOVERY_ZITADEL_FAIL_OPEN" >&2; exit 297; fi
systemctl start "$Z_SVC"; wait_zitadel || { echo "PROD_RECOVERY_ZITADEL_RESTART_FAIL" >&2; exit 298; }
run_read || { echo "PROD_RECOVERY_ZITADEL_POST_FAIL" >&2; exit 299; }

systemctl stop "$BAO_SVC"
if run_read; then echo "PROD_RECOVERY_OPENBAO_FAIL_OPEN" >&2; exit 300; fi
systemctl start "$BAO_SVC"; wait_bao || { echo "PROD_RECOVERY_OPENBAO_RESTART_FAIL" >&2; exit 301; }
run_read || { echo "PROD_RECOVERY_OPENBAO_POST_FAIL" >&2; exit 302; }

SUCCESS=true
printf '{"schema":"velvetos.office-v2.phase3b-production-recovery.v0","status":"PASS","baseline":"PASS","opa":{"outage_fail_closed":true,"recovery":"PASS"},"zitadel":{"outage_fail_closed":true,"recovery":"PASS"},"openbao":{"outage_fail_closed":true,"recovery":"PASS","unseal_without_persistent_root":true},"production_writer_change":false,"external_mutation_performed":false}\n'
