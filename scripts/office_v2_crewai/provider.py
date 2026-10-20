"""Local-only model provider. Refuses unless the approved config file exists.

No remote host and no paid API is ever called. complete() opens a socket only
after an explicit preflight authorization, only to the approved loopback, and
only when OLLAMA_NO_CLOUD is set and the served digest matches.
"""
from __future__ import annotations

import json
from pathlib import Path

from urllib.parse import urlsplit, urlunsplit

from office_v2_crewai.contract import (
    APPROVED_BASE_URL,
    APPROVED_BY,
    APPROVED_ENDPOINT,
    APPROVED_HOST,
    APPROVED_MODEL,
    APPROVED_MODEL_DIGEST,
    APPROVED_OLLAMA_HOST,
    APPROVED_OPENAI_BASE,
    REASONING_EFFORT,
    APPROVED_AT,
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


def normalize_ollama_base_url(base_url: str) -> str:
    """Match crewai's ollama normalizer. A missing port becomes 11434.

    That default is the approved pilot port only for host 127.0.0.1.
    localhost and port 11435 stay refused.
    """
    if "://" not in base_url:
        base_url = "http://" + base_url
    parts = urlsplit(base_url)
    netloc = parts.netloc
    if parts.scheme == "http" and parts.port is None:
        netloc = netloc + ":%s" % APPROVED_PORT
    path = parts.path.rstrip("/")
    if not path.endswith("/v1"):
        path = path + "/v1"
    return urlunsplit((parts.scheme, netloc, path, parts.query, parts.fragment))


def effective_endpoint(value: object) -> str:
    """Return host:port only when the URL is exactly the approved loopback."""
    if not isinstance(value, str) or not value.strip():
        raise ProviderRefusal("LLM_ENDPOINT_MISMATCH")
    parts = urlsplit(normalize_ollama_base_url(value.strip()))
    if (
        parts.scheme != "http"
        or parts.hostname != APPROVED_HOST
        or parts.port != APPROVED_PORT
        or parts.path.rstrip("/") != "/v1"
        or parts.query
        or parts.fragment
        or parts.username
    ):
        raise ProviderRefusal("LLM_ENDPOINT_MISMATCH")
    return APPROVED_ENDPOINT


def assert_llm_route(spec: object) -> None:
    """Refuse litellm and any endpoint other than 127.0.0.1:11434."""
    if not isinstance(spec, dict):
        raise ProviderRefusal("LLM_ENDPOINT_MISMATCH")
    if spec.get("is_litellm") is not False:
        raise ProviderRefusal("LITELLM_ROUTE_REFUSED")
    if spec.get("base_url") != APPROVED_OPENAI_BASE:
        raise ProviderRefusal("LLM_BASE_URL_REFUSED")
    if spec.get("ollama_host") != APPROVED_OLLAMA_HOST:
        raise ProviderRefusal("OLLAMA_HOST_REFUSED")
    if effective_endpoint(spec["base_url"]) != APPROVED_ENDPOINT:
        raise ProviderRefusal("LLM_ENDPOINT_MISMATCH")
    if effective_endpoint(spec["ollama_host"]) != APPROVED_ENDPOINT:
        raise ProviderRefusal("LLM_ENDPOINT_MISMATCH")


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
    if data.get("approved_by") != APPROVED_BY or data.get("approved_at") != APPROVED_AT:
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
    if data.get("reasoning_effort") != REASONING_EFFORT:
        raise ProviderRefusal("REASONING_EFFORT_REFUSED")
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
        "reasoning_effort": REASONING_EFFORT,
        "remote_apis_allowed": False,
        "paid_apis_allowed": False,
    }


def binds_from_proc(text: str, port: int, ipv6: bool = False) -> list:
    """TCP LISTEN rows from /proc/net/tcp. This reads a file and does not open a socket."""
    if not isinstance(text, str) or isinstance(port, bool) or not isinstance(port, int):
        raise ProviderRefusal("OLLAMA_BIND_UNPROVEN")
    rows = []
    for line in text.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 4 or parts[3] != "0A":
            continue
        local = parts[1]
        if ":" not in local:
            raise ProviderRefusal("OLLAMA_BIND_UNPROVEN")
        ip_hex, port_hex = local.rsplit(":", 1)
        try:
            row_port = int(port_hex, 16)
        except ValueError as exc:
            raise ProviderRefusal("OLLAMA_BIND_UNPROVEN") from exc
        if row_port != port:
            continue
        rows.append({"address": _proc_address(ip_hex, ipv6), "port": row_port})
    return rows


def _proc_address(ip_hex: str, ipv6: bool) -> str:
    try:
        raw = bytes.fromhex(ip_hex)
    except ValueError as exc:
        raise ProviderRefusal("OLLAMA_BIND_UNPROVEN") from exc
    if not ipv6:
        if len(raw) != 4:
            raise ProviderRefusal("OLLAMA_BIND_UNPROVEN")
        return ".".join(str(byte) for byte in raw[::-1])
    if len(raw) != 16:
        raise ProviderRefusal("OLLAMA_BIND_UNPROVEN")
    words = [raw[index:index + 4][::-1] for index in range(0, 16, 4)]
    addr = b"".join(words)
    if addr == b"\x00" * 16:
        return "::"
    if addr == b"\x00" * 15 + b"\x01":
        return "::1"
    return ":".join(addr[index:index + 2].hex() for index in range(0, 16, 2))


def binds_from_netstat(text: str, port: int) -> list:
    """Listening TCP rows from netstat -ano, by column shape. No socket is opened.

    The English word LISTENING is not required. Port 11435 is refused.
    """
    from office_v2_crewai.usage_guard import UsageRefusal, parse_netstat, tcp_listener_binds

    try:
        return tcp_listener_binds(parse_netstat(text), port)
    except UsageRefusal as exc:
        raise ProviderRefusal("OLLAMA_BIND_UNPROVEN") from exc


def binds_from_lsof(text: str, port: int) -> list:
    """LISTEN rows from lsof -nP -iTCP -sTCP:LISTEN. A header alone is an empty set."""
    if not isinstance(text, str) or isinstance(port, bool) or not isinstance(port, int):
        raise ProviderRefusal("OLLAMA_BIND_UNPROVEN")
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    header = [part.upper() for part in lines[0].split()]
    if "NAME" not in header:
        raise ProviderRefusal("OLLAMA_BIND_UNPROVEN")
    name_index = header.index("NAME")
    rows = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) <= name_index:
            raise ProviderRefusal("OLLAMA_BIND_UNPROVEN")
        name = " ".join(parts[name_index:])
        if "(LISTEN)" not in name.upper():
            raise ProviderRefusal("OLLAMA_BIND_UNPROVEN")
        endpoint = name.split()[0]
        if endpoint.startswith("[") and "]" in endpoint:
            host = endpoint[1:endpoint.index("]")]
            port_text = endpoint.rsplit(":", 1)[-1]
        else:
            host, sep, port_text = endpoint.rpartition(":")
            if not sep:
                raise ProviderRefusal("OLLAMA_BIND_UNPROVEN")
        try:
            row_port = int(port_text)
        except ValueError as exc:
            raise ProviderRefusal("OLLAMA_BIND_UNPROVEN") from exc
        if row_port != port:
            continue
        if host == "*":
            host = "0.0.0.0"
        rows.append({"address": host, "port": row_port})
    return rows


def collect_ollama_binds(port: int = APPROVED_PORT, observe=None) -> list:
    """Listener rows for the approved port. The default observer does not open a socket."""
    if isinstance(port, bool) or port != APPROVED_PORT:
        raise ProviderRefusal("OLLAMA_BIND_UNPROVEN")
    if observe is not None:
        try:
            rows = observe()
        except ProviderRefusal:
            raise
        except (OSError, ValueError, TypeError) as exc:
            raise ProviderRefusal("OLLAMA_BIND_UNPROVEN") from exc
    else:
        rows = _platform_ollama_binds(port)
    if not isinstance(rows, list):
        raise ProviderRefusal("OLLAMA_BIND_UNPROVEN")
    return rows


def _platform_ollama_binds(port: int) -> list:
    import sys
    from pathlib import Path

    if sys.platform == "linux":
        tcp = Path("/proc/net/tcp")
        if not tcp.is_file():
            raise ProviderRefusal("OLLAMA_BIND_UNPROVEN")
        try:
            rows = binds_from_proc(tcp.read_text(encoding="ascii", errors="replace"), port, ipv6=False)
            tcp6 = Path("/proc/net/tcp6")
            if tcp6.is_file():
                rows.extend(binds_from_proc(tcp6.read_text(encoding="ascii", errors="replace"), port, ipv6=True))
        except OSError as exc:
            raise ProviderRefusal("OLLAMA_BIND_UNPROVEN") from exc
        return rows
    if sys.platform == "darwin":
        return _lsof_binds(port)
    if sys.platform == "win32":
        return _netstat_binds(port)
    raise ProviderRefusal("OLLAMA_BIND_UNPROVEN")


def _lsof_binds(port: int) -> list:
    import subprocess

    from office_v2_crewai.usage_guard import run_trusted_listener, trusted_listener_binary

    binary = trusted_listener_binary("lsof", "darwin")
    if binary is None:
        raise ProviderRefusal("OLLAMA_BIND_UNPROVEN")
    try:
        proc = run_trusted_listener(
            binary,
            [binary, "-nP", "-iTCP:%s" % port, "-sTCP:LISTEN"],
        )
    except (OSError, subprocess.SubprocessError, UnicodeError) as exc:
        # Native listener output may use an unexpected Windows OEM code page.
        # Text decoding errors are refusals, never unclassified exceptions.
        raise ProviderRefusal("OLLAMA_BIND_UNPROVEN") from exc
    if proc.returncode == 1 and not (proc.stdout or "").strip() and not (proc.stderr or "").strip():
        return []
    if proc.returncode != 0:
        raise ProviderRefusal("OLLAMA_BIND_UNPROVEN")
    return binds_from_lsof(proc.stdout or "", port)


def _netstat_binds(port: int) -> list:
    """Approved-port binds from ``netstat -ano`` column shape only."""
    import subprocess

    from office_v2_crewai.usage_guard import (
        WINDOWS_NETSTAT,
        UsageRefusal,
        parse_netstat,
        run_trusted_listener,
        tcp_listener_binds,
        trusted_listener_binary,
    )

    if isinstance(port, bool) or port != APPROVED_PORT:
        raise ProviderRefusal("OLLAMA_BIND_UNPROVEN")
    binary = trusted_listener_binary("netstat", "win32")
    if binary != WINDOWS_NETSTAT:
        raise ProviderRefusal("OLLAMA_BIND_UNPROVEN")
    try:
        proc = run_trusted_listener(
            binary, [binary, "-ano"], path_value=str(Path(binary).parent),
        )
    except (OSError, subprocess.SubprocessError, UnicodeError) as exc:
        # Native listener output may use an unexpected Windows OEM code page.
        # Text decoding errors are refusals, never unclassified exceptions.
        raise ProviderRefusal("OLLAMA_BIND_UNPROVEN") from exc
    if proc.returncode != 0:
        raise ProviderRefusal("OLLAMA_BIND_UNPROVEN")
    try:
        return tcp_listener_binds(parse_netstat(proc.stdout or ""), port)
    except UsageRefusal as exc:
        raise ProviderRefusal("OLLAMA_BIND_UNPROVEN") from exc


def digest_from_tags(body: object, model: str = APPROVED_MODEL) -> str:
    """Read the digest from Ollama /api/tags. /api/show on 0.40.6 has no digest."""
    if not isinstance(body, dict):
        raise ProviderRefusal("MODEL_DIGEST_MISMATCH")
    models = body.get("models")
    if not isinstance(models, list) or not models:
        raise ProviderRefusal("MODEL_DIGEST_MISMATCH")
    wanted = model.casefold()
    found = None
    for row in models:
        if not isinstance(row, dict):
            continue
        name = row.get("name") if isinstance(row.get("name"), str) else row.get("model")
        if not isinstance(name, str) or name.casefold() != wanted:
            continue
        if found is not None:
            raise ProviderRefusal("MODEL_DIGEST_MISMATCH")
        found = row.get("digest")
    if found is None:
        raise ProviderRefusal("MODEL_DIGEST_MISMATCH")
    return digest_hex(found)


def assert_ollama_bind(listeners: object, port: int = APPROVED_PORT) -> None:
    """Refuse a server on the approved port that is not bound to loopback.

    0.0.0.0 and :: are refused. An empty observation is unproven. This does
    not open a socket; the caller passes the listener rows.
    """
    if port != APPROVED_PORT or not isinstance(listeners, list) or not listeners:
        raise ProviderRefusal("OLLAMA_BIND_UNPROVEN")
    saw_loopback = False
    for row in listeners:
        if not isinstance(row, dict):
            raise ProviderRefusal("OLLAMA_BIND_UNPROVEN")
        address = row.get("address")
        row_port = row.get("port")
        if not isinstance(address, str) or isinstance(row_port, bool) or not isinstance(row_port, int):
            raise ProviderRefusal("OLLAMA_BIND_UNPROVEN")
        if row_port != port:
            continue
        host = address.strip().strip("[]").lower()
        if host in {"127.0.0.1", "::1"}:
            saw_loopback = True
            continue
        raise ProviderRefusal("OLLAMA_BIND_WILDCARD")
    if not saw_loopback:
        raise ProviderRefusal("OLLAMA_BIND_UNPROVEN")


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

    def complete(self, messages: object, urlopen=None, env: dict | None = None,
                 binds: object = None, harness=None, started: float | None = None,
                 now: float | None = None) -> str:
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
        if self.config.get("reasoning_effort") != REASONING_EFFORT:
            raise ProviderRefusal("REASONING_EFFORT_REFUSED")
        if not no_cloud_enabled(environment):
            raise ProviderRefusal("OLLAMA_NO_CLOUD_ABSENT")
        assert_llm_route({
            "base_url": APPROVED_OPENAI_BASE,
            "ollama_host": environment.get("OLLAMA_HOST"),
            "is_litellm": False,
        })
        from office_v2_crewai.sandbox import assert_proxy_env
        assert_proxy_env(environment)
        timeout = _attempt_timeout(harness, started, now)
        if binds is None:
            binds = collect_ollama_binds()
        assert_ollama_bind(binds)
        base_url = assert_loopback_url(self.config.get("base_url"))
        if urlopen is None:
            urlopen = open_loopback
        listed = _open_json(urlopen, base_url + "/api/tags", None, timeout)
        if digest_from_tags(listed) != APPROVED_MODEL_DIGEST:
            raise ProviderRefusal("MODEL_DIGEST_MISMATCH")
        self.calls += 1
        payload = {
            "model": APPROVED_MODEL,
            "messages": _messages(messages),
            "stream": False,
            "think": False,
            "reasoning_effort": REASONING_EFFORT,
            "options": {"temperature": 0.0},
        }
        body = _open_json(urlopen, base_url + "/api/chat", payload, timeout)
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


def _attempt_timeout(harness, started: float | None, now: float | None) -> float:
    """Enforce the 600s harness once a start time exists. Otherwise cap the socket at 30s."""
    if started is None:
        return 30
    if now is None:
        import time
        now = time.monotonic()
    from office_v2_crewai.kill_harness import KillHarness
    clock = harness if harness is not None else KillHarness()
    return clock.socket_timeout(started, now)


def open_loopback(request, timeout: float = 30):
    """Open one loopback URL. Redirects are refused, including 301/302/307/308."""
    from urllib import request as urlrequest

    class _RefuseRedirects(urlrequest.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise ProviderRefusal("MODEL_REDIRECT_REFUSED")

    opener = urlrequest.build_opener(_RefuseRedirects, urlrequest.ProxyHandler({}))
    response = opener.open(request, timeout=timeout)
    requested = getattr(request, "full_url", None)
    final = response.geturl()
    if not isinstance(requested, str) or not requested or final != requested:
        response.close()
        raise ProviderRefusal("MODEL_REDIRECT_REFUSED")
    return response


def _open_json(urlopen, target: str, payload: dict | None, timeout: float) -> dict:
    base, _, path = target.partition("/api/")
    assert_loopback_url(base)
    if path not in {"tags", "chat"}:
        raise ProviderRefusal("MODEL_URL_PATH_REFUSED")
    if payload is None:
        if path != "tags":
            raise ProviderRefusal("MODEL_URL_PATH_REFUSED")
        from urllib import request as urlrequest
        request_obj = urlrequest.Request(target, method="GET")
    else:
        if path != "chat":
            raise ProviderRefusal("MODEL_URL_PATH_REFUSED")
        request_obj = _request(target, json.dumps(payload).encode("utf-8"))
    with urlopen(request_obj, timeout=timeout) as response:
        raw = response.read()
    body = json.loads(raw.decode("utf-8"))
    if not isinstance(body, dict):
        raise ProviderRefusal("LOCAL_MODEL_RESPONSE_UNUSABLE")
    return body
