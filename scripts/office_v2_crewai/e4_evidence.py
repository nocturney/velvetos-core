"""E4 containment evidence. Does not import crewai and does not claim a Chris run."""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

from office_v2_crewai.contract import (
    CREWAI_PROFILE_REL,
    E4_APPDIRS_VERSION,
    TOKEN_CREDENTIALS_REL,
    E4_COMMENT,
    E4_CREWAI_VERSION,
    POSITIVE_DB_NAME,
    SANDBOX_ROOT,
)
from office_v2_crewai.sandbox import StorageRefusal, assert_sandbox_env, on_drive_d, under_root

MANIFEST_SCHEMA = "velvetos.office-v2.crewai-e4-path-manifest.v1"
INDEX_SCHEMA = "velvetos.office-v2.crewai-e4-containment.v1"
HKCU_SCHEMA = "velvetos.office-v2.crewai-e4-hkcu-diff.v1"
CONTROL_SCHEMA = "velvetos.office-v2.crewai-e4-control-run.v1"
POSITIVE_SCHEMA = "velvetos.office-v2.crewai-e4-positive-control.v1"
PROFILE_SOURCE = "SHGetFolderPathW"

REQUIRED_RELS = (
    "AppData\\Local\\CrewAI",
    "AppData\\Local\\CrewAI\\credentials",
    "AppData\\Roaming\\CrewAI",
    "AppData\\Local\\crewai",
    "AppData\\Local\\crewai\\credentials",
    "AppData\\Local\\crewai\\Cache",
    ".crewai",
    ".config\\crewai",
    ".cache",
    ".cache\\huggingface",
    ".cache\\chroma",
    ".cache\\pip",
    "AppData\\Local\\pip\\Cache",
    "AppData\\Local\\Temp",
    ".local\\share\\crewai",
    "__listing__\\profile",
    "__listing__\\AppData\\Local",
    "__listing__\\AppData\\Roaming",
    "__glob__\\AppData\\Local\\chroma",
)

CHILD_REASONS = {
    "manifest_before": "MANIFEST_BEFORE_ABSENT",
    "manifest_after": "MANIFEST_AFTER_ABSENT",
    "hkcu_before": "HKCU_BEFORE_ABSENT",
    "hkcu_after": "HKCU_AFTER_ABSENT",
    "hkcu_diff": "HKCU_DIFF_ABSENT",
    "control_run": "CONTROL_RUN_ABSENT",
    "positive_control": "POSITIVE_CONTROL_ABSENT",
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _dump(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(payload, sort_keys=True, indent=2) + "\n").encode("ascii"))


def _load(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _absent() -> dict:
    return {"present": False, "sha256": None, "size": None, "mtime": None}


def _fingerprint_file(path: Path) -> dict:
    data = path.read_bytes()
    return {"present": True, "sha256": _sha(data), "size": len(data), "mtime": path.stat().st_mtime_ns}


def _fingerprint_files(path: Path, files: list[Path]) -> dict:
    lines = []
    total = 0
    for child in files:
        blob = child.read_bytes()
        total += len(blob)
        rel = child.relative_to(path).as_posix()
        lines.append("%s %s %d" % (rel, _sha(blob), len(blob)))
    body = ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")
    return {"present": True, "sha256": _sha(body), "size": total, "mtime": path.stat().st_mtime_ns}


def _fingerprint_path(path: Path) -> dict:
    if not path.exists():
        return _absent()
    if path.is_file():
        return _fingerprint_file(path)
    if path.is_dir():
        files = sorted((item for item in path.rglob("*") if item.is_file()), key=lambda item: item.as_posix())
        return _fingerprint_files(path, files)
    return _absent()


def _fingerprint_listing(path: Path) -> dict:
    if not path.exists():
        return _absent()
    if path.is_file():
        return _fingerprint_file(path)
    if not path.is_dir():
        return _absent()
    names = sorted(child.name for child in path.iterdir())
    body = ("\n".join(names) + ("\n" if names else "")).encode("utf-8")
    return {"present": True, "sha256": _sha(body), "size": len(names), "mtime": path.stat().st_mtime_ns}


def _fingerprint_chroma(profile: Path) -> dict:
    parent = profile / "AppData" / "Local"
    if not parent.is_dir():
        return _absent()
    matches = [item for item in parent.iterdir() if item.name.lower().startswith("chroma")]
    if not matches:
        return _absent()
    files = []
    for item in matches:
        if item.is_file():
            files.append(item)
        elif item.is_dir():
            files.extend(child for child in item.rglob("*") if child.is_file())
    return _fingerprint_files(parent, sorted(files, key=lambda item: item.as_posix()))


def collect_manifest(profile: Path) -> dict:
    """Hash the CLQ-16 profile paths. Missing paths stay present=false."""
    entries = []
    for rel in REQUIRED_RELS:
        if rel == "__listing__\\profile":
            finger = _fingerprint_listing(profile)
        elif rel.startswith("__listing__\\"):
            finger = _fingerprint_listing(profile.joinpath(*rel.split("\\")[1:]))
        elif rel == "__glob__\\AppData\\Local\\chroma":
            finger = _fingerprint_chroma(profile)
        else:
            finger = _fingerprint_path(profile.joinpath(*rel.split("\\")))
        entries.append({"rel": rel, **finger})
    return {
        "entries": entries,
        "profile_root_source": PROFILE_SOURCE,
        "schema": MANIFEST_SCHEMA,
        "status": "OBSERVED",
    }


def registry_keys(text: str) -> dict[str, str]:
    keys: dict[str, str] = {}
    current = None
    buf: list[str] = []

    def flush() -> None:
        nonlocal current, buf
        if current is not None:
            keys[current] = "\n".join(buf).strip()
        current = None
        buf = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[HKEY_") and stripped.endswith("]"):
            flush()
            current = stripped[1:-1]
            continue
        if current is not None:
            buf.append(line)
    flush()
    return keys


def hkcu_diff(before_text: str, after_text: str) -> dict:
    before = registry_keys(before_text)
    after = registry_keys(after_text)
    return {
        "added": sorted(set(after) - set(before)),
        "removed": sorted(set(before) - set(after)),
        "changed": sorted(key for key in set(before) & set(after) if before[key] != after[key]),
    }


def _entry_map(manifest: dict) -> dict | str:
    if manifest.get("schema") != MANIFEST_SCHEMA:
        return "MANIFEST_SCHEMA_REFUSED"
    if manifest.get("status") != "OBSERVED":
        return "MANIFEST_NOT_OBSERVED"
    if manifest.get("profile_root_source") != PROFILE_SOURCE:
        return "MANIFEST_PROFILE_SOURCE_REFUSED"
    rows = manifest.get("entries")
    if not isinstance(rows, list):
        return "MANIFEST_SCHEMA_REFUSED"
    mapping = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("rel"), str):
            return "MANIFEST_SCHEMA_REFUSED"
        if row["rel"] in mapping:
            return "MANIFEST_SCHEMA_REFUSED"
        present = row.get("present")
        digest = row.get("sha256")
        size = row.get("size")
        mtime = row.get("mtime")
        if present is True:
            if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
                return "MANIFEST_SCHEMA_REFUSED"
            if not isinstance(size, int) or size < 0 or not isinstance(mtime, int):
                return "MANIFEST_SCHEMA_REFUSED"
        elif present is False:
            if digest is not None or size is not None or mtime is not None:
                return "MANIFEST_SCHEMA_REFUSED"
        else:
            return "MANIFEST_SCHEMA_REFUSED"
        mapping[row["rel"]] = row
    if set(mapping) != set(REQUIRED_RELS):
        return "MANIFEST_PATH_MISSING"
    return mapping


def _identity(row: dict) -> tuple:
    return (row["present"], row["sha256"], row["size"], row["mtime"])


def judge_manifests(before: dict, after: dict, control: dict) -> str:
    before_map = _entry_map(before)
    if isinstance(before_map, str):
        return before_map
    after_map = _entry_map(after)
    if isinstance(after_map, str):
        return after_map
    control_reason = _control_flags(control)
    if control_reason:
        return control_reason
    noise = control.get("noise_rels")
    changed = [rel for rel in REQUIRED_RELS if _identity(before_map[rel]) != _identity(after_map[rel])]
    if CREWAI_PROFILE_REL in changed:
        return "MANIFEST_CREWAI_PROFILE_WRITE"
    if TOKEN_CREDENTIALS_REL in changed:
        return "MANIFEST_TOKEN_CREDENTIALS_WRITE"
    for rel in changed:
        if rel not in noise:
            return "MANIFEST_CHANGED"
    return "PASS"


def _string_list(value) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _control_flags(control: dict) -> str | None:
    if not isinstance(control, dict) or control.get("schema") != CONTROL_SCHEMA:
        return "CONTROL_RUN_ABSENT"
    if control.get("status") != "OBSERVED":
        return "CONTROL_RUN_ABSENT"
    if control.get("pilot_started") is not False:
        return "CONTROL_RUN_STARTED_PILOT"
    if control.get("duration_matches_pilot") is not True:
        return "CONTROL_DURATION_MISMATCH"
    if control.get("allowlist_fixed_before_run") is not True:
        return "CONTROL_ALLOWLIST_UNFIXED"
    if not _string_list(control.get("noise_rels")) or not _string_list(control.get("hkcu_noise")):
        return "CONTROL_ALLOWLIST_UNFIXED"
    if CREWAI_PROFILE_REL in control["noise_rels"]:
        return "MANIFEST_CREWAI_PROFILE_WRITE"
    if control.get("overlap_with_candidate") is not False:
        return "CONTROL_NOISE_OVERLAP"
    return None


def judge_hkcu(before_text: str, after_text: str, recorded: dict, control: dict) -> str:
    if not isinstance(recorded, dict) or recorded.get("schema") != HKCU_SCHEMA:
        return "HKCU_DIFF_ABSENT"
    if recorded.get("status") != "OBSERVED":
        return "HKCU_NOT_OBSERVED"
    before_sha = _sha(before_text.encode("utf-8"))
    after_sha = _sha(after_text.encode("utf-8"))
    if recorded.get("before_sha256") != before_sha or recorded.get("after_sha256") != after_sha:
        return "HKCU_EXPORT_MISMATCH"
    actual = hkcu_diff(before_text, after_text)
    for key in ("added", "removed", "changed"):
        if recorded.get(key) != actual[key]:
            return "HKCU_EXPORT_MISMATCH"
    flag = _control_flags(control)
    if flag:
        return flag
    noise = set(control["hkcu_noise"])
    for key in ("added", "removed", "changed"):
        if any(item not in noise for item in actual[key]):
            return "HKCU_DIFF_NONEMPTY"
    return "PASS"


def judge_positive(positive: dict) -> str:
    if not isinstance(positive, dict) or positive.get("schema") != POSITIVE_SCHEMA:
        return "POSITIVE_CONTROL_ABSENT"
    if positive.get("status") != "OBSERVED":
        return "POSITIVE_CONTROL_ABSENT"
    if positive.get("exit_code") != 0:
        return "POSITIVE_EXIT_NONEMPTY"
    if positive.get("db_exists") is not True:
        return "POSITIVE_DB_ABSENT"
    if positive.get("lock_exists") is not True:
        return "POSITIVE_LOCK_ABSENT"
    db_path = positive.get("db_path")
    lock_path = positive.get("lock_path")
    if not isinstance(db_path, str) or not on_drive_d(db_path):
        return "POSITIVE_DB_NOT_ON_D"
    if not under_root(db_path, SANDBOX_ROOT):
        return "POSITIVE_DB_NOT_ON_D"
    expected_db = SANDBOX_ROOT + "\\crewai-storage\\" + POSITIVE_DB_NAME
    if db_path.replace("/", "\\").rstrip("\\").casefold() != expected_db.casefold():
        return "POSITIVE_DB_ABSENT"
    if not isinstance(lock_path, str) or not on_drive_d(lock_path) or not under_root(lock_path, SANDBOX_ROOT):
        return "POSITIVE_LOCK_NOT_IN_TMP"
    normalized = lock_path.replace("/", "\\").rstrip("\\")
    tmp_prefix = SANDBOX_ROOT + "\\tmp\\"
    if not normalized.casefold().startswith(tmp_prefix.casefold()) or not normalized.lower().endswith(".lock"):
        return "POSITIVE_LOCK_NOT_IN_TMP"
    return "PASS"


def positive_files_present(storage_dir: Path, tmp_dir: Path) -> str:
    db_path = storage_dir / POSITIVE_DB_NAME
    if not db_path.is_file():
        return "POSITIVE_DB_ABSENT"
    locks = [path for path in tmp_dir.glob("*.lock") if path.is_file()]
    if not locks:
        return "POSITIVE_LOCK_ABSENT"
    return "PASS"


def _child(evidence_dir: Path, index: dict, key: str) -> Path | None:
    raw = index.get(key)
    if not isinstance(raw, str) or not raw:
        return None
    parts = raw.replace("\\", "/").split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return None
    return evidence_dir.joinpath(*parts)


def assess_evidence(evidence_dir: Path, env: dict) -> str:
    """Return PASS only for a complete observed bundle and a D: sandbox env."""
    index = _load(evidence_dir / "e4-containment.json")
    if index is None or index.get("schema") != INDEX_SCHEMA:
        return "CONTAINMENT_EVIDENCE_ABSENT" if index is None else "CONTAINMENT_SCHEMA_REFUSED"
    if index.get("status") != "OBSERVED":
        return "CONTAINMENT_NOT_OBSERVED"
    if index.get("comment") != E4_COMMENT:
        return "CONTAINMENT_COMMENT_MISMATCH"
    if index.get("localappdata_redirect_sufficient") is not False:
        return "LOCALAPPDATA_REDIRECT_REFUSED"
    if index.get("profile_root_source") != PROFILE_SOURCE:
        return "MANIFEST_PROFILE_SOURCE_REFUSED"
    if index.get("sandbox_root") != SANDBOX_ROOT:
        return "SANDBOX_OUTSIDE_ROOT:ROOT"
    if index.get("crewai_version") != E4_CREWAI_VERSION or index.get("appdirs_version") != E4_APPDIRS_VERSION:
        return "CONTAINMENT_COMMENT_MISMATCH"
    try:
        assert_sandbox_env(env)
    except StorageRefusal as exc:
        return str(exc)
    paths = {}
    for key, reason in CHILD_REASONS.items():
        path = _child(evidence_dir, index, key)
        if path is None or not path.is_file():
            return reason
        paths[key] = path
    before = _load(paths["manifest_before"])
    after = _load(paths["manifest_after"])
    control = _load(paths["control_run"])
    recorded = _load(paths["hkcu_diff"])
    positive = _load(paths["positive_control"])
    if before is None:
        return "MANIFEST_BEFORE_ABSENT"
    if after is None:
        return "MANIFEST_AFTER_ABSENT"
    if control is None:
        return "CONTROL_RUN_ABSENT"
    if recorded is None:
        return "HKCU_DIFF_ABSENT"
    if positive is None:
        return "POSITIVE_CONTROL_ABSENT"
    try:
        before_text = paths["hkcu_before"].read_text(encoding="utf-8")
        after_text = paths["hkcu_after"].read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return "HKCU_BEFORE_ABSENT"
    manifest_reason = judge_manifests(before, after, control)
    if manifest_reason != "PASS":
        return manifest_reason
    hkcu_reason = judge_hkcu(before_text, after_text, recorded, control)
    if hkcu_reason != "PASS":
        return hkcu_reason
    return judge_positive(positive)


def _observed_control() -> dict:
    return {
        "allowlist_fixed_before_run": True,
        "duration_matches_pilot": True,
        "hkcu_noise": [],
        "noise_rels": [],
        "overlap_with_candidate": False,
        "pilot_started": False,
        "schema": CONTROL_SCHEMA,
        "status": "OBSERVED",
    }


def _observed_positive() -> dict:
    return {
        "db_exists": True,
        "db_path": SANDBOX_ROOT + "\\crewai-storage\\" + POSITIVE_DB_NAME,
        "exit_code": 0,
        "lock_exists": True,
        "lock_path": SANDBOX_ROOT + "\\tmp\\kickoff.lock",
        "schema": POSITIVE_SCHEMA,
        "status": "OBSERVED",
    }


def _index(status: str) -> dict:
    return {
        "appdirs_version": E4_APPDIRS_VERSION,
        "comment": E4_COMMENT,
        "control_run": "e4/control-run.json",
        "crewai_version": E4_CREWAI_VERSION,
        "hkcu_after": "e4/hkcu-after.reg",
        "hkcu_before": "e4/hkcu-before.reg",
        "hkcu_diff": "e4/hkcu-diff.json",
        "localappdata_redirect_sufficient": False,
        "manifest_after": "e4/manifest-after.json",
        "manifest_before": "e4/manifest-before.json",
        "positive_control": "e4/positive-control.json",
        "profile_root_source": PROFILE_SOURCE,
        "sandbox_root": SANDBOX_ROOT,
        "schema": INDEX_SCHEMA,
        "status": status,
    }


def write_observed_e4(evidence_dir: Path) -> None:
    """Synthetic observed bundle for the sensor. It is not a Chris observation."""
    evidence_dir.mkdir(parents=True, exist_ok=True)
    profile = evidence_dir / "_profile"
    for rel in REQUIRED_RELS:
        if rel.startswith("__"):
            continue
        profile.joinpath(*rel.split("\\")).mkdir(parents=True, exist_ok=True)
    manifest = collect_manifest(profile)
    before = deepcopy(manifest)
    before["phase"] = "before"
    after = deepcopy(manifest)
    after["phase"] = "after"
    reg = (
        "Windows Registry Editor Version 5.00\n"
        "\n"
        "[HKEY_CURRENT_USER\\Software\\VelvetOS\\CrewAIE4Synthetic]\n"
        "\"marker\"=dword:00000000\n"
    )
    folder = evidence_dir / "e4"
    folder.mkdir(parents=True, exist_ok=True)
    _dump(folder / "manifest-before.json", before)
    _dump(folder / "manifest-after.json", after)
    (folder / "hkcu-before.reg").write_bytes(reg.encode("ascii"))
    (folder / "hkcu-after.reg").write_bytes(reg.encode("ascii"))
    diff = hkcu_diff(reg, reg)
    _dump(folder / "hkcu-diff.json", {
        "added": diff["added"],
        "after_sha256": _sha(reg.encode("utf-8")),
        "before_sha256": _sha(reg.encode("utf-8")),
        "changed": diff["changed"],
        "removed": diff["removed"],
        "schema": HKCU_SCHEMA,
        "status": "OBSERVED",
    })
    _dump(folder / "control-run.json", _observed_control())
    _dump(folder / "positive-control.json", _observed_positive())
    _dump(evidence_dir / "e4-containment.json", _index("OBSERVED"))


def emit_not_observed(evidence_dir: Path) -> None:
    """Record the required E4 artifacts without inventing a Chris observation."""
    evidence_dir.mkdir(parents=True, exist_ok=True)
    entries = [{"mtime": None, "present": None, "rel": rel, "sha256": None, "size": None} for rel in REQUIRED_RELS]
    base = {
        "entries": entries,
        "profile_root_source": PROFILE_SOURCE,
        "schema": MANIFEST_SCHEMA,
        "status": "NOT_OBSERVED",
    }
    before = dict(base)
    before["phase"] = "before"
    after = dict(base)
    after["phase"] = "after"
    folder = evidence_dir / "e4"
    folder.mkdir(parents=True, exist_ok=True)
    _dump(folder / "manifest-before.json", before)
    _dump(folder / "manifest-after.json", after)
    (folder / "hkcu-before.reg").write_bytes(b"NOT_OBSERVED\n")
    (folder / "hkcu-after.reg").write_bytes(b"NOT_OBSERVED\n")
    _dump(folder / "hkcu-diff.json", {
        "added": [],
        "after_sha256": None,
        "before_sha256": None,
        "changed": [],
        "removed": [],
        "schema": HKCU_SCHEMA,
        "status": "NOT_OBSERVED",
    })
    _dump(folder / "control-run.json", {
        "allowlist_fixed_before_run": False,
        "duration_matches_pilot": False,
        "hkcu_noise": [],
        "noise_rels": [],
        "overlap_with_candidate": False,
        "pilot_started": False,
        "schema": CONTROL_SCHEMA,
        "status": "NOT_OBSERVED",
    })
    _dump(folder / "positive-control.json", {
        "db_exists": False,
        "db_path": None,
        "exit_code": None,
        "lock_exists": False,
        "lock_path": None,
        "schema": POSITIVE_SCHEMA,
        "status": "NOT_OBSERVED",
    })
    _dump(evidence_dir / "e4-containment.json", _index("NOT_OBSERVED"))
