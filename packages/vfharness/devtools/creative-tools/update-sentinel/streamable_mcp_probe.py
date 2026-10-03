#!/usr/bin/env python3
import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request

def decode_body(body):
    text = body.decode("utf-8", "replace")
    stripped = text.strip()
    if stripped.startswith("{"):
        return json.loads(stripped)
    data = [line[5:].strip() for line in text.splitlines() if line.startswith("data:")]
    return json.loads("\n".join(data)) if data else {"raw": text[:2048]}

def post(url, payload, session=None):
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if session:
        headers["Mcp-Session-Id"] = session
    req = urllib.request.Request(url, data=json.dumps(payload, separators=(",", ":")).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = resp.read()
            return resp.status, dict(resp.headers.items()), decode_body(body) if body else None, body
    except urllib.error.HTTPError as exc:
        body = exc.read()
        return exc.code, dict(exc.headers.items()), decode_body(body) if body else None, body

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--tool", action="append", required=True)
    ap.add_argument("--client-name", default="velvetos-update-sentinel")
    args = ap.parse_args()
    summary = {"schema": "velvetos.update-sentinel.streamable-probe.v1", "url": args.url}
    init = {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":args.client_name,"version":"1.0"}}}
    status, headers, body, raw = post(args.url, init)
    summary["initialize_http"] = status
    if status >= 400 or not isinstance(body, dict) or "error" in body:
        summary["status"] = "FAIL"
        print(json.dumps(summary)); return 2
    session = headers.get("Mcp-Session-Id") or headers.get("mcp-session-id")
    post(args.url, {"jsonrpc":"2.0","method":"notifications/initialized","params":{}}, session)
    status, _, body, _ = post(args.url, {"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}, session)
    tools = []
    try:
        tools = [x["name"] for x in body["result"]["tools"]]
    except Exception:
        pass
    selected = next((name for name in args.tool if name in tools), None)
    summary.update({"tools_list_http":status,"tool_count":len(tools),"selected_tool":selected})
    if status >= 400 or not selected:
        summary["status"] = "FAIL"
        print(json.dumps(summary)); return 3
    status, _, body, raw = post(args.url, {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":selected,"arguments":{}}}, session)
    is_error = False
    if isinstance(body, dict):
        is_error = bool(body.get("error")) or bool((body.get("result") or {}).get("isError"))
    summary["tool_call_http"] = status
    summary["response_sha256"] = hashlib.sha256(raw).hexdigest()
    summary["status"] = "PASS" if status < 400 and not is_error else "FAIL"
    print(json.dumps(summary, separators=(",", ":")))
    return 0 if summary["status"] == "PASS" else 4

if __name__ == "__main__":
    sys.exit(main())
