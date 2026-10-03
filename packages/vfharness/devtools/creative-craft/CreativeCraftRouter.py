import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(r"D:\Velvet")
RUNTIME = ROOT / "Runtime" / "CreativeCraft"
DEFAULT_REGISTRY = RUNTIME / "creative-craft-registry.json"
DEFAULT_ROUTING = ROOT / "State" / "DCC-Adobe-Update-Sentinel" / "routing-state.json"
DEFAULT_CANDIDATE_MATRIX = ROOT / "State" / "CreativeCraft" / "missing-integrations-phase2-candidate-matrix.json"
DEFAULT_AUTHORITY_ROOTS = ROOT / "State" / "CreativeCraft" / "authority-roots.json"
HOST_MANAGER = ROOT / "Runtime" / "Autostart" / "Invoke-VelvetDccHost.ps1"
VALID_PRINTER_KEYS = {"h2d", "u1", "ecc2", "c5", "c5pro"}
HOST_MANIFEST = ROOT / "Runtime" / "Autostart" / "dcc-desktop-hosts.json"
COREL_TOKEN = ROOT / "State" / "Corel" / "corel-adapter-token.txt"
LOG_ROOT = ROOT / "Logs" / "CreativeCraft" / "jobs"
OUTPUT_ROOT = ROOT / "Output" / "CreativeCraft"
FUSION_SCRIPTS = ROOT / "Tools" / "CreativeTools" / "FusionProvider" / "0.1.0" / "skill" / "scripts"
FUSION_EXPORT_ROOT = ROOT / "Tmp" / "creative-tools" / "fusion-provider"
MESHMIXER_ADAPTER = ROOT / "Tools" / "CreativeTools" / "Meshmixer" / "adapter-0.1.0" / "VelvetMeshmixerAdapter.exe"
TOPAZ_ADAPTER = ROOT / "Runtime" / "CreativeTools" / "TopazVideo" / "TopazVideoSafeAdapter.py"
COREL_PORTS = {"coreldraw": 6771, "corel-designer": 6772}


def emit(payload, exit_code=0):
    print(json.dumps(payload, ensure_ascii=True, separators=(",", ":")))
    return exit_code


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def registry(path=None):
    p = Path(path) if path else DEFAULT_REGISTRY
    data = load_json(p)
    if data.get("schema") != "velvetos.creative-craft.registry.v1":
        raise RuntimeError("unexpected Creative Craft registry schema")
    return data


def routing(path=None):
    p = Path(path) if path else DEFAULT_ROUTING
    data = load_json(p)
    hosts = data.get("hosts")
    if not isinstance(hosts, dict):
        raise RuntimeError("routing-state.json is missing hosts")
    return data


def route_state(tool_id, route_doc=None):
    route_doc = route_doc or routing()
    row = route_doc.get("hosts", {}).get(tool_id)
    if row is None:
        return {"status": "missing", "reason": "tool absent from routing state"}
    return row


def sha256_file(path):
    p = Path(path)
    h = hashlib.sha256()
    with p.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def candidate_matrix(reg):
    path = reg.get("policy", {}).get("candidate_matrix") or str(DEFAULT_CANDIDATE_MATRIX)
    return load_json(path)


def authority_roots(reg):
    path = reg.get("policy", {}).get("authority_roots") or str(DEFAULT_AUTHORITY_ROOTS)
    return load_json(path)


def command_exists(command):
    try:
        proc = subprocess.run(
            ["where.exe", str(command)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return proc.returncode == 0
    except Exception:
        return False


def state_conditions(path, conditions):
    p = Path(path)
    if not p.is_file():
        return False, f"state file missing: {p}"
    try:
        data = load_json(p)
    except Exception as exc:
        return False, f"state file unreadable: {exc}"
    mismatches = []
    for key, expected in (conditions or {}).items():
        actual = data.get(key)
        if actual != expected:
            mismatches.append(f"{key}={actual!r} expected {expected!r}")
    if mismatches:
        return False, "; ".join(mismatches)
    return True, "state conditions satisfied"


def accepted_candidate_hash(row):
    for key in ("runtime_adapter", "adapter", "source_adapter"):
        value = row.get(key)
        if isinstance(value, dict) and value.get("sha256"):
            return str(value["sha256"]).upper()
    return None


def evaluate_availability(gate, reg, route_doc=None):
    gate = gate or {"type": "dcc_routing"}
    kind = gate.get("type")

    if kind == "all":
        details = [evaluate_availability(item, reg, route_doc) for item in gate.get("gates", [])]
        ok = all(item.get("available") for item in details)
        return {
            "available": ok,
            "status": "available" if ok else "blocked",
            "reason": "all availability gates passed" if ok else "one or more availability gates failed",
            "details": details,
        }

    if kind == "dcc_routing":
        route_doc = route_doc or routing(reg.get("policy", {}).get("routing_state"))
        route_key = gate.get("route_key")
        row = route_state(route_key, route_doc)
        required = reg.get("policy", {}).get("required_routing_status", "available")
        ok = row.get("status") == required
        return {
            "available": ok,
            "status": row.get("status"),
            "reason": row.get("reason"),
            "gate": "dcc_routing",
            "route_key": route_key,
        }

    if kind == "candidate_matrix":
        try:
            matrix = candidate_matrix(reg)
            key = gate.get("key")
            row = matrix.get("accepted", {}).get(key)
            if not isinstance(row, dict):
                return {"available": False, "status": "missing", "reason": f"candidate receipt missing: {key}"}
            if row.get("status") != "PASS":
                return {"available": False, "status": row.get("status", "blocked"), "reason": f"candidate not accepted: {key}"}
            runtime_file = gate.get("runtime_file")
            if runtime_file:
                p = Path(runtime_file)
                if not p.is_file():
                    return {"available": False, "status": "missing", "reason": f"accepted runtime adapter missing: {p}"}
                expected = accepted_candidate_hash(row)
                if expected:
                    actual = sha256_file(p)
                    if actual != expected:
                        return {
                            "available": False,
                            "status": "hash_mismatch",
                            "reason": f"runtime adapter hash differs from accepted candidate: {key}",
                            "expected_sha256": expected,
                            "actual_sha256": actual,
                        }
            return {"available": True, "status": "accepted", "reason": f"accepted candidate receipt PASS: {key}", "gate": "candidate_matrix"}
        except Exception as exc:
            return {"available": False, "status": "error", "reason": f"candidate matrix gate failed: {exc}"}

    if kind == "file_exists":
        p = Path(gate.get("path", ""))
        ok = p.is_file()
        return {"available": ok, "status": "available" if ok else "missing", "reason": str(p), "gate": "file_exists"}

    if kind == "command_exists":
        name = gate.get("command")
        ok = command_exists(name)
        return {"available": ok, "status": "available" if ok else "missing", "reason": str(name), "gate": "command_exists"}

    if kind == "state_json":
        ok, reason = state_conditions(gate.get("path"), gate.get("conditions", {}))
        return {"available": ok, "status": "available" if ok else "blocked", "reason": reason, "gate": "state_json"}

    if kind == "authority_files":
        try:
            roots = authority_roots(reg)
            root_key = gate.get("root_key")
            root = Path(roots.get(root_key, "")).resolve()
            missing = []
            mismatched = []
            expected = roots.get("expected_sha256", {})
            for rel in gate.get("relative_paths", []):
                candidate = root / rel
                if not candidate.is_file():
                    missing.append(rel)
                    continue
                accepted_hash = str(expected.get(rel, "")).upper()
                if accepted_hash:
                    actual_hash = sha256_file(candidate)
                    if actual_hash != accepted_hash:
                        mismatched.append({
                            "path": rel,
                            "expected_sha256": accepted_hash,
                            "actual_sha256": actual_hash,
                        })
            ok = bool(str(root)) and not missing and not mismatched
            reason = f"authority root {root}; accepted hashes match"
            if missing:
                reason = f"missing authority files: {missing}"
            elif mismatched:
                reason = "authority hash mismatch"
            return {
                "available": ok,
                "status": "available" if ok else ("hash_mismatch" if mismatched else "missing"),
                "reason": reason,
                "gate": "authority_files",
                "authority_root": str(root),
                "hash_mismatches": mismatched,
            }
        except Exception as exc:
            return {"available": False, "status": "error", "reason": f"authority root gate failed: {exc}"}

    return {"available": False, "status": "unsupported_gate", "reason": f"unsupported availability gate: {kind}"}



def authority_roots(reg):
    path = reg.get("policy", {}).get("authority_roots")
    if not path:
        return {}
    return load_json(path)


def candidate_matrix(reg):
    path = reg.get("policy", {}).get("candidate_matrix")
    if not path:
        return {}
    return load_json(path)


def availability_check(gate, reg, route_doc):
    if not gate:
        return {"available": False, "status": "missing_gate", "reason": "no availability gate configured"}
    kind = gate.get("type")
    if kind == "dcc_routing":
        key = gate.get("route_key")
        row = route_state(key, route_doc)
        required = reg.get("policy", {}).get("required_routing_status", "available")
        return {
            "available": row.get("status") == required,
            "status": row.get("status", "missing"),
            "reason": row.get("reason") or f"DCC routing state for {key}",
            "gate": kind,
        }
    if kind == "candidate_matrix":
        matrix = candidate_matrix(reg)
        key = gate.get("key")
        row = matrix.get("accepted", {}).get(key, {})
        runtime_file = Path(gate.get("runtime_file", ""))
        accepted = row.get("status") == "PASS"
        exists = runtime_file.is_file()
        expected = (row.get("runtime_adapter") or row.get("adapter") or row.get("source_adapter") or {}).get("sha256")
        actual = hashlib.sha256(runtime_file.read_bytes()).hexdigest().upper() if exists else None
        hash_ok = not expected or actual == str(expected).upper()
        ok = bool(accepted and exists and hash_ok)
        return {
            "available": ok,
            "status": "accepted" if ok else "missing_unaccepted_or_hash_mismatch",
            "reason": f"candidate={key} accepted={accepted} runtime_file={exists} hash_ok={hash_ok}",
            "gate": kind,
            "expected_sha256": expected,
            "actual_sha256": actual,
        }
    if kind == "file_exists":
        p = Path(gate.get("path", ""))
        exists = p.is_file()
        return {"available": exists, "status": "present" if exists else "missing", "reason": str(p), "gate": kind}
    if kind == "command_exists":
        command = str(gate.get("command") or "")
        found = shutil.which(command)
        return {"available": bool(found), "status": "present" if found else "missing", "reason": found or command, "gate": kind}
    if kind == "state_json":
        p = Path(gate.get("path", ""))
        if not p.is_file():
            return {"available": False, "status": "missing", "reason": str(p), "gate": kind}
        doc = load_json(p)
        conditions = gate.get("conditions", {})
        failed = {k: {"expected": v, "actual": doc.get(k)} for k, v in conditions.items() if doc.get(k) != v}
        return {
            "available": not failed,
            "status": "verified" if not failed else "state_mismatch",
            "reason": str(p) if not failed else json.dumps(failed, ensure_ascii=False),
            "gate": kind,
        }
    if kind == "authority_files":
        roots = authority_roots(reg)
        root_key = gate.get("root_key")
        root_value = roots.get(root_key)
        if not root_value:
            return {"available": False, "status": "missing_root", "reason": str(root_key), "gate": kind}
        root = Path(root_value)
        rels = gate.get("relative_paths", [])
        missing = [rel for rel in rels if not (root / rel).is_file()]
        expected_hashes = roots.get("sha256", {})
        mismatched = []
        for rel in rels:
            expected = expected_hashes.get(rel)
            fp = root / rel
            if expected and fp.is_file():
                actual = hashlib.sha256(fp.read_bytes()).hexdigest().upper()
                if actual != str(expected).upper():
                    mismatched.append({"path": rel, "expected": expected, "actual": actual})
        ok = not missing and not mismatched
        return {
            "available": ok,
            "status": "present" if ok else ("hash_mismatch" if mismatched else "missing_files"),
            "reason": str(root) if ok else json.dumps({"missing": missing, "mismatched": mismatched}, ensure_ascii=False),
            "gate": kind,
        }
    if kind == "all":
        details = [availability_check(x, reg, route_doc) for x in gate.get("gates", [])]
        ok = bool(details) and all(x.get("available") for x in details)
        return {
            "available": ok,
            "status": "available" if ok else "blocked",
            "reason": "; ".join(f"{x.get('status')}:{x.get('reason')}" for x in details),
            "gate": kind,
            "details": details,
        }
    return {"available": False, "status": "unknown_gate", "reason": str(kind), "gate": kind}


def tool_status(tool_id, reg=None, route_doc=None):
    reg = reg or registry()
    route_doc = route_doc or routing(reg.get("policy", {}).get("routing_state"))
    tool = reg.get("tools", {}).get(tool_id)
    if tool is None:
        raise RuntimeError(f"unknown Creative Craft tool: {tool_id}")
    gate = tool.get("availability") or {"type": "dcc_routing", "route_key": tool_id}
    avail = availability_check(gate, reg, route_doc)
    return {
        "tool": tool_id,
        "display_name": tool.get("display_name"),
        "available": bool(avail.get("available")),
        "routing_status": avail.get("status"),
        "routing_reason": avail.get("reason"),
        "availability_gate": avail.get("gate"),
        "lifecycle": tool.get("lifecycle"),
        "production_surface": tool.get("production_surface"),
        "operations": tool.get("operations", []),
        "blocked": tool.get("blocked", []),
        "readiness": tool.get("readiness"),
        "skills": tool.get("skills", []),
        "typed_gaps": tool.get("typed_gaps", []),
    }


def status_payload(tool_id=None, registry_path=None):
    reg = registry(registry_path)
    route_doc = routing(reg.get("policy", {}).get("routing_state"))
    ids = [tool_id] if tool_id else list(reg.get("tools", {}).keys())
    rows = [tool_status(t, reg, route_doc) for t in ids]
    return {
        "status": "PASS",
        "registry_version": reg.get("version"),
        "tools": rows,
        "all_requested_available": all(x["available"] for x in rows),
        "unavailable": [x["tool"] for x in rows if not x["available"]],
    }


def plan(intent, registry_path=None):
    reg = registry(registry_path)
    pipeline = reg.get("pipelines", {}).get(intent)
    if pipeline is None:
        raise RuntimeError(f"unknown Creative Craft intent: {intent}")
    route_doc = routing(reg.get("policy", {}).get("routing_state"))
    steps = []
    blocked = []
    for index, step in enumerate(pipeline.get("steps", []), start=1):
        state = tool_status(step["tool"], reg, route_doc)
        row = {
            "index": index,
            "tool": step["tool"],
            "purpose": step.get("purpose"),
            "required": bool(step.get("required", True)),
            "available": state["available"],
            "routing_status": state["routing_status"],
            "production_surface": state["production_surface"],
            "readiness": state.get("readiness"),
            "typed_gaps": state.get("typed_gaps", []),
        }
        if row["required"] and not row["available"]:
            blocked.append(step["tool"])
        steps.append(row)
    return {
        "status": "PASS" if not blocked else "BLOCKED",
        "intent": intent,
        "authority": pipeline.get("authority"),
        "skills": pipeline.get("skills", []),
        "readiness": pipeline.get("readiness"),
        "steps": steps,
        "blocked_required_tools": blocked,
        "expected_artifacts": pipeline.get("expected_artifacts", []),
        "qa": pipeline.get("qa"),
        "cleanup_policy": pipeline.get("cleanup_policy"),
        "policy": {
            "fail_closed": bool(reg.get("policy", {}).get("fail_closed", True)),
            "raw_script_execution": bool(reg.get("policy", {}).get("raw_script_execution", False)),
            "stop_agent_launched_hosts": bool(reg.get("policy", {}).get("stop_agent_launched_hosts", True)),
            "printer_network_control": bool(reg.get("policy", {}).get("printer_network_control", False)),
            "auto_publish": bool(reg.get("policy", {}).get("auto_publish", False)),
        },
    }


def route_request(request, registry_path=None):
    request = str(request or "").strip()
    if not request:
        raise RuntimeError("request must not be empty")
    reg = registry(registry_path)
    hay = request.casefold()
    scored = []
    for order, rule in enumerate(reg.get("intent_rules", [])):
        hits = [kw for kw in rule.get("keywords", []) if str(kw).casefold() in hay]
        if hits:
            scored.append((len(hits), -order, rule.get("pipeline"), hits))
    if not scored:
        return {
            "status": "BLOCKED",
            "reason": "no_intent_match",
            "request": request,
            "available_intents": list(reg.get("pipelines", {}).keys()),
        }
    scored.sort(reverse=True)
    _, _, intent, hits = scored[0]
    result = plan(intent, registry_path)
    result["request"] = request
    result["matched_keywords"] = hits
    return result


def host_process_name(tool_id):
    manifest = load_json(HOST_MANIFEST)
    for row in manifest.get("apps", []):
        if row.get("id") == tool_id:
            return str(row.get("process") or "").strip()
    return ""


def process_running(process_name):
    if not process_name:
        return False
    image = process_name if process_name.lower().endswith(".exe") else process_name + ".exe"
    proc = subprocess.run(
        ["tasklist.exe", "/FI", f"IMAGENAME eq {image}", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    out = (proc.stdout or "").strip()
    if not out or out.upper().startswith("INFO:"):
        return False
    return image.lower() in out.lower()


def run_host_manager(action, tool_id, compatibility_probe=False):
    args = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(HOST_MANAGER), "-Action", action, "-AppId", tool_id,
    ]
    if compatibility_probe:
        args.append("-CompatibilityProbe")
    proc = subprocess.run(args, capture_output=True, text=True, timeout=90)
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    parsed = None
    if stdout:
        try:
            parsed = json.loads(stdout)
        except Exception:
            parsed = stdout
    return {
        "exit_code": proc.returncode,
        "output": parsed,
        "stderr": stderr or None,
    }


def host_action(tool_id, action, registry_path=None):
    reg = registry(registry_path)
    state = tool_status(tool_id, reg)
    tool = reg["tools"][tool_id]
    if tool.get("lifecycle") != "dcc-host":
        return {
            "status": "PASS",
            "tool": tool_id,
            "action": action,
            "lifecycle": tool.get("lifecycle"),
            "note": "no DCC host lifecycle action required",
        }
    if action == "start" and not state["available"]:
        return {
            "status": "BLOCKED",
            "tool": tool_id,
            "routing_status": state["routing_status"],
            "reason": state["routing_reason"],
        }
    if (
        action == "start"
        and reg.get("policy", {}).get("preserve_preexisting_user_sessions", True)
        and process_running(host_process_name(tool_id))
    ):
        managed = run_host_manager("status", tool_id)
        managed_output = managed.get("output") if isinstance(managed, dict) else None
        if isinstance(managed_output, dict) and int(managed_output.get("running") or 0) > 0:
            return {
                "status": "PASS",
                "tool": tool_id,
                "action": action,
                "note": "managed_agent_session_already_running",
                "host_manager": managed,
            }
        return {
            "status": "BLOCKED",
            "tool": tool_id,
            "reason": "preexisting_user_session",
        }
    result = run_host_manager(action, tool_id)
    return {
        "status": "PASS" if result["exit_code"] == 0 else "FAIL",
        "tool": tool_id,
        "action": action,
        "host_manager": result,
    }


def safe_path(path, must_exist=False):
    p = Path(path).resolve()
    root = ROOT.resolve()
    try:
        p.relative_to(root)
    except ValueError as exc:
        raise RuntimeError("path must stay under D:\\Velvet") from exc
    if must_exist and not p.is_file():
        raise RuntimeError(f"input file not found: {p}")
    return p


def file_artifact(path):
    p = Path(path)
    data = p.read_bytes()
    return {
        "path": str(p),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest().upper(),
    }


def copy_no_overwrite(source, destination):
    src = Path(source)
    dst = Path(destination)
    if not src.is_file():
        raise RuntimeError(f"source artifact missing: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        raise RuntimeError(f"refusing to overwrite existing output: {dst}")
    dst.write_bytes(src.read_bytes())
    return file_artifact(dst)


def run_json_command(args, stdin_payload=None, timeout=90):
    proc = subprocess.run(
        [str(x) for x in args],
        input=None if stdin_payload is None else json.dumps(stdin_payload, ensure_ascii=False),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    payload = None
    if stdout:
        try:
            payload = json.loads(stdout)
        except Exception:
            lines = [line.strip() for line in stdout.splitlines() if line.strip()]
            for line in reversed(lines):
                try:
                    payload = json.loads(line)
                    break
                except Exception:
                    continue
    if payload is None:
        payload = {"raw_stdout": stdout or None}
    return {
        "exit_code": proc.returncode,
        "payload": payload,
        "stderr": stderr or None,
    }


def corel_request(app_id, path, method="GET", payload=None, timeout=20):
    token = COREL_TOKEN.read_text(encoding="utf-8").strip()
    data = None
    headers = {"Authorization": f"Bearer {token}"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(
        f"http://127.0.0.1:{COREL_PORTS[app_id]}/{path.lstrip('/')}",
        method=method,
        headers=headers,
        data=data,
    )
    try:
        with urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            return json.loads(exc.read().decode("utf-8"))
        except Exception:
            return {"status": "FAIL", "error": f"HTTP {exc.code}"}
    except URLError as exc:
        return {"status": "FAIL", "error": str(exc)}
def wait_corel(app_id, timeout=30):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        last = corel_request(app_id, "status", timeout=2)
        if last.get("status") == "PASS":
            return last
        time.sleep(0.5)
    raise RuntimeError(f"{app_id} safe adapter did not become ready: {last}")


def safe_spec_path(path):
    p = Path(path).resolve()
    root = ROOT.resolve()
    try:
        p.relative_to(root)
    except ValueError as exc:
        raise RuntimeError("Creative Craft spec must be under D:\\Velvet") from exc
    if p.suffix.lower() != ".json" or not p.is_file():
        raise RuntimeError("Creative Craft spec must be an existing .json file")
    return p


def write_job_log(app_id, spec_path, result):
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_name = "".join(c for c in spec_path.stem if c.isalnum() or c in "-_")[:64] or "job"
    path = LOG_ROOT / f"{stamp}-{app_id}-{safe_name}.json"
    record = {
        "schema": "velvetos.creative-craft.job.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "app_id": app_id,
        "spec_path": str(spec_path),
        "result": result,
    }
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)
def corel_craft(app_id, spec_path, registry_path=None):
    if app_id not in COREL_PORTS:
        raise RuntimeError("corel-craft supports only coreldraw or corel-designer")
    reg = registry(registry_path)
    state = tool_status(app_id, reg)
    if not state["available"]:
        return {
            "status": "BLOCKED",
            "app": app_id,
            "routing_status": state["routing_status"],
            "reason": state["routing_reason"],
        }
    spec_path = safe_spec_path(spec_path)
    spec = load_json(spec_path)
    launched = False
    current = corel_request(app_id, "status", timeout=2)
    if current.get("status") != "PASS":
        start = host_action(app_id, "start", registry_path)
        if start.get("status") != "PASS":
            return {"status": "FAIL", "app": app_id, "stage": "start", "detail": start}
        launched = True
        wait_corel(app_id, timeout=30)
    try:
        result = corel_request(app_id, "craft", method="POST", payload=spec, timeout=60)
        log_path = write_job_log(app_id, spec_path, result)
        return {
            "status": result.get("status", "FAIL"),
            "app": app_id,
            "launched_by_router": launched,
            "result": result,
            "job_log": log_path,
        }
    finally:
        if launched and reg.get("policy", {}).get("stop_agent_launched_hosts", True):
            host_action(app_id, "stop", registry_path)
def validate_job_id(value):
    value = str(value or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value):
        raise RuntimeError("job_id must match [A-Za-z0-9_-]{1,64}")
    return value


def wait_command_probe(args, timeout=45):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        last = run_json_command(args, timeout=8)
        if last["exit_code"] == 0:
            return last
        time.sleep(0.75)
    raise RuntimeError(f"tool did not become ready: {last}")



def meshmixer_review(input_path, screenshot_path, registry_path=None):
    reg = registry(registry_path)
    state = tool_status("meshmixer", reg)
    if not state["available"]:
        return {"status": "BLOCKED", "tool": "meshmixer", "reason": state["routing_reason"]}
    inp = safe_path(input_path, must_exist=True)
    shot = safe_path(screenshot_path, must_exist=False)
    if shot.suffix.lower() != ".png":
        raise RuntimeError("Meshmixer screenshot output must be .png")
    if shot.exists():
        raise RuntimeError(f"refusing to overwrite existing screenshot: {shot}")
    if process_running(host_process_name("meshmixer")):
        return {"status": "BLOCKED", "tool": "meshmixer", "reason": "preexisting_user_session"}
    launched = False
    try:
        started = host_action("meshmixer", "start", registry_path)
        if started.get("status") != "PASS":
            return {"status": "FAIL", "tool": "meshmixer", "stage": "start", "detail": started}
        launched = True
        wait_command_probe([MESHMIXER_ADAPTER, "probe"], timeout=45)
        imported = run_json_command([MESHMIXER_ADAPTER, "import", inp], timeout=30)
        if imported["exit_code"] != 0:
            return {"status": "FAIL", "tool": "meshmixer", "stage": "import", "detail": imported}
        ids = imported["payload"].get("object_ids", []) if isinstance(imported["payload"], dict) else []
        details = []
        for obj_id in ids[:20]:
            info = run_json_command([MESHMIXER_ADAPTER, "info", str(obj_id)], timeout=15)
            if info["exit_code"] == 0:
                details.append(info["payload"])
        screenshot = run_json_command([MESHMIXER_ADAPTER, "screenshot", shot], timeout=30)
        if screenshot["exit_code"] != 0 or not shot.is_file():
            return {"status": "FAIL", "tool": "meshmixer", "stage": "screenshot", "detail": screenshot}
        return {
            "status": "PASS",
            "tool": "meshmixer",
            "input": str(inp),
            "objects": details,
            "screenshot": file_artifact(shot),
        }
    finally:
        if launched and reg.get("policy", {}).get("stop_agent_launched_hosts", True):
            host_action("meshmixer", "stop", registry_path)


def mesh_technical_sheet(input_path, job_id, app_id="corel-designer", registry_path=None):
    job_id = validate_job_id(job_id)
    if app_id not in COREL_PORTS:
        raise RuntimeError("technical sheet app must be coreldraw or corel-designer")
    screenshot = OUTPUT_ROOT / "Meshmixer" / f"{job_id}-mesh.png"
    mesh = meshmixer_review(input_path, screenshot, registry_path)
    if mesh.get("status") != "PASS":
        return {
            "status": "FAIL",
            "intent": "mesh-technical-sheet",
            "stage": "meshmixer",
            "meshmixer": mesh,
        }
    first = mesh.get("objects", [{}])[0] if mesh.get("objects") else {}
    vertices = first.get("vertices", "unknown")
    triangles = first.get("triangles", "unknown")
    spec_path = ROOT / "Tmp" / "creative-craft" / f"{job_id}-technical-sheet.json"
    spec = {
        "job_id": job_id,
        "page": {"width_mm": 210, "height_mm": 148},
        "objects": [
            {
                "type": "image",
                "path": str(screenshot),
                "x_mm": 15,
                "y_mm": 125,
                "width_mm": 95,
                "height_mm": 95,
            },
            {
                "type": "text",
                "x_mm": 120,
                "y_mm": 120,
                "text": "MESH REVIEW",
                "font": "Arial",
                "size_pt": 18,
                "bold": True,
                "fill": [20, 20, 20],
            },
            {
                "type": "line",
                "x1_mm": 120,
                "y1_mm": 110,
                "x2_mm": 195,
                "y2_mm": 110,
                "stroke": [32, 95, 224],
            },
            {
                "type": "text",
                "x_mm": 120,
                "y_mm": 98,
                "text": f"Vertices: {vertices} | Triangles: {triangles}",
                "font": "Arial",
                "size_pt": 10,
                "fill": [70, 70, 70],
            },
            {
                "type": "text",
                "x_mm": 120,
                "y_mm": 88,
                "text": "VelvetOS Creative Craft",
                "font": "Arial",
                "size_pt": 9,
                "fill": [90, 90, 90],
            },
        ],
        "outputs": ["cdr", "pdf"],
    }
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    corel = corel_craft(app_id, spec_path, registry_path)
    if corel.get("status") != "PASS":
        return {
            "status": "FAIL",
            "intent": "mesh-technical-sheet",
            "stage": app_id,
            "meshmixer": mesh,
            "corel": corel,
        }
    return {
        "status": "PASS",
        "intent": "mesh-technical-sheet",
        "job_id": job_id,
        "meshmixer": mesh,
        "corel": corel,
        "spec_path": str(spec_path),
    }


def topaz_enhance(input_path, output_path, model="ahq-12", scale=1, registry_path=None):
    reg = registry(registry_path)
    state = tool_status("topaz-video", reg)
    if not state["available"]:
        return {"status": "BLOCKED", "tool": "topaz-video", "reason": state["routing_reason"]}
    inp = safe_path(input_path, must_exist=True)
    out = safe_path(output_path, must_exist=False)
    if out.exists():
        raise RuntimeError(f"refusing to overwrite existing Topaz output: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    result = run_json_command(
        [
            sys.executable,
            TOPAZ_ADAPTER,
            "enhance",
            "--input", inp,
            "--output", out,
            "--model", str(model),
            "--scale", str(scale),
        ],
        timeout=1800,
    )
    if result["exit_code"] != 0 or not out.is_file():
        return {"status": "FAIL", "tool": "topaz-video", "stage": "enhance", "detail": result}
    return {
        "status": "PASS",
        "tool": "topaz-video",
        "model": model,
        "scale": scale,
        "artifact": file_artifact(out),
        "adapter": result["payload"],
    }



def wait_command_ready(args, timeout=45, interval=0.5):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        last = run_json_command(args, timeout=15)
        if last["exit_code"] == 0:
            return last
        time.sleep(interval)
    raise RuntimeError(f"tool did not become ready: {last}")


def write_named_job_log(tool_id, job_id, result):
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    job_id = validate_job_id(job_id)
    path = LOG_ROOT / f"{stamp}-{tool_id}-{job_id}.json"
    record = {
        "schema": "velvetos.creative-craft.job.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "tool_id": tool_id,
        "job_id": job_id,
        "result": result,
    }
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def fusion_box(job_id, width_mm, depth_mm, height_mm, export_format="stl", registry_path=None):
    job_id = validate_job_id(job_id)
    export_format = str(export_format).lower()
    if export_format not in ("stl", "step"):
        raise RuntimeError("export format must be stl or step")
    reg = registry(registry_path)
    state = tool_status("fusion", reg)
    if not state["available"]:
        return {"status": "BLOCKED", "tool": "fusion", "reason": state["routing_reason"]}
    if process_running(host_process_name("fusion")):
        return {"status": "BLOCKED", "tool": "fusion", "reason": "preexisting_user_session"}
    target = OUTPUT_ROOT / "Fusion" / f"{job_id}.{export_format}"
    if target.exists():
        raise RuntimeError(f"refusing to overwrite existing Fusion output: {target}")
    temp_export = FUSION_EXPORT_ROOT / f"{job_id}.{export_format}"
    temp_export.unlink(missing_ok=True)
    launched = False
    try:
        started = host_action("fusion", "start", registry_path)
        if started.get("status") != "PASS":
            return {"status": "FAIL", "tool": "fusion", "stage": "start", "detail": started}
        launched = True
        wait_command_ready([sys.executable, FUSION_SCRIPTS / "status.py"], timeout=120)
        operation = run_json_command(
            [sys.executable, FUSION_SCRIPTS / "create_export_box.py"],
            {
                "width_mm": width_mm,
                "depth_mm": depth_mm,
                "height_mm": height_mm,
                "format": export_format,
                "basename": job_id,
            },
            timeout=120,
        )
        if operation["exit_code"] != 0 or not temp_export.is_file():
            raise RuntimeError(f"atomic Fusion box operation failed: {operation}")
        artifact = copy_no_overwrite(temp_export, target)
        result = {
            "status": "PASS",
            "tool": "fusion",
            "job_id": job_id,
            "dimensions_mm": [float(width_mm), float(depth_mm), float(height_mm)],
            "format": export_format,
            "artifact": artifact,
            "provider": operation["payload"],
        }
        result["job_log"] = write_named_job_log("fusion", job_id, result)
        return result
    finally:
        temp_export.unlink(missing_ok=True)
        if launched and reg.get("policy", {}).get("stop_agent_launched_hosts", True):
            host_action("fusion", "stop", registry_path)


def fabrication_root(reg):
    roots = authority_roots(reg)
    root = Path(roots.get("velvetos_core", "")).resolve()
    required = [
        root / "scripts" / "vf_fabrication_router.py",
        root / "scripts" / "vf_cad.py",
        root / "scripts" / "vf_3d.py",
        root / "packages" / "vfprod" / "FABRICATION-ROUTER.json",
    ]
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise RuntimeError(f"fabrication authority is incomplete: {missing}")
    return root


def fabrication_status(registry_path=None):
    reg = registry(registry_path)
    gate = tool_status("fabrication", reg)
    if not gate["available"]:
        return {"status": "BLOCKED", "tool": "fabrication", "reason": gate["routing_reason"]}
    root = fabrication_root(reg)
    router = root / "scripts" / "vf_fabrication_router.py"
    cad = root / "scripts" / "vf_cad.py"
    checks = {
        "verify": run_json_command([sys.executable, router, "verify"], timeout=90),
        "doctor": run_json_command([sys.executable, router, "doctor"], timeout=90),
        "cad_doctor": run_json_command([sys.executable, cad, "doctor"], timeout=120),
    }
    ok = all(item["exit_code"] == 0 for item in checks.values())
    return {
        "status": "PASS" if ok else "FAIL",
        "tool": "fabrication",
        "authority_root": str(root),
        "checks": checks,
        "printer_network_control": False,
    }


def fabrication_route(request, file_path=None, registry_path=None):
    reg = registry(registry_path)
    state = tool_status("fabrication", reg)
    if not state["available"]:
        return {"status": "BLOCKED", "tool": "fabrication", "reason": state["routing_reason"]}
    root = fabrication_root(reg)
    args = [sys.executable, root / "scripts" / "vf_fabrication_router.py", "decide", "--request", str(request)]
    input_artifact = None
    if file_path:
        inp = safe_path(file_path, must_exist=True)
        args.extend(["--file", inp])
        input_artifact = file_artifact(inp)
    result = run_json_command(args, timeout=90)
    payload = result["payload"]
    if result["exit_code"] != 0:
        return {"status": "FAIL", "tool": "fabrication", "stage": "route", "detail": result}
    if isinstance(payload, dict) and payload.get("printer_actions_allowed") is True:
        return {
            "status": "FAIL",
            "tool": "fabrication",
            "stage": "safety-check",
            "reason": "canonical router unexpectedly allowed physical printer actions",
            "detail": payload,
        }
    return {
        "status": "PASS",
        "tool": "fabrication",
        "authority_root": str(root),
        "input": input_artifact,
        "decision": payload,
        "printer_network_control": False,
    }


def fabrication_dfam(input_path, angle_limit=45.0, registry_path=None):
    reg = registry(registry_path)
    state = tool_status("fabrication", reg)
    if not state["available"]:
        return {"status": "BLOCKED", "tool": "fabrication", "reason": state["routing_reason"]}
    root = fabrication_root(reg)
    inp = safe_path(input_path, must_exist=True)
    result = run_json_command(
        [
            sys.executable,
            root / "scripts" / "vf_cad.py",
            "dfam",
            "--input", inp,
            "--angle-limit", str(float(angle_limit)),
        ],
        timeout=180,
    )
    if result["exit_code"] != 0:
        return {"status": "FAIL", "tool": "fabrication", "stage": "dfam", "detail": result}
    return {
        "status": "PASS",
        "tool": "fabrication",
        "authority_root": str(root),
        "input": file_artifact(inp),
        "angle_limit": float(angle_limit),
        "analysis": result["payload"],
        "source_mutation": False,
    }


def fabrication_slice(input_path, printer, output_path, execute=False, registry_path=None):
    reg = registry(registry_path)
    state = tool_status("fabrication", reg)
    if not state["available"]:
        return {"status": "BLOCKED", "tool": "fabrication", "reason": state["routing_reason"]}
    printer = str(printer).lower()
    if printer not in VALID_PRINTER_KEYS:
        raise RuntimeError(f"printer must be one of: {sorted(VALID_PRINTER_KEYS)}")
    root = fabrication_root(reg)
    inp = safe_path(input_path, must_exist=True)
    out = safe_path(output_path, must_exist=False)
    if out.exists():
        raise RuntimeError(f"refusing to overwrite existing slice output: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    args = [
        sys.executable,
        root / "scripts" / "vf_cad.py",
        "slice",
        "--input", inp,
        "--printer", printer,
        "--output", out,
    ]
    if execute:
        args.append("--execute")
    result = run_json_command(args, timeout=900 if execute else 180)
    if result["exit_code"] != 0:
        return {"status": "FAIL", "tool": "fabrication", "stage": "slice", "detail": result}
    artifact = file_artifact(out) if out.is_file() else None
    return {
        "status": "PASS",
        "tool": "fabrication",
        "authority_root": str(root),
        "mode": "generate_and_validate_local_gcode_only" if execute else "dry_run",
        "input": file_artifact(inp),
        "printer": printer,
        "output": str(out),
        "artifact": artifact,
        "provider": result["payload"],
        "printer_network_control": False,
    }



def velvetos_authority_root(reg):
    roots = authority_roots(reg)
    root = Path(roots.get("velvetos_core", "")).resolve()
    if not root.is_dir():
        raise RuntimeError("Creative Craft VelvetOS authority root is unavailable")
    return root


def fabrication_status(registry_path=None):
    reg = registry(registry_path)
    state = tool_status("fabrication", reg)
    if not state["available"]:
        return {"status": "BLOCKED", "tool": "fabrication", "reason": state["routing_reason"]}
    root = velvetos_authority_root(reg)
    commands = [
        ("verify", [sys.executable, root / "scripts" / "vf_fabrication_router.py", "verify"]),
        ("doctor", [sys.executable, root / "scripts" / "vf_fabrication_router.py", "doctor"]),
        ("cad_doctor", [sys.executable, root / "scripts" / "vf_cad.py", "doctor"]),
    ]
    results = {}
    ok = True
    for name, args in commands:
        result = run_json_command(args, timeout=120)
        results[name] = result
        ok = ok and result["exit_code"] == 0
    return {"status": "PASS" if ok else "FAIL", "tool": "fabrication", "authority_root": str(root), "checks": results}


def fabrication_route(request, file_path=None, registry_path=None):
    reg = registry(registry_path)
    state = tool_status("fabrication", reg)
    if not state["available"]:
        return {"status": "BLOCKED", "tool": "fabrication", "reason": state["routing_reason"]}
    root = velvetos_authority_root(reg)
    args = [sys.executable, root / "scripts" / "vf_fabrication_router.py", "decide", "--request", str(request)]
    if file_path:
        inp = safe_path(file_path, must_exist=True)
        args += ["--file", inp]
    result = run_json_command(args, timeout=120)
    return {"status": "PASS" if result["exit_code"] == 0 else "FAIL", "tool": "fabrication", "operation": "route", "authority_root": str(root), "result": result}


def fabrication_dfam(input_path, angle_limit=45.0, registry_path=None):
    reg = registry(registry_path)
    state = tool_status("fabrication", reg)
    if not state["available"]:
        return {"status": "BLOCKED", "tool": "fabrication", "reason": state["routing_reason"]}
    root = velvetos_authority_root(reg)
    inp = safe_path(input_path, must_exist=True)
    args = [sys.executable, root / "scripts" / "vf_cad.py", "dfam", "--input", inp, "--angle-limit", str(float(angle_limit))]
    result = run_json_command(args, timeout=180)
    return {"status": "PASS" if result["exit_code"] == 0 else "FAIL", "tool": "fabrication", "operation": "dfam", "input": file_artifact(inp), "result": result}


def fabrication_slice(input_path, printer, output_path, execute=False, registry_path=None):
    allowed = {"h2d", "u1", "ecc2", "c5", "c5pro"}
    if printer not in allowed:
        raise RuntimeError(f"unsupported canonical printer key: {printer}")
    reg = registry(registry_path)
    state = tool_status("fabrication", reg)
    if not state["available"]:
        return {"status": "BLOCKED", "tool": "fabrication", "reason": state["routing_reason"]}
    root = velvetos_authority_root(reg)
    inp = safe_path(input_path, must_exist=True)
    out = safe_path(output_path, must_exist=False)
    if out.exists():
        raise RuntimeError(f"refusing to overwrite existing slice output: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    args = [sys.executable, root / "scripts" / "vf_cad.py", "slice", "--input", inp, "--printer", printer, "--output", out]
    if execute:
        args.append("--execute")
    result = run_json_command(args, timeout=1800 if execute else 180)
    artifact = file_artifact(out) if execute and out.is_file() else None
    return {
        "status": "PASS" if result["exit_code"] == 0 else "FAIL",
        "tool": "fabrication",
        "operation": "slice",
        "execute": bool(execute),
        "printer": printer,
        "input": file_artifact(inp),
        "artifact": artifact,
        "result": result,
        "printer_network_control": False,
    }


def build_parser():
    p = argparse.ArgumentParser(description="VelvetOS Creative Craft router")
    p.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("status")
    s.add_argument("--tool")

    q = sub.add_parser("plan")
    q.add_argument("--intent", required=True)

    rq = sub.add_parser("route")
    rq.add_argument("--request", required=True)

    h = sub.add_parser("host")
    h.add_argument("--tool", required=True)
    h.add_argument("--action", required=True, choices=["start", "stop", "status"])

    c = sub.add_parser("corel-craft")
    c.add_argument("--app", required=True, choices=sorted(COREL_PORTS))
    c.add_argument("--spec", required=True)

    m = sub.add_parser("meshmixer-review")
    m.add_argument("--input", required=True)
    m.add_argument("--screenshot", required=True)

    mts = sub.add_parser("mesh-technical-sheet")
    mts.add_argument("--input", required=True)
    mts.add_argument("--job-id", required=True)
    mts.add_argument("--app", default="corel-designer", choices=sorted(COREL_PORTS))

    t = sub.add_parser("topaz-enhance")
    t.add_argument("--input", required=True)
    t.add_argument("--output", required=True)
    t.add_argument("--model", default="ahq-12")
    t.add_argument("--scale", default=1, type=int)

    f = sub.add_parser("fusion-box")
    f.add_argument("--job-id", required=True)
    f.add_argument("--width-mm", required=True, type=float)
    f.add_argument("--depth-mm", required=True, type=float)
    f.add_argument("--height-mm", required=True, type=float)
    f.add_argument("--format", default="stl", choices=["stl", "step"])

    sub.add_parser("fabrication-status")
    fr = sub.add_parser("fabrication-route")
    fr.add_argument("--request", required=True)
    fr.add_argument("--file")

    fd = sub.add_parser("fabrication-dfam")
    fd.add_argument("--input", required=True)
    fd.add_argument("--angle-limit", type=float, default=45.0)

    fs = sub.add_parser("fabrication-slice")
    fs.add_argument("--input", required=True)
    fs.add_argument("--printer", required=True, choices=["h2d", "u1", "ecc2", "c5", "c5pro"])
    fs.add_argument("--output", required=True)
    fs.add_argument("--execute", action="store_true")
    return p


def main():
    args = build_parser().parse_args()
    try:
        if args.command == "status":
            payload = status_payload(args.tool, args.registry)
        elif args.command == "plan":
            payload = plan(args.intent, args.registry)
        elif args.command == "route":
            payload = route_request(args.request, args.registry)
        elif args.command == "host":
            payload = host_action(args.tool, args.action, args.registry)
        elif args.command == "corel-craft":
            payload = corel_craft(args.app, args.spec, args.registry)
        elif args.command == "meshmixer-review":
            payload = meshmixer_review(args.input, args.screenshot, args.registry)
        elif args.command == "mesh-technical-sheet":
            payload = mesh_technical_sheet(args.input, args.job_id, args.app, args.registry)
        elif args.command == "topaz-enhance":
            payload = topaz_enhance(args.input, args.output, args.model, args.scale, args.registry)
        elif args.command == "fusion-box":
            payload = fusion_box(args.job_id, args.width_mm, args.depth_mm, args.height_mm, args.format, args.registry)
        elif args.command == "fabrication-status":
            payload = fabrication_status(args.registry)
        elif args.command == "fabrication-route":
            payload = fabrication_route(args.request, args.file, args.registry)
        elif args.command == "fabrication-dfam":
            payload = fabrication_dfam(args.input, args.angle_limit, args.registry)
        elif args.command == "fabrication-slice":
            payload = fabrication_slice(args.input, args.printer, args.output, args.execute, args.registry)
        else:
            raise RuntimeError("unsupported command")
        return emit(payload, 0 if payload.get("status") == "PASS" else 2)
    except Exception as exc:
        return emit({"status": "FAIL", "error": str(exc)}, 1)


if __name__ == "__main__":
    sys.exit(main())
