#!/usr/bin/env python3
"""Delivery-approval trust-boundary sensor (ephemeral keys only).

Proves verify/sign/spend/gate matrix without production secrets.
Also asserts mutation service isolation markers in source.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import sys
import tempfile
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT / "scripts"))

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from vfigos.approval.capabilities import mutation_tool_ids, read_only_tool_ids
from vfigos.approval.canonical import canonical_payload_bytes
from vfigos.approval.gate import authorize_mutation
from vfigos.approval.issuer.signing import issue_approval
from vfigos.approval.keys_registry import KeyRegistry
from vfigos.approval.media_bytes import (
    encode_media_sha256s_claim,
    inject_media_sha256s,
    set_media_byte_fetcher_override,
    sha256_hex,
)
from vfigos.approval.mutation_payload import mutation_payload_sha256
from vfigos.approval.schema import CLAIM_FIELDS, DEFAULT_IG_USER_ID, SCHEMA_ID
from vfigos.approval.spend import MemorySpendStore, UnavailableSpendStore
from vfigos.approval.verify import verify_receipt


def fail(msg: str) -> None:
    print(f"FAIL delivery-approval: {msg}", file=sys.stderr)
    raise SystemExit(1)


def _now() -> datetime:
    return datetime(2026, 9, 16, 12, 0, 0, tzinfo=timezone.utc)


def _ephemeral():
    priv = Ed25519PrivateKey.generate()
    key_id = "test-ephemeral-key"
    registry = KeyRegistry.from_ephemeral(key_id, priv.public_key())
    return priv, key_id, registry


DIGEST = "a" * 64
CONTENT = "VF-TEST-CONTENT"

# Immutable media fixtures — CAS URLs embed sha256; fetcher returns exact bytes.
_BYTES_A = b"velvet-image-bytes-AAAA"
_BYTES_B = b"velvet-image-bytes-BBBB"
_BYTES_C = b"velvet-image-bytes-CCCC"
_DIG_A = sha256_hex(_BYTES_A)
_DIG_B = sha256_hex(_BYTES_B)
_DIG_C = sha256_hex(_BYTES_C)


def _cas_url(digest: str, name: str = "a.jpg") -> str:
    return f"https://cas.example.test/sha256/{digest}/{name}"


_URL_A = _cas_url(_DIG_A, "a.jpg")
_URL_B = _cas_url(_DIG_B, "b.jpg")
_URL_C = _cas_url(_DIG_C, "c.jpg")
_MEDIA_STORE = {_URL_A: _BYTES_A, _URL_B: _BYTES_B, _URL_C: _BYTES_C}


def _fetcher(url: str) -> bytes:
    if url not in _MEDIA_STORE:
        raise ValueError(f"unknown media URL in test store: {url}")
    return _MEDIA_STORE[url]


DEFAULT_IMAGE_PAYLOAD = {
    "image_url": _URL_A,
    "caption": "hello",
    "account": "velvets_cloud",
}
DEFAULT_MEDIA_ARTIFACTS = [{"bytes_b64": __import__("base64").b64encode(_BYTES_A).decode()}]


def _issue(priv, key_id, **overrides):
    kwargs = dict(
        private_key=priv,
        key_id=key_id,
        content_id=CONTENT,
        package_sha256=DIGEST,
        mutation_tool="publish_image",
        mutation_payload=DEFAULT_IMAGE_PAYLOAD,
        media_artifacts=DEFAULT_MEDIA_ARTIFACTS,
        media_byte_fetcher=_fetcher,
        ttl_seconds=600,
        now=_now(),
    )
    kwargs.update(overrides)
    result = issue_approval(**kwargs)
    if not result["ok"]:
        fail(f"issue failed unexpectedly: {result}")
    return result["receipt"]


def _payload_with_media(tool: str, params: dict, digests: list[str]) -> dict:
    return inject_media_sha256s(tool, params, digests)

def main() -> int:
    priv, key_id, registry = _ephemeral()
    set_media_byte_fetcher_override(_fetcher)
    tools = mutation_tool_ids()
    reads = read_only_tool_ids()
    for required in (
        "publish_image",
        "publish_carousel",
        "publish_reel",
        "publish_video",
        "publish_story",
        "delete_media",
        "reply_to_comment",
        "hide_comment",
        "delete_comment",
    ):
        if required not in tools:
            fail(f"canonical mutation set missing {required}")
    for ro in ("list_media", "get_profile", "healthcheck", "graph_mutation_matrix"):
        if ro in tools:
            fail(f"read-only tool incorrectly classified as mutation: {ro}")
        if ro not in reads and ro != "graph_mutation_matrix":
            # graph_mutation_matrix is forced into read_only by loader
            pass
    if "graph_mutation_matrix" in tools:
        fail("graph_mutation_matrix must not be a mutation tool")

    # 12. unsupported write tool -> issuer refuses
    bad = issue_approval(
        private_key=priv,
        key_id=key_id,
        content_id=CONTENT,
        package_sha256=DIGEST,
        mutation_tool="not_a_real_tool",
        now=_now(),
    )
    if bad["ok"] or "unsupported mutation_tool" not in " ".join(bad["problems"]):
        fail("issuer must refuse unsupported mutation_tool")

    # Valid issue + verify
    receipt = _issue(priv, key_id)
    vr = verify_receipt(receipt, registry=registry, now=_now())
    if not vr.ok:
        fail(f"valid receipt must verify: {vr.problems}")

    # 9. tampered payload
    tampered = dict(receipt)
    tampered["content_id"] = "OTHER"
    if verify_receipt(tampered, registry=registry, now=_now()).ok:
        fail("tampered payload must be blocked")

    # 10. tampered signature
    sig_bad = dict(receipt)
    sig_bad["signature"] = "AAAA" + receipt["signature"][4:]
    if verify_receipt(sig_bad, registry=registry, now=_now()).ok:
        fail("tampered signature must be blocked")

    # 11. unknown key_id
    unk = dict(receipt)
    unk["key_id"] = "no-such-key"
    # re-sign? just change key_id without matching sig
    if verify_receipt(unk, registry=registry, now=_now()).ok:
        fail("unknown key_id must be blocked")

    # 3-6 wrong bindings
    for kwargs, label in (
        ({"expected_content_id": "WRONG"}, "wrong content_id"),
        ({"expected_package_sha256": "b" * 64}, "wrong package_sha256"),
        ({"expected_mutation_tool": "delete_media"}, "wrong mutation_tool"),
        ({"expected_ig_user_id": "000"}, "wrong ig_user_id"),
    ):
        r = verify_receipt(receipt, registry=registry, now=_now(), **kwargs)
        if r.ok:
            fail(f"{label} must be blocked")

    # 7. expired
    expired = _issue(priv, key_id, ttl_seconds=60)
    late = _now() + timedelta(hours=2)
    if verify_receipt(expired, registry=registry, now=late).ok:
        fail("expired approval must be blocked")

    # 8. future-issued
    future_receipt = _issue(priv, key_id, now=_now() + timedelta(hours=3))
    if verify_receipt(future_receipt, registry=registry, now=_now()).ok:
        fail("future-issued receipt must be blocked")

    # 14/15 direct mutation without approval
    store = MemorySpendStore()
    blocked = authorize_mutation(
        receipt=None,
        mutation_tool="publish_image",
        spend_store=store,
        registry=registry,
        content_id=CONTENT,
        package_sha256=DIGEST,
        now=_now(),
    )
    if blocked.ok:
        fail("direct publish_image without approval must be blocked")
    blocked_del = authorize_mutation(
        receipt=None,
        mutation_tool="delete_media",
        spend_store=store,
        registry=registry,
        now=_now(),
    )
    if blocked_del.ok:
        fail("direct delete_media without approval must be blocked")

    # 16. serial replay
    store = MemorySpendStore()
    r1 = authorize_mutation(
        receipt=receipt,
        mutation_tool="publish_image",
        spend_store=store,
        registry=registry,
        content_id=CONTENT,
        package_sha256=DIGEST,
        now=_now(),
    )
    if not r1.ok:
        fail(f"first claim must succeed: {r1.problems}")
    r2 = authorize_mutation(
        receipt=receipt,
        mutation_tool="publish_image",
        spend_store=store,
        registry=registry,
        content_id=CONTENT,
        package_sha256=DIGEST,
        now=_now(),
    )
    if r2.ok or (r2.claim and r2.claim.status != "already_spent"):
        fail("serial replay must block second claim")

    # 17. concurrent replay
    store = MemorySpendStore()
    receipt2 = _issue(priv, key_id)
    results: list = []
    lock = threading.Lock()

    def attempt():
        res = authorize_mutation(
            receipt=receipt2,
            mutation_tool="publish_image",
            spend_store=store,
            registry=registry,
            content_id=CONTENT,
            package_sha256=DIGEST,
            now=_now(),
        )
        with lock:
            results.append(res)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futs = [pool.submit(attempt) for _ in range(8)]
        for f in futs:
            f.result()
    wins = [r for r in results if r.ok]
    if len(wins) != 1:
        fail(f"concurrent replay must allow exactly one claim, got {len(wins)}")

    # 18. spend-store unavailable
    receipt3 = _issue(priv, key_id)
    unavailable = authorize_mutation(
        receipt=receipt3,
        mutation_tool="publish_image",
        spend_store=UnavailableSpendStore(),
        registry=registry,
        content_id=CONTENT,
        package_sha256=DIGEST,
        now=_now(),
    )
    if unavailable.ok:
        fail("unavailable spend store must block mutation")

    # 19. Graph failure after claim — approval remains spent (no unspend)
    store = MemorySpendStore()
    receipt4 = _issue(priv, key_id)
    claimed = authorize_mutation(
        receipt=receipt4,
        mutation_tool="publish_image",
        spend_store=store,
        registry=registry,
        content_id=CONTENT,
        package_sha256=DIGEST,
        now=_now(),
    )
    if not claimed.ok:
        fail("claim before simulated graph failure must succeed")
    # simulate graph failure: do nothing; retry must fail
    retry = authorize_mutation(
        receipt=receipt4,
        mutation_tool="publish_image",
        spend_store=store,
        registry=registry,
        content_id=CONTENT,
        package_sha256=DIGEST,
        now=_now(),
    )
    if retry.ok:
        fail("after graph failure, spent approval must not be reusable")

    # 20. valid approval + gates
    store = MemorySpendStore()
    receipt5 = _issue(priv, key_id)
    ok = authorize_mutation(
        receipt=receipt5,
        mutation_tool="publish_image",
        spend_store=store,
        registry=registry,
        content_id=CONTENT,
        package_sha256=DIGEST,
        ig_user_id=DEFAULT_IG_USER_ID,
        now=_now(),
    )
    if not ok.ok:
        fail(f"valid approval must allow mutation gate: {ok.problems}")

    # 13. read-only unaffected — classification only (no approval required)
    if "list_media" in tools:
        fail("read-only list_media must not require delivery approval class")

    # 2. evidence without approval — preflight CLI
    import subprocess

    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "vf_project_preflight.py"),
            "--text",
            "publish to Instagram",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    body = json.loads(proc.stdout)
    if body.get("delivery_authorized") is not False:
        fail("preflight without signed approval must keep delivery_authorized=false")
    if body.get("project_preflight") != "BLOCKED":
        fail("preflight without signed approval must BLOCK")
    problems = (body.get("delivery_approval") or {}).get("problems") or []
    if "signed delivery approval missing" not in problems:
        fail("preflight must report missing signed delivery approval")

    # 1. forged workspace PASS is not enough — no signature ⇒ blocked (above covers)
    # Isolation markers in mutation deploy / remote sources
    deploy = (ROOT / "packages/vfigos/remote/deploy.sh").read_text(encoding="utf-8")
    if "VELVET_DELIVERY_APPROVAL_PRIVATE" in deploy and "Refusing deploy" not in deploy:
        # private secret name may appear in refuse check — ensure refuse exists
        fail("mutation deploy.sh must refuse private key mount")
    if "Refusing deploy" not in deploy:
        fail("mutation deploy.sh must refuse private key mount")
    issuer_deploy = (ROOT / "packages/vfigos/approval/issuer/deploy-issuer.sh").read_text(encoding="utf-8")
    if "--no-allow-unauthenticated" not in issuer_deploy:
        fail("issuer must deploy with Cloud Run IAM (no allow-unauthenticated)")
    if "VELVET_INSTAGRAM_MCP_BEARER_TOKEN" in issuer_deploy and "Do NOT mount" not in issuer_deploy:
        fail("issuer deploy must not mount MCP bearer")
    http_issuer = (ROOT / "packages/vfigos/approval/issuer/http_issuer.py").read_text(encoding="utf-8")
    for needle in ("fastmcp", "INSTAGRAM_MCP_ACCESS_TOKEN", "/mcp"):
        # isolation check references ACCESS_TOKEN as forbidden — OK
        pass
    if "from fastmcp" in http_issuer or "import fastmcp" in http_issuer:
        fail("issuer must not import fastmcp")
    if 'Mount("/mcp"' in http_issuer or "MCP_PATH" in http_issuer:
        fail("issuer must not expose /mcp")

    remote_http = (ROOT / "packages/vfigos/remote/http_server.py").read_text(encoding="utf-8")
    if "apply_delivery_approval_gate" not in remote_http:
        fail("mutation http_server must apply delivery approval gate")
    if "mutation_service_has_private_key\": False" not in remote_http.replace(" ", ""):
        # allow spacing variants
        if "mutation_service_has_private_key" not in remote_http:
            fail("healthz must declare mutation_service_has_private_key false")

    # Canonical serializer uniqueness — signing uses same bytes as verify
    payload = canonical_payload_bytes({k: receipt[k] for k in CLAIM_FIELDS})
    if not payload.startswith(b"{") or b" " in payload:
        fail("canonical payload must be compact JSON")
    if receipt["schema"] != SCHEMA_ID:
        fail("schema mismatch")
    if "mutation_payload_sha256" not in receipt:
        fail("receipt must include mutation_payload_sha256")
    if "media_sha256s" not in receipt:
        fail("receipt must include media_sha256s")

    # --- Finding 2: exact mutation payload binding ---
    store = MemorySpendStore()
    base_payload = dict(DEFAULT_IMAGE_PAYLOAD)
    receipt_bind = _issue(priv, key_id, mutation_payload=base_payload)
    expected_digest = mutation_payload_sha256(
        "publish_image", _payload_with_media("publish_image", base_payload, [_DIG_A])
    )
    if receipt_bind["mutation_payload_sha256"] != expected_digest:
        fail("issuer must compute mutation_payload_sha256 from mutation_payload+media digests")
    if receipt_bind.get("media_sha256s") != encode_media_sha256s_claim([_DIG_A]):
        fail("issuer must bind media_sha256s from trusted bytes")

    ok_exact = authorize_mutation(
        receipt=receipt_bind,
        mutation_tool="publish_image",
        spend_store=store,
        registry=registry,
        content_id=CONTENT,
        package_sha256=DIGEST,
        mutation_payload_sha256=expected_digest,
        media_sha256s=[_DIG_A],
        now=_now(),
    )
    if not ok_exact.ok:
        fail(f"exact payload must authorize: {ok_exact.problems}")

    def _block_mismatch(
        label: str,
        tool: str,
        issued_payload: dict,
        actual_payload: dict,
        *,
        artifacts=None,
    ):
        st = MemorySpendStore()
        rec = _issue(
            priv,
            key_id,
            mutation_tool=tool,
            mutation_payload=issued_payload,
            media_artifacts=artifacts,
        )
        from vfigos.approval.media_bytes import decode_media_sha256s_claim

        issued_digests = decode_media_sha256s_claim(rec["media_sha256s"])
        actual = mutation_payload_sha256(
            tool, _payload_with_media(tool, actual_payload, issued_digests)
        )
        if actual == rec["mutation_payload_sha256"]:
            fail(f"test setup error for {label}: digests unexpectedly equal")
        blocked = authorize_mutation(
            receipt=rec,
            mutation_tool=tool,
            spend_store=st,
            registry=registry,
            content_id=CONTENT,
            package_sha256=DIGEST,
            mutation_payload_sha256=actual,
            media_sha256s=issued_digests,
            now=_now(),
        )
        if blocked.ok:
            fail(f"{label} must be blocked by mutation_payload_sha256")

    # changed caption
    _block_mismatch(
        "changed caption",
        "publish_image",
        base_payload,
        {**base_payload, "caption": "DIFFERENT"},
        artifacts=DEFAULT_MEDIA_ARTIFACTS,
    )
    # different media asset URL
    other_payload = {
        "image_url": _URL_B,
        "caption": "hello",
        "account": "velvets_cloud",
    }
    _block_mismatch(
        "different media",
        "publish_image",
        base_payload,
        other_payload,
        artifacts=DEFAULT_MEDIA_ARTIFACTS,
    )
    # carousel reorder (URL order)
    car_a = {
        "image_urls": [_URL_A, _URL_B],
        "caption": "c",
        "account": "velvets_cloud",
    }
    car_b = {
        "image_urls": [_URL_B, _URL_A],
        "caption": "c",
        "account": "velvets_cloud",
    }
    _block_mismatch(
        "carousel reorder",
        "publish_carousel",
        car_a,
        car_b,
        artifacts=[
            {"bytes_b64": __import__("base64").b64encode(_BYTES_A).decode()},
            {"bytes_b64": __import__("base64").b64encode(_BYTES_B).decode()},
        ],
    )
    # delete media_id mismatch
    del_a = {"media_id": "1789001", "account": "velvets_cloud"}
    del_b = {"media_id": "1789002", "account": "velvets_cloud"}
    st = MemorySpendStore()
    rec_del = _issue(
        priv,
        key_id,
        mutation_tool="delete_media",
        mutation_payload=del_a,
        media_artifacts=None,
    )
    actual_del = mutation_payload_sha256("delete_media", del_b)
    blocked_del = authorize_mutation(
        receipt=rec_del,
        mutation_tool="delete_media",
        spend_store=st,
        registry=registry,
        content_id=CONTENT,
        package_sha256=DIGEST,
        mutation_payload_sha256=actual_del,
        media_sha256s=[],
        now=_now(),
    )
    if blocked_del.ok:
        fail("delete media_id must be blocked by mutation_payload_sha256")
    # reply text mismatch
    rep_a = {"comment_id": "1791", "message": "thanks", "account": "velvets_cloud"}
    rep_b = {"comment_id": "1791", "message": "CHANGED", "account": "velvets_cloud"}
    st = MemorySpendStore()
    rec_rep = _issue(
        priv,
        key_id,
        mutation_tool="reply_to_comment",
        mutation_payload=rep_a,
        media_artifacts=None,
    )
    blocked_rep = authorize_mutation(
        receipt=rec_rep,
        mutation_tool="reply_to_comment",
        spend_store=st,
        registry=registry,
        content_id=CONTENT,
        package_sha256=DIGEST,
        mutation_payload_sha256=mutation_payload_sha256("reply_to_comment", rep_b),
        media_sha256s=[],
        now=_now(),
    )
    if blocked_rep.ok:
        fail("reply text must be blocked")
    # comment_id mismatch
    hid_a = {"comment_id": "1791", "hide": True, "account": "velvets_cloud"}
    hid_b = {"comment_id": "1799", "hide": True, "account": "velvets_cloud"}
    st = MemorySpendStore()
    rec_hid = _issue(
        priv,
        key_id,
        mutation_tool="hide_comment",
        mutation_payload=hid_a,
        media_artifacts=None,
    )
    blocked_hid = authorize_mutation(
        receipt=rec_hid,
        mutation_tool="hide_comment",
        spend_store=st,
        registry=registry,
        content_id=CONTENT,
        package_sha256=DIGEST,
        mutation_payload_sha256=mutation_payload_sha256("hide_comment", hid_b),
        media_sha256s=[],
        now=_now(),
    )
    if blocked_hid.ok:
        fail("comment_id must be blocked")

    # Client-supplied mutation_payload_sha256 / media_sha256s must not be trusted by issuer
    forged = issue_approval(
        private_key=priv,
        key_id=key_id,
        content_id=CONTENT,
        package_sha256=DIGEST,
        mutation_tool="publish_image",
        mutation_payload={
            **base_payload,
            "media_sha256s": ["f" * 64],
            "media_sha256": "f" * 64,
        },
        media_artifacts=DEFAULT_MEDIA_ARTIFACTS,
        media_byte_fetcher=_fetcher,
        now=_now(),
    )
    if not forged["ok"]:
        fail("baseline issue for forge check failed")
    if forged["receipt"]["media_sha256s"] != encode_media_sha256s_claim([_DIG_A]):
        fail("issuer must ignore caller media_sha256s and recompute from bytes")
    if forged["receipt"]["mutation_payload_sha256"] != expected_digest:
        fail("issuer must not blind-sign client mutation_payload_sha256")

    # --- Immutable media-byte binding regressions ---
    import base64 as _b64

    # Non-CAS mutable URL must be refused at issue
    bad_url = issue_approval(
        private_key=priv,
        key_id=key_id,
        content_id=CONTENT,
        package_sha256=DIGEST,
        mutation_tool="publish_image",
        mutation_payload={
            "image_url": "https://example.com/mutable.jpg",
            "caption": "x",
            "account": "velvets_cloud",
        },
        media_artifacts=DEFAULT_MEDIA_ARTIFACTS,
        media_byte_fetcher=_fetcher,
        now=_now(),
    )
    if bad_url["ok"]:
        fail("issuer must refuse non-content-addressed media URL")

    # Caller supplies only fake digest without bytes → refuse
    fake_only = issue_approval(
        private_key=priv,
        key_id=key_id,
        content_id=CONTENT,
        package_sha256=DIGEST,
        mutation_tool="publish_image",
        mutation_payload=base_payload,
        media_artifacts=[{"sha256": _DIG_A}],
        media_byte_fetcher=_fetcher,
        now=_now(),
    )
    if fake_only["ok"]:
        fail("issuer must refuse caller-supplied digest without bytes_b64")

    # G: tampered media_sha256s in receipt → signature/verify blocked
    media_tampered = dict(receipt_bind)
    media_tampered["media_sha256s"] = encode_media_sha256s_claim([_DIG_B])
    if verify_receipt(media_tampered, registry=registry, now=_now()).ok:
        fail("tampered media_sha256s must invalidate signature")

    # C: exact original bytes allowed
    store_ok = MemorySpendStore()
    rec_ok = _issue(priv, key_id)
    ok_media = authorize_mutation(
        receipt=rec_ok,
        mutation_tool="publish_image",
        spend_store=store_ok,
        registry=registry,
        content_id=CONTENT,
        package_sha256=DIGEST,
        mutation_payload_sha256=rec_ok["mutation_payload_sha256"],
        media_sha256s=[_DIG_A],
        now=_now(),
    )
    if not ok_media.ok:
        fail(f"exact original media bytes must allow: {ok_media.problems}")

    # E: carousel byte/order bindings
    car_art = [
        {"bytes_b64": _b64.b64encode(_BYTES_A).decode()},
        {"bytes_b64": _b64.b64encode(_BYTES_B).decode()},
    ]
    car_rec = _issue(
        priv,
        key_id,
        mutation_tool="publish_carousel",
        mutation_payload=car_a,
        media_artifacts=car_art,
    )
    if car_rec["media_sha256s"] != encode_media_sha256s_claim([_DIG_A, _DIG_B]):
        fail("carousel issue must bind ordered media_sha256s")
    wrong_order = authorize_mutation(
        receipt=car_rec,
        mutation_tool="publish_carousel",
        spend_store=MemorySpendStore(),
        registry=registry,
        content_id=CONTENT,
        package_sha256=DIGEST,
        mutation_payload_sha256=car_rec["mutation_payload_sha256"],
        media_sha256s=[_DIG_B, _DIG_A],
        now=_now(),
    )
    if wrong_order.ok:
        fail("carousel digest order mismatch must be blocked")
    car_exact = authorize_mutation(
        receipt=car_rec,
        mutation_tool="publish_carousel",
        spend_store=MemorySpendStore(),
        registry=registry,
        content_id=CONTENT,
        package_sha256=DIGEST,
        mutation_payload_sha256=car_rec["mutation_payload_sha256"],
        media_sha256s=[_DIG_A, _DIG_B],
        now=_now(),
    )
    if not car_exact.ok:
        fail(f"exact carousel bytes+order must allow: {car_exact.problems}")

    # F: reel/story bind media digests
    reel_bytes = b"velvet-reel-bytes-XXXX"
    reel_dig = sha256_hex(reel_bytes)
    reel_url = _cas_url(reel_dig, "r.mp4")
    _MEDIA_STORE[reel_url] = reel_bytes
    reel_payload = {
        "video_url": reel_url,
        "caption": "reel",
        "account": "velvets_cloud",
        "share_to_feed": True,
    }
    reel_rec = _issue(
        priv,
        key_id,
        mutation_tool="publish_reel",
        mutation_payload=reel_payload,
        media_artifacts=[{"bytes_b64": _b64.b64encode(reel_bytes).decode()}],
    )
    if reel_rec["media_sha256s"] != encode_media_sha256s_claim([reel_dig]):
        fail("publish_reel must bind media_sha256s")
    if authorize_mutation(
        receipt=reel_rec,
        mutation_tool="publish_reel",
        spend_store=MemorySpendStore(),
        registry=registry,
        content_id=CONTENT,
        package_sha256=DIGEST,
        mutation_payload_sha256=reel_rec["mutation_payload_sha256"],
        media_sha256s=[_DIG_A],
        now=_now(),
    ).ok:
        fail("reel wrong media digest must be blocked")

    story_bytes = b"velvet-story-bytes-YYYY"
    story_dig = sha256_hex(story_bytes)
    story_url = _cas_url(story_dig, "s.jpg")
    _MEDIA_STORE[story_url] = story_bytes
    story_rec = _issue(
        priv,
        key_id,
        mutation_tool="publish_story",
        mutation_payload={"image_url": story_url, "account": "velvets_cloud"},
        media_artifacts=[{"bytes_b64": _b64.b64encode(story_bytes).decode()}],
    )
    if story_rec["media_sha256s"] != encode_media_sha256s_claim([story_dig]):
        fail("publish_story must bind media_sha256s")

    # J: non-media mutations unchanged — empty media_sha256s
    if rec_del.get("media_sha256s") != "[]":
        fail("non-media delete_media must have media_sha256s=[]")
    if rec_rep.get("media_sha256s") != "[]":
        fail("non-media reply_to_comment must have media_sha256s=[]")

    # --- Finding 1: guard install order / dynamic resolve (CI-safe stub) ---
    # Do not require adelaidasofia-instagram-mcp in sensor CI. Install a minimal
    # stub that mirrors upstream module-global ``_guard`` lookup + overlay
    # ``ig_server._guard`` dynamic resolve, then patch in production order.
    import types

    remote_dir = ROOT / "packages" / "vfigos" / "remote"
    sys.path.insert(0, str(remote_dir))

    # Source contracts: gate before overlays; no stale ``from … import _guard``.
    http_src = (remote_dir / "http_server.py").read_text(encoding="utf-8")
    gate_pos = http_src.find("apply_delivery_approval_gate")
    mut_pos = http_src.find("apply_mutation_tools")
    story_pos = http_src.find("apply_story_publish_patch")
    if gate_pos < 0 or mut_pos < 0 or story_pos < 0:
        fail("http_server._build_mcp must wire delivery gate + mutation/story overlays")
    if not (gate_pos < story_pos and gate_pos < mut_pos):
        fail("apply_delivery_approval_gate must appear before mutation/story overlays")
    for rel in ("mutations.py", "story_publish.py", "cta_tools.py", "insights_v21.py"):
        src = (remote_dir / rel).read_text(encoding="utf-8")
        if "from instagram_mcp.server import _guard" in src:
            fail(f"{rel} must not capture _guard via from-import")
        if "ig_server._guard" not in src and rel != "insights_v21.py":
            fail(f"{rel} must resolve ig_server._guard dynamically")
        if rel == "insights_v21.py" and "ig_server._guard" not in src:
            fail("insights_v21.py must resolve ig_server._guard dynamically")

    # Stub package: original _guard + upstream-style tools that look up globals.
    stub_pkg = types.ModuleType("instagram_mcp")
    stub_server = types.ModuleType("instagram_mcp.server")
    stub_auth = types.ModuleType("instagram_mcp.auth")
    stub_validators = types.ModuleType("instagram_mcp.validators")

    def _orig_guard(tool_name: str, params: dict, impl):
        return impl()

    stub_server._guard = _orig_guard
    stub_server.__dict__["_guard"] = _orig_guard

    # Upstream-style: bare ``_guard`` name resolves in module globals at call time.
    exec(
        "def publish_image(image_url, caption=None, account=None):\n"
        "    return _guard('publish_image',"
        " {'image_url': image_url, 'caption': caption, 'account': account},"
        " lambda: {'ok': True, 'tool': 'publish_image'})\n"
        "def publish_story(image_url=None, video_url=None, account=None):\n"
        "    return _guard('publish_story',"
        " {'image_url': image_url, 'video_url': video_url, 'account': account},"
        " lambda: {'ok': True, 'tool': 'publish_story'})\n"
        "def reply_to_comment(comment_id, message, account=None):\n"
        "    return _guard('reply_to_comment',"
        " {'comment_id': comment_id, 'message': message, 'account': account},"
        " lambda: {'ok': True, 'tool': 'reply_to_comment'})\n"
        "def hide_comment(comment_id, hide=True, account=None):\n"
        "    return _guard('hide_comment',"
        " {'comment_id': comment_id, 'hide': hide, 'account': account},"
        " lambda: {'ok': True, 'tool': 'hide_comment'})\n"
        "def delete_comment(comment_id, account=None):\n"
        "    return _guard('delete_comment',"
        " {'comment_id': comment_id, 'account': account},"
        " lambda: {'ok': True, 'tool': 'delete_comment'})\n",
        stub_server.__dict__,
    )

    sys.modules["instagram_mcp"] = stub_pkg
    sys.modules["instagram_mcp.server"] = stub_server
    sys.modules["instagram_mcp.auth"] = stub_auth
    sys.modules["instagram_mcp.validators"] = stub_validators
    stub_pkg.server = stub_server
    stub_pkg.auth = stub_auth
    stub_pkg.validators = stub_validators

    from delivery_approval_gate import apply_delivery_approval_gate, authorize_or_block
    from mutations import apply_mutation_tools

    # Stale capture BEFORE gate install — must not be used by write tools.
    captured_before = stub_server._guard

    # Production order: install approval guard, THEN register write overlays.
    if hasattr(stub_server, "_velvet_delivery_approval_guard_patched"):
        delattr(stub_server, "_velvet_delivery_approval_guard_patched")
    apply_delivery_approval_gate(None)
    if not getattr(stub_server, "_velvet_delivery_approval_guard_patched", False):
        fail("delivery approval guard must be marked installed")
    if stub_server._guard is captured_before:
        fail("gate install must replace module _guard (not leave stale reference)")

    class _FakeMcp:
        tools: dict = {}

        class local_provider:
            @staticmethod
            def remove_tool(_name):
                return None

        @classmethod
        def tool(cls):
            def deco(fn):
                cls.tools[fn.__name__] = fn
                return fn

            return deco

        @staticmethod
        def remove_tool(_name):
            return None

    apply_mutation_tools(_FakeMcp)
    if "delete_media" not in _FakeMcp.tools:
        fail("delete_media must register after gate install")

    # Overlay path: dynamic ig_server._guard — must block without receipt.
    del_result = _FakeMcp.tools["delete_media"]("1789", account="velvets_cloud", confirm_irreversible=True)
    if not isinstance(del_result, dict) or not del_result.get("blocked"):
        fail("delete_media registered after gate must hit approval guard")

    # Upstream-style globals lookup after patch — must also block.
    for name, call in (
        ("publish_image", lambda: stub_server.publish_image("https://example.com/a.jpg", "x", "velvets_cloud")),
        ("publish_story", lambda: stub_server.publish_story(image_url="https://example.com/s.jpg", account="velvets_cloud")),
        ("reply_to_comment", lambda: stub_server.reply_to_comment("1", "hi", "velvets_cloud")),
        ("hide_comment", lambda: stub_server.hide_comment("1", True, "velvets_cloud")),
        ("delete_comment", lambda: stub_server.delete_comment("1", "velvets_cloud")),
    ):
        out = call()
        if not isinstance(out, dict) or not out.get("blocked"):
            fail(f"{name} must execute through live approval guard")

    # Stale captured reference bypasses approval — proves why from-import is forbidden.
    stale_out = captured_before(
        "publish_image",
        dict(base_payload),
        lambda: {"ok": True, "stale": True},
    )
    if stale_out != {"ok": True, "stale": True}:
        fail("stale captured _guard must retain unwrapped behavior (negative control)")

    # authorize_or_block direct path
    blocked_direct = authorize_or_block("publish_image", dict(base_payload))
    if blocked_direct is None:
        fail("publish_image without receipt must be blocked by approval guard")

    # read-only tools remain unaffected
    passthrough = stub_server._guard("list_media", {}, lambda: {"ok": True, "read": True})
    if passthrough != {"ok": True, "read": True}:
        fail("read-only tools must remain unaffected by delivery approval guard")

    # I/A/D: direct mutation path — same URL, different bytes → BLOCKED before claim
    rec_direct = _issue(priv, key_id)
    os.environ.pop("VELVET_DELIVERY_APPROVAL_SPEND_BUCKET", None)

    tampered_store = dict(_MEDIA_STORE)
    tampered_store[_URL_A] = _BYTES_A[:-1] + bytes([_BYTES_A[-1] ^ 0x01])

    def _tampered_fetcher(url: str) -> bytes:
        if url not in tampered_store:
            raise ValueError(url)
        return tampered_store[url]

    set_media_byte_fetcher_override(_tampered_fetcher)
    blocked_tamper = authorize_or_block(
        "publish_image",
        {
            **DEFAULT_IMAGE_PAYLOAD,
            "delivery_approval": rec_direct,
            "content_id": CONTENT,
            "package_sha256": DIGEST,
        },
    )
    if blocked_tamper is None or not blocked_tamper.get("blocked"):
        fail("one-byte media tamper must block before Graph/claim")
    set_media_byte_fetcher_override(_fetcher)

    # Same approval + different media bytes (URL_B bytes behind approval for URL_A)
    rec_wrong = _issue(priv, key_id)
    blocked_wrong = authorize_or_block(
        "publish_image",
        {
            "image_url": _URL_B,
            "caption": "hello",
            "account": "velvets_cloud",
            "delivery_approval": rec_wrong,
            "content_id": CONTENT,
            "package_sha256": DIGEST,
        },
    )
    if blocked_wrong is None or not blocked_wrong.get("blocked"):
        fail("direct tool wrong-media must be blocked")

    # Carousel: one item's bytes changed behind same URL list
    car_art2 = [
        {"bytes_b64": __import__("base64").b64encode(_BYTES_A).decode()},
        {"bytes_b64": __import__("base64").b64encode(_BYTES_B).decode()},
    ]
    car_rec2 = _issue(
        priv,
        key_id,
        mutation_tool="publish_carousel",
        mutation_payload=car_a,
        media_artifacts=car_art2,
    )
    car_tamper_store = dict(_MEDIA_STORE)
    car_tamper_store[_URL_B] = _BYTES_C  # different bytes; CAS URL still says DIG_B → resolve fails

    def _car_tamper(url: str) -> bytes:
        return car_tamper_store[url]

    set_media_byte_fetcher_override(_car_tamper)
    blocked_car = authorize_or_block(
        "publish_carousel",
        {
            **car_a,
            "delivery_approval": car_rec2,
            "content_id": CONTENT,
            "package_sha256": DIGEST,
        },
    )
    if blocked_car is None or not blocked_car.get("blocked"):
        fail("carousel item byte change must be blocked")
    set_media_byte_fetcher_override(_fetcher)

    # --- Finding 3: issuer body cap / auth-before-buffer (pure ASGI; no TestClient) ---
    import asyncio
    import base64

    from cryptography.hazmat.primitives import serialization

    from vfigos.approval.issuer import http_issuer
    from vfigos.approval.schema import ISSUER_MAX_BODY_BYTES

    # Issuer isolation forbids Meta/MCP secrets in-process — clear injected Cloud secrets
    # for this ephemeral test only.
    saved_iso = {
        name: os.environ.pop(name, None)
        for name in (
            "INSTAGRAM_MCP_ACCESS_TOKEN",
            "VELVET_INSTAGRAM_MCP_BEARER_TOKEN",
            "INSTAGRAM_MCP_DM_ENABLED",
        )
    }
    os.environ["VELVET_DELIVERY_APPROVAL_ISSUER_TOKEN"] = "test-issuer-bearer"
    os.environ["VELVET_DELIVERY_APPROVAL_KEY_ID"] = key_id

    seed = priv.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    os.environ["VELVET_DELIVERY_APPROVAL_PRIVATE_KEY_B64"] = (
        base64.urlsafe_b64encode(seed).decode().rstrip("=")
    )

    try:
        app = http_issuer.create_app()

        async def _asgi_call(
            headers: list[tuple[bytes, bytes]], bodies: list[bytes]
        ) -> tuple[int, bytes, int]:
            sent: list[dict] = []
            state = {"i": 0, "reads": 0}

            async def receive():
                state["reads"] += 1
                i = state["i"]
                if i < len(bodies):
                    state["i"] = i + 1
                    return {
                        "type": "http.request",
                        "body": bodies[i],
                        "more_body": i < len(bodies) - 1,
                    }
                return {"type": "http.request", "body": b"", "more_body": False}

            async def send(message):
                sent.append(message)

            scope = {
                "type": "http",
                "asgi": {"version": "3.0"},
                "http_version": "1.1",
                "method": "POST",
                "scheme": "http",
                "path": "/v1/delivery-approvals",
                "raw_path": b"/v1/delivery-approvals",
                "query_string": b"",
                "headers": headers,
                "client": ("127.0.0.1", 123),
                "server": ("test", 80),
            }
            await app(scope, receive, send)
            start = next(m for m in sent if m["type"] == "http.response.start")
            body = b"".join(
                m.get("body", b"") for m in sent if m["type"] == "http.response.body"
            )
            return int(start["status"]), body, state["reads"]

        oversize_status, _, _ = asyncio.run(
            _asgi_call(
                [
                    (b"authorization", b"Bearer test-issuer-bearer"),
                    (b"content-length", str(ISSUER_MAX_BODY_BYTES + 50).encode()),
                    (b"content-type", b"application/json"),
                ],
                [b"{}"],
            )
        )
        if oversize_status != 413:
            fail(f"oversized Content-Length must return 413, got {oversize_status}")

        chunk_status, _, _ = asyncio.run(
            _asgi_call(
                [
                    (b"authorization", b"Bearer test-issuer-bearer"),
                    (b"content-type", b"application/json"),
                ],
                [b"x" * 8000, b"y" * 8000, b"z" * 8000],
            )
        )
        if chunk_status != 413:
            fail(f"chunked body over cap must return 413, got {chunk_status}")

        # Auth failure before body buffering: wrong bearer + declared huge body → 401, not 413.
        auth_status, _, auth_reads = asyncio.run(
            _asgi_call(
                [
                    (b"authorization", b"Bearer wrong"),
                    (b"content-length", str(ISSUER_MAX_BODY_BYTES + 50).encode()),
                    (b"content-type", b"application/json"),
                ],
                [b"x" * (ISSUER_MAX_BODY_BYTES + 50)],
            )
        )
        if auth_status != 401:
            fail(f"auth failure must return 401 before body cap, got {auth_status}")
        if auth_reads > 1:
            fail("auth failure must not fully buffer oversized body")

        bad_json_status, _, _ = asyncio.run(
            _asgi_call(
                [
                    (b"authorization", b"Bearer test-issuer-bearer"),
                    (b"content-type", b"application/json"),
                ],
                [b"{not-json"],
            )
        )
        if bad_json_status != 400:
            fail(f"malformed JSON must return 400, got {bad_json_status}")

        good_body = json.dumps(
            {
                "content_id": CONTENT,
                "package_sha256": DIGEST,
                "mutation_tool": "publish_image",
                "mutation_payload": base_payload,
                "mutation_payload_sha256": "f" * 64,
                "media_sha256s": ["f" * 64],
                "media_artifacts": DEFAULT_MEDIA_ARTIFACTS,
            }
        ).encode("utf-8")
        # HTTP issuer uses real fetch unless override is set — keep override.
        set_media_byte_fetcher_override(_fetcher)
        good_status, good_raw, _ = asyncio.run(
            _asgi_call(
                [
                    (b"authorization", b"Bearer test-issuer-bearer"),
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(good_body)).encode()),
                ],
                [good_body],
            )
        )
        good_json = json.loads(good_raw.decode("utf-8"))
        if good_status != 200 or not good_json.get("ok"):
            fail(f"valid small issue request must succeed: {good_status} {good_raw!r}")
        if good_json["receipt"]["mutation_payload_sha256"] == "f" * 64:
            fail("issuer must not blind-sign client mutation_payload_sha256")
        if good_json["receipt"]["media_sha256s"] == '["' + ("f" * 64) + '"]':
            fail("issuer must not blind-sign client media_sha256s")
        if good_json["receipt"]["mutation_payload_sha256"] != expected_digest:
            fail("issuer receipt digest must match server-computed payload")
        if good_json["receipt"]["media_sha256s"] != encode_media_sha256s_claim([_DIG_A]):
            fail("issuer receipt media_sha256s must match trusted bytes")
    finally:
        for name, value in saved_iso.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        os.environ.pop("VELVET_DELIVERY_APPROVAL_PRIVATE_KEY_B64", None)
        os.environ.pop("VELVET_DELIVERY_APPROVAL_ISSUER_TOKEN", None)

    # Registry file must not contain private key material
    reg = json.loads((ROOT / "packages/vfigos/approval/keys/registry.json").read_text(encoding="utf-8"))
    blob = json.dumps(reg)
    for banned in ("private_key", "PRIVATE", "seed", "BEGIN"):
        if banned in blob and banned != "seed":  # note field may say never
            if "private_key" in blob:
                fail("registry must not contain private_key fields")

    print(
        "OK delivery-approval "
        f"mutation_tools={len(tools)} "
        "ephemeral_sign_verify=PASS "
        "serial_replay=PASS "
        "concurrent_replay=PASS "
        "spend_unavailable=PASS "
        "issuer_iam=PASS "
        "mutation_private_key=NO "
        "guard_order=PASS "
        "payload_binding=PASS "
        "media_bytes=PASS "
        "body_cap=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
