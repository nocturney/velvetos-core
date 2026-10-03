import argparse, hashlib, json, re, sys, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import pythoncom, win32com.client, win32com.client.dynamic

ROOT=Path(r"D:\Velvet").resolve()
STATE=ROOT/"State"/"MissingIntegrationsPhase2"
TOKEN_FILE=STATE/"adapter-token.txt"
TMP=ROOT/"Tmp"/"creative-tools"/"missing-integrations-phase2"
OUTPUT=ROOT/"Output"/"CreativeCraft"/"PhotoPaint"
PROGID="CorelPHOTOPAINT.Application.27"
PORT=6782


def file_info(path,prefix=None):
    p=Path(path); deadline=time.monotonic()+10; last=None; stable=0
    while time.monotonic()<deadline:
        if p.is_file():
            s=p.stat(); mark=(s.st_size,s.st_mtime_ns)
            stable=stable+1 if s.st_size>0 and mark==last else 0; last=mark
            if stable>=3: break
        time.sleep(.2)
    data=p.read_bytes()
    if prefix and not data.startswith(prefix): raise RuntimeError("unexpected output format")
    return {"path":str(p),"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest().upper()}
def safe_path(value, exts=None):
    p=Path(value).resolve()
    try: p.relative_to(ROOT)
    except ValueError as e: raise RuntimeError("path must stay under D:\\Velvet") from e
    if exts and p.suffix.lower() not in exts: raise RuntimeError("unsupported file extension")
    return p


def slug(value):
    value=str(value or "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}",value): raise RuntimeError("invalid job_id")
    return value


def load_token():
    token=TOKEN_FILE.read_text(encoding="utf-8").strip()
    if len(token)<32: raise RuntimeError("adapter token missing or too short")
    return token


class PhotoPaintHost:
    def __init__(self):
        pythoncom.CoInitialize(); self.app=None; self.owned=False
        try:
            try: existing=win32com.client.GetActiveObject(PROGID)
            except Exception: existing=None
            if existing is not None: raise RuntimeError("refusing to attach to pre-existing PHOTO-PAINT session")
            self.app=win32com.client.dynamic.DumbDispatch(PROGID); self.owned=True; self.app.Visible=False
        except Exception:
            pythoncom.CoUninitialize(); raise
    def probe(self):
        return {"status":"PASS","app":"photopaint","name":str(self.app.Name),"version":str(self.app.Version),
                "visible":bool(self.app.Visible),"documents":int(self.app.Documents.Count),"automation":"official_com"}

    def acceptance(self):
        TMP.mkdir(parents=True,exist_ok=True); out=TMP/"photopaint-acceptance.png"
        out.unlink(missing_ok=True); doc=None
        stage="create_background"
        try:
            bg=self.app.CreateRGBColor(255,255,255)
            stage="create_document"
            doc=self.app.CreateDocument(160,120,4,96,96,True,bg,False,1)
            stage="readback"
            readback={"width":int(doc.SizeWidth),"height":int(doc.SizeHeight),"dpi_x":float(doc.DpiX),"dpi_y":float(doc.DpiY),"layers":int(doc.Layers.Count)}
            stage="save_options"
            opts=self.app.CreateStructSaveOptions()
            stage="save_as"
            filt=doc.SaveAs(str(out),802,opts)
            stage="finish_export"
            filt.Finish(); filt=None
            stage="verify_file"
            artifact=file_info(out,b"\x89PNG\r\n\x1a\n")
            stage="close_document"
            doc.Close(); doc=None
            return {"status":"PASS","app":"photopaint","readback":readback,"artifact":artifact,"post_documents":int(self.app.Documents.Count)}
        except Exception as e:
            raise RuntimeError(f"{stage}: {e}") from e
        finally:
            if doc is not None:
                try: doc.Close()
                except Exception: pass

    def transform(self,spec):
        if not isinstance(spec,dict): raise RuntimeError("spec must be an object")
        job=slug(spec.get("job_id")); src=safe_path(spec.get("input"),{".png",".jpg",".jpeg",".tif",".tiff",".bmp",".cpt"})
        if not src.is_file(): raise RuntimeError("input file missing")
        fmt=str(spec.get("format","png")).lower()
        if fmt not in {"png","jpeg"}: raise RuntimeError("format must be png or jpeg")
        width=spec.get("width_px"); height=spec.get("height_px")
        if width is not None and (not isinstance(width,int) or not 1<=width<=30000): raise RuntimeError("invalid width_px")
        if height is not None and (not isinstance(height,int) or not 1<=height<=30000): raise RuntimeError("invalid height_px")
        OUTPUT.mkdir(parents=True,exist_ok=True); out=OUTPUT/f"{job}.{'png' if fmt=='png' else 'jpg'}"
        if out.exists(): raise RuntimeError("refusing to overwrite existing output")
        doc=None
        try:
            doc=self.app.OpenDocument(str(src))
            before={"width":int(doc.SizeWidth),"height":int(doc.SizeHeight),"dpi_x":float(doc.DpiX),"dpi_y":float(doc.DpiY)}
            if width is not None or height is not None:
                w=width if width is not None else int(doc.SizeWidth); h=height if height is not None else int(doc.SizeHeight)
                doc.Resample(w,h,True)
            flt=802 if fmt=="png" else 774
            opts=self.app.CreateStructSaveOptions()
            ef=doc.SaveAs(str(out),flt,opts); ef.Finish(); ef=None
            after={"width":int(doc.SizeWidth),"height":int(doc.SizeHeight),"dpi_x":float(doc.DpiX),"dpi_y":float(doc.DpiY)}
            artifact=file_info(out,b"\x89PNG" if fmt=="png" else b"\xff\xd8\xff")
            doc.Close(); doc=None
            return {"status":"PASS","app":"photopaint","job_id":job,"before":before,"after":after,"artifact":artifact}
        except Exception:
            out.unlink(missing_ok=True); raise
        finally:
            if doc is not None:
                try: doc.Close()
                except Exception: pass
    def shutdown(self):
        if int(self.app.Documents.Count): return {"status":"FAIL","error":"open documents prevent shutdown"}
        if self.owned: self.app.Quit()
        return {"status":"PASS","quit_app":self.owned}

    def close(self):
        self.app=None; pythoncom.CoUninitialize()


class Server(HTTPServer):
    allow_reuse_address=False
    def __init__(self,addr,handler,host,token): self.host=host; self.token=token; self.stop=False; super().__init__(addr,handler)


class Handler(BaseHTTPRequestHandler):
    server_version="VelvetPhotoPaintSafe/0.1.0"
    def log_message(self,*args): return
    def reply(self,code,obj):
        raw=json.dumps(obj,separators=(",",":"),ensure_ascii=False).encode(); self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def auth(self): return self.headers.get("Authorization","")==f"Bearer {self.server.token}"
    def body(self):
        n=int(self.headers.get("Content-Length","0") or 0)
        if n>131072: raise RuntimeError("request too large")
        return json.loads(self.rfile.read(n).decode() or "{}")
    def do_GET(self):
        if not self.auth(): return self.reply(401,{"status":"FAIL","error":"unauthorized"})
        try:
            if self.path in ("/probe","/status"): return self.reply(200,self.server.host.probe())
            self.reply(404,{"status":"FAIL","error":"not_found"})
        except Exception as e: self.reply(500,{"status":"FAIL","error":str(e)})
    def do_POST(self):
        if not self.auth(): return self.reply(401,{"status":"FAIL","error":"unauthorized"})
        try:
            body=self.body()
            if self.path=="/acceptance": result=self.server.host.acceptance()
            elif self.path=="/transform": result=self.server.host.transform(body)
            elif self.path=="/shutdown":
                result=self.server.host.shutdown(); self.server.stop=result.get("status")=="PASS"
            else: return self.reply(404,{"status":"FAIL","error":"not_found"})
            self.reply(200 if result.get("status")=="PASS" else 409,result)
        except Exception as e: self.reply(500,{"status":"FAIL","error":str(e)})


def serve():
    host=PhotoPaintHost(); server=Server(("127.0.0.1",PORT),Handler,host,load_token()); server.timeout=.5
    try:
        while not server.stop: server.handle_request()
    finally: server.server_close(); host.close()
def client(action,spec=None):
    method="GET" if action in ("probe","status") else "POST"; data=None if method=="GET" else json.dumps(spec or {}).encode()
    req=Request(f"http://127.0.0.1:{PORT}/{action}",method=method,data=data,headers={"Authorization":f"Bearer {load_token()}","Content-Type":"application/json"})
    try:
        with urlopen(req,timeout=30) as r: obj=json.loads(r.read().decode())
    except HTTPError as e: obj=json.loads(e.read().decode())
    except URLError as e: obj={"status":"FAIL","error":str(e)}
    print(json.dumps(obj,separators=(",",":"),ensure_ascii=False)); return 0 if obj.get("status")=="PASS" else 1


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("action",choices=["serve","probe","status","acceptance","transform","shutdown"]); ap.add_argument("--spec")
    a=ap.parse_args()
    if a.action=="serve": serve(); return 0
    spec=json.loads(Path(a.spec).read_text(encoding="utf-8")) if a.spec else None
    return client(a.action,spec)

if __name__=="__main__": sys.exit(main())
