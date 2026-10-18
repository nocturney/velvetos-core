#!/usr/bin/env python3
"""Sensor: reviewed CrewAI runner stays fail-closed and the frozen manifest matches."""
from __future__ import annotations

import ast
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from office_v2_crewai.contract import (  # noqa: E402
    APPROVED_BASE_URL,
    APPROVED_MODEL,
    APPROVED_MODEL_DIGEST,
    PRIVATE_REPO_NEEDLE,
    TELEMETRY_FLAGS,
)
from office_v2_crewai.kill_harness import KillHarness, KillRefusal  # noqa: E402
from office_v2_crewai.preflight import evaluate, synthetic_passing_bundle, verify_manifest  # noqa: E402
from office_v2_crewai.provider import (  # noqa: E402
    LocalOllamaProvider,
    ProviderRefusal,
    assert_loopback_url,
)
from office_v2_crewai.runner import execute  # noqa: E402
from office_v2_crewai.usage_guard import (  # noqa: E402
    UsageRefusal,
    assert_crew_spec,
    assert_not_chroma_cli,
    assert_post_run,
    module_is_forbidden,
)

PACKAGE = SCRIPTS / "office_v2_crewai"
INPUTS = PACKAGE / "inputs"
EVIDENCE = PACKAGE / "evidence"
MODEL = PACKAGE / "model" / "approved-local-ollama.json"
GROUPS = (
    "identity",
    "reproducibility",
    "safety",
    "graph_smoke",
    "scope",
    "execution",
    "result",
    "teardown",
)


def fail(message: str) -> None:
    print("FAIL check-crewai-reviewed-runner: %s" % message, file=sys.stderr)
    raise SystemExit(1)


def telemetry() -> dict:
    return dict(TELEMETRY_FLAGS)


def check_text(path: Path) -> None:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf") or b"\r" in data or any(byte > 127 for byte in data):
        fail("non-ascii or non-lf bytes in %s" % path.relative_to(ROOT))


def check_manifest() -> None:
    manifest, reason = verify_manifest(INPUTS)
    if manifest is None or reason != "OK":
        fail("committed manifest: %s" % reason)
    for path in INPUTS.iterdir():
        if path.is_file() and PRIVATE_REPO_NEEDLE in path.read_text(encoding="utf-8").lower():
            fail("private repo material in %s" % path.name)


def check_committed_gates() -> None:
    report = evaluate(INPUTS, EVIDENCE, {}, MODEL)
    if report["ok"] or report["model_calls"] != 0:
        fail("committed tree must refuse with zero model calls")
    if report["model_status"] != "CONFIG_ACCEPTED_NO_CALL":
        fail("approved config was not accepted: %s" % report["model_status"])
    e3 = report["gates"]["E3"]
    e6 = report["gates"]["E6"]
    if e3["status"] != "PASS":
        fail("recorded E3 decision did not pass: %s" % e3)
    if e6["status"] != "NOT_VERIFIED" or e6["reason"] != "INSUFFICIENT_OPEN_ISSUES":
        fail("E6 did not stay unverified: %s" % e6)
    issues = json.loads((INPUTS / "issues.json").read_text(encoding="ascii"))
    numbers = [row["number"] for row in issues["issues"]]
    if issues["open_issue_count"] != 12 or 612 not in numbers or 595 not in numbers:
        fail("frozen issue set is not the 12 open public issues")
    if not (EVIDENCE / "e3-security-decision.json").is_file():
        fail("recorded E3 decision file is missing")


def check_gate_mutations() -> None:
    base = Path(tempfile.mkdtemp(prefix="crewai-gates-"))
    try:
        synthetic_passing_bundle(base)
        report = evaluate(base / "inputs", base / "evidence", telemetry(), None)
        if not report["ok"] or report["model_calls"] != 0:
            fail("synthetic bundle did not pass preflight: %s" % report["missing_gates"])
        removals = {
            "E1": base / "evidence" / "e1-authorization.json",
            "E2": base / "evidence" / "e2-capacity.json",
            "E3": base / "evidence" / "e3-security-decision.json",
            "E4": base / "evidence" / "e4-containment.json",
            "E5": base / "evidence" / "e5-network.json",
            "E6": base / "inputs" / "manifest.json",
            "E7": base / "evidence" / "e7-guardrails.json",
        }
        for gate, path in removals.items():
            trial = Path(tempfile.mkdtemp(prefix="crewai-miss-"))
            try:
                shutil.copytree(base / "evidence", trial / "evidence")
                shutil.copytree(base / "inputs", trial / "inputs")
                (trial / path.relative_to(base)).unlink()
                missed = evaluate(trial / "inputs", trial / "evidence", telemetry(), None)
                status = missed["gates"][gate]["status"]
                if missed["ok"] or status == "PASS" or missed["model_calls"] != 0:
                    fail("missing %s did not refuse" % gate)
            finally:
                shutil.rmtree(trial, ignore_errors=True)
    finally:
        shutil.rmtree(base, ignore_errors=True)


def _expect_usage(call, code: str) -> None:
    try:
        call()
    except UsageRefusal as exc:
        if str(exc) != code:
            fail("usage refusal %s != %s" % (exc, code))
        return
    fail("condition %s was accepted" % code)


def check_condition_mutations() -> None:
    base = Path(tempfile.mkdtemp(prefix="crewai-e3-"))
    try:
        synthetic_passing_bundle(base)
        flips = {
            "memory": True,
            "knowledge": True,
            "rag": True,
            "tools_empty": False,
            "mcp_servers": True,
            "crewai_tools": True,
            "chroma_cli": True,
            "pilot_listening_ports": 1,
            "forbid_loaded_modules": ["chromadb"],
        }
        for key, bad in flips.items():
            trial = Path(tempfile.mkdtemp(prefix="crewai-cond-"))
            try:
                shutil.copytree(base / "evidence", trial / "evidence")
                shutil.copytree(base / "inputs", trial / "inputs")
                path = trial / "evidence" / "e3-security-decision.json"
                document = json.loads(path.read_text(encoding="utf-8"))
                document["conditions"][key] = bad
                path.write_text(json.dumps(document), encoding="utf-8")
                missed = evaluate(trial / "inputs", trial / "evidence", telemetry(), None)
                reason = missed["gates"]["E3"]["reason"]
                if missed["ok"] or missed["gates"]["E3"]["status"] == "PASS" or missed["model_calls"] != 0:
                    fail("condition %s did not refuse" % key)
                if reason != "SECURITY_DECISION_CONDITION_" + key.upper():
                    fail("condition %s reason %s" % (key, reason))
            finally:
                shutil.rmtree(trial, ignore_errors=True)
        trial = Path(tempfile.mkdtemp(prefix="crewai-e5-"))
        try:
            shutil.copytree(base / "evidence", trial / "evidence")
            shutil.copytree(base / "inputs", trial / "inputs")
            path = trial / "evidence" / "e5-network.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            document["pilot_listening_ports"] = 1
            path.write_text(json.dumps(document), encoding="utf-8")
            missed = evaluate(trial / "inputs", trial / "evidence", telemetry(), None)
            if missed["gates"]["E5"]["status"] == "PASS" or missed["gates"]["E5"]["reason"] != "PILOT_LISTENER_PRESENT":
                fail("listening port mutation did not refuse: %s" % missed["gates"]["E5"])
            if missed["model_calls"] != 0:
                fail("listening port mutation called a model")
        finally:
            shutil.rmtree(trial, ignore_errors=True)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    spec = {"memory": False, "knowledge": None, "rag": None, "tools": [], "mcps": None, "crewai_tools": False}
    assert_crew_spec(spec)
    _expect_usage(lambda: assert_crew_spec({**spec, "memory": True}), "MEMORY_NOT_DISABLED")
    _expect_usage(lambda: assert_crew_spec({**spec, "knowledge": ["doc"]}), "KNOWLEDGE_OR_RAG_REFUSED")
    _expect_usage(lambda: assert_crew_spec({**spec, "rag": True}), "KNOWLEDGE_OR_RAG_REFUSED")
    _expect_usage(lambda: assert_crew_spec({**spec, "tools": ["search"]}), "TOOLS_NOT_EMPTY")
    _expect_usage(lambda: assert_crew_spec({**spec, "mcps": ["srv"]}), "MCP_SERVERS_REFUSED")
    _expect_usage(lambda: assert_crew_spec({**spec, "crewai_tools": True}), "CREWAI_TOOLS_REFUSED")
    if module_is_forbidden("chromadb") or module_is_forbidden("chromadb.utils.embedding_functions"):
        fail("chromadb itself was treated as the server")
    benign = {"chromadb": object(), "chromadb.utils.embedding_functions.openai_embedding_function": object()}
    assert_post_run(benign, 0, [["python3", "-c", "print(1)"]])
    for name in ("chromadb.server", "chromadb.server.app", "fastapi", "uvicorn", "mcp", "mcp.server"):
        _expect_usage(lambda name=name: assert_post_run({name: object(), "chromadb": object()}, 0, []), "FORBIDDEN_MODULE_LOADED")
    _expect_usage(lambda: assert_post_run(benign, 2, []), "PILOT_LISTENER_PRESENT")
    _expect_usage(lambda: assert_not_chroma_cli(["chroma", "run"]), "CHROMA_CLI_REFUSED")
    _expect_usage(lambda: assert_not_chroma_cli(["python3", "-m", "chromadb.server"]), "CHROMA_CLI_REFUSED")
    try:
        KillHarness().spawn(["chroma", "run"])
    except KillRefusal as exc:
        if str(exc) != "CHROMA_CLI_REFUSED":
            fail("chroma spawn reason %s" % exc)
    else:
        fail("chroma CLI spawn was accepted")


def check_manifest_mutation() -> None:
    parent = Path(tempfile.mkdtemp(prefix="crewai-hash-"))
    trial = parent / "inputs"
    try:
        shutil.copytree(INPUTS, trial)
        target = trial / "issues.json"
        target.write_bytes(target.read_bytes().replace(b"open", b"OPEN", 1))
        _manifest, reason = verify_manifest(trial)
        if reason != "MANIFEST_HASH_MISMATCH":
            fail("mutated input was not a hash mismatch: %s" % reason)
    finally:
        shutil.rmtree(parent, ignore_errors=True)


class _Body:
    def __init__(self, payload: dict):
        self.raw = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self.raw

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> bool:
        return False


def check_provider() -> None:
    missing = Path(tempfile.mkdtemp(prefix="crewai-model-")) / "missing.json"
    try:
        LocalOllamaProvider(missing)
    except ProviderRefusal as exc:
        if str(exc) != "MODEL_CONFIG_ABSENT":
            fail("missing config reason: %s" % exc)
    else:
        fail("missing config was accepted")
    refused = {
        "http://example.com": "MODEL_URL_NOT_LOOPBACK",
        "http://10.0.0.1": "MODEL_URL_NOT_LOOPBACK",
        "http://192.168.1.1:11435": "MODEL_URL_NOT_LOOPBACK",
        "https://api.openai.com": "MODEL_URL_SCHEME_REFUSED",
        "http://localhost:11435": "MODEL_URL_NOT_EXACT_APPROVAL",
        "http://127.0.0.1:11434": "MODEL_URL_NOT_EXACT_APPROVAL",
        "https://127.0.0.1:11435": "MODEL_URL_SCHEME_REFUSED",
    }
    for url, code in refused.items():
        try:
            assert_loopback_url(url)
        except ProviderRefusal as exc:
            if str(exc) != code:
                fail("%s refused as %s" % (url, exc))
        else:
            fail("%s was accepted" % url)
    if assert_loopback_url(APPROVED_BASE_URL) != APPROVED_BASE_URL:
        fail("approved loopback was not accepted")
    provider = LocalOllamaProvider(MODEL)
    calls = []

    def boom(*_args, **_kwargs):
        calls.append("called")
        raise AssertionError("urlopen")

    try:
        provider.complete("hello", urlopen=boom, env={"OLLAMA_NO_CLOUD": "1"})
    except ProviderRefusal as exc:
        if str(exc) != "MODEL_CALL_BEFORE_PREFLIGHT" or calls:
            fail("unauthorized complete reached the network")
    else:
        fail("unauthorized complete returned")
    bad = json.loads(MODEL.read_text(encoding="ascii"))
    bad["model_digest"] = "a" * 64
    bad_path = missing.parent / "bad.json"
    bad_path.write_text(json.dumps(bad), encoding="ascii")
    try:
        LocalOllamaProvider(bad_path)
    except ProviderRefusal as exc:
        if str(exc) != "MODEL_DIGEST_MISMATCH":
            fail("bad digest reason: %s" % exc)
    else:
        fail("bad digest config was accepted")
    provider.authorize()
    try:
        provider.complete("hello", urlopen=boom, env={})
    except ProviderRefusal as exc:
        if str(exc) != "OLLAMA_NO_CLOUD_ABSENT" or calls:
            fail("missing OLLAMA_NO_CLOUD reached the network: %s" % exc)
    else:
        fail("missing OLLAMA_NO_CLOUD was accepted")
    seen = []

    def show_mismatch(request, timeout=30):
        seen.append(request.full_url)
        return _Body({"digest": "b" * 64})

    try:
        provider.complete("hello", urlopen=show_mismatch, env={"OLLAMA_NO_CLOUD": "1"})
    except ProviderRefusal as exc:
        if str(exc) != "MODEL_DIGEST_MISMATCH":
            fail("served digest reason: %s" % exc)
        if len(seen) != 1 or not seen[0].endswith("/api/show"):
            fail("digest mismatch continued past /api/show: %s" % seen)
    else:
        fail("served digest mismatch was accepted")
    chat = []

    def show_then_chat(request, timeout=30):
        chat.append((request.full_url, request.data))
        if request.full_url.endswith("/api/show"):
            return _Body({"digest": APPROVED_MODEL_DIGEST})
        return _Body({"message": {"content": "local"}})

    text = provider.complete("hello", urlopen=show_then_chat, env={"OLLAMA_NO_CLOUD": "1"})
    if text != "local" or provider.calls != 1 or len(chat) != 2:
        fail("approved local chat was not a single think-disabled call")
    if b'"think": false' not in chat[1][1] or not chat[1][0].endswith("/api/chat"):
        fail("chat payload did not send think false")
    if APPROVED_MODEL.encode("ascii") not in chat[1][1]:
        fail("chat payload did not use the approved model")


def check_kill() -> None:
    harness = KillHarness()
    proc = harness.spawn([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        killed = harness.kill_owned()
        proc.wait(timeout=5)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
    if proc.poll() is None or proc.pid not in killed:
        fail("owned sleep was not killed")
    if KillHarness().signal_pid(os.getpid()) != "REFUSED_NOT_OWNED":
        fail("untracked pid was not refused")
    try:
        KillHarness(cost_ceiling=1)
    except KillRefusal:
        return
    fail("nonzero cost ceiling was accepted")


def check_execute() -> None:
    out = Path(tempfile.mkdtemp(prefix="crewai-out-"))
    try:
        code = execute(INPUTS, out, EVIDENCE, MODEL, env={})
        if code != 2:
            fail("committed execute returned %s" % code)
        receipt = json.loads((out / "attempt-receipt.json").read_text(encoding="utf-8"))
        status = receipt["result"]["status"]
        if status in {"PASS", "PASS_TASK_ONLY"}:
            fail("receipt fabricated %s" % status)
        if receipt["execution"]["model_calls"] != 0:
            fail("execute recorded a model call")
        for group in GROUPS:
            if group not in receipt:
                fail("receipt missing %s" % group)
        if (out / "summary.md").read_text(encoding="utf-8") != "NOT_RUN\n":
            fail("summary is not NOT_RUN")
        if not (out / "postflight-receipt.json").is_file():
            fail("postflight receipt missing")
        if "crewai" in sys.modules:
            fail("crewai was imported")
    finally:
        shutil.rmtree(out, ignore_errors=True)


def check_ast() -> None:
    path = PACKAGE / "crew_build.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
            if "crewai" in names:
                fail("crewai import is at module scope")
    agents = []
    crews = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr == "Agent":
            agents.append(node)
        if node.func.attr == "Crew":
            crews.append(node)
    if len(agents) != 2 or len(crews) != 1:
        fail("crew shape is not two agents and one crew")
    roles = []
    for node in agents:
        tools = next(kw.value for kw in node.keywords if kw.arg == "tools")
        role = next(kw.value for kw in node.keywords if kw.arg == "role")
        if not isinstance(tools, ast.List) or tools.elts:
            fail("agent tools are not empty")
        if not isinstance(role, ast.Constant):
            fail("agent role is not a literal")
        roles.append(role.value)
    if roles != ["Triage", "Reviewer"]:
        fail("roles are %s" % roles)
    memory = next(kw.value for kw in crews[0].keywords if kw.arg == "memory")
    if not isinstance(memory, ast.Constant) or memory.value is not False:
        fail("memory is not False")
    for forbidden in ("allow_code_execution", "CodeInterpreter", "crewai-tools"):
        if forbidden in source:
            fail("crew source contains %s" % forbidden)
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        if any("crewai_tools" in name or "crewai-tools" in name for name in names):
            fail("crew source imports crewai-tools")
    for node in agents + crews:
        for keyword in node.keywords:
            if keyword.arg in {"knowledge", "knowledge_sources", "rag", "mcps", "mcp_servers", "embedder"}:
                fail("crew passes %s" % keyword.arg)


def check_workflows() -> None:
    folder = ROOT / ".github" / "workflows"
    for path in folder.glob("*"):
        if path.is_file() and "office_v2_crewai" in path.read_text(encoding="utf-8", errors="replace"):
            fail("workflow mentions the runner: %s" % path.name)


def main() -> int:
    if "crewai" in sys.modules:
        fail("crewai was already imported")
    for path in sorted(PACKAGE.rglob("*.py")):
        check_text(path)
    check_text(Path(__file__))
    check_manifest()
    check_committed_gates()
    check_gate_mutations()
    check_condition_mutations()
    check_manifest_mutation()
    check_provider()
    check_kill()
    check_execute()
    check_ast()
    check_workflows()
    if "crewai" in sys.modules:
        fail("crewai was imported by the sensor")
    print("OK check-crewai-reviewed-runner")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
