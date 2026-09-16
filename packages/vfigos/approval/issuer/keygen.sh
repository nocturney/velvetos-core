#!/usr/bin/env bash
# Generate an Ed25519 keypair for delivery approval.
# Writes PRIVATE material only to stdout guidance / GSM — never commits it.
# Prints public registry JSON fragment for packages/vfigos/approval/keys/registry.json.
set -euo pipefail

KEY_ID="${1:-vf-da-$(date -u +%Y%m)}"
python3 - <<'PY' "$KEY_ID"
import base64, json, sys
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

key_id = sys.argv[1]
priv = Ed25519PrivateKey.generate()
seed = priv.private_bytes_raw()
pub = priv.public_key().public_bytes_raw()
priv_b64 = base64.urlsafe_b64encode(seed).decode("ascii").rstrip("=")
pub_b64 = base64.b64encode(pub).decode("ascii")
print("=== PRIVATE (GSM only — do not commit / do not print into tickets) ===", file=sys.stderr)
print(priv_b64)
print("=== PUBLIC registry fragment (safe to commit) ===", file=sys.stderr)
print(json.dumps({
    "key_id": key_id,
    "algorithm": "Ed25519",
    "public_key_b64": pub_b64,
}, indent=2))
print(f"Store private in GSM secret velvet-delivery-approval-ed25519-private", file=sys.stderr)
print(f"Store key_id '{key_id}' in GSM secret velvet-delivery-approval-key-id", file=sys.stderr)
print(f"Append public fragment to packages/vfigos/approval/keys/registry.json and set active_signing_key_id", file=sys.stderr)
PY
