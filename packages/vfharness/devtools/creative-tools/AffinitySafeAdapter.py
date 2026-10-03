import argparse
import base64
import http.client
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

HOST = "127.0.0.1"
PORT = 6767
PROTOCOL = "2025-11-25"
VELVET_ROOT = Path(r"D:\Velvet").resolve()
PREFS = Path(r"C:\Users\Chris\AppData\Roaming\Affinity\Affinity\3.0\Settings\MCPPreferences.xml")
ACCEPTANCE_GATE = Path(r"D:\Velvet\State\CreativeTools\Affinity\acceptance.enabled")
ACCEPTANCE_RENDER = Path(r"D:\Velvet\Tmp\creative-tools\affinity\acceptance-render.jpg")
REQUIRED_TOOLS = {
    "add_sdk_hint",
    "execute_script",
    "list_library_scripts",
    "list_sdk_documentation",
    "read_library_script",
    "read_sdk_documentation_topic",
    "render_selection",
    "render_spread",
    "report_sdk_issue",
    "save_script_to_library",
    "search_sdk_hints",
}
EXPECTED_PREFS = {
    "EnableMCPServer": "True",
    "EnableLocalMemory": "False",
    "EnableReadScripts": "True",
    "EnableWriteScripts": "False",
    "EnableCanvaAI": "False",
    "EnableFileSystem": "False",
    "EnableNetwork": "False",
    "EnableReporting": "False",
}
UUID_RE = re.compile(r"^[0-9A-Fa-f-]{16,64}$")

STATUS_SCRIPT = r"""
const { Application } = require('/application.js');
const { Document } = require('/document.js');
const current = Document.current;
console.log(JSON.stringify({
  marker: "VELVET_AFFINITY_STATUS_V1",
  version: Application.version,
  shortVersion: Application.shortVersion,
  buildVersion: Application.buildVersion,
  documentCount: Document.all.length,
  current: current ? {
    sessionUuid: current.sessionUuid,
    persistentUuid: current.persistentUuid,
    sizePixels: current.sizePixels,
    isDirty: current.isDirty,
    needsSaving: current.needsSaving
  } : null
}));
"""

ACCEPTANCE_CREATE_SCRIPT = r"""
const { Document, NewDocumentOptions } = require('/document.js');
const { UnitType } = require('/units.js');
const { AddChildNodesCommandBuilder } = require('/commands.js');
const { Rectangle } = require('/geometry.js');
const { ShapeNodeDefinition } = require('/nodes.js');
const { ShapeRectangle } = require('/shapes.js');
const { RGB8 } = require('/colours.js');

if (Document.all.length !== 0)
  throw new Error('Acceptance requires zero open documents');

const opts = NewDocumentOptions.createDefault();
opts.units = UnitType.Pixel;
opts.width = 256;
opts.height = 256;
opts.dpi = 72;
opts.isTransparentBackground = false;
opts.pageCount = 1;
const doc = Document.create(opts);

const def = ShapeNodeDefinition.create(
  ShapeRectangle.create(),
  new Rectangle(32, 32, 192, 192),
  RGB8(32, 96, 224)
);
const builder = AddChildNodesCommandBuilder.create();
builder.addShapeNode(def);
doc.executeCommand(builder.createCommand(false));

console.log(JSON.stringify({
  marker: "VELVET_AFFINITY_ACCEPTANCE_V1",
  sessionUuid: doc.sessionUuid,
  sizePixels: doc.sizePixels,
  spreadCount: [...doc.spreads].length,
  isDirty: doc.isDirty,
  documentCount: Document.all.length,
  currentSessionUuid: Document.current ? Document.current.sessionUuid : null
}));
"""

ACCEPTANCE_CLEANUP_SCRIPT = r"""
const { Document } = require('/document.js');
if (Document.all.length !== 1)
  throw new Error('Refusing acceptance cleanup: expected exactly one document');
const doc = Document.current;
if (!doc)
  throw new Error('Refusing acceptance cleanup: no current document');
const size = doc.sizePixels;
if (!size || size.width !== 256 || size.height !== 256)
  throw new Error('Refusing acceptance cleanup: unexpected document size');
const closed = doc.sessionUuid;
doc.close();
console.log(JSON.stringify({
  marker: "VELVET_AFFINITY_CLEANUP_V1",
  closed: closed,
  remaining: Document.all.length,
  current: Document.current ? Document.current.sessionUuid : null
}));
"""

def emit(obj, code=0):
    print(json.dumps(obj, ensure_ascii=True))
    raise SystemExit(code)

def fail(message, code="ADAPTER_ERROR", exit_code=2, **extra):
    out = {"ok": False, "error": {"code": code, "message": message}}
    out.update(extra)
    emit(out, exit_code)

def safe_output(raw):
    try:
        p = Path(raw).expanduser().resolve()
    except Exception:
        fail("output path could not be resolved", "INVALID_PATH")
    if p != VELVET_ROOT and VELVET_ROOT not in p.parents:
        fail("output path must be under D:\\Velvet", "PATH_OUTSIDE_VELVET")
    if p.suffix.lower() not in {".jpg", ".jpeg"}:
        fail("render output must be .jpg or .jpeg", "INVALID_OUTPUT_FORMAT")
    if p.exists():
        fail("output already exists; overwrite is not allowed", "OUTPUT_EXISTS")
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def read_preferences():
    if not PREFS.is_file():
        fail("Affinity MCP preferences file is missing", "PREFERENCES_MISSING")
    try:
        root = ET.parse(PREFS).getroot()
    except Exception as exc:
        fail(f"Affinity MCP preferences could not be parsed: {exc}", "PREFERENCES_INVALID")
    found = {child.tag: (child.text or "").strip() for child in root}
    drift = {k: {"expected": v, "observed": found.get(k)} for k, v in EXPECTED_PREFS.items() if found.get(k) != v}
    if drift:
        fail("Affinity MCP permissions differ from the accepted fail-closed profile", "PERMISSION_DRIFT", drift=drift)
    return found

class AffinityMCP:
    def __init__(self, client_name="VelvetOS-Affinity-SafeAdapter"):
        self.conn = http.client.HTTPConnection(HOST, PORT, timeout=30)
        try:
            self.conn.request("GET", "/sse", headers={"Accept": "text/event-stream"})
            self.resp = self.conn.getresponse()
        except Exception as exc:
            fail(f"Affinity MCP is unreachable on {HOST}:{PORT}: {exc}", "MCP_UNREACHABLE")
        if self.resp.status != 200:
            fail(f"Affinity MCP SSE returned HTTP {self.resp.status}", "MCP_BAD_STATUS")
        self.endpoint = self._read_endpoint()
        self.next_id = 0
        self.init_result = self.request("initialize", {
            "protocolVersion": PROTOCOL,
            "capabilities": {},
            "clientInfo": {"name": client_name, "version": "0.1.0"},
        })
        if self.init_result.get("protocolVersion") != PROTOCOL:
            fail("Affinity MCP protocol drift detected", "PROTOCOL_DRIFT", observed=self.init_result.get("protocolVersion"))
        self.post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        self.preamble_read = False

    def _read_endpoint(self):
        event = None
        deadline = time.time() + 8
        while time.time() < deadline:
            line = self.resp.readline()
            if not line:
                break
            text = line.decode("utf-8", "replace").rstrip("\r\n")
            if text.startswith("event:"):
                event = text.split(":", 1)[1].strip()
            elif text.startswith("data:") and event == "endpoint":
                endpoint = text.split(":", 1)[1].strip()
                if not endpoint.startswith("/message?session_id="):
                    fail("Unexpected Affinity MCP session endpoint", "ENDPOINT_DRIFT")
                return endpoint
        fail("Affinity MCP did not publish a session endpoint", "MCP_NO_ENDPOINT")

    def post(self, obj):
        c = http.client.HTTPConnection(HOST, PORT, timeout=5)
        body = json.dumps(obj).encode("utf-8")
        c.request("POST", self.endpoint, body=body, headers={"Content-Type": "application/json"})
        r = c.getresponse()
        data = r.read()
        status = r.status
        c.close()
        if status not in (200, 202):
            fail(f"Affinity MCP POST failed with HTTP {status}", "MCP_POST_FAILED")

    def request(self, method, params):
        self.next_id += 1
        request_id = self.next_id
        self.post({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        deadline = time.time() + 30
        while time.time() < deadline:
            line = self.resp.readline()
            if not line:
                break
            text = line.decode("utf-8", "replace").rstrip("\r\n")
            if not text.startswith("data:"):
                continue
            try:
                obj = json.loads(text.split(":", 1)[1].lstrip())
            except Exception:
                continue
            if obj.get("id") != request_id:
                continue
            if "error" in obj:
                fail("Affinity MCP returned a JSON-RPC error", "MCP_RPC_ERROR", rpc_error=obj["error"])
            return obj.get("result") or {}
        fail(f"Timed out waiting for Affinity MCP response to {method}", "MCP_TIMEOUT")

    def tool(self, name, arguments=None):
        return self.request("tools/call", {"name": name, "arguments": arguments or {}})

    def tools(self):
        return (self.request("tools/list", {}) or {}).get("tools") or []

    def ensure_preamble(self):
        if self.preamble_read:
            return
        result = self.tool("read_sdk_documentation_topic", {"filename": "preamble"})
        if result.get("isError"):
            fail("Affinity required preamble could not be read", "PREAMBLE_FAILED")
        self.preamble_read = True

    def execute_fixed(self, script):
        self.ensure_preamble()
        result = self.tool("execute_script", {"script": script})
        if result.get("isError"):
            fail("Affinity fixed script failed", "SCRIPT_FAILED", detail=text_content(result)[-2000:])
        return result

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass

def text_content(result):
    return "\n".join(
        item.get("text", "")
        for item in result.get("content") or []
        if item.get("type") == "text"
    )

def marker_from(result, marker):
    for line in text_content(result).splitlines():
        if marker in line:
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if obj.get("marker") == marker:
                return obj
    fail(f"Expected Affinity script marker {marker} was not returned", "MARKER_MISSING")

def image_bytes(result):
    if result.get("isError"):
        fail("Affinity render tool returned an error", "RENDER_FAILED", detail=text_content(result)[-1200:])
    for item in result.get("content") or []:
        if item.get("type") == "image" and item.get("mimeType") == "image/jpeg":
            try:
                raw = base64.b64decode(item.get("data") or "", validate=False)
            except Exception:
                fail("Affinity render image was not valid base64", "RENDER_INVALID")
            if len(raw) < 256 or not raw.startswith(b"\xff\xd8"):
                fail("Affinity render image was not a valid JPEG", "RENDER_INVALID")
            return raw
    fail("Affinity render tool did not return JPEG image content", "RENDER_MISSING")

def status_with(mcp):
    result = mcp.execute_fixed(STATUS_SCRIPT)
    return marker_from(result, "VELVET_AFFINITY_STATUS_V1")

def op_probe():
    prefs = read_preferences()
    mcp = AffinityMCP()
    try:
        tools = mcp.tools()
        names = {t.get("name") for t in tools}
        missing = sorted(REQUIRED_TOOLS - names)
        if missing:
            fail("Required Affinity MCP tools are missing", "TOOLS_DRIFT", missing=missing)
        server = mcp.init_result.get("serverInfo") or {}
        if server.get("name") != "Affinity":
            fail("Unexpected MCP server identity", "SERVER_IDENTITY_DRIFT", observed=server)
        emit({
            "ok": True,
            "status": "PASS",
            "transport": "sse",
            "host": HOST,
            "port": PORT,
            "protocol": PROTOCOL,
            "serverInfo": server,
            "tool_count": len(tools),
            "permissions": prefs,
            "production_surface": ["probe", "status", "render-current"],
            "raw_execute_script_exposed": False,
            "acceptance_gate_required": True,
        })
    finally:
        mcp.close()

def op_status():
    read_preferences()
    mcp = AffinityMCP()
    try:
        status = status_with(mcp)
        emit({"ok": True, "status": status})
    finally:
        mcp.close()

def op_render_current(output):
    read_preferences()
    dst = safe_output(output)
    mcp = AffinityMCP()
    try:
        status = status_with(mcp)
        current = status.get("current")
        if not current:
            fail("No current Affinity document to render", "NO_CURRENT_DOCUMENT")
        uuid = current.get("sessionUuid")
        if not UUID_RE.fullmatch(uuid or ""):
            fail("Current Affinity document returned an invalid session UUID", "INVALID_SESSION_UUID")
        result = mcp.tool("render_spread", {"document_session_uuid": uuid, "spread_index": 0})
        raw = image_bytes(result)
        dst.write_bytes(raw)
        emit({"ok": True, "operation": "render-current", "output": str(dst), "bytes": len(raw), "document": current})
    finally:
        mcp.close()

def op_acceptance():
    read_preferences()
    if not ACCEPTANCE_GATE.is_file():
        fail("Acceptance gate is not enabled", "ACCEPTANCE_GATE_REQUIRED")
    if ACCEPTANCE_RENDER.exists():
        ACCEPTANCE_RENDER.unlink()
    mcp = AffinityMCP(client_name="VelvetOS-Affinity-Acceptance")
    created = None
    cleaned = False
    try:
        before = status_with(mcp)
        if before.get("documentCount") != 0 or before.get("current") is not None:
            fail("Acceptance requires zero open Affinity documents", "ACCEPTANCE_PRECONDITION")

        created_result = mcp.execute_fixed(ACCEPTANCE_CREATE_SCRIPT)
        created = marker_from(created_result, "VELVET_AFFINITY_ACCEPTANCE_V1")
        uuid = created.get("sessionUuid")
        if not UUID_RE.fullmatch(uuid or ""):
            fail("Acceptance document returned an invalid UUID", "INVALID_SESSION_UUID")
        if created.get("documentCount") != 1 or created.get("currentSessionUuid") != uuid:
            fail("Acceptance document readback did not match expected state", "ACCEPTANCE_READBACK_FAILED")

        render_result = mcp.tool("render_spread", {"document_session_uuid": uuid, "spread_index": 0})
        raw = image_bytes(render_result)
        ACCEPTANCE_RENDER.parent.mkdir(parents=True, exist_ok=True)
        ACCEPTANCE_RENDER.write_bytes(raw)

        cleanup_result = mcp.execute_fixed(ACCEPTANCE_CLEANUP_SCRIPT)
        cleanup = marker_from(cleanup_result, "VELVET_AFFINITY_CLEANUP_V1")
        cleaned = cleanup.get("remaining") == 0 and cleanup.get("current") is None
        if not cleaned:
            fail("Acceptance cleanup readback failed", "ACCEPTANCE_CLEANUP_FAILED")

        after = status_with(mcp)
        if after.get("documentCount") != 0 or after.get("current") is not None:
            fail("Affinity still has open documents after acceptance cleanup", "ACCEPTANCE_POSTCONDITION")

        emit({
            "ok": True,
            "status": "PASS",
            "created": created,
            "render": {
                "path": str(ACCEPTANCE_RENDER),
                "bytes": len(raw),
            },
            "cleanup": cleanup,
            "post": after,
        })
    finally:
        mcp.close()

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="operation", required=True)
    sub.add_parser("probe")
    sub.add_parser("status")
    rr = sub.add_parser("render-current")
    rr.add_argument("--output", required=True)
    sub.add_parser("acceptance")
    args = parser.parse_args()
    if args.operation == "probe":
        op_probe()
    elif args.operation == "status":
        op_status()
    elif args.operation == "render-current":
        op_render_current(args.output)
    elif args.operation == "acceptance":
        op_acceptance()

if __name__ == "__main__":
    main()
