#!/usr/bin/env python3
"""Gemini API bridge for the orchestra desk.

This is Google AI Studio / Gemini API (`GEMINI_API_KEY`).
It is not the gemini.google.com Plus/Advanced subscription, Gems, Canvas,
Deep Research, or Workspace connected apps.

No secrets in git. No invented bodies. No Veo from HQ.
Without a key: print «חסר מפתח Gemini» and exit 2.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = "https://generativelanguage.googleapis.com/v1beta"
MISSING_KEY = "חסר מפתח Gemini"
NO_BODY = "אין גוף"
SKIP_SUBSTR = (
    "embed",
    "veo",
    "aqa",
    "gecko",
    "tts",
    "robotics",
    "imagen",
    "image",
    "computer-use",
    "lyria",
)
ORCHESTRA_SYSTEM = (
    "Velvet Factory HQ research desk. Hebrew product copy. "
    "Pickup Sderot only. WhatsApp 050-2517000. IG @velvets_cloud. "
    "Do not invent ₪ prices or Insights. Do not suggest auto-DM, boost, "
    "national shipping, or a second agent runtime. Concrete office improvements only."
)


class GeminiError(RuntimeError):
    """API or usage error. Message is safe to print (no key)."""


def api_key() -> str | None:
    raw = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
    return raw or None


def short_name(name: str) -> str:
    n = (name or "").strip()
    if n.startswith("models/"):
        return n[len("models/") :]
    return n


def parse_version(name: str) -> tuple[int, int]:
    n = short_name(name).lower()
    m = re.search(r"gemini-(\d+)(?:\.(\d+))?", n)
    if not m:
        return (0, 0)
    return (int(m.group(1)), int(m.group(2) or 0))


def is_text_generate_model(row: dict[str, Any]) -> bool:
    name = short_name(str(row.get("name") or "")).lower()
    if not name.startswith("gemini-"):
        return False
    methods = [str(x) for x in (row.get("supportedGenerationMethods") or [])]
    if methods and "generateContent" not in methods:
        return False
    return not any(s in name for s in SKIP_SUBSTR)


def _preference_score(name: str, prefer_pro: bool) -> tuple[int, ...]:
    n = short_name(name).lower()
    major, minor = parse_version(n)
    is_lite = "lite" in n
    is_preview = "preview" in n or "exp" in n
    is_flash = "flash" in n
    is_pro = ("pro" in n) and not is_flash
    match = (prefer_pro and is_pro) or ((not prefer_pro) and is_flash)
    return (
        major,
        minor,
        0 if is_lite else 1,
        1 if match else 0,
        0 if is_preview else 1,
    )


def pick_generate_model(
    models: list[dict[str, Any]],
    *,
    prefer_pro: bool = False,
    requested: str | None = None,
) -> str:
    usable = [row for row in models if is_text_generate_model(row)]
    if requested:
        want = short_name(requested)
        for row in usable:
            if short_name(str(row.get("name") or "")) == want:
                return want
        for row in models:
            if short_name(str(row.get("name") or "")) == want:
                return want
        raise GeminiError(f"model not on live list: {want}")
    if prefer_pro:
        pros = []
        for row in usable:
            n = short_name(str(row.get("name") or "")).lower()
            if "pro" in n and "flash" not in n:
                pros.append(row)
        if pros:
            usable = pros
    if not usable:
        raise GeminiError("no generateContent Gemini text model on live list")
    best = max(usable, key=lambda row: _preference_score(str(row.get("name") or ""), prefer_pro))
    return short_name(str(best.get("name") or ""))


def _request(url: str, *, data: bytes | None = None, timeout: int = 60) -> dict[str, Any]:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GeminiError(f"HTTP {exc.code}: {body[:500]}") from exc
    except urllib.error.URLError as exc:
        raise GeminiError(f"network: {exc.reason}") from exc
    if not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GeminiError("API returned non-JSON") from exc
    if not isinstance(parsed, dict):
        raise GeminiError("API returned a non-object")
    return parsed


def _url(path: str, key: str, **extra: str) -> str:
    q = {"key": key, **extra}
    return f"{API_ROOT}{path}?{urllib.parse.urlencode(q)}"


def list_models(key: str) -> list[dict[str, Any]]:
    payload = _request(_url("/models", key))
    rows = payload.get("models") or []
    if not isinstance(rows, list):
        raise GeminiError("models list missing")
    return [row for row in rows if isinstance(row, dict)]


def extract_text(payload: dict[str, Any]) -> str:
    prompt_feedback = payload.get("promptFeedback") or {}
    block = prompt_feedback.get("blockReason")
    cands = payload.get("candidates") or []
    if not cands:
        if block:
            return f"{NO_BODY} ({block})"
        return NO_BODY
    cand = cands[0] if isinstance(cands[0], dict) else {}
    finish = str(cand.get("finishReason") or "")
    parts = ((cand.get("content") or {}).get("parts")) or []
    texts: list[str] = []
    for part in parts:
        if isinstance(part, dict) and isinstance(part.get("text"), str):
            texts.append(part["text"])
    body = "\n".join(texts).strip()
    if body:
        return body
    if finish and finish not in {"STOP", "MAX_TOKENS"}:
        return f"{NO_BODY} ({finish})"
    return NO_BODY


def generate_content(
    key: str,
    model: str,
    prompt: str,
    *,
    system: str | None = None,
    ground: bool = False,
    json_mode: bool = False,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
    }
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    if ground:
        body["tools"] = [{"google_search": {}}]
    if json_mode:
        body["generationConfig"] = {"responseMimeType": "application/json"}
    path = f"/models/{urllib.parse.quote(short_name(model), safe='.-')}:generateContent"
    return _request(_url(path, key), data=json.dumps(body).encode("utf-8"))


def require_key() -> str:
    key = api_key()
    if not key:
        raise GeminiError(MISSING_KEY)
    return key


def cmd_status(_: argparse.Namespace) -> int:
    if api_key():
        print("ready (key in env, not printed)")
        print("product: Gemini API / AI Studio — not gemini.google.com subscription")
        return 0
    print(MISSING_KEY)
    return 2


def cmd_models(_: argparse.Namespace) -> int:
    key = require_key()
    rows = list_models(key)
    usable = [short_name(str(r.get("name") or "")) for r in rows if is_text_generate_model(r)]
    pick = pick_generate_model(rows)
    pick_pro = pick_generate_model(rows, prefer_pro=True)
    print(f"live_text_models={len(usable)}")
    print(f"default_flash={pick}")
    print(f"default_pro={pick_pro}")
    for name in usable:
        print(name)
    if not usable:
        print(NO_BODY)
        return 1
    return 0


def _run_ask(args: argparse.Namespace, *, system: str | None) -> tuple[str, str]:
    key = require_key()
    rows = list_models(key)
    model = pick_generate_model(rows, prefer_pro=bool(args.pro), requested=args.model)
    try:
        payload = generate_content(
            key,
            model,
            args.prompt,
            system=system,
            ground=bool(args.ground),
            json_mode=bool(args.json),
        )
    except GeminiError as exc:
        if args.ground and "google_search" in str(exc).lower():
            payload = generate_content(
                key,
                model,
                args.prompt,
                system=system,
                ground=False,
                json_mode=bool(args.json),
            )
        else:
            raise
    text = extract_text(payload)
    return model, text


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
    out = ROOT / "packages" / "vfresearch" / "sources" / f"{day}-gemini-api.md"
    if args.out:
        out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    body = (
        f"# Gemini API orchestra\n\n"
        f"Date: {day}\n"
        f"Model: `{model}`\n"
        f"Product: Gemini API / AI Studio — **not** gemini.google.com subscription.\n"
        f"Grounding: {'on' if args.ground else 'off'}\n\n"
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
    p = argparse.ArgumentParser(description="Gemini API orchestra bridge (not the consumer subscription).")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Key present? Never prints the key.")
    sub.add_parser("models", help="List live generateContent text models.")

    ask = sub.add_parser("ask", help="One generateContent call.")
    ask.add_argument("prompt")
    ask.add_argument("--model", default=None)
    ask.add_argument("--pro", action="store_true")
    ask.add_argument("--ground", action="store_true")
    ask.add_argument("--json", action="store_true")
    ask.add_argument("--system", default=None)

    orch = sub.add_parser("orchestra", help="06:15 Gemini desk via API; write vfresearch source.")
    orch.add_argument("prompt", nargs="?", default="")
    orch.add_argument("--file", default=None)
    orch.add_argument("--model", default=None)
    orch.add_argument("--pro", action="store_true")
    orch.add_argument("--ground", action="store_true", default=True)
    orch.add_argument("--no-ground", action="store_false", dest="ground")
    orch.add_argument("--json", action="store_true")
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
        raise GeminiError(f"unknown command {args.cmd}")
    except GeminiError as exc:
        print(str(exc), file=sys.stderr)
        if MISSING_KEY in str(exc):
            return 2
        if NO_BODY in str(exc):
            return 1
        return 1


if __name__ == "__main__":
    sys.exit(main())
