#!/usr/bin/env python3
"""Normalize Hebrew/English BiDi rendering in README.md without breaking Markdown.

GitHub chooses paragraph direction from surrounding text and mixed Hebrew/Latin
lines can reorder punctuation, labels and inline technical terms. This script:
- adds an RTL mark to Hebrew-dominant Markdown lines in the Hebrew section;
- sets RTL direction on HTML table cells that contain Hebrew;
- keeps English/status-only cells untouched (LTR by content).

The transformation is idempotent and display-only.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
RLM = "\u200f"
HEBREW = re.compile(r"[\u0590-\u05FF]")
TD = re.compile(r"<td(?![^>]*\bdir=)([^>]*)>(.*?)</td>", re.S | re.I)
BIDI_MARKS = "\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"


def has_hebrew(text: str) -> bool:
    return bool(HEBREW.search(text))


def fix_html_cells(line: str) -> str:
    def repl(match: re.Match[str]) -> str:
        attrs, body = match.group(1), match.group(2)
        if not has_hebrew(body):
            return match.group(0)
        return f'<td dir="rtl" align="right"{attrs}>{body}</td>'

    return TD.sub(repl, line)


def add_rlm(line: str) -> str:
    if not has_hebrew(line) or RLM in line[:8]:
        return line
    stripped = line.lstrip()
    indent = line[: len(line) - len(stripped)]

    # Keep structural Markdown characters in front, put the direction mark at
    # the beginning of the visible text.
    for prefix in ("###### ", "##### ", "#### ", "### ", "## ", "# ", "- ", "> "):
        if stripped.startswith(prefix):
            return indent + prefix + RLM + stripped[len(prefix):]

    # Markdown table rows: the cells determine direction individually; adding
    # RLM immediately after the first pipe stabilizes Hebrew-first rows.
    if stripped.startswith("|"):
        return indent + "|" + RLM + stripped[1:]

    # Raw HTML gets explicit dir attributes instead of paragraph marks.
    if stripped.startswith("<"):
        return line

    return indent + RLM + stripped


def find_h1(text: str, label: str) -> int:
    match = re.search(rf"(?m)^# [{re.escape(BIDI_MARKS)}]*{re.escape(label)}[ \t]*$", text)
    return -1 if match is None else match.start()


def normalize(text: str) -> str:
    start = find_h1(text, "עברית")
    end = find_h1(text, "English")
    if start < 0 or end < 0 or end <= start:
        raise SystemExit("README Hebrew/English section markers not found")

    before, hebrew, after = text[:start], text[start:end], text[end:]
    in_fence = False
    out: list[str] = []
    for line in hebrew.splitlines(keepends=True):
        bare = line.rstrip("\r\n")
        ending = line[len(bare):]
        if bare.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        fixed = fix_html_cells(bare)
        fixed = add_rlm(fixed)
        out.append(fixed + ending)
    return before + "".join(out) + after


def main() -> int:
    current = README.read_text(encoding="utf-8")
    fixed = normalize(current)
    if fixed == current:
        print("OK README BiDi already normalized")
        return 0
    README.write_text(fixed, encoding="utf-8")
    print("OK README Hebrew BiDi normalized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
