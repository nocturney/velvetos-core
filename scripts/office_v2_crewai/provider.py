"""Local-only model provider. Refuses unless the approved config file exists.

No remote host and no paid API is ever called. complete() opens a socket only
after an explicit preflight authorization, only to the approved loopback, and
only when OLLAMA_NO_CLOUD is set and the served digest matches.
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit

from office_v2_crewai.contract import (
    APPROVED_BASE_URL,
    APPROVED_BY,
    APPROVED_HOST,
    APPROVED_MODEL,
    APPROVED_MODEL_DIGEST,
    APPROVED_PORT,
    EVIDENCE_COMMENT,
    PAID_ENV_NAMES,
)


class ProviderRefusal(RuntimeError):
    """Closed refusal. No model call was made."""


def _as_mapping(value: object) -> dict:
    if not isinstance(value, dict):
        raise ProviderRefusal("MODEL_CONFIG_NOT_OBJECT")
    return value


def _is_loopback_host(host: str | None) -> bool:
    if not host:
        return False
    name = host.lower().strip("[]")
    if name in {"localhost", "::1"}:
        return True
    parts = name.split(".")
    if len(parts) != 4:
        return False
    try:
        numbers = [int(part) for part in parts]
    except ValueError:
        return False
    return numbers[0] == 127 and all(0 <= number <= 255 for number in numbers)


def digest_hex(value: object) -> str:
    if not isinstance(value, str):
        raise ProviderRefusal("MODEL_DIGEST_MISMATCH")
    text = value.strip().lower()
    if text.startswith("sha256:"):
        text = text[7:]
    if len(text) != 64 or any(char not in "0123456789abcdef" for char in text):
        raise ProviderRefusal("MODEL_DIGEST_MISMATCH")
    return text


def assert_loopback_url(url: object) -> str:
    """Accept only the owner-approved loopback endpoint. Refuse everything else."""
    if not isinstance(url, str) or not url:
        raise ProviderRefusal("MODEL_URL_MISSING")
    parts = urlsplit(url.strip())
    if parts.scheme != "http":
        raise ProviderRefusal("MODEL_URL_SCHEME_REFUSED")
    if parts.username or parts.password:
        raise ProviderRefusal("MODEL_URL_USERINFO_REFUSED")
    if not _is_loopback_host(parts.hostname):
        raise ProviderRefusal("MODEL_URL_NOT_LOOPBACK")
    port = 80 if parts.port is None else parts.port
    if parts.hostname != APPROVED_HOST or port != APPROVED_PORT:
        raise ProviderRefusal("MODEL_URL_NOT_EXACT_APPROVAL")
    if parts.path not in ("", "/"):
        raise ProviderRefusal("MODEL_URL_PATH_REFUSED")
    if parts.query or parts.fragment:
        raise ProviderRefusal("MODEL_URL_QUERY_REFUSED")
    if url.strip().rstrip("/") != APPROVED_BASE_URL:
        raise ProviderRefusal("MODEL_URL_NOT_EXACT_APPROVAL")
    return APPROVED_BASE_URL


def no_cloud_enabled(env: dict) -> bool:
    """OLLAMA_NO_CLOUD must be set to 1 or true. Absent, empty, or 0 is a refusal."""
    value = env.get("OLLAMA_NO_CLOUD")
    if not isinstance(value, str):
        return False
    return value.strip().lower() in {"1", "true"}


def validate_config_document(document: object) -> dict:
    data = _as_mapping(document)
    if data.get("schema") != "velvetos.office-v2.crewai-local-model.v1":
        raise ProviderRefusal("MODEL_CONFIG_SCHEMA")
    if data.get("approved_by") != APPROVED_BY or data.get("approved_at") != "2026-10-18T15:28:00+03:00":
        raise ProviderRefusal("MODEL_APPROVAL_MISMATCH")
    if data.get("evidence") != EVIDENCE_COMMENT:
        raise ProviderRefusal("MODEL_EVIDENCE_MISMATCH")
    if data.get("provider") != "ollama":
        raise ProviderRefusal("MODEL_PROVIDER_REFUSED")
    if data.get("remote_apis_allowed") is not False:
        raise ProviderRefusal("REMOTE_API_REFUSED")
    if data.get("paid_apis_allowed") is not False:
        raise ProviderRefusal("PAID_API_REFUSED")
    if data.get("api_key") not in (None, ""):
        raise ProviderRefusal("API_KEY_REFUSED")
    if data.get("think") is not False:
        raise ProviderRefusal("THINK_NOT_DISABLED")
    if data.get("ollama_no_cloud") != "1":
        raise ProviderRefusal("OLLAMA_NO_CLOUD_ABSENT")
    for forbidden in ("openai", "anthropic", "gemini", "openrouter", "azure", "groq"):
        if forbidden in data:
            raise ProviderRefusal("PAID_PROVIDER_FIELD_REFUSED")
    base_url = assert_loopback_url(data.get("base_url"))
    if data.get("model") != APPROVED_MODEL:
        raise ProviderRefusal("MODEL_TAG_MISMATCH")
    if digest_hex(data.get("model_digest")) != APPROVED_MODEL_DIGEST:
        raise ProviderRefusal("MODEL_DIGEST_MISMATCH")
    return {
        "base_url": base_url,
        "provider": "ollama",
        "model": APPROVED_MODEL,
        "model_digest": APPROVED_MODEL_DIGEST,
        "think": False,
        "remote_apis_allowed": False,
        "paid_apis_allowed": False,
    }


def inherited_paid_credentials(env: dict) -> list[str]:
    found = []
    for name in PAID_ENV_NAMES:
        value = env.get(name)
        if isinstance(value, str) and value.strip():
            found.append(name)
    return found


class LocalOllamaProvider:
    """Pluggable provider. Authorization is a separate explicit step."""

    def __init__(self, config_path: Path):
        self.config_path = Path(config_path)
        self.calls = 0
        self.authorized = False
        self.config = self._load()

    def _load(self) -> dict:
        if not self.config_path.is_file():
            raise ProviderRefusal("MODEL_CONFIG_ABSENT")
        try:
            document = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ProviderRefusal("MODEL_CONFIG_UNREADABLE") from exc
        return validate_config_document(document)

    def authorize(self) -> None:
        self.authorized = True

    def complete(self, messages: object, urlopen=None, env: dict | None = None) -> str:
        """Call loopback Ollama only when preflight has authorized this object."""
        import os

        environment = os.environ if env is None else env
        if not self.authorized:
            raise ProviderRefusal("MODEL_CALL_BEFORE_PREFLIGHT")
        if self.config.get("model") != APPROVED_MODEL:
            raise ProviderRefusal("MODEL_TAG_MISMATCH")
        if digest_hex(self.config.get("model_digest")) != APPROVED_MODEL_DIGEST:
            raise ProviderRefusal("MODEL_DIGEST_MISMATCH")
        if self.config.get("think") is not False:
            raise ProviderRefusal("THINK_NOT_DISABLED")
        if not no_cloud_enabled(environment):
            raise ProviderRefusal("OLLAMA_NO_CLOUD_ABSENT")
        base_url = assert_loopback_url(self.config.get("base_url"))
        if urlopen is None:
            from urllib import request as urlrequest
            urlopen = urlrequest.urlopen
        shown = _post_json(urlopen, base_url + "/api/show", {"model": APPROVED_MODEL})
        served = shown.get("digest")
        if digest_hex(served) != APPROVED_MODEL_DIGEST:
            raise ProviderRefusal("MODEL_DIGEST_MISMATCH")
        self.calls += 1
        payload = {
            "model": APPROVED_MODEL,
            "messages": _messages(messages),
            "stream": False,
            "think": False,
        }
        body = _post_json(urlopen, base_url + "/api/chat", payload)
        message = body.get("message") if isinstance(body, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str):
            raise ProviderRefusal("LOCAL_MODEL_RESPONSE_UNUSABLE")
        return content


def _messages(messages: object) -> list[dict]:
    if isinstance(messages, str):
        return [{"role": "user", "content": messages}]
    if isinstance(messages, list):
        cleaned = []
        for item in messages:
            if isinstance(item, str):
                cleaned.append({"role": "user", "content": item})
                continue
            if not isinstance(item, dict):
                raise ProviderRefusal("MODEL_MESSAGE_REFUSED")
            role = item.get("role")
            content = item.get("content")
            if role not in {"system", "user", "assistant"} or not isinstance(content, str):
                raise ProviderRefusal("MODEL_MESSAGE_REFUSED")
            cleaned.append({"role": role, "content": content})
        return cleaned
    raise ProviderRefusal("MODEL_MESSAGE_REFUSED")


def _request(target: str, payload: bytes):
    from urllib import request as urlrequest
    return urlrequest.Request(
        target,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )


def _post_json(urlopen, target: str, payload: dict) -> dict:
    base, _, path = target.partition("/api/")
    assert_loopback_url(base)
    if not path:
        raise ProviderRefusal("MODEL_URL_PATH_REFUSED")
    request_obj = _request(target, json.dumps(payload).encode("utf-8"))
    with urlopen(request_obj, timeout=30) as response:
        raw = response.read()
    body = json.loads(raw.decode("utf-8"))
    if not isinstance(body, dict):
        raise ProviderRefusal("LOCAL_MODEL_RESPONSE_UNUSABLE")
    return body
