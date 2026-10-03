import argparse, ctypes, hashlib, json, os, re, subprocess, sys, time, traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pythoncom
import win32com.client
from pywinauto import Desktop
import pyautogui

ROOT=Path(r"D:\Velvet").resolve()
STATE=ROOT/"State"/"MissingIntegrationsPhase2"
TOKEN_FILE=STATE/"adapter-token.txt"
TMP=ROOT/"Tmp"/"creative-tools"/"missing-integrations-phase2"
OUTPUT=ROOT/"Output"/"CreativeCraft"/"XVL"
XVL_EXE=Path(r"C:\Program Files\Lattice\XVLStudio3DCADCorelEdition27\xvlstudio2_E.exe")
OFFICIAL_SAMPLE=Path(r"C:\Program Files\Lattice\XVLStudio3DCADCorelEdition27\Samples\Model\DigitalCamera_from_CAD.xv2")
DESIGNER_PROGID="CorelDESIGNER.Application.27"
PORT=6789
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
    if p.suffix.lower()!=".xv2" or not p.is_file(): raise RuntimeError("input must be an existing .xv2 file")
    return p

def process_rows(name):
    ps=f"$r=@(Get-Process '{name}' -ErrorAction SilentlyContinue|Select-Object Id,SessionId,StartTime,MainWindowTitle); $r|ConvertTo-Json -Depth 4"
    cp=subprocess.run(["powershell.exe","-NoProfile","-Command",ps],capture_output=True,text=True,timeout=15,
                      creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    raw=cp.stdout.strip()
    if not raw: return []
    obj=json.loads(raw)
    return obj if isinstance(obj,list) else [obj]

def file_info(path,prefix=None):
    p=Path(path)
    deadline=time.time()+10; last=None; stable=0
    while time.time()<deadline:
        if p.is_file():
            st=p.stat(); sig=(st.st_size,st.st_mtime_ns)
            if st.st_size>0 and sig==last:
                stable+=1
                if stable>=3: break
            else: stable=0
            last=sig
        time.sleep(.25)
    if not p.is_file() or p.stat().st_size<=0: raise RuntimeError("artifact missing or empty")
    data=p.read_bytes()
    if prefix and not data.startswith(prefix): raise RuntimeError("artifact has unexpected format")
    return {"path":str(p),"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest().upper()}
def wait_uia_window(pid,timeout=30):
    deadline=time.time()+timeout
    while time.time()<deadline:
        d=Desktop(backend="uia")
        for w in d.windows():
            try:
                if w.element_info.process_id==pid and "XVL Studio" in w.window_text() and w.is_visible():
                    return w
            except Exception: pass
        time.sleep(.4)
    raise TimeoutError("XVL Studio window did not become ready")

def wait_win32_dialog(pid,title,timeout=30):
    deadline=time.time()+timeout
    while time.time()<deadline:
        d=Desktop(backend="win32")
        for w in d.windows():
            try:
                if w.process_id()==pid and w.window_text()==title and w.is_visible():
                    return w
            except Exception: pass
        time.sleep(.3)
    raise TimeoutError(f"dialog did not appear: {title}")

def wait_designer_pid(timeout=30):
    deadline=time.time()+timeout
    while time.time()<deadline:
        rows=process_rows("Designer")
        if rows: return int(rows[0]["Id"])
        time.sleep(.4)
    raise TimeoutError("Corel DESIGNER did not start")

def terminate_pid(pid):
    if not pid: return
    subprocess.run(["powershell.exe","-NoProfile","-Command",
                    f"Stop-Process -Id {int(pid)} -Force -ErrorAction SilentlyContinue"],
                   capture_output=True,text=True,timeout=10,
                   creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
def transfer_to_designer(spec,out_dir,input_override=None):
    if not isinstance(spec,dict): raise RuntimeError("spec must be an object")
    job=slug(spec.get("job_id"))
    src=Path(input_override).resolve() if input_override else safe_input(spec.get("input"))
    outputs=spec.get("outputs",["cdr","pdf"])
    if not isinstance(outputs,list) or not outputs or any(x not in ("cdr","pdf") for x in outputs):
        raise RuntimeError("outputs may contain only cdr and pdf")
    outputs=list(dict.fromkeys(outputs))
    if process_rows("xvlstudio2_E"): raise RuntimeError("refusing because a pre-existing XVL Studio process is running")
    if process_rows("Designer"): raise RuntimeError("refusing because a pre-existing Corel DESIGNER process is running")
    out_dir.mkdir(parents=True,exist_ok=True)
    targets={ext:out_dir/f"{job}.{ext}" for ext in outputs}
    for p in targets.values():
        if p.exists(): raise RuntimeError(f"refusing to overwrite existing output: {p}")
    xvl_proc=None; designer_pid=None; app=None; doc=None; created=[]
    stage="launch_xvl"
    try:
        xvl_proc=subprocess.Popen([str(XVL_EXE),str(src)],
                                  creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        top=wait_uia_window(xvl_proc.pid,30)
        time.sleep(2)
        stage="open_file_menu"
        top.set_focus()
        menuitems=top.descendants(control_type="MenuItem")
        files=[c for c in menuitems if c.window_text()=="File"]
        if not files: raise RuntimeError("File menu not found")
        files[0].click_input(); time.sleep(.7)
        stage="send_to_designer_menu"
        menuitems=top.descendants(control_type="MenuItem")
        send_items=[c for c in menuitems if c.window_text()=="Send to Corel DESIGNER..."]
        if not send_items: raise RuntimeError("Send to Corel DESIGNER menu item not found")
        send_items[0].click_input()
        stage="send_dialog"
        dlg=wait_win32_dialog(xvl_proc.pid,"Send to Corel DESIGNER",20)
        buttons=[c for c in dlg.children() if c.class_name()=="Button" and c.window_text()=="Send..."]
        if not buttons: raise RuntimeError("Send button not found")
        buttons[0].click_input()
        try:
            ctypes.windll.user32.ShowWindow(int(top.handle),0)
        except Exception: pass
        stage="wait_designer"
        designer_pid=wait_designer_pid(30)
        stage="import_svg"
        import_dlg=wait_win32_dialog(designer_pid,"Import SVG File",30)
        oks=[c for c in import_dlg.children() if c.class_name()=="Button" and c.window_text()=="OK"]
        if not oks: raise RuntimeError("Import SVG OK button not found")
        oks[0].click_input()
        time.sleep(3)
        stage="designer_com"
        pythoncom.CoInitialize()
        try:
            app=win32com.client.Dispatch(DESIGNER_PROGID)
            # Corel DESIGNER is single-instance here; Dispatch must not create another PID.
            pids=[int(x["Id"]) for x in process_rows("Designer")]
            if designer_pid not in pids or len(pids)!=1:
                raise RuntimeError("unexpected Corel DESIGNER process set after COM attach")
            deadline=time.time()+20
            while time.time()<deadline:
                if int(app.Documents.Count)==1 and int(app.ActiveDocument.ActivePage.Shapes.Count)>0: break
                time.sleep(.5)
            if int(app.Documents.Count)!=1: raise RuntimeError("expected one Designer document")
            doc=app.ActiveDocument
            shape_count=int(doc.ActivePage.Shapes.Count)
            if shape_count<1: raise RuntimeError("XVL transfer produced no vector shapes")
            app.Visible=False
            shape=doc.ActivePage.Shapes.Item(1)
            readback={"pages":int(doc.Pages.Count),"shapes":shape_count,
                      "shape_name":str(shape.Name),"shape_type":int(shape.Type),
                      "width":float(shape.SizeWidth),"height":float(shape.SizeHeight)}
            if "cdr" in targets:
                stage="save_cdr"
                doc.SaveAsCopy(str(targets["cdr"]),app.CreateStructSaveAsOptions())
                created.append(targets["cdr"])
            if "pdf" in targets:
                stage="publish_pdf"
                doc.PublishToPDF(str(targets["pdf"]))
                created.append(targets["pdf"])
            artifacts={}
            if "cdr" in targets: artifacts["cdr"]=file_info(targets["cdr"])
            if "pdf" in targets: artifacts["pdf"]=file_info(targets["pdf"],b"%PDF-")
            return {"status":"PASS","app":"xvl-studio-corel-gui","job_id":job,
                    "automation":"official_gui_workflow_plus_corel_com",
                    "source":str(src),"readback":readback,"artifacts":artifacts,
                    "xvl_sdk_api":False}
        finally:
            if doc is not None:
                try: doc.Dirty=False; doc.Close()
                except Exception: pass
                doc=None
            if app is not None:
                try: app.Quit()
                except Exception: pass
                app=None
            pythoncom.CoUninitialize()
    except Exception as e:
        for p in created:
            try: Path(p).unlink(missing_ok=True)
            except Exception: pass
        for p in targets.values():
            try: p.unlink(missing_ok=True)
            except Exception: pass
        raise RuntimeError(f"{stage}: {e}") from e
    finally:
        if designer_pid:
            for row in process_rows("Designer"):
                if int(row["Id"])==designer_pid: terminate_pid(designer_pid)
        if xvl_proc is not None:
            try:
                if xvl_proc.poll() is None:
                    xvl_proc.terminate()
                    try: xvl_proc.wait(timeout=3)
                    except Exception: xvl_proc.kill()
            except Exception: terminate_pid(xvl_proc.pid)
def probe():
    return {"status":"PASS","app":"xvl-studio-corel-gui",
            "automation":"official_gui_workflow_plus_corel_com",
            "xvl_exe":str(XVL_EXE),"xvl_exe_exists":XVL_EXE.is_file(),
            "designer_progid":DESIGNER_PROGID,
            "input_types":[".xv2"],"outputs":["cdr","pdf"],
            "xvl_sdk_api":False,"direct_2d_pdf":False,
            "limited_capability":True}

def acceptance():
    TMP.mkdir(parents=True,exist_ok=True)
    for ext in ("cdr","pdf"):
        (TMP/f"xvl-corel-acceptance.{ext}").unlink(missing_ok=True)
    return transfer_to_designer({"job_id":"xvl-corel-acceptance","outputs":["cdr","pdf"]},
                                TMP,input_override=OFFICIAL_SAMPLE)

class Server(HTTPServer):
    allow_reuse_address=False
    def __init__(self,addr,handler,token): self.token=token; super().__init__(addr,handler)

class Handler(BaseHTTPRequestHandler):
    server_version="VelvetXVLCorelSafe/0.1.0"
    def log_message(self,*args): return
    def reply(self,code,obj):
        raw=json.dumps(obj,separators=(",",":"),ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
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
            elif self.path=="/illustration_to_designer": result=transfer_to_designer(self.body(),OUTPUT)
            elif self.path=="/shutdown":
                result={"status":"PASS","app":"xvl-studio-corel-gui","state":"SHUTTING_DOWN"}
                import threading; threading.Thread(target=self.server.shutdown,daemon=True).start()
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
        with urlopen(req,timeout=300) as r: obj=json.loads(r.read().decode())
    except HTTPError as e: obj=json.loads(e.read().decode())
    except URLError as e: obj={"status":"FAIL","error":str(e)}
    print(json.dumps(obj,separators=(",",":"),ensure_ascii=False))
    return 0 if obj.get("status")=="PASS" else 1

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("action",choices=["serve","probe","status","acceptance","illustration_to_designer","shutdown"])
    ap.add_argument("--spec")
    a=ap.parse_args()
    if a.action=="serve": serve(); return 0
    spec=json.loads(Path(a.spec).read_text(encoding="utf-8")) if a.spec else None
    return client(a.action,spec)
if __name__=="__main__": sys.exit(main())
