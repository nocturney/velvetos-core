import argparse, hashlib, json, os, re, shutil, subprocess, sys, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT=Path(r"D:\Velvet").resolve()
STATE=ROOT/"State"/"MissingIntegrationsPhase2"
TOKEN_FILE=STATE/"adapter-token.txt"
TMP=ROOT/"Tmp"/"creative-tools"/"missing-integrations-phase2"
OUTPUT=ROOT/"Output"/"CreativeCraft"/"XVLHtml5"
XVL_ROOT=Path(r"C:\Program Files\Lattice\XVLStudio3DCADCorelEdition27")
GEN=XVL_ROOT/"xvlgenhtm.exe"
TEMPLATE=XVL_ROOT/"Etc"/"HTML5"
SAMPLE=XVL_ROOT/"Samples"/"Model"/"DigitalCamera_from_CAD.xv2"
PORT=6790

def load_token():
    v=TOKEN_FILE.read_text(encoding="utf-8").strip()
    if len(v)<32: raise RuntimeError("adapter token missing or too short")
    return v

def slug(v):
    s=str(v or "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}",s): raise RuntimeError("invalid job_id")
    return s
def safe_input(v):
    p=Path(v).resolve()
    try: p.relative_to(ROOT)
    except ValueError as e: raise RuntimeError("input must stay under D:\\Velvet") from e
    if p.suffix.lower()!=".xv2" or not p.is_file():
        raise RuntimeError("input must be an existing .xv2 file")
    return p

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest().upper()

def validate_package(html):
    html=Path(html)
    files_dir=html.with_suffix(".files")
    if not html.is_file() or html.stat().st_size<1000:
        raise RuntimeError("generated HTML missing or too small")
    js=files_dir/"viewing.js"
    jpgs=list(files_dir.glob("*.jpg"))
    res=list((files_dir/"res").glob("*.png")) if (files_dir/"res").is_dir() else []
    if not files_dir.is_dir() or not js.is_file() or not jpgs:
        raise RuntimeError("generated HTML5 package is incomplete")
    all_files=[p for p in files_dir.rglob("*") if p.is_file()]
    return {
        "html":{"path":str(html),"bytes":html.stat().st_size,"sha256":sha(html)},
        "sidecar_dir":str(files_dir),
        "file_count":1+len(all_files),
        "jpg_count":len(jpgs),
        "resource_png_count":len(res),
        "viewing_js":{"bytes":js.stat().st_size,"sha256":sha(js)},
        "total_bytes":html.stat().st_size+sum(p.stat().st_size for p in all_files),
    }
def publish(spec,out_root=OUTPUT):
    if not isinstance(spec,dict): raise RuntimeError("spec must be an object")
    job=slug(spec.get("job_id"))
    src=safe_input(spec.get("input"))
    out_dir=Path(out_root)/job
    html=out_dir/"index.html"
    if out_dir.exists(): raise RuntimeError("refusing to overwrite existing job output")
    out_dir.mkdir(parents=True,exist_ok=False)
    cmd=[str(GEN),"-a:eng",f"-t:{TEMPLATE}",str(src),str(html)]
    try:
        cp=subprocess.run(cmd,cwd=str(XVL_ROOT),capture_output=True,text=True,timeout=300,
                          creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        if cp.returncode!=0:
            raise RuntimeError((cp.stderr or cp.stdout or f"xvlgenhtm exit {cp.returncode}").strip())
        package=validate_package(html)
        manifest={
            "job_id":job,"status":"PASS","app":"xvl-html5","automation":"bundled_xvlgenhtm_cli",
            "source":str(src),"source_sha256":sha(src),"package":package,
        }
        m=out_dir/"manifest.json"
        m.write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
        manifest["manifest"]={"path":str(m),"bytes":m.stat().st_size,"sha256":sha(m)}
        return manifest
    except Exception:
        shutil.rmtree(out_dir,ignore_errors=True)
        raise
def probe():
    missing=[str(p) for p in (GEN,TEMPLATE,SAMPLE) if not p.exists()]
    if missing: raise RuntimeError("missing XVL runtime components: "+", ".join(missing))
    cp=subprocess.run([str(GEN),"/?"],cwd=str(XVL_ROOT),capture_output=True,text=True,timeout=20,
                      creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    banner=(cp.stdout or cp.stderr or "").splitlines()
    return {"status":"PASS","app":"xvl-html5","automation":"bundled_xvlgenhtm_cli",
            "generator":str(GEN),"template":str(TEMPLATE),
            "banner":banner[0] if banner else "XVL HTML5 Generator",
            "full_studio_sdk":False,"supported_input":[".xv2"]}

def acceptance():
    TMP.mkdir(parents=True,exist_ok=True)
    fixture=TMP/"xvl-html5-acceptance-input.xv2"
    shutil.copy2(SAMPLE,fixture)
    out=TMP/"xvl-html5-acceptance"
    shutil.rmtree(out,ignore_errors=True)
    try:
        return publish({"job_id":"xvl-html5-acceptance","input":str(fixture)},TMP)
    finally:
        fixture.unlink(missing_ok=True)
class Server(HTTPServer):
    allow_reuse_address=False
    def __init__(self,addr,handler,token): self.token=token; super().__init__(addr,handler)

class Handler(BaseHTTPRequestHandler):
    server_version="VelvetXvlHtmlSafe/0.1.0"
    def log_message(self,*args): return
    def reply(self,code,obj):
        raw=json.dumps(obj,separators=(",",":"),ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def auth(self): return self.headers.get("Authorization","")==f"Bearer {self.server.token}"
    def body(self):
        n=int(self.headers.get("Content-Length","0") or 0)
        if n>65536: raise RuntimeError("request too large")
        return json.loads(self.rfile.read(n).decode() or "{}")
    def do_GET(self):
        if not self.auth(): return self.reply(401,{"status":"FAIL","error":"unauthorized"})
        try:
            if self.path in ("/probe","/status"): return self.reply(200,probe())
            self.reply(404,{"status":"FAIL","error":"not_found"})
        except Exception as e: self.reply(500,{"status":"FAIL","error":str(e)})
    def do_POST(self):
        if not self.auth(): return self.reply(401,{"status":"FAIL","error":"unauthorized"})
        try:
            if self.path=="/acceptance": result=acceptance()
            elif self.path=="/publish_html5": result=publish(self.body())
            elif self.path=="/shutdown":
                result={"status":"PASS","app":"xvl-html5","state":"SHUTTING_DOWN"}
                threading.Thread(target=self.server.shutdown,daemon=True).start()
            else: return self.reply(404,{"status":"FAIL","error":"not_found"})
            self.reply(200,result)
        except Exception as e: self.reply(500,{"status":"FAIL","error":str(e)})
def serve():
    s=Server(("127.0.0.1",PORT),Handler,load_token())
    try: s.serve_forever(poll_interval=.5)
    finally: s.server_close()

def client(action,spec=None):
    method="GET" if action in ("probe","status") else "POST"
    data=None if method=="GET" else json.dumps(spec or {}).encode()
    req=Request(f"http://127.0.0.1:{PORT}/{action}",method=method,data=data,
                headers={"Authorization":f"Bearer {load_token()}","Content-Type":"application/json"})
    try:
        with urlopen(req,timeout=360) as r: obj=json.loads(r.read().decode())
    except HTTPError as e: obj=json.loads(e.read().decode())
    except URLError as e: obj={"status":"FAIL","error":str(e)}
    print(json.dumps(obj,separators=(",",":"),ensure_ascii=False))
    return 0 if obj.get("status")=="PASS" else 1

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("action",choices=["serve","probe","status","acceptance","publish_html5","shutdown"])
    ap.add_argument("--spec"); a=ap.parse_args()
    if a.action=="serve": serve(); return 0
    spec=json.loads(Path(a.spec).read_text(encoding="utf-8")) if a.spec else None
    return client(a.action,spec)

if __name__=="__main__": sys.exit(main())
