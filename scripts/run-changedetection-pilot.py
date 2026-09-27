#!/usr/bin/env python3
"""Run a localhost-only changedetection.io two-snapshot change pilot."""
from __future__ import annotations

import functools
import http.server
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "tools" / "changedetection" / "python"
DATA = ROOT / "tools" / "changedetection" / "data"
CLI = VENDOR / "bin" / ("changedetection.io.exe" if os.name == "nt" else "changedetection.io")
RECEIPT = ROOT / "packages" / "vfharness" / "state" / "changedetection-pilot-2026-09-27.json"

def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])

def run_cd(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(CLI), *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=90,
    )

def main() -> int:
    if not CLI.is_file():
        print("FAIL changedetection.io local install missing", file=sys.stderr)
        return 2

    DATA.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=DATA) as td:
        work = Path(td)
        target = work / "target"
        store = work / "store"
        target.mkdir()
        (target / "index.txt").write_text("version-one\n", encoding="utf-8")

        handler = functools.partial(
            http.server.SimpleHTTPRequestHandler,
            directory=str(target),
        )
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        env = os.environ.copy()
        env["PYTHONPATH"] = str(VENDOR)
        env["ALLOW_IANA_RESTRICTED_ADDRESSES"] = "true"
        for key in (
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY", "PLAYWRIGHT_DRIVER_URL", "WEBDRIVER_URL",
        ):
            env.pop(key, None)

        app_port = free_port()
        url = f"http://127.0.0.1:{server.server_port}/index.txt"
        first = run_cd([
            "-h", "127.0.0.1", "-p", str(app_port), "-C", "-d", str(store),
            "-u", url, "-u0", '{"fetch_backend":"html_requests"}', "-b",
        ], env)

        watch_files = list(store.glob("*/watch.json"))
        first_batch_ok = (
            first.returncode in (0, 15)
            and "All 1 iterations completed" in first.stdout
        )
        if not first_batch_ok or len(watch_files) != 1:
            server.shutdown()
            print(
                "FAIL changedetection first snapshot "
                f"rc={first.returncode} watches={len(watch_files)} "
                f"stdout_tail={first.stdout[-1200:]!r} stderr_tail={first.stderr[-1200:]!r}",
                file=sys.stderr,
            )
            return 2
        watch_path = watch_files[0]
        baseline = json.loads(watch_path.read_text(encoding="utf-8"))
        baseline_md5 = baseline.get("previous_md5")
        baseline_ok = (
            baseline.get("check_count") == 1
            and baseline.get("fetch_backend") == "html_requests"
            and baseline.get("last_error") is False
            and bool(baseline_md5)
        )

        (target / "index.txt").write_text("version-two\n", encoding="utf-8")
        second = run_cd([
            "-h", "127.0.0.1", "-p", str(app_port), "-d", str(store),
            "-r", "all", "-b",
        ], env)
        final = json.loads(watch_path.read_text(encoding="utf-8"))
        history = list(watch_path.parent.glob("*.html.br"))
        second_batch_ok = (
            second.returncode in (0, 15)
            and "All 1 iterations completed" in second.stdout
        )
        changed = (
            second_batch_ok
            and final.get("check_count", 0) >= 2
            and final.get("last_error") is False
            and final.get("previous_md5") != baseline_md5
            and len(history) >= 2
            and "Change detected in UUID" in second.stdout
        )
        server.shutdown()
        thread.join(timeout=5)

        receipt = {
            "schema": 1,
            "component": "changedetection.io",
            "version": "0.60.7",
            "state": "PILOT",
            "deployment": "LOCAL_WINDOWS_BATCH_HTML_REQUESTS",
            "authority_role": "EXTERNAL_DEPENDENCY_CHANGE_SENSOR_ONLY",
            "localhost_override_scope": "ACCEPTANCE_FIXTURE_ONLY",
            "fetch_backend": "html_requests",
            "browser_fetcher_used": False,
            "llm_or_ai_feature_used": False,
            "paid_api_credentials_supplied": False,
            "hosted_service_used": False,
            "baseline_snapshot": "PASS" if baseline_ok else "FAIL",
            "change_detection": "PASS" if changed else "FAIL",
            "snapshots_observed": len(history),
            "dependency_footprint": "HEAVY_OPTIONAL_CLIENTS_INSTALLED_BY_UPSTREAM_DISTRIBUTION",
            "promotion_decision": "PILOT_ONLY_PENDING_COMPLEXITY_REVIEW",
            "incremental_recurring_cost_ils": 0,
        }
        RECEIPT.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        if not baseline_ok or not changed:
            print("FAIL changedetection pilot", file=sys.stderr)
            return 2

    print("OK changedetection 0.60.7 baseline=PASS change=PASS cost=0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
