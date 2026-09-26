#!/bin/sh
set -eu
NEW=/opt/openpost/v4.35.0-vfbridge6
WEB_DROP=/etc/systemd/system/openpost.service.d/zz-vfbridge6.conf
WORKER_DROP=/etc/systemd/system/openpost-worker.service.d/zz-vfbridge6.conf
HELPER_SRC=/opt/openpost/v4.35.0-vfbridge5/fetch-bearer-varlib.py
SERVER_SHA=7680c802ddb9de55e51b5fc68ef7dafae659a2798b9ba2fd07cfeab907100293
TOKEN_SHA=a31030d4bb9c8234266e168f9aa6435970a44f9cbc6923a5a60ba5735cf1dc31

rollback(){
  sudo rm -f "$WEB_DROP" "$WORKER_DROP"
  sudo systemctl daemon-reload
  sudo systemctl restart openpost || true
  sudo systemctl restart openpost-worker || true
}
trap 'rollback' HUP INT TERM

sudo mkdir -p "$NEW"
sudo install -o root -g root -m 0755 /tmp/openpost-server-v6 "$NEW/openpost-server"
sudo install -o root -g root -m 0755 /tmp/vf-openpost-token-v6 "$NEW/vf-openpost-token"
sudo install -o root -g root -m 0755 "$HELPER_SRC" "$NEW/fetch-bearer-varlib.py"
test "$(sha256sum "$NEW/openpost-server" | awk '{print $1}')" = "$SERVER_SHA"
test "$(sha256sum "$NEW/vf-openpost-token" | awk '{print $1}')" = "$TOKEN_SHA"

cat >/tmp/zz-vfbridge6-web.conf <<'EOF'
[Service]
ExecStart=
ExecStart=/opt/openpost/v4.35.0-vfbridge6/openpost-server
EnvironmentFile=-/etc/openpost/velvet.env
EOF
cat >/tmp/zz-vfbridge6-worker.conf <<'EOF'
[Service]
ExecStart=
ExecStart=/opt/openpost/v4.35.0-vfbridge6/openpost-server worker
ExecStartPre=
ExecStartPre=+/opt/openpost/v4.35.0-vfbridge6/fetch-bearer-varlib.py
EOF
sudo install -o root -g root -m 0644 /tmp/zz-vfbridge6-web.conf "$WEB_DROP"
sudo install -o root -g root -m 0644 /tmp/zz-vfbridge6-worker.conf "$WORKER_DROP"
rm -f /tmp/zz-vfbridge6-web.conf /tmp/zz-vfbridge6-worker.conf
sudo systemctl daemon-reload
if ! sudo systemctl restart openpost; then rollback; exit 1; fi
if ! sudo systemctl restart openpost-worker; then rollback; exit 2; fi
sleep 4
if [ "$(systemctl is-active openpost)" != active ] || [ "$(systemctl is-active openpost-worker)" != active ]; then rollback; exit 3; fi
if ! curl -fsS http://127.0.0.1:18080/api/v1/ready >/tmp/openpost-v6-ready.json; then rollback; exit 4; fi
python3 - <<'PY'
import json
d=json.load(open('/tmp/openpost-v6-ready.json'))
assert d.get('status')=='ready',d
assert d.get('database')=='ok',d
print('VFBRIDGE6_READY')
PY
systemctl show openpost -p ExecStart --value | grep -q 'v4.35.0-vfbridge6'
systemctl show openpost-worker -p ExecStart --value | grep -q 'v4.35.0-vfbridge6'
trap - HUP INT TERM
echo VFBRIDGE6_DEPLOYED