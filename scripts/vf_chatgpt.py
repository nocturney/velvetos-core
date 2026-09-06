#!/usr/bin/env python3
"""ChatGPT / OpenAI API bridge for the orchestra desk.

This is platform.openai.com (`OPENAI_API_KEY`).
It is not the chatgpt.com Plus/Pro subscription, GPTs, Canvas, or Deep Research.

No secrets in git. No invented bodies. No browser cookies.
Without a key: print «חסר מפתח ChatGPT» and exit 2.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = "https://api.openai.com/v1"
MISSING_KEY = "חסר מפתח ChatGPT"
NO_BODY = "אין גוף"
SKIP_SUBSTR = (
    "embed",
    "whisper",
    "tts",
    "dall-e",
    "dalle",
    "audio",
    "realtime",
    "moderation",
    "transcribe",
    "search",
    "similarity",
    "babbage",
    "davinci",
    "ada",
    "image",
)
ORCHESTRA_SYSTEM = (
    "Velvet Factory HQ research desk. Hebrew product copy. "
    "Pickup Sderot only. WhatsApp 050-2517000. IG @velvets_cloud. "
    "Do not invent ₪ prices or Insights. Do not suggest auto-DM, boost, "
    "national shipping, or a second agent runtime. Concrete office improvements only."
)


class ChatGPTError(RuntimeError):
    """API or usage error. Message is safe to print (no key)."""


def api_key() -> str | None:
    raw = (os.environ.get("OPENAI_API_KEY") or os.environ.get("CHATGPT_API_KEY") or "").strip()
    return raw or None


def is_chat_model(row: dict[str, Any]) -> bool:
    name = str(row.get("id") or "").lower()
    if not name:
        return False
    if any(s in name for s in SKIP_SUBSTR):
        return False
    return name.startswith("gpt-") or name.startswith("o1") or name.startswith("o3") or name.startswith("o4")


def _preference_score(name: str, prefer_pro: bool) -> tuple[int, ...]:
    n = name.lower()
    m = re.search(r"gpt-(\d+)(?:\.(\d+))?", n)
    major = int(m.group(1)) if m else (3 if n.startswith("o") else 0)
    minor = int(m.group(2) or 0) if m else 0
    is_mini = "mini" in n or "nano" in n
    is_preview = "preview" in n or "exp" in n
    is_proish = (not is_mini) and ("pro" in n or n.startswith("o1") or n.startswith("o3") or n.startswith("o4") or "gpt-4" in n or "gpt-5" in n)
    match = (prefer_pro and is_proish) or ((not prefer_pro) and not is_mini)
    return (major, minor, 0 if is_mini else 1, 1 if match else 0, 0 if is_preview else 1)


def pick_chat_model(
    models: list[dict[str, Any]],
    *,
    prefer_pro: bool = False,
    requested: str | None = None,
) -> str:
    usable = [row for row in models if is_chat_model(row)]
    if requested:
        want = requested.strip()
        for row in usable:
            if str(row.get("id") or "") == want:
                return want
        for row in models:
            if str(row.get("id") or "") == want:
                return want
        raise ChatGPTError(f"model not on live list: {want}")
    if prefer_pro:
        pros = []
        for row in usable:
            n = str(row.get("id") or "").lower()
            if "mini" not in n and "nano" not in n:
                pros.append(row)
        if pros:
            usable = pros
    if not usable:
        raise ChatGPTError("no chat model on live list")
    best = max(usable, key=lambda row: _preference_score(str(row.get("id") or ""), prefer_pro))
    return str(best.get("id") or "")


def _request(path: str, key: str, *, data: bytes | None = None, timeout: int = 60) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    req = urllib.request.Request(
        f"{API_ROOT}{path}",
        data=data,
        headers=headers,
        method="POST" if data else "GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise ChatGPTError(f"HTTP {exc.code}: {body[:500]}") from exc
    except urllib.error.URLError as exc:
        raise ChatGPTError(f"network: {exc.reason}") from exc
    if not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ChatGPTError("API returned non-JSON") from exc
    if not isinstance(parsed, dict):
        raise ChatGPTError("API returned a non-object")
    return parsed


def list_models(key: str) -> list[dict[str, Any]]:
    payload = _request("/models", key)
    rows = payload.get("data") or []
    if not isinstance(rows, list):
        raise ChatGPTError("models list missing")
    return [row for row in rows if isinstance(row, dict)]


def extract_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices or not isinstance(choices[0], dict):
        err = payload.get("error") or {}
        if isinstance(err, dict) and err.get("message"):
            return f"{NO_BODY} ({err.get('message')})"
        return NO_BODY
    msg = choices[0].get("message") or {}
    content = msg.get("content") if isinstance(msg, dict) else None
    if isinstance(content, str) and content.strip():
        return content.strip()
    return NO_BODY


def chat_complete(
    key: str,
    model: str,
    prompt: str,
    *,
    system: str | None = None,
) -> dict[str, Any]:
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body = json.dumps({"model": model, "messages": messages}).encode("utf-8")
    return _request("/chat/completions", key, data=body)


def require_key() -> str:
    key = api_key()
    if not key:
        raise ChatGPTError(MISSING_KEY)
    return key


def cmd_status(_: argparse.Namespace) -> int:
    if api_key():
        print("ready (key in env, not printed)")
        print("product: OpenAI API — not chatgpt.com Plus/Pro subscription")
        return 0
    print(MISSING_KEY, file=sys.stderr)
    return 2


def cmd_models(_: argparse.Namespace) -> int:
    key = require_key()
    rows = list_models(key)
    usable = [str(r.get("id") or "") for r in rows if is_chat_model(r)]
    pick = pick_chat_model(rows)
    print(f"live_chat_models={len(usable)}")
    print(f"default={pick}")
    for name in usable:
        print(name)
    if not usable:
        print(NO_BODY, file=sys.stderr)
        return 1
    return 0


def _run_ask(args: argparse.Namespace, *, system: str | None) -> tuple[str, str]:
    key = require_key()
    rows = list_models(key)
    model = pick_chat_model(rows, prefer_pro=bool(args.pro), requested=args.model)
    payload = chat_complete(key, model, args.prompt, system=system)
    return model, extract_text(payload)


def cmd_ask(args: argparse.Namespace) -> int:
    model, text = _run_ask(args, system=args.system)
    print(f"model={model}")
    print(text)
    if text.startswith(NO_BODY):
        return 1
    return 0


def cmd_orchestra(args: argparse.Namespace) -> int:
    prompt = args.prompt
    if args.file:
        prompt = Path(args.file).read_text(encoding="utf-8")
    if not prompt:
        daily = ROOT / "packages" / "vfresearch" / "DAILY.md"
        prompt = daily.read_text(encoding="utf-8") if daily.is_file() else (
            "מה לבנות או לייעל עכשיו במשרד הקיים — בלי ₪ ובלי האק צמיחה."
        )
    args.prompt = prompt
    args.system = args.system or ORCHESTRA_SYSTEM
    model, text = _run_ask(args, system=args.system)
    day = datetime.now(timezone.utc).date().isoformat()
    out = ROOT / "packages" / "vfresearch" / "sources" / f"{day}-chatgpt-api.md"
    if args.out:
        out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    body = (
        f"# ChatGPT API orchestra\n\n"
        f"Date: {day}\n"
        f"Model: `{model}`\n"
        f"Product: OpenAI API — **not** chatgpt.com Plus/Pro subscription.\n\n"
        f"## Body\n\n{text}\n"
    )
    out.write_text(body, encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")
    print(f"model={model}")
    print(text)
    if text.startswith(NO_BODY):
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="OpenAI API orchestra bridge (not the ChatGPT Plus subscription).")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", help="Key present? Never prints the key.")
    sub.add_parser("models", help="List live chat models.")
    ask = sub.add_parser("ask", help="One chat.completions call.")
    ask.add_argument("prompt")
    ask.add_argument("--model", default=None)
    ask.add_argument("--pro", action="store_true")
    ask.add_argument("--system", default=None)
    orch = sub.add_parser("orchestra", help="06:15 ChatGPT desk via API; write vfresearch source.")
    orch.add_argument("prompt", nargs="?", default="")
    orch.add_argument("--file", default=None)
    orch.add_argument("--model", default=None)
    orch.add_argument("--pro", action="store_true")
    orch.add_argument("--system", default=None)
    orch.add_argument("--out", default=None)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "status":
            return cmd_status(args)
        if args.cmd == "models":
            return cmd_models(args)
        if args.cmd == "ask":
            return cmd_ask(args)
        if args.cmd == "orchestra":
            return cmd_orchestra(args)
        raise ChatGPTError(f"unknown command {args.cmd}")
    except ChatGPTError as exc:
        print(str(exc), file=sys.stderr)
        if MISSING_KEY in str(exc):
            return 2
        return 1


if __name__ == "__main__":
    sys.exit(main())
