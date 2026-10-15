#!/usr/bin/env python3
"""#604 CP070: pinned OpenSSH Ed25519 LAB source/role binding, never Core lease.

Four separately signed synthetic claims: one exact allowed lab identity and
three crypto-valid WRONG-identity/target samples. The issuer key is not a
Core signer and is not a Git writer. No signature here can authorize effects.
No subprocess except a fixed ssh-keygen -Y verify call; no network or model.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
P2 = ROOT / "docs/implementation/office-v2/phase2"
SCHEMA = "velvetos.office-v2.604.synthetic-signed-bound-capability.v1"
ISSUER = "vf604-cp070-synthetic-not-core"
NAMESPACE = "velvetos-cp070"
ANCHOR = "cp070-allowed-signers.txt"
EXPECTED_ANCHOR_SHA = "26981ff24e52e217df023bb1bde189607355d0c69c10332809ce86aed672223c"
EXPECTED = {
    "good": (
        "14c87a93c7ecafd9339e825d0fc51a5cef9291302c40439baef57d65309fd58d",
        "ff3cbc4fdb0626200848ea99cc42312f81a713d02e49f07cf40f3513eea192b3"),
    "bad-host": (
        "b73ce34296a591fa232a6b02aca0704c9a8f1121c982135b2ce64ce72ec2e9e3",
        "34879ccc93f21d5712ef6b95e2e29cc8025832188f4148d41f0bf050c806a1c0"),
    "bad-uid": (
        "a0dcbcad50afdf91e11fa128897e39dea70437c508aa7c86c442c3f9edbae5eb",
        "58b7f2944b1ca3e00102bbd1f5574afde873ba59cc06d0cd6ad74230a6c1fb20"),
    "bad-effect": (
        "c0a5f3e98d075ec01671364fa54240eadeb2b824e2245d901361ecef979ffdd9",
        "6b73db663e2df45f1ba5711c8d526164a0390c5e6f120d0a2dede3be1117ec94"),
}
REQUIRED = {
    "audience", "effect_kind", "host_id", "issuer_id", "issuer_role",
    "job_key", "lease_epoch", "model_source_sha256", "production_authority",
    "provider_lease_id", "provider_live_revocation_checked",
    "provider_revision", "resource", "schema", "target", "worker_os_uid",
}
SOURCE_SHA = "544908a800b3546b9e5ee0bba57a6395b95f99a4aef6fd5d931e73e89631b5e3"


class Refuse(Exception):
    pass


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise Refuse(reason)


def digest(buf: bytes) -> str:
    return hashlib.sha256(buf).hexdigest()


def load_fixed(label: str) -> tuple[bytes, bytes]:
    need(label in EXPECTED, "NOT_A_FIXED_SYNTHETIC_CLAIM")
    obj = P2 / ("cp070-signed-" + label + ".json")
    sig = P2 / ("cp070-signed-" + label + ".json.sig")
    key = P2 / ANCHOR
    for target in (obj, sig, key):
        need(target.is_file() and not target.is_symlink(), "FIXTURE_MISSING_OR_SYMLINK")
    payload, signature = obj.read_bytes(), sig.read_bytes()
    need(digest(payload) == EXPECTED[label][0] and
         digest(signature) == EXPECTED[label][1],
         "FROZEN_SYNTHETIC_SIGNATURE_OR_PAYLOAD_CHANGED")
    need(digest(key.read_bytes()) == EXPECTED_ANCHOR_SHA,
         "UNTRUSTED_SYNTHETIC_ALLOWLIST_CHANGED")
    return payload, signature


def authenticated_synthetic_bytes(message: bytes, sig: Path,
                                  *, namespace: str = NAMESPACE,
                                  identity: str = ISSUER) -> bool:
    need(type(message) is bytes and len(message) < 4096,
         "MALFORMED_SIGNATURE_INPUT")
    need(sig.is_file() and not sig.is_symlink(), "SIGNATURE_MISSING_OR_ALIAS")
    cmd = ["/usr/bin/ssh-keygen", "-Y", "verify", "-f", str(P2 / ANCHOR),
           "-I", identity, "-n", namespace, "-s", str(sig)]
    proc = subprocess.run(cmd, input=message, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=12, close_fds=True)
    return proc.returncode == 0


def bind_synthetic_scope(row: dict) -> None:
    need(type(row) is dict and set(row) == REQUIRED, "SIGNED_SCHEMA_SCOPE_DRIFT")
    fixed = {
        "schema": SCHEMA,
        "audience": "OFFICE_604_CP070_SYNTHETIC_VERIFY_ONLY",
        "issuer_id": ISSUER,
        "issuer_role": "LAB_SIMULATED_ONLY",
        "host_id": "MacMiniOffice2.local",
        "worker_os_uid": 65534,
        "job_key": "cp058-windows-merge-exact-int-proposal",
        "model_source_sha256": SOURCE_SHA,
        "resource": "colima-velvet-qa:cpu",
        "provider_lease_id": "SYNTHETIC_NOT_ETCD",
        "effect_kind": "NONE",
        "target": "quarantine/windows_merge.py",
        "production_authority": False,
        "provider_live_revocation_checked": False,
    }
    for name, value in fixed.items():
        need(type(row.get(name)) is type(value) and row[name] == value,
             "SIGNED_CLAIM_WRONG_" + name)
    need(type(row["lease_epoch"]) is int and row["lease_epoch"] == 7,
         "LEASE_EPOCH_NOT_FIXED")
    need(type(row["provider_revision"]) is int and row["provider_revision"] == 42,
         "PROVIDER_REVISION_NOT_FIXED")
    # Cryptographically signed synthetic payload is NOT current lease proof.
    # No effect can be authorized without trusted live provider + sole sink.
    return None


def selftest() -> dict:
    positive = 0
    signed_wrong = 0
    negatives = 0
    for label in EXPECTED:
        data, sig_bytes = load_fixed(label)
        path = P2 / ("cp070-signed-" + label + ".json.sig")
        need(authenticated_synthetic_bytes(data, path), "VALID_ED25519_SIGNATURE_NOT_VERIFIED")
        positive += 1
        row = json.loads(data.decode("utf-8"))
        try:
            bind_synthetic_scope(row)
        except Refuse:
            need(label != "good", "GOOD_BINDING_REJECTED")
            signed_wrong += 1
        else:
            need(label == "good", "SIGNED_WRONG_IDENTITY_ADMITTED")
        # Every mutation below is a signed-byte tamper, NOT a new signature.
        if label == "good":
            for text, replacement in (
                (b"MacMiniOffice2.local", b"MacMiniOffice.local"),
                (b"65534", b"501"),
                (b'"NONE"', b'"git_ref_update"'),
                (b"544908a800b3546b", b"0000000000000000"),
                (b'"lease_epoch": 7', b'"lease_epoch": 8'),
                (b'"provider_revision": 42', b'"provider_revision": 43'),
                (b'"SYNTHETIC_NOT_ETCD"', b'"REAL_ETCD"'),
                (b'"production_authority": false', b'"production_authority": true')):
                need(text in data, "MUTATION_NOT_APPLIED")
                need(not authenticated_synthetic_bytes(
                    data.replace(text, replacement, 1), path),
                    "PAYLOAD_TAMPER_SIGNATURE_ACCEPTED")
                negatives += 1
            need(not authenticated_synthetic_bytes(data, path, namespace="wrong"),
                 "CROSS_NAMESPACE_SIGNED_REPLAY")
            negatives += 1
            need(not authenticated_synthetic_bytes(data, path, identity="wrong"),
                 "CROSS_PRINCIPAL_SIGNED_REPLAY")
            negatives += 1
            need(not authenticated_synthetic_bytes(sig_bytes, path),
                 "SIGNED_SIGNATURE_AS_PAYLOAD")
            negatives += 1
    need(positive == 4 and signed_wrong == 3 and negatives == 11,
         "TEST_COUNT_DRIFT")
    return {
        "status": "PASS_SYNTHETIC_ED25519_BINDING_NO_CORE_AUTHORITY",
        "valid_signatures": positive, "signed_wrong_identity_rejected": signed_wrong,
        "unsigned_tamper_denials": negatives, "total_negative_denials": negatives + signed_wrong,
        "source_code_executed": False, "model_calls": 0,
        "core_provider_live_authenticated": False,
        "core_signed_lease_issued": False, "external_git_effect_authorized": False,
        "git_write_calls": 0, "production_authority": False,
    }


def main() -> None:
    need(len(sys.argv) == 2 and sys.argv[1] in ("selftest", "inspect", "admit"),
         "EXPECTED_SELFTEST_INSPECT_OR_REFUSE_ADMIT")
    if sys.argv[1] == "admit":
        raise Refuse("NO_CORE_PROVIDER_REVOCATION_AT_SINK_NEVER_ADMIT")
    result = selftest()
    if sys.argv[1] == "inspect":
        result["verdict"] = "SIGNED_SYNTHETIC_TEST_ONLY_NO_ACTUAL_LEASE"
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (Refuse, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)[:200],
                          "core_signed_lease_issued": False,
                          "git_write_calls": 0,
                          "production_authority": False}, sort_keys=True))
        raise SystemExit(2)
