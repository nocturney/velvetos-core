#!/usr/bin/env python3
"""Fake-ffmpeg coverage for SKIP_ENV_MISSING_<CAP> and a real render mismatch."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import stat
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import vf_ffmpeg_env  # noqa: E402

FAKE = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import os
    import sys
    from pathlib import Path

    log = os.environ.get("VF_FAKE_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as handle:
            handle.write("\\n".join(sys.argv) + "\\n")
    name = Path(sys.argv[0]).name.lower()
    if name.startswith("ffprobe"):
        print("ffprobe version fake")
        raise SystemExit(0)
    args = sys.argv[1:]
    mode = os.environ.get("VF_FAKE_FFMPEG", "full")
    if "-filters" in args:
        names = [
            "zoompan", "drawtext", "overlay", "afade", "scale", "crop", "format",
            "sidedata", "asidedata",
        ]
        if mode == "missing-drawtext":
            names.remove("drawtext")
        if mode == "missing-zoompan":
            names.remove("zoompan")
        if mode == "missing-sidedata":
            names = [item for item in names if item not in {"sidedata", "asidedata"}]
        for item in names:
            print(f" .. {item}")
        raise SystemExit(0)
    if "-buildconf" in args:
        flags = [
            "--enable-libfreetype",
            "--enable-libfribidi",
            "--enable-libass",
            "--enable-libharfbuzz",
            "--enable-libx264",
        ]
        if mode == "missing-fribidi":
            flags = [item for item in flags if item != "--enable-libfribidi"]
        if mode == "missing-libass":
            flags = [item for item in flags if item != "--enable-libass"]
        print("\\n".join(flags))
        raise SystemExit(0)
    if "-encoders" in args:
        print(" V..... libx264")
        print(" A..... aac")
        print(" V..... mpeg4")
        raise SystemExit(0)
    if "-version" in args:
        print("ffmpeg version fake")
        raise SystemExit(0)
    sys.stderr.write("fake render refused\\n")
    raise SystemExit(1)
    """
)


class FakeFfmpeg:
    def __init__(self, root: Path, mode: str) -> None:
        self.root = root
        self.mode = mode
        self.log = root / "argv.log"
        self._old_path = os.environ.get("PATH", "")
        self._old_mode = os.environ.get("VF_FAKE_FFMPEG")
        self._old_log = os.environ.get("VF_FAKE_LOG")

    def __enter__(self) -> "FakeFfmpeg":
        script = self.root / "ffmpeg"
        script.write_text(FAKE, encoding="utf-8")
        script.chmod(script.stat().st_mode | stat.S_IEXEC)
        (self.root / "ffprobe").write_bytes(script.read_bytes())
        (self.root / "ffprobe").chmod(script.stat().st_mode)
        (self.root / "ffmpeg.cmd").write_text('@python "%~dp0ffmpeg" %*\r\n', encoding="utf-8")
        (self.root / "ffprobe.cmd").write_text('@python "%~dp0ffprobe" %*\r\n', encoding="utf-8")
        os.environ["PATH"] = str(self.root) + os.pathsep + self._old_path
        os.environ["VF_FAKE_FFMPEG"] = self.mode
        os.environ["VF_FAKE_LOG"] = str(self.log)
        return self

    def __exit__(self, *_) -> None:
        os.environ["PATH"] = self._old_path
        if self._old_mode is None:
            os.environ.pop("VF_FAKE_FFMPEG", None)
        else:
            os.environ["VF_FAKE_FFMPEG"] = self._old_mode
        if self._old_log is None:
            os.environ.pop("VF_FAKE_LOG", None)
        else:
            os.environ["VF_FAKE_LOG"] = self._old_log

    def argv_log(self) -> str:
        if not self.log.is_file():
            return ""
        return self.log.read_text(encoding="utf-8")


@contextlib.contextmanager
def github_actions(value: str | None):
    old = os.environ.get("GITHUB_ACTIONS")
    if value is None:
        os.environ.pop("GITHUB_ACTIONS", None)
    else:
        os.environ["GITHUB_ACTIONS"] = value
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("GITHUB_ACTIONS", None)
        else:
            os.environ["GITHUB_ACTIONS"] = old


class EmptyPath:
    def __enter__(self) -> Path:
        self._old = os.environ.get("PATH", "")
        self.root = Path(tempfile.mkdtemp(prefix="vf-no-ffmpeg-"))
        os.environ["PATH"] = str(self.root)
        return self.root

    def __exit__(self, *_) -> None:
        os.environ["PATH"] = self._old


def require_no_caption_gap(case: unittest.TestCase) -> None:
    """Full caption ffmpeg has no gap. Missing zoompan skips on a local host.

    ci_skip_failure returns the gap line when GITHUB_ACTIONS=true, and None
    otherwise. Any other gap still fails the assertion.
    """
    gap = vf_ffmpeg_env.caption_gap()
    if gap is None:
        return
    if gap.token == "SKIP_ENV_MISSING_ZOOMPAN":
        blocked = vf_ffmpeg_env.ci_skip_failure(gap)
        if blocked:
            raise RuntimeError(blocked)
        print(gap.line, flush=True)
        raise unittest.SkipTest(gap.line)
    case.assertIsNone(gap)


def _load(name: str):
    path = SCRIPTS / name
    spec = importlib.util.spec_from_file_location(name.replace("-", "_").replace(".py", ""), path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FfmpegCapabilityTests(unittest.TestCase):
    def test_missing_fribidi_is_a_skip_and_does_not_render(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        with tempfile.TemporaryDirectory() as tmp:
            with FakeFfmpeg(Path(tmp), "missing-fribidi") as fake:
                gap = vf_ffmpeg_env.caption_gap()
                self.assertIsNotNone(gap)
                assert gap is not None
                self.assertEqual(gap.token, "SKIP_ENV_MISSING_FRIBIDI")
                self.assertIn("ffmpeg -buildconf", gap.reason)
                self.assertIn("--enable-libfribidi", gap.reason)
                stdout = io.StringIO()
                stderr = io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    code = caption.doctor()
                text = stdout.getvalue() + stderr.getvalue()
                self.assertEqual(code, 2, text)
                self.assertIn("SKIP_ENV_MISSING_FRIBIDI", text)
                self.assertNotIn("FAIL bidi self-test", text)
                logged = fake.argv_log()
                self.assertIn("-filters", logged)
                self.assertIn("-buildconf", logged)
                self.assertNotIn("http://", logged)
                self.assertNotIn("https://", logged)

    def test_missing_libass_is_its_own_capability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with FakeFfmpeg(Path(tmp), "missing-libass"):
                gap = vf_ffmpeg_env.caption_gap()
                self.assertIsNotNone(gap)
                assert gap is not None
                self.assertEqual(gap.token, "SKIP_ENV_MISSING_LIBASS")
                self.assertIn("--enable-libass", gap.reason)
                self.assertIn("ffmpeg -buildconf", gap.reason)

    def test_missing_drawtext_filter_is_a_skip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with FakeFfmpeg(Path(tmp), "missing-drawtext"):
                gap = vf_ffmpeg_env.caption_gap()
                self.assertIsNotNone(gap)
                assert gap is not None
                self.assertEqual(gap.token, "SKIP_ENV_MISSING_DRAWTEXT")
                self.assertIn("ffmpeg -filters", gap.reason)
                self.assertIn("drawtext", gap.reason)

    def test_missing_zoompan_skips_locally_and_fails_on_ci(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with FakeFfmpeg(Path(tmp), "missing-zoompan"), github_actions(None):
                gap = vf_ffmpeg_env.caption_gap()
                self.assertIsNotNone(gap)
                assert gap is not None
                self.assertEqual(gap.token, "SKIP_ENV_MISSING_ZOOMPAN")
                self.assertIn("ffmpeg -filters", gap.reason)
                self.assertIn("zoompan", gap.reason)
                self.assertIsNone(vf_ffmpeg_env.ci_skip_failure(gap))
                with self.assertRaises(unittest.SkipTest) as caught:
                    require_no_caption_gap(self)
                self.assertIn("SKIP_ENV_MISSING_ZOOMPAN", str(caught.exception))
            with FakeFfmpeg(Path(tmp), "missing-zoompan"), github_actions("true"):
                with self.assertRaises(RuntimeError) as caught_fail:
                    require_no_caption_gap(self)
                self.assertIn("SKIP_ENV_MISSING_ZOOMPAN", str(caught_fail.exception))
                self.assertNotIsInstance(caught_fail.exception, unittest.SkipTest)
        sensor = _load("check-hyperframes-backend.py")
        self.assertEqual(sensor.zoompan_suite_action(gap, None), "skip")
        self.assertEqual(sensor.zoompan_suite_action(gap, gap.line), "fail")
        self.assertEqual(sensor.zoompan_suite_action(None, None), "run")
        other = vf_ffmpeg_env.EnvGap("SKIP_ENV_MISSING_DRAWTEXT", "drawtext")
        self.assertEqual(sensor.zoompan_suite_action(other, None), "run")

    def test_missing_sidedata_skips_normalization_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with FakeFfmpeg(Path(tmp), "missing-sidedata"):
                norm = vf_ffmpeg_env.normalization_gap()
                self.assertIsNotNone(norm)
                assert norm is not None
                self.assertEqual(norm.token, "SKIP_ENV_MISSING_SIDEDATA")
                self.assertIn("ffmpeg -filters", norm.reason)
                require_no_caption_gap(self)
                public = vf_ffmpeg_env.publication_gap()
                self.assertIsNotNone(public)
                assert public is not None
                self.assertEqual(public.token, "SKIP_ENV_MISSING_SIDEDATA")

    def test_missing_binary_skips_without_running_the_probe(self) -> None:
        with EmptyPath():
            for gap in (
                vf_ffmpeg_env.caption_gap(),
                vf_ffmpeg_env.normalization_gap(),
                vf_ffmpeg_env.publication_gap(),
            ):
                self.assertIsNotNone(gap)
                assert gap is not None
                self.assertEqual(gap.token, "SKIP_ENV_MISSING_FFMPEG")
                self.assertIn("ffmpeg -filters", gap.reason)
                self.assertIn("ffmpeg -buildconf", gap.reason)
                self.assertIn("not on PATH", gap.reason)

    def test_advertised_capability_with_bad_pixels_still_fails(self) -> None:
        import vf_ffmpeg_svg_caption as caption

        with tempfile.TemporaryDirectory() as tmp:
            with FakeFfmpeg(Path(tmp), "mismatch"):
                require_no_caption_gap(self)
                stdout = io.StringIO()
                stderr = io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    code = caption.doctor()
                text = stdout.getvalue() + stderr.getvalue()
                self.assertEqual(code, 1, text)
                self.assertIn("FAIL bidi self-test", text)
                self.assertNotIn("SKIP_ENV_MISSING", text)

    def test_video_sensor_skips_when_ffmpeg_is_missing(self) -> None:
        module = _load("check-video-normalization.py")
        with github_actions(None), EmptyPath():
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                with self.assertRaises(unittest.SkipTest) as caught:
                    module.VideoNormalizationTests.setUpClass()
        self.assertIn("SKIP_ENV_MISSING_FFMPEG", str(caught.exception))
        self.assertIn("SKIP_ENV_MISSING_FFMPEG", stdout.getvalue())

    def test_publication_sensor_skips_when_ffmpeg_is_missing(self) -> None:
        module = _load("check-publication-evidence.py")
        case = module.EvidenceTests("test_public_mp4_requires_hash_bound_normalization")
        case.setUp()
        try:
            with github_actions(None), EmptyPath():
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    with self.assertRaises(unittest.SkipTest) as caught:
                        case.test_public_mp4_requires_hash_bound_normalization()
            self.assertIn("SKIP_ENV_MISSING_FFMPEG", str(caught.exception))
            self.assertIn("SKIP_ENV_MISSING_FFMPEG", stdout.getvalue())
        finally:
            case.doCleanups()

    def test_github_actions_fails_video_privacy_skip(self) -> None:
        module = _load("check-video-normalization.py")
        with github_actions("true"), EmptyPath():
            with self.assertRaises(RuntimeError) as caught:
                module.VideoNormalizationTests.setUpClass()
        self.assertIn("SKIP_ENV_MISSING_FFMPEG", str(caught.exception))
        self.assertNotIsInstance(caught.exception, unittest.SkipTest)

    def test_github_actions_fails_public_video_skip(self) -> None:
        module = _load("check-publication-evidence.py")
        case = module.EvidenceTests("test_public_mp4_requires_hash_bound_normalization")
        case.setUp()
        try:
            with github_actions("true"), EmptyPath():
                with self.assertRaises(AssertionError) as caught:
                    case.test_public_mp4_requires_hash_bound_normalization()
            self.assertIn("SKIP_ENV_MISSING_FFMPEG", str(caught.exception))
        finally:
            case.doCleanups()


if __name__ == "__main__":
    unittest.main(verbosity=2)
