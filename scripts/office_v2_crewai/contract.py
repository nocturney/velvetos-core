"""Shared constants for the reviewed CrewAI pilot runner.

ASCII only. No network. No model import.
"""
from __future__ import annotations

APPROVED_BASE_URL = "http://127.0.0.1:11435"
APPROVED_OPENAI_BASE = "http://127.0.0.1:11435/v1"
APPROVED_OLLAMA_HOST = "127.0.0.1:11435"
APPROVED_ENDPOINT = "127.0.0.1:11435"
APPROVED_HOST = "127.0.0.1"
APPROVED_PORT = 11435
APPROVED_AT = "2026-10-18T15:28:00+03:00"
APPROVED_BY = "Christian"
APPROVED_MODEL = "qwen3.5:9b"
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
# through SHGetFolderPathW, so LOCALAPPDATA does not move the CrewAI mkdir.
# CREWAI_STORAGE_DIR must be an absolute path on D:.
E4_COMMENT = "https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6250312836"
E4_CREWAI_VERSION = "1.15.28"
E4_APPDIRS_VERSION = "1.4.4"
SANDBOX_ROOT = "D:\\Velvet\\Pilots\\crewai-e4\\sandbox-home"
CREWAI_PROFILE_REL = "AppData\\Local\\CrewAI"
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
