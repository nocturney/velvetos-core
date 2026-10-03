import argparse, json, subprocess, sys, tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT=Path(r"D:\Velvet").resolve()
STATE=ROOT/"State"/"MissingIntegrationsPhase2"
TOKEN_FILE=STATE/"adapter-token.txt"
HELPER=Path(r"D:\Velvet\Runtime\CreativeTools\MissingIntegrationsPhase2\Invoke-AcrobatInspect.ps1")
PORT=6787

def load_token():
    v=TOKEN_FILE.read_text(encoding="utf-8").strip()
    if len(v)<32: raise RuntimeError("adapter token missing or too short")
    return v

def safe_pdf(value):
    p=Path(value).resolve()
    try: p.relative_to(ROOT)
    except ValueError as e: raise RuntimeError("PDF must stay under D:\\Velvet") from e
    if p.suffix.lower()!=".pdf" or not p.is_file(): raise RuntimeError("valid PDF input required")
    return p

def probe():
    return {"status":"PASS","app":"acrobat","progid":"AcroExch.PDDoc","automation":"official_com"}

def inspect_pdf(spec):
    if not isinstance(spec,dict): raise RuntimeError("spec must be an object")
    pdf=safe_pdf(spec.get("input"))
    tmp=ROOT/"Tmp"/"creative-tools"/"missing-integrations-phase2"
    tmp.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".json",dir=tmp,delete=False) as f:
        out=Path(f.name)
    try:
        cp=subprocess.run(["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-File",str(HELPER),"-PdfPath",str(pdf),"-OutPath",str(out)],capture_output=True,text=True,timeout=45,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        if cp.returncode!=0: raise RuntimeError(cp.stderr.strip() or f"PowerShell exit {cp.returncode}")
        obj=json.loads(out.read_text(encoding="utf-8-sig"))
        if obj.get("status")!="PASS": raise RuntimeError(obj.get("error","Acrobat inspect failed"))
        obj["app"]="acrobat"; obj["automation"]="official_com"
        return obj
    finally:
        out.unlink(missing_ok=True)

class Server(HTTPServer):
    allow_reuse_address=False
    def __init__(self,addr,handler,token): self.token=token; super().__init__(addr,handler)

class Handler(BaseHTTPRequestHandler):
    server_version="VelvetAcrobatSafe/0.1.0"
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
            if self.path=="/inspect": result=inspect_pdf(self.body())
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
        with urlopen(req,timeout=60) as r: obj=json.loads(r.read().decode())
    except HTTPError as e: obj=json.loads(e.read().decode())
    except URLError as e: obj={"status":"FAIL","error":str(e)}
    print(json.dumps(obj,separators=(",",":"),ensure_ascii=False)); return 0 if obj.get("status")=="PASS" else 1

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("action",choices=["serve","probe","status","inspect"]); ap.add_argument("--spec")
    a=ap.parse_args()
    if a.action=="serve": serve(); return 0
    spec=json.loads(Path(a.spec).read_text(encoding="utf-8")) if a.spec else None
    return client(a.action,spec)

if __name__=="__main__": sys.exit(main())
