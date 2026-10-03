import argparse, hashlib, json, re, subprocess, sys, tempfile, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT=Path(r"D:\Velvet").resolve()
STATE=ROOT/"State"/"MissingIntegrationsPhase2"
TOKEN_FILE=STATE/"adapter-token.txt"
TMP=ROOT/"Tmp"/"creative-tools"/"missing-integrations-phase2"
OUTPUT=ROOT/"Output"/"CreativeCraft"/"FusionStudio"
FUSCRIPT=Path(r"C:\Program Files\Blackmagic Design\Fusion 21\fuscript.exe")
PORT=6784

def load_token():
    v=TOKEN_FILE.read_text(encoding="utf-8").strip()
    if len(v)<32: raise RuntimeError("adapter token missing or too short")
    return v

def slug(v):
    v=str(v or "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}",v): raise RuntimeError("invalid job_id")
    return v

def bounded_float(v,name,lo=0.0,hi=1.0):
    x=float(v)
    if x<lo or x>hi: raise RuntimeError(f"{name} outside allowed range")
    return x

def bounded_int(v,name,lo,hi):
    x=int(v)
    if x<lo or x>hi: raise RuntimeError(f"{name} outside allowed range")
    return x

def file_info(path):
    p=Path(path)
    deadline=time.monotonic()+15
    last=None; stable=0
    while time.monotonic()<deadline:
        if p.is_file():
            s=p.stat(); mark=(s.st_size,s.st_mtime_ns)
            stable=stable+1 if s.st_size>0 and mark==last else 0; last=mark
            if stable>=3: break
        time.sleep(.2)
    data=p.read_bytes()
    return {"path":str(p),"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest().upper()}

def lua_path(s):
    return str(s).replace("\\","\\\\").replace("]]","] ]")

def run_lua(source, timeout=90):
    TMP.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile("w",suffix=".lua",prefix="fusion_phase2_",dir=TMP,delete=False,encoding="utf-8") as f:
        f.write(source); script=Path(f.name)
    try:
        cp=subprocess.run([str(FUSCRIPT),str(script)],capture_output=True,text=True,timeout=timeout,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        if cp.returncode!=0: raise RuntimeError(f"fuscript exit {cp.returncode}: {cp.stderr.strip() or cp.stdout.strip()}")
    finally:
        script.unlink(missing_ok=True)

def probe():
    report=TMP/"fusion-adapter-probe.txt"; report.unlink(missing_ok=True)
    run_lua(f'''local f=io.open([[{lua_path(report)}]],"w")
local ok,err=pcall(function()
 local fu=Fusion(); if fu==nil then error("Fusion() returned nil") end
 local a=fu:GetAttrs()
 f:write("PASS\\n"..tostring(a.FUSIONS_Version or a.FUSIONS_VersionString or "").."\\n")
end)
if not ok then f:write("FAIL\\n"..tostring(err).."\\n") end
f:close()''',30)
    lines=report.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0]!="PASS": raise RuntimeError(lines[1] if len(lines)>1 else "Fusion probe failed")
    return {"status":"PASS","app":"fusion-studio","version":lines[1] if len(lines)>1 else "","automation":"official_fuscript"}

def render_solid(spec,out_dir):
    if not isinstance(spec,dict): raise RuntimeError("spec must be an object")
    job=slug(spec.get("job_id"))
    width=bounded_int(spec.get("width",1920),"width",16,16384)
    height=bounded_int(spec.get("height",1080),"height",16,16384)
    rgba=spec.get("rgba",[0,0,0,1])
    if not isinstance(rgba,list) or len(rgba)!=4: raise RuntimeError("rgba must contain 4 numbers")
    r,g,b,a=[bounded_float(v,"rgba") for v in rgba]
    out_dir.mkdir(parents=True,exist_ok=True)
    comp=out_dir/f"{job}.comp"; base=out_dir/f"{job}.png"; frame=out_dir/f"{job}0000.png"; report=TMP/f"{job}-fusion-report.txt"
    for q in (comp,base,frame,report):
        if q.exists(): raise RuntimeError(f"refusing to overwrite existing output: {q}")
    src=f'''local f=io.open([[{lua_path(report)}]],"w")
local ok,err=pcall(function()
 local fu=Fusion(); if fu==nil then error("Fusion() returned nil") end
 local comp=fu:NewComp(); if comp==nil then error("NewComp returned nil") end
 comp:SetAttrs({{COMPN_GlobalStart=0,COMPN_GlobalEnd=0,COMPN_RenderStart=0,COMPN_RenderEnd=0}})
 local bg=comp:AddTool("Background"); local saver=comp:AddTool("Saver")
 if bg==nil or saver==nil then error("tool creation failed") end
 bg.UseFrameFormatSettings[0]=0
 bg.Width[0]={width}; bg.Height[0]={height}
 bg.TopLeftRed[0]={r}; bg.TopLeftGreen[0]={g}; bg.TopLeftBlue[0]={b}; bg.TopLeftAlpha[0]={a}
 bg.TopRightRed[0]={r}; bg.TopRightGreen[0]={g}; bg.TopRightBlue[0]={b}; bg.TopRightAlpha[0]={a}
 bg.BottomLeftRed[0]={r}; bg.BottomLeftGreen[0]={g}; bg.BottomLeftBlue[0]={b}; bg.BottomLeftAlpha[0]={a}
 bg.BottomRightRed[0]={r}; bg.BottomRightGreen[0]={g}; bg.BottomRightBlue[0]={b}; bg.BottomRightAlpha[0]={a}
 saver.Clip[0]=[[{lua_path(base)}]]
 if not saver.Input:ConnectTo(bg.Output) then error("connect failed") end
 if not comp:Save([[{lua_path(comp)}]]) then error("save failed") end
 if not comp:Render({{Start=0,End=0,Wait=true}}) then error("render failed") end
 f:write("PASS\\n")
end)
if not ok then f:write("FAIL\\n"..tostring(err).."\\n") end
f:close()'''
    try:
        run_lua(src,120)
        lines=report.read_text(encoding="utf-8").splitlines()
        if not lines or lines[0]!="PASS": raise RuntimeError(lines[1] if len(lines)>1 else "Fusion render failed")
        if not frame.is_file(): raise RuntimeError("expected Fusion frame output missing")
        return {"status":"PASS","app":"fusion-studio","job_id":job,"readback":{"width":width,"height":height,"rgba":[r,g,b,a]},"artifacts":{"comp":file_info(comp),"png":file_info(frame)}}
    except Exception:
        for q in (comp,base,frame): q.unlink(missing_ok=True)
        raise
    finally:
        report.unlink(missing_ok=True)

def acceptance():
    for q in TMP.glob("fusion-adapter-acceptance*"): q.unlink(missing_ok=True)
    return render_solid({"job_id":"fusion-adapter-acceptance","width":320,"height":180,"rgba":[0.125,0.5,0.75,1]},TMP)

class Server(HTTPServer):
    allow_reuse_address=False
    def __init__(self,addr,handler,token): self.token=token; self.stop=False; super().__init__(addr,handler)

class Handler(BaseHTTPRequestHandler):
    server_version="VelvetFusionSafe/0.1.0"
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
            elif self.path=="/render_solid": result=render_solid(self.body(),OUTPUT)
            elif self.path=="/shutdown": result={"status":"PASS","shutdown":True}; self.server.stop=True
            else: return self.reply(404,{"status":"FAIL","error":"not_found"})
            self.reply(200,result)
        except Exception as e: self.reply(500,{"status":"FAIL","error":str(e)})

def serve():
    server=Server(("127.0.0.1",PORT),Handler,load_token()); server.timeout=.5
    try:
        while not server.stop: server.handle_request()
    finally: server.server_close()

def client(action,spec=None):
    method="GET" if action in ("probe","status") else "POST"
    data=None if method=="GET" else json.dumps(spec or {}).encode()
    req=Request(f"http://127.0.0.1:{PORT}/{action}",method=method,data=data,headers={"Authorization":f"Bearer {load_token()}","Content-Type":"application/json"})
    try:
        with urlopen(req,timeout=140) as r: obj=json.loads(r.read().decode())
    except HTTPError as e: obj=json.loads(e.read().decode())
    except URLError as e: obj={"status":"FAIL","error":str(e)}
    print(json.dumps(obj,separators=(",",":"),ensure_ascii=False)); return 0 if obj.get("status")=="PASS" else 1

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("action",choices=["serve","probe","status","acceptance","render_solid","shutdown"]); ap.add_argument("--spec")
    a=ap.parse_args()
    if a.action=="serve": serve(); return 0
    spec=json.loads(Path(a.spec).read_text(encoding="utf-8")) if a.spec else None
    return client(a.action,spec)

if __name__=="__main__": sys.exit(main())
