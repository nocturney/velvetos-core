import argparse
import ctypes
import hashlib
import json
import os
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pythoncom
import win32com.client

ROOT = Path(r"D:\Velvet").resolve()
STATE = ROOT / "State" / "Corel"
TOKEN_FILE = STATE / "corel-adapter-token.txt"
GATE_FILE = STATE / "acceptance-gate.json"
CRAFT_OUTPUT = ROOT / "Output" / "CreativeCraft" / "Corel"
MAX_CRAFT_OBJECTS = 200
APPS = {
    "coreldraw": {
        "progid": "CorelDRAW.Application.27",
        "expected_name": "CorelDRAW",
        "expected_version": "Version 27.2.0.135",
        "port": 6771,
    },
    "corel-designer": {
        "progid": "CorelDESIGNER.Application.27",
        "expected_name": "Corel DESIGNER",
        "expected_version": "Version 27.2.0.135",
        "port": 6772,
    },
}
COLOR = (32, 95, 224)


def session_id():
    sid = ctypes.c_uint()
    ok = ctypes.windll.kernel32.ProcessIdToSessionId(os.getpid(), ctypes.byref(sid))
    if not ok:
        raise ctypes.WinError()
    return int(sid.value)


def load_token():
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    if len(token) < 32:
        raise RuntimeError("Corel adapter token missing or too short")
    return token


def read_gate(app_id):
    if not GATE_FILE.is_file():
        return False
    try:
        gate = json.loads(GATE_FILE.read_text(encoding="utf-8-sig"))
    except Exception:
        return False
    return (
        gate.get("enabled") is True
        and gate.get("purpose") == "acceptance"
        and app_id in gate.get("apps", [])
    )


def pdf_info(path):
    p = Path(path)
    deadline = time.monotonic() + 10.0
    last = None
    stable = 0
    while time.monotonic() < deadline:
        stat = p.stat()
        marker = (stat.st_size, stat.st_mtime_ns)
        if stat.st_size > 0 and marker == last:
            stable += 1
            if stable >= 4:
                break
        else:
            stable = 0
            last = marker
        time.sleep(0.25)
    if stable < 4:
        raise RuntimeError("exported PDF did not become stable before verification")
    data = p.read_bytes()
    stat_after = p.stat()
    if (stat_after.st_size, stat_after.st_mtime_ns) != last:
        raise RuntimeError("exported PDF changed during verification")
    if len(data) < 8 or not data.startswith(b"%PDF-"):
        raise RuntimeError("exported artifact is not a valid PDF")
    media = re.search(rb"/MediaBox\s*\[\s*[-0-9.]+\s+[-0-9.]+\s+([-0-9.]+)\s+([-0-9.]+)\s*\]", data)
    return {
        "bytes": len(data),
        "page_width_points": float(media.group(1)) if media else None,
        "page_height_points": float(media.group(2)) if media else None,
        "sha256": hashlib.sha256(data).hexdigest().upper(),
    }


def stable_file_info(path, expected_prefix=None):
    p = Path(path)
    deadline = time.monotonic() + 10.0
    last = None
    stable = 0
    while time.monotonic() < deadline:
        stat = p.stat()
        marker = (stat.st_size, stat.st_mtime_ns)
        if stat.st_size > 0 and marker == last:
            stable += 1
            if stable >= 4:
                break
        else:
            stable = 0
            last = marker
        time.sleep(0.25)
    if stable < 4:
        raise RuntimeError("exported artifact did not become stable")
    data = p.read_bytes()
    if expected_prefix and not data.startswith(expected_prefix):
        raise RuntimeError("exported artifact has unexpected format")
    return {
        "path": str(p),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest().upper(),
    }


def safe_slug(value):
    value = str(value or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value):
        raise RuntimeError("job_id must match [A-Za-z0-9_-]{1,64}")
    return value


def finite_number(value, name, minimum=-100000.0, maximum=100000.0):
    try:
        value = float(value)
    except Exception as exc:
        raise RuntimeError(f"{name} must be numeric") from exc
    if not (minimum <= value <= maximum):
        raise RuntimeError(f"{name} is outside the allowed range")
    return value


def rgb(value, name="color"):
    if not isinstance(value, list) or len(value) != 3:
        raise RuntimeError(f"{name} must be [r,g,b]")
    out = []
    for channel in value:
        if isinstance(channel, bool) or not isinstance(channel, int) or not 0 <= channel <= 255:
            raise RuntimeError(f"{name} channels must be integers 0..255")
        out.append(channel)
    return out


def safe_input_image(path):
    p = Path(path).resolve()
    try:
        p.relative_to(ROOT)
    except ValueError as exc:
        raise RuntimeError("image path must stay under D:\\Velvet") from exc
    if p.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
        raise RuntimeError("image input must be PNG or JPEG")
    if not p.is_file() or p.stat().st_size <= 0:
        raise RuntimeError("image input is missing or empty")
    return p


class CorelHost:
    def __init__(self, app_id):
        self.app_id = app_id
        self.cfg = APPS[app_id]
        self.owned = False
        self.app = None
        pythoncom.CoInitialize()
        try:
            existing = None
            try:
                existing = win32com.client.GetActiveObject(self.cfg["progid"])
            except Exception:
                existing = None
            if existing is not None:
                existing = None
                raise RuntimeError("refusing to attach to a pre-existing user Corel session")
            self.app = win32com.client.Dispatch(self.cfg["progid"])
            self.owned = True
            self.app.Visible = False
        except Exception:
            pythoncom.CoUninitialize()
            raise

    def probe(self):
        name = str(self.app.Name)
        version = str(self.app.Version)
        visible = bool(self.app.Visible)
        docs = int(self.app.Documents.Count)
        ok = (
            name == self.cfg["expected_name"]
            and version == self.cfg["expected_version"]
            and visible is False
        )
        return {
            "status": "PASS" if ok else "FAIL",
            "app": self.app_id,
            "name": name,
            "version": version,
            "visible": visible,
            "documents": docs,
            "session": session_id(),
            "owned_by_adapter": self.owned,
            "server_pid": os.getpid(),
            "automation": "official_com",
        }

    def status(self):
        return self.probe()

    def acceptance(self):
        if not read_gate(self.app_id):
            raise RuntimeError("acceptance gate is not enabled for this app")
        if not self.owned:
            raise RuntimeError("refusing acceptance on a pre-existing user Corel session")
        if int(self.app.Documents.Count) != 0:
            raise RuntimeError("acceptance requires zero open documents")
        out_dir = ROOT / "Tmp" / "creative-tools" / "corel"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{self.app_id}-acceptance.pdf"
        if out_path.exists():
            out_path.unlink()
        doc = None
        stage = "create_document"
        try:
            doc = self.app.CreateDocument()
            stage = "create_rectangle"
            shape = doc.ActiveLayer.CreateRectangle2(10.0, 10.0, 40.0, 20.0)
            stage = "get_uniform_fill"
            fill = shape.Fill.UniformColor
            stage = "assign_rgb"
            fill.RGBAssign(*COLOR)
            stage = "readback"
            readback = {
                "pages": int(doc.Pages.Count),
                "shapes": int(doc.ActivePage.Shapes.Count),
                "position_x": float(shape.PositionX),
                "position_y": float(shape.PositionY),
                "width": float(shape.SizeWidth),
                "height": float(shape.SizeHeight),
                "fill_rgb": [int(fill.RGBRed), int(fill.RGBGreen), int(fill.RGBBlue)],
            }
            stage = "publish_pdf"
            doc.PublishToPDF(str(out_path))
            stage = "verify_pdf"
            artifact = pdf_info(out_path)
            stage = "close_document"
            doc.Dirty = False
            doc.Close()
            doc = None
            post_docs = int(self.app.Documents.Count)
            if post_docs != 0:
                raise RuntimeError(f"cleanup failed; documents={post_docs}")
            return {
                "status": "PASS",
                "app": self.app_id,
                "readback": readback,
                "artifact": {"path": str(out_path), **artifact},
                "post_documents": post_docs,
            }
        except Exception as exc:
            raise RuntimeError(f"{stage}: {exc}") from exc
        finally:
            if doc is not None:
                try:
                    doc.Dirty = False
                    doc.Close()
                except Exception:
                    pass

    def craft(self, spec):
        if not self.owned:
            raise RuntimeError("refusing craft on a pre-existing user Corel session")
        if int(self.app.Documents.Count) != 0:
            raise RuntimeError("craft requires zero open documents")
        if not isinstance(spec, dict):
            raise RuntimeError("craft spec must be a JSON object")
        job_id = safe_slug(spec.get("job_id"))
        page = spec.get("page")
        if not isinstance(page, dict):
            raise RuntimeError("page must be an object")
        page_w = finite_number(page.get("width_mm"), "page.width_mm", 10.0, 2000.0)
        page_h = finite_number(page.get("height_mm"), "page.height_mm", 10.0, 2000.0)
        objects = spec.get("objects")
        if not isinstance(objects, list) or not 1 <= len(objects) <= MAX_CRAFT_OBJECTS:
            raise RuntimeError(f"objects must contain 1..{MAX_CRAFT_OBJECTS} items")
        outputs = spec.get("outputs", ["pdf", "cdr"])
        if not isinstance(outputs, list) or not outputs:
            raise RuntimeError("outputs must be a non-empty list")
        if any(x not in ("pdf", "cdr") for x in outputs):
            raise RuntimeError("outputs may contain only pdf and cdr")
        outputs = list(dict.fromkeys(outputs))
        CRAFT_OUTPUT.mkdir(parents=True, exist_ok=True)
        base = CRAFT_OUTPUT / f"{job_id}-{self.app_id}"
        targets = {ext: base.with_suffix(f".{ext}") for ext in outputs}
        for target in targets.values():
            if target.exists():
                raise RuntimeError(f"refusing to overwrite existing output: {target}")

        doc = None
        created = []
        created_paths = []
        stage = "create_document"
        try:
            doc = self.app.CreateDocument()
            doc.Unit = 3
            doc.ActivePage.SetSize(page_w, page_h)
            layer = doc.ActiveLayer
            for index, obj in enumerate(objects):
                if not isinstance(obj, dict):
                    raise RuntimeError(f"objects[{index}] must be an object")
                kind = obj.get("type")
                stage = f"object_{index}_{kind}"
                shape = None
                if kind == "rect":
                    x = finite_number(obj.get("x_mm"), f"objects[{index}].x_mm")
                    y = finite_number(obj.get("y_mm"), f"objects[{index}].y_mm")
                    w = finite_number(obj.get("width_mm"), f"objects[{index}].width_mm", 0.01, 2000.0)
                    h = finite_number(obj.get("height_mm"), f"objects[{index}].height_mm", 0.01, 2000.0)
                    radius = finite_number(obj.get("radius_mm", 0.0), f"objects[{index}].radius_mm", 0.0, 1000.0)
                    shape = layer.CreateRectangle2(x, y, w, h, radius, radius, radius, radius)
                    if "fill" in obj:
                        shape.Fill.UniformColor.RGBAssign(*rgb(obj["fill"], f"objects[{index}].fill"))
                    else:
                        shape.Fill.ApplyNoFill()
                elif kind == "ellipse":
                    cx = finite_number(obj.get("cx_mm"), f"objects[{index}].cx_mm")
                    cy = finite_number(obj.get("cy_mm"), f"objects[{index}].cy_mm")
                    rx = finite_number(obj.get("rx_mm"), f"objects[{index}].rx_mm", 0.01, 1000.0)
                    ry = finite_number(obj.get("ry_mm", rx), f"objects[{index}].ry_mm", 0.01, 1000.0)
                    shape = layer.CreateEllipse2(cx, cy, rx, ry)
                    if "fill" in obj:
                        shape.Fill.UniformColor.RGBAssign(*rgb(obj["fill"], f"objects[{index}].fill"))
                    else:
                        shape.Fill.ApplyNoFill()
                elif kind == "line":
                    x1 = finite_number(obj.get("x1_mm"), f"objects[{index}].x1_mm")
                    y1 = finite_number(obj.get("y1_mm"), f"objects[{index}].y1_mm")
                    x2 = finite_number(obj.get("x2_mm"), f"objects[{index}].x2_mm")
                    y2 = finite_number(obj.get("y2_mm"), f"objects[{index}].y2_mm")
                    shape = layer.CreateLineSegment(x1, y1, x2, y2)
                    stroke = rgb(obj.get("stroke", [0, 0, 0]), f"objects[{index}].stroke")
                    shape.Outline.Color.RGBAssign(*stroke)
                elif kind == "text":
                    x = finite_number(obj.get("x_mm"), f"objects[{index}].x_mm")
                    y = finite_number(obj.get("y_mm"), f"objects[{index}].y_mm")
                    text = str(obj.get("text", ""))
                    if not 1 <= len(text) <= 2000:
                        raise RuntimeError(f"objects[{index}].text must contain 1..2000 characters")
                    font = str(obj.get("font", "Arial"))
                    if not 1 <= len(font) <= 128:
                        raise RuntimeError(f"objects[{index}].font is invalid")
                    size = finite_number(obj.get("size_pt", 18.0), f"objects[{index}].size_pt", 1.0, 500.0)
                    bold = 1 if bool(obj.get("bold", False)) else 0
                    italic = 1 if bool(obj.get("italic", False)) else 0
                    shape = layer.CreateArtisticText(x, y, text, 0, -1, font, size, bold, italic, 7, 6)
                    shape.Fill.UniformColor.RGBAssign(*rgb(obj.get("fill", [0, 0, 0]), f"objects[{index}].fill"))
                elif kind == "image":
                    image_path = safe_input_image(obj.get("path"))
                    x = finite_number(obj.get("x_mm"), f"objects[{index}].x_mm")
                    y = finite_number(obj.get("y_mm"), f"objects[{index}].y_mm")
                    w = finite_number(obj.get("width_mm"), f"objects[{index}].width_mm", 0.01, 2000.0)
                    h = finite_number(obj.get("height_mm"), f"objects[{index}].height_mm", 0.01, 2000.0)
                    before_count = int(layer.Shapes.Count)
                    import_filter = layer.ImportEx(str(image_path), 0, self.app.CreateStructImportOptions())
                    import_filter.Finish()
                    selection = self.app.ActiveSelectionRange
                    if int(selection.Count) < 1:
                        raise RuntimeError("image import completed without a selected shape")
                    shape = selection.Item(1)
                    if int(layer.Shapes.Count) <= before_count:
                        raise RuntimeError("image import did not add a shape")
                    shape.SetSize(w, h)
                    shape.SetPosition(x, y)
                else:
                    raise RuntimeError(f"unsupported object type at index {index}: {kind}")
                created.append({
                    "index": index,
                    "type": kind,
                    "position_x": float(shape.PositionX),
                    "position_y": float(shape.PositionY),
                    "width": float(shape.SizeWidth),
                    "height": float(shape.SizeHeight),
                })

            artifacts = {}
            if "cdr" in targets:
                stage = "save_cdr"
                doc.SaveAsCopy(str(targets["cdr"]), self.app.CreateStructSaveAsOptions())
                created_paths.append(targets["cdr"])
                artifacts["cdr"] = stable_file_info(targets["cdr"])
            if "pdf" in targets:
                stage = "publish_pdf"
                doc.PublishToPDF(str(targets["pdf"]))
                created_paths.append(targets["pdf"])
                artifacts["pdf"] = {"path": str(targets["pdf"]), **pdf_info(targets["pdf"])}
            stage = "close_document"
            doc.Dirty = False
            doc.Close()
            doc = None
            post_docs = int(self.app.Documents.Count)
            if post_docs != 0:
                raise RuntimeError(f"cleanup failed; documents={post_docs}")
            return {
                "status": "PASS",
                "app": self.app_id,
                "job_id": job_id,
                "page_mm": [page_w, page_h],
                "objects": created,
                "shape_count": int(len(created)),
                "artifacts": artifacts,
                "post_documents": post_docs,
            }
        except Exception as exc:
            for path in targets.values():
                try:
                    Path(path).unlink(missing_ok=True)
                except Exception:
                    pass
            raise RuntimeError(f"{stage}: {exc}") from exc
        finally:
            if doc is not None:
                try:
                    doc.Dirty = False
                    doc.Close()
                except Exception:
                    pass

    def shutdown(self):
        docs = int(self.app.Documents.Count)
        if docs != 0:
            return {
                "status": "FAIL",
                "app": self.app_id,
                "error": f"refusing shutdown with {docs} open document(s)",
            }
        quit_app = False
        if self.owned:
            self.app.Quit()
            quit_app = True
        return {
            "status": "PASS",
            "app": self.app_id,
            "quit_app": quit_app,
            "left_preexisting_app_running": not self.owned,
        }

    def close(self):
        self.app = None
        pythoncom.CoUninitialize()

class SafeServer(HTTPServer):
    allow_reuse_address = False

    def __init__(self, address, handler, host, token):
        self.corel_host = host
        self.token = token
        self.should_stop = False
        super().__init__(address, handler)


class Handler(BaseHTTPRequestHandler):
    server_version = "VelvetCorelSafe/0.2.0"

    def log_message(self, fmt, *args):
        return

    def reply(self, code, payload):
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def authorized(self):
        return self.headers.get("Authorization", "") == f"Bearer {self.server.token}"

    def do_GET(self):
        if not self.authorized():
            self.reply(401, {"status": "FAIL", "error": "unauthorized"})
            return
        try:
            if self.path == "/probe":
                self.reply(200, self.server.corel_host.probe())
            elif self.path == "/status":
                self.reply(200, self.server.corel_host.status())
            else:
                self.reply(404, {"status": "FAIL", "error": "not_found"})
        except Exception as exc:
            self.reply(500, {"status": "FAIL", "error": str(exc)})

    def do_POST(self):
        if not self.authorized():
            self.reply(401, {"status": "FAIL", "error": "unauthorized"})
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length > 131072:
            self.reply(413, {"status": "FAIL", "error": "request_too_large"})
            return
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            self.reply(400, {"status": "FAIL", "error": "invalid_json"})
            return
        if not isinstance(payload, dict):
            self.reply(400, {"status": "FAIL", "error": "json_body_must_be_object"})
            return
        try:
            if self.path == "/acceptance":
                self.reply(200, self.server.corel_host.acceptance())
            elif self.path == "/craft":
                self.reply(200, self.server.corel_host.craft(payload))
            elif self.path == "/shutdown":
                result = self.server.corel_host.shutdown()
                self.reply(200 if result["status"] == "PASS" else 409, result)
                if result["status"] == "PASS":
                    self.server.should_stop = True
            else:
                self.reply(404, {"status": "FAIL", "error": "not_found"})
        except Exception as exc:
            self.reply(500, {"status": "FAIL", "error": str(exc)})


def serve(app_id):
    cfg = APPS[app_id]
    token = load_token()
    host = CorelHost(app_id)
    server = SafeServer(("127.0.0.1", cfg["port"]), Handler, host, token)
    server.timeout = 0.5
    try:
        while not server.should_stop:
            server.handle_request()
    finally:
        server.server_close()
        host.close()


def client_call(app_id, action):
    cfg = APPS[app_id]
    token = load_token()
    method = "GET" if action in ("probe", "status") else "POST"
    req = Request(
        f"http://127.0.0.1:{cfg['port']}/{action}",
        method=method,
        headers={"Authorization": f"Bearer {token}"},
        data=None if method == "GET" else b"{}",
    )
    try:
        with urlopen(req, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        payload = json.loads(exc.read().decode("utf-8"))
    except URLError as exc:
        payload = {"status": "FAIL", "error": str(exc)}
    print(json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
    return 0 if payload.get("status") == "PASS" else 1


def main():
    parser = argparse.ArgumentParser(description="VelvetOS safe Corel COM adapter")
    parser.add_argument("action", choices=["serve", "probe", "status", "acceptance", "shutdown"])
    parser.add_argument("--app", required=True, choices=sorted(APPS))
    args = parser.parse_args()
    if args.action == "serve":
        serve(args.app)
        return 0
    return client_call(args.app, args.action)


if __name__ == "__main__":
    sys.exit(main())
