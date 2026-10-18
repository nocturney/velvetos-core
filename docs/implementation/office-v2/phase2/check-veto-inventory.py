#!/usr/bin/env python3
"""Mechanical check for the 2026-10-18 veto inventory.

Confirms coverage against the published regexes and that every row's
canonical_candidate_ids is the alias-map match for that row's own URL,
never the following item's. Read-only. No registry edits.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PHASE2 = Path(__file__).resolve().parent
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


def fail(message: str) -> None:
    print(f"FAIL veto-inventory {message}", file=sys.stderr)
    raise SystemExit(1)


def own_url(lines: list[str], line: int) -> str | None:
    match = URL_RE.search(lines[line - 1])
    if match:
        return match.group(1)
    for index in range(line - 2, -1, -1):
        match = URL_RE.search(lines[index])
        if match:
            return match.group(1)
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


def expected_ids(row: dict, source: dict[str, list[str]], by_url: dict, by_label: dict) -> list[str]:
    url = own_url(source[row["file"]], row["line"])
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


def main() -> int:
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
    source = {rel: (ROOT / rel).read_text(encoding="utf-8").splitlines() for rel in SCAN_FILES}

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
        expect = expected_ids(row, source, by_url, by_label)
        if row["canonical_candidate_ids"] != expect:
            id_mismatches += 1
            print(
                f"FAIL id {rel}:{number} {row['item']!r} "
                f"report={row['canonical_candidate_ids']} own={expect}",
                file=sys.stderr,
            )
    if id_mismatches:
        fail(f"{id_mismatches} candidate-id rows are not this item's own URL/label match")

    summary = inventory["summary"]
    with_ids = sum(1 for row in rows if row["canonical_candidate_ids"])
    if summary["rows"] != len(rows) or summary["rows_with_canonical_candidate_id"] != with_ids:
        fail(f"summary rows={summary['rows']} with_ids={summary['rows_with_canonical_candidate_id']} actual={with_ids}")
    if summary["EVIDENCE_BACKED_BLOCKER"] != sum(1 for row in rows if row["class"] == "EVIDENCE_BACKED_BLOCKER"):
        fail("summary backed count")
    if summary["regex_lines_after_description_skip"] != 77 or summary["excluded_vocabulary_lines"] != 2:
        fail("summary coverage")

    report = REPORT.read_text(encoding="utf-8")
    if f"Rows with a canonical candidate ID: {with_ids}." not in report:
        fail("markdown candidate count")
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
        "own_url_join=PASS shifted_next_item=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
