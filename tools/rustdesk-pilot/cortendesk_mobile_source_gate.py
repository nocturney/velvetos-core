"""Read-only, exact-upstream-source gate for CortenDesk mobile browser research.

This checks the *source tree* of v1.14.0, not any running server or Safari.
It cannot start containers, install agents, create users, connect to a desktop,
or authorize the previously denied remote container launch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Mapping

SCHEMA = "velvetos.cortendesk.mobile_source_gate.v1"
UPSTREAM_TAG = "v1.14.0"
UPSTREAM_COMMIT = "2070d598d30cbaec207060a0fbef539ccf5d5d52"
MAX_SOURCE_BYTES = 256_000

# Git blob IDs obtained from the immutable v1.14.0 source tree. These are
# source-code hashes, NOT the independently pinned OCI image SHA-256 digest.
PINNED_BLOBS = {
    "routes/web.php": "a4eb478d1ccf55133ec605cff42a7187e7244141",
    "routes/api.php": "c3ff2a628b1f5a141596c6b29c59613b633d1407",
    "app/Http/Controllers/WebClientPageController.php": "f215578b7ac387b029e2a8f6476bb0dc7d3378fa",
    "docker/nginx.conf.template": "fb4e8a34fb0d13faf9b8e1b15b5e28d5624e4f66",
    "webclient/src/input/mouse-keyboard.ts": "8f6f0798045a3d4b39b3105ffea2868e859f8e15",
    "webclient/src/ui/app.ts": "3662215d65c9b2063a9ac3d98c9baa6ab715ba04",
    "webclient/src/media/video.ts": "a85fed2edc902ce94dd091c04592efac9bdcbece",
    "webclient/src/media/mse-video.ts": "0ca44c3171fc4e685c7575906950e0f5b450af5f",
    "webclient/src/ui/file-panel.ts": "c6a71f27b05b94564d85d9f62746eb1e8246947c",
    "resources/views/webclient.blade.php": "0a1ec8c0f3b6b7b4b2c130e593306674357b35f1",
}

# A static source signal is not evidence of actual browser compatibility.
FEATURE_RULES = {
    "authenticated_webclient_route": (
        "routes/web.php",
        ("Route::middleware('auth')->group(function () {",
         "Route::get('/webclient', [WebClientPageController::class, 'show'])"),
    ),
    "scoped_read_only_inventory_route": (
        "routes/api.php",
        ("auth:api-token", "Route::get('/devices'",
         "api-token-can:device,r"),
    ),
    "webclient_ticket_and_websocket_origins": (
        "app/Http/Controllers/WebClientPageController.php",
        ("ServerLink::webTicket($user)", "/ws/id", "/ws/relay",
         "'wss'", "'ws'"),
    ),
    "bundled_rendezvous_relay_websocket_bridge": (
        "docker/nginx.conf.template",
        ("location = /ws/id", "location = /ws/relay",
         "proxy_set_header Upgrade", ":21118/", ":21119/"),
    ),
    "touch_pointer_drag_and_long_press": (
        "webclient/src/input/mouse-keyboard.ts",
        ("onPointerDown", "onPointerMove", "onPointerUp",
         "e.pointerType === 'touch'", "TOUCH_LONGPRESS_MS"),
    ),
    "visible_touch_mode_and_safari_fullscreen_awareness": (
        "webclient/src/ui/app.ts",
        ("setInputMode('touch')", "rd-mode-touch",
         "iPhone Safari has no element fullscreen", "MseVideoPlayer"),
    ),
    "webcodecs_and_h264_fallback_detection": (
        "webclient/src/media/video.ts",
        ("VideoDecoder", "mseH264Available", "h264s"),
    ),
    "h264_mse_fallback_player": (
        "webclient/src/media/mse-video.ts",
        ("MseVideoPlayer", "MediaSource", "H.264"),
    ),
    "file_picker_without_file_system_access_api": (
        "webclient/src/ui/file-panel.ts",
        ("input.type = 'file'", "showDirectoryPicker", "Downloads folder"),
    ),
    "iphone_viewport_layout": (
        "resources/views/webclient.blade.php",
        ("name=\"viewport\"", "viewport-fit=cover"),
    ),
}


class SourceGateError(ValueError):
    """Opaque, sanitized reason safe for a public research report."""


def git_blob_id(source: bytes) -> str:
    """Git's blob SHA-1 over the exact byte length and contents."""
    return hashlib.sha1(
        b"blob " + str(len(source)).encode("ascii") + b"\0" + source,
        usedforsecurity=False,
    ).hexdigest()


def inspect_contents(files: Mapping[str, bytes], commit: str) -> dict:
    """Pure check; live execution state is always explicitly unverified."""
    result = {
        "schema": SCHEMA,
        "release": UPSTREAM_TAG,
        "upstream_commit": UPSTREAM_COMMIT,
        "state": "SOURCE_CONTRACT_REJECTED",
        "source_blob_count": len(PINNED_BLOBS),
        "source_exactly_pinned": False,
        "features": {name: "not_verified" for name in FEATURE_RULES},
        "mobile_safari_verified": False,
        "websocket_session_verified": False,
        "remote_input_verified": False,
        "file_transfer_verified": False,
        "container_started": False,
        "may_launch_container": False,
        "performed_mutation": False,
    }
    if commit != UPSTREAM_COMMIT:
        result["reason"] = "source_commit_mismatch"
        return result
    if set(files) != set(PINNED_BLOBS):
        result["reason"] = "source_file_set_invalid"
        return result
    if any(
        not isinstance(files[path], bytes)
        or len(files[path]) > MAX_SOURCE_BYTES
        or git_blob_id(files[path]) != expected
        for path, expected in PINNED_BLOBS.items()
    ):
        result["reason"] = "source_blob_mismatch"
        return result
    result["source_exactly_pinned"] = True
    all_signals = True
    for name, (path, needles) in FEATURE_RULES.items():
        source = files[path].decode("utf-8", errors="replace")
        found = all(needle in source for needle in needles)
        result["features"][name] = (
            "present_in_pinned_source" if found else "source_signal_missing"
        )
        all_signals = all_signals and found
    result["state"] = (
        "PINNED_SOURCE_SIGNALS_PRESENT_NOT_RUNTIME"
        if all_signals else "SOURCE_CONTRACT_REJECTED"
    )
    if not all_signals:
        result["reason"] = "expected_source_signal_missing"
    return result


def inspect_checkout(root: Path) -> dict:
    if not root.is_dir() or root.is_symlink():
        raise SourceGateError("source_checkout_unavailable")
    try:
        head = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
            capture_output=True, text=True, check=False, timeout=8,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SourceGateError("git_source_query_unavailable") from exc
    if head.returncode != 0:
        raise SourceGateError("git_source_query_unavailable")
    commit = head.stdout.strip()
    if commit != UPSTREAM_COMMIT:
        return inspect_contents({}, commit)
    files = {}
    for rel in PINNED_BLOBS:
        file = root / rel
        # Research tool must never traverse source symlinks.
        if not file.is_file() or file.is_symlink():
            raise SourceGateError("source_file_missing_or_symlinked")
        try:
            if file.stat().st_size > MAX_SOURCE_BYTES:
                raise SourceGateError("source_file_too_large")
            files[rel] = file.read_bytes()
        except OSError as exc:
            raise SourceGateError("source_file_unavailable") from exc
    return inspect_contents(files, commit)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline pinned-source mobile capability audit")
    parser.add_argument("--source-root", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        report = inspect_checkout(args.source_root)
    except SourceGateError as exc:
        report = {
            "schema": SCHEMA,
            "state": "SOURCE_UNAVAILABLE",
            "reason": str(exc),
            "mobile_safari_verified": False,
            "may_launch_container": False,
            "performed_mutation": False,
        }
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if report["state"] == "PINNED_SOURCE_SIGNALS_PRESENT_NOT_RUNTIME" else 2


if __name__ == "__main__":
    raise SystemExit(main())
