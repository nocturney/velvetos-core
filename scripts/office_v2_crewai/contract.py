"""Shared constants for the reviewed CrewAI pilot runner.

ASCII only. No network. No model import.
"""
from __future__ import annotations

# Owner decision 2026-10-18 20:41 IDT: the only pilot endpoint is the existing
# D: boot server. Port 11435 is refused.
APPROVED_BASE_URL = "http://127.0.0.1:11434"
APPROVED_OPENAI_BASE = "http://127.0.0.1:11434/v1"
APPROVED_OLLAMA_HOST = "127.0.0.1:11434"
APPROVED_ENDPOINT = "127.0.0.1:11434"
APPROVED_HOST = "127.0.0.1"
APPROVED_PORT = 11434
APPROVED_AT = "2026-10-18T20:41:00+03:00"
APPROVED_BY = "Christian"
APPROVED_MODEL = "qwen3.5:9b"
REASONING_EFFORT = "none"
APPROVED_MODEL_DIGEST = "56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90"
EVIDENCE_COMMENT = "https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6250120048"
E3_DECISION = "ACCEPTED_RISK"
E3_DECISION_LABEL = "ACCEPT_RISK_WITH_CONDITIONS"
E3_DECIDED_BY = "Christian"
E3_DECIDED_AT = "2026-10-18T16:02:00+03:00"
E3_BASIS = "https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6250224612"
E3_RECORD = "https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6250234075"
E3_CONDITIONS = {
    "memory": False,
    "knowledge": False,
    "rag": False,
    "tools_empty": True,
    "mcp_servers": False,
    "crewai_tools": False,
    "chroma_cli": False,
    "pilot_listening_ports": 0,
    "forbid_loaded_modules": ["chromadb.server", "fastapi", "uvicorn", "mcp"],
}

LOCK_SHA256 = "121c1bd04eee730b51eb71e49da503b0d0236cdd06d8687a5df792234f78a669"
LOCK_WHEEL_COUNT = 154
CREWAI_VERSION = "1.15.28"
DIRECT_PINS = (
    "crewai==1.15.28",
    "langgraph==1.2.16",
    "langgraph-checkpoint==4.3.0",
    "langgraph-checkpoint-sqlite==3.1.2",
    "langgraph-sdk==0.4.8",
    "langsmith==0.14.11",
)

CHROMADB_ADVISORIES = (
    "PYSEC-2026-311",
    "PYSEC-2026-3813",
    "PYSEC-2026-3814",
    "PYSEC-2026-3815",
)
MCP_ADVISORY = "CVE-2026-59951"
MCP_INSTALLED = "1.28.1"
MCP_FIX_VERSION = "1.30.0"
CHROMADB_INSTALLED = "1.5.9"
RED_ADVISORIES = CHROMADB_ADVISORIES + (MCP_ADVISORY,)

# Comment 6250954627. These map the red PYSEC ids already on the lock.
# PYSEC-2026-3815 stays unmapped. The lock sha and pins do not change.
PYSEC_CVE_MAP = {
    "PYSEC-2026-311": "CVE-2026-45829",
    "PYSEC-2026-3813": "CVE-2026-45830",
    "PYSEC-2026-3814": "CVE-2026-45833",
}
CREWAI_TOOLS_NA = (
    "CVE-2026-2275",
    "CVE-2026-2285",
    "CVE-2026-2286",
    "CVE-2026-2287",
)
MCP_NOT_AFFECTED = (
    "CVE-2026-52869",
    "CVE-2026-59950",
)
ZDI_FROM_REPOSITORY = "ZDI-26-706"
ZDI_FROM_REPOSITORY_CVE = "CVE-2026-92206"

# crewai 1.15.28 writes this before the first kickoff unless it already exists.
# Exact bytes, no trailing newline.
TRACE_USER_BYTES = b'{"first_execution_done":true,"trace_consent":false}'

PRIVATE_REPO_NEEDLE = "velvetos-velvet-factory"
PUBLIC_REPO = "nocturney/velvetos-core"
PUBLIC_ISSUE_PREFIX = "https://github.com/nocturney/velvetos-core/issues/"
RUNBOOK_MINIMUM_ISSUES = 20
REQUIRED_ISSUE_NUMBERS = (612, 595)

TELEMETRY_FLAGS = {
    "CREWAI_DISABLE_TELEMETRY": "true",
    "OTEL_SDK_DISABLED": "true",
    "CREWAI_TRACING_ENABLED": "false",
    "LANGSMITH_TRACING": "false",
}

ATTEMPT_TIMEOUT_SECONDS = 600
COST_CEILING = 0
ROLES = ("Triage", "Reviewer")

# CLQ-16, issue 612 comment 6250312836. appdirs 1.4.4 resolves LocalAppData
# through SHGetFolderPathW, so LOCALAPPDATA does not move that mkdir.
# CREWAI_STORAGE_DIR must be an absolute path on D:.
# LAB-2, issue 595 comment 6250622621: token_manager reads LOCALAPPDATA
# (CrewAI\credentials\secret.key) even when tracing is off. LOCALAPPDATA
# and APPDATA must still be sandbox paths.
E4_COMMENT = "https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6250312836"
E4_CREWAI_VERSION = "1.15.28"
E4_APPDIRS_VERSION = "1.4.4"
SANDBOX_ROOT = "D:\\Velvet\\Pilots\\crewai-e4\\sandbox-home"
# A pilot root may move, but it has to stay under this prefix. D:\VelvetExtra does not qualify.
VELVET_ROOT = "D:\\Velvet"
CREWAI_PROFILE_REL = "AppData\\Local\\CrewAI"
TOKEN_CREDENTIALS_REL = "AppData\\Local\\CrewAI\\credentials"
KICKOFF_OUTPUT_REL = "crewai-output\\kickoff.md"
POSITIVE_DB_NAME = "latest_kickoff_task_outputs.db"

GATES = ("E1", "E2", "E3", "E4", "E5", "E6", "E7")
GATE_FAIL_STATUS = {
    "E1": "NOT_AUTHORIZED",
    "E2": "PARKED_CAPACITY",
    "E3": "BLOCKED_SECURITY",
    "E4": "BLOCKED_STORAGE",
    "E5": "BLOCKED_SECURITY",
    "E6": "NOT_VERIFIED",
    "E7": "NO_GO",
}

PAID_ENV_NAMES = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "OPENROUTER_API_KEY",
    "GROQ_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "COHERE_API_KEY",
)

RESULT_STATUSES = (
    "PASS_TASK_ONLY",
    "FAIL",
    "BLOCKED_SECURITY",
    "BLOCKED_STORAGE",
    "PARKED_CAPACITY",
    "NOT_RUN",
    "NOT_VERIFIED",
)
