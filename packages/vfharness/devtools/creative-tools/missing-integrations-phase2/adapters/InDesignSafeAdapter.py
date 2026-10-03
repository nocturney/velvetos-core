import argparse, hashlib, json, re, sys, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import pythoncom, win32com.client

ROOT=Path(r"D:\Velvet").resolve()
STATE=ROOT/"State"/"MissingIntegrationsPhase2"
TOKEN_FILE=STATE/"adapter-token.txt"
TMP=ROOT/"Tmp"/"creative-tools"/"missing-integrations-phase2"
OUTPUT=ROOT/"Output"/"CreativeCraft"/"InDesign"
PROGID="InDesign.Application.2026"; PORT=6781
PDF_FORMAT=1952403524; IDML_FORMAT=1768189292; SAVE_NO=1852776480


def file_info(path,prefix=None):
    p=Path(path); deadline=time.monotonic()+12; last=None; stable=0
    while time.monotonic()<deadline:
        if p.is_file():
            s=p.stat(); mark=(s.st_size,s.st_mtime_ns)
            stable=stable+1 if s.st_size>0 and mark==last else 0; last=mark
            if stable>=3: break
        time.sleep(.2)
    data=p.read_bytes()
    if prefix and not data.startswith(prefix): raise RuntimeError("unexpected output format")
    return {"path":str(p),"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest().upper()}
def slug(value):
    value=str(value or "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}",value): raise RuntimeError("invalid job_id")
    return value


def load_token():
    token=TOKEN_FILE.read_text(encoding="utf-8").strip()
    if len(token)<32: raise RuntimeError("adapter token missing or too short")
    return token


class InDesignHost:
    def __init__(self):
        pythoncom.CoInitialize(); self.app=None; self.owned=False
        try:
            try: existing=win32com.client.GetActiveObject(PROGID)
            except Exception: existing=None
            if existing is not None: raise RuntimeError("refusing to attach to pre-existing InDesign session")
            self.app=win32com.client.gencache.EnsureDispatch(PROGID); self.owned=True
            try: self.app.ScriptPreferences.UserInteractionLevel=win32com.client.constants.idNeverInteract
            except Exception: pass
        except Exception:
            pythoncom.CoUninitialize(); raise

    def probe(self):
        return {"status":"PASS","app":"indesign","name":str(self.app.Name),"version":str(self.app.Version),
                "documents":int(self.app.Documents.Count),"automation":"official_com","owned_by_adapter":self.owned}
    def _make(self,job,title,body,out_dir):
        out_dir.mkdir(parents=True,exist_ok=True); pdf=out_dir/f"{job}.pdf"; idml=out_dir/f"{job}.idml"
        if pdf.exists() or idml.exists(): raise RuntimeError("refusing to overwrite existing output")
        doc=None
        try:
            doc=self.app.Documents.Add(); page=doc.Pages.Item(1); frame=page.TextFrames.Add()
            frame.GeometricBounds=[36.0,36.0,360.0,540.0]; frame.Contents=(str(title)+"\r\r"+str(body))[:20000]
            readback={"pages":int(doc.Pages.Count),"text_frames":int(page.TextFrames.Count),"characters":len(str(frame.Contents))}
            doc.Export(PDF_FORMAT,str(pdf)); doc.Export(IDML_FORMAT,str(idml))
            artifacts={"pdf":file_info(pdf,b"%PDF-"),"idml":file_info(idml,b"PK")}
            doc.Close(SAVE_NO); doc=None
            return {"status":"PASS","app":"indesign","job_id":job,"readback":readback,"artifacts":artifacts,"post_documents":int(self.app.Documents.Count)}
        except Exception:
            pdf.unlink(missing_ok=True); idml.unlink(missing_ok=True); raise
        finally:
            if doc is not None:
                try: doc.Close(SAVE_NO)
                except Exception: pass

    def acceptance(self):
        TMP.mkdir(parents=True,exist_ok=True)
        for p in (TMP/"indesign-acceptance.pdf",TMP/"indesign-acceptance.idml"): p.unlink(missing_ok=True)
        return self._make("indesign-acceptance","VelvetOS Phase 2","InDesign official COM acceptance",TMP)
    def compose(self,spec):
        if not isinstance(spec,dict): raise RuntimeError("spec must be an object")
        job=slug(spec.get("job_id")); title=str(spec.get("title","")).strip(); body=str(spec.get("body","")).strip()
        if not 1<=len(title)<=500: raise RuntimeError("title must contain 1..500 characters")
        if not 1<=len(body)<=19000: raise RuntimeError("body must contain 1..19000 characters")
        return self._make(job,title,body,OUTPUT)

    def shutdown(self):
        if int(self.app.Documents.Count): return {"status":"FAIL","error":"open documents prevent shutdown"}
        if self.owned: self.app.Quit()
        return {"status":"PASS","quit_app":self.owned}

    def close(self): self.app=None; pythoncom.CoUninitialize()


class Server(HTTPServer):
    allow_reuse_address=False
    def __init__(self,addr,handler,host,token): self.host=host; self.token=token; self.stop=False; super().__init__(addr,handler)


class Handler(BaseHTTPRequestHandler):
    server_version="VelvetInDesignSafe/0.1.0"
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
            elif self.path=="/compose": result=self.server.host.compose(body)
            elif self.path=="/shutdown": result=self.server.host.shutdown(); self.server.stop=result.get("status")=="PASS"
            else: return self.reply(404,{"status":"FAIL","error":"not_found"})
            self.reply(200 if result.get("status")=="PASS" else 409,result)
        except Exception as e: self.reply(500,{"status":"FAIL","error":str(e)})
def serve():
    host=InDesignHost(); server=Server(("127.0.0.1",PORT),Handler,host,load_token()); server.timeout=.5
    try:
        while not server.stop: server.handle_request()
    finally: server.server_close(); host.close()


def client(action,spec=None):
    method="GET" if action in ("probe","status") else "POST"; data=None if method=="GET" else json.dumps(spec or {}).encode()
    req=Request(f"http://127.0.0.1:{PORT}/{action}",method=method,data=data,headers={"Authorization":f"Bearer {load_token()}","Content-Type":"application/json"})
    try:
        with urlopen(req,timeout=40) as r: obj=json.loads(r.read().decode())
    except HTTPError as e: obj=json.loads(e.read().decode())
    except URLError as e: obj={"status":"FAIL","error":str(e)}
    print(json.dumps(obj,separators=(",",":"),ensure_ascii=False)); return 0 if obj.get("status")=="PASS" else 1


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("action",choices=["serve","probe","status","acceptance","compose","shutdown"]); ap.add_argument("--spec")
    a=ap.parse_args()
    if a.action=="serve": serve(); return 0
    spec=json.loads(Path(a.spec).read_text(encoding="utf-8")) if a.spec else None
    return client(a.action,spec)

if __name__=="__main__": sys.exit(main())
