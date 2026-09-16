"""Load Ed25519 public keys from the canonical repository registry."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .schema import ALGORITHM

_DEFAULT_REGISTRY = Path(__file__).resolve().parent / "keys" / "registry.json"


@dataclass(frozen=True)
class PublicKeyRecord:
    key_id: str
    algorithm: str
    public_key_b64: str

    def public_key(self) -> Ed25519PublicKey:
        if self.algorithm != ALGORITHM:
            raise ValueError(f"unsupported algorithm: {self.algorithm}")
        raw = base64.b64decode(self.public_key_b64, validate=True)
        if len(raw) != 32:
            raise ValueError("Ed25519 public key must be 32 raw bytes")
        return Ed25519PublicKey.from_public_bytes(raw)


class KeyRegistry:
    """In-memory view of packages/vfigos/approval/keys/registry.json (or test double)."""

    def __init__(self, records: Mapping[str, PublicKeyRecord]):
        self._records = dict(records)

    @classmethod
    def from_path(cls, path: Path | None = None) -> "KeyRegistry":
        reg_path = path or _DEFAULT_REGISTRY
        data = json.loads(reg_path.read_text(encoding="utf-8"))
        return cls.from_mapping(data)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "KeyRegistry":
        records: dict[str, PublicKeyRecord] = {}
        for row in data.get("keys") or []:
            if not isinstance(row, dict):
                continue
            key_id = str(row.get("key_id") or "").strip()
            algo = str(row.get("algorithm") or "").strip()
            pub = str(row.get("public_key_b64") or "").strip()
            if not key_id or not pub:
                continue
            records[key_id] = PublicKeyRecord(key_id=key_id, algorithm=algo or ALGORITHM, public_key_b64=pub)
        return cls(records)

    @classmethod
    def from_ephemeral(cls, key_id: str, public_key: Ed25519PublicKey) -> "KeyRegistry":
        """Test helper — never use production keys."""
        raw = public_key.public_bytes_raw()
        rec = PublicKeyRecord(
            key_id=key_id,
            algorithm=ALGORITHM,
            public_key_b64=base64.b64encode(raw).decode("ascii"),
        )
        return cls({key_id: rec})

    def get(self, key_id: str) -> PublicKeyRecord | None:
        return self._records.get(key_id)

    def __contains__(self, key_id: object) -> bool:
        return isinstance(key_id, str) and key_id in self._records

    def key_ids(self) -> frozenset[str]:
        return frozenset(self._records)
