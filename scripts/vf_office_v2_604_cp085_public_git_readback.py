#!/usr/bin/env python3
"""CP085: credential-free, public GitHub *read-only* ref observation.

This does not implement/attest a protected Core issuer, remote GitHub writer,
authenticated API custody, causal effect evidence or reconciliation release.
A matching remote SHA is an observation, NEVER permission to retry/unfreeze.
Only the fixed public repository and a disposable lab/* ref are read.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

SCHEMA = "velvetos.office604.cp085.public-ref-observation.v1"
REPOSITORY = "nocturney/velvetos-core"
ORIGIN = "https://github.com/nocturney/velvetos-core.git"
GIT = "/usr/bin/git"
MAX_OUTPUT_BYTES = 256
SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
REF_RE = re.compile(r"refs/heads/lab/[a-z0-9][a-z0-9._/-]{0,127}\Z")
EXPECTED_STATES = {
    "REMOTE_ADVANCED_REVIEW_REQUIRED",
    "REMOTE_UNCHANGED_REVIEW_REQUIRED",
    "REMOTE_CONFLICT_REVIEW_REQUIRED",
    "READBACK_UNAVAILABLE_REVIEW_REQUIRED",
}


class Refuse(ValueError):
    pass


@dataclasses.dataclass(frozen=True)
class Intent:
    task: str
    ref: str
    expected: str
    candidate: str
    repository: str = REPOSITORY

    def validate(self):
        if type(self.task) is not str or not re.fullmatch(
                r"[a-z0-9][a-z0-9-]{0,63}", self.task):
            raise Refuse("INVALID_TASK")
        if self.repository != REPOSITORY or type(self.ref) is not str:
            raise Refuse("UNAPPROVED_REMOTE_SCOPE")
        if (not REF_RE.fullmatch(self.ref) or ".." in self.ref
                or "//" in self.ref or self.ref.endswith(("/", ".", "-"))):
            raise Refuse("REF_OUTSIDE_DISPOSABLE_LAB")
        if not all(type(s) is str and SHA_RE.fullmatch(s)
                   for s in (self.expected, self.candidate)):
            raise Refuse("INVALID_SHA")
        if self.expected == self.candidate:
            raise Refuse("NO_DISTINCT_CANDIDATE")


def parse_readback(stdout: str, ref: str) -> str:
    """Accept exactly one full Git ls-remote line, never a partial/multi-ref result."""
    if type(stdout) is not str or not (0 < len(stdout.encode()) <= MAX_OUTPUT_BYTES):
        raise Refuse("UNREADABLE_REMOTE_REPLY")
    if "\r" in stdout or "\0" in stdout:
        raise Refuse("MALFORMED_REMOTE_REPLY")
    lines = stdout.splitlines()
    if len(lines) != 1:
        raise Refuse("AMBIGUOUS_REMOTE_REPLY")
    parts = lines[0].split("\t")
    if (len(parts) != 2 or parts[1] != ref
            or not SHA_RE.fullmatch(parts[0])):
        raise Refuse("REMOTE_REF_OR_SHA_MISMATCH")
    return parts[0]


def _sandboxed_env() -> dict[str, str]:
    # Never forward even an unknown-named controller secret to native git.
    return {
        "PATH": "/usr/bin:/bin",
        "HOME": "/nonexistent",
        "LC_ALL": "C",
        "LANG": "C",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_ASKPASS": "/bin/false",
    }


def observe_public_ref(intent: Intent) -> str:
    intent.validate()
    # No writer verb, credentials, arbitrary URL, shell, or inherited process env.
    with tempfile.TemporaryDirectory(prefix="vf604-cp085-public-observer-") as td:
        try:
            p = subprocess.run(
                [GIT, "-c", "credential.helper=", "ls-remote", "--exit-code",
                 ORIGIN, intent.ref],
                cwd=td, capture_output=True, text=True, timeout=12,
                env=_sandboxed_env(), check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            raise Refuse("READBACK_UNAVAILABLE") from None
    if p.returncode != 0:
        # Do not echo stderr: it might contain a URL, auth helper or remote text.
        raise Refuse("READBACK_UNAVAILABLE")
    return parse_readback(p.stdout, intent.ref)


def classify(intent: Intent, remote_sha: str | None,
             *, authenticated_writer_evidence: bool = False) -> dict:
    """Classify a public observation; NEVER infer causality or release a lease."""
    intent.validate()
    if authenticated_writer_evidence:
        # This adapter must never be promoted by a caller-provided boolean.
        raise Refuse("WRITER_EVIDENCE_OUTSIDE_THIS_ADAPTER")
    if remote_sha is None:
        state = "READBACK_UNAVAILABLE_REVIEW_REQUIRED"
    elif type(remote_sha) is not str or not SHA_RE.fullmatch(remote_sha):
        raise Refuse("INVALID_OBSERVED_SHA")
    elif remote_sha == intent.candidate:
        state = "REMOTE_ADVANCED_REVIEW_REQUIRED"
    elif remote_sha == intent.expected:
        state = "REMOTE_UNCHANGED_REVIEW_REQUIRED"
    else:
        state = "REMOTE_CONFLICT_REVIEW_REQUIRED"
    return {
        "schema": SCHEMA,
        "repository": intent.repository,
        "ref": intent.ref,
        "task": intent.task,
        "expected": intent.expected,
        "candidate": intent.candidate,
        "observed": remote_sha,
        "classification": state,
        "journal_state": "UNKNOWN_EFFECT_RECONCILE",
        "frozen": True,
        "retry_allowed": False,
        "release_allowed": False,
        "effect_proven": False,
        "remote_github_writes": 0,
        "production_authority": False,
        "observation_kind": "PUBLIC_READ_ONLY_NOT_AUTHENTICATED_WRITER",
    }


def receipt_bytes(result: dict) -> bytes:
    if not isinstance(result, dict) or set(result) != {
        "schema", "repository", "ref", "task", "expected", "candidate",
        "observed", "classification", "journal_state", "frozen",
        "retry_allowed", "release_allowed", "effect_proven",
        "remote_github_writes", "production_authority", "observation_kind",
    }:
        raise Refuse("INVALID_RECEIPT_KEYS")
    intent = Intent(task=result["task"], ref=result["ref"],
                    expected=result["expected"], candidate=result["candidate"],
                    repository=result["repository"])
    canonical = classify(intent, result["observed"])
    if result != canonical or result["classification"] not in EXPECTED_STATES:
        raise Refuse("MUTATED_OR_PROMOTED_RECEIPT")
    return (json.dumps(result, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True) + "\n").encode()


def write_private_receipt(path: Path, result: dict) -> str:
    """Create-only local receipt. Interrupted/partial files remain non-admissible."""
    data = receipt_bytes(result)
    path = Path(path)
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise Refuse("RECEIPT_PARENT_UNAVAILABLE")
    if path.parent.stat().st_mode & 0o077:
        raise Refuse("RECEIPT_DIR_MUST_BE_PRIVATE")
    if path.name in ("", ".", "..") or "/" in path.name:
        raise Refuse("INVALID_RECEIPT_NAME")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(str(path), flags, 0o600)
    except OSError:
        raise Refuse("RECEIPT_EXISTS_OR_UNWRITABLE") from None
    with os.fdopen(fd, "wb") as out:
        out.write(data)
        out.flush()
        os.fsync(out.fileno())
    # Flush the parent directory to persist the new directory entry.
    try:
        dfd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except OSError:
        # A partially durable receipt is still only a non-authoritative artifact.
        raise Refuse("RECEIPT_DIRECTORY_SYNC_FAILED") from None
    return hashlib.sha256(data).hexdigest()


def read_private_receipt(path: Path) -> dict:
    """Reject truncated, mutated, extra-payload or noncanonical local receipts."""
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise Refuse("RECEIPT_FILE_UNAVAILABLE")
    try:
        if path.stat().st_size > 4096:
            raise Refuse("RECEIPT_OVERSIZE")
        data = path.read_bytes()
        obj = json.loads(data.decode("utf-8"))
        if data != receipt_bytes(obj):
            raise Refuse("RECEIPT_NOT_CANONICAL")
        return obj
    except (OSError, UnicodeError, ValueError, TypeError):
        raise Refuse("RECEIPT_INVALID") from None


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[1] == "--selftest":
        from test_vf_office_v2_604_cp085_public_git_readback import ReadbackTests
        import unittest
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReadbackTests)
        r = unittest.TextTestRunner(stream=sys.stderr).run(suite)
        return 0 if r.wasSuccessful() else 1
    if len(argv) == 7 and argv[1] == "--observe":
        # Explicit CLI gate: no arbitrary repo/remote; no write effect.
        try:
            intent = Intent(task=argv[2], ref=argv[3],
                            expected=argv[4], candidate=argv[5])
            observed = observe_public_ref(intent)
            result = classify(intent, observed)
            if argv[6] != "-":
                receipt_sha = write_private_receipt(Path(argv[6]), result)
            else:
                receipt_sha = None
        except Refuse as exc:
            # No successful readback cannot prove a remote ref is unchanged.
            print(json.dumps({"status": "REFUSED", "reason": str(exc),
                              "security_admission": "RED"}, sort_keys=True))
            return 2
        print(json.dumps({"status": "OBSERVATION_ONLY", "receipt_sha256": receipt_sha,
                          **result}, sort_keys=True))
        return 0
    print("CP085 READ-ONLY: --selftest | --observe TASK LAB_REF EXPECTED CANDIDATE RECEIPT_OR_DASH",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
