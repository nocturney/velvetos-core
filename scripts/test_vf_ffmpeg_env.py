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
def ci_vars(github_actions_value: str | None, ci_value: str | None):
    """Set GITHUB_ACTIONS and CI. None removes the variable for this block."""
    saved = {
        "GITHUB_ACTIONS": os.environ.get("GITHUB_ACTIONS"),
        "CI": os.environ.get("CI"),
    }
    updates = {
        "GITHUB_ACTIONS": github_actions_value,
        "CI": ci_value,
    }
    for name, value in updates.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value
    try:
        yield
    finally:
        for name, previous in saved.items():
            if previous is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = previous


@contextlib.contextmanager
def github_actions(value: str | None):
    """Set GITHUB_ACTIONS and clear CI so the runner's CI=true cannot leak in."""
    with ci_vars(value, None):
        yield


class EmptyPath:
    def __enter__(self) -> Path:
        self._old = os.environ.get("PATH", "")
        self.root = Path(tempfile.mkdtemp(prefix="vf-no-ffmpeg-"))
        os.environ["PATH"] = str(self.root)
        return self.root

    def __exit__(self, *_) -> None:
        os.environ["PATH"] = self._old


def _load(name: str, path: Path | None = None):
    path = path or (SCRIPTS / name)
    mod_name = "vf_ffmpeg_case_" + path.stem.replace("-", "_")
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(mod_name, None)
        raise
    return module


def classify_ci_call(call) -> str:
    """HARD_FAILURE when CI refuses the gap. GUARD_BYPASSED when a skip escapes.

    unittest.SkipTest is not a subclass of the failure the sensors raise, so a
    bare assertRaises lets a removed guard skip the test and still exit 0.
    """
    try:
        call()
    except unittest.SkipTest:
        return "GUARD_BYPASSED"
    except (RuntimeError, AssertionError) as exc:
        if "SKIP_ENV_MISSING_" in str(exc):
            return "HARD_FAILURE"
        return "OTHER_FAILURE"
    else:
        return "NO_FAILURE"


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

    def test_missing_sidedata_skips_normalization_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with FakeFfmpeg(Path(tmp), "missing-sidedata"):
                norm = vf_ffmpeg_env.normalization_gap()
                self.assertIsNotNone(norm)
                assert norm is not None
                self.assertEqual(norm.token, "SKIP_ENV_MISSING_SIDEDATA")
                self.assertIn("ffmpeg -filters", norm.reason)
                self.assertIsNone(vf_ffmpeg_env.caption_gap())
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
                self.assertIsNone(vf_ffmpeg_env.caption_gap())
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
            self.assertEqual(
                classify_ci_call(module.VideoNormalizationTests.setUpClass),
                "HARD_FAILURE",
            )

    def test_github_actions_fails_public_video_skip(self) -> None:
        module = _load("check-publication-evidence.py")
        case = module.EvidenceTests("test_public_mp4_requires_hash_bound_normalization")
        case.setUp()
        try:
            with github_actions("true"), EmptyPath():
                self.assertEqual(
                    classify_ci_call(case.test_public_mp4_requires_hash_bound_normalization),
                    "HARD_FAILURE",
                )
        finally:
            case.doCleanups()

    def test_github_actions_missing_filter_and_flag_are_hard_failures(self) -> None:
        """A missing filter and a missing build flag must not skip on CI."""
        video = _load("check-video-normalization.py")
        with tempfile.TemporaryDirectory() as tmp:
            with FakeFfmpeg(Path(tmp), "missing-sidedata"), github_actions("true"):
                self.assertEqual(
                    classify_ci_call(video.VideoNormalizationTests.setUpClass),
                    "HARD_FAILURE",
                )

        import test_vf_ffmpeg_svg_caption as caption_tests

        with tempfile.TemporaryDirectory() as tmp:
            with FakeFfmpeg(Path(tmp), "missing-fribidi"), github_actions("true"):
                gap = vf_ffmpeg_env.caption_gap()
                self.assertIsNotNone(gap)
                assert gap is not None
                self.assertEqual(gap.token, "SKIP_ENV_MISSING_FRIBIDI")
                self.assertIn("--enable-libfribidi", gap.reason)
                self.assertEqual(
                    classify_ci_call(caption_tests.ffmpeg_skip_reason),
                    "HARD_FAILURE",
                )

        publication = _load("check-publication-evidence.py")
        case = publication.EvidenceTests("test_valid_mp4_delivery_decodes")
        case.setUp()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                with FakeFfmpeg(Path(tmp), "missing-sidedata"), github_actions("true"):
                    self.assertEqual(
                        classify_ci_call(case.test_valid_mp4_delivery_decodes),
                        "HARD_FAILURE",
                    )
        finally:
            case.doCleanups()

    def test_removed_github_actions_guard_is_caught(self) -> None:
        """One mutation: delete the video-privacy raise and require a hard failure."""
        source = (SCRIPTS / "check-video-normalization.py").read_text(encoding="utf-8")
        guard = (
            "        blocked = vf_ffmpeg_env.ci_skip_failure(gap)\n"
            "        if blocked:\n"
            "            raise RuntimeError(blocked)\n"
        )
        self.assertIn(guard, source)
        mutated = source.replace(guard, "", 1)
        self.assertNotIn("raise RuntimeError(blocked)", mutated)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "check_video_normalization_unguarded.py"
            path.write_text(mutated, encoding="utf-8")
            module = _load(path.name, path)
            with FakeFfmpeg(Path(tmp), "missing-sidedata"), github_actions("true"):
                self.assertEqual(
                    classify_ci_call(module.VideoNormalizationTests.setUpClass),
                    "GUARD_BYPASSED",
                )

    def test_caption_fribidi_skip_is_a_hard_failure_on_ci(self) -> None:
        """The caption suite itself fails when the fribidi build flag is missing."""
        import test_vf_ffmpeg_svg_caption as caption_tests

        with tempfile.TemporaryDirectory() as tmp:
            with FakeFfmpeg(Path(tmp), "missing-fribidi"), github_actions("true"):
                self.assertEqual(
                    classify_ci_call(caption_tests.ffmpeg_skip_reason),
                    "HARD_FAILURE",
                )

    def test_removed_caption_fribidi_guard_is_caught(self) -> None:
        """Deleting the caption ci_skip_failure raise lets the fribidi gap skip."""
        source = (SCRIPTS / "test_vf_ffmpeg_svg_caption.py").read_text(encoding="utf-8")
        guard = (
            "    blocked = vf_ffmpeg_env.ci_skip_failure(gap)\n"
            "    if blocked:\n"
            "        raise RuntimeError(blocked)\n"
        )
        self.assertEqual(source.count(guard), 1)
        mutated = source.replace(guard, "", 1)
        self.assertNotIn("raise RuntimeError(blocked)", mutated)
        start = mutated.index("def ffmpeg_skip_reason")
        end = mutated.index("\ndef write_composition")
        namespace: dict = {}
        exec(mutated[start:end], namespace)
        unguarded = namespace["ffmpeg_skip_reason"]
        with tempfile.TemporaryDirectory() as tmp:
            with FakeFfmpeg(Path(tmp), "missing-fribidi"), github_actions("true"):

                def skipped() -> None:
                    reason = unguarded()
                    if reason:
                        raise unittest.SkipTest(reason)

                self.assertEqual(classify_ci_call(skipped), "GUARD_BYPASSED")
                import test_vf_ffmpeg_svg_caption as caption_tests

                self.assertEqual(
                    classify_ci_call(caption_tests.ffmpeg_skip_reason),
                    "HARD_FAILURE",
                )

    def test_ci_env_truthy_values_fail_and_empty_values_skip(self) -> None:
        """true/True/TRUE/1 and CI=true are CI. Empty and unset still skip."""
        with EmptyPath():
            gap = vf_ffmpeg_env.normalization_gap()
            self.assertIsNotNone(gap)
            assert gap is not None
            cases = (
                ("True", None, gap.line),
                ("TRUE", None, gap.line),
                ("1", None, gap.line),
                (None, "true", gap.line),
                ("", None, None),
                (None, None, None),
            )
            for github_value, ci_value, expected in cases:
                with self.subTest(github_actions=github_value, ci=ci_value):
                    with ci_vars(github_value, ci_value):
                        self.assertEqual(vf_ffmpeg_env.ci_skip_failure(gap), expected)

    def test_exact_github_actions_true_check_is_caught(self) -> None:
        """Restoring GITHUB_ACTIONS=='true' accepts True and CI=true. The live gate must not."""
        source = (SCRIPTS / "vf_ffmpeg_env.py").read_text(encoding="utf-8")
        live = (
            "    if _truthy_ci(os.environ.get(\"GITHUB_ACTIONS\")) or _truthy_ci(os.environ.get(\"CI\")):\n"
        )
        exact = "    if os.environ.get(\"GITHUB_ACTIONS\") == \"true\":\n"
        self.assertEqual(source.count(live), 1)
        mutated_source = source.replace(live, exact, 1)
        self.assertNotIn("_truthy_ci(os.environ.get(\"CI\"))", mutated_source)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vf_ffmpeg_env_exact.py"
            path.write_text(mutated_source, encoding="utf-8")
            mutant = _load(path.name, path)
            with EmptyPath():
                gap = vf_ffmpeg_env.normalization_gap()
                self.assertIsNotNone(gap)
                assert gap is not None
                for github_value, ci_value in (("True", None), (None, "true"), ("1", None)):
                    with self.subTest(github_actions=github_value, ci=ci_value):
                        with ci_vars(github_value, ci_value):
                            self.assertIsNone(mutant.ci_skip_failure(gap))
                            self.assertEqual(vf_ffmpeg_env.ci_skip_failure(gap), gap.line)

    def test_removed_publication_fail_is_caught(self) -> None:
        """Deleting self.fail(blocked) lets the publication test skip. The static check names it."""
        checker = (SCRIPTS / "check-hyperframes-backend.py").read_text(encoding="utf-8")
        start = checker.index('ROOT / "scripts" / "check-publication-evidence.py"')
        block = checker[start:checker.index("\n    )", start)]
        self.assertIn('"self.fail(blocked)"', block)
        source = (SCRIPTS / "check-publication-evidence.py").read_text(encoding="utf-8")
        fail_block = "        if blocked:\n            self.fail(blocked)\n"
        self.assertGreaterEqual(source.count(fail_block), 2)
        mutated = source.replace(fail_block, "")
        mutated = mutated.replace(
            "ROOT = Path(__file__).resolve().parents[1]",
            f"ROOT = Path({str(ROOT)!r})",
            1,
        )
        self.assertNotIn("self.fail(blocked)", mutated)
        self.assertIn("ci_skip_failure", mutated)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "check_publication_evidence_nofail.py"
            path.write_text(mutated, encoding="utf-8")
            module = _load(path.name, path)
            case = module.EvidenceTests("test_public_mp4_requires_hash_bound_normalization")
            case.setUp()
            try:
                with github_actions("true"), EmptyPath():
                    self.assertEqual(
                        classify_ci_call(case.test_public_mp4_requires_hash_bound_normalization),
                        "GUARD_BYPASSED",
                    )
            finally:
                case.doCleanups()


if __name__ == "__main__":
    unittest.main(verbosity=2)
