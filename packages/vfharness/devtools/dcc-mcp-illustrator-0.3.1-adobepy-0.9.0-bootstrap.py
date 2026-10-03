from pathlib import Path
import hashlib, json, os, time
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
        "hostVersion": "30.8.2",
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
hold = os.environ.get("VELVET_ILLUSTRATOR_HOLD") == "1"
lease_state = Path(r"D:\Velvet\State\AdobeBridge\illustrator-lease.json")

def write_lease_state(payload):
    tmp = Path(str(lease_state) + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    tmp.replace(lease_state)

try:
    result = client.bootstrap_illustrator_cep(request)
    verified = client.verify_illustrator_bootstrap(result.continuation)
    if verified != result:
        raise RuntimeError("Illustrator bootstrap continuation mismatch")
    summary = {
        "ok": True,
        "bootstrap_status": result.status,
        "continuation_match": True,
        "identity_fingerprint": result.identity_fingerprint,
        "broker": {"pid": result.broker.pid, "version": result.broker.runtime_version},
        "host": {"pid": result.host.pid, "version": result.host.host_version,
                 "profile_id": result.host.profile_id},
        "plugin": {"target": result.plugin.target,
                   "bridge_version": result.plugin.bridge_version},
        "continuation": {"path": result.continuation.path,
                         "receipt_id": result.continuation.receipt_id},
        "adapter_argv": list(result.adapter_continuation.argv),
    }
    print(json.dumps(summary), flush=True)
    if hold:
        from adobe.illustrator import Illustrator
        expected_pid = int(result.host.pid)
        while True:
            sessions = [
                row for row in client.capabilities()
                if row.get("target", "default") == "default"
                and row.get("capabilities", {}).get("host") == "illustrator"
                and row.get("capabilities", {}).get("bridgeKind") == "cep"
            ]
            if len(sessions) != 1:
                raise RuntimeError("Illustrator lease lost its unique CEP session")
            app_version = str(Illustrator(client=client).version)
            identity = client.runtime_identity("illustrator", target="default").to_wire()
            if int(identity["host"]["pid"]) != expected_pid:
                raise RuntimeError("Illustrator lease host PID changed")
            if app_version != result.host.host_version:
                raise RuntimeError("Illustrator lease host version changed")
            write_lease_state({
                "schema": "velvetos.illustrator-lease.v1",
                "status": "ready",
                "lease_pid": os.getpid(),
                "host_pid": expected_pid,
                "broker_pid": int(identity["broker"]["pid"]),
                "host_version": app_version,
                "target": "default",
                "last_heartbeat_epoch_ms": int(time.time() * 1000),
            })
            time.sleep(1)
except Exception as exc:
    message = str(exc).replace(token, "<redacted>")
    if hold:
        try:
            write_lease_state({
                "schema": "velvetos.illustrator-lease.v1",
                "status": "error",
                "lease_pid": os.getpid(),
                "error_type": type(exc).__name__,
                "message": message,
                "last_heartbeat_epoch_ms": int(time.time() * 1000),
            })
        except Exception:
            pass
    print(json.dumps({"ok": False, "error_type": type(exc).__name__, "message": message}), flush=True)
    if hold:
        raise SystemExit(2)
