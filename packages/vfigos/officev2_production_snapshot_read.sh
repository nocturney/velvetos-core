#!/usr/bin/env bash
set -Eeuo pipefail
OUT=/var/officev2/artifacts/phase3b-security/shadow-runtime/production-snapshot-read.json
TMP="$(mktemp -d)"
RUN=/run/officev2/phase3b
KEYFILE="$RUN/zitadel-admin-sa.json"
EXPECTED="$1"
BASE='https://velvetos-instagram-publisher.velvetos-vf.workers.dev'
MACHINE_ID=""
ADMIN_TOKEN=""
CLIENT_SECRET=""
APP_TOKEN=""
BAO_API=""
cleanup(){
  set +e
  if [ -n "$APP_TOKEN" ] && [ -n "$BAO_API" ]; then
    curl -sS -o /dev/null -H "X-Vault-Token: $APP_TOKEN" -X POST "$BAO_API/v1/auth/token/revoke-self" >/dev/null 2>&1 || true
  fi
  if [ -n "$MACHINE_ID" ] && [ -n "$ADMIN_TOKEN" ] && [ -n "${Z_IP:-}" ]; then
    curl --http2-prior-knowledge -sS -o /dev/null -H 'Host: zitadel:8080' -H "Authorization: Bearer $ADMIN_TOKEN" -X DELETE "http://$Z_IP:8080/v2/users/$MACHINE_ID" >/dev/null 2>&1 || true
  fi
  rm -rf "$TMP"
  unset INPUT ROLE_ID SECRET_ID ADMIN_TOKEN CLIENT_SECRET CLIENT_TOKEN ASSERTION APP_TOKEN SNAPSHOT LOGIN
}
trap cleanup EXIT
INPUT="$(cat)"
ROLE_ID="$(printf '%s' "$INPUT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("role_id",""))')"
SECRET_ID="$(printf '%s' "$INPUT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("secret_id",""))')"
[ -n "$ROLE_ID" ] && [ -n "$SECRET_ID" ] || { echo "PROD_APPROLE_INPUT_INVALID" >&2; exit 101; }
[ -s "$KEYFILE" ] || { echo "PROD_ZITADEL_ADMIN_KEY_MISSING" >&2; exit 102; }
CORR="$(python3 -c 'import uuid; print(uuid.uuid4())')"
PRINCIPAL="svc:officev2-p3b-production-publisher-snapshot"
ACTION="publisher.snapshot.read"
RESOURCE="cloudflare:velvetos-instagram-publisher"
Z_IP="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' officev2-p3b-shadow-zitadel 2>/dev/null || true)"
OPA_IP="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' officev2-p3b-shadow-opa 2>/dev/null || true)"
BAO_IP="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' officev2-p3b-shadow-openbao 2>/dev/null || true)"
[ -n "$Z_IP" ] && [ -n "$OPA_IP" ] && [ -n "$BAO_IP" ] || { echo "PROD_CANDIDATE_IP_MISSING" >&2; exit 103; }
BAO_API="http://$BAO_IP:8200"

python3 - "$KEYFILE" "$TMP/admin.pem" "$TMP/admin.meta" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
open(sys.argv[2],'w').write(d['key'])
open(sys.argv[3],'w').write(d['keyId']+'\n'+d['userId']+'\n')
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
[ "$ADMIN_HTTP" = 200 ] || { echo "PROD_ZITADEL_ADMIN_TOKEN_FAIL=$ADMIN_HTTP" >&2; exit 104; }
ADMIN_TOKEN="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["access_token"])' "$TMP/admin-token.json")"
ADMIN_READ="$(curl --http2-prior-knowledge -sS -o "$TMP/admin-user.json" -w '%{http_code}' -H 'Host: zitadel:8080' -H "Authorization: Bearer $ADMIN_TOKEN" "http://$Z_IP:8080/v2/users/$USER_ID" || true)"
[ "$ADMIN_READ" = 200 ] || { echo "PROD_ZITADEL_ADMIN_READ_FAIL=$ADMIN_READ" >&2; exit 105; }
ORG_ID="$(python3 - "$TMP/admin-user.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
print((d.get('details') or {}).get('resourceOwner') or ((d.get('user') or {}).get('details') or {}).get('resourceOwner') or '')
PY
)"
[ -n "$ORG_ID" ] || { echo "PROD_ZITADEL_ORG_MISSING" >&2; exit 106; }
MACHINE_USER="officev2-p3b-production-snapshot-$(date +%s)-$RANDOM"
CREATE_HTTP="$(curl --http2-prior-knowledge -sS -o "$TMP/machine.json" -w '%{http_code}' -H 'Host: zitadel:8080' -H 'Content-Type: application/json' -H "Authorization: Bearer $ADMIN_TOKEN" -X POST "http://$Z_IP:8080/v2/users/new" -d "{\"organizationId\":\"$ORG_ID\",\"username\":\"$MACHINE_USER\",\"machine\":{\"name\":\"OfficeV2 Phase3B Production Publisher Snapshot\",\"description\":\"Ephemeral identity for one production read\",\"accessTokenType\":\"ACCESS_TOKEN_TYPE_BEARER\"}}" || true)"
[ "$CREATE_HTTP" = 200 ] || { echo "PROD_ZITADEL_CREATE_FAIL=$CREATE_HTTP" >&2; exit 107; }
MACHINE_ID="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["id"])' "$TMP/machine.json")"
SECRET_HTTP="$(curl --http2-prior-knowledge -sS -o "$TMP/secret.json" -w '%{http_code}' -H 'Host: zitadel:8080' -H "Authorization: Bearer $ADMIN_TOKEN" -X POST "http://$Z_IP:8080/v2/users/$MACHINE_ID/secret" || true)"
[ "$SECRET_HTTP" = 200 ] || { echo "PROD_ZITADEL_SECRET_FAIL=$SECRET_HTTP" >&2; exit 108; }
CLIENT_SECRET="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["clientSecret"])' "$TMP/secret.json")"

TOKEN_HTTP=0
for i in $(seq 1 15); do
  TOKEN_HTTP="$(curl --http2-prior-knowledge -sS -o "$TMP/client-token.json" -w '%{http_code}' -H 'Host: zitadel:8080' -H 'Content-Type: application/x-www-form-urlencoded' -u "$MACHINE_USER:$CLIENT_SECRET" -X POST "http://$Z_IP:8080/oauth/v2/token" --data-urlencode 'grant_type=client_credentials' --data-urlencode 'scope=openid profile' || true)"
  [ "$TOKEN_HTTP" = 200 ] && break
  sleep 1
done
[ "$TOKEN_HTTP" = 200 ] || { echo "PROD_ZITADEL_TOKEN_FAIL=$TOKEN_HTTP" >&2; exit 109; }
CLIENT_TOKEN="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["access_token"])' "$TMP/client-token.json")"
IDENTITY_TOKEN_SHA="$(printf '%s' "$CLIENT_TOKEN" | sha256sum | awk '{print $1}')"
MACHINE_ID_SHA="$(printf '%s' "$MACHINE_ID" | sha256sum | awk '{print $1}')"

OPA_INPUT="$(python3 -c 'import json,sys; print(json.dumps({"input":{"principal":sys.argv[1],"action":sys.argv[2],"resource":sys.argv[3],"correlation_id":sys.argv[4],"identity_provider":"candidate-zitadel","identity_token_reference_sha256":sys.argv[5]}}))' "$PRINCIPAL" "$ACTION" "$RESOURCE" "$CORR" "$IDENTITY_TOKEN_SHA")"
OPA_HTTP="$(printf '%s' "$OPA_INPUT" | curl -sS -o "$TMP/opa.json" -w '%{http_code}' -H 'Content-Type: application/json' -X POST --data-binary @- "http://$OPA_IP:8181/v1/data/office/shadow/allow" || true)"
OPA_ALLOW="$(python3 - "$TMP/opa.json" <<'PY'
import json,sys
try: print(str(json.load(open(sys.argv[1])).get('result') is True).lower())
except Exception: print('false')
PY
)"
[ "$OPA_HTTP" = 200 ] && [ "$OPA_ALLOW" = true ] || { echo "PROD_OPA_ALLOW_FAIL http=$OPA_HTTP allow=$OPA_ALLOW" >&2; exit 110; }

LOGIN="$(python3 -c 'import json,sys; print(json.dumps({"role_id":sys.argv[1],"secret_id":sys.argv[2]}))' "$ROLE_ID" "$SECRET_ID")"
LOGIN_HTTP="$(printf '%s' "$LOGIN" | curl -sS -o "$TMP/bao-login.json" -w '%{http_code}' -H 'Content-Type: application/json' -X POST --data-binary @- "$BAO_API/v1/auth/approle/login" || true)"
[ "$LOGIN_HTTP" = 200 ] || { echo "PROD_BROKER_LOGIN_FAIL=$LOGIN_HTTP" >&2; exit 111; }
APP_TOKEN="$(python3 -c 'import json,sys; print((json.load(open(sys.argv[1])).get("auth") or {}).get("client_token",""))' "$TMP/bao-login.json")"
[ -n "$APP_TOKEN" ] || { echo "PROD_BROKER_TOKEN_MISSING" >&2; exit 112; }
BROKER_READ="$(curl -sS -o "$TMP/snapshot-secret.json" -w '%{http_code}' -H "X-Vault-Token: $APP_TOKEN" "$BAO_API/v1/secret/data/officev2-pilot/instagram-publisher-snapshot" || true)"
BROKER_UNRELATED="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $APP_TOKEN" "$BAO_API/v1/secret/data/alpha" || true)"
SNAPSHOT="$(python3 - "$TMP/snapshot-secret.json" <<'PY'
import json,sys
try: print((((json.load(open(sys.argv[1])).get('data') or {}).get('data') or {}).get('value','')))
except Exception: print('')
PY
)"
[ "$BROKER_READ" = 200 ] && [ "$BROKER_UNRELATED" = 403 ] && [ -n "$SNAPSHOT" ] || { echo "PROD_BROKER_SCOPE_FAIL read=$BROKER_READ unrelated=$BROKER_UNRELATED" >&2; exit 113; }
CRED_SHA="$(printf '%s' "$SNAPSHOT" | sha256sum | awk '{print $1}')"
[ "$CRED_SHA" = "$EXPECTED" ] || { echo "PROD_CREDENTIAL_HASH_MISMATCH" >&2; exit 114; }

cat > "$TMP/fetch.py" <<'PY'
import json,sys,urllib.request,urllib.error
from datetime import datetime,timezone
base=sys.argv[1].rstrip("/")
summary_path=sys.argv[2]
token=sys.stdin.read().strip()
headers={"Authorization":"Bearer "+token,"Accept":"application/json","User-Agent":"OfficeV2-Phase3B-Production-Read/1.0"}
def call(path,method="GET",body=None):
    data=None if body is None else json.dumps(body).encode()
    h=dict(headers)
    if data is not None: h["Content-Type"]="application/json"
    req=urllib.request.Request(base+path,headers=h,data=data,method=method)
    try:
        with urllib.request.urlopen(req,timeout=20) as resp:
            raw=resp.read()
            return resp.status,(json.loads(raw.decode()) if raw else {})
    except urllib.error.HTTPError as exc:
        raw=exc.read()
        try: payload=json.loads(raw.decode()) if raw else {}
        except Exception: payload={}
        return exc.code,payload

runtime_http,runtime=call("/v1/runtime")
meta_http,meta=call("/v1/meta-health")
jobs_http,listing=call("/v1/jobs")
write_http,_=call("/v1/run","POST",{})
if runtime_http!=200 or meta_http!=200 or jobs_http!=200 or write_http!=401:
    raise SystemExit(f"provider boundary runtime={runtime_http} meta={meta_http} jobs={jobs_http} write={write_http}")
observed=datetime.now(timezone.utc)
tick=int(runtime.get("last_cron_tick") or 0)
age=max(0,int(observed.timestamp())-tick) if tick else None
if age is None or age>180:
    raise SystemExit(f"publisher cron heartbeat stale/missing: age={age}")
if meta.get("ok") is not True:
    raise SystemExit("publisher Meta health failed")
scheduled=[]
detail_codes=[]
for row in listing.get("jobs") or []:
    if row.get("status") not in {"scheduled","retry"}:
        continue
    jid=str(row.get("id") or "")
    code,payload=call("/v1/jobs/"+jid)
    detail_codes.append(code)
    if code!=200:
        raise SystemExit(f"job detail read failed: {jid} http={code}")
    detail=payload.get("job") or {}
    media=detail.get("media") or []
    first=media[0] if media else {}
    ts=int(detail.get("scheduled_at") or row.get("scheduled_at") or 0)
    scheduled.append({
        "publication_id":jid,
        "title":detail.get("content_id") or row.get("content_id") or jid,
        "scheduled_at":datetime.fromtimestamp(ts,tz=timezone.utc).isoformat().replace("+00:00","Z"),
        "content_profile":detail.get("kind") or row.get("kind") or "post",
        "thumbnail_url":first.get("url") or "",
        "status":detail.get("status") or row.get("status"),
        "source":"cloudflare-instagram-publisher",
    })
scheduled.sort(key=lambda x:x["scheduled_at"])
snapshot={
    "schema":"vf.instagram.schedule-snapshot.v1",
    "source":"cloudflare-instagram-publisher",
    "observed_at":observed.isoformat().replace("+00:00","Z"),
    "runtime":{"last_cron_tick":tick,"heartbeat_age_seconds":age,"job_counts":runtime.get("job_counts") or []},
    "meta_health":{"ok":True,"username":str(meta.get("username") or "")},
    "scheduled":scheduled,
}
open(summary_path,"w",encoding="utf-8").write(json.dumps({
    "runtime_http":runtime_http,"meta_health_http":meta_http,"jobs_http":jobs_http,
    "job_detail_http_all_200":all(c==200 for c in detail_codes),"job_detail_count":len(detail_codes),
    "write_run_http":write_http,"scheduled_count":len(scheduled)
},sort_keys=True))
print(json.dumps(snapshot,ensure_ascii=False,separators=(",",":")))
PY
SNAP_JSON="$(printf '%s' "$SNAPSHOT" | python3 "$TMP/fetch.py" "$BASE" "$TMP/provider-summary.json")"
PROVIDER_EXIT=$?
[ "$PROVIDER_EXIT" = 0 ] && [ -n "$SNAP_JSON" ] || { echo "PROD_PROVIDER_SNAPSHOT_FAIL" >&2; exit 115; }

SNAP_SHA="$(printf '%s' "$SNAP_JSON" | sha256sum | awk '{print $1}')"
python3 - "$OUT.tmp" "$CORR" "$PRINCIPAL" "$IDENTITY_TOKEN_SHA" "$MACHINE_ID_SHA" "$OPA_HTTP" "$LOGIN_HTTP" "$BROKER_READ" "$BROKER_UNRELATED" "$CRED_SHA" "$SNAP_SHA" "$TMP/provider-summary.json" <<'PY'
import datetime,json,sys
out,corr,principal,itok,mid,opa,login,bread,bunrel,cred,snapsha,summary_path=sys.argv[1:]
summary=json.load(open(summary_path))
doc={
 "schema":"velvetos.office-v2.phase3b-production-snapshot-read.v0",
 "captured_at":datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z"),
 "status":"PASS","correlation_id":corr,
 "scope_id":"instagram-publisher-snapshot-read","credential_class":"PRODUCTION_READ",
 "principal":principal,"action":"publisher.snapshot.read",
 "resource":"cloudflare:velvetos-instagram-publisher",
 "identity":{"provider":"candidate-zitadel","client_credentials_http":200,"token_reference_sha256":itok,"machine_id_reference_sha256":mid,"ephemeral_cleanup_on_exit":True},
 "authorization":{"engine":"candidate-opa","http":int(opa),"decision":"ALLOW","default":"DENY"},
 "broker":{"broker":"candidate-openbao","approle_login_http":int(login),"exact_scope_read_http":int(bread),"unrelated_scope_http":int(bunrel),"credential_reference_sha256":cred,"session_cleanup_on_exit":True},
 "provider":summary,"snapshot_payload_sha256":snapsha,
 "raw_identity_token_recorded":False,"raw_provider_credential_recorded":False,"raw_broker_token_recorded":False,
 "control_token_read_or_reused":False,"meta_access_token_read_or_reused":False,
 "write_allowed":False,"external_mutation_performed":False,"production_writer_change":False
}
open(out,"w",encoding="utf-8").write(json.dumps(doc,indent=2,sort_keys=True)+"\n")
PY
mv -f "$OUT.tmp" "$OUT"
printf '%s\n' "$SNAP_JSON"
