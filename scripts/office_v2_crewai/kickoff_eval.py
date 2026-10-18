#!/usr/bin/env python3
"""Score saved CrewAI kickoff outputs offline.

Pure stdlib. No node, network, or model call, and no third-party eval
runner. Does not import the crew builder. The four checks are the
ChatGPT-066 javascript assertions (issue 612 comment 6252298649), with
the customer matcher narrowed so a generic plural explanation is not an
identified customer. English customer and client matching ignores case.
A hyphenated client-side token is not an identified customer. Shekel
abbreviations use Hebrew-letter boundaries, including inside a longer
word. Every directory entry is classified before any name is skipped.
Symlinks and other non-regular entries are refused and are not read.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "kickoff_fixtures" / "cases.json"
GOOD_DIR = HERE / "kickoff_samples" / "good"
BAD_DIR = HERE / "kickoff_samples" / "bad"
ISSUE_URL = re.compile(
    r"https://github\.com/nocturney/velvetos-core/issues/\d+"
)
PREFIX = "https://github.com/nocturney/velvetos-core/issues/"

# Assertion 4 exact substrings from the ChatGPT-066 javascript checks.
H_SUMMARY = "## \u05e1\u05d9\u05db\u05d5\u05dd"
H_BLOCKERS = (
    "## \u05d7\u05e1\u05de\u05d9\u05dd \u05d5\u05e6\u05e2\u05d3\u05d9\u05dd \u05d4\u05d1\u05d0\u05d9\u05dd"
)
H_ROW = (
    "| Issue URL | \u05d7\u05e1\u05dd | \u05d1\u05e2\u05dc\u05d9\u05dd | "
    "\u05e6\u05e2\u05d3 \u05d4\u05d1\u05d0 |"
)

# Money check keeps the original ignore-case tokens. Shekel abbreviations
# need Hebrew-letter boundaries so they do not match inside ordinary words.
MONEY = re.compile(
    "\u20aa|\\b(?:ILS|NIS)\\b|"
    "(?<![\u0590-\u05ff])\u05e9[\"\u05f4]?\u05d7(?![\u0590-\u05ff])|"
    "\u05e9\u05e7\u05dc\u05d9\u05dd",
    re.IGNORECASE,
)
# Original customer check. The optional Hebrew suffix also matched the
# generic plural, which ChatGPT-066 recorded as an overbroad failure.
LEGACY_CUSTOMER = re.compile(
    "\\b(?:customer|client)\\b|"
    "\u05dc\u05e7\u05d5\u05d7(?:\u05d4|\u05d9\u05dd|\u05d5\u05ea)?|"
    "\\bDana\\b|\u05d3\u05e0\u05d4"
)
# Narrowed: named or identified customer. Generic \u05dc\u05e7\u05d5\u05d7\u05d5\u05ea
# (and the other generic plural) does not count.
# English customer/client ignores case. Dana stays case-sensitive.
# A hyphen after the word keeps client-side and Client-side out.
NARROW_CUSTOMER = re.compile(
    "(?i:\\b(?:customer|client)\\b(?!-))|\\bDana\\b|"
    "(?<![\u0590-\u05ff])\u05d3\u05e0\u05d4(?![\u0590-\u05ff])|"
    "\u05dc\u05e7\u05d5\u05d7\u05d4(?![\u0590-\u05ff])|"
    "\u05dc\u05e7\u05d5\u05d7(?![\u0590-\u05ff])"
)
BLANK_CELL = re.compile(r"(?:n/?a|unknown|none|-|)", re.IGNORECASE)
EMPTY_TABLE = re.compile(
    r"no rows were provided|no issue rows|\|\s*n/?a\s*\|\s*n/?a\s*\|",
    re.IGNORECASE,
)
GENERIC_PLURAL = "\u05dc\u05e7\u05d5\u05d7\u05d5\u05ea"
DANA_HE = "\u05d3\u05e0\u05d4"
SHEKEL = "\u20aa"


def load_cases(path: Path = FIXTURES) -> list[dict]:
    document = json.loads(path.read_text(encoding="utf-8"))
    cases = document.get("cases") if isinstance(document, dict) else None
    if not isinstance(cases, list):
        raise ValueError("fixtures cases must be a list")
    return cases


def assert_url_coverage(output: str, issues: list[dict]) -> tuple[bool, str]:
    urls = [row["url"] for row in issues]
    missing = [url for url in urls if url not in output]
    cited = ISSUE_URL.findall(output)
    extra = [url for url in cited if url not in urls]
    ok = not missing and not extra
    reason = "Missing: " + ", ".join(missing) + "; Extra: " + ", ".join(extra)
    return ok, reason


def _detail_blank(cell: str) -> bool:
    return BLANK_CELL.fullmatch(cell.strip()) is not None


def assert_not_blank_table(output: str, issues: list[dict]) -> tuple[bool, str]:
    del issues
    lines = [line for line in re.split(r"\r?\n", output) if "|" in line]
    rows = [line for line in lines if ISSUE_URL.search(line)]
    all_blank = (not rows) or all(
        all(_detail_blank(cell) for cell in line.split("|")[2:]) for line in rows
    )
    empty = EMPTY_TABLE.search(output) is not None
    return (not all_blank) and (not empty), (
        "Empty/only N/A table=%s; empty text=%s" % (all_blank, empty)
    )


def assert_no_money_customer(output: str, issues: list[dict]) -> tuple[bool, str]:
    del issues
    money = MONEY.search(output) is not None
    customer = NARROW_CUSTOMER.search(output) is not None
    return (not money) and (not customer), (
        "Unfounded monetary claim=%s; customer claim=%s" % (money, customer)
    )


def assert_hebrew_table(output: str, issues: list[dict]) -> tuple[bool, str]:
    lines = re.split(r"\r?\n", output)
    data = [
        line for line in lines
        if line.strip().startswith("|") and ISSUE_URL.search(line)
    ]
    four = all(len([part for part in line.split("|") if part]) >= 4 for line in data)
    headers = H_SUMMARY in output and H_BLOCKERS in output and H_ROW in output
    urls = [row["url"] for row in issues]
    one_url = all(len(ISSUE_URL.findall(line)) == 1 for line in data)
    coverage = (
        all(any(url in line for line in data) for url in urls)
        and len(data) == len(urls)
        and one_url
    )
    return headers and four and coverage, (
        "Headers=%s, 4 columns=%s, data coverage=%s, rows=%s"
        % (headers, four, coverage, len(data))
    )


CHECKS = (
    ("url_coverage", assert_url_coverage),
    ("blank_table", assert_not_blank_table),
    ("money_customer", assert_no_money_customer),
    ("hebrew_table", assert_hebrew_table),
)


def score_output(output: str, issues: list[dict]) -> list[dict]:
    scored = []
    for name, check in CHECKS:
        ok, reason = check(output, issues)
        scored.append({"id": name, "pass": ok, "reason": reason})
    return scored


def failed_ids(scored: list[dict]) -> list[str]:
    return [row["id"] for row in scored if not row["pass"]]


def output_files(
    directory: Path, cases: list[dict]
) -> tuple[dict[str, Path], list[str], list[str], list[str], list[str]]:
    expected = {case["id"] for case in cases}
    found: dict[str, Path] = {}
    unexpected: list[str] = []
    symlinks: list[str] = []
    nonregular: list[str] = []
    if not directory.is_dir():
        raise ValueError("outputs path is not a directory: %s" % directory)
    for path in sorted(directory.iterdir(), key=lambda item: item.name):
        if path.is_symlink():
            symlinks.append(path.name)
            continue
        if not path.is_file():
            nonregular.append(path.name)
            continue
        stem = path.stem
        if (
            path.suffix.lower() not in {".md", ".txt"}
            or stem not in expected
            or stem in found
        ):
            unexpected.append(path.name)
            continue
        found[stem] = path
    missing = [case_id for case_id in sorted(expected) if case_id not in found]
    return found, missing, unexpected, symlinks, nonregular


def score_directory(directory: Path, cases: list[dict]) -> tuple[int, list[str]]:
    found, missing, unexpected, symlinks, nonregular = output_files(directory, cases)
    lines: list[str] = []
    failed = 0
    if symlinks:
        failed += 1
        lines.append("FAIL SYMLINK_REFUSED " + ", ".join(symlinks))
    if nonregular:
        failed += 1
        lines.append("FAIL NONREGULAR_REFUSED " + ", ".join(nonregular))
    if unexpected:
        failed += 1
        lines.append("FAIL unexpected outputs: " + ", ".join(unexpected))
    by_id = {case["id"]: case for case in cases}
    for case_id in sorted(by_id):
        if case_id not in found:
            continue
        text = found[case_id].read_text(encoding="utf-8")
        scored = score_output(text, by_id[case_id]["issues"])
        bad = failed_ids(scored)
        if bad:
            failed += 1
            reasons = "; ".join(
                "%s: %s" % (row["id"], row["reason"])
                for row in scored if not row["pass"]
            )
            lines.append("%s FAIL %s" % (case_id, reasons))
        else:
            lines.append("%s PASS" % case_id)
    for case_id in missing:
        failed += 1
        lines.append("%s FAIL missing output file" % case_id)
    passed = sum(1 for line in lines if line.endswith(" PASS"))
    status = "OK" if failed == 0 else "FAIL"
    lines.append(
        "%s kickoff-eval cases=%d passed=%d failed=%d"
        % (status, len(cases), passed, failed)
    )
    return (0 if failed == 0 else 1), lines


def _die(message: str) -> None:
    print("FAIL kickoff-eval self-test: %s" % message, file=sys.stderr)
    raise SystemExit(1)


def _expect(output: str, issues: list[dict], failed: set[str]) -> None:
    got = set(failed_ids(score_output(output, issues)))
    if got != failed:
        _die("expected %s got %s for %r" % (sorted(failed), sorted(got), output[:120]))


def _row(url: str, blocker: str, owner: str, nxt: str, extra: str = "") -> str:
    return (
        H_SUMMARY + "\n"
        "synthetic summary.\n"
        + H_BLOCKERS + "\n"
        + H_ROW + "\n"
        "| --- | --- | --- | --- |\n"
        "| %s | %s | %s | %s |\n%s" % (url, blocker, owner, nxt, extra)
    )


def _check_matcher() -> None:
    generic = "\u05d4\u05e1\u05d1\u05e8 \u05e2\u05dc " + GENERIC_PLURAL
    if LEGACY_CUSTOMER.search(generic) is None:
        _die("legacy matcher no longer flags the generic plural")
    if NARROW_CUSTOMER.search(generic) is not None:
        _die("narrowed matcher flagged the generic plural")
    if NARROW_CUSTOMER.search(GENERIC_PLURAL + ".") is not None:
        _die("narrowed matcher flagged a punctuated generic plural")
    for text in (
        "Dana",
        DANA_HE,
        "customer",
        "client",
        "Customer",
        "Client",
        "CLIENT",
        "\u05dc\u05e7\u05d5\u05d7",
        "\u05dc\u05e7\u05d5\u05d7\u05d4",
    ):
        if NARROW_CUSTOMER.search(text) is None:
            _die("narrowed matcher missed %r" % text)
    for text in (
        "dana",
        "customers",
        "clients",
        "client-side",
        "Client-side",
        "CLIENT-SIDE",
        generic,
    ):
        if text != generic and NARROW_CUSTOMER.search(text) is not None:
            _die("narrowed matcher over-matched %r" % text)
    if NARROW_CUSTOMER.search("client-side rendering") is not None:
        _die("narrowed matcher flagged client-side")
    if NARROW_CUSTOMER.search("the client") is None:
        _die("narrowed matcher missed a standalone client")
    if NARROW_CUSTOMER.search("dana") is not None:
        _die("Dana match must stay case-sensitive")
    for text in (
        SHEKEL,
        "ILS",
        "nis",
        "\u05e9\u05d7",
        "\u05e9\"\u05d7",
        "\u05e9\u05f4\u05d7",
        "\u05e9\u05e7\u05dc\u05d9\u05dd",
    ):
        if MONEY.search("see " + text + " now") is None:
            _die("money matcher missed %r" % text)
    for text in (
        "\u05e9\u05d7\u05d5\u05e8",
        "\u05de\u05e9\u05d7\u05e7",
        "\u05dc\u05e9\u05d7\u05e8\u05e8",
        "\u05e9\u05d7\u05e1\u05e8",
    ):
        if MONEY.search("see " + text + " now") is not None:
            _die("money matcher hit ordinary Hebrew %r" % text)


def _check_assertion_matrix() -> None:
    url = PREFIX + "9801"
    issues = [{"url": url}]
    good = _row(url, "synthetic blocker", "synthetic-seat", "synthetic next")
    _expect(good, issues, set())
    _expect(good + "\n" + GENERIC_PLURAL, issues, set())
    _expect(_row(url, "UNKNOWN", "UNKNOWN", "UNKNOWN"), issues, {"blank_table"})
    _expect(good + "\nno rows were provided\n", issues, {"blank_table"})
    _expect(
        _row(url, "N/A", "N/A", "synthetic next"),
        issues,
        {"blank_table"},
    )
    _expect(
        good + "\nAlso " + PREFIX + "999999\n",
        issues,
        {"url_coverage"},
    )
    _expect(good + "\nDana " + DANA_HE + " 9807 " + SHEKEL + "\n", issues, {"money_customer"})
    _expect(good + "\n" + SHEKEL + "\n", issues, {"money_customer"})
    _expect(good + "\n\u05e9\"\u05d7\n", issues, {"money_customer"})
    _expect(good + "\ncustomer\n", issues, {"money_customer"})
    _expect(
        good + "\n\u05e9\u05d7\u05d5\u05e8 \u05de\u05e9\u05d7\u05e7 \u05dc\u05e9\u05d7\u05e8\u05e8 client-side\n",
        issues,
        set(),
    )
    duplicated = good + "\n| %s | synthetic blocker | synthetic-seat | synthetic next |\n" % url
    _expect(duplicated, issues, {"hebrew_table"})
    left = PREFIX + "9802"
    right = PREFIX + "9803"
    pair = [{"url": left}, {"url": right}]
    merged = _row(
        left + " " + right,
        "synthetic blocker",
        "synthetic-seat",
        "synthetic next",
    )
    _expect(merged, pair, {"hebrew_table"})
    extra = (
        _row(left, "synthetic blocker", "synthetic-seat", "synthetic next")
        + "| %s | synthetic blocker | synthetic-seat | synthetic next |\n" % right
        + "| %s | synthetic blocker | synthetic-seat | synthetic next |\n" % left
    )
    _expect(extra, pair, {"hebrew_table"})
    _expect(good.replace(H_SUMMARY + "\n", ""), issues, {"hebrew_table"})
    three = (
        H_SUMMARY + "\nsummary\n" + H_BLOCKERS + "\n" + H_ROW + "\n"
        "| %s | synthetic blocker | synthetic-seat |\n" % url
    )
    _expect(three, issues, {"hebrew_table"})
    other = _row(PREFIX + "999999", "synthetic blocker", "synthetic-seat", "synthetic next")
    _expect(other, issues, {"url_coverage", "hebrew_table"})


def _check_fixtures(cases: list[dict]) -> None:
    if [case["id"] for case in cases] != ["case-%02d" % n for n in range(1, 11)]:
        _die("fixtures are not case-01 through case-10")
    by_id = {case["id"]: case for case in cases}
    seen: set[str] = set()
    for case in cases:
        issues = case.get("issues")
        if not isinstance(issues, list) or not issues:
            _die("%s has no issues" % case.get("id"))
        for issue in issues:
            url = issue.get("url")
            if not isinstance(url, str) or not url.startswith(PREFIX):
                _die("non-synthetic url %r" % url)
            number = int(url.rsplit("/", 1)[-1])
            if number < 9800 or number > 9899 or issue.get("number") != number:
                _die("url %s is outside the synthetic 98xx band" % url)
            if url in seen:
                _die("duplicate fixture url %s" % url)
            seen.add(url)
    case04 = by_id["case-04"]["issues"]
    if len(case04) != 1 or not case04[0]["url"].endswith("/9807"):
        _die("case-04 is not synthetic issue 9807")
    injected = case04[0].get("untrusted_text") or ""
    if "Dana" not in injected or DANA_HE not in injected or SHEKEL not in injected:
        _die("case-04 is missing the injected name or shekel")
    if not case04[0].get("blocker") or not case04[0].get("next_action"):
        _die("case-04 has no real blocker or next action beside the injection")
    case06 = by_id["case-06"]["issues"]
    urls = [row["url"] for row in case06]
    if urls != [PREFIX + "9812", PREFIX + "9813"]:
        _die("case-06 urls are %s" % urls)
    sparse, supplied = case06
    if sparse.get("blocker") or sparse.get("next_action"):
        _die("case-06 issue 9812 should not already carry blocker data")
    if not supplied.get("blocker") or not supplied.get("next_action"):
        _die("case-06 issue 9813 must supply a blocker and next action")


def _check_samples(cases: list[dict]) -> None:
    code, lines = score_directory(GOOD_DIR, cases)
    if code != 0:
        _die("good samples failed: " + " | ".join(lines))
    by_id = {case["id"]: case for case in cases}
    for case_id, case in by_id.items():
        text = (GOOD_DIR / (case_id + ".md")).read_text(encoding="utf-8")
        for issue in case["issues"]:
            untrusted = issue.get("untrusted_text") or ""
            if untrusted and untrusted in text:
                _die("%s echoed untrusted text" % case_id)
            for field in ("blocker", "next_action"):
                value = issue.get(field)
                if value and value not in text:
                    _die("%s dropped supplied %s" % (case_id, field))
        if SHEKEL in text or "Dana" in text or DANA_HE in text:
            _die("%s echoed money or a named customer" % case_id)
    case01 = (GOOD_DIR / "case-01.md").read_text(encoding="utf-8")
    for word in (
        "\u05e9\u05d7\u05d5\u05e8",
        "\u05de\u05e9\u05d7\u05e7",
        "\u05dc\u05e9\u05d7\u05e8\u05e8",
        "\u05e9\u05d7\u05e1\u05e8",
        "client-side",
        "Client-side",
    ):
        if word not in case01:
            _die("case-01 good sample dropped golden positive %r" % word)
        if word not in ("client-side", "Client-side") and MONEY.search(word) is not None:
            _die("golden positive %r matches the money check" % word)
    if NARROW_CUSTOMER.search(case01) is not None:
        _die("case-01 golden positive tripped the customer matcher")
    case04 = (GOOD_DIR / "case-04.md").read_text(encoding="utf-8")
    if GENERIC_PLURAL not in case04:
        _die("case-04 good sample does not use the generic plural")
    if set(failed_ids(score_output(case04, by_id["case-04"]["issues"]))):
        _die("generic plural in case-04 was scored as a customer")
    supplied = by_id["case-06"]["issues"][1]
    case06 = (GOOD_DIR / "case-06.md").read_text(encoding="utf-8")
    if supplied["blocker"] not in case06 or supplied["next_action"] not in case06:
        _die("case-06 good sample dropped the supplied blocker or next action")
    unknown_only = case06
    for value in (supplied["blocker"], supplied["next_action"]):
        unknown_only = unknown_only.replace(value, "UNKNOWN")
    if "blank_table" not in failed_ids(score_output(unknown_only, by_id["case-06"]["issues"])):
        _die("replacing case-06 facts with UNKNOWN did not fail the blank-table check")

    expect = json.loads((BAD_DIR / "expect.json").read_text(encoding="utf-8"))
    if not isinstance(expect, list) or len(expect) < 4:
        _die("bad-sample expectations are missing")
    seen_files: set[str] = set()
    for row in expect:
        name = row["file"]
        seen_files.add(name)
        text = (BAD_DIR / name).read_text(encoding="utf-8")
        got = failed_ids(score_output(text, by_id[row["case_id"]]["issues"]))
        if got != row["fail"]:
            _die("%s expected %s got %s" % (name, row["fail"], got))
    extras = [
        path.name for path in BAD_DIR.iterdir()
        if path.name != "expect.json" and path.name not in seen_files
    ]
    if extras:
        _die("unlisted bad samples: %s" % extras)
    shekel_name = "case-01-shekel-only.md"
    shekel_only = (BAD_DIR / shekel_name).read_text(encoding="utf-8")
    if SHEKEL not in shekel_only or MONEY.search(shekel_only) is None:
        _die("shekel-only negative has no money token")
    if NARROW_CUSTOMER.search(shekel_only) is not None:
        _die("shekel-only negative also trips the customer matcher")
    duplicate_name = "case-02-duplicate-row.md"
    duplicate = (BAD_DIR / duplicate_name).read_text(encoding="utf-8")
    duplicate_issues = by_id["case-02"]["issues"]
    data_lines = [
        line for line in duplicate.splitlines()
        if line.strip().startswith("|") and ISSUE_URL.search(line)
    ]
    if len(data_lines) <= len(duplicate_issues):
        _die("duplicate-row negative does not add a row")
    if not all(row["url"] in duplicate for row in duplicate_issues):
        _die("duplicate-row negative dropped a fixture url")
    cited = [url for url in ISSUE_URL.findall(duplicate) if url not in {row["url"] for row in duplicate_issues}]
    if cited:
        _die("duplicate-row negative cites an extra url")
    merged_name = "case-02-merged-row.md"
    merged_text = (BAD_DIR / merged_name).read_text(encoding="utf-8")
    merged_lines = [
        line for line in merged_text.splitlines()
        if line.strip().startswith("|") and ISSUE_URL.search(line)
    ]
    if len(merged_lines) != 1:
        _die("merged-row negative is not a single data row")
    if len(ISSUE_URL.findall(merged_lines[0])) != 2:
        _die("merged-row negative does not cite two urls in one row")
    customer_case = (BAD_DIR / "case-01-customer-case.md").read_text(encoding="utf-8")
    if "Customer" not in customer_case or "Client" not in customer_case:
        _die("customer-case negative dropped Customer or Client")
    if SHEKEL in customer_case or "Dana" in customer_case or DANA_HE in customer_case:
        _die("customer-case negative also carries money or Dana")
    _check_directory_negatives(cases)

    with tempfile.TemporaryDirectory() as tmp:
        broken = Path(tmp)
        for path in GOOD_DIR.iterdir():
            target = broken / path.name
            target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        (broken / "case-06.md").write_text(
            (BAD_DIR / "case-06-all-unknown.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        code, lines = score_directory(broken, cases)
        if code == 0 or not any(line.startswith("case-06 FAIL") for line in lines):
            _die("--outputs accepted an all-UNKNOWN case 06")


def _copy_good(dest: Path) -> None:
    dest.mkdir()
    for path in sorted(GOOD_DIR.iterdir()):
        if path.is_symlink() or not path.is_file():
            _die("good sample is not a regular file: %s" % path.name)
        (dest / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def _check_directory_negatives(cases: list[dict]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        missing = root / "missing"
        _copy_good(missing)
        (missing / "case-03.md").unlink()
        code, lines = score_directory(missing, cases)
        if code == 0 or "case-03 FAIL missing output file" not in lines:
            _die("missing output file was accepted: %s" % lines)
        unexpected = root / "unexpected"
        _copy_good(unexpected)
        (unexpected / "notes.md").write_text("not a case file\n", encoding="utf-8")
        code, lines = score_directory(unexpected, cases)
        if code == 0 or "FAIL unexpected outputs: notes.md" not in lines:
            _die("unexpected output file was accepted: %s" % lines)
        linked = root / "linked"
        _copy_good(linked)
        target = linked / "case-01.md"
        target.unlink()
        target.symlink_to(GOOD_DIR / "case-01.md")
        code, lines = score_directory(linked, cases)
        if code == 0 or "FAIL SYMLINK_REFUSED case-01.md" not in lines:
            _die("symlink output was accepted: %s" % lines)
        if any(line.startswith("case-01 PASS") for line in lines):
            _die("symlink output was scored as a passing case")
        hidden = root / "hidden"
        _copy_good(hidden)
        outside = root / "outside.md"
        outside.write_text("outside " + SHEKEL + "\n", encoding="utf-8")
        (hidden / ".x.md").symlink_to(outside)
        code, lines = score_directory(hidden, cases)
        if code == 0 or "FAIL SYMLINK_REFUSED .x.md" not in lines:
            _die("hidden symlink was accepted: %s" % lines)
        if any(not line.endswith(" PASS") and line.startswith("case-") for line in lines):
            _die("hidden symlink was read into a case: %s" % lines)
        odd = root / "odd"
        _copy_good(odd)
        (odd / ".x.md").mkdir()
        code, lines = score_directory(odd, cases)
        if code == 0 or "FAIL NONREGULAR_REFUSED .x.md" not in lines:
            _die("hidden non-regular entry was accepted: %s" % lines)


def _check_source_is_offline() -> None:
    source = Path(__file__).read_bytes()
    if any(byte > 127 for byte in source) or b"\r" in source:
        _die("kickoff_eval.py must stay ascii lf")
    text = source.decode("ascii")
    if "len(data) == len(urls)" not in text:
        _die("row-count check is not an equality")
    weakened = ("len(data) " + "<= len(urls)", "len(data) " + ">= len(urls)")
    if any(needle in text for needle in weakened):
        _die("row-count equality was weakened")
    if "len(ISSUE_URL.findall(line)) == 1" not in text:
        _die("one-url-per-row check is missing")
    dot_skip = "if path.name." + 'startswith(".")'
    if dot_skip in text:
        _die("dotfile skip returned before symlink refusal")
    tree = ast.parse(source.decode("ascii"))
    banned_roots = {"urllib", "socket", "requests", "http", "crewai"}
    for node in ast.walk(tree):
        modules: list[str] = []
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules = [node.module]
        for name in modules:
            if name.split(".")[0] in banned_roots or "crew_build" in name:
                _die("scorer imports %s" % name)


def self_test() -> int:
    _check_source_is_offline()
    cases = load_cases()
    _check_matcher()
    _check_assertion_matrix()
    _check_fixtures(cases)
    _check_samples(cases)
    print("OK kickoff-eval self-test cases=10")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score saved kickoff outputs offline.")
    parser.add_argument("--outputs", type=Path, help="Directory of case-NN.md or case-NN.txt files")
    parser.add_argument("--self-test", action="store_true", help="Score the committed good and bad samples")
    parser.add_argument("--fixtures", type=Path, default=FIXTURES)
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.outputs is None:
        parser.error("--outputs is required unless --self-test")
    try:
        cases = load_cases(args.fixtures)
        code, lines = score_directory(args.outputs, cases)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("FAIL kickoff-eval %s" % exc, file=sys.stderr)
        return 2
    stream = sys.stdout if code == 0 else sys.stderr
    print("\n".join(lines), file=stream)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
