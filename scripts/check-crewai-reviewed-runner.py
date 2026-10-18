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
    APPROVED_ENDPOINT,
    APPROVED_MODEL,
    APPROVED_MODEL_DIGEST,
    APPROVED_OLLAMA_HOST,
    APPROVED_OPENAI_BASE,
    PRIVATE_REPO_NEEDLE,
    SANDBOX_ROOT,
    TELEMETRY_FLAGS,
)
from office_v2_crewai.e4_evidence import (  # noqa: E402
    REQUIRED_RELS,
    assess_evidence,
    collect_manifest,
    emit_not_observed,
    judge_manifests,
    positive_files_present,
    write_observed_e4,
)
from office_v2_crewai.kill_harness import KillHarness, KillRefusal  # noqa: E402
from office_v2_crewai.preflight import evaluate, synthetic_passing_bundle, verify_manifest  # noqa: E402
from office_v2_crewai.provider import (  # noqa: E402
    LocalOllamaProvider,
    ProviderRefusal,
    assert_llm_route,
    assert_loopback_url,
    effective_endpoint,
)
from office_v2_crewai.sandbox import (  # noqa: E402
    FORBIDDEN_ENV,
    PATH_KEYS,
    PROXY_KEYS,
    VALUE_KEYS,
    StorageRefusal,
    approved_environment,
    assert_cwd,
    assert_no_dotenv,
    assert_proxy_env,
    assert_sandbox_env,
    bind_process_sandbox,
    enter_sandbox,
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


def passing_env() -> dict:
    env = telemetry()
    env.update(approved_environment())
    return env


def model_env() -> dict:
    env = {"OLLAMA_NO_CLOUD": "1", "OLLAMA_HOST": APPROVED_OLLAMA_HOST}
    env.update(PROXY_KEYS)
    for key, value in PROXY_KEYS.items():
        env[key.lower()] = value
    return env


def _expect_storage(call, code: str) -> None:
    try:
        call()
    except StorageRefusal as exc:
        if str(exc) != code:
            fail("storage refusal %s != %s" % (exc, code))
        return
    fail("storage condition %s was accepted" % code)


def _expect_provider(call, code: str) -> None:
    try:
        call()
    except ProviderRefusal as exc:
        if str(exc) != code:
            fail("provider refusal %s != %s" % (exc, code))
        return
    fail("provider condition %s was accepted" % code)


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
    e4 = report["gates"]["E4"]
    if e4["status"] != "BLOCKED_STORAGE" or e4["reason"] != "CONTAINMENT_NOT_OBSERVED":
        fail("committed E4 was not the missing observation: %s" % e4)
    armed = evaluate(INPUTS, EVIDENCE, passing_env(), MODEL)
    if armed["ok"] or armed["gates"]["E4"]["reason"] != "CONTAINMENT_NOT_OBSERVED":
        fail("sandbox env must not turn the committed tree into a pass: %s" % armed["gates"]["E4"])
    if armed["model_calls"] != 0:
        fail("armed preflight called a model")


def check_gate_mutations() -> None:
    base = Path(tempfile.mkdtemp(prefix="crewai-gates-"))
    try:
        synthetic_passing_bundle(base)
        report = evaluate(base / "inputs", base / "evidence", passing_env(), None)
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
                missed = evaluate(trial / "inputs", trial / "evidence", passing_env(), None)
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
                missed = evaluate(trial / "inputs", trial / "evidence", passing_env(), None)
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
            missed = evaluate(trial / "inputs", trial / "evidence", passing_env(), None)
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
        provider.complete("hello", urlopen=show_mismatch, env=model_env())
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

    text = provider.complete("hello", urlopen=show_then_chat, env=model_env())
    if text != "local" or provider.calls != 1 or len(chat) != 2:
        fail("approved local chat was not a single think-disabled call")
    if b'"think": false' not in chat[1][1] or not chat[1][0].endswith("/api/chat"):
        fail("chat payload did not send think false")
    if APPROVED_MODEL.encode("ascii") not in chat[1][1]:
        fail("chat payload did not use the approved model")
    wrong_host = model_env()
    wrong_host["OLLAMA_HOST"] = "127.0.0.1:11434"
    try:
        provider.complete("hello", urlopen=boom, env=wrong_host)
    except ProviderRefusal as exc:
        if str(exc) != "OLLAMA_HOST_REFUSED" or calls:
            fail("wrong OLLAMA_HOST reached the network: %s" % exc)
    else:
        fail("wrong OLLAMA_HOST was accepted")


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
    tracing = next((kw.value for kw in crews[0].keywords if kw.arg == "tracing"), None)
    if not isinstance(tracing, ast.Constant) or tracing.value is not False:
        fail("tracing is not False")
    if "is_litellm=True" in source or "is_litellm = True" in source:
        fail("crew source sets is_litellm True")
    if "base_url=APPROVED_OPENAI_BASE" not in source:
        fail("crew source does not pin the OpenAI-compatible base URL")
    if APPROVED_OPENAI_BASE != "http://127.0.0.1:11435/v1":
        fail("approved OpenAI base is not the 11435 /v1 endpoint")
    saw_bind = False
    saw_cwd = False
    saw_route = False
    build = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "build_crew")
    for stmt in build.body:
        if isinstance(stmt, ast.Import) and any(alias.name == "crewai" for alias in stmt.names):
            if not (saw_bind and saw_cwd and saw_route):
                fail("crewai is imported before the sandbox and endpoint checks")
            break
        for node in ast.walk(stmt):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "bind_process_sandbox":
                    saw_bind = True
                if node.func.id == "enter_sandbox":
                    saw_cwd = True
                if node.func.id == "assert_llm_route":
                    saw_route = True
    else:
        fail("build_crew does not import crewai")
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


def _good_route() -> dict:
    return {
        "base_url": APPROVED_OPENAI_BASE,
        "ollama_host": APPROVED_OLLAMA_HOST,
        "is_litellm": False,
    }


def check_endpoint_mutations() -> None:
    assert_llm_route(_good_route())
    if effective_endpoint(APPROVED_OPENAI_BASE) != APPROVED_ENDPOINT:
        fail("approved base did not resolve to 11435")
    if effective_endpoint(APPROVED_OLLAMA_HOST) != APPROVED_ENDPOINT:
        fail("approved OLLAMA_HOST did not resolve to 11435")
    if effective_endpoint("http://127.0.0.1:11435") != APPROVED_ENDPOINT:
        fail("a 11435 URL without /v1 did not normalize to the approved endpoint")
    _expect_provider(lambda: assert_llm_route({**_good_route(), "is_litellm": True}), "LITELLM_ROUTE_REFUSED")
    _expect_provider(lambda: assert_llm_route({**_good_route(), "is_litellm": None}), "LITELLM_ROUTE_REFUSED")
    _expect_provider(
        lambda: assert_llm_route({**_good_route(), "base_url": "http://localhost:11434/v1"}),
        "LLM_BASE_URL_REFUSED",
    )
    _expect_provider(
        lambda: assert_llm_route({**_good_route(), "base_url": "http://127.0.0.1:11434/v1"}),
        "LLM_BASE_URL_REFUSED",
    )
    _expect_provider(
        lambda: assert_llm_route({**_good_route(), "base_url": "http://127.0.0.1:11435"}),
        "LLM_BASE_URL_REFUSED",
    )
    _expect_provider(
        lambda: assert_llm_route({**_good_route(), "ollama_host": "127.0.0.1:11434"}),
        "OLLAMA_HOST_REFUSED",
    )
    _expect_provider(
        lambda: assert_llm_route({**_good_route(), "ollama_host": "http://127.0.0.1:11435/v1"}),
        "OLLAMA_HOST_REFUSED",
    )
    for bad in (
        "http://localhost:11434/v1",
        "http://127.0.0.1:11434/v1",
        "http://0.0.0.0:11434/v1",
        "127.0.0.1",
        "127.0.0.1:11434",
    ):
        _expect_provider(lambda bad=bad: effective_endpoint(bad), "LLM_ENDPOINT_MISMATCH")


def check_sandbox_mutations() -> None:
    env = passing_env()
    assert_sandbox_env(env)
    assert_proxy_env(env)
    if "CHROMA_ANONYMIZED_TELEMETRY" in approved_environment():
        fail("removed chroma telemetry variable was set")
    if "TIKTOKEN_CACHE_DIR" in approved_environment():
        fail("TIKTOKEN_CACHE_DIR was set")
    for key in PATH_KEYS:
        missing = dict(env)
        del missing[key]
        _expect_storage(lambda missing=missing: assert_sandbox_env(missing), "SANDBOX_ENV_ABSENT:" + key)
        off_drive = dict(env)
        off_drive[key] = "C:\\Users\\Public"
        _expect_storage(lambda off_drive=off_drive: assert_sandbox_env(off_drive), "SANDBOX_NOT_ON_D:" + key)
        outside = dict(env)
        outside[key] = "D:\\outside"
        _expect_storage(lambda outside=outside: assert_sandbox_env(outside), "SANDBOX_OUTSIDE_ROOT:" + key)
    mismatched = dict(env)
    mismatched["CREWAI_STORAGE_DIR"] = mismatched["LOCALAPPDATA"]
    _expect_storage(lambda: assert_sandbox_env(mismatched), "SANDBOX_PATH_MISMATCH:CREWAI_STORAGE_DIR")
    for key in VALUE_KEYS:
        missing = dict(env)
        del missing[key]
        _expect_storage(lambda missing=missing: assert_sandbox_env(missing), "SANDBOX_ENV_ABSENT:" + key)
        wrong = dict(env)
        wrong[key] = "no"
        _expect_storage(lambda wrong=wrong: assert_sandbox_env(wrong), "SANDBOX_VALUE_MISMATCH:" + key)
    for key, want in PROXY_KEYS.items():
        for name in (key, key.lower()):
            missing = dict(env)
            del missing[name]
            _expect_storage(lambda missing=missing: assert_proxy_env(missing), "E5_PROXY_ABSENT:" + name)
            wrong = dict(env)
            wrong[name] = "http://10.0.0.8:8080" if name.upper() != "NO_PROXY" else "127.0.0.1,localhost"
            _expect_storage(lambda wrong=wrong: assert_proxy_env(wrong), "E5_PROXY_MISMATCH:" + name)
        if want != env[key]:
            fail("proxy %s was not installed" % key)
    for key in FORBIDDEN_ENV:
        bad = dict(env)
        bad[key] = "C:\\Users\\Public\\cache"
        _expect_storage(lambda bad=bad: assert_sandbox_env(bad), "FORBIDDEN_ENV:" + key)
    _expect_storage(lambda: assert_cwd("C:\\Users\\Public"), "SANDBOX_CWD_NOT_ON_D")
    _expect_storage(lambda: assert_cwd("/tmp"), "SANDBOX_CWD_NOT_ON_D")
    _expect_storage(lambda: assert_cwd("D:\\Velvet"), "SANDBOX_CWD_OUTSIDE_ROOT")
    _expect_storage(lambda: enter_sandbox(SANDBOX_ROOT + "\\tmp"), "SANDBOX_CWD_OUTSIDE_ROOT")
    _expect_storage(lambda: enter_sandbox(SANDBOX_ROOT), "SANDBOX_CWD_ABSENT")
    _expect_storage(lambda: enter_sandbox(os.getcwd()), "SANDBOX_CWD_NOT_ON_D")
    dotted = Path(tempfile.mkdtemp(prefix="crewai-dotenv-"))
    clean = Path(tempfile.mkdtemp(prefix="crewai-clean-"))
    try:
        (dotted / ".env").write_text("OPENAI_API_KEY=nope\n", encoding="ascii")
        _expect_storage(lambda: assert_no_dotenv(dotted), "SANDBOX_DOTENV_PRESENT")
        assert_no_dotenv(clean)
    finally:
        shutil.rmtree(dotted, ignore_errors=True)
        shutil.rmtree(clean, ignore_errors=True)
    snapshot = {key: os.environ.get(key) for key in list(approved_environment()) + list(FORBIDDEN_ENV)}
    try:
        _expect_storage(lambda: bind_process_sandbox(root="C:\\nope"), "SANDBOX_NOT_ON_D:ROOT")
        if os.environ.get("CREWAI_STORAGE_DIR", "").startswith("C:"):
            fail("bind wrote a C: storage dir")
        _expect_storage(lambda: bind_process_sandbox(root="D:\\Velvet\\other"), "SANDBOX_OUTSIDE_ROOT:ROOT")
    finally:
        for key, value in snapshot.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def check_e4_mutations() -> None:
    parent = Path(tempfile.mkdtemp(prefix="crewai-e4-"))
    try:
        evidence = parent / "evidence"
        write_observed_e4(evidence)
        if assess_evidence(evidence, passing_env()) != "PASS":
            fail("synthetic E4 evidence did not pass: %s" % assess_evidence(evidence, passing_env()))
        profile = parent / "profile"

        def make_profile() -> None:
            if profile.exists():
                shutil.rmtree(profile)
            for rel in REQUIRED_RELS:
                if rel.startswith("__"):
                    continue
                profile.joinpath(*rel.split("\\")).mkdir(parents=True, exist_ok=True)

        make_profile()
        before = collect_manifest(profile)
        control = json.loads((evidence / "e4" / "control-run.json").read_text(encoding="ascii"))
        if judge_manifests(before, json.loads(json.dumps(before)), control) != "PASS":
            fail("unchanged profile manifest was not a pass")
        crew_dir = profile.joinpath(*"AppData\\Local\\CrewAI".split("\\"))
        (crew_dir / "latest_kickoff_task_outputs.db").write_bytes(b"pilot")
        after = collect_manifest(profile)
        if judge_manifests(before, after, control) != "MANIFEST_CREWAI_PROFILE_WRITE":
            fail("CrewAI profile write was not refused")
        make_profile()
        before = collect_manifest(profile)
        temp_dir = profile.joinpath(*"AppData\\Local\\Temp".split("\\"))
        (temp_dir / "noise.lock").write_bytes(b"noise")
        after = collect_manifest(profile)
        noisy = dict(control)
        noisy["noise_rels"] = ["AppData\\Local\\Temp"]
        if judge_manifests(before, after, noisy) != "PASS":
            fail("allowlisted temp noise was refused")
        overlapped = dict(noisy)
        overlapped["overlap_with_candidate"] = True
        if judge_manifests(before, after, overlapped) != "CONTROL_NOISE_OVERLAP":
            fail("overlapping control noise was accepted")
        storage = parent / "storage"
        tmp = parent / "tmp"
        storage.mkdir()
        tmp.mkdir()
        if positive_files_present(storage, tmp) != "POSITIVE_DB_ABSENT":
            fail("missing db was accepted")
        (storage / "latest_kickoff_task_outputs.db").write_bytes(b"db")
        if positive_files_present(storage, tmp) != "POSITIVE_LOCK_ABSENT":
            fail("missing lock was accepted")
        (tmp / "kickoff.lock").write_bytes(b"lock")
        if positive_files_present(storage, tmp) != "PASS":
            fail("sandbox db and lock were not accepted")

        def mutate(edit, code: str) -> None:
            trial = Path(tempfile.mkdtemp(prefix="crewai-e4m-"))
            try:
                shutil.copytree(evidence, trial / "evidence")
                edit(trial / "evidence")
                reason = assess_evidence(trial / "evidence", passing_env())
                if reason != code:
                    fail("E4 mutation %s returned %s" % (code, reason))
            finally:
                shutil.rmtree(trial, ignore_errors=True)

        def load(path: Path) -> dict:
            return json.loads(path.read_text(encoding="utf-8"))

        def dump(path: Path, payload: dict) -> None:
            path.write_text(json.dumps(payload), encoding="ascii")

        mutate(lambda root: (root / "e4" / "manifest-before.json").unlink(), "MANIFEST_BEFORE_ABSENT")
        mutate(lambda root: (root / "e4" / "manifest-after.json").unlink(), "MANIFEST_AFTER_ABSENT")
        mutate(lambda root: (root / "e4" / "control-run.json").unlink(), "CONTROL_RUN_ABSENT")
        mutate(lambda root: (root / "e4" / "positive-control.json").unlink(), "POSITIVE_CONTROL_ABSENT")

        def crewai_hash(root: Path) -> None:
            path = root / "e4" / "manifest-after.json"
            document = load(path)
            for row in document["entries"]:
                if row["rel"] == "AppData\\Local\\CrewAI":
                    row["present"] = True
                    row["sha256"] = "a" * 64
                    row["size"] = 1
                    row["mtime"] = 1
            dump(path, document)

        mutate(crewai_hash, "MANIFEST_CREWAI_PROFILE_WRITE")

        def cache_hash(root: Path) -> None:
            path = root / "e4" / "manifest-after.json"
            document = load(path)
            for row in document["entries"]:
                if row["rel"] == ".cache":
                    row["present"] = True
                    row["sha256"] = "b" * 64
                    row["size"] = 2
                    row["mtime"] = 2
            dump(path, document)

        mutate(cache_hash, "MANIFEST_CHANGED")

        def localappdata_source(root: Path) -> None:
            path = root / "e4" / "manifest-before.json"
            document = load(path)
            document["profile_root_source"] = "LOCALAPPDATA"
            dump(path, document)

        mutate(localappdata_source, "MANIFEST_PROFILE_SOURCE_REFUSED")

        def pilot_control(root: Path) -> None:
            path = root / "e4" / "control-run.json"
            document = load(path)
            document["pilot_started"] = True
            dump(path, document)

        mutate(pilot_control, "CONTROL_RUN_STARTED_PILOT")

        def hkcu_key(root: Path) -> None:
            reg = root / "e4" / "hkcu-after.reg"
            reg.write_text(reg.read_text(encoding="ascii") + "\n[HKEY_CURRENT_USER\\Software\\PilotWrite]\n", encoding="ascii")

        mutate(hkcu_key, "HKCU_EXPORT_MISMATCH")

        def positive_db(root: Path) -> None:
            path = root / "e4" / "positive-control.json"
            document = load(path)
            document["db_exists"] = False
            dump(path, document)

        mutate(positive_db, "POSITIVE_DB_ABSENT")

        def positive_lock(root: Path) -> None:
            path = root / "e4" / "positive-control.json"
            document = load(path)
            document["lock_exists"] = False
            dump(path, document)

        mutate(positive_lock, "POSITIVE_LOCK_ABSENT")

        def positive_drive(root: Path) -> None:
            path = root / "e4" / "positive-control.json"
            document = load(path)
            document["db_path"] = "C:\\Users\\Public\\latest_kickoff_task_outputs.db"
            dump(path, document)

        mutate(positive_drive, "POSITIVE_DB_NOT_ON_D")

        def positive_lock_dir(root: Path) -> None:
            path = root / "e4" / "positive-control.json"
            document = load(path)
            document["lock_path"] = SANDBOX_ROOT + "\\crewai-storage\\kickoff.lock"
            dump(path, document)

        mutate(positive_lock_dir, "POSITIVE_LOCK_NOT_IN_TMP")

        def positive_exit(root: Path) -> None:
            path = root / "e4" / "positive-control.json"
            document = load(path)
            document["exit_code"] = 1
            dump(path, document)

        mutate(positive_exit, "POSITIVE_EXIT_NONEMPTY")

        def redirect_flag(root: Path) -> None:
            path = root / "e4-containment.json"
            document = load(path)
            document["localappdata_redirect_sufficient"] = True
            dump(path, document)

        mutate(redirect_flag, "LOCALAPPDATA_REDIRECT_REFUSED")
        bare = dict(passing_env())
        del bare["HTTPS_PROXY"]
        del bare["https_proxy"]
        reason = assess_evidence(evidence, bare)
        if reason != "E5_PROXY_ABSENT:HTTPS_PROXY":
            fail("missing proxy did not fail E4 env check: %s" % reason)
    finally:
        shutil.rmtree(parent, ignore_errors=True)


def check_proxy_gate() -> None:
    base = Path(tempfile.mkdtemp(prefix="crewai-e5-"))
    try:
        synthetic_passing_bundle(base)
        report = evaluate(base / "inputs", base / "evidence", passing_env(), None)
        if report["gates"]["E5"]["status"] != "PASS" or report["gates"]["E4"]["status"] != "PASS":
            fail("synthetic E4/E5 did not pass: %s" % report["gates"])
        env = passing_env()
        env["HTTP_PROXY"] = "http://10.1.1.1:8080"
        env["http_proxy"] = env["HTTP_PROXY"]
        missed = evaluate(base / "inputs", base / "evidence", env, None)
        if missed["gates"]["E5"]["reason"] != "E5_PROXY_MISMATCH:HTTP_PROXY" or missed["model_calls"] != 0:
            fail("proxy mutation did not refuse: %s" % missed["gates"]["E5"])
        env = passing_env()
        env["NO_PROXY"] = "127.0.0.1,localhost"
        env["no_proxy"] = env["NO_PROXY"]
        missed = evaluate(base / "inputs", base / "evidence", env, None)
        if missed["gates"]["E5"]["reason"] != "E5_PROXY_MISMATCH:NO_PROXY":
            fail("broad NO_PROXY was accepted: %s" % missed["gates"]["E5"])
        env = passing_env()
        env["OLLAMA_HOST"] = "127.0.0.1:11434"
        missed = evaluate(base / "inputs", base / "evidence", env, None)
        if missed["ok"] or missed["model_calls"] != 0:
            fail("11434 host was accepted")
        if missed["gates"]["E5"]["reason"] != "OLLAMA_HOST_REFUSED" and missed["gates"]["E4"]["reason"] != "SANDBOX_VALUE_MISMATCH:OLLAMA_HOST":
            fail("11434 host reason was %s / %s" % (missed["gates"]["E4"], missed["gates"]["E5"]))
    finally:
        shutil.rmtree(base, ignore_errors=True)


def check_committed_e4_shape() -> None:
    fresh = Path(tempfile.mkdtemp(prefix="crewai-e4-emit-"))
    try:
        emit_not_observed(fresh)
        for path in sorted(p for p in fresh.rglob("*") if p.is_file()):
            committed = EVIDENCE / path.relative_to(fresh)
            if not committed.is_file() or committed.read_bytes() != path.read_bytes():
                fail("committed E4 evidence drifted: %s" % path.relative_to(fresh))
    finally:
        shutil.rmtree(fresh, ignore_errors=True)
    before = json.loads((EVIDENCE / "e4" / "manifest-before.json").read_text(encoding="ascii"))
    rels = [row["rel"] for row in before["entries"]]
    if rels != list(REQUIRED_RELS):
        fail("committed manifest paths drifted")
    if any(row.get("sha256") for row in before["entries"]):
        fail("committed manifest invented a hash")
    index = json.loads((EVIDENCE / "e4-containment.json").read_text(encoding="ascii"))
    if index.get("status") != "NOT_OBSERVED":
        fail("committed containment claims an observation")


def check_workflows() -> None:
    folder = ROOT / ".github" / "workflows"
    for path in folder.glob("*"):
        if path.is_file() and "office_v2_crewai" in path.read_text(encoding="utf-8", errors="replace"):
            fail("workflow mentions the runner: %s" % path.name)


def main() -> int:
    if "crewai" in sys.modules:
        fail("crewai was already imported")
    for path in sorted(PACKAGE.rglob("*")):
        if path.is_file() and path.suffix in {".py", ".json", ".reg"}:
            check_text(path)
    check_text(Path(__file__))
    check_manifest()
    check_committed_gates()
    check_committed_e4_shape()
    check_gate_mutations()
    check_condition_mutations()
    check_e4_mutations()
    check_sandbox_mutations()
    check_endpoint_mutations()
    check_proxy_gate()
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
