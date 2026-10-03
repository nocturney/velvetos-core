"""Shared bounded Fusion native-MCP helpers.

No caller can supply Python source. Tool modules build fixed trusted scripts from
validated scalar arguments, then this helper executes them through Autodesk's
native MCP. The Fusion 2705.1.25 execute response may hang after the script has
already completed, so completion is proven by a marker written by the trusted
script and the hung client is terminated afterwards.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import textwrap
import time
import uuid

NODE = Path(r"C:\Program Files\nodejs\node.exe")
CLIENT = Path(r"D:\Velvet\Tools\CreativeTools\FusionProvider\0.1.0\fusion-native-call.mjs")
STATE_ROOT = Path(r"D:\Velvet\State\CreativeTools\FusionProvider")
OPS_ROOT = STATE_ROOT / "ops"
TEMP_STATE = STATE_ROOT / "temp-design.json"
EXPORT_ROOT = Path(r"D:\Velvet\Tmp\creative-tools\fusion-provider")
_CREATE_NO_WINDOW = 0x08000000


class FusionProviderError(RuntimeError):
    pass


def _ensure_dirs() -> None:
    OPS_ROOT.mkdir(parents=True, exist_ok=True)
    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)


def _node_command(tool_name: str, args_path: Path) -> list[str]:
    if not NODE.is_file():
        raise FusionProviderError(f"Node runtime missing: {NODE}")
    if not CLIENT.is_file():
        raise FusionProviderError(f"Fusion native client missing: {CLIENT}")
    return [str(NODE), str(CLIENT), tool_name, str(args_path)]


def _parse_client_stdout(stdout: str) -> dict:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise FusionProviderError("Fusion native client returned no JSON.")
    try:
        value = json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        raise FusionProviderError(f"Invalid Fusion native client JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise FusionProviderError("Fusion native client returned a non-object result.")
    return value


def native_call(tool_name: str, arguments: dict, timeout: float = 15.0) -> dict:
    _ensure_dirs()
    op_id = uuid.uuid4().hex
    args_path = OPS_ROOT / f"{op_id}.args.json"
    args_path.write_text(json.dumps(arguments), encoding="utf-8")
    try:
        proc = subprocess.run(
            _node_command(tool_name, args_path),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            creationflags=_CREATE_NO_WINDOW,
        )
        envelope = _parse_client_stdout(proc.stdout)
        if proc.returncode != 0 or not envelope.get("ok"):
            raise FusionProviderError(
                str(envelope.get("error") or proc.stderr.strip() or f"exit={proc.returncode}")
            )
        result = envelope.get("result")
        if not isinstance(result, dict):
            raise FusionProviderError("Fusion native result is not an object.")
        return result
    except subprocess.TimeoutExpired as exc:
        raise FusionProviderError(f"Fusion native call timed out after {timeout}s.") from exc
    finally:
        try:
            args_path.unlink(missing_ok=True)
        except Exception:
            pass


def _trusted_script(body: str, marker: Path) -> str:
    indented = textwrap.indent(textwrap.dedent(body).strip(), "        ")
    marker_literal = repr(str(marker))
    return f"""import adsk.core, adsk.fusion, json, traceback

def _vf_write_marker(data):
    with open({marker_literal}, "w", encoding="utf-8") as handle:
        json.dump(data, handle)

def run(_context):
    try:
{indented}
        _vf_write_marker({{"ok": True, "result": result}})
    except Exception as exc:
        _vf_write_marker({{
            "ok": False,
            "error": str(exc),
            "type": type(exc).__name__,
            "traceback": traceback.format_exc()
        }})
"""


def run_trusted_script(body: str, *, read_only: bool = False, timeout: float = 45.0) -> dict:
    _ensure_dirs()
    op_id = uuid.uuid4().hex
    marker = OPS_ROOT / f"{op_id}.result.json"
    args_path = OPS_ROOT / f"{op_id}.args.json"
    script = _trusted_script(body, marker)
    args = {"featureType": "script", "object": {"script": script, "readOnly": bool(read_only)}}
    args_path.write_text(json.dumps(args), encoding="utf-8")

    proc = subprocess.Popen(
        _node_command("fusion_mcp_execute", args_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=_CREATE_NO_WINDOW,
    )
    deadline = time.monotonic() + timeout
    marker_value = None
    try:
        while time.monotonic() < deadline:
            if marker.is_file():
                try:
                    marker_value = json.loads(marker.read_text(encoding="utf-8"))
                    break
                except (OSError, json.JSONDecodeError):
                    pass
            if proc.poll() is not None and not marker.is_file():
                stdout, stderr = proc.communicate(timeout=1)
                envelope = None
                try:
                    envelope = _parse_client_stdout(stdout)
                except Exception:
                    envelope = None
                raise FusionProviderError(
                    str(
                        (envelope or {}).get("error")
                        or stderr.strip()
                        or f"Fusion execute client exited before completion marker (exit={proc.returncode})."
                    )
                )
            time.sleep(0.1)

        if marker_value is None:
            raise FusionProviderError(f"Fusion trusted operation timed out after {timeout}s.")

        if not isinstance(marker_value, dict) or not marker_value.get("ok"):
            raise FusionProviderError(
                str((marker_value or {}).get("error") or "Fusion trusted operation failed.")
            )

        result = marker_value.get("result")
        if not isinstance(result, dict):
            raise FusionProviderError("Fusion trusted operation marker has no object result.")
        return result
    finally:
        if proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        try:
            args_path.unlink(missing_ok=True)
        except Exception:
            pass


def load_temp_state() -> dict:
    if not TEMP_STATE.is_file():
        raise FusionProviderError("No provider-owned temporary Fusion design is tracked.")
    try:
        value = json.loads(TEMP_STATE.read_text(encoding="utf-8"))
    except Exception as exc:
        raise FusionProviderError(f"Temporary design state is unreadable: {exc}") from exc
    if not isinstance(value, dict) or not value.get("document") or not value.get("token"):
        raise FusionProviderError("Temporary design state is invalid.")
    return value


def save_temp_state(value: dict) -> None:
    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    tmp = TEMP_STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    tmp.replace(TEMP_STATE)


def clear_temp_state() -> None:
    try:
        TEMP_STATE.unlink(missing_ok=True)
    except Exception:
        pass


def print_success(message: str, context: dict) -> None:
    print(json.dumps({"success": True, "message": message, "context": context}, separators=(",", ":")))


def fail(message: str, exc: Exception | None = None) -> None:
    context = {}
    if exc is not None:
        context["error"] = str(exc)
    print(json.dumps({"success": False, "message": message, "context": context}, separators=(",", ":")))
    raise SystemExit(1)
