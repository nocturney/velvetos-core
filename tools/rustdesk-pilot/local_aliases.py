"""Local-only, hashed RustDesk ID to friendly host-name mapping.

No network, RustDesk client modification, database write, credential access,
or persistent service. Callers explicitly provide an owner-private JSON file.
Raw RustDesk IDs belong only in a private HTML report, not this alias file.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Any

SCHEMA = "velvetos.rustdesk.local_aliases.v1"
MAX_ENTRIES = 1000
MAX_BYTES = 65536
HASH = re.compile(r"[0-9a-f]{64}\Z")
EVIDENCE = frozenset({"local_cli_get_id", "rustdesk_peer_cache_hostname"})


class LocalAliasError(ValueError):
    pass


def _inside_git_tree(folder: Path) -> bool:
    for ancestor in (folder, *folder.parents):
        if (ancestor / ".git").exists():
            return True
    return False


def load_aliases(path: Path) -> dict[str, str]:
    """Read a private explicit mapping from SHA256(ID) to hostname.

    The file MUST be outside Git and private to the OS user on POSIX.
    Never return underlying file paths, IDs, or alias values in errors.
    """
    if path.is_symlink():
        raise LocalAliasError("alias_symlink_rejected")
    try:
        resolved = path.expanduser().resolve(strict=True)
        if not resolved.is_file():
            raise LocalAliasError("alias_not_regular_file")
        if _inside_git_tree(resolved.parent):
            raise LocalAliasError("alias_must_be_outside_git")
        info = resolved.stat()
        if info.st_size > MAX_BYTES:
            raise LocalAliasError("alias_file_too_large")
        if os.name == "posix" and stat.S_IMODE(info.st_mode) & 0o077:
            raise LocalAliasError("alias_file_not_private")
        obj = json.loads(resolved.read_text(encoding="utf-8"))
    except LocalAliasError:
        raise
    except (OSError, ValueError, UnicodeError) as exc:
        raise LocalAliasError("alias_file_unavailable") from exc
    if (not isinstance(obj, dict) or set(obj) != {"schema", "entries"} or
            obj.get("schema") != SCHEMA):
        raise LocalAliasError("invalid_alias_schema")
    entries = obj.get("entries")
    if not isinstance(entries, list) or len(entries) > MAX_ENTRIES:
        raise LocalAliasError("invalid_alias_entries")
    aliases: dict[str, str] = {}
    names: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {
            "id_sha256", "display_name", "evidence",
        }:
            raise LocalAliasError("invalid_alias_entry")
        digest = entry["id_sha256"]
        name = entry["display_name"]
        evidence = entry["evidence"]
        if not isinstance(digest, str) or not HASH.fullmatch(digest):
            raise LocalAliasError("invalid_alias_hash")
        if (not isinstance(name, str) or not 1 <= len(name) <= 64 or
                name != name.strip() or not name.isprintable() or
                any(char in "<>\\/\r\n" for char in name)):
            raise LocalAliasError("invalid_alias_name")
        if not isinstance(evidence, str) or evidence not in EVIDENCE:
            raise LocalAliasError("invalid_alias_evidence")
        if digest in aliases or name.casefold() in names:
            raise LocalAliasError("ambiguous_alias_mapping")
        aliases[digest] = name
        names.add(name.casefold())
    return aliases


def apply_aliases(inventory: dict[str, Any], aliases: dict[str, str]) -> dict[str, Any]:
    """Enrich only a registered-ID inventory; never replace device ID or status."""
    if not isinstance(inventory, dict) or inventory.get("state") != "REGISTRY_READ_ONLY":
        raise LocalAliasError("aliases_require_local_registry")
    if not isinstance(aliases, dict):
        raise LocalAliasError("invalid_alias_mapping")
    result = deepcopy(inventory)
    matched = 0
    for device in result["devices"]:
        identifier = device["device_id"]
        digest = hashlib.sha256(identifier.encode("utf-8")).hexdigest()
        name = aliases.get(digest)
        if name is not None:
            device["display_name"] = name
            device["name_source"] = "owner_private_exact_id_match"
            matched += 1
        else:
            device["display_name"] = identifier
            device["name_source"] = "unmatched"
    result["named_devices"] = matched
    result["unnamed_devices"] = len(result["devices"]) - matched
    return result
