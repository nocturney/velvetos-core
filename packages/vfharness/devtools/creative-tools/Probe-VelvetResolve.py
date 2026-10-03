import json
import DaVinciResolveScript as dvr

resolve = dvr.scriptapp("Resolve")
if not resolve:
    raise RuntimeError("scriptapp('Resolve') returned None")

pm = resolve.GetProjectManager()
project = pm.GetCurrentProject() if pm else None
timeline = project.GetCurrentTimeline() if project else None

print(json.dumps({
    "status": "PASS",
    "ok": True,
    "product": resolve.GetProductName(),
    "version": resolve.GetVersionString(),
    "version_fields": resolve.GetVersion(),
    "page": resolve.GetCurrentPage(),
    "project": project.GetName() if project else None,
    "timeline": timeline.GetName() if timeline else None,
}, ensure_ascii=True))
