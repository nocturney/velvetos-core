#!/usr/bin/env python3
"""Deterministic ffmpeg + SVG caption fallback for Velvet reel stills.

HyperFrames stays the primary compositor. This bridge renders the same
request.json when HyperFrames is unavailable: a product still, a slow zoom,
a Hebrew caption in Rubik with the copper accent, safe-area placement,
and an audio track with fade in/out. The SVG keeps logical text with
direction=rtl. The pixels come from drawtext, which has no RTL base option,
so the line is reordered to visual RTL and drawn with text_shaping=0.
It writes an ffprobe + SHA-256 receipt and fails closed. An ffprobe or ffmpeg
timeout, and any unparsable probe field, exits with an explicit FAIL reason.
It does not install packages and it does not publish.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NoReturn
from xml.sax.saxutils import escape as xml_escape

BACKEND = "ffmpeg-svg-caption-composition"
ACCEPTED_BACKENDS = {"hyperframes", BACKEND}
COPPER = "#a86838"
BRAND_SAFE_X = 86
BRAND_SAFE_TOP = 150
BRAND_SAFE_BOTTOM = 230
FADE_IN_SEC = 0.6
FADE_OUT_SEC = 1.7
DEFAULT_ZOOM_END = 1.08
DEFAULT_PAN_Y = 20.0
DEFAULT_ORIGIN = (0.5, 0.40)
HEBREW_RE = re.compile(r"[\u0590-\u05FF]")
PORTRAIT = (1080, 1920)
_BIDI_CONTROLS = set("\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069")


def _bidi_class(ch: str) -> str:
    if ch in _BIDI_CONTROLS:
        return "BN"
    if ("\u0590" <= ch <= "\u05FF") or ("\uFB1D" <= ch <= "\uFB4F") or ("\u0600" <= ch <= "\u06FF"):
        return "R"
    code = ord(ch)
    if ("A" <= ch <= "Z") or ("a" <= ch <= "z") or (0x00C0 <= code <= 0x024F):
        return "L"
    if "0" <= ch <= "9":
        return "EN"
    return "ON"


def visual_order(text: str) -> str:
    """Return LTR glyph order for a caption whose paragraph base is RTL.

    ffmpeg drawtext hardcodes an LTR fribidi paragraph and exposes no
    base-direction option. Hebrew does not need complex shaping, so the
    caption is pre-ordered and drawn with text_shaping=0. Browsers still
    receive the logical string in the SVG.
    """
    if not text:
        return text
    chars = list(text)
    classes = [_bidi_class(ch) for ch in chars]
    for index, ch in enumerate(chars):
        if classes[index] != "ON" or ch not in ".,:/":
            continue
        previous = next((classes[pos] for pos in range(index - 1, -1, -1) if classes[pos] != "BN"), None)
        following = next((classes[pos] for pos in range(index + 1, len(classes)) if classes[pos] != "BN"), None)
        if previous == "EN" and following == "EN":
            classes[index] = "EN"

    def nearest(start: int, step: int) -> str:
        pos = start
        while 0 <= pos < len(classes):
            if classes[pos] in {"R", "L", "EN"}:
                return "L" if classes[pos] in {"L", "EN"} else "R"
            pos += step
        return "R"

    resolved: list[str] = []
    for index, kind in enumerate(classes):
        if kind in {"R", "L", "EN"}:
            resolved.append(kind)
            continue
        left = nearest(index - 1, -1)
        right = nearest(index + 1, 1)
        resolved.append(left if left == right else "R")
    kept = [(ch, 1 if kind == "R" else 2) for ch, kind, cls in zip(chars, resolved, classes) if cls != "BN"]
    if not kept:
        return ""
    sequence = kept
    for level in range(max(item[1] for item in sequence), 0, -1):
        rewritten: list[tuple[str, int]] = []
        index = 0
        while index < len(sequence):
            if sequence[index][1] >= level:
                end = index + 1
                while end < len(sequence) and sequence[end][1] >= level:
                    end += 1
                rewritten.extend(reversed(sequence[index:end]))
                index = end
            else:
                rewritten.append(sequence[index])
                index += 1
        sequence = rewritten
    # UAX #9 L4: mirror paired brackets that resolved to an RTL level.
    # Reversal alone leaves "(" facing the wrong way once the run is drawn LTR.
    mirrors = str.maketrans("()[]{}<>«»‹›", ")(][}{><»«›‹")
    return "".join(ch.translate(mirrors) if level % 2 else ch for ch, level in sequence)


def fail(message: str, code: int = 2) -> NoReturn:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(code)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def runtime_tmp_dir(output: Path | None = None, explicit: str | None = None) -> Path:
    """Temp directory for caption work. Never the process system temp.

    Precedence is an explicit --tmp-dir, then VELVETOS_RUNTIME_ROOT/tmp,
    then a directory beside the render output, then a gitignored repo-local
    directory for doctor when no request exists.
    """
    chosen = (explicit or "").strip()
    env = os.environ.get("VELVETOS_RUNTIME_ROOT", "").strip()
    if chosen:
        root = Path(chosen).expanduser()
    elif env:
        root = Path(env).expanduser() / "tmp"
    elif output is not None:
        root = Path(output).expanduser().resolve().parent / ".vf-tmp"
    else:
        root = repo_root() / ".local-devtools" / "vf-caption-tmp"
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def release_derived_tmp(tmp_root: Path, output: Path, explicit: str | None) -> None:
    """Remove an empty derived .vf-tmp directory after a successful render.

    An explicit --tmp-dir, and the tmp directory under VELVETOS_RUNTIME_ROOT,
    are the operator's directories and are left in place. An empty .vf-tmp
    beside the output is still removed when that runtime root is set for
    another reason. A non-empty directory is left in place. Failure to
    remove the directory does not discard the render.
    """
    if (explicit or "").strip():
        return
    derived = Path(output).expanduser().resolve().parent / ".vf-tmp"
    env = os.environ.get("VELVETOS_RUNTIME_ROOT", "").strip()
    try:
        resolved = tmp_root.resolve()
        if env and resolved == (Path(env).expanduser() / "tmp").resolve():
            return
        if resolved != derived.resolve() or not derived.is_dir():
            return
        if any(derived.iterdir()):
            return
        derived.rmdir()
    except OSError:
        return


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"request not found: {path}")
    except json.JSONDecodeError as exc:
        fail(f"invalid request JSON: {exc}")
    if not isinstance(value, dict):
        fail("request must be a JSON object")
    return value


def require_text(obj: dict[str, Any], key: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        fail(f"request.{key} must be a non-empty string")
    return value.strip()


def resolve_under(base: Path, raw: str, label: str) -> Path:
    candidate = (base / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
    try:
        candidate.relative_to(base.resolve())
    except ValueError:
        fail(f"{label} must stay under projectDir")
    return candidate


def escape_filter_text(text: str) -> str:
    """Escape a path string for an ffmpeg filtergraph argv.

    Windows drive colons must be escaped with a doubled backslash. That is the
    form ffmpeg 9 essentials accepts when the graph is a direct argument.
    """
    text = text.replace("\\", "/")
    if any(char in text for char in (" ", "'", ",", "[", "]")):
        fail(f"path is not safe inside an ffmpeg filtergraph: {text}")
    return text.replace(":", "\\\\:")


def escape_filter_path(path: Path) -> str:
    return escape_filter_text(path.resolve().as_posix())


def rubik_font() -> dict[str, Any]:
    tokens_path = repo_root() / "packages" / "vfbrand" / "brand-tokens.json"
    if not tokens_path.is_file():
        fail(f"brand tokens missing: {tokens_path}")
    tokens = json.loads(tokens_path.read_text(encoding="utf-8"))
    families = ((tokens.get("fonts") or {}).get("families") or [])
    rubik = next((row for row in families if row.get("family") == "Rubik"), None)
    if not rubik:
        fail("brand tokens have no Rubik family")
    path = repo_root() / str(rubik["file"])
    if not path.is_file():
        fail(f"Rubik font file missing: {path}")
    actual = sha256_file(path)
    if actual != rubik.get("sha256"):
        fail("Rubik font sha256 does not match brand-tokens.json")
    return {"path": path, "family": "Rubik", "sha256": actual}


# Static instances of the pinned variable font. drawtext does not apply the
# wght axis, so the headline and subhead use these files (brand roles 700 / 600).
RUBIK_WEIGHTS = {
    700: (
        "packages/vfbrand/assets/fonts/rubik/Rubik-wght700.ttf",
        "c8ccdd2d106f02d7652beb11f9c41ab3264cca727ae6e7eaa570414d14d0eb1e",
    ),
    600: (
        "packages/vfbrand/assets/fonts/rubik/Rubik-wght600.ttf",
        "d09a67cea25e5a1f03cbf26d2702b126ff1d45c49861068bd3376559b7eaede3",
    ),
}


def rubik_weight_font(weight: int) -> Path:
    spec = RUBIK_WEIGHTS.get(weight)
    if spec is None:
        fail(f"Rubik weight instance is not pinned: {weight}")
    rel, digest = spec
    path = repo_root() / rel
    if not path.is_file():
        fail(f"Rubik weight {weight} instance missing: {path}")
    actual = sha256_file(path)
    if actual != digest:
        fail(f"Rubik weight {weight} sha256 does not match")
    return path


def drawn_font_record(weight: int) -> dict[str, Any]:
    path = rubik_weight_font(weight)
    return {"weight": weight, "file": path.name, "sha256": sha256_file(path)}


def fonts_used(layout: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Hashes of the static Rubik files drawtext actually loads."""
    used = {"headline": drawn_font_record(700)}
    if layout.get("subheadLines"):
        used["subhead"] = drawn_font_record(600)
    return used


def css_block(html: str, selector: str) -> str:
    match = re.search(rf"{re.escape(selector)}\s*\{{([^}}]*)\}}", html)
    return match.group(1) if match else ""


def keyframes_body(html: str, name: str) -> str:
    match = re.search(rf"@keyframes\s+{re.escape(name)}\s*\{{", html)
    if not match:
        return ""
    depth = 1
    index = match.end()
    while index < len(html) and depth:
        if html[index] == "{":
            depth += 1
        elif html[index] == "}":
            depth -= 1
        index += 1
    return html[match.end():index - 1]


def css_px(block: str, prop: str, default: float) -> float:
    match = re.search(rf"(?:^|[;{{])\s*{prop}\s*:\s*(-?[0-9.]+)px", block)
    return float(match.group(1)) if match else default


def tag_attr(html: str, tag: str, class_name: str, attr: str) -> str | None:
    for match in re.finditer(rf"<{tag}\b[^>]*>", html, flags=re.IGNORECASE):
        blob = match.group(0)
        if class_name and not re.search(rf'class="[^"]*\b{re.escape(class_name)}\b', blob):
            continue
        found = re.search(rf'\b{attr}="([^"]*)"', blob)
        if found and found.group(1).strip():
            return found.group(1).strip()
    return None


def inner_text(html: str, tag: str, class_name: str) -> str:
    match = re.search(
        rf"<{tag}\b[^>]*class=\"[^\"]*\b{re.escape(class_name)}\b[^\"]*\"[^>]*>(.*?)</{tag}>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return ""
    text = re.sub(r"<[^>]+>", "", match.group(1))
    return re.sub(r"\s+", " ", text).strip()


def parse_composition(html: str, project: Path, variables: dict[str, Any] | None) -> dict[str, Any]:
    variables = variables or {}
    width = int(re.search(r'data-width="(\d+)"', html).group(1)) if re.search(r'data-width="(\d+)"', html) else 0
    height = int(re.search(r'data-height="(\d+)"', html).group(1)) if re.search(r'data-height="(\d+)"', html) else 0
    fps_match = re.search(r'data-fps="(\d+)"', html)
    duration_match = re.search(r'data-duration="([0-9.]+)"', html)
    if not width or not height or not duration_match:
        fail("composition frame must declare data-width, data-height and data-duration")
    duration = float(duration_match.group(1))
    if duration <= 0:
        fail("composition duration must be positive")
    fps = int(fps_match.group(1)) if fps_match else 30

    hero_raw = str(variables.get("heroImage") or "").strip() or tag_attr(html, "img", "hero", "src") or tag_attr(html, "img", "", "src")
    if not hero_raw:
        fail("composition has no hero image")
    hero = resolve_under(project, hero_raw, "hero image")
    if not hero.is_file():
        fail(f"hero image missing: {hero}")

    audio_raw = str(variables.get("audioFile") or "").strip() or tag_attr(html, "audio", "", "src")
    audio = None
    if audio_raw:
        audio = resolve_under(project, audio_raw, "audio")
        if not audio.is_file():
            fail(f"audio file missing: {audio}")

    headline = str(variables.get("headline") or "").strip() or inner_text(html, "h1", "headline")
    subhead = str(variables.get("subhead") or "").strip() or inner_text(html, "p", "subhead")
    if not headline:
        fail("composition has no Hebrew headline")
    if not HEBREW_RE.search(headline):
        fail("caption headline must include Hebrew")

    accent = str(variables.get("accentHex") or "").strip() or ""
    rule = css_block(html, ".rule")
    color_match = re.search(r"background\s*:\s*(#[0-9A-Fa-f]{6})", rule)
    if not accent and color_match:
        accent = color_match.group(1)
    accent = (accent or COPPER).lower()
    if accent != COPPER:
        fail(f"caption accent must be copper {COPPER}")

    copy = css_block(html, ".copy")
    safe_x = max(BRAND_SAFE_X, css_px(copy, "left", 80), css_px(copy, "right", 80))
    safe_bottom = max(BRAND_SAFE_BOTTOM, css_px(copy, "bottom", 220))
    headline_css = css_block(html, ".headline")
    subhead_css = css_block(html, ".subhead")
    headline_size = css_px(headline_css, "font-size", 84)
    subhead_size = css_px(subhead_css, "font-size", 50)
    rule_w = css_px(rule, "width", 180)
    rule_h = css_px(rule, "height", 10)

    motion = keyframes_body(html, "kenburns")
    scales = [float(value) for value in re.findall(r"scale\(\s*([0-9.]+)\s*\)", motion)]
    if len(scales) >= 2:
        zoom_start, zoom_end = scales[0], scales[-1]
    elif len(scales) == 1:
        zoom_start, zoom_end = 1.0, scales[0]
    else:
        zoom_start, zoom_end = 1.0, DEFAULT_ZOOM_END
    translate = re.search(r"translateY\(\s*(-?[0-9.]+)px", motion)
    origin = re.search(r"transform-origin:\s*([0-9.]+)%\s+([0-9.]+)%", html)
    # CSS translateY(-20px) moves the still up, so the viewport samples lower.
    pan_y = -float(translate.group(1)) if translate else DEFAULT_PAN_Y
    return {
        "width": width,
        "height": height,
        "fps": fps,
        "duration": duration,
        "hero": hero,
        "audio": audio,
        "headline": headline,
        "subhead": subhead,
        "accent": accent,
        "safeX": safe_x,
        "safeTop": BRAND_SAFE_TOP,
        "safeBottom": safe_bottom,
        "headlineSize": headline_size,
        "subheadSize": subhead_size,
        "ruleWidth": rule_w,
        "ruleHeight": rule_h,
        "zoomStart": zoom_start,
        "zoomEnd": zoom_end,
        "panY": pan_y,
        "originX": float(origin.group(1)) / 100 if origin else DEFAULT_ORIGIN[0],
        "originY": float(origin.group(2)) / 100 if origin else DEFAULT_ORIGIN[1],
    }


def prepare_request(data: dict[str, Any]) -> dict[str, Any]:
    if data.get("backend") not in ACCEPTED_BACKENDS:
        fail("request.backend must be 'hyperframes' or 'ffmpeg-svg-caption-composition'")
    job_id = require_text(data, "jobId")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", job_id):
        fail("request.jobId contains unsupported characters")
    project = Path(require_text(data, "projectDir")).expanduser().resolve()
    if not project.is_dir():
        fail(f"projectDir is not a directory: {project}")
    composition = resolve_under(project, str(data.get("composition") or "index.html"), "composition")
    if not composition.is_file():
        fail(f"composition not found: {composition}")
    stage = str(data.get("stage") or "rough")
    if stage not in {"rough", "review", "final"}:
        fail("stage must be rough, review or final")
    output_format = str(data.get("format") or "mp4")
    if output_format != "mp4":
        fail("ffmpeg-svg-caption-composition renders mp4 only")
    resolution = str(data.get("resolution") or "portrait")
    if resolution != "portrait":
        fail("ffmpeg-svg-caption-composition renders portrait 1080x1920 only")
    fps = int(data.get("fps") or 30)
    if fps != 30:
        fail("ffmpeg-svg-caption-composition renders 30 fps only")
    quality_default = "high" if stage == "final" else "draft" if stage == "rough" else "standard"
    quality = str(data.get("quality") or quality_default)
    if quality not in {"draft", "standard", "high"}:
        fail("quality must be draft, standard or high")
    if stage == "final" and quality != "high":
        fail("final stage requires quality=high")
    target = str(data.get("target") or "reel_master")
    output = resolve_under(project, require_text(data, "output"), "output")
    if output.suffix.lower() != ".mp4":
        fail("output extension must be .mp4")
    variables = None
    variables_file = None
    if data.get("variablesFile"):
        variables_file = resolve_under(project, str(data["variablesFile"]), "variablesFile")
        if not variables_file.is_file():
            fail(f"variablesFile not found: {variables_file}")
        variables = read_json(variables_file)
    audio_required = bool(data.get("audioRequired", target in {"reel_master", "story_master", "feed_video"}))
    composition_info = parse_composition(composition.read_text(encoding="utf-8"), project, variables)
    if (composition_info["width"], composition_info["height"]) != PORTRAIT:
        fail(f"composition must be portrait {PORTRAIT[0]}x{PORTRAIT[1]}")
    if composition_info["fps"] != fps:
        fail("composition data-fps must match request.fps")
    if audio_required and composition_info["audio"] is None:
        fail("audioRequired but the composition has no audio track")
    font = rubik_font()
    return {
        "jobId": job_id,
        "projectDir": project,
        "composition": composition,
        "compositionArg": composition.relative_to(project).as_posix(),
        "stage": stage,
        "target": target,
        "format": output_format,
        "resolution": resolution,
        "fps": fps,
        "quality": quality,
        "output": output,
        "outputArg": output.relative_to(project).as_posix(),
        "audioRequired": audio_required,
        "strictAll": bool(data.get("strictAll", stage == "final")),
        "variablesFile": variables_file,
        "compositionInfo": composition_info,
        "font": font,
    }


def fades_for(duration: float) -> tuple[float, float]:
    fade_in, fade_out = FADE_IN_SEC, FADE_OUT_SEC
    if fade_in + fade_out >= duration:
        fade_in = duration * 0.2
        fade_out = duration * 0.3
    if fade_in <= 0 or fade_out <= 0 or fade_in + fade_out >= duration:
        fail("audio fade does not fit the composition duration")
    return fade_in, fade_out


def frame_count(info: dict[str, Any]) -> int:
    frames = int(round(float(info["duration"]) * int(info["fps"])))
    if frames < 1:
        fail("composition is shorter than one frame")
    return frames


def run_ffmpeg(args: list[str], *, timeout: int = 180) -> None:
    print("RUN " + " ".join(args))
    try:
        proc = subprocess.run(args, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        fail(f"ffmpeg timed out after {timeout}s", 1)
    except OSError as exc:
        fail(f"ffmpeg failed to start: {exc}", 1)
    if proc.returncode != 0:
        fail(f"command failed with exit={proc.returncode}: {args[0]}", proc.returncode or 1)


def run_ff_tool(args: list[str], *, timeout: int, role: str) -> subprocess.CompletedProcess[str]:
    """Run ffprobe or ffmpeg and fail closed on timeout or a start error."""
    try:
        return subprocess.run(args, text=True, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        fail(f"{role} timed out after {timeout}s", 1)
    except OSError as exc:
        fail(f"{role} failed to start: {exc}", 1)


def ffmpeg_version_line(ffmpeg: str) -> str:
    version = run_ff_tool([ffmpeg, "-version"], timeout=10, role="ffmpeg")
    return ((version.stdout or "ffmpeg").splitlines() or ["ffmpeg"])[0]


def tool_path(name: str) -> str | None:
    return shutil.which(name)


def filter_names(ffmpeg: str) -> set[str]:
    proc = run_ff_tool([ffmpeg, "-hide_banner", "-filters"], timeout=20, role="ffmpeg")
    names = set()
    for line in (proc.stdout or "").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] and parts[1] and not parts[0].startswith("-"):
            names.add(parts[1])
    return names


def encoder_names(ffmpeg: str) -> set[str]:
    proc = run_ff_tool([ffmpeg, "-hide_banner", "-encoders"], timeout=20, role="ffmpeg")
    names = set()
    for line in (proc.stdout or "").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0][:1] in {"V", "A", "."}:
            names.add(parts[1])
    return names


def _right_aligned_ink(text: str, ffmpeg: str, font: Path, tmp_dir: Path) -> tuple[int, int] | None:
    """Ink bounds of one right-aligned caption line, scrim and rule excluded."""
    width = 1800
    info = {
        "width": width,
        "height": 1920,
        "safeX": 40.0,
        "headlineSize": 72.0,
        "subheadSize": 40.0,
        "ruleWidth": 12.0,
        "ruleHeight": 4.0,
    }
    layout = {
        "headlineLines": [text],
        "subheadLines": [],
        "top": 80.0,
        "headLineH": 100.0,
        "ruleX": 40.0,
        "ruleY": 1700.0,
        "subTop": 1760.0,
        "subLineH": 50.0,
    }
    with tempfile.TemporaryDirectory(dir=tmp_dir) as tmp:
        work = Path(tmp)
        png = work / "line.png"
        try:
            render_caption_png(info, layout, font, png, work, ffmpeg)
        except SystemExit:
            return None
        raw = work / "line.raw"
        proc = subprocess.run(
            [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(png), "-f", "rawvideo", "-pix_fmt", "rgb24", str(raw)],
            text=True,
            timeout=30,
        )
        if proc.returncode != 0 or not raw.is_file():
            return None
        data = raw.read_bytes()
        min_x, max_x = width, -1
        row_bytes = width * 3
        for y in range(60, 200):
            row = data[y * row_bytes:(y + 1) * row_bytes]
            for x in range(width):
                if row[x * 3] > 16 or row[x * 3 + 1] > 16 or row[x * 3 + 2] > 16:
                    if x < min_x:
                        min_x = x
                    if x > max_x:
                        max_x = x
        if max_x < 0:
            return None
        return min_x, max_x


def doctor(tmp_dir: Path | None = None) -> int:
    from vf_ffmpeg_env import caption_gap

    ffmpeg = tool_path("ffmpeg")
    ffprobe = tool_path("ffprobe")
    facts = {"ffmpeg": ffmpeg, "ffprobe": ffprobe}
    print(json.dumps(facts, ensure_ascii=False, indent=2))
    gap = caption_gap()
    if gap is not None:
        print(gap.line)
        return 2
    try:
        font = rubik_font()
    except SystemExit:
        return 1
    if not ffmpeg:
        print("FAIL missing tools: ffmpeg, ffprobe", file=sys.stderr)
        return 1
    probe_dir = tmp_dir or runtime_tmp_dir()
    plain = _right_aligned_ink("שלום", ffmpeg, font["path"], probe_dir)
    dotted = _right_aligned_ink("שלום.", ffmpeg, font["path"], probe_dir)
    if (
        plain is None
        or dotted is None
        or plain[0] - dotted[0] < 8
        or abs(plain[1] - dotted[1]) > 4
    ):
        print("FAIL bidi self-test: trailing punctuation did not land on the left", file=sys.stderr)
        return 1
    print(
        f"OK {BACKEND} ffmpeg+ffprobe drawtext/zoompan/libx264/aac Rubik "
        "--enable-libfribidi --enable-libharfbuzz bidi-self-test=pass"
    )
    return 0


def text_ink_width(font: Path, text: str, size: float, ffmpeg: str, tmp_dir: Path) -> int:
    if not text:
        return 0
    width, height = 4096, max(int(size * 3), 32)
    with tempfile.TemporaryDirectory(dir=tmp_dir) as tmp:
        text_path = Path(tmp) / "line.txt"
        raw_path = Path(tmp) / "line.raw"
        text_path.write_text(visual_order(text), encoding="utf-8")
        vf = (
            f"drawtext=fontfile={escape_filter_path(font)}:textfile={escape_filter_path(text_path)}"
            f":text_shaping=0:expansion=none:fontcolor=white:fontsize={size:.2f}:x=0:y=0"
        )
        proc = subprocess.run(
            [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c=black:s={width}x{height}:d=1",
             "-vf", vf, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", str(raw_path)],
            text=True, timeout=30,
        )
        if proc.returncode != 0 or not raw_path.is_file():
            fail("could not measure caption text with ffmpeg drawtext", 1)
        data = raw_path.read_bytes()
        if len(data) != width * height * 3:
            fail("caption measurement frame has an unexpected size", 1)
        max_x = -1
        for y in range(height):
            row = data[y * width * 3:(y + 1) * width * 3]
            for x in range(width):
                if row[x * 3] > 16:
                    max_x = max(max_x, x)
        if max_x < 0:
            fail("caption text produced no ink", 1)
        return max_x + 1


def wrap_text(font: Path, text: str, size: float, max_width: float, ffmpeg: str, tmp_dir: Path) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if text_ink_width(font, trial, size, ffmpeg, tmp_dir) <= max_width:
            current = trial
            continue
        if not current:
            fail(f"caption word does not fit the safe area: {word}")
        lines.append(current)
        current = word
    if current:
        if text_ink_width(font, current, size, ffmpeg, tmp_dir) > max_width:
            fail("caption line does not fit the safe area")
        lines.append(current)
    return lines


def layout_caption(info: dict[str, Any], font: Path, ffmpeg: str | None, tmp_dir: Path | None = None) -> dict[str, Any]:
    content_width = info["width"] - (2 * info["safeX"])
    if content_width < 120:
        fail("safe area leaves no room for the caption")
    if ffmpeg:
        measure_dir = tmp_dir or runtime_tmp_dir()
        headline_lines = wrap_text(rubik_weight_font(700), info["headline"], info["headlineSize"], content_width, ffmpeg, measure_dir)
        subhead_lines = wrap_text(rubik_weight_font(600), info["subhead"], info["subheadSize"], content_width, ffmpeg, measure_dir) if info["subhead"] else []
    else:
        headline_lines = [info["headline"]]
        subhead_lines = [info["subhead"]] if info["subhead"] else []
    head_line_h = info["headlineSize"] * 1.12
    sub_line_h = info["subheadSize"] * 1.25
    head_block = len(headline_lines) * head_line_h
    sub_block = len(subhead_lines) * sub_line_h
    gap_after_head = 36 if subhead_lines or True else 0
    gap_after_rule = 30 if subhead_lines else 0
    block = head_block + gap_after_head + info["ruleHeight"] + gap_after_rule + sub_block
    bottom = info["height"] - info["safeBottom"]
    top = bottom - block
    if top < info["safeTop"]:
        fail("caption does not fit inside the safe area")
    rule_x = info["width"] - info["safeX"] - info["ruleWidth"]
    rule_y = top + head_block + gap_after_head
    return {
        "headlineLines": headline_lines,
        "subheadLines": subhead_lines,
        "top": top,
        "headLineH": head_line_h,
        "subLineH": sub_line_h,
        "ruleX": rule_x,
        "ruleY": rule_y,
        "subTop": rule_y + info["ruleHeight"] + gap_after_rule,
        "contentRight": info["width"] - info["safeX"],
    }


def build_svg(info: dict[str, Any], layout: dict[str, Any], font: dict[str, Any]) -> str:
    del font  # the variable-font record is not the face drawtext loads
    texts = []
    y = layout["top"]
    for line in layout["headlineLines"]:
        texts.append(
            f'<text x="{layout["contentRight"]:.1f}" y="{y:.1f}" text-anchor="start" direction="rtl" '
            f'unicode-bidi="embed" font-family="Rubik" font-size="{info["headlineSize"]:.1f}" '
            f'font-weight="700" fill="#ffffff" dominant-baseline="hanging">{xml_escape(line)}</text>'
        )
        y += layout["headLineH"]
    texts.append(
        f'<rect x="{layout["ruleX"]:.1f}" y="{layout["ruleY"]:.1f}" width="{info["ruleWidth"]:.1f}" '
        f'height="{info["ruleHeight"]:.1f}" fill="{COPPER}"/>'
    )
    y = layout["subTop"]
    for line in layout["subheadLines"]:
        texts.append(
            f'<text x="{layout["contentRight"]:.1f}" y="{y:.1f}" text-anchor="start" direction="rtl" '
            f'unicode-bidi="embed" font-family="Rubik" font-size="{info["subheadSize"]:.1f}" '
            f'font-weight="600" fill="#ffffff" dominant-baseline="hanging">{xml_escape(line)}</text>'
        )
        y += layout["subLineH"]
    body = "\n  ".join(texts)
    fonts = fonts_used(layout)
    headline_font = fonts["headline"]
    font_meta = f'headlineFont={headline_font["file"]}; headlineFontSha256={headline_font["sha256"]}'
    subhead_font = fonts.get("subhead")
    if subhead_font is not None:
        font_meta += f'; subheadFont={subhead_font["file"]}; subheadFontSha256={subhead_font["sha256"]}'
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{info["width"]}" height="{info["height"]}" viewBox="0 0 {info["width"]} {info["height"]}">\n'
        f'  <metadata>headline={xml_escape(info["headline"])}; subhead={xml_escape(info["subhead"])}; '
        f'font=Rubik; {font_meta}; accent={COPPER}; direction=rtl; '
        f'safeX={info["safeX"]}; safeTop={info["safeTop"]}; safeBottom={info["safeBottom"]}</metadata>\n'
        f"  {body}\n"
        "</svg>\n"
    )


def crf_for(quality: str) -> tuple[str, str]:
    if quality == "high":
        return "18", "veryfast"
    if quality == "standard":
        return "23", "veryfast"
    return "28", "ultrafast"


def build_commands(req: dict[str, Any], layout: dict[str, Any], svg_text: str, *, resolve_binary: bool) -> dict[str, Any]:
    info = req["compositionInfo"]
    frames = frame_count(info)
    fade_in, fade_out = fades_for(info["duration"])
    fade_out_start = info["duration"] - fade_out
    zoom_delta = max(0.0, float(info["zoomEnd"]) - float(info["zoomStart"]))
    denom = max(frames - 1, 1)
    zoom = (
        f"zoompan=z='{info['zoomStart']:.6f}+{zoom_delta:.6f}*on/{denom}'"
        f":x='iw*{info['originX']:.6f}*(1-1/zoom)'"
        f":y='ih*{info['originY']:.6f}*(1-1/zoom)+{info['panY']:.4f}*on/{denom}'"
        f":d={frames}:s={info['width']}x{info['height']}:fps={info['fps']}"
    )
    video = (
        f"[0:v]scale={info['width']}:{info['height']}:force_original_aspect_ratio=increase,"
        f"crop={info['width']}:{info['height']},setsar=1,{zoom},format=yuv420p[bg]"
    )
    caption_index = 1
    inputs = [["-loop", "1", "-i", str(info["hero"])]]
    maps = []
    if info["audio"] is not None:
        inputs.append(["-i", str(info["audio"])])
        caption_index = 2
        graph = (
            f"{video};[bg][{caption_index}:v]overlay=0:0:format=auto[v];"
            f"[1:a]atrim=start=0:end={info['duration']:.6f},asetpts=PTS-STARTPTS,"
            f"afade=t=in:st=0:d={fade_in:.6f},afade=t=out:st={fade_out_start:.6f}:d={fade_out:.6f},"
            f"aresample=48000[a]"
        )
        maps = ["-map", "[v]", "-map", "[a]", "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "48000"]
    else:
        graph = f"{video};[bg][{caption_index}:v]overlay=0:0:format=auto[v]"
        maps = ["-map", "[v]"]
    crf, preset = crf_for(req["quality"])
    binary = tool_path("ffmpeg") if resolve_binary else "ffmpeg"
    if resolve_binary and not binary:
        fail("ffmpeg is required", 1)
    command = [binary or "ffmpeg", "-y", "-hide_banner"]
    for group in inputs:
        command.extend(group)
    command.extend(["-i", "CAPTION_PNG", "-filter_complex", graph, *maps,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", preset, "-crf", crf,
                    "-r", str(info["fps"]), "-frames:v", str(frames),
                    "-movflags", "+faststart", str(req["output"])])
    return {
        "command": command,
        "frames": frames,
        "fadeIn": fade_in,
        "fadeOut": fade_out,
        "graph": graph,
        "svg": svg_text,
    }


def plan(req: dict[str, Any]) -> dict[str, Any]:
    info = req["compositionInfo"]
    layout = layout_caption(info, req["font"]["path"], ffmpeg=None)
    svg_text = build_svg(info, layout, req["font"])
    built = build_commands(req, layout, svg_text, resolve_binary=False)
    fonts = fonts_used(layout)
    return {
        "backend": BACKEND,
        "cwd": str(req["projectDir"]),
        "commands": [built["command"]],
        "svg": svg_text,
        "output": str(req["output"]),
        "width": info["width"],
        "height": info["height"],
        "fps": info["fps"],
        "durationSec": info["duration"],
        "frames": built["frames"],
        "accent": info["accent"],
        "fontFamily": "Rubik",
        "fontSha256": fonts["headline"]["sha256"],
        "fonts": fonts,
        "safeArea": {"x": info["safeX"], "top": info["safeTop"], "bottom": info["safeBottom"]},
        "zoom": {"start": info["zoomStart"], "end": info["zoomEnd"], "panY": info["panY"], "originX": info["originX"], "originY": info["originY"]},
        "fadeInSec": built["fadeIn"],
        "fadeOutSec": built["fadeOut"],
        "audioRequired": req["audioRequired"],
        "renderedOutput": None,
        "note": "plan does not render or install ffmpeg",
    }


def probe_streams(probe: dict[str, Any]) -> list[dict[str, Any]]:
    streams = probe.get("streams")
    if streams is None:
        return []
    if not isinstance(streams, list) or any(not isinstance(row, dict) for row in streams):
        fail("ffprobe streams is unparsable", 1)
    return streams


def probe_format(probe: dict[str, Any]) -> dict[str, Any]:
    fmt = probe.get("format")
    if fmt is None:
        fail("ffprobe duration is missing", 1)
    if not isinstance(fmt, dict):
        fail("ffprobe format is unparsable", 1)
    return fmt


def probe_float(value: Any, field: str) -> float:
    if isinstance(value, bool):
        fail(f"ffprobe {field} is unparsable: {value!r}", 1)
    if value is None or (isinstance(value, str) and not value.strip()):
        fail(f"ffprobe {field} is missing", 1)
    try:
        number = float(value)
    except (TypeError, ValueError):
        fail(f"ffprobe {field} is unparsable: {value!r}", 1)
    if number != number or number in (float("inf"), float("-inf")):
        fail(f"ffprobe {field} is unparsable: {value!r}", 1)
    return number


def probe_int(value: Any, field: str) -> int:
    if isinstance(value, bool):
        fail(f"ffprobe {field} is unparsable: {value!r}", 1)
    if value is None or (isinstance(value, str) and not value.strip()):
        fail(f"ffprobe {field} is missing", 1)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")) or not value.is_integer():
            fail(f"ffprobe {field} is unparsable: {value!r}", 1)
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        try:
            number = float(text)
        except ValueError:
            fail(f"ffprobe {field} is unparsable: {value!r}", 1)
        if number != number or number in (float("inf"), float("-inf")) or not number.is_integer():
            fail(f"ffprobe {field} is unparsable: {value!r}", 1)
        return int(number)
    fail(f"ffprobe {field} is unparsable: {value!r}", 1)


def probe_media(path: Path) -> dict[str, Any]:
    ffprobe = tool_path("ffprobe")
    if not ffprobe:
        fail("ffprobe is required to verify render output", 1)
    proc = run_ff_tool(
        [ffprobe, "-v", "error", "-show_entries", "format=duration:stream=index,codec_type,codec_name,width,height,avg_frame_rate,sample_rate,channels", "-of", "json", str(path)],
        timeout=30,
        role="ffprobe",
    )
    if proc.returncode != 0:
        fail(f"ffprobe failed: {(proc.stderr or '').strip()}", 1)
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        fail(f"ffprobe returned invalid JSON: {exc}", 1)
    if not isinstance(payload, dict):
        fail("ffprobe returned invalid JSON: expected an object", 1)
    return payload


def audio_duration(path: Path) -> float:
    probe = probe_media(path)
    streams = [row for row in probe_streams(probe) if row.get("codec_type") == "audio"]
    if not streams:
        fail(f"audio source has no audio stream: {path}", 1)
    return probe_float(probe_format(probe).get("duration"), "duration")


def verify_output(req: dict[str, Any], probe: dict[str, Any], frames: int) -> dict[str, Any]:
    info = req["compositionInfo"]
    streams = probe_streams(probe)
    videos = [row for row in streams if row.get("codec_type") == "video"]
    audios = [row for row in streams if row.get("codec_type") == "audio"]
    if not videos:
        fail("render has no video stream", 1)
    video = videos[0]
    width = probe_int(video.get("width"), "width")
    height = probe_int(video.get("height"), "height")
    if (width, height) != (info["width"], info["height"]) or height <= width:
        fail(f"render is not portrait {info['width']}x{info['height']}: {width}x{height}", 1)
    if video.get("codec_name") != "h264":
        fail(f"render video codec must be h264, found {video.get('codec_name')}", 1)
    if req["audioRequired"] and not audios:
        fail("render requires audio but ffprobe found no audio stream", 1)
    if req["audioRequired"] and audios[0].get("codec_name") != "aac":
        fail(f"render audio codec must be aac, found {audios[0].get('codec_name')}", 1)
    duration = probe_float(probe_format(probe).get("duration"), "duration")
    expected = frames / float(info["fps"])
    if duration <= 0 or abs(duration - expected) > max(0.15, 2 / float(info["fps"])):
        fail(f"render duration {duration} does not match {expected}", 1)
    return {
        "durationSec": round(duration, 3),
        "width": width,
        "height": height,
        "videoCodec": video.get("codec_name"),
        "audioStreams": len(audios),
        "audioRequired": req["audioRequired"],
    }


def drawtext_filters(info: dict[str, Any], layout: dict[str, Any], font: Path, work: Path) -> str:
    # replace=1 writes alpha. Without it, drawbox on a transparent canvas keeps
    # alpha at 0 and the scrim and copper rule disappear in the overlay.
    del font
    headline_font = rubik_weight_font(700)
    subhead_font = rubik_weight_font(600)
    filters = [
        f"drawbox=x=0:y={info['height'] - 760:.0f}:w={info['width']}:h=760:color=black@0.45:t=fill:replace=1",
        (
            f"drawbox=x={layout['ruleX']:.1f}:y={layout['ruleY']:.1f}:w={info['ruleWidth']:.1f}:"
            f"h={info['ruleHeight']:.1f}:color={COPPER}@1:t=fill:replace=1"
        ),
    ]
    y = layout["top"]
    index = 0
    for line in layout["headlineLines"]:
        path = work / f"headline-{index}.txt"
        path.write_text(visual_order(line), encoding="utf-8")
        filters.append(
            "drawtext=fontfile=" + escape_filter_path(headline_font)
            + ":textfile=" + escape_filter_path(path)
            + f":text_shaping=0:expansion=none:fontcolor=white:fontsize={info['headlineSize']:.2f}"
            + f":x=w-text_w-{info['safeX']:.1f}:y={y:.1f}"
        )
        y += layout["headLineH"]
        index += 1
    y = layout["subTop"]
    index = 0
    for line in layout["subheadLines"]:
        path = work / f"subhead-{index}.txt"
        path.write_text(visual_order(line), encoding="utf-8")
        filters.append(
            "drawtext=fontfile=" + escape_filter_path(subhead_font)
            + ":textfile=" + escape_filter_path(path)
            + f":text_shaping=0:expansion=none:fontcolor=white:fontsize={info['subheadSize']:.2f}"
            + f":x=w-text_w-{info['safeX']:.1f}:y={y:.1f}"
        )
        y += layout["subLineH"]
        index += 1
    return ",".join(filters)


def render_caption_png(info: dict[str, Any], layout: dict[str, Any], font: Path, png: Path, work: Path, ffmpeg: str) -> list[str]:
    vf = drawtext_filters(info, layout, font, work)
    command = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", f"color=c=black@0.0:s={info['width']}x{info['height']}:d=1,format=rgba",
        "-vf", vf, "-frames:v", "1", "-pix_fmt", "rgba", str(png),
    ]
    run_ffmpeg(command, timeout=60)
    if not png.is_file() or png.stat().st_size <= 0:
        fail("caption PNG was not written", 1)
    return command


def receipt_path(req: dict[str, Any], override: str | None) -> Path:
    if override:
        return resolve_under(req["projectDir"], override, "receipt")
    return req["output"].with_suffix(req["output"].suffix + ".receipt.json")


def command_for_receipt(command: list[str]) -> list[str]:
    if not command:
        return command
    return [Path(command[0]).name, *command[1:]]


def render_prepared(req: dict[str, Any], receipt_override: str | None, failover: dict[str, Any] | None) -> dict[str, Any]:
    if req.get("batchFile") or req.get("batchRows"):
        fail("ffmpeg-svg-caption-composition does not render HyperFrames batches", 1)
    explicit = req.get("tmpDir") if isinstance(req.get("tmpDir"), str) else None
    tmp_root = runtime_tmp_dir(req["output"], explicit)
    if doctor(tmp_root) != 0:
        raise SystemExit(1)
    ffmpeg = tool_path("ffmpeg")
    if not ffmpeg:
        fail("ffmpeg is required", 1)
    info = req["compositionInfo"]
    if req["audioRequired"]:
        if info["audio"] is None:
            fail("audioRequired but the composition has no audio track", 1)
        duration = audio_duration(info["audio"])
        if duration + 0.02 < float(info["duration"]):
            fail(f"audio is shorter than the composition ({duration:.3f}s < {info['duration']}s)", 1)
    font = req["font"]
    layout = layout_caption(info, font["path"], ffmpeg, tmp_root)
    svg_text = build_svg(info, layout, font)
    svg_path = req["output"].with_suffix(req["output"].suffix + ".caption.svg")
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.write_text(svg_text, encoding="utf-8")
    output = req["output"]
    committed = False
    try:
        with tempfile.TemporaryDirectory(prefix="vf-svg-caption-", dir=tmp_root) as tmp:
            work = Path(tmp)
            png = work / "caption.png"
            caption_cmd = render_caption_png(info, layout, font["path"], png, work, ffmpeg)
            built = build_commands(req, layout, svg_text, resolve_binary=True)
            command = [png.as_posix() if part == "CAPTION_PNG" else part for part in built["command"]]
            output.parent.mkdir(parents=True, exist_ok=True)
            run_ffmpeg(command, timeout=max(180, built["frames"] * 2))
        if not output.is_file() or output.stat().st_size <= 0:
            fail(f"render output missing or empty: {output}", 1)
        raw_probe = probe_media(output)
        verified = verify_output(req, raw_probe, built["frames"])
        version_line = ffmpeg_version_line(ffmpeg)
        used_fonts = fonts_used(layout)
        receipt: dict[str, Any] = {
            "schemaVersion": 1,
            "jobId": req["jobId"],
            "backend": BACKEND,
            "package": f"{BACKEND} ({version_line})",
            "stage": req["stage"],
            "target": req["target"],
            "output": req["outputArg"],
            "bytes": output.stat().st_size,
            "sha256": sha256_file(output),
            "verifiedAt": datetime.now(timezone.utc).isoformat(),
            "probe": verified,
            "ffprobe": raw_probe,
            "commands": [command_for_receipt(caption_cmd), command_for_receipt(command)],
            "captionSvg": svg_path.relative_to(req["projectDir"]).as_posix(),
            "captionSvgSha256": sha256_file(svg_path),
            "fontFamily": "Rubik",
            "fontSha256": used_fonts["headline"]["sha256"],
            "fonts": used_fonts,
            "accent": COPPER,
            "renderReceiptIsPublishReceipt": False,
            "qaLowered": False,
        }
        if failover is not None:
            receipt["failover"] = failover
        target = receipt_path(req, receipt_override)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        committed = True
        release_derived_tmp(tmp_root, output, explicit)
        print(f"OK render verified receipt={target}")
        return receipt
    finally:
        if not committed and output.exists():
            output.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="VelvetOS ffmpeg SVG caption composition")
    sub = parser.add_subparsers(dest="command", required=True)
    doctor_parser = sub.add_parser("doctor", help="check ffmpeg/ffprobe filters and the Rubik font")
    doctor_parser.add_argument("--tmp-dir", dest="tmp_dir", help="temp directory, instead of the system temp")
    plan_parser = sub.add_parser("plan", help="validate a HyperFrames-shaped request and print the ffmpeg plan")
    plan_parser.add_argument("request", type=Path)
    plan_parser.add_argument("--tmp-dir", dest="tmp_dir", help="temp directory, instead of the system temp")
    run_parser = sub.add_parser("run", help="render and write an ffprobe/SHA-256 receipt")
    run_parser.add_argument("request", type=Path)
    run_parser.add_argument("--receipt", help="receipt path relative to projectDir")
    run_parser.add_argument("--tmp-dir", dest="tmp_dir", help="temp directory, instead of the system temp")
    args = parser.parse_args()
    if args.command == "doctor":
        return doctor(runtime_tmp_dir(explicit=getattr(args, "tmp_dir", None)))
    req = prepare_request(read_json(args.request))
    if getattr(args, "tmp_dir", None):
        req["tmpDir"] = args.tmp_dir
    if args.command == "plan":
        print(json.dumps(plan(req), ensure_ascii=False, indent=2))
        return 0
    render_prepared(req, args.receipt, failover=None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
