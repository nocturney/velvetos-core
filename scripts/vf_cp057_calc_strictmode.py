#!/usr/bin/env python3
"""CP057 calc.ps1 strict-mode regression.

Windows PowerShell 5.1 Set-StrictMode -Version Latest unrolls
`return @()` to no output. Assigning that output stores $null, and
`$null.Count` throws PropertyNotFoundException. The same throw happens
for a single unrolled object that has no Count property. `@($null)` is
not the repair: it has Count 1 and would refuse a closed Calculator.

This sensor models that empty-result case and rejects a calc.ps1 whose
Calcs call sites, or any other possibly-empty .Count/.Length, are left
unwrapped. It also requires a 10000 ms poll for CalculatorResults and
the buttons the script presses, a Calculator-only UWP host bind
(ApplicationFrameHost or the Calculator process), a content bind to the
CalculatorApp window (Windows.UI.Core.CoreWindow) rather than the outer
frame, and a frame choice that follows the CalculatorApp process started
by this attempt instead of the shared ApplicationFrameHost process or an
English title alone. The receipt records the refusal message, refusal
code, bound element, bound process, and redacted candidate-frame titles.
A refusal still stops that Calculator process and records calc_closed
from what remains. The console session is resolved with
WTSGetActiveConsoleSessionId and the expected user's explorer.exe, and
the idle gate is the single constant 120 seconds. Mutations of the fixed
script must go red; the fixed script must stay green. It does not launch
Calculator or touch a Windows session.
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
EARLIER = "97e942bcccfb5c5bcbbe13e97badd058e027e1df3e803a4a24d9eaac933cbc6f"
FIRST_READ = "32824ef410023d84a61c7ecd88edd872ade2e70bdee0ec22b27ae001a3b35f13"
FRAME = "d851448d96791b1d5ec84575b8b923777217630b1dd8ee43a695ccc621425727"
CONTENT = "18bb936d340441fb3a3434afef6792ea65074dc02e38879dd6f6143cf323fe75"
ASCII_FRAME = "cf091c81a971c85bb3c1709dc1e5a91da3dcc33cf04f99a3753e8bf1dc870d00"
ATTEMPT7 = "ee6c41e0635256d662cbc74cb9bb126b9fa7d18681810cfff679810359947144"
ATTEMPT8 = "36abe219c4cf4995b8ce95078e568ee3"
RECEIPT8 = "0e0ae55b1ec00ee26a116be172eda17e3c7a917ffba4f3102c73bdbe4da6bb5c"
ATTEMPT9 = "0ffe7808fd864ba68eeebf7c3310e51b"
RECEIPT9 = "663db01cd7d7423a26d6cf36a15d06080de06a53c9565a5ed3e5263b1500e75e"
# Sha256 values already named in the accepted PIN note. They are prior pins
# and sources, not the attempt-8/9 receipts. Any other sha256 is unknown.
RECORDED_NOTE_SHA256 = frozenset(
    {
        EARLIER,
        FIRST_READ,
        FRAME,
        ASCII_FRAME,
        ATTEMPT7,
        "13590aac5adc76894f4b009d38e6fa51d8ec2642ca12b449a5d3c709b456a977",
        "437eeb9505f2ed62620fbf221a7b4dbe6c7c89a9d6802211fcdb797018fba4f4",
    }
)
ACCEPTED = "ACCEPTED"
IDLE_GATE_SECONDS = 120
UIA_WAIT_MS = 10000
UIA_POLL_MS = 250
TREE_IDS = (
    "CalculatorResults",
    "num6Button",
    "multiplyButton",
    "num7Button",
    "equalButton",
)

REQUIRED = (
    "Set-StrictMode -Version Latest",
    "$ErrorActionPreference='Stop'",
    "$AllowedHost='CHRIS'",
    "$AllowedUser='CHRIS\\Chris'",
    "$Root='D:\\Velvet\\Pilots\\CuaCalcCP057-20261014'",
    "Refuse 'NOT_INTERACTIVE_LIMITED_USER'",
    "Refuse 'CONSOLE_SESSION_UNAVAILABLE'",
    "Refuse 'CONSOLE_SESSION_MISMATCH'",
    "Refuse 'CONSOLE_USER_MISMATCH'",
    "WTSGetActiveConsoleSessionId",
    "$IdleGateSeconds=120",
    "$who.session -ne $console",
    "$_.SessionId -eq $script:ConsoleSession",
    "$data.session -ne $console",
    "$data.console_session -ne $console",
    "console_session=-1",
    "if($rec.idle_seconds -lt $IdleGateSeconds)",
    "if((IdleSeconds) -lt $IdleGateSeconds)",
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
    "/IT /RL LIMITED",
    "num6Button",
    "multiplyButton",
    "num7Button",
    "equalButton",
    "CalculatorResults",
    "PASS_NATIVE_UIA_CALCULATOR_42_ONLY",
    "Refuse 'CALCULATOR_WINDOW_HOST_MISMATCH'",
    "$UiaReadyWaitMs=10000",
    "$UiaReadyPollMs=250",
    "failure_message=''",
    "refusal_code=''",
    "Format-RefusalMessage",
    "Wait-CalculatorTree",
    "ApplicationFrameHost",
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
            if prop == "Length" and rhs is not None:
                stripped = rhs.lstrip()
                if stripped[:1] in "'\"":
                    continue
                # -replace and .Trim() yield [string]. Strict mode exposes Length.
                if "-replace" in stripped or ".Trim()" in stripped:
                    continue
        findings.append(
            f"line {line}: {recv}.{prop} can throw PropertyNotFoundException "
            "on an empty or scalar pipeline result; wrap the result in @()"
        )
    return findings


def script_findings(text: str) -> list[str]:
    code = blank_non_code(text)
    return calcs_call_findings(code) + count_findings(code, text)


def function_spans(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"(?m)^function ([^\s({]+)", text))
    spans: list[tuple[str, str]] = []
    if not matches:
        return [("script", text)]
    spans.append(("script-preamble", text[: matches[0].start()]))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        spans.append((match.group(1), text[match.start() : end]))
    return spans


def _compact(body: str) -> str:
    return re.sub(r"\s+", "", body)


def loop_is_bounded(body: str) -> bool:
    compact = _compact(body)
    while_at = compact.find("while($true)")
    if while_at < 0:
        return True
    segment = compact[while_at:]
    deadline = segment.find("UtcNow-ge$deadline")
    sleep = segment.find("Start-Sleep-Milliseconds$UiaReadyPollMs")
    refuse = segment.find("Refuse")
    ceiling = compact.find("AddMilliseconds($UiaReadyWaitMs)")
    return (
        deadline >= 0
        and sleep >= 0
        and refuse >= 0
        and ceiling >= 0
        and ceiling < while_at
        and deadline < sleep
    )


def wait_findings(text: str) -> list[str]:
    problems: list[str] = []
    ceilings = re.findall(r"\$UiaReadyWaitMs\s*=\s*(\d+)", text)
    if ceilings != [str(UIA_WAIT_MS)]:
        problems.append(
            f"UIA wait ceiling must be assigned once as {UIA_WAIT_MS} ms, found {ceilings or 'none'}"
        )
    polls = re.findall(r"\$UiaReadyPollMs\s*=\s*(\d+)", text)
    if polls != [str(UIA_POLL_MS)]:
        problems.append(
            f"UIA poll interval must be assigned once as {UIA_POLL_MS} ms, found {polls or 'none'}"
        )
    if "AddMilliseconds($UiaReadyWaitMs)" not in text:
        problems.append("wait deadline is not derived from $UiaReadyWaitMs")
    if re.search(r"AddMilliseconds\(\s*(?!\$UiaReadyWaitMs\b)\d+", text):
        problems.append("a wait uses a numeric deadline instead of $UiaReadyWaitMs")
    spans = dict(function_spans(text))
    for name, body in function_spans(text):
        if "while($true)" not in body:
            continue
        if not loop_is_bounded(body):
            problems.append(f"{name}: while($true) is not a bounded poll that fail-closes on the deadline")
    tree = spans.get("Wait-CalculatorTree", "")
    if not tree:
        problems.append("missing Wait-CalculatorTree")
    else:
        for token in TREE_IDS:
            if token not in tree:
                problems.append(f"Wait-CalculatorTree does not wait for {token}")
        if "AddMilliseconds($UiaReadyWaitMs)" not in tree:
            problems.append("Wait-CalculatorTree has no $UiaReadyWaitMs deadline")
    finder = spans.get("FindElement", "")
    if "AddMilliseconds($UiaReadyWaitMs)" not in finder:
        problems.append("FindElement does not bound its wait with $UiaReadyWaitMs")
    press = spans.get("Press", "")
    if "FindElement" not in press:
        problems.append("Press must resolve buttons through the bounded FindElement wait")
    tree_at = text.find("$calcWindow=Wait-CalculatorTree")
    read_at = text.find("$rec.first_result=Display")
    if tree_at < 0 or read_at < 0 or tree_at > read_at:
        problems.append("the CalculatorResults wait must run before the first Display read")
    if "ApplicationFrameHost" not in text or "CalculatorApp" not in text:
        problems.append("window bind must name ApplicationFrameHost and CalculatorApp")
    name_lines = [line for line in text.splitlines() if "Get-Process -Name" in line]
    if not name_lines:
        problems.append("missing Calculator process filter")
    for line in name_lines:
        if "ApplicationFrameHost" in line:
            problems.append("ApplicationFrameHost must not be selected as a Calculator process")
    if "Stop-Process -Name" in text or re.search(r"Stop-Process\b[^\n]*ApplicationFrameHost", text):
        problems.append("the script must not stop ApplicationFrameHost")
    if re.search(r"\$root\.FindAll\([^\n]*Descendants", text) or re.search(
        r"\$root\.FindFirst\([^\n]*Descendants", text
    ):
        problems.append("desktop search must not walk descendants from the root")
    if "$root.FindAll(" not in text or "ApplicationFrameWindow" not in text:
        problems.append("frame search must enumerate top-level ApplicationFrameWindow windows")
    if "TreeScope]::Children,$cond)" not in text:
        problems.append("window search must stay on immediate children")
    return problems


def content_findings(text: str) -> list[str]:
    """Reads and presses bind to the CalculatorApp content window, not the frame."""
    problems: list[str] = []
    if "Windows.UI.Core.CoreWindow" not in text:
        problems.append("content bind must name Windows.UI.Core.CoreWindow")
    if "EnumChildWindows" not in text:
        problems.append("content bind must enumerate child windows of the frame")
    if "NativeWindowHandle" not in text:
        problems.append("content bind must start from the frame NativeWindowHandle")
    if "Find-CalculatorContent" not in text:
        problems.append("missing Find-CalculatorContent")
    if "CALCULATOR_CONTENT_WINDOW_UNAVAILABLE" not in text:
        problems.append("missing CALCULATOR_CONTENT_WINDOW_UNAVAILABLE refusal")
    if "bound_element=''" not in text or "bound_process=''" not in text:
        problems.append("receipt schema must include bound_element and bound_process")
    if "$rec.bound_element=" not in text or "$rec.bound_process=" not in text:
        problems.append("receipt must record bound_element and bound_process")
    if "bound_via=''" not in text or "$rec.bound_via=" not in text:
        problems.append("receipt must include bound_via")
    if "toplevel_corewindow" not in text or "frame_child" not in text:
        problems.append("bound_via must name toplevel_corewindow and frame_child")
    if not re.search(r"\bEnumWindows\b", text):
        problems.append("top-level CoreWindow pass must use EnumWindows")
    spans = dict(function_spans(text))
    top = spans.get("Find-TopLevelCoreWindow", "")
    if "Test-StartedThisAttempt" not in top or "FromHandle" not in top:
        problems.append("top-level CoreWindow must belong to a Calculator process started by this attempt")
    if "CALCULATOR_CONTENT_WINDOW_AMBIGUOUS" not in top:
        problems.append("more than one top-level CoreWindow must fail closed")
    if "Windows.UI.Core.CoreWindow" not in top:
        problems.append("top-level pass must filter Windows.UI.Core.CoreWindow")
    frames = spans.get("Get-TopLevelFrames", "")
    content = spans.get("Find-CalculatorContent", "")
    if "Find-TopLevelCoreWindow" not in frames or "Find-TopLevelCoreWindow" not in content:
        problems.append("Get-TopLevelFrames and Find-CalculatorContent must run the top-level CoreWindow pass")
    if re.search(r"EnumChildWindows\s*\(\s*(?:IntPtr\.Zero|\[IntPtr\]::Zero)", text):
        problems.append("EnumChildWindows must not start at the desktop")
    if re.search(r"Children\s*\(\s*\[IntPtr\]::Zero\s*\)", text):
        problems.append("Win32 child search must not start at the desktop")
    spans = dict(function_spans(text))
    if "Resolve-ContentWindow" not in spans.get("FindElement", ""):
        problems.append("FindElement must rebind to the content window")
    tree = spans.get("Wait-CalculatorTree", "")
    if "Find-CalculatorContent" not in tree:
        problems.append("Wait-CalculatorTree must search the content window")
    if "CALCULATOR_CONTENT_WINDOW_UNAVAILABLE" not in tree:
        problems.append("Wait-CalculatorTree must fail closed when the content window is absent")
    if "FindElementOnce $frame" in tree:
        problems.append("Wait-CalculatorTree must not read automation ids from the outer frame")
    if "Find-BoundRoot" not in spans.get("Display", ""):
        problems.append("Display must read the bound content element")
    if "Find-BoundRoot" not in spans.get("Press", ""):
        problems.append("Press must invoke the bound content element")
    parts = text.split("} finally {", 1)
    if len(parts) != 2:
        problems.append("missing cleanup finally")
    else:
        tail = parts[1]
        close_at = tail.find(".Close()")
        guard_at = tail.find("Test-ContentProcess")
        if close_at < 0 or guard_at < 0 or guard_at > close_at:
            problems.append("WindowPattern.Close must be limited to the Calculator content process")
    return problems


def frame_findings(text: str) -> list[str]:
    """Select the frame by the Calculator process this attempt started."""
    problems: list[str] = []
    spans = dict(function_spans(text))
    if "Test-StartedThisAttempt" not in text:
        problems.append("frame selection must require a Calculator process started by this attempt")
    if re.search(r"if\(\$frameName -eq 'ApplicationFrameHost'\)\{return \$true\}", text):
        problems.append("a frame must not be selected only because its process is ApplicationFrameHost")
    if re.search(r"if\(\$name -eq 'ApplicationFrameHost'\)\{return 'ready'\}", text):
        problems.append("ApplicationFrameHost must not be treated as a ready Calculator frame")
    owns = spans.get("Test-FrameOwnsAttempt", "")
    if "Test-StartedThisAttempt" not in owns or "Get-FrameContentPid" not in owns:
        problems.append("an ApplicationFrameHost frame is accepted only through its Calculator CoreWindow")
    if re.search(r"if\(-not \(Test-CalculatorTitle", owns):
        problems.append("a title mismatch must not reject an owned Calculator frame")
    title = spans.get("Test-CalculatorTitle", "")
    hebrew = spans.get("Get-HebrewCalculatorTitle", "")
    if "'Calculator'" not in title or "Get-HebrewCalculatorTitle" not in title:
        problems.append("Test-CalculatorTitle must accept Calculator and the Hebrew title")
    if "0x05DE,0x05D7,0x05E9,0x05D1,0x05D5,0x05DF" not in hebrew:
        problems.append("Hebrew Calculator title must be built from ASCII code points")
    built = "".join(chr(n) for n in (0x05DE, 0x05D7, 0x05E9, 0x05D1, 0x05D5, 0x05DF))
    if built != "מחשבון":
        problems.append("Hebrew code points do not spell the Calculator title")
    raw = text.encode("utf-8")
    if raw.startswith(b"\xef\xbb\xbf") or any(byte >= 128 for byte in raw):
        problems.append(
            "calc.ps1 must stay ASCII-only; Windows PowerShell 5.1 reads a BOM-less file as ANSI"
        )
    if "candidate_frame_count=0" not in text or "candidate_frame_titles=''" not in text:
        problems.append("receipt must include candidate frame count and titles")
    if "$rec.candidate_frame_titles=" not in text:
        problems.append("receipt must record candidate frame titles")
    formatted = spans.get("Format-FrameTitles", "")
    for token in ("<path>", "<user>", "160"):
        if token not in formatted:
            problems.append(f"Format-FrameTitles missing {token}")
    parts = text.split("} finally {", 1)
    if len(parts) != 2:
        problems.append("missing cleanup finally")
        return problems
    tail = parts[1]
    if "Stop-Process -Id" not in tail:
        problems.append("refusal path must stop the Calculator process it created")
    if re.search(r"if\(\$owned -contains \$pr\.Id\)\{[^}]*Stop-Process -Id", tail):
        problems.append("refusal cleanup must not skip a Calculator pid outside the early snapshot")
    stop_at = tail.find("Stop-Process -Id")
    closed_at = tail.find("$rec.calc_closed=(@(Calcs).Count -eq 0)")
    if stop_at < 0 or closed_at < 0 or closed_at < stop_at:
        problems.append("calc_closed must be recorded from the process list after the stop")
    return problems


def receipt_findings(text: str) -> list[str]:
    problems: list[str] = []
    if "failure_message=''" not in text or "refusal_code=''" not in text:
        problems.append("receipt schema must include failure_message and refusal_code")
    parts = text.split("} catch {", 1)
    if len(parts) != 2:
        return problems + ["missing fail-closed catch"]
    catch = parts[1].split("} finally {", 1)[0]
    if "$rec.failure_message=" not in catch:
        problems.append("catch does not record failure_message")
    if "$rec.refusal_code=" not in catch:
        problems.append("catch does not record refusal_code")
    if "Exception.Message" not in catch:
        problems.append("catch does not read the exception message")
    if "Format-RefusalMessage" not in catch:
        problems.append("catch does not pass the exception message through the sanitizer")
    if "REFUSED_" not in catch:
        problems.append("catch does not extract the REFUSED_ code")
    sanitizer = dict(function_spans(text)).get("Format-RefusalMessage", "")
    if not sanitizer:
        problems.append("missing Format-RefusalMessage")
    else:
        for token in ("<path>", "<user>", "REFUSED_", "-cmatch", "160", "A-Za-z0-9_"):
            if token not in sanitizer:
                problems.append(f"Format-RefusalMessage missing {token}")
    if "A-Za-z0-9_" not in catch:
        problems.append("refusal code pattern must keep mixed-case automation ids")
    return problems



def plm_findings(text: str) -> list[str]:
    """PLM must be positively observed on the owned CalculatorApp only, at UIA timeout."""
    problems: list[str] = []
    spans = dict(function_spans(text))
    probe = spans.get("Test-CalculatorPlmSuspension", "")
    native = spans.get("Add-CalcContentNative", "")
    wrapper = spans.get("Refuse-CalculatorUnavailable", "")
    for token in (
        "if($proc.ProcessName -ne 'CalculatorApp'){continue}",
        "Test-StartedThisAttempt $proc",
        "$thread.ThreadState -eq [System.Diagnostics.ThreadState]::Wait",
        "$thread.WaitReason -eq [System.Diagnostics.ThreadWaitReason]::Suspended",
        "$script:PlmSuspendedThreads++",
        "$script:PlmTotalThreads++",
        "if($script:PlmTotalThreads -eq 0){$allSuspended=$false}",
        "Windows.UI.Core.CoreWindow",
        "([CalcContentNativeCP057]::ProcessOf($hwnd))",
        "[CalcContentNativeCP057]::CloakOf($hwnd)",
        "$script:DwmCloaked=[int]$cloaked",
        "if($cloaked -gt 0){return $true}",
        "return $allSuspended",
    ):
        if token not in probe:
            problems.append(f"PLM probe missing owned thread/cloak guard {token}")
    for token in (
        'DllImport("dwmapi.dll"',
        "DwmGetWindowAttribute(hwnd,14,out state,sizeof(int))",
        "if(hr != 0){return -1;}",
    ):
        if token not in native:
            problems.append(f"DWM cloak probe missing {token}")
    if "try {$plm=[bool](Test-CalculatorPlmSuspension)} catch {$plm=$false}" not in wrapper:
        problems.append("PLM probe must fail closed to the original refusal on probe errors")
    if "if($plm){Refuse 'CALCULATOR_SUSPENDED_BY_PLM'}" not in wrapper:
        problems.append("positive PLM evidence must select the exact refusal code")
    if "Refuse $fallback" not in wrapper:
        problems.append("non-PLM UIA loss must preserve the original refusal code")
    for func, tokens in (
        ("FindElement", (
            "Refuse-CalculatorUnavailable 'EXPECTED_CALCULATOR_WINDOW_ABSENT'",
            "Refuse-CalculatorUnavailable ('CALCULATOR_ELEMENT_UNAVAILABLE_'+$id)",
        )),
        ("Wait-CalculatorTree", (
            "Refuse-CalculatorUnavailable 'CALCULATOR_CONTENT_WINDOW_UNAVAILABLE'",
            "Refuse-CalculatorUnavailable ('CALCULATOR_ELEMENT_UNAVAILABLE_'+$missing)",
        )),
    ):
        body = spans.get(func, "")
        for token in tokens:
            if token not in body:
                problems.append(f"{func} bypassed PLM diagnosis at timeout: {token}")
        if re.search(r"\bRefuse\s+\('CALCULATOR_ELEMENT_UNAVAILABLE_", body):
            problems.append(f"{func} directly emitted an unclassified element refusal")
    child = text.split("if($Mode -eq 'Child'){", 1)
    if len(child) != 2:
        problems.append("missing Child receipt schema for PLM")
        return problems
    receipt, _, tail = child[1].partition("} catch {")
    catch = tail.partition("} finally {")[0]
    for field, initial in (
        ("suspended_threads", "0"),
        ("total_threads", "0"),
        ("dwm_cloaked", "$null"),
    ):
        if f"{field}={initial}" not in receipt:
            problems.append(f"receipt missing {field} initial value")
    for field, value in (
        ("suspended_threads", "[int]$script:PlmSuspendedThreads"),
        ("total_threads", "[int]$script:PlmTotalThreads"),
        ("dwm_cloaked", "$script:DwmCloaked"),
    ):
        if f"$rec.{field}={value}" not in catch:
            problems.append(f"failure receipt does not capture {field}")
    return problems


def plm_model_findings() -> list[str]:
    """Independent decision truth-table; absent/partial observations never prove suspension."""
    def classified(suspended: int, total: int, cloak: int | None) -> bool:
        return (total > 0 and suspended == total) or (cloak is not None and cloak > 0)

    cases = (
        (23, 23, None, True),
        (0, 23, 2, True),
        (22, 23, 0, False),
        (0, 0, None, False),
        (0, 0, -1, False),
        (0, 0, 2, True),
        (23, 24, None, False),
        (23, 23, 0, True),
    )
    return [
        f"PLM classification mismatch for {suspended}/{total}, cloak={cloak}"
        for suspended, total, cloak, expected in cases
        if classified(suspended, total, cloak) != expected
    ]

def sanitize_refusal(raw: str) -> tuple[str, str]:
    """Mirror of Format-RefusalMessage. Fixed REFUSED_* tokens pass through."""
    if not raw:
        return "", ""
    text = re.sub(r"[\r\n\t]+", " ", raw).strip()
    if re.fullmatch(r"REFUSED_[A-Za-z0-9_]+", text):
        return text, text[len("REFUSED_") :]
    found = re.search(r"REFUSED_[A-Za-z0-9_]+", text)
    if found:
        token = found.group(0)
        return token, token[len("REFUSED_") :]
    text = re.sub(r"(?i)[A-Za-z]:\\[^\s'\";]+", "<path>", text)
    text = re.sub(r"(?i)\\\\[^\s'\";]+", "<path>", text)
    text = re.sub(r"(?i)CHRIS\\Chris", "<user>", text)
    if len(text) > 160:
        text = text[:160]
    return text.strip(), ""


def sanitizer_model_findings() -> list[str]:
    problems: list[str] = []
    samples = {
        "REFUSED_CALCULATOR_ELEMENT_UNAVAILABLE_CalculatorResults": (
            "REFUSED_CALCULATOR_ELEMENT_UNAVAILABLE_CalculatorResults",
            "CALCULATOR_ELEMENT_UNAVAILABLE_CalculatorResults",
        ),
        "REFUSED_EXPECTED_CALCULATOR_WINDOW_ABSENT": (
            "REFUSED_EXPECTED_CALCULATOR_WINDOW_ABSENT",
            "EXPECTED_CALCULATOR_WINDOW_ABSENT",
        ),
        "REFUSED_CALCULATOR_WINDOW_HOST_MISMATCH": (
            "REFUSED_CALCULATOR_WINDOW_HOST_MISMATCH",
            "CALCULATOR_WINDOW_HOST_MISMATCH",
        ),
        "REFUSED_CALCULATOR_ELEMENT_UNAVAILABLE_num6Button": (
            "REFUSED_CALCULATOR_ELEMENT_UNAVAILABLE_num6Button",
            "CALCULATOR_ELEMENT_UNAVAILABLE_num6Button",
        ),
        "REFUSED_CALCULATOR_CONTENT_WINDOW_UNAVAILABLE": (
            "REFUSED_CALCULATOR_CONTENT_WINDOW_UNAVAILABLE",
            "CALCULATOR_CONTENT_WINDOW_UNAVAILABLE",
        ),
    }
    for raw, expected in samples.items():
        if sanitize_refusal(raw) != expected:
            problems.append(f"sanitizer dropped the refusal token {raw}")
    leaked = "failed at D:\\Velvet\\Pilots\\secret.txt for CHRIS\\Chris"
    message, code = sanitize_refusal(leaked)
    if code:
        problems.append("a non-refusal exception must not invent a refusal code")
    if "D:\\" in message or "CHRIS\\Chris" in message or "secret" in message:
        problems.append("sanitizer kept a path or the account name")
    if "<path>" not in message or "<user>" not in message:
        problems.append("sanitizer did not redact the path and account")
    long_message, _code = sanitize_refusal("x" * 400)
    if len(long_message) > 160:
        problems.append("sanitizer did not cap the message at 160 characters")
    if sanitize_refusal("") != ("", ""):
        problems.append("empty exception message must stay empty")
    return problems


def mutate(text: str, kind: str) -> str:
    if kind == "drop-preread-wait":
        anchor = "$calcWindow=Wait-CalculatorTree\n"
        if anchor not in text:
            return text
        return text.replace(anchor, "", 1)
    if kind == "unbounded-wait":
        anchor = "$UiaReadyWaitMs=10000"
        if anchor not in text:
            return text
        return text.replace(anchor, "$UiaReadyWaitMs=600000", 1)
    if kind == "drop-deadline":
        anchor = "AddMilliseconds($UiaReadyWaitMs)"
        if anchor not in text:
            return text
        return text.replace(anchor, "AddMilliseconds(0)")
    if kind == "drop-receipt-reason":
        anchor = "$rec.failure_message=Format-RefusalMessage ([string]$_.Exception.Message)\n"
        if anchor not in text:
            return text
        return text.replace(anchor, "", 1)
    if kind == "broaden-host-kill":
        anchor = "Get-Process -Name CalculatorApp,Calculator,calc"
        if anchor not in text:
            return text
        return text.replace(anchor, "Get-Process -Name ApplicationFrameHost,CalculatorApp,Calculator,calc", 1)
    if kind == "drop-corewindow":
        anchor = "Windows.UI.Core.CoreWindow"
        if anchor not in text:
            return text
        return text.replace(anchor, "ApplicationFrameWindow")
    if kind == "rebind-frame":
        mutated = text.replace("$window=Resolve-ContentWindow $window", "$window=FindWindow", 1)
        mutated = mutated.replace("$window=Find-CalculatorContent $frame", "$window=$frame", 1)
        mutated = mutated.replace("$window=Find-BoundRoot", "$window=FindWindow")
        return mutated
    if kind == "drop-bound-receipt":
        anchor = "bound_element='';bound_process='';bound_via=''"
        if anchor not in text:
            return text
        return text.replace(anchor, "", 1)
    if kind == "close-frame":
        anchor = "if(Test-ContentProcess $closeName){"
        if anchor not in text:
            return text
        return text.replace(anchor, "if($true){", 1)
    if kind == "wrong-frame":
        anchor = "$frameName=Get-ContentProcessName $frame\n"
        if anchor not in text:
            return text
        return text.replace(
            anchor,
            "$frameName=Get-ContentProcessName $frame\n"
            " if($frameName -eq 'ApplicationFrameHost'){return $true}\n",
            1,
        )
    if kind == "title-only":
        anchor = "$title=Get-FrameTitle $frame\n"
        if anchor not in text:
            return text
        return text.replace(
            anchor,
            "$title=Get-FrameTitle $frame\n if(-not (Test-CalculatorTitle $title)){return $false}\n",
            1,
        )
    if kind == "drop-hebrew":
        anchor = "0x05DE,0x05D7,0x05E9,0x05D1,0x05D5,0x05DF"
        if anchor not in text:
            return text
        return text.replace(anchor, "0x0041", 1)
    if kind == "raw-hebrew":
        anchor = "if($title -eq (Get-HebrewCalculatorTitle)){return $true}"
        if anchor not in text:
            return text
        return text.replace(anchor, "if($title -eq '\u05de\u05d7\u05e9\u05d1\u05d5\u05df'){return $true}", 1)
    if kind == "owned-only-close":
        anchor = "try { Stop-Process -Id ([int]$pr.Id) -Force -ErrorAction Stop } catch {}"
        if anchor not in text:
            return text
        return text.replace(
            anchor,
            "if($owned -contains $pr.Id){ try { Stop-Process -Id ([int]$pr.Id) -Force -ErrorAction Stop } catch {} }",
            1,
        )
    if kind == "drop-toplevel":
        anchor = "$top=Find-TopLevelCoreWindow\n"
        if anchor not in text:
            return text
        return text.replace(anchor, "")
    if kind == "plm-bypass-initial-tree":
        return text.replace(
            "Refuse-CalculatorUnavailable ('CALCULATOR_ELEMENT_UNAVAILABLE_'+$missing)",
            "Refuse ('CALCULATOR_ELEMENT_UNAVAILABLE_'+$missing)", 1)
    if kind == "plm-bypass-followup-element":
        return text.replace(
            "Refuse-CalculatorUnavailable ('CALCULATOR_ELEMENT_UNAVAILABLE_'+$id)",
            "Refuse ('CALCULATOR_ELEMENT_UNAVAILABLE_'+$id)", 1)
    if kind == "plm-drop-suspended-reason":
        return text.replace(
            "[System.Diagnostics.ThreadWaitReason]::Suspended",
            "[System.Diagnostics.ThreadWaitReason]::Executive", 1)
    if kind == "plm-ignore-dwm-cloak":
        return text.replace("if($cloaked -gt 0){return $true}",
                            "if($false){return $true}", 1)
    if kind == "plm-drop-receipt":
        return text.replace("  $rec.dwm_cloaked=$script:DwmCloaked\n", "", 1)
    if kind == "plm-allow-zero-threads":
        return text.replace(
            "if($script:PlmTotalThreads -eq 0){$allSuspended=$false}",
            "if($script:PlmTotalThreads -lt 0){$allSuspended=$false}", 1)
    if kind == "plm-drop-ownership":
        return text.replace("if($proc.ProcessName -ne 'CalculatorApp'){continue}",
                            "if($false){continue}", 1)
    if kind == "fake-closed":
        anchor = "$rec.calc_closed=(@(Calcs).Count -eq 0)"
        if anchor not in text:
            return text
        return text.replace(anchor, "$rec.calc_closed=$true", 1)
    if kind == "hardcode-session-1":
        mutated = text.replace("$_.SessionId -eq $script:ConsoleSession", "$_.SessionId -eq 1", 1)
        mutated = mutated.replace("$who.session -ne $console", "$who.session -ne 1", 1)
        mutated = mutated.replace("$data.session -ne $console", "$data.session -ne 1", 1)
        return mutated.replace("SessionId -ne $script:ConsoleSession", "SessionId -ne 1", 1)
    if kind == "accept-nonconsole":
        mutated = text.replace(
            "if(-not $consoleOwned -or -not $userOnConsole){Refuse 'CONSOLE_SESSION_MISMATCH'}",
            "if($false){Refuse 'CONSOLE_SESSION_MISMATCH'}",
            1,
        )
        return mutated.replace("$who.session -ne $console", "$who.session -ge 0", 1)
    if kind == "drop-session-match":
        return text.replace(
            "$data.session -ne $console -or $data.console_session -ne $console -or\n",
            "",
            1,
        )
    if kind == "weaken-idle":
        return text.replace("$IdleGateSeconds=120", "$IdleGateSeconds=600", 1)
    return text


def mutation_findings(text: str) -> list[str]:
    """Red before the fix, green after. Each mutation is the fixed script with one guard removed."""
    problems: list[str] = []
    checks = (
        ("drop-preread-wait", wait_findings),
        ("unbounded-wait", wait_findings),
        ("drop-deadline", wait_findings),
        ("drop-receipt-reason", receipt_findings),
        ("broaden-host-kill", wait_findings),
        ("drop-corewindow", content_findings),
        ("rebind-frame", content_findings),
        ("drop-bound-receipt", content_findings),
        ("close-frame", content_findings),
        ("wrong-frame", frame_findings),
        ("title-only", frame_findings),
        ("drop-hebrew", frame_findings),
        ("raw-hebrew", frame_findings),
        ("drop-toplevel", content_findings),
        ("owned-only-close", frame_findings),
        ("fake-closed", frame_findings),
        ("plm-bypass-initial-tree", plm_findings),
        ("plm-bypass-followup-element", plm_findings),
        ("plm-drop-suspended-reason", plm_findings),
        ("plm-ignore-dwm-cloak", plm_findings),
        ("plm-drop-receipt", plm_findings),
        ("plm-allow-zero-threads", plm_findings),
        ("plm-drop-ownership", plm_findings),
        ("hardcode-session-1", session_findings),
        ("accept-nonconsole", session_findings),
        ("drop-session-match", session_findings),
        ("weaken-idle", idle_findings),
    )
    for kind, checker in checks:
        mutated = mutate(text, kind)
        if mutated == text:
            problems.append(f"red-before {kind} did not change the script")
            continue
        found = checker(mutated)
        if not found:
            problems.append(f"red-before {kind} was not detected")
    return problems


def idle_findings(text: str) -> list[str]:
    """The idle gate is one named constant, 120 seconds."""
    problems: list[str] = []
    assigned = re.findall(r"\$IdleGateSeconds\s*=\s*(\d+)", text)
    if assigned != [str(IDLE_GATE_SECONDS)]:
        problems.append("idle constant must be assigned once as 120")
    if re.search(r"idle_seconds\s*-lt\s+\d+", text) or re.search(
        r"IdleSeconds\)\s*-lt\s+\d+", text
    ):
        problems.append("idle gate must use the named constant")
    uses = text.count("-lt $IdleGateSeconds")
    if uses != 4:
        problems.append(f"idle gate must use the named constant at all 4 checks, found {uses}")
    return problems


def session_findings(text: str) -> list[str]:
    """Console session comes from WTS plus the expected user's explorer.exe."""
    problems: list[str] = []
    if re.search(r"(?i)(?:sessionid|\.session)\s*-(?:eq|ne)\s+1\b", text):
        problems.append("hardcoded session 1")
    spans = dict(function_spans(text))
    resolve = spans.get("Resolve-ConsoleSession", "")
    calcs = spans.get("Calcs", "")
    started = spans.get("Test-StartedThisAttempt", "")
    for token in (
        "WTSGetActiveConsoleSessionId",
        "$wts -eq [uint32]0",
        "$wts -eq [uint32]4294967295",
        "Refuse 'CONSOLE_SESSION_UNAVAILABLE'",
        "Name='explorer.exe'",
        "Invoke-CimMethod -InputObject $proc -MethodName GetOwner",
        "-ieq $AllowedUser",
        "Refuse 'CONSOLE_USER_MISMATCH'",
        "if(-not $consoleOwned -or -not $userOnConsole){Refuse 'CONSOLE_SESSION_MISMATCH'}",
        "$script:ConsoleSession=[int]$wts",
    ):
        if token not in resolve:
            problems.append(f"console resolver missing {token}")
    if "$_.SessionId -eq $script:ConsoleSession" not in calcs:
        problems.append("Calcs must filter on the resolved console session")
    if "if($script:ConsoleSession -lt 1){Refuse 'CONSOLE_SESSION_UNAVAILABLE'}" not in calcs:
        problems.append("Calcs must refuse session 0 and an unresolved console session")
    if "SessionId -ne $script:ConsoleSession" not in started:
        problems.append("attempt ownership must stay on the resolved console session")
    parts = text.split("if($Mode -eq 'Child'){", 1)
    if len(parts) != 2 or "# Controller:" not in parts[1]:
        return problems + ["missing Child or Controller console gate"]
    child_only, _, controller = parts[1].partition("# Controller:")
    for token in (
        "$console=Resolve-ConsoleSession",
        "$rec.console_session=$console",
        "$who.session -ne $console",
        "console_session=-1",
    ):
        if token not in child_only:
            problems.append(f"child console gate missing {token}")
    call_at = controller.find("$console=Resolve-ConsoleSession")
    run_at = controller.find("/Run /TN")
    if call_at < 0 or run_at < 0 or call_at > run_at:
        problems.append("controller must resolve the console session before /Run")
    if "$data.session -ne $console" not in controller or "$data.console_session -ne $console" not in controller:
        problems.append("controller must refuse a child/controller session mismatch")
    return problems


def console_refusal(
    wts: int,
    explorers: list[tuple[int, str]],
    child_session: int,
    child_user: str,
    controller_session: int,
    receipt_session: int,
    receipt_console: int,
) -> str:
    """Policy mirror for the console gate. Empty string means the identity is acceptable."""
    expected = "CHRIS\\Chris"
    if wts in (0, 0xFFFFFFFF) or wts < 1:
        return "CONSOLE_SESSION_UNAVAILABLE"
    on_console = [user for sid, user in explorers if sid == wts]
    if not on_console:
        return "CONSOLE_SESSION_MISMATCH"
    if any(user != expected for user in on_console):
        return "CONSOLE_USER_MISMATCH"
    if child_session != wts or child_user != expected:
        return "NOT_INTERACTIVE_LIMITED_USER"
    if (
        controller_session != wts
        or receipt_session != controller_session
        or receipt_console != controller_session
    ):
        return "CHILD_RECEIPT_IDENTITY_MISMATCH"
    return ""


def session_model_findings() -> list[str]:
    """Non-console, RDP, session 0, and Child/Controller disagreement stay refused."""
    problems: list[str] = []
    user = "CHRIS\\Chris"
    other = "CHRIS\\Other"
    cases = (
        (0, [(0, user)], 0, user, 0, 0, 0, "CONSOLE_SESSION_UNAVAILABLE"),
        (0xFFFFFFFF, [(2, user)], 2, user, 2, 2, 2, "CONSOLE_SESSION_UNAVAILABLE"),
        (2, [], 2, user, 2, 2, 2, "CONSOLE_SESSION_MISMATCH"),
        (2, [(3, user)], 3, user, 2, 3, 2, "CONSOLE_SESSION_MISMATCH"),
        (2, [(2, other)], 2, other, 2, 2, 2, "CONSOLE_USER_MISMATCH"),
        (2, [(2, user)], 3, user, 2, 3, 2, "NOT_INTERACTIVE_LIMITED_USER"),
        (2, [(2, user), (3, user)], 3, user, 2, 3, 2, "NOT_INTERACTIVE_LIMITED_USER"),
        (2, [(2, user)], 2, user, 2, 1, 2, "CHILD_RECEIPT_IDENTITY_MISMATCH"),
        (2, [(2, user)], 2, user, 1, 2, 2, "CHILD_RECEIPT_IDENTITY_MISMATCH"),
        (2, [(2, user)], 2, user, 2, 2, 1, "CHILD_RECEIPT_IDENTITY_MISMATCH"),
        (2, [(2, user)], 2, user, 2, 2, 2, ""),
    )
    for wts, explorers, child_session, child_user, controller, receipt, receipt_console, expected_code in cases:
        got = console_refusal(
            wts, explorers, child_session, child_user, controller, receipt, receipt_console
        )
        if got != expected_code:
            problems.append(
                f"console policy {wts}/{child_session}/{receipt} returned {got or 'ACCEPT'} "
                f"expected {expected_code or 'ACCEPT'}"
            )
    return problems


def safety_findings(text: str) -> list[str]:
    problems = [f"missing safety text: {item}" for item in REQUIRED if item not in text]
    problems.extend(idle_findings(text))
    if "activationAllowed" in text or "runtimeAuthority" in text:
        problems.append("calc.ps1 must not declare runtime authority")
    if re.search(r"SessionId\s*-eq\s+0", text):
        problems.append("session 0 must stay out of scope")
    return problems


def _sha256_runs(note: str) -> list[str]:
    """Maximal hex runs long enough to be a sha256, including extra appended hex."""
    return [run for run in re.findall(r"[0-9a-f]+", note) if len(run) >= 64]


def _prefix_impostor(run: str) -> bool:
    """A 64-hex sha that wears a receipt prefix but is not that receipt."""
    return (
        len(run) == 64
        and run not in (RECEIPT8, RECEIPT9)
        and (run.startswith(RECEIPT8[:8]) or run.startswith(RECEIPT9[:8]))
    )


def acceptance_findings(pin: dict) -> list[str]:
    """ACCEPTED is allowed only when the note cites both receipt shas and attempt ids."""
    problems: list[str] = []
    if pin.get("runtimeAuthority") is not False:
        problems.append("RUNTIME_AUTHORITY_NOT_FALSE")
    if pin.get("activationAllowed") is not False:
        problems.append("ACTIVATION_ALLOWED_NOT_FALSE")
    acceptance = pin.get("acceptance")
    note = str(pin.get("note") or "").lower()
    if acceptance == ACCEPTED:
        if ATTEMPT8 not in note:
            problems.append("ACCEPTED_NOTE_MISSING_ATTEMPT8")
        if ATTEMPT9 not in note:
            problems.append("ACCEPTED_NOTE_MISSING_ATTEMPT9")
        runs = _sha256_runs(note)
        cited = {run for run in runs if run in (RECEIPT8, RECEIPT9)}
        unknown = [
            run
            for run in runs
            if run not in (RECEIPT8, RECEIPT9)
            and run not in RECORDED_NOTE_SHA256
            and not _prefix_impostor(run)
        ]
        if unknown:
            problems.append("RECEIPT_SHA_UNKNOWN")
        elif any(_prefix_impostor(run) for run in runs):
            problems.append("ACCEPTED_RECEIPT_SHA_MISMATCH")
        elif len(cited) == 1:
            problems.append("ACCEPTED_NOTE_CITES_ONE_RECEIPT")
        elif len(cited) == 0:
            problems.append("ACCEPTED_NOTE_MISSING_RECEIPT")
    elif acceptance != "RED_UNVERIFIED":
        problems.append("PIN_ACCEPTANCE_NOT_ALLOWED")
    return problems


def acceptance_mutation_findings(pin: dict) -> list[str]:
    """Each acceptance defect fails closed with its own reason code."""
    if acceptance_findings(pin):
        return ["acceptance baseline failed before mutations"]
    note = str(pin.get("note") or "")
    cases = {
        "accepted-without-attempt-8": (
            {"note": note.replace(ATTEMPT8, "")},
            "ACCEPTED_NOTE_MISSING_ATTEMPT8",
        ),
        "accepted-without-attempt-9": (
            {"note": note.replace(ATTEMPT9, "")},
            "ACCEPTED_NOTE_MISSING_ATTEMPT9",
        ),
        "accepted-without-receipt-8": (
            {"note": note.replace(RECEIPT8, "")},
            "ACCEPTED_NOTE_CITES_ONE_RECEIPT",
        ),
        "accepted-without-receipt-9": (
            {"note": note.replace(RECEIPT9, "")},
            "ACCEPTED_NOTE_CITES_ONE_RECEIPT",
        ),
        "wrong-receipt-8": (
            {"note": note.replace(RECEIPT8, "0e0ae55b" + ("f" * 56))},
            "ACCEPTED_RECEIPT_SHA_MISMATCH",
        ),
        "wrong-receipt-9": (
            {"note": note.replace(RECEIPT9, "663db01c" + ("f" * 56))},
            "ACCEPTED_RECEIPT_SHA_MISMATCH",
        ),
        "receipt-8-extra-hex": (
            {"note": note.replace(RECEIPT8, RECEIPT8 + "ab")},
            "RECEIPT_SHA_UNKNOWN",
        ),
        "receipt-9-extra-hex": (
            {"note": note.replace(RECEIPT9, RECEIPT9 + "ab")},
            "RECEIPT_SHA_UNKNOWN",
        ),
        "accepted-without-either-receipt": (
            {"note": note.replace(RECEIPT8, "").replace(RECEIPT9, "")},
            "ACCEPTED_NOTE_MISSING_RECEIPT",
        ),
        "unknown-receipt-sha": (
            {"note": note.replace(RECEIPT8, "ab" * 32)},
            "RECEIPT_SHA_UNKNOWN",
        ),
        "runtime-authority": ({"runtimeAuthority": True}, "RUNTIME_AUTHORITY_NOT_FALSE"),
        "activation-allowed": ({"activationAllowed": True}, "ACTIVATION_ALLOWED_NOT_FALSE"),
    }
    problems: list[str] = []
    for name, (changes, code) in cases.items():
        mutated = dict(pin)
        mutated.update(changes)
        found = acceptance_findings(mutated)
        if code not in found:
            problems.append(f"acceptance mutation {name} missing {code}: {found}")
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
    if str(pin.get("supersedes_sha256", "")).lower() != ATTEMPT7:
        problems.append("PIN supersedes_sha256 must be the attempt-7 pin ee6c41e0")
    pin_text = PIN.read_text(encoding="utf-8").lower()
    if EARLIER not in pin_text:
        problems.append("PIN lost the earlier strict-mode hash")
    if FIRST_READ not in pin_text:
        problems.append("PIN lost the first-read failure hash")
    if FRAME not in pin_text:
        problems.append("PIN lost the frame-bind hash")
    if ASCII_FRAME not in pin_text:
        problems.append("PIN lost the ASCII frame-select hash")
    problems.extend(acceptance_findings(pin))
    problems.extend(acceptance_mutation_findings(pin))
    if pin.get("line_ending") != "lf":
        problems.append("PIN line_ending must stay lf")
    root_readme = README.read_text(encoding="utf-8")
    cua_readme = CUA_README.read_text(encoding="utf-8")
    for path, body in ((README, root_readme), (CUA_README, cua_readme)):
        if digest not in body.lower():
            problems.append(f"{path.relative_to(ROOT)} does not record {digest}")
        for token in (
            "CalculatorResults",
            "refusal_code",
            "ApplicationFrameHost",
            "RED/UNVERIFIED",
            "Windows.UI.Core.CoreWindow",
            "bound_process",
            "CALCULATOR_ELEMENT_UNAVAILABLE_CalculatorResults",
            "מחשבון",
            "candidate_frame_titles",
            "CALCULATOR_CONTENT_WINDOW_UNAVAILABLE",
            "bound_via",
            "toplevel_corewindow",
            "CALCULATOR_SUSPENDED_BY_PLM",
            "suspended_threads",
            "total_threads",
            "dwm_cloaked",
        ):
            if token not in body:
                problems.append(f"{path.relative_to(ROOT)} missing {token}")
    if "PropertyNotFoundException" not in root_readme:
        problems.append("README must record the strict-mode failure class")
    if "RuntimeException" not in root_readme or "RuntimeException" not in cua_readme:
        problems.append("README must record the first-read RuntimeException")
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
        problems.extend(wait_findings(text))
        problems.extend(content_findings(text))
        problems.extend(frame_findings(text))
        problems.extend(receipt_findings(text))
        problems.extend(plm_findings(text))
        problems.extend(session_findings(text))
        problems.extend(mutation_findings(text))
        problems.extend(sanitizer_model_findings())
        problems.extend(plm_model_findings())
        problems.extend(session_model_findings())
        if not problems:
            problems.extend(pin_findings(text))
    if problems:
        print("FAIL cp057-calc-strictmode", file=sys.stderr)
        for item in problems:
            print(f"FAIL {item}", file=sys.stderr)
        return 1
    digest = hashlib.sha256(CALC.read_bytes()).hexdigest()
    print(
        "OK red-before drop-preread-wait=DETECTED unbounded-wait=DETECTED "
        "drop-deadline=DETECTED drop-receipt-reason=DETECTED broaden-host-kill=DETECTED "
        "drop-corewindow=DETECTED rebind-frame=DETECTED drop-bound-receipt=DETECTED "
        "close-frame=DETECTED wrong-frame=DETECTED title-only=DETECTED "
        "drop-hebrew=DETECTED raw-hebrew=DETECTED drop-toplevel=DETECTED "
        "owned-only-close=DETECTED fake-closed=DETECTED "
        "plm-bypass-initial-tree=DETECTED plm-bypass-followup-element=DETECTED "
        "plm-drop-suspended-reason=DETECTED plm-ignore-dwm-cloak=DETECTED "
        "plm-drop-receipt=DETECTED plm-allow-zero-threads=DETECTED "
        "plm-drop-ownership=DETECTED "
        "hardcode-session-1=DETECTED accept-nonconsole=DETECTED "
        "drop-session-match=DETECTED weaken-idle=DETECTED"
    )
    print("OK green-after wait=BOUNDED receipt=REASON host=UWP content=COREWINDOW frame=OWNED plm=CLASSIFIED_OR_FALLBACK")
    print(f"OK cp057-calc-strictmode empty-result=GUARDED sha256={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
