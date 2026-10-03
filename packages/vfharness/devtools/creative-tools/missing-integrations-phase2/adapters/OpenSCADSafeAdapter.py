import argparse, hashlib, json, re, subprocess, sys, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT=Path(r"D:\Velvet").resolve()
STATE=ROOT/"State"/"MissingIntegrationsPhase2"
TOKEN_FILE=STATE/"adapter-token.txt"
TMP=ROOT/"Tmp"/"creative-tools"/"missing-integrations-phase2"
OUTPUT=ROOT/"Output"/"CreativeCraft"/"OpenSCAD"
EXE=Path(r"C:\Program Files\OpenSCAD (Nightly)\openscad.com")
PORT=6785

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
    if p.suffix.lower()!=".scad": raise RuntimeError("input must be .scad")
    if not p.is_file(): raise RuntimeError("input file missing")
    return p

def file_info(path):
    p=Path(path); data=p.read_bytes()
    if not data: raise RuntimeError("empty output")
    return {"path":str(p),"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest().upper()}

def run(args,timeout=120):
    cp=subprocess.run([str(EXE),*args],capture_output=True,text=True,timeout=timeout,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    if cp.returncode!=0: raise RuntimeError((cp.stderr or cp.stdout or f"OpenSCAD exit {cp.returncode}").strip())
    return cp

def probe():
    cp=run(["--version"],20)
    txt=(cp.stdout or cp.stderr).strip()
    return {"status":"PASS","app":"openscad","version":txt.replace("OpenSCAD version ",""),"automation":"official_cli"}

def render(spec,out_dir):
    if not isinstance(spec,dict): raise RuntimeError("spec must be an object")
    job=slug(spec.get("job_id")); src=safe_input(spec.get("input"))
    fmt=str(spec.get("format","stl")).lower()
    if fmt not in {"stl","3mf"}: raise RuntimeError("format must be stl or 3mf")
    out_dir.mkdir(parents=True,exist_ok=True)
    out=out_dir/f"{job}.{fmt}"
    if out.exists(): raise RuntimeError("refusing to overwrite existing output")
    args=["-o",str(out),str(src)]
    try:
        cp=run(args,180)
        info=file_info(out)
        return {"status":"PASS","app":"openscad","job_id":job,"source":str(src),"format":fmt,"artifact":info,"stderr":cp.stderr.strip()[-2000:]}
    except Exception:
        out.unlink(missing_ok=True); raise

def acceptance():
    TMP.mkdir(parents=True,exist_ok=True)
    src=TMP/"openscad-acceptance.scad"; out=TMP/"openscad-acceptance.stl"
    src.write_text("cube([10,20,30], center=false);\n",encoding="utf-8")
    out.unlink(missing_ok=True)
    return render({"job_id":"openscad-acceptance","input":str(src),"format":"stl"},TMP)

class Server(HTTPServer):
    allow_reuse_address=False
    def __init__(self,addr,handler,token): self.token=token; super().__init__(addr,handler)

class Handler(BaseHTTPRequestHandler):
    server_version="VelvetOpenSCADSafe/0.1.0"
    def log_message(self,*args): return
    def reply(self,code,obj):
        raw=json.dumps(obj,separators=(",",":"),ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def auth(self): return self.headers.get("Authorization","")==f"Bearer {self.server.token}"
    def body(self):
        n=int(self.headers.get("Content-Length","0") or 0)
        if n>131072: raise RuntimeError("request too large")
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
            elif self.path=="/render": result=render(self.body(),OUTPUT)
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
    req=Request(f"http://127.0.0.1:{PORT}/{action}",method=method,data=data,headers={"Authorization":f"Bearer {load_token()}","Content-Type":"application/json"})
    try:
        with urlopen(req,timeout=190) as r: obj=json.loads(r.read().decode())
    except HTTPError as e: obj=json.loads(e.read().decode())
    except URLError as e: obj={"status":"FAIL","error":str(e)}
    print(json.dumps(obj,separators=(",",":"),ensure_ascii=False)); return 0 if obj.get("status")=="PASS" else 1

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("action",choices=["serve","probe","status","acceptance","render"]); ap.add_argument("--spec")
    a=ap.parse_args()
    if a.action=="serve": serve(); return 0
    spec=json.loads(Path(a.spec).read_text(encoding="utf-8")) if a.spec else None
    return client(a.action,spec)

if __name__=="__main__": sys.exit(main())
