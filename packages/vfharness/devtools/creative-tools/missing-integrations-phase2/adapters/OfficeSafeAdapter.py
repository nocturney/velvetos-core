import argparse, json, re, subprocess, sys, threading, time, uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT=Path(r"D:\Velvet").resolve()
STATE=ROOT/"State"/"MissingIntegrationsPhase2"
TOKEN_FILE=STATE/"adapter-token.txt"
TMP=ROOT/"Tmp"/"creative-tools"/"missing-integrations-phase2"
TASKS={
    "word_document":("VelvetOS Phase2 Candidate office-word",STATE/"office-word-request.json",STATE/"office-word-response.json"),
    "excel_table":("VelvetOS Phase2 Candidate office-excel",STATE/"office-excel-request.json",STATE/"office-excel-response.json"),
    "powerpoint_deck":("VelvetOS Phase2 Candidate office-powerpoint",STATE/"office-powerpoint-request.json",STATE/"office-powerpoint-response.json"),
}
WORD_INPUTS={
    "job_id":STATE/"office-word-job.txt",
    "title":STATE/"office-word-title.txt",
    "body":STATE/"office-word-body.txt",
    "target":STATE/"office-word-target.txt",
}
PORT=6786
LOCK=threading.Lock()
PS_FLAGS=getattr(subprocess,"CREATE_NO_WINDOW",0)

def ps(script,timeout=40):
    cp=subprocess.run(["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-Command",script],capture_output=True,text=True,timeout=timeout,creationflags=PS_FLAGS)
    if cp.returncode!=0: raise RuntimeError((cp.stderr or cp.stdout or f"PowerShell exit {cp.returncode}").strip())
    return cp.stdout.strip()

def load_token():
    v=TOKEN_FILE.read_text(encoding="utf-8").strip()
    if len(v)<32: raise RuntimeError("adapter token missing or too short")
    return v

def slug(v):
    s=str(v or "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}",s): raise RuntimeError("invalid job_id")
    return s

def service_snapshot():
    raw=ps("$s=Get-CimInstance Win32_Service -Filter \"Name='ClickToRunSvc'\"; [pscustomobject]@{State=$s.State;StartMode=$s.StartMode}|ConvertTo-Json -Compress")
    return json.loads(raw)

def prepare_service(original):
    if original.get("State")=="Running": return
    if original.get("StartMode")=="Disabled":
        ps("Set-Service -Name ClickToRunSvc -StartupType Manual")
    ps("Start-Service -Name ClickToRunSvc; $s=Get-CimInstance Win32_Service -Filter \"Name='ClickToRunSvc'\"; if($s.State -ne 'Running'){throw 'ClickToRunSvc did not reach Running'}")

def restore_service(original):
    if original.get("State")!="Running":
        ps("Stop-Service -Name ClickToRunSvc -Force -ErrorAction SilentlyContinue")
    mode=original.get("StartMode")
    if mode=="Disabled": ps("Set-Service -Name ClickToRunSvc -StartupType Disabled")
    elif mode=="Manual": ps("Set-Service -Name ClickToRunSvc -StartupType Manual")
    elif mode=="Auto": ps("Set-Service -Name ClickToRunSvc -StartupType Automatic")

def office_process_count():
    raw=ps("@(Get-Process WINWORD,EXCEL,POWERPNT -ErrorAction SilentlyContinue).Count")
    try: return int(raw or "0")
    except ValueError: return 0

def cleanup_owned_office(started_epoch):
    cut=max(0,int(started_epoch)-2)
    script=f"$cut=[DateTimeOffset]::FromUnixTimeSeconds({cut}).UtcDateTime; Get-Process WINWORD,EXCEL,POWERPNT -ErrorAction SilentlyContinue|Where-Object{{$_.MainWindowHandle -eq 0 -and $_.StartTime.ToUniversalTime() -ge $cut}}|Stop-Process -Force -ErrorAction SilentlyContinue"
    ps(script)

def validate_word(spec):
    job=slug(spec.get("job_id")); title=str(spec.get("title","")).strip(); body=str(spec.get("body","")).strip()
    if not 1<=len(title)<=500: raise RuntimeError("title must contain 1..500 characters")
    if not 1<=len(body)<=19000: raise RuntimeError("body must contain 1..19000 characters")
    return {"action":"word_document","job_id":job,"title":title,"body":body,"target":spec.get("_target","production")}

def validate_excel(spec):
    job=slug(spec.get("job_id")); rows=spec.get("rows")
    if not isinstance(rows,list) or not 1<=len(rows)<=200: raise RuntimeError("rows must contain 1..200 rows")
    clean=[]; total=0
    for ri,row in enumerate(rows):
        if not isinstance(row,list) or len(row)>50: raise RuntimeError(f"row {ri} must be a list of at most 50 cells")
        cr=[]
        for cell in row:
            if cell is None or isinstance(cell,(bool,int,float)): cr.append(cell)
            elif isinstance(cell,str) and len(cell)<=1000: cr.append(cell)
            else: raise RuntimeError("cells must be scalar values; strings max 1000 characters")
        total+=len(cr); clean.append(cr)
    if total>5000: raise RuntimeError("table exceeds 5000 cells")
    return {"action":"excel_table","job_id":job,"rows":clean,"target":spec.get("_target","production")}

def validate_powerpoint(spec):
    job=slug(spec.get("job_id")); slides=spec.get("slides")
    if not isinstance(slides,list) or not 1<=len(slides)<=50: raise RuntimeError("slides must contain 1..50 slides")
    clean=[]
    for i,s in enumerate(slides):
        if not isinstance(s,dict): raise RuntimeError(f"slide {i} must be an object")
        title=str(s.get("title","")).strip(); body=str(s.get("body","")).strip()
        if not 1<=len(title)<=500: raise RuntimeError(f"slide {i} title invalid")
        if len(body)>4000: raise RuntimeError(f"slide {i} body too long")
        clean.append({"title":title,"body":body})
    return {"action":"powerpoint_deck","job_id":job,"slides":clean,"target":spec.get("_target","production")}

def run_scheduled_task(spec,timeout=150):
    action=spec.get("action")
    if action not in TASKS: raise RuntimeError("unsupported Office action")
    task,req,resp=TASKS[action]
    STATE.mkdir(parents=True,exist_ok=True)
    resp.unlink(missing_ok=True); req.unlink(missing_ok=True)
    if action=="word_document":
        for key,path in WORD_INPUTS.items():
            path.unlink(missing_ok=True)
            path.write_text(str(spec.get(key,"")),encoding="utf-8")
    else:
        req.write_text(json.dumps(spec,ensure_ascii=False),encoding="utf-8")
    try:
        cp=subprocess.run(["schtasks.exe","/Run","/TN",task],capture_output=True,text=True,timeout=10,creationflags=PS_FLAGS)
        if cp.returncode!=0: raise RuntimeError((cp.stderr or cp.stdout or "failed to start Office task").strip())
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline and not resp.is_file(): time.sleep(.25)
        if not resp.is_file():
            subprocess.run(["schtasks.exe","/End","/TN",task],capture_output=True,text=True,creationflags=PS_FLAGS,timeout=10)
            raise RuntimeError(f"{action} task response timeout")
        obj=json.loads(resp.read_text(encoding="utf-8-sig"))
        if obj.get("status")!="PASS": raise RuntimeError(obj.get("error",f"{action} worker failed"))
        return obj
    finally:
        if action=="word_document":
            for path in WORD_INPUTS.values(): path.unlink(missing_ok=True)
        else:
            req.unlink(missing_ok=True)
        resp.unlink(missing_ok=True)

def run_worker(spec,timeout=150):
    with LOCK:
        if office_process_count()!=0: raise RuntimeError("refusing to run while a pre-existing Office process is present")
        original=service_snapshot()
        started=time.time()
        failed=False
        try:
            prepare_service(original)
            return run_scheduled_task(spec,timeout)
        except Exception:
            failed=True
            raise
        finally:
            try: cleanup_owned_office(started)
            except Exception: pass
            try: restore_service(original)
            except Exception as e:
                if not failed: raise RuntimeError(f"Office job completed but service restore failed: {e}")

def probe():
    raw=ps("$c=Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Office\\ClickToRun\\Configuration' -ErrorAction Stop; $s=Get-CimInstance Win32_Service -Filter \"Name='ClickToRunSvc'\"; [pscustomobject]@{Product=$c.ProductReleaseIds;Build=$c.ClientVersionToReport;Platform=$c.Platform;ServiceState=$s.State;ServiceStartMode=$s.StartMode}|ConvertTo-Json -Compress")
    info=json.loads(raw)
    return {"status":"PASS","app":"office","automation":"official_com_via_typed_powershell","installed":info}

def acceptance():
    jobs=[
      ("word",validate_word({"job_id":"office-adapter-word-acceptance","title":"VelvetOS Phase 2","body":"Word typed adapter acceptance","_target":"tmp"})),
      ("excel",validate_excel({"job_id":"office-adapter-excel-acceptance","rows":[["VelvetOS Phase 2",123],["Excel typed adapter",True]],"_target":"tmp"})),
      ("powerpoint",validate_powerpoint({"job_id":"office-adapter-powerpoint-acceptance","slides":[{"title":"VelvetOS Phase 2","body":"PowerPoint typed adapter acceptance"}],"_target":"tmp"}))
    ]
    exts={"word":["docx","pdf"],"excel":["xlsx","pdf"],"powerpoint":["pptx","pdf"]}
    for name,s in jobs:
        for ext in exts[name]: (TMP/f"{s['job_id']}.{ext}").unlink(missing_ok=True)
    results={}
    for name,s in jobs: results[name]=run_worker(s)
    return {"status":"PASS","app":"office","results":results,"post_service":service_snapshot()}

class Server(HTTPServer):
    allow_reuse_address=False
    def __init__(self,addr,handler,token): self.token=token; super().__init__(addr,handler)

class Handler(BaseHTTPRequestHandler):
    server_version="VelvetOfficeSafe/0.1.0"
    def log_message(self,*args): return
    def reply(self,code,obj):
        raw=json.dumps(obj,separators=(",",":"),ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def auth(self): return self.headers.get("Authorization","")==f"Bearer {self.server.token}"
    def body(self):
        n=int(self.headers.get("Content-Length","0") or 0)
        if n>524288: raise RuntimeError("request too large")
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
            body=self.body()
            if self.path=="/acceptance": result=acceptance()
            elif self.path=="/word_document": result=run_worker(validate_word(body))
            elif self.path=="/excel_table": result=run_worker(validate_excel(body))
            elif self.path=="/powerpoint_deck": result=run_worker(validate_powerpoint(body))
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
        with urlopen(req,timeout=500) as r: obj=json.loads(r.read().decode())
    except HTTPError as e: obj=json.loads(e.read().decode())
    except URLError as e: obj={"status":"FAIL","error":str(e)}
    print(json.dumps(obj,separators=(",",":"),ensure_ascii=False)); return 0 if obj.get("status")=="PASS" else 1

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("action",choices=["serve","probe","status","acceptance","word_document","excel_table","powerpoint_deck"]); ap.add_argument("--spec")
    a=ap.parse_args()
    if a.action=="serve": serve(); return 0
    spec=json.loads(Path(a.spec).read_text(encoding="utf-8")) if a.spec else None
    return client(a.action,spec)

if __name__=="__main__": sys.exit(main())
