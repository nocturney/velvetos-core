#!/usr/bin/env python3
"""VelvetOS speech-provider adapter for VoiceStudio's OpenAI-compatible API."""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "packages" / "vfom" / "SPEECH-BACKEND.json"
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
PROVIDER = CONFIG["provider"]
DEFAULTS = CONFIG["defaults"]
ENGINES = CONFIG["engines"]
PROVIDER_MINIMUM_VERSION = str(PROVIDER["minimumVersion"])
PROVIDER_RECOVERY_VERSION = str(PROVIDER["recoveryVersion"])
PROVIDER_RECOVERY_COMMIT = str(PROVIDER["recoveryCommit"])
PROVIDER_VERSION_POLICY = str(PROVIDER.get("versionPolicy") or "latest-compatible")
DEFAULT_ROOT = os.environ.get("VF_SPEECH_URL", str(PROVIDER["serviceRoot"])).rstrip("/")
PLATFORM_DEFAULT_TTS = DEFAULTS.get("ttsModelWindows") if os.name == "nt" else DEFAULTS.get("ttsModelMac")
DEFAULT_TTS_MODEL = os.environ.get(
    "VF_SPEECH_TTS_MODEL",
    str(PLATFORM_DEFAULT_TTS or DEFAULTS["ttsModel"]),
)
DEFAULT_ASR_MODEL = os.environ.get(
    "VF_SPEECH_ASR_MODEL",
    str(DEFAULTS["asrModelWindows"] if os.name == "nt" else DEFAULTS["asrModelMac"]),
)
DEFAULT_VOICE = os.environ.get("VF_SPEECH_VOICE", str(DEFAULTS["voice"]))
API_KEY = os.environ.get("VF_SPEECH_API_KEY", "")
SELECTION_POLICY = ENGINES.get("selectionPolicy") or {}
ALLOWED_OPERATIONS = {"synthesize", "transcribe", "qa"}


def fail(message: str, code: int = 2) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(code)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def semver_tuple(value: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?", value.strip())
    return tuple(int(part) for part in match.groups()) if match else None


_PROVIDER_DISCOVERY_CACHE: tuple[dict[str, Any], str] | None = None


def provider_compatibility() -> tuple[dict[str, Any], str]:
    global _PROVIDER_DISCOVERY_CACHE
    if _PROVIDER_DISCOVERY_CACHE is not None:
        return _PROVIDER_DISCOVERY_CACHE
    discovery = request_json("GET", f"{DEFAULT_ROOT}/.well-known/voicestudio-speech", timeout=4)
    actual = str(discovery.get("service_version") or discovery.get("version") or "").strip().lstrip("v")
    actual_tuple = semver_tuple(actual)
    minimum_tuple = semver_tuple(PROVIDER_MINIMUM_VERSION)
    if actual_tuple is None:
        fail(f"VoiceStudio service version is missing or invalid: {actual!r}", 1)
    if minimum_tuple is None:
        fail(f"VoiceStudio minimum version config is invalid: {PROVIDER_MINIMUM_VERSION!r}", 1)
    if actual_tuple < minimum_tuple:
        fail(
            f"VoiceStudio is below supported minimum {PROVIDER_MINIMUM_VERSION}: found {actual}",
            1,
        )
    _PROVIDER_DISCOVERY_CACHE = (discovery, actual)
    return _PROVIDER_DISCOVERY_CACHE


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        fail(f"request not found: {path}")
    except json.JSONDecodeError as exc:
        fail(f"invalid request JSON: {exc}")
    if not isinstance(data, dict):
        fail("request must be a JSON object")
    return data


def headers(content_type: str | None = None) -> dict[str, str]:
    out = {"User-Agent": f"VelvetOS-Speech/1 VoiceStudio/{PROVIDER_VERSION_POLICY}"}
    if content_type:
        out["Content-Type"] = content_type
    if API_KEY:
        out["Authorization"] = f"Bearer {API_KEY}"
    return out


def request_bytes(
    method: str,
    url: str,
    body: bytes | None = None,
    content_type: str | None = None,
    timeout: int | None = None,
) -> tuple[bytes, dict[str, str]]:
    req = urllib.request.Request(url, data=body, method=method, headers=headers(content_type))
    attempts = int(DEFAULTS.get("maxAttempts", 2))
    timeout = int(timeout or DEFAULTS.get("timeoutSeconds", 180))
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read(), dict(resp.headers.items())
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            last = exc
            if attempt + 1 < attempts:
                time.sleep(1.0)
    fail(f"VoiceStudio request failed: {last}")
    raise AssertionError


def request_json(method: str, url: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    raw, _ = request_bytes(method, url, body, "application/json" if body else None, timeout)
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"VoiceStudio returned non-JSON response from {url}: {exc}")
    if not isinstance(data, dict):
        fail(f"VoiceStudio returned unexpected JSON from {url}")
    return data


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    text = re.sub(r"[\u0591-\u05c7]", "", text)
    text = re.sub(r"[^0-9a-z\u0590-\u05ff]+", " ", text)
    return " ".join(text.split())


def similarity(expected: str, actual: str) -> float:
    a, b = normalize_text(expected), normalize_text(actual)
    if not a and not b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def multipart_file(path: Path, fields: dict[str, str]) -> tuple[bytes, str]:
    boundary = f"----velvetos-{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for key, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode(),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    chunks.extend(
        [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'.encode(),
            f"Content-Type: {mime}\r\n\r\n".encode(),
            path.read_bytes(),
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def transcribe(path: Path, model: str, language: str = "he", response_format: str = "json") -> tuple[str, Any]:
    if not path.is_file():
        fail(f"input audio not found: {path}")
    body, content_type = multipart_file(
        path,
        {"model": model, "language": language, "response_format": response_format},
    )
    raw, _ = request_bytes("POST", f"{DEFAULT_ROOT}/v1/audio/transcriptions", body, content_type)
    if response_format in {"srt", "vtt", "text"}:
        text = raw.decode("utf-8", errors="replace")
        return text, text
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        fail(f"invalid transcription response: {exc}")
    text = str(data.get("text") or "") if isinstance(data, dict) else ""
    if not text.strip():
        fail("transcription returned no text")
    return text, data


def synthesize(req: dict[str, Any]) -> Path:
    _, provider_version = provider_compatibility()
    text = str(req.get("text") or "").strip()
    if not text:
        fail("synthesize requires text")
    output_raw = str(req.get("outputAudio") or "").strip()
    if not output_raw:
        fail("synthesize requires outputAudio")
    output = Path(output_raw).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    model = str(req.get("ttsModel") or DEFAULT_TTS_MODEL)
    commercial = bool(req.get("commercialPublish", True))
    payload = {
        "model": model,
        "voice": str(req.get("voice") or DEFAULT_VOICE),
        "input": text,
        "response_format": str(req.get("responseFormat") or DEFAULTS["responseFormat"]),
        "speed": float(req.get("speed") or DEFAULTS["speed"]),
    }
    audio, response_headers = request_bytes(
        "POST",
        f"{DEFAULT_ROOT}/v1/audio/speech",
        json.dumps(payload).encode("utf-8"),
        "application/json",
    )
    if len(audio) < 64:
        fail("speech response is unexpectedly small")
    output.write_bytes(audio)
    receipt = {
        "schemaVersion": 1,
        "provider": "voicestudio",
        "providerVersion": provider_version,
        "providerVersionPolicy": PROVIDER_VERSION_POLICY,
        "providerMinimumVersion": PROVIDER_MINIMUM_VERSION,
        "providerRecoveryVersion": PROVIDER_RECOVERY_VERSION,
        "providerRecoveryCommit": PROVIDER_RECOVERY_COMMIT,
        "jobId": req.get("jobId"),
        "operation": "synthesize",
        "model": model,
        "voice": payload["voice"],
        "language": str(req.get("language") or ENGINES["language"]),
        "commercialPublish": commercial,
        "toolCostPolicy": "free-tools-allowed",
        "commercialSuitabilityRuntimeBlocked": False,
        "licenseMetadataTracked": bool(SELECTION_POLICY.get("licenseMetadataMustBeTracked", True)),
        "output": str(output),
        "bytes": len(audio),
        "sha256": sha256_file(output),
        "contentType": response_headers.get("Content-Type"),
        "generatedAt": now_iso(),
        "publishAuthorized": False,
    }
    receipt_path = Path(str(output) + ".speech.receipt.json")
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK speech generated output={output} receipt={receipt_path}")
    return output


def qa(req: dict[str, Any], audio_path: Path | None = None) -> dict[str, Any]:
    _, provider_version = provider_compatibility()
    expected = str(req.get("text") or "").strip()
    if not expected:
        fail("qa requires expected text")
    path = audio_path or Path(str(req.get("inputAudio") or "")).expanduser().resolve()
    model = str(req.get("asrModel") or DEFAULT_ASR_MODEL)
    heard, _ = transcribe(path, model, str(req.get("language") or ENGINES["language"]), "json")
    score = similarity(expected, heard)
    threshold = float(req.get("minimumSimilarity") or DEFAULTS["qaMinimumSimilarity"])
    result = {
        "schemaVersion": 1,
        "provider": "voicestudio",
        "providerVersion": provider_version,
        "providerVersionPolicy": PROVIDER_VERSION_POLICY,
        "providerMinimumVersion": PROVIDER_MINIMUM_VERSION,
        "providerRecoveryVersion": PROVIDER_RECOVERY_VERSION,
        "jobId": req.get("jobId"),
        "operation": "back-transcription-qa",
        "asrModel": model,
        "audio": str(path),
        "audioSha256": sha256_file(path),
        "expected": expected,
        "heard": heard,
        "similarity": round(score, 6),
        "minimumSimilarity": threshold,
        "status": "PASS" if score >= threshold else "FAIL",
        "checkedAt": now_iso(),
        "publishAuthorized": False,
    }
    out = Path(str(req.get("outputTranscript") or (str(path) + ".speech.qa.json"))).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if score < threshold:
        fail(f"speech QA similarity {score:.3f} below threshold {threshold:.3f}", 1)
    print(f"OK speech QA receipt={out}")
    return result


def doctor() -> int:
    facts: dict[str, Any] = {
        "provider": "voicestudio",
        "versionPolicy": PROVIDER_VERSION_POLICY,
        "minimumVersion": PROVIDER_MINIMUM_VERSION,
        "recoveryVersion": PROVIDER_RECOVERY_VERSION,
        "recoveryCommit": PROVIDER_RECOVERY_COMMIT,
        "serviceRoot": DEFAULT_ROOT,
        "ttsModel": DEFAULT_TTS_MODEL,
        "asrModel": DEFAULT_ASR_MODEL,
        "voice": DEFAULT_VOICE,
        "platform": os.name,
    }
    try:
        discovery, actual = provider_compatibility()
    except SystemExit:
        print(json.dumps(facts, ensure_ascii=False, indent=2))
        print("FAIL VoiceStudio speech service is unreachable or incompatible", file=sys.stderr)
        return 1
    facts["discovery"] = discovery
    facts["actualVersion"] = actual
    print(json.dumps(facts, ensure_ascii=False, indent=2))
    print(
        f"OK VoiceStudio speech provider compatible actual={actual} "
        f"minimum={PROVIDER_MINIMUM_VERSION} policy={PROVIDER_VERSION_POLICY}"
    )
    return 0


def validate_request(req: dict[str, Any]) -> str:
    job_id = str(req.get("jobId") or "")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", job_id):
        fail("request.jobId must match ^[A-Za-z0-9._-]+$")
    operation = str(req.get("operation") or "")
    if operation not in ALLOWED_OPERATIONS:
        fail(f"request.operation must be one of {sorted(ALLOWED_OPERATIONS)}")
    return operation


def run(path: Path) -> None:
    req = read_json(path)
    operation = validate_request(req)
    provider_compatibility()
    if operation == "synthesize":
        audio = synthesize(req)
        if bool(req.get("qaBackTranscribe", DEFAULTS["qaBackTranscribe"])):
            qa_req = dict(req)
            qa_req["inputAudio"] = str(audio)
            qa(qa_req, audio)
    elif operation == "transcribe":
        audio = Path(str(req.get("inputAudio") or "")).expanduser().resolve()
        model = str(req.get("asrModel") or DEFAULT_ASR_MODEL)
        text, raw = transcribe(audio, model, str(req.get("language") or ENGINES["language"]), "json")
        output = req.get("outputTranscript")
        if output:
            out = Path(str(output)).expanduser().resolve()
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n" if isinstance(raw, dict) else text, encoding="utf-8")
        print(text)
    else:
        qa(req)


def main() -> None:
    parser = argparse.ArgumentParser(description="VelvetOS VoiceStudio speech adapter")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    run_parser = sub.add_parser("run")
    run_parser.add_argument("request", type=Path)
    args = parser.parse_args()
    if args.command == "doctor":
        raise SystemExit(doctor())
    run(args.request)


if __name__ == "__main__":
    main()
