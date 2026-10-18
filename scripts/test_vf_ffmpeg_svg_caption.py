#!/usr/bin/env python3
"""Unit and small-render tests for the ffmpeg SVG caption fallback."""
from __future__ import annotations

import contextlib
import io
import json
import shutil
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
