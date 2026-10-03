#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

def send(proc, req, expect=True, timeout=25):
    proc.stdin.write(json.dumps(req, separators=(",", ":")) + "\n")
    proc.stdin.flush()
    if not expect:
        return None
    deadline = time.time() + timeout
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            break
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("id") == req.get("id"):
            return obj
    raise RuntimeError("no response for request id %s" % req.get("id"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", required=True)
    ap.add_argument("--server-arg", action="append", default=[])
    ap.add_argument("--env", action="append", default=[])
    ap.add_argument("--tool", required=True)
    ap.add_argument("--accept-result-error")
    ap.add_argument("--expected-server-name")
    args = ap.parse_args()
    env = os.environ.copy()
    for item in args.env:
        key, value = item.split("=", 1)
        env[key] = value
    proc = subprocess.Popen([args.server] + args.server_arg, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", env=env, bufsize=1)
    summary = {"schema":"velvetos.update-sentinel.stdio-probe.v1","tool":args.tool}
    try:
        init = send(proc, {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"velvetos-update-sentinel","version":"1.0"}}})
        send(proc, {"jsonrpc":"2.0","method":"notifications/initialized","params":{}}, expect=False)
        tools = send(proc, {"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}})
        names = [x["name"] for x in tools.get("result",{}).get("tools",[])]
        summary["server_name"] = init.get("result",{}).get("serverInfo",{}).get("name")
        summary["server_version"] = init.get("result",{}).get("serverInfo",{}).get("version")
        summary["tool_count"] = len(names)
        summary["tool_present"] = args.tool in names
        if args.expected_server_name and summary["server_name"] != args.expected_server_name:
            raise RuntimeError("unexpected MCP server identity")
        if args.tool not in names:
            raise RuntimeError("required read-only tool missing")
        call = send(proc, {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":args.tool,"arguments":{}}})
        if "error" in call:
            raise RuntimeError("MCP tools/call returned protocol error")
        raw = json.dumps(call, sort_keys=True, separators=(",", ":")).encode()
        summary["response_sha256"] = hashlib.sha256(raw).hexdigest()
        text_payload = ""
        try:
            text_payload = "\n".join(x.get("text","") for x in call.get("result",{}).get("content",[]) if x.get("type") == "text")
        except Exception:
            pass
        result_ok = True
        if text_payload.strip().startswith("{"):
            try:
                payload = json.loads(text_payload)
                if payload.get("ok") is False:
                    err = json.dumps(payload.get("error",""), ensure_ascii=False)
                    result_ok = bool(args.accept_result_error and args.accept_result_error.lower() in err.lower())
            except json.JSONDecodeError:
                pass
        summary["status"] = "PASS" if result_ok else "FAIL"
    except Exception as exc:
        summary["status"] = "FAIL"
        summary["error"] = str(exc)[:500]
    finally:
        try: proc.stdin.close()
        except Exception: pass
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
        stderr = proc.stderr.read() if proc.stderr else ""
        summary["stderr_sha256"] = hashlib.sha256(stderr.encode("utf-8","replace")).hexdigest()
    print(json.dumps(summary, separators=(",", ":")))
    return 0 if summary["status"] == "PASS" else 5

if __name__ == "__main__":
    sys.exit(main())
