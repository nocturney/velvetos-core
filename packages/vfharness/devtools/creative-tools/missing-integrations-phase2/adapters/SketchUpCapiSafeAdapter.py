import argparse, ctypes, hashlib, json, os, re, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT=Path(r"D:\Velvet").resolve()
STATE=ROOT/"State"/"MissingIntegrationsPhase2"
TOKEN_FILE=STATE/"adapter-token.txt"
TMP=ROOT/"Tmp"/"creative-tools"/"missing-integrations-phase2"
OUTPUT=ROOT/"Output"/"CreativeCraft"/"SketchUpCAPI"
SU_ROOT=Path(r"C:\Program Files\SketchUp\SketchUp 2026\SketchUp")
LO_ROOT=Path(r"C:\Program Files\SketchUp\SketchUp 2026\LayOut")
PORT=6783
MM_PER_INCH=25.4

class Ref(ctypes.Structure):
    _fields_=[("ptr",ctypes.c_void_p)]
class Point3D(ctypes.Structure):
    _fields_=[("x",ctypes.c_double),("y",ctypes.c_double),("z",ctypes.c_double)]
class BoundingBox3D(ctypes.Structure):
    _fields_=[("min_point",Point3D),("max_point",Point3D)]
def load_token():
    v=TOKEN_FILE.read_text(encoding="utf-8").strip()
    if len(v)<32: raise RuntimeError("adapter token missing or too short")
    return v

def slug(v):
    s=str(v or "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}",s): raise RuntimeError("invalid job_id")
    return s

def dim_mm(v,name):
    try: n=float(v)
    except Exception as e: raise RuntimeError(f"{name} must be numeric") from e
    if not (0.1 <= n <= 100000.0): raise RuntimeError(f"{name} out of range")
    return n

def safe_skp(v):
    p=Path(v).resolve()
    try: p.relative_to(ROOT)
    except ValueError as e: raise RuntimeError("input must stay under D:\\Velvet") from e
    if p.suffix.lower()!=".skp" or not p.is_file(): raise RuntimeError("input must be an existing .skp")
    return p

def safe_layout(v):
    p=Path(v).resolve()
    try: p.relative_to(ROOT)
    except ValueError as e: raise RuntimeError("input must stay under D:\\Velvet") from e
    if p.suffix.lower()!=".layout" or not p.is_file(): raise RuntimeError("input must be an existing .layout")
    return p

def file_info(path):
    p=Path(path); data=p.read_bytes()
    if not data: raise RuntimeError("empty output")
    return {"path":str(p),"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest().upper()}
class SketchUpApi:
    def __init__(self):
        os.add_dll_directory(str(SU_ROOT))
        self.dll=ctypes.WinDLL(str(SU_ROOT/"SketchUpAPI.dll"))
        self.bind()
    def f(self,name,args,ret=ctypes.c_int):
        fn=getattr(self.dll,name); fn.argtypes=args; fn.restype=ret; return fn
    def bind(self):
        self.init=self.f("SUInitialize",[],None); self.term=self.f("SUTerminate",[],None)
        self.version=self.f("SUGetAPIVersion",[ctypes.POINTER(ctypes.c_size_t),ctypes.POINTER(ctypes.c_size_t)],None)
        self.model_create=self.f("SUModelCreate",[ctypes.POINTER(Ref)])
        self.model_open=self.f("SUModelCreateFromFileWithStatus",[ctypes.POINTER(Ref),ctypes.c_char_p,ctypes.POINTER(ctypes.c_int)])
        self.model_entities=self.f("SUModelGetEntities",[Ref,ctypes.POINTER(Ref)])
        self.model_save=self.f("SUModelSaveToFile",[Ref,ctypes.c_char_p])
        self.model_release=self.f("SUModelRelease",[ctypes.POINTER(Ref)])
        self.get_faces=self.f("SUEntitiesGetNumFaces",[Ref,ctypes.POINTER(ctypes.c_size_t)])
        self.get_bbox=self.f("SUEntitiesGetBoundingBox",[Ref,ctypes.POINTER(BoundingBox3D)])
        self.geom_create=self.f("SUGeometryInputCreate",[ctypes.POINTER(Ref)])
        self.geom_vertices=self.f("SUGeometryInputSetVertices",[Ref,ctypes.c_size_t,ctypes.POINTER(Point3D)])
        self.geom_face=self.f("SUGeometryInputAddFace",[Ref,ctypes.POINTER(Ref),ctypes.POINTER(ctypes.c_size_t)])
        self.geom_release=self.f("SUGeometryInputRelease",[ctypes.POINTER(Ref)])
        self.loop_create=self.f("SULoopInputCreate",[ctypes.POINTER(Ref)])
        self.loop_vertex=self.f("SULoopInputAddVertexIndex",[Ref,ctypes.c_size_t])
        self.fill=self.f("SUEntitiesFill",[Ref,Ref,ctypes.c_bool])
    def check(self,rc,label):
        if rc!=0: raise RuntimeError(f"{label} failed: SUResult={rc}")
    def api_version(self):
        major=ctypes.c_size_t(); minor=ctypes.c_size_t()
        self.version(ctypes.byref(major),ctypes.byref(minor))
        return f"{major.value}.{minor.value}"
    def inspect(self,path):
        model=Ref(None)
        try:
            status=ctypes.c_int()
            self.check(self.model_open(ctypes.byref(model),str(path).encode("utf-8"),ctypes.byref(status)),"open")
            entities=Ref(None); self.check(self.model_entities(model,ctypes.byref(entities)),"entities")
            faces=ctypes.c_size_t(); self.check(self.get_faces(entities,ctypes.byref(faces)),"face_count")
            box=BoundingBox3D(); self.check(self.get_bbox(entities,ctypes.byref(box)),"bounding_box")
            ext=[(box.max_point.x-box.min_point.x)*MM_PER_INCH,
                 (box.max_point.y-box.min_point.y)*MM_PER_INCH,
                 (box.max_point.z-box.min_point.z)*MM_PER_INCH]
            return {"faces":faces.value,"load_status":status.value,"bounds_mm":[round(x,6) for x in ext]}
        finally:
            if model.ptr: self.model_release(ctypes.byref(model))
    def create_box(self,spec,out_dir):
        if not isinstance(spec,dict): raise RuntimeError("spec must be an object")
        job=slug(spec.get("job_id"))
        dims=[dim_mm(spec.get(k),k) for k in ("x_mm","y_mm","z_mm")]
        out_dir.mkdir(parents=True,exist_ok=True); out=out_dir/f"{job}.skp"
        if out.exists(): raise RuntimeError("refusing to overwrite existing output")
        x,y,z=[v/MM_PER_INCH for v in dims]
        pts=(Point3D*8)(Point3D(0,0,0),Point3D(x,0,0),Point3D(x,y,0),Point3D(0,y,0),
                        Point3D(0,0,z),Point3D(x,0,z),Point3D(x,y,z),Point3D(0,y,z))
        faces=((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))
        model=Ref(None); geom=Ref(None)
        try:
            self.check(self.model_create(ctypes.byref(model)),"model_create")
            entities=Ref(None); self.check(self.model_entities(model,ctypes.byref(entities)),"entities")
            self.check(self.geom_create(ctypes.byref(geom)),"geometry_create")
            self.check(self.geom_vertices(geom,8,pts),"set_vertices")
            for indexes in faces:
                loop=Ref(None); self.check(self.loop_create(ctypes.byref(loop)),"loop_create")
                for idx in indexes: self.check(self.loop_vertex(loop,idx),"loop_vertex")
                face_index=ctypes.c_size_t()
                self.check(self.geom_face(geom,ctypes.byref(loop),ctypes.byref(face_index)),"add_face")
            self.check(self.fill(entities,geom,True),"entities_fill")
            self.check(self.geom_release(ctypes.byref(geom)),"geometry_release")
            self.check(self.model_save(model,str(out).encode("utf-8")),"save")
        except Exception:
            out.unlink(missing_ok=True); raise
        finally:
            if geom.ptr: self.geom_release(ctypes.byref(geom))
            if model.ptr: self.model_release(ctypes.byref(model))
        check=self.inspect(out)
        if check["faces"]!=6: out.unlink(missing_ok=True); raise RuntimeError("box verification failed")
        return {"status":"PASS","app":"sketchup-capi","job_id":job,"dimensions_mm":dims,
                "verification":check,"artifact":file_info(out)}
class LayoutApi:
    def __init__(self):
        os.add_dll_directory(str(LO_ROOT))
        self.pdflib=ctypes.WinDLL(str(LO_ROOT/"pdflib.dll"))
        self.controllers=ctypes.WinDLL(str(LO_ROOT/"LayOutControllers.dll"))
        self.dll=ctypes.WinDLL(str(LO_ROOT/"LayOutAPI.dll")); self.bind()
    def f(self,name,args,ret=ctypes.c_int):
        fn=getattr(self.dll,name); fn.argtypes=args; fn.restype=ret; return fn
    def bind(self):
        self.init=self.f("LOInitialize",[],None); self.term=self.f("LOTerminate",[],None)
        self.create=self.f("LODocumentCreateEmpty",[ctypes.POINTER(Ref)])
        self.open=self.f("LODocumentCreateFromFile",[ctypes.POINTER(Ref),ctypes.c_char_p])
        self.save=self.f("LODocumentSaveToFile",[Ref,ctypes.c_char_p,ctypes.c_int])
        self.export_pdf=self.f("LODocumentExportToPDF",[Ref,ctypes.c_char_p,Ref])
        self.release=self.f("LODocumentRelease",[ctypes.POINTER(Ref)])
    def create_empty(self,spec,out_dir):
        job=slug(spec.get("job_id")); out_dir.mkdir(parents=True,exist_ok=True); out=out_dir/f"{job}.layout"
        if out.exists(): raise RuntimeError("refusing to overwrite existing output")
        doc=Ref(None)
        try:
            rc=self.create(ctypes.byref(doc))
            if rc!=0: raise RuntimeError(f"layout create failed: SUResult={rc}")
            rc=self.save(doc,str(out).encode("utf-8"),23)
            if rc!=0: raise RuntimeError(f"layout save failed: SUResult={rc}")
        except Exception:
            out.unlink(missing_ok=True); raise
        finally:
            if doc.ptr: self.release(ctypes.byref(doc))
        return {"status":"PASS","app":"layout-capi","job_id":job,"artifact":file_info(out)}
    def export_existing(self,spec,out_dir):
        if not isinstance(spec,dict): raise RuntimeError("spec must be an object")
        job=slug(spec.get("job_id")); src=safe_layout(spec.get("input"))
        out_dir.mkdir(parents=True,exist_ok=True); out=out_dir/f"{job}.pdf"
        if out.exists(): raise RuntimeError("refusing to overwrite existing output")
        doc=Ref(None)
        try:
            rc=self.open(ctypes.byref(doc),str(src).encode("utf-8"))
            if rc!=0: raise RuntimeError(f"layout open failed: SUResult={rc}")
            rc=self.export_pdf(doc,str(out).encode("utf-8"),Ref(None))
            if rc!=0: raise RuntimeError(f"layout pdf export failed: SUResult={rc}")
        except Exception:
            out.unlink(missing_ok=True); raise
        finally:
            if doc.ptr: self.release(ctypes.byref(doc))
        return {"status":"PASS","app":"layout-capi","job_id":job,"source":str(src),"artifact":file_info(out)}
SU=SketchUpApi(); LO=LayoutApi()

def probe():
    model=Ref(None)
    try:
        SU.check(SU.model_create(ctypes.byref(model)),"probe_model_create")
        return {"status":"PASS","app":"sketchup-layout-capi","sketchup_api":SU.api_version(),
                "automation":"official_c_api","sketchup_exe_required":False,
                "layout_create":True,"layout_pdf_export":True}
    finally:
        if model.ptr: SU.model_release(ctypes.byref(model))

def acceptance():
    TMP.mkdir(parents=True,exist_ok=True)
    for p in (TMP/"sketchup-capi-acceptance.skp",TMP/"layout-capi-acceptance.layout",TMP/"layout-capi-acceptance.pdf"):
        p.unlink(missing_ok=True)
    box=SU.create_box({"job_id":"sketchup-capi-acceptance","x_mm":10,"y_mm":20,"z_mm":30},TMP)
    layout=LO.create_empty({"job_id":"layout-capi-acceptance"},TMP)
    pdf=LO.export_existing({"job_id":"layout-capi-acceptance","input":layout["artifact"]["path"]},TMP)
    return {"status":"PASS","app":"sketchup-layout-capi","sketchup":box,"layout":layout,"layout_pdf":pdf}

class Server(HTTPServer):
    allow_reuse_address=False
    def __init__(self,addr,handler,token): self.token=token; super().__init__(addr,handler)
class Handler(BaseHTTPRequestHandler):
    server_version="VelvetSketchUpCapiSafe/0.1.0"
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
            elif self.path=="/create_box": result=SU.create_box(self.body(),OUTPUT)
            elif self.path=="/inspect":
                p=safe_skp(self.body().get("input")); result={"status":"PASS","app":"sketchup-capi","input":str(p),**SU.inspect(p)}
            elif self.path=="/create_layout": result=LO.create_empty(self.body(),OUTPUT)
            elif self.path=="/export_layout_pdf": result=LO.export_existing(self.body(),OUTPUT)
            else: return self.reply(404,{"status":"FAIL","error":"not_found"})
            self.reply(200,result)
        except Exception as e: self.reply(500,{"status":"FAIL","error":str(e)})
def serve():
    SU.init(); LO.init()
    s=Server(("127.0.0.1",PORT),Handler,load_token())
    try: s.serve_forever(poll_interval=.5)
    finally:
        s.server_close(); LO.term(); SU.term()

def client(action,spec=None):
    method="GET" if action in ("probe","status") else "POST"
    data=None if method=="GET" else json.dumps(spec or {}).encode()
    req=Request(f"http://127.0.0.1:{PORT}/{action}",method=method,data=data,
                headers={"Authorization":f"Bearer {load_token()}","Content-Type":"application/json"})
    try:
        with urlopen(req,timeout=190) as r: obj=json.loads(r.read().decode())
    except HTTPError as e: obj=json.loads(e.read().decode())
    except URLError as e: obj={"status":"FAIL","error":str(e)}
    print(json.dumps(obj,separators=(",",":"),ensure_ascii=False))
    return 0 if obj.get("status")=="PASS" else 1

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("action",choices=["serve","probe","status","acceptance","create_box","inspect","create_layout","export_layout_pdf"])
    ap.add_argument("--spec"); a=ap.parse_args()
    if a.action=="serve": serve(); return 0
    spec=json.loads(Path(a.spec).read_text(encoding="utf-8")) if a.spec else None
    return client(a.action,spec)

if __name__=="__main__": sys.exit(main())
