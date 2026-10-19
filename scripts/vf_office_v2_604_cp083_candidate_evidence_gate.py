#!/usr/bin/env python3
"""Offline byte-integrity gate for NEW CP083 candidate full-chain receipts.

This gate is deliberately *not* a runtime attestation, independent QA, or a
security admission. It does not launch etcd, sockets, Git, subprocesses, or
privileged operations. Missing fresh evidence is a FAIL_CLOSED, never a pass.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/vf_office_v2_604_cp083_hardened_candidate.py"
SOURCE_SHA = "83260c77846b34c4f459eaa812f477e51764fa1eee261af1d542a39dd561cd2c"
SOURCE_COMMIT = "e065552825d64e9151dca0a53d4b3c7a896ab479"
PIN_ETCD = "117cc09981c0f1eb378e7520be6969756c2d6a762f376944e53f7bc9800c0c59"
PIN_CTL = "de07257495499384f91f028dbc0c8e0394e0bd572b728ac486bbadbfa1cdf275"
SCHEMA = "velvetos.office-v2.604.cp083.candidate-fullchain-receipts.v1"
GUEST_SCHEMA = "velvetos.office-v2.604.cp083.guest-preflight-observation.v1"
RUN_SCHEMA = "velvetos.office-v2.604.cp083.osuid-mtls-localgit-option-a.v1"
# Original 2026-10-17 historical source, not the hardened candidate.
OLD_RECEIPT_HASHES = frozenset({
    "45303441866630124d0c66f871b67bba8bcabef2c0416ad137341a5366ee1d98",
    "87c5a83b767c29e1d85701469f527b68d5f10201c6bb630864731d51a4c52358",
})
OLD_PROVIDER_PREFIXES = frozenset({
    "b56d8ae9eac5d44a65f5611cb981ca905a3e586f841828a22c121bc7ae8b433d",
    "de17f125a4f4ddd4e2cce72f5b76eeca33bd2315810fbd92558502f12ad772e2",
})
REQUIRED_CASES = frozenset({
    "worker_cannot_read_sink_key_git_or_journal",
    "attacker_cannot_spoof_worker_uid",
    "worker_cannot_change_task_scope",
    "normal_private_sink_committed_native_local_git",
    "normal_no_unknown_and_single_admitted_effect",
    "revoke-first_atomic_admission_denied",
    "revoke-first_never_written_git_ref",
    "drain-before_revoke_moves_to_draining",
    "drain-before_ref_reservation_stays",
    "drain-before_never_written_git_ref",
    "mid_real_etcd_revoke_after_native_git",
    "mid_post_native_revoke_is_unknown_not_success",
    "mid_durable_unknown_frozen",
    "mid_no_blind_retry",
    "mid_restart_does_not_unlock",
    "ack-before_worker_sees_actual_lost_ack",
    "ack-before_durable_unknown_frozen",
    "ack-before_no_blind_retry",
    "ack-before_restart_does_not_unlock",
    "ack-after_worker_sees_actual_lost_ack",
    "ack-after_durable_unknown_frozen",
    "ack-after_no_blind_retry",
    "ack-after_restart_does_not_unlock",
    "crash_after_real_git_killed_sink_before_ack",
    "crash-after_durable_unknown_frozen",
    "crash-after_no_blind_retry",
    "crash-after_restart_does_not_unlock",
})
TRUE_FLAGS = frozenset({
    "distinct_kernel_os_uids", "root_test_fixture_controller",
    "real_mtls_rbac_provider", "real_atomic_etcd_admission",
    "native_local_bare_git_effect", "sink_only_tls_key_and_sqlite_git_dac",
    "durable_unknown_freeze",
})
FALSE_FLAGS = frozenset({
    "real_protected_core_issuer", "remote_github_sink_proven",
    "claim_signature_validated", "two_host_autonomous_coding_proven",
    "cross_store_atomicity_proven", "production_authority",
})
RECEIPT_KEYS = (TRUE_FLAGS | FALSE_FLAGS | {
    "schema", "status", "checks", "check_count", "fixture_prefix_sha256",
    "security_admission", "real_external_github_writes",
})
MANIFEST_KEYS = {
    "schema", "security_admission", "production_authority",
    "real_protected_core_issuer", "independent_security_review_completed",
    "remote_github_writes", "candidate_commit_sha", "candidate_source_sha256",
    "runs",
}
RUN_KEYS = {"run_id", "receipt_path", "receipt_sha256",
            "guest_path", "guest_sha256"}
GUEST_KEYS = {
    "schema", "run_id", "platform", "architecture", "controller_uid",
    "sink_uid", "worker_uid", "attacker_uid", "candidate_source_sha256",
    "no_host_home_mounts_observed", "no_ambient_credentials_observed",
    "mountinfo_sha256", "etcd_sha256", "etcdctl_sha256",
    "etcd_version", "kernel_uid_observation_method",
}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
RUN_ID = re.compile(r"[a-z][a-z0-9_-]{2,63}\Z")
SEGMENT = re.compile(r"[a-zA-Z0-9_][a-zA-Z0-9_.-]*\Z")


class Refused(ValueError):
    pass


def require(test: bool, error: str) -> None:
    if test is not True:
        raise Refused(error)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def is_sha(value: object) -> bool:
    return type(value) is str and HEX64.fullmatch(value) is not None


def unique_pairs(pairs):
    obj = {}
    for key, value in pairs:
        require(key not in obj, "DUPLICATE_JSON_KEY")
        obj[key] = value
    return obj


def _reject_non_finite(_text):
    raise Refused("NON_FINITE_JSON")


def _finite_float(text):
    value = float(text)
    if value != value or value in (float("inf"), float("-inf")):
        raise Refused("NON_FINITE_JSON")
    return value


def decode(raw: bytes) -> dict:
    """Strict JSON object. CR, duplicate keys, NaN/Infinity and extra values fail."""
    # json.loads treats CR as whitespace and keeps the last duplicate key.
    # Both checks have to happen before a value is trusted.
    require(type(raw) is bytes or type(raw) is bytearray, "JSON_BYTES_REQUIRED")
    raw = bytes(raw)
    require(b"\r" not in raw, "CR_IN_CANONICAL_JSON")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise Refused("INVALID_UTF8_OR_JSON") from exc
    try:
        obj = json.loads(text, object_pairs_hook=unique_pairs,
                         parse_constant=_reject_non_finite,
                         parse_float=_finite_float)
    except Refused:
        raise
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise Refused("INVALID_UTF8_OR_JSON") from exc
    require(type(obj) is dict, "JSON_OBJECT_REQUIRED")
    return obj


def decode_wire_frame(raw: bytes, limit: int) -> dict:
    """One LF-terminated JSON object. A second frame or a CR byte is refused."""
    require(type(raw) is bytes or type(raw) is bytearray, "WIRE_FRAME_BYTES")
    raw = bytes(raw)
    require(b"\r" not in raw, "CR_IN_CANONICAL_JSON")
    require(len(raw) <= limit, "MESSAGE_SIZE_REFUSED")
    if b"\n" not in raw:
        raise Refused("WIRE_FRAME_REQUIRED")
    if raw.count(b"\n") != 1 or not raw.endswith(b"\n"):
        raise Refused("WIRE_TRAILING_PAYLOAD")
    return decode(raw[:-1])


def require_evidence_inode(info: os.stat_result, limit: int) -> None:
    """One regular file, one name. A second link or a non-file is not evidence."""
    require(stat.S_ISREG(info.st_mode), "NONREGULAR_FILE")
    require(info.st_nlink == 1, "HARDLINK_ALIAS_REFUSED")
    require(info.st_size <= limit, "OVERSIZED_FILE")


def directory_open_flags() -> int:
    """POSIX directory open. Zero is not a directory requirement.

    Windows has no O_DIRECTORY. Substituting 0 would open a non-directory.
    That host fails closed before the open. POSIX still passes the real flag.
    """
    flag = getattr(os, "O_DIRECTORY", 0)
    if os.name != "posix" or type(flag) is not int or flag == 0:
        raise Refused("SKIP_NON_POSIX")
    return os.O_RDONLY | flag | getattr(os, "O_NOFOLLOW", 0)


def read_bounded(path: Path, limit: int) -> bytes:
    """Reject symlink endpoints, non-regular files, and hardlinks; cap bytes."""
    require(not path.is_symlink(), "SYMLINK_FILE_REFUSED")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(path, flags)
    try:
        require_evidence_inode(os.fstat(fd), limit)
        raw = os.read(fd, limit + 1)
        require(len(raw) <= limit, "OVERSIZED_FILE")
        return raw
    finally:
        os.close(fd)


def artifact_path(base: Path, name: object) -> Path:
    require(type(name) is str and 1 <= len(name) <= 200 and "\\" not in name,
            "UNSAFE_ARTIFACT_PATH")
    path = PurePosixPath(name)
    parts = path.parts
    require(not path.is_absolute() and bool(parts) and
            all(p not in (".", "..") and SEGMENT.fullmatch(p) for p in parts) and
            "/./" not in name and "//" not in name,
            "UNSAFE_ARTIFACT_PATH")
    check = base
    for part in parts[:-1]:
        check = check / part
        require(not check.is_symlink() and check.is_dir(),
                "ARTIFACT_PARENT_NOT_REAL_DIRECTORY")
    return base.joinpath(*parts)


def refuse_symlinked_anchor(base: Path) -> None:
    """O_NOFOLLOW only sees the final component. An ancestor symlink is still a different tree."""
    try:
        real = os.path.realpath(base, strict=True)
    except OSError as exc:
        raise Refused("ANCHORED_OPEN_REFUSED") from exc
    if real != os.path.abspath(base):
        raise Refused("ANCHORED_OPEN_REFUSED")


def read_anchored(base: Path, name: object, limit: int) -> bytes:
    """Open each path component from a held directory fd. O_NOFOLLOW.

    A parent name that changes after the fd is acquired is not the file read.
    Hardlinked regular files are refused: another name can rewrite the inode.
    """
    require(type(name) is str and 1 <= len(name) <= 200 and "\\" not in name,
            "UNSAFE_ARTIFACT_PATH")
    path = PurePosixPath(name)
    parts = path.parts
    require(not path.is_absolute() and bool(parts) and
            all(p not in (".", "..") and SEGMENT.fullmatch(p) for p in parts) and
            "/./" not in name and "//" not in name,
            "UNSAFE_ARTIFACT_PATH")
    flags_dir = directory_open_flags()
    refuse_symlinked_anchor(base)
    flags_file = (os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) |
                  getattr(os, "O_NONBLOCK", 0))
    try:
        base_fd = os.open(base, flags_dir)
    except OSError as exc:
        raise Refused("ANCHORED_OPEN_REFUSED") from exc
    extra = []
    dirfd = base_fd
    try:
        for part in parts[:-1]:
            try:
                nextfd = os.open(part, flags_dir, dir_fd=dirfd)
            except OSError as exc:
                raise Refused("ARTIFACT_PARENT_NOT_REAL_DIRECTORY") from exc
            extra.append(nextfd)
            dirfd = nextfd
        try:
            fd = os.open(parts[-1], flags_file, dir_fd=dirfd)
        except OSError as exc:
            raise Refused("SYMLINK_FILE_REFUSED") from exc
        try:
            require_evidence_inode(os.fstat(fd), limit)
            raw = os.read(fd, limit + 1)
            require(len(raw) <= limit, "OVERSIZED_FILE")
            return raw
        finally:
            os.close(fd)
    finally:
        for item in extra:
            os.close(item)
        os.close(base_fd)


def validate_guest(raw: bytes, run_id: str) -> None:
    guest = decode(raw)
    require(set(guest) == GUEST_KEYS and guest["schema"] == GUEST_SCHEMA,
            "GUEST_OBSERVATION_SCHEMA")
    require(guest["run_id"] == run_id and guest["platform"] == "linux" and
            guest["architecture"] == "aarch64" and guest["controller_uid"] == 0 and
            guest["sink_uid"] == 62001 and guest["worker_uid"] == 62002 and
            guest["attacker_uid"] == 62004 and
            all(type(guest[k]) is int for k in
                ("controller_uid", "sink_uid", "worker_uid", "attacker_uid")) and
            guest["kernel_uid_observation_method"] == "getresuid+SO_PEERCRED" and
            guest["candidate_source_sha256"] == SOURCE_SHA and
            guest["etcd_version"] == "3.6.15",
            "GUEST_OBSERVATION_SCOPE_MISMATCH")
    require(guest["no_host_home_mounts_observed"] is True and
            guest["no_ambient_credentials_observed"] is True,
            "GUEST_NO_SECRET_BOUNDARY_NOT_OBSERVED")
    require(is_sha(guest["mountinfo_sha256"]) and
            guest["etcd_sha256"] == PIN_ETCD and
            guest["etcdctl_sha256"] == PIN_CTL,
            "GUEST_OFFICIAL_ETCD_BINARY_PIN_MISMATCH")


def validate_receipt(raw: bytes) -> str:
    # CRLF still ends with LF and still has one LF, so a bare endswith/count
    # check accepts it. Original receipts are LF-only; any CR is refused.
    require(b"\r" not in raw and raw.endswith(b"\n") and raw.count(b"\n") == 1,
            "RECEIPT_MUST_BE_ORIGINAL_ONE_LINE_LF")
    receipt = decode(raw)
    require(set(receipt) == RECEIPT_KEYS and receipt["schema"] == RUN_SCHEMA and
            receipt["status"] == "PASS_CP083_TEST_ONLY" and
            receipt["security_admission"] == "RED" and
            type(receipt["real_external_github_writes"]) is int and
            receipt["real_external_github_writes"] == 0 and
            type(receipt["check_count"]) is int and receipt["check_count"] == 59,
            "CANDIDATE_RECEIPT_SCHEMA_OR_COUNTS")
    require(all(receipt[k] is True for k in TRUE_FLAGS) and
            all(receipt[k] is False for k in FALSE_FLAGS),
            "UNPROVEN_AUTHORITY_PROMOTED")
    labels = receipt["checks"]
    require(type(labels) is list and len(labels) == 59 and
            all(type(label) is str for label in labels) and
            len(set(labels)) == 59 and REQUIRED_CASES.issubset(set(labels)),
            "REQUIRED_DYNAMIC_FAULT_MATRIX_MISSING")
    prefix = receipt["fixture_prefix_sha256"]
    require(is_sha(prefix) and prefix not in OLD_PROVIDER_PREFIXES,
            "HISTORICAL_PROVIDER_REUSED")
    return prefix


def verify(manifest_path: Path) -> dict:
    # Hard source pin: old CP083's 118 assertions cannot prove the hardened HEAD.
    require(sha(read_bounded(SOURCE, 128 * 1024)) == SOURCE_SHA,
            "CANDIDATE_SOURCE_BYTE_PIN_DRIFT")
    manifest_path = Path(manifest_path)
    manifest = decode(read_bounded(manifest_path, 32 * 1024))
    require(set(manifest) == MANIFEST_KEYS and manifest["schema"] == SCHEMA,
            "MANIFEST_SCHEMA")
    require(manifest["security_admission"] == "RED" and
            manifest["production_authority"] is False and
            manifest["real_protected_core_issuer"] is False and
            manifest["independent_security_review_completed"] is False and
            type(manifest["remote_github_writes"]) is int and
            manifest["remote_github_writes"] == 0 and
            manifest["candidate_commit_sha"] == SOURCE_COMMIT and
            manifest["candidate_source_sha256"] == SOURCE_SHA,
            "UNPROVEN_FULLCHAIN_AUTHORITY_PROMOTED")
    runs = manifest["runs"]
    require(type(runs) is list and len(runs) == 2, "TWO_FRESH_RUNS_REQUIRED")
    ids, hashes, prefixes, guest_hashes, paths = set(), set(), set(), set(), set()
    base = manifest_path.parent
    for entry in runs:
        require(type(entry) is dict and set(entry) == RUN_KEYS and
                type(entry["run_id"]) is str and
                RUN_ID.fullmatch(entry["run_id"]) is not None,
                "RUN_ENTRY_SCHEMA")
        run_id = entry["run_id"]
        require(run_id not in ids, "DUPLICATE_RUN_ID")
        ids.add(run_id)
        for path_key, hash_key, cap in (("receipt_path", "receipt_sha256", 16 * 1024),
                                        ("guest_path", "guest_sha256", 16 * 1024)):
            relative = entry[path_key]
            require(relative not in paths, "REUSED_ARTIFACT_PATH")
            paths.add(relative)
            require(is_sha(entry[hash_key]), "ARTIFACT_SHA256_MISSING")
            original = read_anchored(base, relative, cap)
            require(sha(original) == entry[hash_key], "ARTIFACT_BYTES_MISMATCH")
            if path_key == "receipt_path":
                require(entry[hash_key] not in OLD_RECEIPT_HASHES and
                        entry[hash_key] not in hashes, "HISTORICAL_OR_REUSED_RECEIPT")
                hashes.add(entry[hash_key])
                prefix = validate_receipt(original)
                require(prefix not in prefixes, "TWO_DISTINCT_PROVIDER_PREFIXES_REQUIRED")
                prefixes.add(prefix)
            else:
                require(entry[hash_key] not in guest_hashes,
                        "REUSED_GUEST_OBSERVATION")
                guest_hashes.add(entry[hash_key])
                validate_guest(original, run_id)
    return {
        "status": "OFFLINE_BYTE_CONSISTENCY_ONLY_NOT_RUNTIME_QA",
        "candidate_commit_sha": SOURCE_COMMIT,
        "candidate_source_sha256": SOURCE_SHA,
        "raw_receipt_files": 2,
        "guest_preflight_files": 2,
        "security_admission": "RED",
        "independent_runtime_provenance_verified": False,
        "host_attestation": "REFUSED_UNSIGNED_SELF_ISSUED",
        "production_authority": False,
    }


def refuse_host_attestation(result: dict) -> None:
    """Byte-consistent self-issued receipts are not a host or admission proof."""
    require(type(result) is dict and
            result.get("status") == "OFFLINE_BYTE_CONSISTENCY_ONLY_NOT_RUNTIME_QA" and
            result.get("security_admission") == "RED" and
            result.get("independent_runtime_provenance_verified") is False and
            result.get("host_attestation") == "REFUSED_UNSIGNED_SELF_ISSUED" and
            result.get("production_authority") is False,
            "NOT_HOST_ATTESTATION")
    raise Refused("SELF_ISSUED_RECEIPTS_NOT_HOST_ATTESTATION")


def main(args: list[str]) -> int:
    require(len(args) == 2 and args[0] == "--manifest",
            "USAGE_--manifest_PATH")
    result = verify(Path(args[1]))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (Refused, OSError, TypeError, ValueError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)[:120],
                          "security_admission": "RED", "production_authority": False},
                         sort_keys=True))
        raise SystemExit(2)
