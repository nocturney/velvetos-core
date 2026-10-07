#!/usr/bin/env bash
set -Eeuo pipefail
TMP="$(mktemp -d)"
RUN=/run/officev2/phase3b
KEYFILE="$RUN/zitadel-admin-sa.json"
MACHINE_ID=""
ADMIN_TOKEN=""
SUCCESS=false
cleanup(){
  rc=$?
  set +e
  if [ "$SUCCESS" != true ] && [ -n "$MACHINE_ID" ] && [ -n "$ADMIN_TOKEN" ] && [ -n "${Z_IP:-}" ]; then
    curl --http2-prior-knowledge -sS -o /dev/null -H 'Host: zitadel:8080' -H "Authorization: Bearer $ADMIN_TOKEN" -X DELETE "http://$Z_IP:8080/v2/users/$MACHINE_ID" >/dev/null 2>&1 || true
  fi
  rm -rf "$TMP"
  unset ADMIN_TOKEN CLIENT_SECRET CLIENT_TOKEN ASSERTION
  exit "$rc"
}
trap cleanup EXIT

[ -s "$KEYFILE" ] || { echo "PROD_ZITADEL_ADMIN_KEY_MISSING" >&2; exit 201; }
Z_IP="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' officev2-p3b-shadow-zitadel 2>/dev/null || true)"
[ -n "$Z_IP" ] || { echo "PROD_ZITADEL_IP_MISSING" >&2; exit 202; }
READY="$(curl --http2-prior-knowledge -sS -o /dev/null -w '%{http_code}' -H 'Host: zitadel:8080' "http://$Z_IP:8080/debug/ready" || true)"
[ "$READY" = 200 ] || { echo "PROD_ZITADEL_NOT_READY=$READY" >&2; exit 203; }

python3 - "$KEYFILE" "$TMP/admin.pem" "$TMP/admin.meta" <<'PY'
import json,sys
d=json.load(open(sys.argv[1],encoding='utf-8'))
open(sys.argv[2],'w',encoding='utf-8').write(d['key'])
open(sys.argv[3],'w',encoding='utf-8').write(d['keyId']+'\n'+d['userId']+'\n')
PY
chmod 0600 "$TMP/admin.pem"
KEY_ID="$(sed -n '1p' "$TMP/admin.meta")"
USER_ID="$(sed -n '2p' "$TMP/admin.meta")"
b64url(){ python3 -c 'import sys,base64; print(base64.urlsafe_b64encode(sys.stdin.buffer.read()).decode().rstrip("="))'; }
NOW="$(date +%s)"; EXP="$((NOW+300))"
HEADER="$(printf '{"alg":"RS256","kid":"%s"}' "$KEY_ID" | b64url)"
PAYLOAD="$(printf '{"iss":"%s","sub":"%s","aud":"http://zitadel:8080","iat":%s,"exp":%s}' "$USER_ID" "$USER_ID" "$NOW" "$EXP" | b64url)"
SIGNING="$HEADER.$PAYLOAD"
SIG="$(printf '%s' "$SIGNING" | openssl dgst -sha256 -sign "$TMP/admin.pem" -binary | b64url)"
ASSERTION="$SIGNING.$SIG"
ADMIN_HTTP="$(curl --http2-prior-knowledge -sS -o "$TMP/admin-token.json" -w '%{http_code}' -H 'Host: zitadel:8080' -H 'Content-Type: application/x-www-form-urlencoded' -X POST "http://$Z_IP:8080/oauth/v2/token" --data-urlencode 'grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer' --data-urlencode 'scope=openid profile urn:zitadel:iam:org:project:id:zitadel:aud' --data-urlencode "assertion=$ASSERTION" || true)"
[ "$ADMIN_HTTP" = 200 ] || { echo "PROD_ZITADEL_ADMIN_TOKEN_FAIL=$ADMIN_HTTP" >&2; exit 204; }
ADMIN_TOKEN="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["access_token"])' "$TMP/admin-token.json")"
READ_ADMIN="$(curl --http2-prior-knowledge -sS -o "$TMP/admin-user.json" -w '%{http_code}' -H 'Host: zitadel:8080' -H "Authorization: Bearer $ADMIN_TOKEN" "http://$Z_IP:8080/v2/users/$USER_ID" || true)"
[ "$READ_ADMIN" = 200 ] || { echo "PROD_ZITADEL_ADMIN_READ_FAIL=$READ_ADMIN" >&2; exit 205; }
ORG_ID="$(python3 - "$TMP/admin-user.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
print((d.get('details') or {}).get('resourceOwner') or ((d.get('user') or {}).get('details') or {}).get('resourceOwner') or '')
PY
)"
[ -n "$ORG_ID" ] || { echo "PROD_ZITADEL_ORG_MISSING" >&2; exit 206; }

MACHINE_USER="officev2-p3b-prod-publisher-snapshot-$(date +%s)-$RANDOM"
CREATE_HTTP="$(curl --http2-prior-knowledge -sS -o "$TMP/machine.json" -w '%{http_code}' -H 'Host: zitadel:8080' -H 'Content-Type: application/json' -H "Authorization: Bearer $ADMIN_TOKEN" -X POST "http://$Z_IP:8080/v2/users/new" -d "{\"organizationId\":\"$ORG_ID\",\"username\":\"$MACHINE_USER\",\"machine\":{\"name\":\"OfficeV2 Phase3B Production Publisher Snapshot\",\"description\":\"Persistent bounded production read identity\",\"accessTokenType\":\"ACCESS_TOKEN_TYPE_BEARER\"}}" || true)"
[ "$CREATE_HTTP" = 200 ] || { echo "PROD_ZITADEL_CREATE_FAIL=$CREATE_HTTP" >&2; exit 207; }
MACHINE_ID="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["id"])' "$TMP/machine.json")"
READBACK_HTTP="$(curl --http2-prior-knowledge -sS -o "$TMP/readback.json" -w '%{http_code}' -H 'Host: zitadel:8080' -H "Authorization: Bearer $ADMIN_TOKEN" "http://$Z_IP:8080/v2/users/$MACHINE_ID" || true)"
[ "$READBACK_HTTP" = 200 ] || { echo "PROD_ZITADEL_READBACK_FAIL=$READBACK_HTTP" >&2; exit 208; }
SECRET_HTTP="$(curl --http2-prior-knowledge -sS -o "$TMP/secret.json" -w '%{http_code}' -H 'Host: zitadel:8080' -H "Authorization: Bearer $ADMIN_TOKEN" -X POST "http://$Z_IP:8080/v2/users/$MACHINE_ID/secret" || true)"
[ "$SECRET_HTTP" = 200 ] || { echo "PROD_ZITADEL_SECRET_FAIL=$SECRET_HTTP" >&2; exit 209; }
CLIENT_SECRET="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["clientSecret"])' "$TMP/secret.json")"

TOKEN_HTTP=0
for i in $(seq 1 15); do
  TOKEN_HTTP="$(curl --http2-prior-knowledge -sS -o "$TMP/client-token.json" -w '%{http_code}' -H 'Host: zitadel:8080' -H 'Content-Type: application/x-www-form-urlencoded' -u "$MACHINE_USER:$CLIENT_SECRET" -X POST "http://$Z_IP:8080/oauth/v2/token" --data-urlencode 'grant_type=client_credentials' --data-urlencode 'scope=openid profile' || true)"
  [ "$TOKEN_HTTP" = 200 ] && break
  sleep 1
done
[ "$TOKEN_HTTP" = 200 ] || { echo "PROD_ZITADEL_CLIENT_TOKEN_FAIL=$TOKEN_HTTP" >&2; exit 210; }
CLIENT_TOKEN="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["access_token"])' "$TMP/client-token.json")"
[ -n "$CLIENT_TOKEN" ] || { echo "PROD_ZITADEL_CLIENT_TOKEN_EMPTY" >&2; exit 211; }
WRONG_HTTP="$(curl --http2-prior-knowledge -sS -o /dev/null -w '%{http_code}' -H 'Host: zitadel:8080' -H 'Content-Type: application/x-www-form-urlencoded' -u "$MACHINE_USER:wrong-$CLIENT_SECRET" -X POST "http://$Z_IP:8080/oauth/v2/token" --data-urlencode 'grant_type=client_credentials' --data-urlencode 'scope=openid profile' || true)"
[ "$WRONG_HTTP" != 200 ] || { echo "PROD_ZITADEL_WRONG_SECRET_ALLOWED" >&2; exit 212; }

python3 - "$MACHINE_ID" "$MACHINE_USER" "$CLIENT_SECRET" <<'PY'
import json,sys
print(json.dumps({
  "schema":"velvetos.office-v2.phase3b-production-zitadel-bundle.v0",
  "machine_id":sys.argv[1],
  "username":sys.argv[2],
  "client_secret":sys.argv[3]
},separators=(",",":")))
PY
SUCCESS=true
