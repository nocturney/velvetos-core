#!/usr/bin/env python3
"""Publish fingerprint guard sensor (#198) — repeated identical publish regression.

Replays the 2026-09-13 incident shape: one approved GRID-FOUNDATION publish,
then five more publishes of the SAME asset + caption, each with a FRESH valid
approval. Only the first may reach Graph; every repeat must be refused before
the approval is spent and before any media fetch. Ephemeral keys and in-memory
stores only — no network, no production secrets.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
import types
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT / "packages" / "vfigos" / "remote"))

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from vfigos.approval.issuer.signing import issue_approval
from vfigos.approval.media_bytes import (
    media_fetch_count,
    reset_media_fetch_count,
    set_media_byte_fetcher_override,
    sha256_hex,
)
from vfigos.approval.publish_fingerprint import (
    DEFAULT_WINDOW_SECONDS,
    MemoryFingerprintStore,
    UnavailableFingerprintStore,
    check_fingerprint,
    default_fingerprint_store_from_env,
    is_definite_failure,
    publish_fingerprint,
    window_seconds_from_env,
)
from vfigos.approval.schema import ALGORITHM, DEFAULT_IG_USER_ID
from vfigos.approval.spend import MemorySpendStore

NAME = "publish-fingerprint"


def fail(msg: str) -> None:
    print(f"FAIL {NAME}: {msg}", file=sys.stderr)
    raise SystemExit(1)


BYTES_A = b"grid-foundation-01-bytes"
BYTES_B = b"grid-foundation-02-bytes"
DIG_A = sha256_hex(BYTES_A)
DIG_B = sha256_hex(BYTES_B)
URL_A = f"https://cas.example.test/sha256/{DIG_A}/a.jpg"
URL_B = f"https://cas.example.test/sha256/{DIG_B}/b.jpg"
MEDIA = {URL_A: BYTES_A, URL_B: BYTES_B}
CONTENT = "GRID-FOUNDATION-01"
PKG = "b" * 64
CAPTION = "GRID FOUNDATION 01\n#VelvetFactory"


def _fetcher(url: str) -> bytes:
    if url not in MEDIA:
        raise ValueError(f"unknown media URL: {url}")
    return MEDIA[url]


def unit_checks() -> None:
    base = dict(ig_user_id=DEFAULT_IG_USER_ID, media_sha256s=[DIG_A], caption=CAPTION)
    fp = publish_fingerprint(**base)
    if fp != publish_fingerprint(**base):
        fail("fingerprint must be deterministic")
    if fp != publish_fingerprint(**{**base, "caption": "  GRID FOUNDATION 01 \n\n #VelvetFactory  "}):
        fail("whitespace-only caption changes must not dodge the fingerprint")
    if fp != publish_fingerprint(**{**base, "media_sha256s": json.dumps([DIG_A])}):
        fail("compact JSON claim string and list must fingerprint identically")
    # NFC: composed vs decomposed é
    if publish_fingerprint(**{**base, "caption": "caf\u00e9"}) != publish_fingerprint(
        **{**base, "caption": "cafe\u0301"}
    ):
        fail("NFC-equivalent captions must fingerprint identically")
    for label, change in (
        ("caption", {"caption": CAPTION + " v2"}),
        ("media", {"media_sha256s": [DIG_B]}),
        ("account", {"ig_user_id": "17840000000000000"}),
        ("carousel order", {"media_sha256s": [DIG_B, DIG_A]}),
    ):
        if publish_fingerprint(**{**base, **change}) == fp:
            fail(f"different {label} must change the fingerprint")
    for bad in ([], None, ["NOTHEX"]):
        try:
            publish_fingerprint(**{**base, "media_sha256s": bad})
        except (TypeError, ValueError):
            pass
        else:
            fail(f"media_sha256s={bad!r} must be rejected")

    store = MemoryFingerprintStore()
    now = 1_800_000_000.0
    if check_fingerprint(fp, store=store, window_seconds=3600, now=now).status != "clear":
        fail("empty store must be clear")
    store.record(fp, at=now - 10)
    c = check_fingerprint(fp, store=store, window_seconds=3600, now=now)
    if c.ok or c.status != "repeat_within_window":
        fail(f"repeat inside window must be refused, got {c}")
    if not check_fingerprint(fp, store=store, window_seconds=5, now=now).ok:
        fail("record older than the window must be clear")
    if check_fingerprint(fp, store=store, window_seconds=0, now=now).status != "disabled":
        fail("window 0 must report disabled")
    c = check_fingerprint(fp, store=UnavailableFingerprintStore(), window_seconds=3600, now=now)
    if c.ok or c.status != "store_unavailable":
        fail("unavailable store must fail closed")

    if not isinstance(default_fingerprint_store_from_env({}), UnavailableFingerprintStore):
        fail("no bucket configured must yield the fail-closed store")
    if window_seconds_from_env({}) != DEFAULT_WINDOW_SECONDS:
        fail("default window mismatch")
    if window_seconds_from_env({"VELVET_PUBLISH_FINGERPRINT_WINDOW_SECONDS": "0"}) != 0:
        fail("operator override 0 must disable")

    matrix = [
        ({"id": "1789"}, False),
        ({"ok": True}, False),
        ({"ok": False, "write_outcome": "unknown"}, False),
        ({"ok": False, "write_outcome": "not_sent"}, True),
        ({"ok": False, "write_outcome": "rejected"}, True),
        ({"ok": False, "blocked": True}, True),
        (None, False),
    ]
    for result, expected in matrix:
        if is_definite_failure(result) is not expected:
            fail(f"is_definite_failure({result!r}) must be {expected}")


def install_stub_gate():
    stub_pkg = types.ModuleType("instagram_mcp")
    stub_server = types.ModuleType("instagram_mcp.server")

    def _orig_guard(tool_name, params, impl):
        return impl()

    stub_server._guard = _orig_guard
    sys.modules["instagram_mcp"] = stub_pkg
    sys.modules["instagram_mcp.server"] = stub_server
    stub_pkg.server = stub_server
    import delivery_approval_gate as dag

    dag.apply_delivery_approval_gate(None)
    return stub_server, dag


def e2e_checks() -> None:
    set_media_byte_fetcher_override(_fetcher)
    priv = Ed25519PrivateKey.generate()
    key_id = "fp-sensor-key"
    reg = Path(tempfile.mkdtemp()) / "registry.json"
    reg.write_text(
        json.dumps(
            {
                "keys": [
                    {
                        "key_id": key_id,
                        "algorithm": ALGORITHM,
                        "public_key_b64": base64.b64encode(priv.public_key().public_bytes_raw()).decode(),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    os.environ["VELVET_DELIVERY_APPROVAL_REGISTRY"] = str(reg)
    os.environ["INSTAGRAM_MCP_IG_USER_ID"] = DEFAULT_IG_USER_ID
    os.environ.pop("VELVET_DELIVERY_APPROVAL_SPEND_BUCKET", None)

    server, dag = install_stub_gate()
    spend = MemorySpendStore()
    claims = {"n": 0}

    class CountingSpend:
        def claim(self, approval_id, *, meta=None):
            claims["n"] += 1
            return spend.claim(approval_id, meta=meta)

    fp_store = MemoryFingerprintStore()
    dag._spend_store = lambda: CountingSpend()
    dag._fingerprint_store = lambda: fp_store
    dag._fingerprint_window_seconds = lambda: DEFAULT_WINDOW_SECONDS

    graph = {"n": 0}

    def publish(caption=CAPTION, url=URL_A, blob=BYTES_A, outcome=None):
        payload = {"image_url": url, "caption": caption, "account": "velvets_cloud"}
        issued = issue_approval(
            private_key=priv,
            key_id=key_id,
            content_id=CONTENT,
            package_sha256=PKG,
            mutation_tool="publish_image",
            mutation_payload=payload,
            media_artifacts=[{"bytes_b64": base64.b64encode(blob).decode()}],
            media_byte_fetcher=_fetcher,
            ttl_seconds=600,
            now=datetime.now(timezone.utc),
        )
        if not issued["ok"]:
            fail(f"issue failed: {issued}")

        def impl():
            graph["n"] += 1
            return outcome if outcome is not None else {"account": "velvets_cloud", "id": f"1789{graph['n']}"}

        params = {**payload, "delivery_approval": issued["receipt"], "content_id": CONTENT, "package_sha256": PKG}
        return server._guard("publish_image", params, impl)

    # 1. First approved publish reaches Graph and records its fingerprint.
    first = publish()
    if not isinstance(first, dict) or first.get("blocked") or graph["n"] != 1:
        fail(f"first approved publish must reach Graph, got {first}")
    if not first.get("publish_fingerprint_recorded"):
        fail("first publish must record its fingerprint")

    # 2. Incident replay: five more identical publishes, each with a FRESH approval.
    for i in range(5):
        reset_media_fetch_count()
        before = claims["n"]
        out = publish()
        if not isinstance(out, dict) or not out.get("blocked"):
            fail(f"repeat #{i + 1} of identical publish must be BLOCKED, got {out}")
        if "repeat_within_window" not in " ".join(out.get("problems") or []):
            fail(f"repeat #{i + 1} must cite repeat_within_window")
        if claims["n"] != before:
            fail(f"repeat #{i + 1} must be refused BEFORE approval spend")
        if media_fetch_count() != 0:
            fail(f"repeat #{i + 1} must be refused before any media fetch")
    if graph["n"] != 1:
        fail(f"identical publish reached Graph {graph['n']} times; expected exactly 1")

    # 3. Whitespace-only caption edits do not dodge the guard.
    if not publish(caption="  " + CAPTION.replace("\n", "   ") + " ").get("blocked"):
        fail("whitespace-only caption variant must be BLOCKED")

    # 4. A genuinely different asset or caption is allowed.
    if publish(url=URL_B, blob=BYTES_B).get("blocked"):
        fail("different asset must be allowed")
    if publish(caption=CAPTION + " (edit)").get("blocked"):
        fail("different caption must be allowed")

    # 5. Ambiguous media_publish outcome counts as possibly-live ⇒ repeat refused.
    amb_caption = "ambiguous outcome"
    amb = publish(caption=amb_caption, outcome={"ok": False, "write_outcome": "unknown", "retry_safety": "reconcile_only"})
    if amb.get("blocked"):
        fail("ambiguous first attempt itself must reach Graph")
    if not publish(caption=amb_caption).get("blocked"):
        fail("retry after ambiguous outcome must be BLOCKED (reconcile with list_media first)")

    # 6. Definite failure (nothing live) ⇒ not recorded ⇒ fresh-approval retry allowed.
    nf_caption = "container failed before publish"
    publish(caption=nf_caption, outcome={"ok": False, "write_outcome": "not_sent", "retry_safety": "safe_with_fresh_approval"})
    if publish(caption=nf_caption).get("blocked"):
        fail("retry after a definite not_sent failure must be allowed")

    # 7. Store unavailable ⇒ fail closed before spend.
    dag._fingerprint_store = lambda: UnavailableFingerprintStore()
    before = claims["n"]
    out = publish(caption="store down")
    if not out.get("blocked") or claims["n"] != before:
        fail("unavailable fingerprint store must block before spend")
    dag._fingerprint_store = lambda: fp_store

    # 8. Operator override (window 0) disables the guard.
    dag._fingerprint_window_seconds = lambda: 0
    if publish().get("blocked"):
        fail("window 0 operator override must allow")
    dag._fingerprint_window_seconds = lambda: DEFAULT_WINDOW_SECONDS

    # 9. Non-publish mutations are unaffected.
    if dag._pending_fingerprint_ctx.get() is not None:
        fail("pending fingerprint must be cleared after each call")


def source_contract() -> None:
    src = (ROOT / "packages/vfigos/remote/delivery_approval_gate.py").read_text(encoding="utf-8")
    fp_at = src.find("check_fingerprint(fingerprint")
    claim_at = src.find("claimed = claim_authorization(")
    if fp_at < 0 or claim_at < 0 or fp_at > claim_at:
        fail("fingerprint check must run before claim_authorization (before approval spend)")
    if "_run_and_record_fingerprint" not in src:
        fail("guard must record fingerprints after the Graph write")


def main() -> int:
    unit_checks()
    e2e_checks()
    source_contract()
    print(
        f"OK {NAME} repeated_identical_publish=BLOCKED(5/5 before spend) graph_calls=1 "
        f"window_default={DEFAULT_WINDOW_SECONDS}s ambiguous=BLOCK not_sent=ALLOW store_down=BLOCK"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
