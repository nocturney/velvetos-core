import argparse, hashlib, json, os, re, shutil, subprocess, sys, threading, time, uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT=Path(r"D:\Velvet").resolve()
STATE=ROOT/"State"/"MissingIntegrationsPhase2"
TOKEN_FILE=STATE/"adapter-token.txt"
TMP=ROOT/"Tmp"/"creative-tools"/"missing-integrations-phase2"
OUTPUT=ROOT/"Output"/"CreativeCraft"/"MediaEncoder"
JOBS=ROOT/"AME"/"Jobs"
STAGING=ROOT/"AME"/"Staging"
AME_EXE=Path(r"C:\Program Files\Adobe\Adobe Media Encoder 2026\Adobe Media Encoder.exe")
FFMPEG=ROOT/"Tools"/"Shared"/"ffmpeg"/"current"/"bin"/"ffmpeg.exe"
FFPROBE=ROOT/"Tools"/"Shared"/"ffmpeg"/"current"/"bin"/"ffprobe.exe"
PORT=6788
PRESETS={
    "h264-high":{
        "watch":ROOT/"AME"/"Watch"/"h264-high",
        "output":ROOT/"AME"/"Watch"/"h264-high"/"Output",
        "archive":ROOT/"AME"/"Watch"/"h264-high"/"Source",
        "extension":".mp4",
        "video_codec":"h264",
        "label":"H.264 / Match Source - High bitrate",
    }
}
ALLOWED_EXTS={
    ".mp4",".mov",".mxf",".avi",".mkv",".m4v",".mpg",".mpeg",
    ".wav",".aif",".aiff",".mp3",".m4a"
}

def load_token():
    v=TOKEN_FILE.read_text(encoding="utf-8").strip()
    if len(v)<32: raise RuntimeError("adapter token missing or too short")
    return v
def slug(v):
    s=str(v or "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}",s):
        raise RuntimeError("invalid job_id")
    return s

def safe_input(v):
    p=Path(v).resolve()
    try: p.relative_to(ROOT)
    except ValueError as e: raise RuntimeError("input must stay under D:\\Velvet") from e
    if p.suffix.lower() not in ALLOWED_EXTS: raise RuntimeError("unsupported input extension")
    if not p.is_file(): raise RuntimeError("input file missing")
    return p

def preset(v):
    key=str(v or "h264-high")
    if key not in PRESETS: raise RuntimeError("unknown preset_id")
    cfg=PRESETS[key]
    for k in ("watch","output","archive"):
        if not cfg[k].is_dir(): raise RuntimeError(f"watch folder not ready: {cfg[k]}")
    return key,cfg
def file_info(path):
    p=Path(path); data=p.read_bytes()
    if not data: raise RuntimeError("empty artifact")
    return {"path":str(p),"bytes":len(data),
            "sha256":hashlib.sha256(data).hexdigest().upper()}

def atomic_json(path,obj):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding="utf-8")
    os.replace(tmp,p)

def ame_running():
    cp=subprocess.run(
        ["tasklist","/FI","IMAGENAME eq Adobe Media Encoder.exe","/FO","CSV","/NH"],
        capture_output=True,text=True,timeout=10,
        creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    return "Adobe Media Encoder.exe" in cp.stdout
def run_ffprobe(path):
    cp=subprocess.run(
        [str(FFPROBE),"-v","error","-print_format","json",
         "-show_format","-show_streams",str(path)],
        capture_output=True,text=True,timeout=30,
        creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    if cp.returncode!=0: raise RuntimeError(cp.stderr.strip() or "ffprobe failed")
    obj=json.loads(cp.stdout)
    streams=obj.get("streams") or []
    video=next((s for s in streams if s.get("codec_type")=="video"),None)
    audio=next((s for s in streams if s.get("codec_type")=="audio"),None)
    fmt=obj.get("format") or {}
    return {
        "format":fmt.get("format_name"),
        "duration":float(fmt.get("duration") or 0),
        "video_codec":video.get("codec_name") if video else None,
        "width":video.get("width") if video else None,
        "height":video.get("height") if video else None,
        "frame_rate":video.get("avg_frame_rate") if video else None,
        "audio_codec":audio.get("codec_name") if audio else None,
    }
def wait_stable(path,timeout):
    deadline=time.time()+timeout
    last=None; stable=0
    while time.time()<deadline:
        p=Path(path)
        if p.is_file():
            st=p.stat(); now=(st.st_size,st.st_mtime_ns)
            if st.st_size>0 and now==last:
                stable+=1
                if stable>=2:
                    try:
                        with p.open("rb") as f: f.read(1)
                        return p
                    except OSError:
                        pass
            else:
                stable=0
            last=now
        time.sleep(1)
    raise TimeoutError("watch folder output timed out")

def cleanup_archived(name,timeout=6):
    removed=[]
    cfg=PRESETS["h264-high"]
    deadline=time.time()+timeout
    while time.time()<deadline:
        matches=[p for p in cfg["archive"].rglob(name) if p.is_file()]
        if matches:
            for p in matches:
                p.unlink(missing_ok=True); removed.append(str(p))
                parent=p.parent
                try:
                    if parent!=cfg["archive"] and not any(parent.iterdir()): parent.rmdir()
                except OSError: pass
            break
        time.sleep(.5)
    return removed

def write_manifest(job,obj):
    atomic_json(JOBS/job/"job.json",obj)
def encode(spec):
    if not isinstance(spec,dict): raise RuntimeError("spec must be an object")
    job=slug(spec.get("job_id"))
    src=safe_input(spec.get("input"))
    preset_id,cfg=preset(spec.get("preset_id"))
    try: timeout=int(spec.get("timeout_seconds",900))
    except Exception as e: raise RuntimeError("timeout_seconds must be an integer") from e
    if not 10<=timeout<=3600: raise RuntimeError("timeout_seconds out of range")
    if not ame_running(): raise RuntimeError("Adobe Media Encoder is not running")
    final=OUTPUT/f"{job}{cfg['extension']}"
    expected=cfg["output"]/f"{job}{cfg['extension']}"
    submitted=cfg["watch"]/f"{job}{src.suffix.lower()}"
    stage_dir=STAGING/job; stage=stage_dir/f"{job}{src.suffix.lower()}"
    manifest_path=JOBS/job/"job.json"
    if final.exists() or expected.exists() or submitted.exists() or manifest_path.exists():
        raise RuntimeError("refusing duplicate or overwrite for job_id")
    stage_dir.mkdir(parents=True,exist_ok=False)
    OUTPUT.mkdir(parents=True,exist_ok=True)
    src_hash=hashlib.sha256(src.read_bytes()).hexdigest().upper()
    shutil.copy2(src,stage)
    stage_hash=hashlib.sha256(stage.read_bytes()).hexdigest().upper()
    if stage_hash!=src_hash: raise RuntimeError("staging hash mismatch")
    manifest={
        "job_id":job,"preset_id":preset_id,"state":"STAGED",
        "source":str(src),"source_sha256":src_hash,
        "staged":str(stage),"submitted":str(submitted),
        "watch_output":str(expected),"final":str(final),
        "created_at":time.time()
    }
    write_manifest(job,manifest)
    os.replace(stage,submitted)
    manifest["state"]="SUBMITTED"; manifest["submitted_at"]=time.time()
    write_manifest(job,manifest)
    try:
        ready=wait_stable(expected,timeout)
        meta=run_ffprobe(ready)
        if meta["duration"]<=0: raise RuntimeError("invalid output duration")
        if cfg.get("video_codec") and meta["video_codec"]!=cfg["video_codec"]:
            raise RuntimeError("unexpected video codec")
        watch_info=file_info(ready)
        tmp_final=final.with_suffix(final.suffix+".partial")
        tmp_final.unlink(missing_ok=True)
        shutil.copy2(ready,tmp_final)
        os.replace(tmp_final,final)
        artifact=file_info(final)
        ready.unlink(missing_ok=True)
        archived=cleanup_archived(submitted.name)
        manifest.update({"state":"SUCCEEDED","completed_at":time.time(),
                         "validation":meta,"artifact":artifact,
                         "watch_output":watch_info,
                         "cleanup":{"watch_output_removed":not ready.exists(),
                                    "archived_source_removed":archived}})
        write_manifest(job,manifest)
        shutil.rmtree(stage_dir,ignore_errors=True)
        return {"status":"PASS","app":"media-encoder","automation":"official_watch_folder",
                "job_id":job,"preset_id":preset_id,"validation":meta,
                "artifact":artifact,"watch_output":watch_info,
                "cleanup":manifest["cleanup"]}
    except Exception as e:
        submitted.unlink(missing_ok=True); expected.unlink(missing_ok=True)
        cleanup_archived(submitted.name,2)
        shutil.rmtree(stage_dir,ignore_errors=True)
        manifest["state"]="TIMED_OUT" if isinstance(e,TimeoutError) else "FAILED"
        manifest["error"]=str(e); manifest["failed_at"]=time.time()
        write_manifest(job,manifest)
        raise
def job_status(spec):
    if not isinstance(spec,dict): raise RuntimeError("spec must be an object")
    job=slug(spec.get("job_id"))
    p=JOBS/job/"job.json"
    if not p.is_file(): raise RuntimeError("job not found")
    obj=json.loads(p.read_text(encoding="utf-8"))
    return {"status":"PASS","app":"media-encoder","job":obj}

def probe():
    presets={}
    for key,cfg in PRESETS.items():
        presets[key]={
            "ready":all(cfg[k].is_dir() for k in ("watch","output","archive")),
            "watch":str(cfg["watch"]),"output":str(cfg["output"]),
            "label":cfg["label"],"expected_extension":cfg["extension"]
        }
    return {"status":"PASS","app":"media-encoder",
            "automation":"official_watch_folder","ame_exe":str(AME_EXE),
            "ame_running":ame_running(),"presets":presets,
            "remote_ame_api":False,"uxp_available_for_installed_version":False}
def acceptance():
    TMP.mkdir(parents=True,exist_ok=True)
    job="ame-watch-"+uuid.uuid4().hex[:12]
    fixture=TMP/f"{job}-input.mp4"
    cp=subprocess.run([
        str(FFMPEG),"-hide_banner","-loglevel","error",
        "-f","lavfi","-i","testsrc2=size=320x180:rate=24",
        "-f","lavfi","-i","sine=frequency=1000:sample_rate=48000",
        "-t","2","-c:v","libx264","-pix_fmt","yuv420p",
        "-c:a","aac","-y",str(fixture)],
        capture_output=True,text=True,timeout=60,
        creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    if cp.returncode!=0: raise RuntimeError(cp.stderr.strip() or "fixture generation failed")
    try:
        return encode({"job_id":job,"input":str(fixture),
                       "preset_id":"h264-high","timeout_seconds":120})
    finally:
        fixture.unlink(missing_ok=True)
class Server(HTTPServer):
    allow_reuse_address=False
    def __init__(self,addr,handler,token):
        self.token=token; super().__init__(addr,handler)

class Handler(BaseHTTPRequestHandler):
    server_version="VelvetMediaEncoderWatchSafe/0.1.0"
    def log_message(self,*args): return
    def reply(self,code,obj):
        raw=json.dumps(obj,separators=(",",":"),ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(raw))); self.end_headers()
        self.wfile.write(raw)
    def auth(self):
        return self.headers.get("Authorization","")==f"Bearer {self.server.token}"
    def body(self):
        n=int(self.headers.get("Content-Length","0") or 0)
        if n>131072: raise RuntimeError("request too large")
        return json.loads(self.rfile.read(n).decode() or "{}")
    def do_GET(self):
        if not self.auth(): return self.reply(401,{"status":"FAIL","error":"unauthorized"})
        try:
            if self.path in ("/probe","/status"): return self.reply(200,probe())
            return self.reply(404,{"status":"FAIL","error":"not_found"})
        except Exception as e:
            self.reply(500,{"status":"FAIL","error":str(e)})
    def do_POST(self):
        if not self.auth(): return self.reply(401,{"status":"FAIL","error":"unauthorized"})
        try:
            if self.path=="/acceptance": result=acceptance()
            elif self.path=="/encode": result=encode(self.body())
            elif self.path=="/job_status": result=job_status(self.body())
            elif self.path=="/shutdown":
                result={"status":"PASS","app":"media-encoder","state":"SHUTTING_DOWN"}
                threading.Thread(target=self.server.shutdown,daemon=True).start()
            else: return self.reply(404,{"status":"FAIL","error":"not_found"})
            self.reply(200,result)
        except Exception as e:
            self.reply(500,{"status":"FAIL","error":str(e)})
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
        with urlopen(req,timeout=3700) as r: obj=json.loads(r.read().decode())
    except HTTPError as e: obj=json.loads(e.read().decode())
    except URLError as e: obj={"status":"FAIL","error":str(e)}
    print(json.dumps(obj,separators=(",",":"),ensure_ascii=False))
    return 0 if obj.get("status")=="PASS" else 1
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("action",choices=[
        "serve","probe","status","acceptance","encode","job_status","shutdown"])
    ap.add_argument("--spec")
    a=ap.parse_args()
    if a.action=="serve":
        serve(); return 0
    spec=json.loads(Path(a.spec).read_text(encoding="utf-8")) if a.spec else None
    return client(a.action,spec)

if __name__=="__main__":
    sys.exit(main())
