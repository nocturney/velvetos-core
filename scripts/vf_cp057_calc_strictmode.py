#!/usr/bin/env python3
"""CP057 calc.ps1 strict-mode regression.

Windows PowerShell 5.1 Set-StrictMode -Version Latest unrolls
`return @()` to no output. Assigning that output stores $null, and
`$null.Count` throws PropertyNotFoundException. The same throw happens
for a single unrolled object that has no Count property. `@($null)` is
not the repair: it has Count 1 and would refuse a closed Calculator.

This sensor models that empty-result case and rejects a calc.ps1 whose
Calcs call sites, or any other possibly-empty .Count/.Length, are left
unwrapped. It does not launch Calculator or touch a Windows session.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CALC = ROOT / "packages/vfharness/devtools/pilots/cua/cp057/calc.ps1"
PIN = ROOT / "packages/vfharness/devtools/pilots/cua/cp057/PIN.json"
README = ROOT / "README.md"
CUA_README = ROOT / "packages/vfharness/devtools/pilots/cua/README.md"
SUPERSEDES = "97e942bcccfb5c5bcbbe13e97badd058e027e1df3e803a4a24d9eaac933cbc6f"

REQUIRED = (
    "Set-StrictMode -Version Latest",
    "$ErrorActionPreference='Stop'",
    "$AllowedHost='CHRIS'",
    "$AllowedUser='CHRIS\\Chris'",
    "$Root='D:\\Velvet\\Pilots\\CuaCalcCP057-20261014'",
    "Refuse 'NOT_INTERACTIVE_LIMITED_USER'",
    "Refuse 'USER_ACTIVE'",
    "Refuse 'CALCULATOR_ALREADY_OPEN'",
    "Refuse 'WRONG_HOST'",
    "Refuse 'WRONG_SOURCE_PATH'",
    "Refuse 'CONTROLLER_REQUIRES_SYSTEM'",
    "Refuse 'SOURCE_DIGEST_MISMATCH'",
    "Refuse 'CHILD_RECEIPT_IDENTITY_MISMATCH'",
    "Refuse 'OWNED_CALCULATOR_PROCESS_NOT_FOUND'",
    "FAIL_CLOSED_REAL_APP",
    "DENIED_USER_ACTIVE",
    "gui_scope='CALCULATOR_ONLY'",
    "$who.session -ne 1",
    "$_.SessionId -eq 1",
    "if($rec.idle_seconds -lt 600)",
    "if((IdleSeconds) -lt 600)",
    "/IT /RL LIMITED",
    "num6Button",
    "multiplyButton",
    "num7Button",
    "equalButton",
    "CalculatorResults",
    "PASS_NATIVE_UIA_CALCULATOR_42_ONLY",
)

BUGGY = """
$prior=Calcs
if($prior.Count -ne 0){Refuse 'CALCULATOR_ALREADY_OPEN'}
$owned=@((Calcs) | Select-Object -ExpandProperty Id)
if($owned.Count -eq 0){Refuse 'OWNED_CALCULATOR_PROCESS_NOT_FOUND'}
"""

FIXED_SNIPPET = """
$prior=@(Calcs)
if($prior.Count -ne 0){Refuse 'CALCULATOR_ALREADY_OPEN'}
$owned=@( @(Calcs) | Select-Object -ExpandProperty Id )
if($owned.Count -eq 0){Refuse 'OWNED_CALCULATOR_PROCESS_NOT_FOUND'}
$run='powershell.exe -File'
if($run.Length -ge 261){Refuse 'TASK_COMMAND_TOO_LONG'}
foreach($pr in @(Calcs)){}
$rec.calc_closed=(@(Calcs).Count -eq 0)
"""


class PropertyNotFoundException(Exception):
    """Windows PowerShell 5.1 strict-mode missing property."""


class Scalar:
    """One unrolled pipeline object. Strict mode exposes no Count."""

    def __init__(self, value: object) -> None:
        self.value = value


def emit_returned_array(items: list[object]) -> list[object]:
    """`return @(items)` writes each element. An empty array writes nothing."""
    return list(items)


def assign_pipeline(emitted: list[object]) -> object:
    """Function output assigned to a variable. Empty output becomes $null."""
    if len(emitted) == 0:
        return None
    if len(emitted) == 1:
        return Scalar(emitted[0])
    return list(emitted)


def at_subexpression(emitted: list[object]) -> list[object]:
    """`@(pipeline)` collects emitted objects. No objects → empty array, not @($null)."""
    return list(emitted)


def at_of_stored_null(value: object) -> list[object]:
    """`@($prior)` after an empty assignment is @($null), Count 1. That is the wrong wrap."""
    if value is None:
        return [None]
    if isinstance(value, Scalar):
        return [value]
    if isinstance(value, list):
        return list(value)
    return [value]


def strict_count(value: object) -> int:
    if value is None or isinstance(value, Scalar):
        raise PropertyNotFoundException(type(value).__name__)
    if isinstance(value, list):
        return len(value)
    raise PropertyNotFoundException(type(value).__name__)


def semantic_empty_result() -> list[str]:
    """Reproduce the CP057 precondition: zero Calculator processes."""
    problems: list[str] = []
    empty = emit_returned_array([])
    stored = assign_pipeline(empty)
    try:
        strict_count(stored)
    except PropertyNotFoundException:
        pass
    else:
        problems.append("empty Calcs assignment must throw PropertyNotFoundException on .Count")
    if strict_count(at_subexpression(empty)) != 0:
        problems.append("@(Calcs) on empty output must be Count 0")
    if strict_count(at_of_stored_null(stored)) != 1:
        problems.append("@($prior) after empty assignment must be Count 1 and is not a valid repair")
    one = emit_returned_array(["calc"])
    try:
        strict_count(assign_pipeline(one))
    except PropertyNotFoundException:
        pass
    else:
        problems.append("single unrolled Calculator process must throw on .Count")
    if strict_count(at_subexpression(one)) != 1:
        problems.append("@(Calcs) on one process must be Count 1")
    two = emit_returned_array(["a", "b"])
    if strict_count(assign_pipeline(two)) != 2:
        problems.append("two emitted processes keep Count 2 without wrapping")
    return problems


def blank_non_code(text: str) -> str:
    """Replace comments and strings with spaces so scanners stay on code."""
    out = list(text)
    i = 0
    n = len(text)
    while i < n:
        if text.startswith("<#", i):
            end = text.find("#>", i + 2)
            end = n if end < 0 else end + 2
            for j in range(i, end):
                if out[j] != "\n":
                    out[j] = " "
            i = end
            continue
        if text.startswith("@'", i) or text.startswith('@"', i):
            quote = text[i + 1]
            end = text.find("'@" if quote == "'" else '"@', i + 2)
            end = n if end < 0 else end + 2
            for j in range(i, end):
                if out[j] != "\n":
                    out[j] = " "
            i = end
            continue
        ch = text[i]
        if ch == "#":
            end = text.find("\n", i)
            end = n if end < 0 else end
            for j in range(i, end):
                out[j] = " "
            i = end
            continue
        if ch in "'\"":
            j = i + 1
            while j < n:
                if text[j] == ch:
                    if ch == "'" and j + 1 < n and text[j + 1] == "'":
                        j += 2
                        continue
                    if ch == '"' and text[j - 1] == "`":
                        j += 1
                        continue
                    j += 1
                    break
                j += 1
            for k in range(i, j):
                if out[k] != "\n":
                    out[k] = " "
            i = j
            continue
        i += 1
    return "".join(out)


def _matching_open(code: str, close: int) -> int:
    depth = 0
    for i in range(close, -1, -1):
        if code[i] == ")":
            depth += 1
        elif code[i] == "(":
            depth -= 1
            if depth == 0:
                return i
    return -1


def receiver_before(code: str, dot: int) -> str:
    i = dot - 1
    while i >= 0 and code[i] in " \t":
        i -= 1
    if i < 0:
        return ""
    if code[i] == ")":
        open_at = _matching_open(code, i)
        if open_at < 0:
            return code[: i + 1]
        start = open_at - 1 if open_at > 0 and code[open_at - 1] == "@" else open_at
        return code[start : i + 1]
    end = i + 1
    while i >= 0 and (code[i].isalnum() or code[i] in "_$."):
        i -= 1
    return code[i + 1 : end]


def _rhs(code: str, start: int) -> str:
    i = start
    n = len(code)
    while i < n and code[i] in " \t":
        i += 1
    if i >= n:
        return ""
    if code[i] == "@" and i + 1 < n and code[i + 1] == "(":
        close = _span_close(code, i + 1)
        return code[i : close + 1] if close >= 0 else code[i:]
    if code[i] == "(":
        close = _span_close(code, i)
        return code[i : close + 1] if close >= 0 else code[i:]
    end = i
    while end < n and code[end] not in "\n;":
        end += 1
    return code[i:end].strip()


def _span_close(code: str, open_paren: int) -> int:
    depth = 0
    for i in range(open_paren, len(code)):
        if code[i] == "(":
            depth += 1
        elif code[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


def last_rhs(code: str, name: str) -> str | None:
    found = None
    for match in re.finditer(rf"\${re.escape(name)}\s*=(?!=)", code):
        found = _rhs(code, match.end())
    return found


def calcs_call_findings(code: str) -> list[str]:
    findings: list[str] = []
    for match in re.finditer(r"\bCalcs\b", code):
        before = code[: match.start()]
        if re.search(r"\bfunction\s+$", before):
            continue
        if re.search(r"@\(\s*$", before):
            continue
        line = code.count("\n", 0, match.start()) + 1
        findings.append(f"line {line}: Calcs call is not wrapped in @()")
    return findings


def count_findings(code: str, original: str) -> list[str]:
    findings: list[str] = []
    for match in re.finditer(r"\.(Count|Length)\b", code):
        prop = match.group(1)
        recv = receiver_before(code, match.start()).strip()
        line = code.count("\n", 0, match.start()) + 1
        if recv.startswith("@(") and recv.endswith(")"):
            continue
        var = re.fullmatch(r"\$(\w+)", recv)
        if var:
            rhs = last_rhs(original, var.group(1))
            if rhs is not None and rhs.lstrip().startswith("@("):
                continue
            if prop == "Length" and rhs is not None and rhs.lstrip()[:1] in "'\"":
                continue
        findings.append(
            f"line {line}: {recv}.{prop} can throw PropertyNotFoundException "
            "on an empty or scalar pipeline result; wrap the result in @()"
        )
    return findings


def script_findings(text: str) -> list[str]:
    code = blank_non_code(text)
    return calcs_call_findings(code) + count_findings(code, text)


def safety_findings(text: str) -> list[str]:
    problems = [f"missing safety text: {item}" for item in REQUIRED if item not in text]
    if re.search(r"idle_seconds\s*-lt\s+(?!600\b)\d+", text):
        problems.append("idle gate threshold was weakened")
    if re.search(r"IdleSeconds\)\s*-lt\s+(?!600\b)\d+", text):
        problems.append("press idle gate threshold was weakened")
    if "activationAllowed" in text or "runtimeAuthority" in text:
        problems.append("calc.ps1 must not declare runtime authority")
    if re.search(r"SessionId\s*-eq\s+0", text):
        problems.append("session 0 must stay out of scope")
    return problems


def pin_findings(text: str) -> list[str]:
    if not PIN.is_file():
        return ["missing PIN.json"]
    try:
        pin = json.loads(PIN.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"PIN.json is not JSON: {exc}"]
    digest = hashlib.sha256(CALC.read_bytes()).hexdigest()
    problems: list[str] = []
    if pin.get("schema") != "velvetos.cp057.calc-ps1-pin.v1":
        problems.append("PIN schema mismatch")
    if pin.get("path") != "packages/vfharness/devtools/pilots/cua/cp057/calc.ps1":
        problems.append("PIN path mismatch")
    if pin.get("sha256") != digest:
        problems.append(f"PIN sha256 {pin.get('sha256')} != file {digest}")
    if str(pin.get("supersedes_sha256", "")).lower() != SUPERSEDES:
        problems.append("PIN lost the pre-fix Windows hash")
    if pin.get("runtimeAuthority") is not False or pin.get("activationAllowed") is not False:
        problems.append("PIN must keep runtimeAuthority and activationAllowed false")
    if pin.get("acceptance") != "RED_UNVERIFIED":
        problems.append("PIN must not claim Calculator acceptance")
    for path in (README, CUA_README):
        body = path.read_text(encoding="utf-8")
        if digest not in body.lower():
            problems.append(f"{path.relative_to(ROOT)} does not record {digest}")
    if "PropertyNotFoundException" not in text and "PropertyNotFoundException" not in README.read_text(encoding="utf-8"):
        problems.append("README must record the strict-mode failure class")
    return problems


def main() -> int:
    problems = semantic_empty_result()
    buggy = script_findings(BUGGY)
    if not any("not wrapped" in item or ".Count" in item for item in buggy):
        problems.append(f"buggy empty-result fixture was not detected: {buggy}")
    if script_findings(FIXED_SNIPPET):
        problems.append("fixed snippet still flagged: " + "; ".join(script_findings(FIXED_SNIPPET)))
    if not CALC.is_file():
        problems.append(f"missing {CALC}")
        text = ""
    else:
        text = CALC.read_text(encoding="utf-8")
        problems.extend(script_findings(text))
        problems.extend(safety_findings(text))
        if not problems:
            problems.extend(pin_findings(text))
    if problems:
        print("FAIL cp057-calc-strictmode", file=sys.stderr)
        for item in problems:
            print(f"FAIL {item}", file=sys.stderr)
        return 1
    digest = hashlib.sha256(CALC.read_bytes()).hexdigest()
    print(f"OK cp057-calc-strictmode empty-result=GUARDED sha256={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
