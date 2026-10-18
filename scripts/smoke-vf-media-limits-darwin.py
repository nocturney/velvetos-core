#!/usr/bin/env python3
"""Manual, unprivileged Darwin process-group acceptance; synthetic assets only.

Run: python3 scripts/smoke-vf-media-limits-darwin.py
Not a production effects/asset-render gate or cross-session process sandbox.
"""
import importlib.util
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

if sys.platform != "darwin":
    print("SKIP Darwin-only bounded media process-group acceptance")
    raise SystemExit(0)

path = Path(__file__).with_name("vf_media_limits.py")
spec = importlib.util.spec_from_file_location("vf_media_limits_darwin_smoke", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
cap = 64 * 1024 * 1024
passed = 0


def run_case(label, cmd, *, timeout=5, memory=cap, capture=False, denied=False):
    global passed
    try:
        module.run_bounded(cmd, timeout=timeout, memory_bytes=memory, capture=capture)
        outcome = "allow"
    except ValueError:
        outcome = "deny"
    if (outcome == "deny") != denied:
        raise AssertionError(f"{label}: unexpected {outcome}")
    passed += 1
    print("PASS", label, outcome, flush=True)


run_case("benign_child", [sys.executable, "-c", "print('hello')"], capture=True)
run_case("excess_stdout", [sys.executable, "-c", 'print("A"*80000)'], capture=True, denied=True)
run_case("nonzero_child", [sys.executable, "-c", "raise SystemExit(3)"], denied=True)
run_case("wall_timeout", [sys.executable, "-c", "import time;time.sleep(3)"], timeout=1, denied=True)
run_case("direct_rss", [sys.executable, "-c", "import time;x=bytearray(145000000);time.sleep(1)"], denied=True)

alloc = "import time;x=bytearray(145000000);time.sleep(.8)"
wait_grandchild = (
    "import subprocess,sys;"
    "p=subprocess.Popen([sys.executable, '-c', " + repr(alloc) + "]);"
    "raise SystemExit(p.wait())"
)
run_case("forked_grandchild_rss", [sys.executable, "-c", wait_grandchild], denied=True)

real_ffmpeg = shutil.which("ffmpeg")
if real_ffmpeg:
    source = [real_ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error",
              "-re", "-f", "lavfi", "-i", "testsrc=size=1920x1080:rate=8",
              "-frames:v", "8", "-f", "null", "-"]
    run_case("synthetic_1080p_ffmpeg_512m", source, timeout=8, memory=512*1024*1024)
    run_case("synthetic_1080p_ffmpeg_16m", source, timeout=8, memory=16*1024*1024, denied=True)
else:
    print("SKIP optional synthetic FFmpeg 1080p cases (ffmpeg not installed)", flush=True)

# A parent can exit while an ordinary same-group descendant still runs. A
# successful bounded wrapper must have killed the descendant before returning.
with tempfile.TemporaryDirectory(prefix="vf-media-pgroup-") as directory:
    marker = str(Path(directory, "child.pid"))
    escaped = (
        "import os,time;"
        "f=open(" + repr(marker) + ",'w');f.write(str(os.getpid()));f.close();"
        "x=bytearray(32000000);time.sleep(5)"
    )
    quick_parent = (
        "import subprocess,sys,time;"
        "subprocess.Popen([sys.executable, '-c', " + repr(escaped) + "],"
        "stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);"
        "time.sleep(.35)"
    )
    try:
        module.run_bounded([sys.executable, "-c", quick_parent], timeout=5,
                           memory_bytes=512 * 1024 * 1024)
    except ValueError:
        # A conservative denial is acceptable for a parent with unfinished work.
        pass
    pid_path = Path(marker)
    if not pid_path.is_file():
        raise AssertionError("orphan cleanup fixture did not write PID")
    pid = int(pid_path.read_text())
    time.sleep(.15)
    result = subprocess.run(["/bin/ps", "-p", str(pid), "-o", "stat="],
                            capture_output=True, text=True, check=False)
    running = result.returncode == 0 and not result.stdout.strip().startswith("Z")
    if running:
        try:
            os.kill(pid, signal.SIGKILL)  # clean exactly our synthetic child
        except ProcessLookupError:
            pass
        raise AssertionError("same-group descendant survived worker completion")
    passed += 1
    print("PASS", "orphan_same_group_reaped", flush=True)

# Monkeypatch only our isolated local smoke process, never production code.
original_run = module.subprocess.run
try:
    for mode in ("unavailable", "malformed", "wrong_group", "over_cap"):
        def fake_sampler(args, **kwargs):
            if mode == "unavailable":
                raise OSError("synthetic /bin/ps unavailable")
            if mode == "malformed":
                output = "bad data"
            elif mode == "wrong_group":
                output = "777 999999 4"
            else:
                output = "777 " + args[4] + " 999999"
            return subprocess.CompletedProcess(args, 0, output, "")
        module.subprocess.run = fake_sampler
        outcome = module._worker([sys.executable, "-c", "import time;time.sleep(2)"], 5, cap, False)
        if outcome != 2:
            raise AssertionError("invalid sampler was not denied: " + mode)
        passed += 1
        print("PASS", "negative_sampler_" + mode, flush=True)
finally:
    module.subprocess.run = original_run

print("DARWIN_PROCESS_GROUP_ACCEPTANCE_PASS", passed, "cases", flush=True)
