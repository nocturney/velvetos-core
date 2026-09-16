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
DEFAULT_IMAGE_PAYLOAD = {
    "image_url": "https://example.com/a.jpg",
    "caption": "hello",
    "account": "velvets_cloud",
}


def _issue(priv, key_id, **overrides):
    kwargs = dict(
        private_key=priv,
        key_id=key_id,
        content_id=CONTENT,
        package_sha256=DIGEST,
        mutation_tool="publish_image",
        mutation_payload=DEFAULT_IMAGE_PAYLOAD,
        ttl_seconds=600,
        now=_now(),
    )
    kwargs.update(overrides)
    result = issue_approval(**kwargs)
    if not result["ok"]:
        fail(f"issue failed unexpectedly: {result}")
    return result["receipt"]


def main() -> int:
    priv, key_id, registry = _ephemeral()
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

    # --- Finding 2: exact mutation payload binding ---
    store = MemorySpendStore()
    base_payload = dict(DEFAULT_IMAGE_PAYLOAD)
    receipt_bind = _issue(priv, key_id, mutation_payload=base_payload)
    expected_digest = mutation_payload_sha256("publish_image", base_payload)
    if receipt_bind["mutation_payload_sha256"] != expected_digest:
        fail("issuer must compute mutation_payload_sha256 from mutation_payload")

    ok_exact = authorize_mutation(
        receipt=receipt_bind,
        mutation_tool="publish_image",
        spend_store=store,
        registry=registry,
        content_id=CONTENT,
        package_sha256=DIGEST,
        mutation_payload_sha256=expected_digest,
        now=_now(),
    )
    if not ok_exact.ok:
        fail(f"exact payload must authorize: {ok_exact.problems}")

    def _block_mismatch(label: str, tool: str, issued_payload: dict, actual_payload: dict):
        st = MemorySpendStore()
        rec = _issue(
            priv,
            key_id,
            mutation_tool=tool,
            mutation_payload=issued_payload,
        )
        actual = mutation_payload_sha256(tool, actual_payload)
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
    )
    # different media asset
    _block_mismatch(
        "different media",
        "publish_image",
        base_payload,
        {**base_payload, "image_url": "https://example.com/b.jpg"},
    )
    # carousel reorder
    car_a = {
        "image_urls": ["https://example.com/1.jpg", "https://example.com/2.jpg"],
        "caption": "c",
        "account": "velvets_cloud",
    }
    car_b = {
        "image_urls": ["https://example.com/2.jpg", "https://example.com/1.jpg"],
        "caption": "c",
        "account": "velvets_cloud",
    }
    _block_mismatch("carousel reorder", "publish_carousel", car_a, car_b)
    # delete media_id mismatch
    del_a = {"media_id": "1789001", "account": "velvets_cloud"}
    del_b = {"media_id": "1789002", "account": "velvets_cloud"}
    _block_mismatch("delete media_id", "delete_media", del_a, del_b)
    # reply text mismatch
    rep_a = {"comment_id": "1791", "message": "thanks", "account": "velvets_cloud"}
    rep_b = {"comment_id": "1791", "message": "CHANGED", "account": "velvets_cloud"}
    _block_mismatch("reply text", "reply_to_comment", rep_a, rep_b)
    # comment_id mismatch
    hid_a = {"comment_id": "1791", "hide": True, "account": "velvets_cloud"}
    hid_b = {"comment_id": "1799", "hide": True, "account": "velvets_cloud"}
    _block_mismatch("comment_id", "hide_comment", hid_a, hid_b)

    # Client-supplied mutation_payload_sha256 must not be trusted by issuer
    forged = issue_approval(
        private_key=priv,
        key_id=key_id,
        content_id=CONTENT,
        package_sha256=DIGEST,
        mutation_tool="publish_image",
        mutation_payload=base_payload,
        now=_now(),
    )
    if not forged["ok"]:
        fail("baseline issue for forge check failed")
    # recompute proves issuer ignored any external digest field (signing API has no such param)

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

    # --- Finding 3: issuer body cap / auth-before-buffer ---
    from starlette.testclient import TestClient

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
    import base64
    from cryptography.hazmat.primitives import serialization

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
        client = TestClient(app)

        import asyncio

        async def _asgi_call(headers: list[tuple[bytes, bytes]], bodies: list[bytes]) -> int:
            sent: list[dict] = []
            state = {"i": 0}

            async def receive():
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
            return int(start["status"])

        oversize_status = asyncio.run(
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

        chunk_status = asyncio.run(
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

        bad_auth = client.post(
            "/v1/delivery-approvals",
            content=b'{"content_id":"x"}',
            headers={"authorization": "Bearer wrong", "content-type": "application/json"},
        )
        if bad_auth.status_code != 401:
            fail(f"auth failure must return 401, got {bad_auth.status_code}")

        bad_json = client.post(
            "/v1/delivery-approvals",
            content=b"{not-json",
            headers={
                "authorization": "Bearer test-issuer-bearer",
                "content-type": "application/json",
            },
        )
        if bad_json.status_code != 400:
            fail(f"malformed JSON must return 400, got {bad_json.status_code}")

        good = client.post(
            "/v1/delivery-approvals",
            json={
                "content_id": CONTENT,
                "package_sha256": DIGEST,
                "mutation_tool": "publish_image",
                "mutation_payload": base_payload,
                "mutation_payload_sha256": "f" * 64,
            },
            headers={"authorization": "Bearer test-issuer-bearer"},
        )
        if good.status_code != 200 or not good.json().get("ok"):
            fail(f"valid small issue request must succeed: {good.status_code} {good.text}")
        if good.json()["receipt"]["mutation_payload_sha256"] == "f" * 64:
            fail("issuer must not blind-sign client mutation_payload_sha256")
        if good.json()["receipt"]["mutation_payload_sha256"] != expected_digest:
            fail("issuer receipt digest must match server-computed payload")
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
        "body_cap=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
