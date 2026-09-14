#!/usr/bin/env python3
"""Normalize and validate Hebrew/English BiDi rendering in README.md.

GitHub chooses paragraph direction from surrounding text and mixed Hebrew/Latin
lines can reorder punctuation, labels and inline technical terms. This script:
- adds an RTL mark to Hebrew-dominant Markdown lines in the Hebrew section;
- sets RTL direction on HTML table cells that contain Hebrew;
- keeps English/status-only cells untouched (LTR by content);
- gives both language sections explicit stable anchors;
- supports --check so CI can reject rendering regressions.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
RLM = "\u200f"
HEBREW = re.compile(r"[\u0590-\u05FF]")
TD = re.compile(r"<td(?![^>]*\bdir=)([^>]*)>(.*?)</td>", re.S | re.I)
BIDI_MARKS = "\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
HEBREW_ANCHOR = '<a id="hebrew"></a>'
ENGLISH_ANCHOR = '<a id="english"></a>'


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

    for prefix in ("###### ", "##### ", "#### ", "### ", "## ", "# ", "- ", "> "):
        if stripped.startswith(prefix):
            return indent + prefix + RLM + stripped[len(prefix):]

    if stripped.startswith("|"):
        return indent + "|" + RLM + stripped[1:]

    if stripped.startswith("<"):
        return line

    return indent + RLM + stripped


def find_h1(text: str, label: str) -> int:
    match = re.search(rf"(?m)^# [{re.escape(BIDI_MARKS)}]*{re.escape(label)}[ \t]*$", text)
    return -1 if match is None else match.start()


def ensure_language_anchors(text: str) -> str:
    text = text.replace('<a href="#עברית">עברית</a>', '<a href="#hebrew">עברית</a>')

    he_match = re.search(rf"(?m)^# [{re.escape(BIDI_MARKS)}]*עברית[ \t]*$", text)
    if he_match is None:
        raise SystemExit("README Hebrew section marker not found")
    he_prefix = text[max(0, he_match.start() - len(HEBREW_ANCHOR) - 3):he_match.start()]
    if HEBREW_ANCHOR not in he_prefix:
        text = text[:he_match.start()] + HEBREW_ANCHOR + "\n\n" + text[he_match.start():]

    en_match = re.search(r"(?m)^# English[ \t]*$", text)
    if en_match is None:
        raise SystemExit("README English section marker not found")
    en_prefix = text[max(0, en_match.start() - len(ENGLISH_ANCHOR) - 3):en_match.start()]
    if ENGLISH_ANCHOR not in en_prefix:
        text = text[:en_match.start()] + ENGLISH_ANCHOR + "\n\n" + text[en_match.start():]
    return text


def normalize(text: str) -> str:
    text = ensure_language_anchors(text)
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


def validate(text: str) -> list[str]:
    issues: list[str] = []
    if text.count(HEBREW_ANCHOR) != 1:
        issues.append("expected exactly one explicit #hebrew anchor")
    if text.count(ENGLISH_ANCHOR) != 1:
        issues.append("expected exactly one explicit #english anchor")
    if '<a href="#hebrew">עברית</a>' not in text:
        issues.append("top language navigation must link Hebrew to #hebrew")
    if '<a href="#english">English</a>' not in text:
        issues.append("top language navigation must link English to #english")
    if 'href="#עברית"' in text:
        issues.append("legacy implicit Hebrew anchor is still referenced")

    start = find_h1(text, "עברית")
    end = find_h1(text, "English")
    if start < 0 or end < 0 or end <= start:
        issues.append("Hebrew/English section markers are invalid")
        return issues

    hebrew = text[start:end]
    for match in re.finditer(r"<td([^>]*)>(.*?)</td>", hebrew, re.S | re.I):
        attrs, body = match.group(1), match.group(2)
        if has_hebrew(body) and 'dir="rtl"' not in attrs:
            issues.append("Hebrew HTML table cell missing dir=rtl")
            break
    return issues


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    current = README.read_text(encoding="utf-8")
    fixed = normalize(current)
    issues = validate(fixed)

    if args.check:
        if current != fixed:
            print("FAIL README Hebrew BiDi is not normalized. Run: python3 scripts/fix-readme-bidi.py")
            return 1
        if issues:
            for issue in issues:
                print(f"FAIL {issue}")
            return 1
        print("OK README Hebrew BiDi and language anchors are valid")
        return 0

    if issues:
        for issue in issues:
            print(f"FAIL {issue}")
        return 1
    if fixed == current:
        print("OK README BiDi already normalized")
        return 0
    README.write_text(fixed, encoding="utf-8")
    print("OK README Hebrew BiDi normalized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
