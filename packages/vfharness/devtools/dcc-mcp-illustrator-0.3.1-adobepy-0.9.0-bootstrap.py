from pathlib import Path
import hashlib, json, os
from adobe.core import BrokerClient, IllustratorBootstrapRequest

host = Path(r"C:\Program Files\Adobe\Adobe Illustrator 2026\Support Files\Contents\Windows\Illustrator.exe")
root = Path(r"C:\Users\Chris\AppData\Roaming\Adobe\CEP\extensions\com.adobepy.bridge.illustrator")
manifest = root / "CSXS" / "manifest.xml"
index = root / "index.html"
module = root / "dist" / "main.js"

def ident(path):
    data = path.read_bytes()
    return len(data), hashlib.sha256(data).hexdigest()

host_bytes, host_sha = ident(host)
manifest_bytes, manifest_sha = ident(manifest)
index_bytes, index_sha = ident(index)
module_bytes, module_sha = ident(module)
request = IllustratorBootstrapRequest.from_mapping({
    "bootstrapVersion": 1,
    "target": "default",
    "timeoutMs": 30000,
    "host": {
        "executablePath": str(host),
        "executableBytes": host_bytes,
        "executableSha256": host_sha,
        "hostVersion": "30.8.1",
        "profileId": "dcc-mcp-illustrator-default",
    },
    "plugin": {
        "installedPluginRoot": str(root),
        "moduleOrigin": str(module),
        "bridgeVersion": "0.1.0",
        "manifestBytes": manifest_bytes,
        "manifestSha256": manifest_sha,
        "indexBytes": index_bytes,
        "indexSha256": index_sha,
        "moduleBytes": module_bytes,
        "moduleSha256": module_sha,
    },
})
token = Path(r"D:\Velvet\State\AdobeBridge\adobepy-token.txt").read_text(encoding="utf-8").strip()
client = BrokerClient(
    broker_url="http://127.0.0.1:47391",
    token=token,
    target="default",
    timeout=35.0,
)
try:
    result = client.bootstrap_illustrator_cep(request)
    verified = client.verify_illustrator_bootstrap(result.continuation)
    print(json.dumps({
        "ok": True,
        "bootstrap_status": result.status,
        "continuation_match": verified == result,
        "identity_fingerprint": result.identity_fingerprint,
        "broker": {"pid": result.broker.pid, "version": result.broker.runtime_version},
        "host": {"pid": result.host.pid, "version": result.host.host_version,
                 "profile_id": result.host.profile_id},
        "plugin": {"target": result.plugin.target,
                   "bridge_version": result.plugin.bridge_version},
        "continuation": {"path": result.continuation.path,
                         "receipt_id": result.continuation.receipt_id},
        "adapter_argv": list(result.adapter_continuation.argv),
    }))
except Exception as exc:
    message = str(exc).replace(token, "<redacted>")
    print(json.dumps({"ok": False, "error_type": type(exc).__name__, "message": message}))
