#!/usr/bin/env python3
"""Unit and small-render tests for the ffmpeg SVG caption fallback."""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import vf_hyperframes  # noqa: E402

HEADLINE = "קשה להתווכח עם המבט הזה."
SUBHEAD = "העיניים הן רק ההתחלה"
COPPER = "#a86838"


def ffmpeg_skip_reason() -> str | None:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        return "ffmpeg or ffprobe is not on PATH"
    return None


def write_composition(root: Path, *, duration: str = "10", audio: str | None = "assets/music.m4a", hero: str = "assets/hero.jpg") -> None:
    (root / "assets").mkdir(parents=True, exist_ok=True)
    audio_tag = ""
    if audio:
        audio_tag = f'<audio id="audio-track" src="{audio}" data-start="0" data-duration="{duration}"></audio>'
    html = f"""<!doctype html>
<html lang="he">
<head>
  <meta charset="utf-8" />
  <style>
    .hero {{ transform-origin: 50% 40%; animation: kenburns {duration}s linear forwards; }}
    @keyframes kenburns {{ from {{ transform: scale(1.0); }} to {{ transform: scale(1.08) translateY(-20px); }} }}
    .copy {{ position: absolute; left: 80px; right: 80px; bottom: 220px; }}
    .headline {{ font-size: 84px; line-height: 1.12; }}
    .rule {{ width: 180px; height: 10px; background: {COPPER}; }}
    .subhead {{ font-size: 50px; }}
    .scrim {{ height: 760px; }}
  </style>
</head>
<body>
  <div class="frame" data-composition-id="main" data-width="1080" data-height="1920" data-fps="30" data-duration="{duration}" data-no-timeline>
    <img class="hero" src="{hero}" alt="" />
    <div class="scrim"></div>
    <section class="copy" dir="rtl">
      <h1 class="headline">{HEADLINE}</h1>
      <div class="rule"></div>
      <p class="subhead">{SUBHEAD}</p>
    </section>
    {audio_tag}
  </div>
</body>
</html>
"""
    (root / "index.html").write_text(html, encoding="utf-8")


def request_body(root: Path, **overrides) -> dict:
    data = {
        "jobId": "hf180-fallback-unit",
        "backend": "hyperframes",
        "projectDir": str(root),
        "composition": "index.html",
        "stage": "final",
        "target": "reel_master",
        "format": "mp4",
        "resolution": "portrait",
        "fps": 30,
        "quality": "high",
        "output": "out/reel.mp4",
        "audioRequired": True,
        "strictAll": True,
    }
    data.update(overrides)
    return data


class CaptionPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        write_composition(self.root)
        (self.root / "assets" / "hero.jpg").write_bytes(b"\xff\xd8\xff\xd9")
        (self.root / "assets" / "music.m4a").write_bytes(b"not-audio")
        self.request = self.root / "request.json"
        self.request.write_text(json.dumps(request_body(self.root)), encoding="utf-8")

    def test_plan_accepts_hyperframes_request_and_describes_svg_caption(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        req = caption.prepare_request(json.loads(self.request.read_text(encoding="utf-8")))
        planned = caption.plan(req)
        self.assertEqual(planned["backend"], "ffmpeg-svg-caption-composition")
        self.assertEqual(planned["width"], 1080)
        self.assertEqual(planned["height"], 1920)
        self.assertEqual(planned["fps"], 30)
        self.assertEqual(planned["durationSec"], 10.0)
        self.assertEqual(planned["accent"], COPPER)
        self.assertEqual(planned["fontFamily"], "Rubik")
        self.assertTrue(planned["audioRequired"])
        self.assertGreaterEqual(planned["safeArea"]["x"], 86)
        self.assertGreaterEqual(planned["safeArea"]["bottom"], 230)
        self.assertIn("libx264", json.dumps(planned["commands"]))
        self.assertIn("aac", json.dumps(planned["commands"]))
        svg = planned["svg"]
        self.assertIn(HEADLINE, svg)
        self.assertIn(SUBHEAD, svg)
        self.assertIn('direction="rtl"', svg)
        self.assertIn("Rubik", svg)
        self.assertIn(COPPER, svg)
        self.assertAlmostEqual(planned["zoom"]["start"], 1.0)
        self.assertAlmostEqual(planned["zoom"]["end"], 1.08)
        self.assertAlmostEqual(planned["zoom"]["panY"], 20.0)
        self.assertIsNone(planned.get("renderedOutput"))
        self.assertEqual(caption.escape_filter_text("D:/Velvet/font.ttf"), "D\\\\:/Velvet/font.ttf")

    def test_plan_rejects_bad_backend_missing_hebrew_and_escaped_output(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        bad = request_body(self.root, backend="remotion")
        with self.assertRaises(SystemExit):
            caption.prepare_request(bad)
        write_composition(self.root)
        html = (self.root / "index.html").read_text(encoding="utf-8").replace(HEADLINE, "Latin only")
        (self.root / "index.html").write_text(html, encoding="utf-8")
        with self.assertRaises(SystemExit):
            caption.prepare_request(request_body(self.root))
        write_composition(self.root)
        with self.assertRaises(SystemExit):
            caption.prepare_request(request_body(self.root, output="../outside.mp4"))
        with self.assertRaises(SystemExit):
            caption.prepare_request(request_body(self.root, quality="draft"))
        write_composition(self.root, audio=None)
        with self.assertRaises(SystemExit):
            caption.prepare_request(request_body(self.root, audioRequired=True))

    def test_direct_backend_name_is_accepted(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        req = caption.prepare_request(request_body(self.root, backend="ffmpeg-svg-caption-composition"))
        self.assertEqual(req["format"], "mp4")
        self.assertTrue(req["audioRequired"])


class FailoverDecisionTests(unittest.TestCase):
    def test_two_primary_failures_switch_once_and_record_failover(self) -> None:
        calls = {"primary": 0, "fallback": 0}

        def primary(req, receipt_override):
            calls["primary"] += 1
            raise SystemExit(1)

        def fallback(req, receipt_override, failover):
            calls["fallback"] += 1
            self.assertEqual(failover["from"], "hyperframes")
            self.assertEqual(failover["to"], "ffmpeg-svg-caption-composition")
            self.assertEqual(failover["attempts"], 2)
            self.assertIs(failover["qaLowered"], False)
            self.assertEqual(len(failover["errors"]), 2)
            return {"backend": "ffmpeg-svg-caption-composition", "failover": failover}

        receipt = vf_hyperframes.failover_after_primary({"jobId": "x"}, None, primary, fallback)
        self.assertEqual(calls, {"primary": 2, "fallback": 1})
        self.assertEqual(receipt["failover"]["to"], "ffmpeg-svg-caption-composition")
        self.assertIs(receipt["failover"]["qaLowered"], False)

    def test_primary_success_does_not_failover(self) -> None:
        def primary(req, receipt_override):
            return {"backend": "hyperframes"}

        def fallback(req, receipt_override, failover):
            raise AssertionError("fallback must not run after primary success")

        receipt = vf_hyperframes.failover_after_primary({}, None, primary, fallback)
        self.assertEqual(receipt["backend"], "hyperframes")
        self.assertNotIn("failover", receipt)

    def test_missing_hyperframes_binary_uses_fallback(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        write_composition(root, duration="0.2")
        (root / "assets").mkdir(exist_ok=True)
        (root / "assets" / "hero.jpg").write_bytes(b"\xff\xd8\xff\xd9")
        (root / "assets" / "music.m4a").write_bytes(b"not-audio")
        # composition duration in the fixture HTML is 10 by default; rewrite for this case
        write_composition(root)
        raw = request_body(root)
        request_path = root / "request.json"
        request_path.write_text(json.dumps(raw), encoding="utf-8")
        req = vf_hyperframes.validate_request(raw)
        seen = {}

        def fake_render(prepared, receipt_override, failover):
            seen["failover"] = failover
            seen["jobId"] = prepared["jobId"]
            seen["prepared"] = prepared
            return {"backend": "ffmpeg-svg-caption-composition", "failover": failover, "jobId": prepared["jobId"]}

        real_which = shutil.which

        def hide_hyperframes(name: str):
            if name == "hyperframes":
                return None
            return real_which(name)

        import vf_ffmpeg_svg_caption as caption

        with mock.patch.object(vf_hyperframes.shutil, "which", side_effect=hide_hyperframes), mock.patch.object(
            caption, "render_prepared", side_effect=fake_render
        ):
            receipt = vf_hyperframes.execute(req, None)
        self.assertEqual(seen["jobId"], "hf180-fallback-unit")
        self.assertIn("compositionInfo", seen["prepared"])
        self.assertIn("font", seen["prepared"])
        self.assertIsInstance(req["sourceRequest"], dict)
        self.assertEqual(req["sourceRequest"]["backend"], "hyperframes")
        self.assertIsInstance(req["sourceRequest"]["projectDir"], str)
        self.assertEqual(receipt["backend"], "ffmpeg-svg-caption-composition")
        self.assertEqual(seen["failover"]["attempts"], 2)
        self.assertIs(seen["failover"]["qaLowered"], False)
        self.assertFalse((root / "out" / "reel.mp4").exists())


class RealRenderTests(unittest.TestCase):
    def test_small_ffmpeg_render_when_available(self) -> None:
        reason = ffmpeg_skip_reason()
        if reason:
            self.skipTest(reason)
        import vf_ffmpeg_svg_caption as caption

        doctor = caption.doctor()
        if doctor != 0:
            self.fail("ffmpeg is on PATH but ffmpeg-svg-caption doctor failed")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        write_composition(root, duration="0.2")
        hero = root / "assets" / "hero.jpg"
        audio = root / "assets" / "music.m4a"
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=s=640x360:d=1", "-frames:v", "1", str(hero)],
            check=True,
            timeout=30,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=1:sample_rate=48000", "-c:a", "aac", str(audio)],
            check=True,
            timeout=30,
        )
        req = caption.prepare_request(request_body(root, jobId="small-render", stage="review", quality="draft"))
        receipt = caption.render_prepared(req, None, failover=None)
        output = root / "out" / "reel.mp4"
        self.assertTrue(output.is_file())
        self.assertGreater(output.stat().st_size, 0)
        self.assertEqual(receipt["backend"], "ffmpeg-svg-caption-composition")
        self.assertEqual(receipt["probe"]["width"], 1080)
        self.assertEqual(receipt["probe"]["height"], 1920)
        self.assertEqual(receipt["probe"]["videoCodec"], "h264")
        self.assertEqual(receipt["probe"]["audioStreams"], 1)
        self.assertIs(receipt["probe"]["audioRequired"], True)
        self.assertEqual(receipt["sha256"], caption.sha256_file(output))
        streams = receipt["ffprobe"]["streams"]
        kinds = {stream["codec_type"]: stream["codec_name"] for stream in streams}
        self.assertEqual(kinds["video"], "h264")
        self.assertEqual(kinds["audio"], "aac")
        self.assertFalse(receipt["renderReceiptIsPublishReceipt"])
        svg_path = output.with_suffix(output.suffix + ".caption.svg")
        svg = svg_path.read_text(encoding="utf-8")
        self.assertIn(HEADLINE, svg)
        self.assertIn(COPPER, svg)
        self.assertIn('direction="rtl"', svg)
        _assert_receipt_fonts_match_drawn_files(self, caption, receipt, svg)
        self.assertFalse((root / "out" / ".vf-tmp").exists())


def _headline_ink_bounds(text: str) -> tuple[int, int, str, str]:
    """Render one caption line through the production drawtext path.

    Returns (left, right, textfile contents, filter graph). The scrim and
    copper rule sit outside the scanned band so only glyph ink is measured.
    """
    import vf_ffmpeg_svg_caption as caption

    font = caption.rubik_font()["path"]
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise unittest.SkipTest("ffmpeg or ffprobe is not on PATH")
    width, height = 1800, 1920
    info = {
        "width": width,
        "height": height,
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
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        graph = caption.drawtext_filters(info, layout, font, work)
        written = (work / "headline-0.txt").read_text(encoding="utf-8")
        png = work / "line.png"
        caption.render_caption_png(info, layout, font, png, work, ffmpeg)
        raw = work / "line.raw"
        subprocess.run(
            [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(png), "-f", "rawvideo", "-pix_fmt", "rgb24", str(raw)],
            check=True,
            timeout=30,
        )
        data = raw.read_bytes()
        min_x, max_x = width, -1
        for y in range(60, 200):
            row = data[y * width * 3:(y + 1) * width * 3]
            for x in range(width):
                if row[x * 3] > 16 or row[x * 3 + 1] > 16 or row[x * 3 + 2] > 16:
                    if x < min_x:
                        min_x = x
                    if x > max_x:
                        max_x = x
        if max_x < 0:
            raise AssertionError(f"caption line produced no ink: {text!r}")
        return min_x, max_x, written, graph


class BidiCaptionTests(unittest.TestCase):
    def test_visual_order_puts_punctuation_and_latin_runs_in_rtl(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        self.assertEqual(caption.visual_order("שלום."), ".םולש")
        self.assertEqual(caption.visual_order("שלום!"), "!םולש")
        self.assertEqual(caption.visual_order("אב."), ".בא")
        self.assertEqual(caption.visual_order("קשה Velvet"), "Velvet השק")
        self.assertEqual(caption.visual_order("קשה DEF"), "DEF השק")
        self.assertEqual(caption.visual_order("קשה Velvet להתווכח."), ".חכוותהל Velvet השק")
        self.assertEqual(caption.visual_order("קשה 12"), "12 השק")

    def test_trailing_punctuation_extends_the_left_edge(self) -> None:
        reason = ffmpeg_skip_reason()
        if reason:
            self.skipTest(reason)
        base_left, base_right, base_text, base_graph = _headline_ink_bounds("שלום")
        dot_left, dot_right, dot_text, dot_graph = _headline_ink_bounds("שלום.")
        bang_left, bang_right, bang_text, bang_graph = _headline_ink_bounds("שלום!")
        self.assertEqual(base_text, "םולש")
        self.assertEqual(dot_text, ".םולש")
        self.assertEqual(bang_text, "!םולש")
        self.assertIn("text_shaping=0", base_graph)
        self.assertIn("text_shaping=0", dot_graph)
        self.assertIn("text_shaping=0", bang_graph)
        self.assertNotIn("text_shaping=1", dot_graph)
        self.assertLessEqual(dot_left, base_left - 8)
        self.assertLessEqual(bang_left, base_left - 8)
        self.assertLessEqual(abs(dot_right - base_right), 4)
        self.assertLessEqual(abs(bang_right - base_right), 4)

    def test_latin_run_in_hebrew_line_extends_the_left_edge(self) -> None:
        reason = ffmpeg_skip_reason()
        if reason:
            self.skipTest(reason)
        base_left, base_right, base_text, _graph = _headline_ink_bounds("קשה")
        velvet_left, velvet_right, velvet_text, velvet_graph = _headline_ink_bounds("קשה Velvet")
        def_left, def_right, def_text, _def_graph = _headline_ink_bounds("קשה DEF")
        self.assertEqual(base_text, "השק")
        self.assertEqual(velvet_text, "Velvet השק")
        self.assertEqual(def_text, "DEF השק")
        self.assertIn("text_shaping=0", velvet_graph)
        self.assertLessEqual(velvet_left, base_left - 40)
        self.assertLessEqual(def_left, base_left - 20)
        self.assertLessEqual(abs(velvet_right - base_right), 4)
        self.assertLessEqual(abs(def_right - base_right), 4)

    def test_doctor_records_fribidi_harfbuzz_and_bidi_self_test(self) -> None:
        reason = ffmpeg_skip_reason()
        if reason:
            self.skipTest(reason)
        import vf_ffmpeg_svg_caption as caption

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = caption.doctor()
        text = stdout.getvalue()
        self.assertEqual(code, 0, text)
        self.assertIn("--enable-libfribidi", text)
        self.assertIn("--enable-libharfbuzz", text)
        self.assertIn("bidi-self-test=pass", text)


class FallbackHandoffTests(unittest.TestCase):
    def _owl_root(self, root: Path, *, real_media: bool) -> dict:
        write_composition(
            root,
            duration="0.2",
            hero="assets/owl-v13-hero.jpg",
            audio="assets/owl-v13-music-sirens-cc0.m4a",
        )
        hero = root / "assets" / "owl-v13-hero.jpg"
        audio = root / "assets" / "owl-v13-music-sirens-cc0.m4a"
        if real_media:
            subprocess.run(
                ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=s=640x360:d=1", "-frames:v", "1", str(hero)],
                check=True,
                timeout=30,
            )
            subprocess.run(
                ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=1:sample_rate=48000", "-c:a", "aac", str(audio)],
                check=True,
                timeout=30,
            )
        else:
            hero.write_bytes(b"\xff\xd8\xff\xd9")
            audio.write_bytes(b"not-audio")
        return request_body(
            root,
            jobId="hf180-gate2-fallback",
            stage="final",
            quality="high",
            output="out/reel.mp4",
            audioRequired=True,
        )

    def test_fallback_exception_writes_fail_receipt_without_traceback(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        raw = self._owl_root(root, real_media=False)
        req = vf_hyperframes.validate_request(raw)
        import vf_ffmpeg_svg_caption as caption

        real_which = shutil.which

        def hide_hyperframes(name: str):
            if name == "hyperframes":
                return None
            return real_which(name)

        stderr = io.StringIO()
        with mock.patch.object(vf_hyperframes.shutil, "which", side_effect=hide_hyperframes), mock.patch.object(
            caption, "render_prepared", side_effect=KeyError("compositionInfo")
        ), contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as caught:
                vf_hyperframes.execute(req, None)
        self.assertEqual(caught.exception.code, 1)
        err = stderr.getvalue()
        self.assertIn("FAIL", err)
        self.assertNotIn("Traceback", err)
        receipt_path = root / "out" / "reel.mp4.receipt.json"
        self.assertTrue(receipt_path.is_file())
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertIs(receipt["ok"], False)
        self.assertIs(receipt["verified"], False)
        self.assertNotIn("sha256", receipt)
        self.assertIs(receipt["qaLowered"], False)
        self.assertIs(receipt["renderReceiptIsPublishReceipt"], False)
        self.assertEqual(receipt["failover"]["attempts"], 2)
        self.assertEqual(receipt["backend"], "ffmpeg-svg-caption-composition")
        self.assertIn("KeyError", receipt["fail"])

    def test_execute_raw_hyperframes_request_renders_when_primary_missing(self) -> None:
        reason = ffmpeg_skip_reason()
        if reason:
            self.skipTest(reason)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        raw = self._owl_root(root, real_media=True)
        self.assertEqual(raw["backend"], "hyperframes")
        self.assertEqual(raw["resolution"], "portrait")
        self.assertEqual(raw["fps"], 30)
        self.assertEqual(raw["format"], "mp4")
        self.assertIs(raw["audioRequired"], True)
        req = vf_hyperframes.validate_request(raw)
        real_which = shutil.which

        def hide_hyperframes(name: str):
            if name == "hyperframes":
                return None
            return real_which(name)

        with mock.patch.object(vf_hyperframes.shutil, "which", side_effect=hide_hyperframes):
            receipt = vf_hyperframes.execute(req, None)
        output = root / "out" / "reel.mp4"
        self.assertTrue(output.is_file())
        self.assertGreater(output.stat().st_size, 0)
        self.assertEqual(receipt["backend"], "ffmpeg-svg-caption-composition")
        self.assertEqual(receipt["failover"]["from"], "hyperframes")
        self.assertEqual(receipt["failover"]["to"], "ffmpeg-svg-caption-composition")
        self.assertEqual(receipt["failover"]["attempts"], 2)
        self.assertIs(receipt["failover"]["qaLowered"], False)
        self.assertIs(receipt["renderReceiptIsPublishReceipt"], False)
        self.assertEqual(receipt["probe"]["width"], 1080)
        self.assertEqual(receipt["probe"]["height"], 1920)
        self.assertEqual(receipt["probe"]["videoCodec"], "h264")
        self.assertGreaterEqual(receipt["probe"]["audioStreams"], 1)
        streams = {stream["codec_type"]: stream["codec_name"] for stream in receipt["ffprobe"]["streams"]}
        self.assertEqual(streams["video"], "h264")
        self.assertEqual(streams["audio"], "aac")
        svg = (output.with_suffix(output.suffix + ".caption.svg")).read_text(encoding="utf-8")
        self.assertIn(HEADLINE, svg)
        self.assertIn('direction="rtl"', svg)


def _drawn_font_paths(command: list[str]) -> list[Path]:
    blob = " ".join(command)
    found = re.findall(r"fontfile=((?:\\\\.|[^:])+)", blob)
    return [Path(item.replace("\\\\:", ":")) for item in found]


def _assert_receipt_fonts_match_drawn_files(test: unittest.TestCase, caption, receipt: dict, svg: str) -> None:
    paths = _drawn_font_paths(receipt["commands"][0])
    by_name = {}
    for path in paths:
        test.assertTrue(path.is_file(), str(path))
        by_name[path.name] = caption.sha256_file(path)
    test.assertIn("Rubik-wght700.ttf", by_name)
    test.assertIn("Rubik-wght600.ttf", by_name)
    test.assertEqual(receipt["fonts"]["headline"]["sha256"], by_name["Rubik-wght700.ttf"])
    test.assertEqual(receipt["fonts"]["subhead"]["sha256"], by_name["Rubik-wght600.ttf"])
    test.assertEqual(receipt["fontSha256"], by_name["Rubik-wght700.ttf"])
    test.assertNotEqual(receipt["fontSha256"], caption.rubik_font()["sha256"])
    test.assertIn(by_name["Rubik-wght700.ttf"], svg)
    test.assertIn(by_name["Rubik-wght600.ttf"], svg)
    test.assertNotIn(caption.rubik_font()["sha256"], svg)


def _portrait_request() -> dict:
    return {
        "compositionInfo": {"width": 1080, "height": 1920, "fps": 30, "duration": 1.0},
        "audioRequired": False,
    }


def _video_probe(**overrides) -> dict:
    probe = {
        "streams": [{"codec_type": "video", "codec_name": "h264", "width": 1080, "height": 1920}],
        "format": {"duration": "1.000000"},
    }
    probe.update(overrides)
    return probe


class ProbeFailClosedTests(unittest.TestCase):
    """ffprobe/ffmpeg timeouts and unparsable probe fields fail closed with a reason."""

    def assert_fail_closed(self, call, *includes: str, excludes: tuple[str, ...] = ("Traceback", "0.0")):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as caught:
                call()
        self.assertEqual(caught.exception.code, 1)
        text = stderr.getvalue()
        self.assertTrue(text.startswith("FAIL "), text)
        for part in includes:
            self.assertIn(part, text)
        for part in excludes:
            self.assertNotIn(part, text)
        return text

    def test_ffprobe_timeout_fails_closed(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        expired = subprocess.TimeoutExpired(["ffprobe", "out.mp4"], 30)
        with mock.patch.object(caption, "tool_path", return_value="/usr/bin/ffprobe"), mock.patch.object(
            caption.subprocess, "run", side_effect=expired
        ):
            self.assert_fail_closed(
                lambda: caption.probe_media(Path("out.mp4")),
                "ffprobe timed out after 30s",
            )

    def test_ffmpeg_timeout_fails_closed(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        expired = subprocess.TimeoutExpired(["ffmpeg", "-filters"], 20)
        with mock.patch.object(caption.subprocess, "run", side_effect=expired):
            self.assert_fail_closed(
                lambda: caption.filter_names("/usr/bin/ffmpeg"),
                "ffmpeg timed out after 20s",
            )

    def test_ffmpeg_encoder_timeout_fails_closed(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        expired = subprocess.TimeoutExpired(["ffmpeg", "-encoders"], 20)
        with mock.patch.object(caption.subprocess, "run", side_effect=expired):
            self.assert_fail_closed(
                lambda: caption.encoder_names("/usr/bin/ffmpeg"),
                "ffmpeg timed out after 20s",
            )

    def test_ffmpeg_version_timeout_fails_closed(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        expired = subprocess.TimeoutExpired(["ffmpeg", "-version"], 10)
        with mock.patch.object(caption.subprocess, "run", side_effect=expired):
            self.assert_fail_closed(
                lambda: caption.ffmpeg_version_line("/usr/bin/ffmpeg"),
                "ffmpeg timed out after 10s",
            )

    def test_ffprobe_start_error_fails_closed(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        with mock.patch.object(caption, "tool_path", return_value="/usr/bin/ffprobe"), mock.patch.object(
            caption.subprocess, "run", side_effect=OSError("exec failed")
        ):
            self.assert_fail_closed(
                lambda: caption.probe_media(Path("out.mp4")),
                "ffprobe failed to start",
                "exec failed",
            )

    def test_probe_json_must_be_an_object(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        proc = subprocess.CompletedProcess(["ffprobe"], 0, stdout="[1]", stderr="")
        with mock.patch.object(caption, "tool_path", return_value="/usr/bin/ffprobe"), mock.patch.object(
            caption.subprocess, "run", return_value=proc
        ):
            self.assert_fail_closed(
                lambda: caption.probe_media(Path("out.mp4")),
                "ffprobe returned invalid JSON",
                "expected an object",
            )

    def test_audio_duration_rejects_unparsable_value(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        probe = {"streams": [{"codec_type": "audio", "codec_name": "aac"}], "format": {"duration": "nope"}}
        with mock.patch.object(caption, "probe_media", return_value=probe):
            self.assert_fail_closed(
                lambda: caption.audio_duration(Path("music.m4a")),
                "ffprobe duration is unparsable",
                "'nope'",
            )

    def test_audio_duration_rejects_missing_value(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        probe = {"streams": [{"codec_type": "audio"}], "format": {}}
        with mock.patch.object(caption, "probe_media", return_value=probe):
            self.assert_fail_closed(
                lambda: caption.audio_duration(Path("music.m4a")),
                "ffprobe duration is missing",
            )

    def test_audio_duration_rejects_nan(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        probe = {"streams": [{"codec_type": "audio"}], "format": {"duration": "nan"}}
        with mock.patch.object(caption, "probe_media", return_value=probe):
            self.assert_fail_closed(
                lambda: caption.audio_duration(Path("music.m4a")),
                "ffprobe duration is unparsable",
            )

    def test_audio_duration_keeps_a_parsed_zero(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        probe = {"streams": [{"codec_type": "audio"}], "format": {"duration": "0.0"}}
        with mock.patch.object(caption, "probe_media", return_value=probe):
            self.assertEqual(caption.audio_duration(Path("music.m4a")), 0.0)

    def test_audio_duration_keeps_a_parsed_number(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        probe = {"streams": [{"codec_type": "audio"}], "format": {"duration": "8.5"}}
        with mock.patch.object(caption, "probe_media", return_value=probe):
            self.assertEqual(caption.audio_duration(Path("music.m4a")), 8.5)

    def test_verify_output_rejects_fractional_width(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        probe = _video_probe()
        probe["streams"][0]["width"] = 1080.9
        self.assert_fail_closed(
            lambda: caption.verify_output(_portrait_request(), probe, 30),
            "ffprobe width is unparsable",
            "1080.9",
        )

    def test_verify_output_rejects_unparsable_width(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        probe = _video_probe()
        probe["streams"][0]["width"] = "wide"
        self.assert_fail_closed(
            lambda: caption.verify_output(_portrait_request(), probe, 30),
            "ffprobe width is unparsable",
            "'wide'",
        )

    def test_verify_output_rejects_missing_width(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        probe = _video_probe()
        del probe["streams"][0]["width"]
        self.assert_fail_closed(
            lambda: caption.verify_output(_portrait_request(), probe, 30),
            "ffprobe width is missing",
        )

    def test_verify_output_rejects_unparsable_height(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        probe = _video_probe()
        probe["streams"][0]["height"] = "tall"
        self.assert_fail_closed(
            lambda: caption.verify_output(_portrait_request(), probe, 30),
            "ffprobe height is unparsable",
            "'tall'",
        )

    def test_verify_output_rejects_missing_height(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        probe = _video_probe()
        probe["streams"][0]["height"] = ""
        self.assert_fail_closed(
            lambda: caption.verify_output(_portrait_request(), probe, 30),
            "ffprobe height is missing",
        )

    def test_verify_output_rejects_unparsable_duration(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        probe = _video_probe(format={"duration": "n/a"})
        self.assert_fail_closed(
            lambda: caption.verify_output(_portrait_request(), probe, 30),
            "ffprobe duration is unparsable",
            "'n/a'",
            excludes=("Traceback", "does not match"),
        )

    def test_verify_output_rejects_missing_duration(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        probe = _video_probe(format={})
        self.assert_fail_closed(
            lambda: caption.verify_output(_portrait_request(), probe, 30),
            "ffprobe duration is missing",
            excludes=("Traceback", "does not match"),
        )

    def test_verify_output_rejects_unparsable_streams(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        self.assert_fail_closed(
            lambda: caption.verify_output(_portrait_request(), {"streams": "nope", "format": {"duration": "1"}}, 30),
            "ffprobe streams is unparsable",
        )

    def test_verify_output_accepts_a_parsed_probe(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        verified = caption.verify_output(_portrait_request(), _video_probe(), 30)
        self.assertEqual(verified["width"], 1080)
        self.assertEqual(verified["height"], 1920)
        self.assertEqual(verified["durationSec"], 1.0)


def _us_weight_class(path: Path) -> int:
    data = path.read_bytes()
    count = struct.unpack(">H", data[4:6])[0]
    for index in range(count):
        rec = 12 + index * 16
        if data[rec:rec + 4] != b"OS/2":
            continue
        offset = struct.unpack(">I", data[rec + 8:rec + 12])[0]
        return struct.unpack(">H", data[offset + 4:offset + 6])[0]
    raise AssertionError(f"OS/2 table missing in {path}")


def _glyph_ink(font: Path, text: str = "א") -> int:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise unittest.SkipTest("ffmpeg or ffprobe is not on PATH")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        raw = tmp_path / "ink.raw"
        txt = tmp_path / "ink.txt"
        txt.write_text(text, encoding="utf-8")
        width, height = 400, 220
        vf = (
            f"drawtext=fontfile={font}:textfile={txt}:text_shaping=0:expansion=none:"
            f"fontcolor=white:fontsize=140:x=30:y=30"
        )
        subprocess.run(
            [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c=black:s={width}x{height}:d=1",
             "-vf", vf, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", str(raw)],
            check=True,
            timeout=30,
        )
        blob = raw.read_bytes()
        return sum(1 for index in range(0, len(blob), 3) if blob[index] > 32)


class CaptionDefectTests(unittest.TestCase):
    def test_parentheses_mirror_on_rtl_level(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        self.assertEqual(caption.visual_order("שלום (Velvet)"), "(Velvet) םולש")
        self.assertEqual(caption.visual_order("(קשה)"), "(השק)")
        self.assertEqual(caption.visual_order("קשה [א]"), "[א] השק")
        reason = ffmpeg_skip_reason()
        if reason:
            return
        _left, _right, written, graph = _headline_ink_bounds("שלום (Velvet)")
        self.assertEqual(written, "(Velvet) םולש")
        self.assertIn("text_shaping=0", graph)
        self.assertIn("replace=1", graph)

    def test_headline_font_is_weight_700_and_heavier_than_the_default_master(self) -> None:
        reason = ffmpeg_skip_reason()
        if reason:
            self.skipTest(reason)
        import vf_ffmpeg_svg_caption as caption

        bold = caption.rubik_weight_font(700)
        variable = caption.rubik_font()["path"]
        self.assertEqual(_us_weight_class(bold), 700)
        self.assertGreater(_glyph_ink(bold), int(_glyph_ink(variable) * 1.5))
        info = {
            "width": 1800,
            "height": 1920,
            "safeX": 40.0,
            "headlineSize": 72.0,
            "subheadSize": 40.0,
            "ruleWidth": 12.0,
            "ruleHeight": 4.0,
        }
        layout = {
            "headlineLines": ["קשה"],
            "subheadLines": ["התחלה"],
            "top": 80.0,
            "headLineH": 100.0,
            "ruleX": 40.0,
            "ruleY": 1700.0,
            "subTop": 1760.0,
            "subLineH": 50.0,
        }
        with tempfile.TemporaryDirectory() as tmp:
            graph = caption.drawtext_filters(info, layout, variable, Path(tmp))
        self.assertIn("Rubik-wght700", graph)
        self.assertIn("Rubik-wght600", graph)
        self.assertNotIn(variable.name, graph)
        self.assertIn("replace=1", graph)

    def test_real_render_keeps_copper_rule_and_darker_scrim(self) -> None:
        reason = ffmpeg_skip_reason()
        if reason:
            self.skipTest(reason)
        import vf_ffmpeg_svg_caption as caption

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        write_composition(root, duration="0.2")
        hero = root / "assets" / "hero.jpg"
        audio = root / "assets" / "music.m4a"
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=white:s=640x360:d=1", "-frames:v", "1", str(hero)],
            check=True,
            timeout=30,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=1:sample_rate=48000", "-c:a", "aac", str(audio)],
            check=True,
            timeout=30,
        )
        req = caption.prepare_request(request_body(root, jobId="copper-scrim", stage="review", quality="draft"))
        caption.render_prepared(req, None, failover=None)
        output = root / "out" / "reel.mp4"
        raw = root / "frame.raw"
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(output), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", str(raw)],
            check=True,
            timeout=30,
        )
        width, height = 1080, 1920
        data = raw.read_bytes()
        self.assertEqual(len(data), width * height * 3)
        copper = 0
        for y in range(height - 800, height):
            row = data[y * width * 3:(y + 1) * width * 3]
            for x in range(width):
                red, green, blue = row[x * 3], row[x * 3 + 1], row[x * 3 + 2]
                if abs(red - 168) <= 18 and abs(green - 104) <= 18 and abs(blue - 56) <= 18:
                    copper += 1
        self.assertGreater(copper, 100)

        def mean_luma(y0: int, y1: int) -> float:
            total = 0
            for y in range(y0, y1):
                row = data[y * width * 3:(y + 1) * width * 3]
                total += sum(row)
            return total / (3 * (y1 - y0) * width)

        upper = mean_luma(400, 700)
        scrim = mean_luma(1180, 1280)
        self.assertLess(scrim, upper - 30)

    def test_tempfile_is_called_with_the_output_runtime_dir(self) -> None:
        reason = ffmpeg_skip_reason()
        if reason:
            self.skipTest(reason)
        import vf_ffmpeg_svg_caption as caption

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        write_composition(root, duration="0.2")
        hero = root / "assets" / "hero.jpg"
        audio = root / "assets" / "music.m4a"
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=gray:s=320x180:d=1", "-frames:v", "1", str(hero)],
            check=True,
            timeout=30,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=1:sample_rate=48000", "-c:a", "aac", str(audio)],
            check=True,
            timeout=30,
        )
        req = caption.prepare_request(request_body(root, jobId="tmp-dir", stage="review", quality="draft"))
        seen: list[str | None] = []
        real = tempfile.TemporaryDirectory

        def spy(*args, **kwargs):
            seen.append(kwargs.get("dir"))
            return real(*args, **kwargs)

        expected = (root / "out" / ".vf-tmp").resolve()
        env = os.environ.copy()
        env.pop("VELVETOS_RUNTIME_ROOT", None)
        with mock.patch.dict(os.environ, env, clear=True), mock.patch.object(caption.tempfile, "TemporaryDirectory", spy):
            caption.render_prepared(req, None, failover=None)
        self.assertTrue(seen)
        for item in seen:
            self.assertIsNotNone(item)
            self.assertEqual(Path(item).resolve(), expected)

    def test_runtime_root_and_explicit_tmp_dir_override_the_output_dir(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        output = root / "out" / "reel.mp4"
        explicit = root / "custom-tmp"
        self.assertEqual(caption.runtime_tmp_dir(output, str(explicit)), explicit.resolve())
        env_root = root / "runtime-root"
        with mock.patch.dict(os.environ, {"VELVETOS_RUNTIME_ROOT": str(env_root)}):
            self.assertEqual(caption.runtime_tmp_dir(output), (env_root / "tmp").resolve())
        reason = ffmpeg_skip_reason()
        if reason:
            return
        seen: list[str | None] = []
        real = tempfile.TemporaryDirectory

        def spy(*args, **kwargs):
            seen.append(kwargs.get("dir"))
            return real(*args, **kwargs)

        with mock.patch.dict(os.environ, {"VELVETOS_RUNTIME_ROOT": str(env_root)}), mock.patch.object(
            caption.tempfile, "TemporaryDirectory", spy
        ):
            caption.text_ink_width(caption.rubik_weight_font(700), "שלום", 48, shutil.which("ffmpeg"), caption.runtime_tmp_dir())
        self.assertTrue(seen)
        self.assertEqual(Path(seen[0]).resolve(), (env_root / "tmp").resolve())

    def test_receipt_font_hash_matches_the_drawn_font_file(self) -> None:
        reason = ffmpeg_skip_reason()
        if reason:
            self.skipTest(reason)
        import vf_ffmpeg_svg_caption as caption

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        write_composition(root, duration="0.2")
        hero = root / "assets" / "hero.jpg"
        audio = root / "assets" / "music.m4a"
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=white:s=320x180:d=1", "-frames:v", "1", str(hero)],
            check=True,
            timeout=30,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=1:sample_rate=48000", "-c:a", "aac", str(audio)],
            check=True,
            timeout=30,
        )
        env = os.environ.copy()
        env.pop("VELVETOS_RUNTIME_ROOT", None)
        with mock.patch.dict(os.environ, env, clear=True):
            receipt = caption.render_prepared(
                caption.prepare_request(request_body(root, jobId="font-hash", stage="review", quality="draft")),
                None,
                failover=None,
            )
        svg = (root / "out" / "reel.mp4.caption.svg").read_text(encoding="utf-8")
        _assert_receipt_fonts_match_drawn_files(self, caption, receipt, svg)
        self.assertFalse((root / "out" / ".vf-tmp").exists())

    def test_release_derived_tmp_removes_only_an_empty_derived_directory(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        output = root / "out" / "reel.mp4"
        derived = root / "out" / ".vf-tmp"
        derived.mkdir(parents=True)
        caption.release_derived_tmp(derived, output, None)
        self.assertFalse(derived.exists())
        derived.mkdir()
        (derived / "keep.txt").write_text("x", encoding="utf-8")
        caption.release_derived_tmp(derived, output, None)
        self.assertTrue((derived / "keep.txt").is_file())
        explicit = root / "keep-tmp"
        explicit.mkdir()
        caption.release_derived_tmp(explicit, output, str(explicit))
        self.assertTrue(explicit.is_dir())

    def test_hyperframes_forwards_tmp_dir_into_the_prepared_fallback(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        write_composition(root, duration="0.2")
        (root / "assets" / "hero.jpg").write_bytes(b"\xff\xd8\xff\xd9")
        (root / "assets" / "music.m4a").write_bytes(b"not-audio")
        req = vf_hyperframes.validate_request(request_body(root))
        seen = {}

        def fake_render(prepared, receipt_override, failover):
            seen["tmpDir"] = prepared.get("tmpDir")
            return {"backend": "ffmpeg-svg-caption-composition", "failover": failover}

        real_which = shutil.which

        def hide_hyperframes(name: str):
            if name == "hyperframes":
                return None
            return real_which(name)

        import vf_ffmpeg_svg_caption as caption

        with mock.patch.object(vf_hyperframes.shutil, "which", side_effect=hide_hyperframes), mock.patch.object(
            caption, "render_prepared", side_effect=fake_render
        ):
            vf_hyperframes.execute(req, None, tmp_dir=str(root / "explicit-tmp"))
        self.assertEqual(seen["tmpDir"], str(root / "explicit-tmp"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
