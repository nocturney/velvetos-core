import argparse
import http.client
import json
import sys


def post(conn, path, payload, headers):
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    merged = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    merged.update(headers)
    conn.request("POST", path, body=body, headers=merged)
    response = conn.getresponse()
    raw = response.read()
    text = raw.decode("utf-8", errors="replace")
    return response.status, dict(response.getheaders()), text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=27182)
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--expected-server-name", default="MCP Server Adapter")
    args = parser.parse_args()

    conn = http.client.HTTPConnection(args.host, args.port, timeout=args.timeout)
    session_id = None
    protocol = "2025-11-25"
    try:
        init = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": protocol,
                "capabilities": {},
                "clientInfo": {"name": "VelvetOS Update Sentinel", "version": "0.1.0"},
            },
        }
        status, headers, text = post(conn, "/mcp", init, {})
        if status != 200:
            raise RuntimeError(f"initialize HTTP {status}: {text[:300]}")
        init_result = json.loads(text)
        session_id = headers.get("MCP-Session-Id") or headers.get("Mcp-Session-Id")
        if not session_id:
            raise RuntimeError("initialize returned no MCP-Session-Id")
        server = init_result.get("result", {}).get("serverInfo", {})
        if server.get("name") != args.expected_server_name:
            raise RuntimeError(f"unexpected server name: {server.get('name')!r}")

        common = {"MCP-Session-Id": session_id, "MCP-Protocol-Version": protocol}
        status, _, _ = post(conn, "/mcp", {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, common)
        if status not in (200, 202):
            raise RuntimeError(f"initialized notification HTTP {status}")

        status, _, text = post(conn, "/mcp", {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, common)
        if status != 200:
            raise RuntimeError(f"tools/list HTTP {status}: {text[:300]}")
        tools_result = json.loads(text)
        tool_names = [item.get("name") for item in tools_result.get("result", {}).get("tools", [])]
        if "fusion_mcp_read" not in tool_names:
            raise RuntimeError("fusion_mcp_read missing from tools/list")

        call = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "fusion_mcp_read", "arguments": {"queryType": "activeCommand"}},
        }
        status, _, text = post(conn, "/mcp", call, common)
        if status != 200:
            raise RuntimeError(f"tools/call HTTP {status}: {text[:300]}")
        call_result = json.loads(text)
        if "error" in call_result:
            raise RuntimeError(f"tools/call error: {call_result['error']}")
        content = call_result.get("result", {}).get("content", [])
        read_payload = None
        if content and isinstance(content[0], dict):
            raw_text = content[0].get("text")
            if raw_text:
                try:
                    read_payload = json.loads(raw_text)
                except json.JSONDecodeError:
                    read_payload = raw_text

        print(json.dumps({
            "status": "PASS",
            "protocol": protocol,
            "server": server,
            "tool_names": tool_names,
            "read_probe": read_payload,
            "session_created": True,
        }, separators=(",", ":")))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}, separators=(",", ":")))
        return 2
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
