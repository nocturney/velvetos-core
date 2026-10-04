#!/usr/bin/env python3
"""Offline sensor for Gmail brief OAuth/CID production path. No network, no send."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from email import message_from_bytes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))

from vfops import gmail_brief_send as sender  # noqa: E402
from vfops import gmail_apps_script_request as bridge  # noqa: E402
from vfops.gmail_brief_request import build_safe_mime, encode_subject  # noqa: E402


def fail(msg: str) -> None:
    print(f"FAIL {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    required = [
        ROOT / "packages" / "vfops" / "gmail_brief_send.py",
        ROOT / "packages" / "vfops" / "gmail_oauth_bootstrap.py",
        ROOT / "packages" / "vfops" / "gmail_brief_request.py",
        ROOT / "packages" / "vfops" / "gmail_apps_script_request.py",
        ROOT / "packages" / "vfops" / "apps_script_gmail_bridge" / "Code.gs",
        ROOT / "packages" / "vfops" / "apps_script_gmail_bridge" / "appsscript.json",
        ROOT / ".github" / "workflows" / "gmail-brief-send.yml",
        ROOT / "packages" / "vfops" / "out" / "gmail-send-request.json",
        ROOT / "packages" / "velvetos" / "policy" / "gmail.send.json",
        ROOT / "packages" / "velvetos" / "policy" / "gmail-send-test-vectors.json",
        ROOT / "scripts" / "vf_gmail_send_policy.py",
        ROOT / "constitution" / "SEND.md",
        ROOT / "scripts" / "vf_send_preflight.py",
        ROOT / "scripts" / "generate-stage4e-gmail-send-report.py",
        ROOT / "packages" / "velvetos" / "policy" / "reports" / "stage4e-gmail-send-simplification.json",
        ROOT / "constitution" / "VISIBLE_TEXT.md",
    ]
    for path in required:
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")

    gmail_policy = json.loads((ROOT / "packages/velvetos/policy/gmail.send.json").read_text(encoding="utf-8"))
    if gmail_policy.get("schema") != "velvetos.gmail-send-policy.v1":
        fail("gmail.send machine policy schema drift")
    if gmail_policy.get("policy_id") != "gmail.send" or gmail_policy.get("status") != "ACTIVE_STAGE4E":
        fail("gmail.send machine policy identity/status drift")
    if gmail_policy.get("version") != 1:
        fail("gmail.send machine policy version drift")
    if set(gmail_policy.get("routine_scopes") or []) != {"owner_brief", "known_thread_reply", "routine_forward"}:
        fail("gmail.send routine scopes drift")
    if gmail_policy.get("commitment_receipt_mode") != "EXACT_ACTION_ON_COMMITMENT":
        fail("gmail.send commitment receipt mode drift")
    triggers = gmail_policy.get("restricted_triggers") or {}
    expected_triggers = {
        "new_commercial_commitment": "REQUIRE_OWNER_APPROVAL",
        "price_or_spend": "REQUIRE_OWNER_APPROVAL",
        "rights_privacy_ambiguity": "REQUIRE_OWNER_APPROVAL",
        "unverified_fact": "DENY",
        "blast": "DENY",
    }
    if triggers != expected_triggers:
        fail(f"gmail.send restricted trigger drift: {triggers}")

    policy_test = subprocess.run(
        [sys.executable, str(ROOT / "scripts/vf_gmail_send_policy.py"), "--self-test"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    if policy_test.returncode != 0:
        fail("gmail.send policy vectors failed: " + (policy_test.stderr.strip() or policy_test.stdout.strip()))
    if "OK gmail.send vectors=19 routine_owner_prompt=0 commitment_exact_binding=YES" not in policy_test.stdout:
        fail("gmail.send policy vector summary drift")

    send_law = (ROOT / "constitution/SEND.md").read_text(encoding="utf-8")
    for needle in (
        "policy_id: gmail.send",
        "Routine send בלי ceremony מיותר",
        "known_thread_reply",
        "approved_static_copy",
        "EXACT_ACTION_ON_COMMITMENT",
        "blast",
    ):
        if needle not in send_law:
            fail(f"SEND.md missing Stage 4E contract marker {needle!r}")

    preflight = (ROOT / "scripts/vf_send_preflight.py").read_text(encoding="utf-8")
    for needle in (
        "transport diagnostics only",
        '"transport_only": True',
        '"authorization_policy_id": "gmail.send"',
        '"authorization_evaluator": "scripts/vf_gmail_send_policy.py"',
    ):
        if needle not in preflight:
            fail(f"vf_send_preflight.py missing Gmail transport/auth separation {needle!r}")

    action_vectors = json.loads((ROOT / "packages/velvetos/policy/action-receipt-test-vectors.json").read_text(encoding="utf-8"))
    action_vector_ids = {row.get("id") for row in action_vectors.get("vectors") or []}
    for vector_id in (
        "gmail-commitment-exact-body-valid",
        "gmail-commitment-missing-exact-body-blocked",
        "gmail-routine-reply-does-not-require-exact-action-binding",
    ):
        if vector_id not in action_vector_ids:
            fail(f"action receipt contract missing Stage 4E vector {vector_id}")

    report = json.loads((ROOT / "packages/velvetos/policy/reports/stage4e-gmail-send-simplification.json").read_text(encoding="utf-8"))
    if report.get("schema") != "velvetos.stage4e-gmail-send-simplification.v1" or report.get("stage") != "4E":
        fail("Stage 4E Gmail report schema/stage drift")
    if report.get("policy_id") != "gmail.send" or report.get("repository_acceptance") != "PASS":
        fail("Stage 4E Gmail report identity/acceptance drift")
    routine = report.get("routine_happy_path") or {}
    if routine.get("owner_prompt_count") != 0 or routine.get("requires_exact_action_receipt") is not False:
        fail("Stage 4E routine Gmail path regained approval ceremony")
    if routine.get("routine_vectors_all_allow") is not True:
        fail("Stage 4E routine Gmail vectors no longer all ALLOW")
    summary = report.get("vector_summary") or {}
    if summary.get("count") != 19 or summary.get("decision_counts") != {"ALLOW": 5, "REQUIRE_OWNER_APPROVAL": 5, "DENY": 9}:
        fail("Stage 4E Gmail decision distribution drift")
    if report.get("transport_output_proves_non_authority") is not True:
        fail("Stage 4E Gmail transport/auth separation not proven")
    if (report.get("approved_static_copy") or {}).get("full_rewrite_pipeline_rerun_required_when_exact_and_current") is not False:
        fail("Stage 4E approved static copy regained rewrite ceremony")
    gated = report.get("gated_cases") or {}
    if gated.get("commitment_receipt_mode") != "EXACT_ACTION_ON_COMMITMENT" or gated.get("exact_owner_approval_body_binding_required") is not True:
        fail("Stage 4E commitment exact-binding contract drift")

    visible_text = (ROOT / "constitution/VISIBLE_TEXT.md").read_text(encoding="utf-8")
    for needle in ("approved_static_copy", "body_sha256", "אין חובה להריץ שוב rewrite/Humanizer מלא"):
        if needle not in visible_text:
            fail(f"VISIBLE_TEXT.md missing Stage 4E static-copy reuse marker {needle!r}")

    workflow = (ROOT / ".github" / "workflows" / "gmail-brief-send.yml").read_text(encoding="utf-8")
    for needle in (
        "GMAIL_APPS_SCRIPT_URL",
        "GMAIL_APPS_SCRIPT_SECRET",
        "gmail_apps_script_request",
        "VFBRIEF_ALLOWED_RECIPIENT",
        "contents: read",
    ):
        if needle not in workflow:
            fail(f"workflow missing {needle}")
    if "GMAIL_OAUTH_JSON" in workflow:
        fail("workflow still references retired GMAIL_OAUTH_JSON transport")

    request = json.loads((ROOT / "packages" / "vfops" / "out" / "gmail-send-request.json").read_text())
    if request.get("enabled") is not False:
        fail("bootstrap send request must be disabled on main")
    if request.get("to") != "nocturney@gmail.com":
        fail("send request owner recipient lock changed")
    expected_transport = {
        "html": "packages/vfops/out/morning-green-current.html",
        "visibleText": "packages/vfops/out/morning-green-current.txt",
        "images": "packages/vfops/out/morning-green-assets-current",
        "retentionMode": "rolling-current-transport",
    }
    for key, expected in expected_transport.items():
        if request.get(key) != expected:
            fail(f"Morning Green rolling transport path drift: {key}={request.get(key)!r}")

    original_refresh = sender._refresh_authorized_user

    def synthetic_refresh_failure(data: dict) -> str:
        raise RuntimeError("synthetic refresh failure")

    sender._refresh_authorized_user = synthetic_refresh_failure
    try:
        try:
            sender._token_from_mapping(
                {
                    "type": "authorized_user",
                    "client_id": "client",
                    "client_secret": "secret",
                    "refresh_token": "refresh",
                    "token": "stale-access-token",
                }
            )
        except RuntimeError as exc:
            if "synthetic refresh failure" not in str(exc):
                fail(f"unexpected OAuth refresh failure: {exc}")
        else:
            fail("authorized_user refresh failure fell back to stale access token")
    finally:
        sender._refresh_authorized_user = original_refresh

    raw = "ZmFrZS1yZmM4MjI"
    sig1 = bridge._signature(
        "test-secret",
        request_id="req-1",
        issued_at=1234567890,
        to="nocturney@gmail.com",
        raw=raw,
    )
    sig2 = bridge._signature(
        "test-secret",
        request_id="req-1",
        issued_at=1234567890,
        to="nocturney@gmail.com",
        raw=raw,
    )
    if sig1 != sig2 or len(sig1) != 64:
        fail("Apps Script HMAC signature is not deterministic SHA-256 hex")

    bridge_source = (
        ROOT / "packages" / "vfops" / "apps_script_gmail_bridge" / "Code.gs"
    ).read_text(encoding="utf-8")
    for needle in (
        "ALLOWED_RECIPIENT = 'nocturney@gmail.com'",
        "VF_GMAIL_BRIEF_SHARED_SECRET",
        "MAX_SKEW_SECONDS = 300",
        "LAST_SUCCESS_REQUEST_ID",
        "LAST_SUCCESS_MESSAGE_ID",
        "deduplicated: true",
        "Gmail.Users.Messages.send({raw: raw}, 'me')",
    ):
        if needle not in bridge_source:
            fail(f"Apps Script bridge missing {needle}")

    manifest = json.loads(
        (ROOT / "packages" / "vfops" / "apps_script_gmail_bridge" / "appsscript.json").read_text()
    )
    scopes = set(manifest.get("oauthScopes") or [])
    expected_scopes = {"https://www.googleapis.com/auth/gmail.send"}
    if scopes != expected_scopes:
        fail(f"Apps Script scopes changed: {sorted(scopes)}")
    services = (manifest.get("dependencies") or {}).get("enabledAdvancedServices") or []
    gmail_services = [
        item for item in services
        if item.get("serviceId") == "gmail"
        and item.get("userSymbol") == "Gmail"
        and item.get("version") == "v1"
    ]
    if len(gmail_services) != 1:
        fail("Apps Script advanced Gmail service is not pinned to Gmail v1")

    utf8_subject = "Velvet Factory — בריף הבוקר · בדיקה"
    encoded_subject = encode_subject(utf8_subject)
    try:
        encoded_subject.encode("ascii")
    except UnicodeEncodeError:
        fail("UTF-8 subject was not converted to ASCII-safe RFC 2047")
    if "=?utf-8?" not in encoded_subject.lower():
        fail("UTF-8 subject is missing RFC 2047 encoding")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        original = sender._download_one

        def fake_download(url: str, dest: Path, *, max_bytes: int) -> Path:
            if not url.startswith("https://"):
                fail("embed test received non-https URL")
            out = dest.with_suffix(".png")
            out.write_bytes(b"\x89PNG\r\n\x1a\nCIDTEST")
            return out

        sender._download_one = fake_download
        try:
            html = '<html dir="rtl"><body>בדיקת · CID — עברית<img src="https://example.com/a.png?x=1&amp;y=2" alt="A"></body></html>'
            rewritten, images = sender.embed_remote_images(html, tmp_path, limit=3, max_bytes=4096)
        finally:
            sender._download_one = original

        if len(images) != 1 or images[0].name != "remote-01.png":
            fail(f"unexpected embedded images: {[p.name for p in images]}")
        if 'src="cid:remote-01.png"' not in rewritten:
            fail("remote image was not rewritten to cid")

        mime = build_safe_mime(
            html=rewritten,
            images=images,
            to="nocturney@gmail.com",
            subject=utf8_subject,
        )
        try:
            blob_bytes = mime.as_bytes()
        except UnicodeEncodeError as exc:
            fail(f"UTF-8 MIME serialization failed: {exc}")

        parsed = message_from_bytes(blob_bytes)
        if parsed.get_content_type() != "multipart/related":
            fail("MIME is not multipart/related")
        parts = list(parsed.walk())
        html_parts = [p for p in parts if p.get_content_type() == "text/html"]
        if len(html_parts) != 1:
            fail("expected exactly one HTML MIME part")
        decoded_html = html_parts[0].get_payload(decode=True).decode("utf-8")
        if "בדיקת · CID — עברית" not in decoded_html:
            fail("UTF-8 HTML did not round-trip through MIME")
        if 'src="cid:remote-01.png"' not in decoded_html:
            fail("HTML CID reference missing after MIME decoding")
        if not any(p.get("Content-ID") == "<remote-01.png>" for p in parts):
            fail("downloaded image missing matching Content-ID")

    for rel in (
        "packages/vfops/out/gmail-send-request.json",
        ".github/workflows/gmail-brief-send.yml",
    ):
        text = (ROOT / rel).read_text(encoding="utf-8")
        if "refresh_token\": \"1//" in text or "client_secret\": \"GOCSPX" in text:
            fail(f"credential-looking material committed in {rel}")

    print("OK Gmail brief sender: Apps Script advanced Gmail + owner lock + UTF-8 MIME + remote-image CID rewrite")


if __name__ == "__main__":
    main()
