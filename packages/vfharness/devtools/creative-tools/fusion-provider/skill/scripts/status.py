"""Read-only Fusion native MCP status for the DCC-MCP adapter."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import uuid

NODE = Path(r"C:\Program Files\nodejs\node.exe")
CLIENT = Path(r"D:\Velvet\Tools\CreativeTools\FusionProvider\0.1.0\fusion-native-call.mjs")
STATE_DIR = Path(r"D:\Velvet\State\CreativeTools\FusionProvider\ops")


def _extract_text(result: object) -> object:
    if not isinstance(result, dict):
        return result
    content = result.get("content")
    if not isinstance(content, list):
        return result
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str):
            try:
                return json.loads(block["text"])
            except json.JSONDecodeError:
                return block["text"]
    return result


def main() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    args_path = STATE_DIR / f"status-{uuid.uuid4().hex}.json"
    args_path.write_text(json.dumps({"queryType": "activeCommand"}), encoding="utf-8")
    try:
        if not NODE.is_file():
            raise RuntimeError(f"Node runtime missing: {NODE}")
        if not CLIENT.is_file():
            raise RuntimeError(f"Fusion native client missing: {CLIENT}")

        proc = subprocess.run(
            [str(NODE), str(CLIENT), "fusion_mcp_read", str(args_path)],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        if not lines:
            raise RuntimeError(
                f"Fusion native client returned no JSON (exit={proc.returncode})"
            )
        envelope = json.loads(lines[-1])
        if proc.returncode != 0 or not envelope.get("ok"):
            raise RuntimeError(str(envelope.get("error") or f"exit={proc.returncode}"))

        payload = {
            "success": True,
            "message": "Autodesk Fusion native MCP is reachable.",
            "context": {
                "provider": "fusion-native-bridge",
                "provider_version": "0.1.0",
                "native_endpoint": "http://127.0.0.1:27182/mcp",
                "active_command": _extract_text(envelope.get("result")),
            },
        }
        print(json.dumps(payload, separators=(",", ":")))
    except Exception as exc:
        print(
            json.dumps(
                {
                    "success": False,
                    "message": "Autodesk Fusion native MCP is unavailable.",
                    "context": {"error": str(exc)},
                },
                separators=(",", ":"),
            )
        )
        sys.exit(1)
    finally:
        try:
            args_path.unlink(missing_ok=True)
        except Exception:
            pass


if __name__ == "__main__":
    main()
