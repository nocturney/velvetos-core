#!/usr/bin/env python3
"""Deterministic AgentShield-pattern audit for committed Cursor/agent surfaces."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CURSOR = ROOT / ".cursor"
MCP = CURSOR / "mcp.json"
SECRET_PATTERNS = {
    "openai-like": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "github-pat": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "slack-token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "google-api-key": re.compile(r"\bAIza[A-Za-z0-9_-]{24,}\b"),
    "bearer-literal": re.compile(r"Bearer\s+(?![A-Z][A-Z0-9_]{8,}\b)[A-Za-z0-9._~-]{24,}"),
}
PIPE_SHELL = re.compile(r"\b(?:curl|wget)\b[^\n|]*\|\s*(?:sudo\s+)?(?:bash|sh|zsh)\b", re.I)
FILLED_JSON_SECRET = re.compile(r'"(?:api[_-]?key|token|secret|password|authorization)"\s*:\s*"(?!\$\{|\$\(|<|REPLACE|YOUR_|ENV:)[^"\n]{12,}"', re.I)


def iter_agent_text() -> list[Path]:
    out: list[Path] = []
    for rel in ("skills", "rules"):
        base = CURSOR / rel
        if base.is_dir():
            out.extend(p for p in base.rglob("*") if p.is_file() and p.suffix in {".md", ".mdc", ".json", ".yaml", ".yml"})
    for name in ("mcp.json", "vf-desk.json"):
        p = CURSOR / name
        if p.is_file():
            out.append(p)
    return sorted(set(out))


def main() -> int:
    problems: list[str] = []
    if not MCP.is_file():
        problems.append("missing .cursor/mcp.json")
    else:
        try:
            data = json.loads(MCP.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append(f"invalid .cursor/mcp.json: {exc}")
            data = {}
        servers = data.get("mcpServers") or {}
        if not isinstance(servers, dict):
            problems.append("mcpServers must be an object")
            servers = {}
        for name, row in servers.items():
            if not isinstance(row, dict):
                problems.append(f"MCP {name}: config must be object")
                continue
            url = row.get("url")
            if url:
                parsed = urlsplit(str(url))
                if parsed.scheme not in {"http", "https"}:
                    problems.append(f"MCP {name}: remote URL must be http(s)")
                if parsed.username or parsed.password:
                    problems.append(f"MCP {name}: credentials embedded in URL")
            if FILLED_JSON_SECRET.search(json.dumps(row, ensure_ascii=False)):
                problems.append(f"MCP {name}: probable committed literal secret")

    files = iter_agent_text()
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(ROOT)
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                problems.append(f"{rel}: probable {label} secret literal")
        for n, line in enumerate(text.splitlines(), 1):
            if PIPE_SHELL.search(line):
                lowered = line.lower()
                if not any(x in lowered for x in ("forbid", "never", "do not", "אסור", "לא להריץ", "deny")):
                    problems.append(f"{rel}:{n}: remote pipe-to-shell command on agent surface")

    if problems:
        for problem in problems:
            print(f"FAIL {problem}", file=sys.stderr)
        return 1
    print(f"OK agent-surface-security files={len(files)} mcp={MCP.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
