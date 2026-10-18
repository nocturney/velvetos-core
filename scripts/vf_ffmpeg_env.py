"""Local ffmpeg capability probe. No network.

A missing binary, filter, encoder, or build flag is SKIP_ENV_MISSING_<CAP>.
The probe runs `ffmpeg -filters`, `ffmpeg -buildconf`, and `ffmpeg -encoders`
on the binary already on PATH. Native encoders such as aac are listed by
`-encoders` because they are not build flags. A render that advertises the
capability and then produces the wrong pixels is not a skip.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass

PROBE_TIMEOUT = 20


@dataclass(frozen=True)
class EnvGap:
    token: str
    reason: str

    @property
    def line(self) -> str:
        return f"{self.token} {self.reason}"


class _ProbeError(Exception):
    def __init__(self, flag: str, detail: str) -> None:
        self.flag = flag
        super().__init__(detail)


def _gap(cap: str, reason: str) -> EnvGap:
    return EnvGap(f"SKIP_ENV_MISSING_{cap}", reason)


def _truthy_ci(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"true", "1"}


def ci_skip_failure(gap: EnvGap | None) -> str | None:
    """CI must run the video-privacy, public-video, and caption tests.

    A local host may skip. When GITHUB_ACTIONS or CI is true/True/TRUE/1 the
    same gap is a failure line, so a missing ffmpeg cannot pass those sensors
    silently. Empty and unset values are not CI.
    """
    if gap is None:
        return None
    if _truthy_ci(os.environ.get("GITHUB_ACTIONS")) or _truthy_ci(os.environ.get("CI")):
        return gap.line
    return None


def _run(binary: str, flag: str) -> str:
    command = [binary, "-hide_banner", "-nostdin", flag]
    try:
        proc = subprocess.run(command, text=True, capture_output=True, timeout=PROBE_TIMEOUT)
    except subprocess.TimeoutExpired as exc:
        raise _ProbeError(flag, f"timed out after {PROBE_TIMEOUT}s") from exc
    except OSError as exc:
        raise _ProbeError(flag, str(exc)) from exc
    return (proc.stdout or "") + "\n" + (proc.stderr or "")


def _filter_names(text: str) -> set[str]:
    names: set[str] = set()
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] and parts[1] and not parts[0].startswith("-"):
            names.add(parts[1])
    return names


def _encoder_names(text: str) -> set[str]:
    names: set[str] = set()
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0][:1] in {"V", "A", "."}:
            names.add(parts[1])
    return names


def _tools() -> tuple[str | None, EnvGap | None]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None, _gap(
            "FFMPEG",
            "ffmpeg is not on PATH, so ffmpeg -filters and ffmpeg -buildconf were not run",
        )
    if shutil.which("ffprobe") is None:
        return None, _gap(
            "FFPROBE",
            "ffprobe is not on PATH, so ffmpeg -filters and ffmpeg -buildconf were not run",
        )
    return ffmpeg, None


@dataclass(frozen=True)
class _Probe:
    filters: set[str]
    build: str
    encoders: set[str]


def _probe(ffmpeg: str) -> tuple[_Probe | None, EnvGap | None]:
    try:
        filters = _run(ffmpeg, "-filters")
        build = _run(ffmpeg, "-buildconf")
        encoders = _run(ffmpeg, "-encoders")
    except _ProbeError as exc:
        return None, _gap("FFMPEG", f"ffmpeg {exc.flag} did not finish: {exc}")
    return _Probe(_filter_names(filters), build, _encoder_names(encoders)), None


def _missing_filter(names: set[str], needed: tuple[str, ...]) -> EnvGap | None:
    for name in needed:
        if name not in names:
            return _gap(name.upper(), f"ffmpeg -filters has no {name} filter")
    return None


def _missing_flag(build: str, flags: tuple[tuple[str, str], ...]) -> EnvGap | None:
    missing = [(flag, cap) for flag, cap in flags if flag not in build]
    if not missing:
        return None
    listed = ", ".join(flag for flag, _cap in missing)
    return _gap(missing[0][1], f"ffmpeg -buildconf has no {listed}")


def _missing_encoder(names: set[str], needed: tuple[str, ...]) -> EnvGap | None:
    for name in needed:
        if name not in names:
            return _gap(name.upper(), f"ffmpeg -encoders has no {name} encoder")
    return None


def capability_gap(
    *,
    filters: tuple[str, ...] = (),
    flags: tuple[tuple[str, str], ...] = (),
    encoders: tuple[str, ...] = (),
) -> EnvGap | None:
    """First missing capability, in tool, filter, build-flag, encoder order."""
    ffmpeg, gap = _tools()
    if gap is not None or ffmpeg is None:
        return gap
    probed, gap = _probe(ffmpeg)
    if gap is not None or probed is None:
        return gap
    return (
        _missing_filter(probed.filters, filters)
        or _missing_flag(probed.build, flags)
        or _missing_encoder(probed.encoders, encoders)
    )


CAPTION_FILTERS = ("zoompan", "drawtext", "overlay", "afade", "scale", "crop", "format")
CAPTION_FLAGS = (
    ("--enable-libfribidi", "FRIBIDI"),
    ("--enable-libass", "LIBASS"),
    ("--enable-libharfbuzz", "HARFBUZZ"),
    ("--enable-libx264", "LIBX264"),
)
CAPTION_ENCODERS = ("libx264", "aac")
NORMALIZATION_FILTERS = ("sidedata", "asidedata")
NORMALIZATION_FLAGS = (("--enable-libx264", "LIBX264"),)
NORMALIZATION_ENCODERS = ("libx264", "aac")
PUBLICATION_ENCODERS = ("mpeg4",)


def caption_gap() -> EnvGap | None:
    return capability_gap(filters=CAPTION_FILTERS, flags=CAPTION_FLAGS, encoders=CAPTION_ENCODERS)


def normalization_gap() -> EnvGap | None:
    return capability_gap(
        filters=NORMALIZATION_FILTERS,
        flags=NORMALIZATION_FLAGS,
        encoders=NORMALIZATION_ENCODERS,
    )


def publication_gap() -> EnvGap | None:
    return normalization_gap() or capability_gap(encoders=PUBLICATION_ENCODERS)
