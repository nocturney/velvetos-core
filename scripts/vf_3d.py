#!/usr/bin/env python3
"""VelvetOS local 3D router: CAD + Blender + print QA, never printer control.

The router is deliberately local-first. It selects an existing VelvetOS production
path, executes bounded Blender/headless QA helpers, and never uploads or starts a
physical print. External paid AI providers are outside this bridge.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import struct
import subprocess
import sys
import time
import uuid
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRINTLAB = Path(os.environ.get(
    "VELVET_PRINTLAB_ROOT", Path.home() / "Documents" / "VelvetPrintLab"
)).resolve()
FUNCTIONAL_TERMS = (
    " mm", "step", "b-rep", "brep", "dimension", "tolerance", "clearance",
    "thread", "bracket", "adapter", "fixture", " jig", "gear", "enclosure",
    "hole", " fit", "assembly", "mechanical", "parametric",
    "מידה", "מידות", 'מ"מ', "סבילות", "חור", "תבריג", "מתאם", "תושבת",
    "ג'יג", "גלגל שיניים", "מכני", "פרמטרי",
)
ORGANIC_TERMS = (
    "organic", "sculpt", "figurine", "statue", "creature", "character",
    "mascot", "decorative", "ornament", "reference image", "from photo",
    "mesh fitting", "פסל", "פסלון", "דמות", "חיה", "אורגני", "פיסול",
    "דקורטיבי", "מתמונה", "מתמונות", "רפרנס",
)
MESH_TERMS = (
    ".stl", ".obj", ".glb", ".gltf", ".blend", "mesh", "remesh", "uv",
    "repair mesh", "existing model", "מודל קיים", "תיקון mesh", "תיקון רשת",
)
FORBIDDEN_SCRIPT_PATTERNS = (
    r"\b(?:import|from)\s+(?:os|subprocess|socket|requests|urllib|http|ctypes|winreg)\b",
    r"\b(?:open|eval|exec|compile|__import__)\s*\(",
    r"\b(?:pip|ensurepip)\b",
)
def printlab_root() -> Path:
    return Path(os.environ.get("VELVET_PRINTLAB_ROOT", DEFAULT_PRINTLAB)).resolve()


def blender_ai_root() -> Path:
    return Path(os.environ.get(
        "BLENDER_AI_MCP_ROOT", printlab_root() / "tools" / "blender-ai-mcp"
    )).resolve()


def design_os_root() -> Path:
    return Path(os.environ.get(
        "DESIGN_OS_3D_ROOT", printlab_root() / "tools" / "design-os-3d-blender"
    )).resolve()


def job_root() -> Path:
    root = Path(os.environ.get(
        "VELVET_3D_JOB_ROOT", printlab_root() / "3d-jobs"
    )).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def venv_python(repo: Path) -> Path:
    return repo / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def component_version(repo: Path) -> str | None:
    """Read the installed component's declared version for reporting, never as a gate."""
    pyproject = repo / "pyproject.toml"
    if not pyproject.is_file():
        return None
    text = pyproject.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r'(?m)^version\s*=\s*["\']([^"\']+)["\']\s*$', text)
    return match.group(1).strip() if match else None


def version_tuple_from_text(value: str | None) -> tuple[int, ...]:
    if not value:
        return ()
    match = re.search(r"(\d+(?:\.\d+)+)", value)
    return tuple(int(part) for part in match.group(1).split(".")) if match else ()


def _blender_version(path: Path) -> tuple[tuple[int, ...], str]:
    """Return a sortable observed Blender version and its display string."""
    try:
        cp = subprocess.run(
            [str(path), "--version"], text=True, capture_output=True,
            timeout=10, check=False,
        )
        line = (cp.stdout.splitlines() or cp.stderr.splitlines() or [""])[0].strip()
    except Exception:
        return (), ""
    return version_tuple_from_text(line), line


def detect_blender() -> Path | None:
    """Discover the best installed Blender without pinning a release number."""
    candidates: list[Path] = []
    if os.environ.get("BLENDER_BIN"):
        candidates.append(Path(os.environ["BLENDER_BIN"]))
    found = shutil.which("blender")
    if found:
        candidates.append(Path(found))

    if os.name == "nt":
        roots = [
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Blender Foundation",
            Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "Programs" / "Blender Foundation",
        ]
        for root in roots:
            if root.is_dir():
                candidates.extend(root.glob("Blender *\\blender.exe"))
                candidates.extend(root.glob("*\\blender.exe"))
        steam = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Steam" / "steamapps" / "common" / "Blender" / "blender.exe"
        candidates.append(steam)

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate.is_file():
            resolved = candidate.resolve()
            key = str(resolved).casefold()
            if key not in seen:
                seen.add(key)
                unique.append(resolved)
    if not unique:
        return None

    ranked = [(_blender_version(candidate)[0], candidate) for candidate in unique]
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[0][1]


def proc(cmd: list[str], *, cwd: Path | None = None, env: dict | None = None,
         timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd, cwd=cwd, env=env, text=True, capture_output=True,
        timeout=timeout, check=False,
    )


def contains_any(text: str, terms: tuple[str, ...]) -> list[str]:
    value = " " + text.casefold() + " "
    return [term for term in terms if term.casefold() in value]


def route_request(text: str) -> dict:
    functional = contains_any(text, FUNCTIONAL_TERMS)
    organic = contains_any(text, ORGANIC_TERMS)
    mesh = contains_any(text, MESH_TERMS)
    if functional and organic:
        route = "HYBRID_CAD_THEN_BLENDER"
        master = ["STEP", "BLEND"]
        reason = "functional constraints plus organic/reference-driven form"
    elif organic:
        route = "BLENDER_NATIVE"
        master = ["BLEND"]
        reason = "organic/sculptural/reference-driven geometry"
    elif mesh:
        route = "BLENDER_NATIVE"
        master = ["BLEND"]
        reason = "existing mesh inspection/repair/refinement"
    else:
        route = "TEXT_TO_CAD"
        master = ["STEP"]
        reason = "default printable engineering path; preserves parametric source"

    return {
        "status": "ROUTED",
        "route": route,
        "reason": reason,
        "signals": {"functional": functional, "organic": organic, "mesh": mesh},
        "master_formats": master,
        "print_sidecars": ["STL", "3MF"],
        "qa": ["geometry_measurements", "print_gate", "orca_dry_run"],
        "physical_print_authorized": False,
        "paid_external_generation_authorized": False,
    }
def _rpc_hardening_state(rpc: Path) -> dict:
    if not rpc.is_file():
        return {"status": "MISSING", "path": str(rpc), "loopback_only": False}
    text = rpc.read_text(encoding="utf-8", errors="ignore")
    loopback = bool(re.search(r'HOST\s*=\s*["\']127\.0\.0\.1["\']', text))
    wildcard = bool(re.search(r'HOST\s*=\s*["\']0\.0\.0\.0["\']', text))
    port_match = re.search(
        r'PORT\s*=\s*int\(os\.environ\.get\(["\']BLENDER_RPC_PORT["\'],\s*["\'](\d+)["\']\)\)',
        text,
    )
    default_port = int(port_match.group(1)) if port_match else None
    port_ok = bool(default_port and 1024 <= default_port <= 65535)
    exclusive = "SO_EXCLUSIVEADDRUSE" in text
    exclusive_ok = exclusive if os.name == "nt" else True
    hardened = loopback and not wildcard and port_ok and exclusive_ok
    return {
        "status": "PASS" if hardened else "FAIL",
        "path": str(rpc),
        "loopback_only": loopback and not wildcard,
        "wildcard_listener_present": wildcard,
        "rpc_port": default_port if port_ok else None,
        "windows_exclusive_bind": exclusive,
    }


def hardening_state() -> dict:
    return _rpc_hardening_state(
        blender_ai_root() / "blender_addon" / "infrastructure" / "rpc_server.py"
    )


def blender_addon_state(blender: Path | None) -> dict:
    """Inspect the addon inside the Blender installation selected at runtime."""
    if not blender:
        return {"status": "MISSING", "module_found": False, "enabled": False}
    code = (
        "import bpy, addon_utils, json, os;"
        "mods=[m for m in addon_utils.modules() if m.__name__=='blender_ai_mcp'];"
        "path=os.path.dirname(mods[0].__file__) if mods else None;"
        "enabled='blender_ai_mcp' in bpy.context.preferences.addons;"
        "print('VF_ADDON_STATE '+json.dumps({'module_found':bool(mods),'enabled':enabled,'path':path}))"
    )
    cp = proc([str(blender), "--background", "--python-expr", code], timeout=45)
    marker = next(
        (line for line in cp.stdout.splitlines() if line.startswith("VF_ADDON_STATE ")),
        None,
    )
    if cp.returncode != 0 or not marker:
        return {
            "status": "FAIL",
            "module_found": False,
            "enabled": False,
            "returncode": cp.returncode,
            "tail": (cp.stdout + "\n" + cp.stderr).splitlines()[-15:],
        }
    try:
        state = json.loads(marker.removeprefix("VF_ADDON_STATE "))
    except Exception as exc:
        return {"status": "FAIL", "module_found": False, "enabled": False, "detail": str(exc)}
    addon_path = Path(state["path"]).resolve() if state.get("path") else None
    installed_hardening = (
        _rpc_hardening_state(addon_path / "infrastructure" / "rpc_server.py")
        if addon_path else {"status": "MISSING"}
    )
    ok = bool(
        state.get("module_found")
        and state.get("enabled")
        and installed_hardening.get("status") == "PASS"
    )
    return {
        "status": "PASS" if ok else "FAIL",
        **state,
        "installed_hardening": installed_hardening,
    }


def configured_rpc_port() -> int | None:
    raw = (os.environ.get("BLENDER_RPC_PORT") or "").strip()
    if raw:
        try:
            port = int(raw)
            if 1024 <= port <= 65535:
                return port
        except ValueError:
            return None
    return hardening_state().get("rpc_port")


def blender_rpc_probe(host: str = "127.0.0.1", port: int | None = None,
                      timeout: float = 1.5) -> dict:
    """Protocol-level Blender addon check; never treats an arbitrary open port as Blender."""
    port = port or configured_rpc_port()
    if port is None:
        return {
            "status": "BLOCKED",
            "host": host,
            "port": None,
            "protocol_verified": False,
            "detail": "No valid loopback Blender RPC port could be resolved from the installed addon.",
        }
    request_id = str(uuid.uuid4())
    payload = json.dumps({
        "request_id": request_id,
        "cmd": "ping",
        "args": {},
        "timeout_seconds": 2,
    }).encode("utf-8")
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
    except OSError as exc:
        return {
            "status": "OFFLINE",
            "host": host,
            "port": port,
            "protocol_verified": False,
            "detail": str(exc),
        }

    def recvall(conn: socket.socket, count: int) -> bytes:
        data = bytearray()
        while len(data) < count:
            chunk = conn.recv(count - len(data))
            if not chunk:
                raise RuntimeError("socket closed before complete Blender RPC frame")
            data.extend(chunk)
        return bytes(data)

    try:
        with sock:
            sock.settimeout(timeout)
            sock.sendall(struct.pack(">I", len(payload)) + payload)
            size = struct.unpack(">I", recvall(sock, 4))[0]
            if size <= 0 or size > 1024 * 1024:
                raise RuntimeError(f"invalid Blender RPC frame length: {size}")
            response = json.loads(recvall(sock, size).decode("utf-8"))
        version = ((response.get("result") or {}).get("version")
                   if isinstance(response, dict) else None)
        ok = (
            isinstance(response, dict)
            and response.get("request_id") == request_id
            and response.get("status") == "ok"
            and isinstance(version, str)
            and bool(version.strip())
        )
        return {
            "status": "PASS" if ok else "FAIL",
            "host": host,
            "port": port,
            "protocol_verified": ok,
            "blender_version": version,
            "response_status": response.get("status") if isinstance(response, dict) else None,
        }
    except Exception as exc:
        return {
            "status": "FAIL",
            "host": host,
            "port": port,
            "protocol_verified": False,
            "detail": str(exc),
        }


def read_receipt(repo: Path) -> dict | None:
    p = repo / ".velvetos-install.json"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def cad_doctor() -> dict:
    cp = proc([sys.executable, str(ROOT / "scripts" / "vf_cad.py"), "doctor"], timeout=90)
    try:
        body = json.loads(cp.stdout)
    except Exception:
        body = {"status": "BLOCKED", "stdout": cp.stdout[-2000:], "stderr": cp.stderr[-2000:]}
    body["returncode"] = cp.returncode
    return body
def doctor() -> dict:
    blender = detect_blender()
    bver = None
    if blender:
        cp = proc([str(blender), "--version"], timeout=15)
        bver = (cp.stdout.splitlines() or [None])[0]
    bai = blender_ai_root()
    dos = design_os_root()
    hardening = hardening_state()
    addon_state = blender_addon_state(blender)
    cad = cad_doctor()
    bai_receipt = read_receipt(bai)
    dos_receipt = read_receipt(dos)

    design_import = None
    if venv_python(dos).is_file():
        design_import = proc(
            [str(venv_python(dos)), "-c",
             "import design_os_3d_blender_mcp.server; print('OK')"],
            cwd=dos, timeout=30,
        )
    blender_ai_import = None
    if venv_python(bai).is_file():
        env = os.environ.copy()
        env["VISION_ENABLED"] = "false"
        blender_ai_import = proc(
            [str(venv_python(bai)), "-c", "import server.main; print('OK')"],
            cwd=bai, env=env, timeout=60,
        )

    installed_hardening = addon_state.get("installed_hardening") or {}
    rpc_probe = blender_rpc_probe(port=installed_hardening.get("rpc_port"))
    dos_runtime = (dos_receipt or {}).get("runtime") or {}
    bai_runtime = (bai_receipt or {}).get("runtime") or {}
    current_blender_version = version_tuple_from_text(bver)
    dos_accepted_blender = version_tuple_from_text(dos_runtime.get("accepted_blender_version"))
    bai_accepted_blender = version_tuple_from_text(bai_runtime.get("selected_blender_version"))
    dos_blender_evidence_current = bool(
        current_blender_version and dos_accepted_blender == current_blender_version
    )
    bai_blender_evidence_current = bool(
        current_blender_version and bai_accepted_blender == current_blender_version
    )
    dos_version = component_version(dos)
    bai_version = component_version(bai)
    dos_receipt_current = bool(
        dos_receipt and dos_version and dos_receipt.get("version") == dos_version
    )
    bai_receipt_current = bool(
        bai_receipt and bai_version and bai_receipt.get("version") == bai_version
    )

    design_ready = bool(
        (design_os_root() / "scripts" / "production-gate.py").is_file()
        and design_import and design_import.returncode == 0
    )
    design_acceptance_current = bool(
        dos_receipt_current
        and dos_blender_evidence_current
        and dos_runtime.get("windows_benchmark") == "PASS"
        and dos_runtime.get("production_geometry_gate") == "PASS"
        and dos_runtime.get("declared_part_coverage_audit") == "PASS"
    )
    blender_ai_acceptance_current = bool(
        bai_receipt_current
        and bai_blender_evidence_current
        and bai_runtime.get("protocol_acceptance") == "PASS"
        and bai_runtime.get("write_acceptance") == "PASS"
    )
    rpc_safe = rpc_probe.get("status") in {"PASS", "OFFLINE"}
    blender_ai_ready = bool(
        hardening["status"] == "PASS"
        and addon_state.get("status") == "PASS"
        and rpc_safe
        and blender_ai_import and blender_ai_import.returncode == 0
    )
    status = "PASS" if blender and cad.get("status") == "PASS" and design_ready and blender_ai_ready else "BLOCKED"
    return {
        "status": status,
        "blender": {"path": str(blender) if blender else None, "version": bver},
        "text_to_cad": cad,
        "design_os": {
            "root": str(dos), "venv": str(venv_python(dos)), "ready": design_ready,
            "installed_version": dos_version,
            "receipt_version_current": dos_receipt_current,
            "blender_evidence_current": dos_blender_evidence_current,
            "acceptance_current": design_acceptance_current,
            "receipt": dos_receipt,
            "import_tail": (design_import.stderr[-500:] if design_import and design_import.returncode else "OK" if design_import else "MISSING"),
        },
        "blender_ai_mcp": {
            "root": str(bai), "venv": str(venv_python(bai)), "ready": blender_ai_ready,
            "installed_version": bai_version,
            "receipt_version_current": bai_receipt_current,
            "blender_evidence_current": bai_blender_evidence_current,
            "acceptance_current": blender_ai_acceptance_current,
            "hardening": hardening,
            "selected_blender_addon": addon_state,
            "rpc_probe": rpc_probe,
            "receipt": bai_receipt,
            "import_tail": (blender_ai_import.stderr[-500:] if blender_ai_import and blender_ai_import.returncode else "OK" if blender_ai_import else "MISSING"),
        },
        "acceptance": {
            "release_evidence_current": bool(
                design_acceptance_current and blender_ai_acceptance_current
            ),
            "stale_evidence_blocks_release_claim_not_runtime_discovery": True,
        },
        "policy": {
            "external_paid_ai": "DISABLED",
            "printer_network_control": False,
            "start_print": False,
            "tool_version_allowlist": False,
        },
    }
def safe_script(path: Path) -> tuple[bool, list[str]]:
    path = path.resolve()
    try:
        path.relative_to(job_root())
    except ValueError:
        return False, ["script must live under VELVET_3D_JOB_ROOT"]
    if not path.is_file() or path.stat().st_size > 1024 * 1024:
        return False, ["script missing or exceeds 1 MiB"]
    text = path.read_text(encoding="utf-8", errors="strict")
    hits = [pattern for pattern in FORBIDDEN_SCRIPT_PATTERNS if re.search(pattern, text, re.I)]
    return not hits, hits


def run_pass(script: Path) -> dict:
    blender = detect_blender()
    if not blender:
        return {"status": "BLOCKED", "reason": "No usable Blender installation was discovered"}
    ok, hits = safe_script(script)
    if not ok:
        return {"status": "BLOCKED", "reason": "script safety gate failed", "hits": hits}
    cp = proc([
        str(blender), "--factory-startup", "--disable-autoexec", "-b",
        "--python-exit-code", "3", "--python", str(script.resolve()),
    ], timeout=180)
    lines = [x.strip() for x in (cp.stdout + "\n" + cp.stderr).splitlines() if x.strip()]
    sentinel = next((x for x in reversed(lines) if x.startswith(("AGENT_OK", "AGENT_FAIL"))), None)
    passed = cp.returncode == 0 and sentinel is not None and sentinel.startswith("AGENT_OK")
    return {
        "status": "PASS" if passed else "FAIL", "returncode": cp.returncode,
        "sentinel": sentinel, "tail": lines[-15:],
    }
def gate(scene: Path, spec: Path, report: Path, export_dir: Path | None) -> dict:
    blender = detect_blender()
    runner = design_os_root() / "scripts" / "production-gate.py"
    if not blender or not runner.is_file():
        return {"status": "BLOCKED", "reason": "design-os or Blender runtime missing"}
    cmd = [
        str(venv_python(design_os_root())), str(runner),
        "--scene", str(scene.resolve()), "--spec", str(spec.resolve()),
        "--report", str(report.resolve()), "--blender", str(blender),
    ]
    if export_dir:
        export_dir.mkdir(parents=True, exist_ok=True)
        cmd.extend(["--export-dir", str(export_dir.resolve())])
    cp = proc(cmd, cwd=design_os_root(), timeout=900)
    lines = [x.strip() for x in (cp.stdout + "\n" + cp.stderr).splitlines() if x.strip()]
    sentinel = next((x for x in reversed(lines) if x.startswith(("AGENT_OK", "AGENT_FAIL"))), None)
    return {
        "status": "PASS" if cp.returncode == 0 and sentinel and sentinel.startswith("AGENT_OK") else "FAIL",
        "returncode": cp.returncode, "sentinel": sentinel, "tail": lines[-20:],
        "report": str(report.resolve()),
    }


def benchmark() -> dict:
    work = job_root() / "benchmark-current"
    work.mkdir(parents=True, exist_ok=True)
    blend = work / "smoke.blend"
    script = work / "smoke.py"
    script.write_text(
        "import bpy, json\n"
        "bpy.context.scene.unit_settings.system='METRIC'\n"
        "bpy.context.scene.unit_settings.scale_length=1.0\n"
        "mesh=bpy.data.meshes.new('VFSmokeMesh')\n"
        "v=[(-.01,-.01,-.005),(.01,-.01,-.005),(.01,.01,-.005),(-.01,.01,-.005),"
        "(-.01,-.01,.005),(.01,-.01,.005),(.01,.01,.005),(-.01,.01,.005)]\n"
        "f=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]\n"
        "mesh.from_pydata(v,[],f); mesh.update()\n"
        "obj=bpy.data.objects.new('VF_SMOKE_20x20x10',mesh); bpy.context.collection.objects.link(obj)\n"
        f"bpy.ops.wm.save_as_mainfile(filepath=r'{str(blend)}')\n"
        "dims=[round(float(x)*1000,3) for x in obj.dimensions]\n"
        "print('AGENT_OK '+json.dumps({'dims_mm':dims,'vertices':len(mesh.vertices),'faces':len(mesh.polygons)}))\n",
        encoding="utf-8",
    )
    t0 = time.perf_counter()
    blender_result = run_pass(script)
    blender_seconds = round(time.perf_counter() - t0, 3)
    t1 = time.perf_counter()
    cad = cad_doctor()
    cad_seconds = round(time.perf_counter() - t1, 3)
    passed = blender_result["status"] == "PASS" and cad.get("status") == "PASS"
    return {
        "status": "PASS" if passed else "FAIL",
        "blender_headless": {**blender_result, "seconds": blender_seconds, "blend": str(blend)},
        "text_to_cad_doctor": {"status": cad.get("status"), "seconds": cad_seconds},
        "comparison_scope": "runtime smoke only; not an aesthetic/model-quality ranking",
        "physical_print_authorized": False,
    }
def mcp_server() -> int:
    root = blender_ai_root()
    py = venv_python(root)
    hardening = hardening_state()
    blender = detect_blender()
    addon_state = blender_addon_state(blender)
    installed_hardening = addon_state.get("installed_hardening") or {}
    rpc_port = installed_hardening.get("rpc_port")
    if (
        not py.is_file()
        or hardening["status"] != "PASS"
        or addon_state.get("status") != "PASS"
        or rpc_port is None
    ):
        print(json.dumps({
            "status": "BLOCKED",
            "reason": "hardened blender-ai-mcp runtime not ready for the selected installed Blender",
            "selected_blender": str(blender) if blender else None,
            "addon_state": addon_state,
        }, ensure_ascii=False))
        return 2
    env = os.environ.copy()
    env.update({
        "BLENDER_RPC_HOST": "127.0.0.1",
        "BLENDER_RPC_PORT": str(rpc_port),
        "MCP_SURFACE_PROFILE": "llm-guided",
        "MCP_TRANSPORT_MODE": "stdio",
        "MCP_PROMPTS_AS_TOOLS_ENABLED": "false",
        "ROUTER_ENABLED": "true",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "HF_DATASETS_OFFLINE": "1",
        "VISION_ENABLED": "false",
        "VISION_REFERENCE_UNDERSTANDING_ENABLED": "false",
        "OTEL_ENABLED": "false",
        "FASTMCP_SHOW_SERVER_BANNER": "false",
        "PYTHONUNBUFFERED": "1",
    })
    return subprocess.call([str(py), "-m", "server.main"], cwd=root, env=env)


def mcp_config() -> dict:
    return {
        "mcpServers": {
            "velvet-blender": {
                "command": sys.executable,
                "args": [str(Path(__file__).resolve()), "mcp-server"],
                "env": {"VELVET_PRINTLAB_ROOT": str(printlab_root())},
            }
        },
        "note": f"Local-only hardened Blender control: llm-guided stdio, RPC 127.0.0.1:{configured_rpc_port()}, Hugging Face offline, external vision/providers disabled.",
    }
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    q = sub.add_parser("route")
    q.add_argument("--request", required=True)
    sub.add_parser("doctor")
    q = sub.add_parser("run-pass")
    q.add_argument("--script", required=True)
    q = sub.add_parser("gate")
    q.add_argument("--scene", required=True)
    q.add_argument("--spec", required=True)
    q.add_argument("--report", required=True)
    q.add_argument("--export-dir")
    sub.add_parser("benchmark")
    sub.add_parser("mcp-config")
    sub.add_parser("mcp-server")
    return p


def main() -> int:
    a = parser().parse_args()
    if a.command == "route":
        result = route_request(a.request)
    elif a.command == "doctor":
        result = doctor()
    elif a.command == "run-pass":
        result = run_pass(Path(a.script))
    elif a.command == "gate":
        result = gate(Path(a.scene), Path(a.spec), Path(a.report),
                      Path(a.export_dir) if a.export_dir else None)
    elif a.command == "benchmark":
        result = benchmark()
    elif a.command == "mcp-config":
        result = mcp_config()
    else:
        return mcp_server()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") not in {"FAIL", "BLOCKED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
