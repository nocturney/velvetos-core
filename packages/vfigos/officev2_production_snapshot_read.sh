#!/usr/bin/env bash
set -Eeuo pipefail
OUT=/var/officev2/artifacts/phase3b-security/shadow-runtime/production-snapshot-read.json
TMP="$(mktemp -d)"
EXPECTED="$1"
BASE='https://velvetos-instagram-publisher.velvetos-vf.workers.dev'
APP_TOKEN=""
CLIENT_TOKEN=""
BAO_API=""
cleanup(){
  set +e
  if [ -n "$APP_TOKEN" ] && [ -n "$BAO_API" ]; then
    curl -sS -o /dev/null -H "X-Vault-Token: $APP_TOKEN" -X POST "$BAO_API/v1/auth/token/revoke-self" >/dev/null 2>&1 || true
  fi
  rm -rf "$TMP"
  unset INPUT ROLE_ID SECRET_ID ZITADEL_USERNAME ZITADEL_CLIENT_SECRET ZITADEL_MACHINE_ID CLIENT_TOKEN APP_TOKEN SNAPSHOT
}
trap cleanup EXIT

INPUT="$(cat)"
readarray -t PARTS < <(printf '%s' "$INPUT" | python3 - <<'PY'
import json,sys
d=json.load(sys.stdin)
print(d.get("role_id",""))
print(d.get("secret_id",""))
print(d.get("zitadel_username",""))
print(d.get("zitadel_client_secret",""))
print(d.get("zitadel_machine_id",""))
print(d.get("scope_id",""))
PY
)
ROLE_ID="${PARTS[0]}"; SECRET_ID="${PARTS[1]}"; ZITADEL_USERNAME="${PARTS[2]}"
ZITADEL_CLIENT_SECRET="${PARTS[3]}"; ZITADEL_MACHINE_ID="${PARTS[4]}"; SCOPE_ID="${PARTS[5]}"
[ -n "$ROLE_ID" ] && [ -n "$SECRET_ID" ] && [ -n "$ZITADEL_USERNAME" ] && [ -n "$ZITADEL_CLIENT_SECRET" ] && [ -n "$ZITADEL_MACHINE_ID" ] || { echo "PROD_RUNTIME_BUNDLE_INVALID" >&2; exit 251; }
[ "$SCOPE_ID" = "instagram-publisher-snapshot-read" ] || { echo "PROD_RUNTIME_SCOPE_INVALID" >&2; exit 252; }

PRINCIPAL="svc:officev2-p3b-prod-publisher-snapshot"
ACTION="publisher.snapshot.read"
RESOURCE="cloudflare:velvetos-instagram-publisher"
CORR="$(python3 -c 'import uuid; print(uuid.uuid4())')"
Z_IP="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' officev2-p3b-shadow-zitadel 2>/dev/null || true)"
OPA_IP="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' officev2-p3b-shadow-opa 2>/dev/null || true)"
BAO_IP="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' officev2-p3b-prod-openbao 2>/dev/null || true)"
[ -n "$Z_IP" ] && [ -n "$OPA_IP" ] && [ -n "$BAO_IP" ] || { echo "PROD_CANDIDATE_IP_MISSING" >&2; exit 253; }
BAO_API="http://$BAO_IP:8200"

TOKEN_HTTP=0
for i in $(seq 1 15); do
  TOKEN_HTTP="$(curl --http2-prior-knowledge -sS -o "$TMP/client-token.json" -w '%{http_code}' -H 'Host: zitadel:8080' -H 'Content-Type: application/x-www-form-urlencoded' -u "$ZITADEL_USERNAME:$ZITADEL_CLIENT_SECRET" -X POST "http://$Z_IP:8080/oauth/v2/token" --data-urlencode 'grant_type=client_credentials' --data-urlencode 'scope=openid profile' || true)"
  [ "$TOKEN_HTTP" = 200 ] && break
  sleep 1
done
[ "$TOKEN_HTTP" = 200 ] || { echo "PROD_ZITADEL_TOKEN_FAIL=$TOKEN_HTTP" >&2; exit 254; }
CLIENT_TOKEN="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["access_token"])' "$TMP/client-token.json")"
[ -n "$CLIENT_TOKEN" ] || { echo "PROD_ZITADEL_TOKEN_EMPTY" >&2; exit 255; }
IDENTITY_TOKEN_SHA="$(printf '%s' "$CLIENT_TOKEN" | sha256sum | awk '{print $1}')"
MACHINE_ID_SHA="$(printf '%s' "$ZITADEL_MACHINE_ID" | sha256sum | awk '{print $1}')"
USERNAME_SHA="$(printf '%s' "$ZITADEL_USERNAME" | sha256sum | awk '{print $1}')"

OPA_INPUT="$(python3 -c 'import json,sys; print(json.dumps({"input":{"principal":sys.argv[1],"action":sys.argv[2],"resource":sys.argv[3],"correlation_id":sys.argv[4],"identity_provider":"zitadel","identity_token_reference_sha256":sys.argv[5]}}))' "$PRINCIPAL" "$ACTION" "$RESOURCE" "$CORR" "$IDENTITY_TOKEN_SHA")"
OPA_HTTP="$(printf '%s' "$OPA_INPUT" | curl -sS -o "$TMP/opa.json" -w '%{http_code}' -H 'Content-Type: application/json' -X POST --data-binary @- "http://$OPA_IP:8181/v1/data/office/shadow/allow" || true)"
OPA_ALLOW="$(python3 - "$TMP/opa.json" <<'PY'
import json,sys
try: print(str(json.load(open(sys.argv[1])).get("result") is True).lower())
except Exception: print("false")
PY
)"
[ "$OPA_HTTP" = 200 ] && [ "$OPA_ALLOW" = true ] || { echo "PROD_OPA_ALLOW_FAIL http=$OPA_HTTP allow=$OPA_ALLOW" >&2; exit 256; }

LOGIN="$(python3 -c 'import json,sys; print(json.dumps({"role_id":sys.argv[1],"secret_id":sys.argv[2]}))' "$ROLE_ID" "$SECRET_ID")"
LOGIN_HTTP="$(printf '%s' "$LOGIN" | curl -sS -o "$TMP/bao-login.json" -w '%{http_code}' -H 'Content-Type: application/json' -X POST --data-binary @- "$BAO_API/v1/auth/approle/login" || true)"
[ "$LOGIN_HTTP" = 200 ] || { echo "PROD_BROKER_LOGIN_FAIL=$LOGIN_HTTP" >&2; exit 257; }
APP_TOKEN="$(python3 -c 'import json,sys; print((json.load(open(sys.argv[1])).get("auth") or {}).get("client_token",""))' "$TMP/bao-login.json")"
[ -n "$APP_TOKEN" ] || { echo "PROD_BROKER_TOKEN_MISSING" >&2; exit 258; }
BROKER_READ="$(curl -sS -o "$TMP/snapshot-secret.json" -w '%{http_code}' -H "X-Vault-Token: $APP_TOKEN" "$BAO_API/v1/secret/data/officev2-prod/instagram-publisher-snapshot" || true)"
BROKER_UNRELATED="$(curl -sS -o /dev/null -w '%{http_code}' -H "X-Vault-Token: $APP_TOKEN" "$BAO_API/v1/secret/data/alpha" || true)"
SNAPSHOT="$(python3 - "$TMP/snapshot-secret.json" <<'PY'
import json,sys
try: print((((json.load(open(sys.argv[1])).get("data") or {}).get("data") or {}).get("value","")))
except Exception: print("")
PY
)"
[ "$BROKER_READ" = 200 ] && [ "$BROKER_UNRELATED" = 403 ] && [ -n "$SNAPSHOT" ] || { echo "PROD_BROKER_SCOPE_FAIL read=$BROKER_READ unrelated=$BROKER_UNRELATED" >&2; exit 259; }
CRED_SHA="$(printf '%s' "$SNAPSHOT" | sha256sum | awk '{print $1}')"
[ "$CRED_SHA" = "$EXPECTED" ] || { echo "PROD_CREDENTIAL_HASH_MISMATCH" >&2; exit 260; }

cat > "$TMP/fetch.py" <<'PY'
import json,sys,urllib.request,urllib.error
from datetime import datetime,timezone
base=sys.argv[1].rstrip("/")
summary_path=sys.argv[2]
token=sys.stdin.read().strip()
headers={"Authorization":"Bearer "+token,"Accept":"application/json","User-Agent":"OfficeV2-Phase3B-Production-Read/2.0"}
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
if age is None or age>180: raise SystemExit(f"publisher cron heartbeat stale/missing: age={age}")
if meta.get("ok") is not True: raise SystemExit("publisher Meta health failed")
scheduled=[]; detail_codes=[]
for row in listing.get("jobs") or []:
    if row.get("status") not in {"scheduled","retry"}: continue
    jid=str(row.get("id") or "")
    code,payload=call("/v1/jobs/"+jid); detail_codes.append(code)
    if code!=200: raise SystemExit(f"job detail read failed: {jid} http={code}")
    detail=payload.get("job") or {}; media=detail.get("media") or []; first=media[0] if media else {}
    ts=int(detail.get("scheduled_at") or row.get("scheduled_at") or 0)
    scheduled.append({"publication_id":jid,"title":detail.get("content_id") or row.get("content_id") or jid,"scheduled_at":datetime.fromtimestamp(ts,tz=timezone.utc).isoformat().replace("+00:00","Z"),"content_profile":detail.get("kind") or row.get("kind") or "post","thumbnail_url":first.get("url") or "","status":detail.get("status") or row.get("status"),"source":"cloudflare-instagram-publisher"})
scheduled.sort(key=lambda x:x["scheduled_at"])
snapshot={"schema":"vf.instagram.schedule-snapshot.v1","source":"cloudflare-instagram-publisher","observed_at":observed.isoformat().replace("+00:00","Z"),"runtime":{"last_cron_tick":tick,"heartbeat_age_seconds":age,"job_counts":runtime.get("job_counts") or []},"meta_health":{"ok":True,"username":str(meta.get("username") or "")},"scheduled":scheduled}
open(summary_path,"w",encoding="utf-8").write(json.dumps({"runtime_http":runtime_http,"meta_health_http":meta_http,"jobs_http":jobs_http,"job_detail_http_all_200":all(c==200 for c in detail_codes),"job_detail_count":len(detail_codes),"write_run_http":write_http,"scheduled_count":len(scheduled)},sort_keys=True))
print(json.dumps(snapshot,ensure_ascii=False,separators=(",",":")))
PY
SNAP_JSON="$(printf '%s' "$SNAPSHOT" | python3 "$TMP/fetch.py" "$BASE" "$TMP/provider-summary.json")"
[ -n "$SNAP_JSON" ] || { echo "PROD_PROVIDER_SNAPSHOT_FAIL" >&2; exit 261; }
SNAP_SHA="$(printf '%s' "$SNAP_JSON" | sha256sum | awk '{print $1}')"

python3 - "$OUT.tmp" "$CORR" "$PRINCIPAL" "$IDENTITY_TOKEN_SHA" "$MACHINE_ID_SHA" "$USERNAME_SHA" "$OPA_HTTP" "$LOGIN_HTTP" "$BROKER_READ" "$BROKER_UNRELATED" "$CRED_SHA" "$SNAP_SHA" "$TMP/provider-summary.json" <<'PY'
import datetime,json,sys
out,corr,principal,itok,mid,uname,opa,login,bread,bunrel,cred,snapsha,summary_path=sys.argv[1:]
summary=json.load(open(summary_path))
doc={
 "schema":"velvetos.office-v2.phase3b-production-snapshot-read.v1",
 "captured_at":datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z"),
 "status":"PASS","correlation_id":corr,"scope_id":"instagram-publisher-snapshot-read","credential_class":"PRODUCTION_READ",
 "principal":principal,"action":"publisher.snapshot.read","resource":"cloudflare:velvetos-instagram-publisher",
 "identity":{"provider":"zitadel","client_credentials_http":200,"token_reference_sha256":itok,"machine_id_reference_sha256":mid,"username_reference_sha256":uname,"persistent_principal":True,"ephemeral_cleanup_on_exit":False},
 "authorization":{"engine":"opa","http":int(opa),"decision":"ALLOW","default":"DENY"},
 "broker":{"broker":"openbao","instance":"officev2-p3b-prod-openbao","role":"officev2-prod-publisher-snapshot","logical_secret_path":"officev2-prod/data/instagram-publisher-snapshot","approle_login_http":int(login),"exact_scope_read_http":int(bread),"unrelated_scope_http":int(bunrel),"credential_reference_sha256":cred,"session_cleanup_on_exit":True},
 "provider":summary,"snapshot_payload_sha256":snapsha,
 "raw_identity_token_recorded":False,"raw_provider_credential_recorded":False,"raw_broker_token_recorded":False,
 "control_token_read_or_reused":False,"meta_access_token_read_or_reused":False,
 "write_allowed":False,"external_mutation_performed":False,"production_writer_change":False
}
open(out,"w",encoding="utf-8").write(json.dumps(doc,indent=2,sort_keys=True)+"\n")
PY
mv -f "$OUT.tmp" "$OUT"
printf '%s\n' "$SNAP_JSON"
