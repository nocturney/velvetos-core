import json
import sys
import DaVinciResolveScript as dvr

resolve = dvr.scriptapp("Resolve")
if not resolve:
    print(json.dumps({"status":"ALREADY_STOPPED"}))
    sys.exit(0)

ok = bool(resolve.Quit())
print(json.dumps({"status":"QUIT_REQUESTED","accepted":ok}))
sys.exit(0 if ok else 2)
