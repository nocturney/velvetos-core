#!/usr/bin/env bash
set -Eeuo pipefail
MACHINE_ID="$1"
TMP="$(mktemp -d)"
RUN=/run/officev2/phase3b
KEYFILE="$RUN/zitadel-admin-sa.json"
trap 'rm -rf "$TMP"; unset ADMIN_TOKEN ASSERTION' EXIT
[ -n "$MACHINE_ID" ] || { echo "PROD_ZITADEL_DELETE_ID_MISSING" >&2; exit 221; }
[ -s "$KEYFILE" ] || { echo "PROD_ZITADEL_ADMIN_KEY_MISSING" >&2; exit 222; }
Z_IP="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' officev2-p3b-shadow-zitadel 2>/dev/null || true)"
[ -n "$Z_IP" ] || { echo "PROD_ZITADEL_IP_MISSING" >&2; exit 223; }
python3 - "$KEYFILE" "$TMP/admin.pem" "$TMP/admin.meta" <<'PY'
import json,sys
d=json.load(open(sys.argv[1],encoding='utf-8'))
open(sys.argv[2],'w',encoding='utf-8').write(d['key'])
open(sys.argv[3],'w',encoding='utf-8').write(d['keyId']+'\n'+d['userId']+'\n')
PY
chmod 0600 "$TMP/admin.pem"
KEY_ID="$(sed -n '1p' "$TMP/admin.meta")"; USER_ID="$(sed -n '2p' "$TMP/admin.meta")"
b64url(){ python3 -c 'import sys,base64; print(base64.urlsafe_b64encode(sys.stdin.buffer.read()).decode().rstrip("="))'; }
NOW="$(date +%s)"; EXP="$((NOW+300))"
HEADER="$(printf '{"alg":"RS256","kid":"%s"}' "$KEY_ID" | b64url)"
PAYLOAD="$(printf '{"iss":"%s","sub":"%s","aud":"http://zitadel:8080","iat":%s,"exp":%s}' "$USER_ID" "$USER_ID" "$NOW" "$EXP" | b64url)"
SIGNING="$HEADER.$PAYLOAD"; SIG="$(printf '%s' "$SIGNING" | openssl dgst -sha256 -sign "$TMP/admin.pem" -binary | b64url)"; ASSERTION="$SIGNING.$SIG"
ADMIN_HTTP="$(curl --http2-prior-knowledge -sS -o "$TMP/admin-token.json" -w '%{http_code}' -H 'Host: zitadel:8080' -H 'Content-Type: application/x-www-form-urlencoded' -X POST "http://$Z_IP:8080/oauth/v2/token" --data-urlencode 'grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer' --data-urlencode 'scope=openid profile urn:zitadel:iam:org:project:id:zitadel:aud' --data-urlencode "assertion=$ASSERTION" || true)"
[ "$ADMIN_HTTP" = 200 ] || { echo "PROD_ZITADEL_ADMIN_TOKEN_FAIL=$ADMIN_HTTP" >&2; exit 224; }
ADMIN_TOKEN="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["access_token"])' "$TMP/admin-token.json")"
DELETE_HTTP="$(curl --http2-prior-knowledge -sS -o /dev/null -w '%{http_code}' -H 'Host: zitadel:8080' -H "Authorization: Bearer $ADMIN_TOKEN" -X DELETE "http://$Z_IP:8080/v2/users/$MACHINE_ID" || true)"
[[ "$DELETE_HTTP" =~ ^(200|404)$ ]] || { echo "PROD_ZITADEL_DELETE_FAIL=$DELETE_HTTP" >&2; exit 225; }
printf 'PASS ZITADEL_DELETE http=%s\n' "$DELETE_HTTP"
