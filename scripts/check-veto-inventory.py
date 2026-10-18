#!/usr/bin/env python3
"""Mechanical check for the 2026-10-18 veto inventory.

Every row's canonical_candidate_ids must be the alias-map match for the URL
on that row's own enclosing JSON object, never the previous or following item.
Read-only. No registry edits.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASE2 = ROOT / "docs" / "implementation" / "office-v2" / "phase2"
INVENTORY = PHASE2 / "veto-inventory-2026-10-18.json"
REPORT = PHASE2 / "veto-inventory-2026-10-18.md"
ALIAS = PHASE2 / "competitor-provenance-alias-map-2026-10-18.json"

SCAN_FILES = [
    "packages/vfe2b/catalog.json",
    "packages/vfe2b/orchestrators.json",
    "packages/vfe2b/LOCK.md",
    "packages/vfe2b/DEER-FLOW-PATTERNS.md",
    "packages/vfe2b/ORCHESTRATORS.md",
    "packages/vfresearch/LINKS.json",
]
SKIP_KEYS = {"title", "pattern", "id", "rule", "item", "kind", "url"}
VOCAB = {
    ("packages/vfe2b/catalog.json", 34),
    ("packages/vfe2b/orchestrators.json", 39),
}
MATCH_STATUSES = {
    "MATCHED_STRONG",
    "MATCHED_BY_URL",
    "AMBIGUOUS_STRONG",
    "AMBIGUOUS_URL",
}
URL_RE = re.compile(r'"url"\s*:\s*"((?:\\.|[^"\\])*)"')
KEY_RE = re.compile(r'"([A-Za-z0-9_\-]+)"\s*:')

# url sits AFTER the veto text. Nearest-preceding url binds Beta to Alpha.
SHIFT_FIXTURE = """[
  {
    "name": "Alpha",
    "verdict": "veto",
    "url": "https://github.com/alpha/alpha"
  },
  {
    "name": "Beta",
    "verdict": "veto",
    "url": "https://github.com/beta/beta"
  }
]
"""
SHIFT_ALIAS = {
    "https://github.com/alpha/alpha": ["candidate-alpha"],
    "https://github.com/beta/beta": ["candidate-beta"],
}


def fail(message: str) -> None:
    print(f"FAIL veto-inventory {message}", file=sys.stderr)
    raise SystemExit(1)


def nearest_preceding_url(lines: list[str], line: int) -> str | None:
    """The binding this check exists to reject when url follows the veto text."""
    match = URL_RE.search(lines[line - 1])
    if match:
        return match.group(1)
    for index in range(line - 2, -1, -1):
        match = URL_RE.search(lines[index])
        if match:
            return match.group(1)
    return None


def _string_at(text: str, index: int) -> tuple[str, int]:
    chars: list[str] = []
    while index < len(text):
        char = text[index]
        if char == "\\":
            if index + 1 < len(text):
                chars.append(text[index + 1])
                index += 2
                continue
        if char == '"':
            return "".join(chars), index + 1
        chars.append(char)
        index += 1
    return "".join(chars), index


def top_level_url(obj: str) -> str | None:
    """Return the url value owned by this object, ignoring nested objects."""
    if not obj or obj[0] != "{":
        return None
    index = 1
    depth = 1
    limit = len(obj)
    while index < limit - 1 and depth >= 1:
        char = obj[index]
        if char == '"':
            literal, index = _string_at(obj, index + 1)
            if depth == 1:
                cursor = index
                while cursor < limit and obj[cursor] in " \t\r\n":
                    cursor += 1
                if cursor < limit and obj[cursor] == ":":
                    cursor += 1
                    while cursor < limit and obj[cursor] in " \t\r\n":
                        cursor += 1
                    if literal == "url" and cursor < limit and obj[cursor] == '"':
                        value, _ = _string_at(obj, cursor + 1)
                        return value
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                break
        index += 1
    return None


def enclosing_url(text: str, line: int) -> str | None:
    """URL of the innermost enclosing object that has its own url key."""
    lines = text.splitlines(keepends=True)
    if line < 1 or line > len(lines):
        return None
    raw = lines[line - 1]
    pad = len(raw) - len(raw.lstrip(" \t"))
    pos = sum(len(lines[i]) for i in range(line - 1)) + pad
    spans: list[int] = []
    objects: list[tuple[int, int]] = []
    index = 0
    in_string = False
    escaped = False
    while index < len(text):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            spans.append(index)
        elif char == "}" and spans:
            start = spans.pop()
            objects.append((start, index + 1))
        index += 1
    containing = [(start, end) for start, end in objects if start <= pos < end]
    containing.sort(key=lambda span: span[1] - span[0])
    for start, end in containing:
        url = top_level_url(text[start:end])
        if url is not None:
            return url
    return None


def key_for_span(line: str, start: int) -> str | None:
    keys = list(KEY_RE.finditer(line[:start]))
    return keys[-1].group(1) if keys else None


def ids_from(entries: list[dict]) -> list[str]:
    found: list[str] = []
    for entry in entries:
        if entry["status"] not in MATCH_STATUSES:
            continue
        for candidate in list(entry["url_matches"]) + list(entry["strong"]):
            if candidate not in found:
                found.append(candidate)
    return found


def expected_ids(text: str, row: dict, by_url: dict, by_label: dict) -> list[str]:
    url = enclosing_url(text, row["line"]) if row["file"].endswith(".json") else None
    if url is not None:
        return ids_from(by_url.get(url, []))
    if row.get("item"):
        return ids_from(by_label.get(row["item"], []))
    return []


def split_md_row(line: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    index = 0
    while index < len(line):
        if line[index] == "\\" and index + 1 < len(line):
            buf.append(line[index:index + 2])
            index += 2
            continue
        if line[index] == "|":
            parts.append("".join(buf))
            buf = []
            index += 1
            continue
        buf.append(line[index])
        index += 1
    parts.append("".join(buf))
    return parts


def shift_regression() -> None:
    """Fail if candidate IDs are taken from the previous item.

    On this fixture the veto text precedes url, so nearest-preceding url
    assigns Beta the Alpha id. Enclosing-object binding must not.
    """
    lines = SHIFT_FIXTURE.splitlines()
    veto_lines = [number for number, line in enumerate(lines, 1) if '"verdict": "veto"' in line]
    if len(veto_lines) != 2:
        fail("shift fixture lost its two veto lines")
    alpha_line, beta_line = veto_lines
    by_url = {
        url: [{"status": "MATCHED_BY_URL", "url_matches": ids, "strong": []}]
        for url, ids in SHIFT_ALIAS.items()
    }

    def bound(line: int) -> list[str]:
        url = enclosing_url(SHIFT_FIXTURE, line)
        return ids_from(by_url.get(url or "", []))

    def shifted(line: int) -> list[str]:
        url = nearest_preceding_url(lines, line)
        return ids_from(by_url.get(url or "", []))

    if bound(alpha_line) != ["candidate-alpha"]:
        fail(f"url-after-text object bound {bound(alpha_line)} instead of its own id")
    if bound(beta_line) != ["candidate-beta"]:
        fail(f"enclosing object bound Beta to {bound(beta_line)}")
    if shifted(beta_line) != ["candidate-alpha"]:
        fail(f"shift fixture no longer reproduces a moved id: {shifted(beta_line)}")
    if bound(beta_line) == shifted(beta_line):
        fail("shifted id was accepted")


def main() -> int:
    shift_regression()
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    alias = json.loads(ALIAS.read_text(encoding="utf-8"))
    by_url: dict[str, list] = {}
    by_label: dict[str, list] = {}
    for entry in alias["rows"]:
        by_url.setdefault(entry["url"], []).append(entry)
        by_label.setdefault(entry["label"], []).append(entry)
    veto = re.compile(inventory["regexes"]["veto"], re.I)
    blocker = re.compile(inventory["regexes"]["blocker"], re.I)
    citation = re.compile(inventory["regexes"]["citation"], re.I)
    source_text = {rel: (ROOT / rel).read_text(encoding="utf-8") for rel in SCAN_FILES}
    source = {rel: text.splitlines() for rel, text in source_text.items()}

    kept: list[tuple[str, int, str]] = []
    dropped = 0
    for rel in SCAN_FILES:
        for number, line in enumerate(source[rel], 1):
            matches = list(veto.finditer(line))
            if not matches:
                continue
            keys = [key_for_span(line, match.start()) for match in matches]
            if keys and all(key in SKIP_KEYS for key in keys):
                dropped += 1
                continue
            kept.append((rel, number, line.strip()))
    if dropped != 7 or len(kept) != 77:
        fail(f"scan drifted dropped={dropped} kept={len(kept)}")
    included = [row for row in kept if (row[0], row[1]) not in VOCAB]
    rows = inventory["rows"]
    if len(included) != len(rows):
        fail(f"row count {len(rows)} != scanned {len(included)}")
    for rel, number in VOCAB:
        if any(row["file"] == rel and row["line"] == number for row in rows):
            fail(f"vocabulary line {rel}:{number} must not be a row and must not carry candidate ids")

    id_mismatches = 0
    for row, (rel, number, quote) in zip(rows, included):
        if (row["file"], row["line"]) != (rel, number):
            fail(f"order {row['file']}:{row['line']} != {rel}:{number}")
        if quote != row["quote"] and not quote.startswith(row["quote"]):
            fail(f"quote {rel}:{number}")
        has_blocker = bool(blocker.search(quote))
        has_citation = bool(citation.search(quote))
        expect_class = "EVIDENCE_BACKED_BLOCKER" if has_blocker and has_citation else "EVIDENCE_FREE_VETO"
        if row["class"] != expect_class:
            fail(f"class {rel}:{number}")
        if row["blocker_term_without_citation"] != (has_blocker and not has_citation):
            fail(f"flag {rel}:{number}")
        expect = expected_ids(source_text[rel], row, by_url, by_label)
        if row["canonical_candidate_ids"] != expect:
            id_mismatches += 1
            print(
                f"FAIL id {rel}:{number} {row['item']!r} "
                f"report={row['canonical_candidate_ids']} enclosing={expect}",
                file=sys.stderr,
            )
    if id_mismatches:
        fail(f"{id_mismatches} candidate-id rows are not this item's enclosing object match")

    summary = inventory["summary"]
    with_ids = sum(1 for row in rows if row["canonical_candidate_ids"])
    if summary["rows"] != len(rows) or summary["rows_with_canonical_candidate_id"] != with_ids:
        fail(f"summary rows={summary['rows']} with_ids={summary['rows_with_canonical_candidate_id']} actual={with_ids}")
    if summary["EVIDENCE_BACKED_BLOCKER"] != sum(1 for row in rows if row["class"] == "EVIDENCE_BACKED_BLOCKER"):
        fail("summary backed count")
    if summary["regex_lines_after_description_skip"] != 77 or summary["excluded_vocabulary_lines"] != 2:
        fail("summary coverage")

    backed = [
        index for index, row in enumerate(rows, 1)
        if row.get("item") == "Archon" and row["class"] == "EVIDENCE_BACKED_BLOCKER"
    ]
    if backed != [31]:
        fail(f"Archon backed row numbers {backed}, expected [31]")

    method = inventory["method"]
    candidate_clause = method.split("Candidate IDs", 1)[-1]
    if "enclosing JSON object" not in method or "nearest preceding" in candidate_clause:
        fail("method must describe enclosing-object binding")
    if "scripts/check-veto-inventory.py" not in method:
        fail("method must point at the check-all sensor")

    report = REPORT.read_text(encoding="utf-8")
    if f"Rows with a canonical candidate ID: {with_ids}." not in report:
        fail("markdown candidate count")
    if "enclosing JSON object" not in report:
        fail("markdown must describe enclosing-object binding")
    if "Row 31 (Archon)" not in report or "row 23" in report or "Row 23" in report:
        fail("Archon prose row reference")
    archon_cells = [
        line for line in report.splitlines()
        if line.startswith("| 31 |") and "Archon" in line and "curl" in line
    ]
    evidence = [
        line for line in archon_cells
        if len(split_md_row(line)) == 7 and split_md_row(line)[4].strip() == "curl\\|bash"
    ]
    if len(evidence) != 1 or any("curl\\|bash" not in line for line in archon_cells):
        fail("Archon basis pipe must stay escaped so the markdown cell does not split")
    in_all = False
    md_rows = 0
    for line in report.splitlines():
        if line.startswith("## All rows"):
            in_all = True
            continue
        if in_all and line.startswith("## "):
            break
        if not in_all or not line.startswith("|") or line.startswith("|---") or line.startswith("| #"):
            continue
        parts = split_md_row(line)
        ids = [part.strip() for part in parts[5].split(",") if part.strip() and part.strip() != "-"]
        if ids != rows[md_rows]["canonical_candidate_ids"]:
            fail(f"markdown ids row {md_rows + 1} {ids} != {rows[md_rows]['canonical_candidate_ids']}")
        md_rows += 1
    if md_rows != len(rows):
        fail(f"markdown table rows {md_rows}")

    print(
        "OK veto-inventory "
        f"rows={len(rows)} coverage=77-2 candidate_ids={with_ids} "
        "object_url_join=PASS shifted_next_item=0 vocab_ids=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
