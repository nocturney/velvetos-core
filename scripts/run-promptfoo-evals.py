#!/usr/bin/env python3
"""Run the pinned Promptfoo suite locally with no configured remote model/provider."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "packages" / "vfharness" / "evals"
CONFIG = EVALS / "promptfooconfig.json"
BIN = ROOT / "tools" / "promptfoo" / "node_modules" / ".bin" / (
    "promptfoo.cmd" if os.name == "nt" else "promptfoo"
)

HARDEN = {
    "CI": "true",
    "NO_ANALYTICS": "1",
    "PROMPTFOO_DISABLE_TELEMETRY": "1",
    "PROMPTFOO_DISABLE_REMOTE_GENERATION": "true",
    "PROMPTFOO_DISABLE_REDTEAM_REMOTE_GENERATION": "true",
    "PROMPTFOO_DISABLE_SHARING": "1",
    "PROMPTFOO_SELF_HOSTED": "1",
    "PROMPTFOO_DISABLE_UPDATE": "1",
}

def metrics(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    prompts = data["results"]["prompts"]
    if len(prompts) != 1:
        raise RuntimeError("expected exactly one local provider")
    return prompts[0]["metrics"]

def run(config: Path, output: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(HARDEN)
    return subprocess.run(
        [str(BIN), "eval", "-c", str(config), "-o", str(output), "--no-cache"],
        cwd=ROOT, env=env, text=True, capture_output=True, timeout=120,
    )

def main() -> int:
    if not BIN.is_file():
        print("FAIL Promptfoo local install missing; run npm ci --prefix tools/promptfoo --ignore-scripts --no-audit --no-fund", file=sys.stderr)
        return 2
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if config.get("providers") != ["exec: python policy_target.py"]:
        print("FAIL remote or untrusted provider configured", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "results.json"
        proc = run(CONFIG, out)
        if proc.returncode != 0 or not out.is_file():
            print(proc.stdout[-4000:], file=sys.stderr)
            print(proc.stderr[-4000:], file=sys.stderr)
            return 2
        good = metrics(out)
        if (good.get("testPassCount"), good.get("testFailCount"), good.get("testErrorCount")) != (17, 0, 0):
            print(f"FAIL unexpected Promptfoo metrics {good}", file=sys.stderr)
            return 2
        if good.get("cost") != 0 or (good.get("tokenUsage") or {}).get("total") != 0:
            print("FAIL local suite unexpectedly reported model cost/tokens", file=sys.stderr)
            return 2

        bad_config = json.loads(CONFIG.read_text(encoding="utf-8"))
        bad_config["tests"][0]["assert"][0]["value"] = "ALLOW|price_source_present"
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", dir=EVALS, encoding="utf-8", delete=False
        ) as fh:
            json.dump(bad_config, fh, ensure_ascii=False)
            bad_path = Path(fh.name)
        try:
            bad_out = Path(td) / "negative-results.json"
            bad_proc = run(bad_path, bad_out)
            if not bad_out.is_file():
                print("FAIL negative control produced no result", file=sys.stderr)
                return 2
            bad = metrics(bad_out)
            if bad.get("testFailCount", 0) < 1:
                print("FAIL Promptfoo negative control did not fail", file=sys.stderr)
                return 2
        finally:
            bad_path.unlink(missing_ok=True)

    print("OK promptfoo local=0.123.1 cases=17 pass=17 negative_control=PASS cost=0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
