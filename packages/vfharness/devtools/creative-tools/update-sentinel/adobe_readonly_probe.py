#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def get_token(args):
    if args.token_file:
        return Path(args.token_file).read_text(encoding="utf-8").strip()
    text = Path(args.config_js).read_text(encoding="utf-8")
    match = re.search(r'token\s*:\s*"([^"]+)"', text)
    if not match:
        raise RuntimeError("broker token binding not found in bridge config")
    return match.group(1)


def illustrator_bounded_snapshot():
    wrapper = Path(r"D:\Velvet\Runtime\CreativeCraft\Invoke-IllustratorReadonly.ps1")
    if not wrapper.is_file():
        raise RuntimeError("bounded Illustrator read-only wrapper missing")
    proc = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(wrapper),
            "-Operation",
            "snapshot",
        ],
        capture_output=True,
        text=True,
        timeout=110,
    )
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    if proc.returncode != 0:
        msg = stderr or stdout or f"bounded Illustrator read-only wrapper failed with exit {proc.returncode}"
        raise RuntimeError(msg[:500])
    payload = None
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
            break
        except Exception:
            continue
    if not isinstance(payload, dict) or payload.get("status") != "PASS":
        raise RuntimeError("bounded Illustrator read-only wrapper returned no PASS payload")
    if payload.get("operation") != "snapshot":
        raise RuntimeError("bounded Illustrator read-only wrapper operation mismatch")
    return payload


def aftereffects_bounded_snapshot():
    wrapper = Path(r"D:\Velvet\Runtime\CreativeCraft\Invoke-AfterEffectsReadonly.ps1")
    if not wrapper.is_file():
        raise RuntimeError("bounded After Effects read-only wrapper missing")
    proc = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(wrapper),
            "-Operation",
            "snapshot",
        ],
        capture_output=True,
        text=True,
        timeout=110,
    )
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    if proc.returncode != 0:
        msg = stderr or stdout or f"bounded After Effects read-only wrapper failed with exit {proc.returncode}"
        raise RuntimeError(msg[:500])
    payload = None
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
            break
        except Exception:
            continue
    if not isinstance(payload, dict) or payload.get("status") != "PASS":
        raise RuntimeError("bounded After Effects read-only wrapper returned no PASS payload")
    if payload.get("operation") != "snapshot":
        raise RuntimeError("bounded After Effects read-only wrapper operation mismatch")
    return payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", choices=["illustrator","aftereffects","photoshop","premiere"], required=True)
    ap.add_argument("--port", type=int, required=True)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--token-file")
    group.add_argument("--config-js")
    args = ap.parse_args()
    token = None
    out = {"schema":"velvetos.update-sentinel.adobe-probe.v1","host":args.host,"port":args.port}
    try:
        broker = "http://127.0.0.1:%d" % args.port
        if args.host == "illustrator":
            snap = illustrator_bounded_snapshot()
            out["version"] = str(snap.get("version") or "")
            out["document"] = snap.get("document")
            out["transport"] = str(snap.get("transport") or "resident-bounded-illustrator-com")
            out["operations"] = ["version", "active-document-read"]
            out["blocked"] = ["unbounded-authoring"]
        elif args.host == "aftereffects":
            snap = aftereffects_bounded_snapshot()
            out["version"] = str(snap.get("version") or "")
            out["project"] = snap.get("project")
            out["transport"] = "bounded-afterfx-com"
            out["operations"] = ["version", "active-project-read"]
            out["blocked"] = ["arbitrary-script-authoring"]
        else:
            token = get_token(args)
            from adobe.core import BrokerClient
            client = BrokerClient(broker_url=broker, token=token, target="default", timeout=12.0)
            _ = client.capabilities()
            if args.host == "photoshop":
                out["version"] = str(client.call("photoshop","app","getVersion"))
                _ = client.call("photoshop","document","getActive")
            else:
                out["version"] = str(client.call("premiere","app","getVersion"))
                _ = client.call("premiere","project","getActive")
        out["status"] = "PASS"
    except Exception as exc:
        msg = str(exc)
        if token:
            msg = msg.replace(token, "<redacted>")
        out["status"] = "FAIL"
        out["error"] = msg[:500]
    print(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    return 0 if out["status"] == "PASS" else 6


if __name__ == "__main__":
    sys.exit(main())
