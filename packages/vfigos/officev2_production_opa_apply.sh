#!/usr/bin/env bash
set -Eeuo pipefail
SRC=/var/officev2/artifacts/phase3b-security/production-opa-policy.rego
DST=/opt/officev2-phase3b-shadow/opa-policy.rego
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
[ -s "$SRC" ] || { echo "PROD_OPA_POLICY_MISSING" >&2; exit 281; }
install -m 0644 "$SRC" "$DST"
systemctl restart officev2-phase3b-opa.service
OPA_IP=""
for _ in $(seq 1 60); do
  OPA_IP="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' officev2-p3b-shadow-opa 2>/dev/null || true)"
  [ -n "$OPA_IP" ] && [ "$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 1 "http://$OPA_IP:8181/health" 2>/dev/null || true)" = 200 ] && break
  sleep .5
done
[ -n "$OPA_IP" ] || { echo "PROD_OPA_NOT_READY" >&2; exit 282; }
probe(){
  local name="$1" principal="$2" action="$3" resource="$4" expected="$5"
  local body code result
  body="$(python3 -c 'import json,sys; print(json.dumps({"input":{"principal":sys.argv[1],"action":sys.argv[2],"resource":sys.argv[3]}}))' "$principal" "$action" "$resource")"
  code="$(printf '%s' "$body" | curl -sS -o "$TMP/$name.json" -w '%{http_code}' -H 'Content-Type: application/json' -X POST --data-binary @- "http://$OPA_IP:8181/v1/data/office/shadow/allow" || true)"
  result="$(python3 - "$TMP/$name.json" <<'PY'
import json,sys
try: print(str(json.load(open(sys.argv[1])).get("result") is True).lower())
except Exception: print("false")
PY
)"
  [ "$code" = 200 ] && [ "$result" = "$expected" ] || { echo "PROD_OPA_PROBE_FAIL name=$name http=$code result=$result expected=$expected" >&2; exit 283; }
}
probe prod_allow svc:officev2-p3b-prod-publisher-snapshot publisher.snapshot.read cloudflare:velvetos-instagram-publisher true
probe prod_write svc:officev2-p3b-prod-publisher-snapshot publisher.snapshot.write cloudflare:velvetos-instagram-publisher false
probe prod_wrong svc:officev2-p3b-prod-publisher-snapshot publisher.snapshot.read cloudflare:other false
probe pilot_allow svc:officev2-p3b-pilot-publisher-snapshot publisher.snapshot.read cloudflare:velvetos-instagram-publisher true
probe shadow_allow svc:shadow read secret:alpha true
probe anonymous anonymous publisher.snapshot.read cloudflare:velvetos-instagram-publisher false
printf 'PASS OPA production=ALLOW write=DENY wrong=DENY pilot=ALLOW shadow=ALLOW anonymous=DENY\n'
