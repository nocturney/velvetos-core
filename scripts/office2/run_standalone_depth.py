#!/usr/bin/env python3
"""One offline step past the 2026-10-19 import smokes. check-all does not run this file.

check-all discovers only scripts/check-*.py. This helper stays under
scripts/office2/ on purpose. It installs nothing, posts nothing, and does
not edit the console, a dashboard, or a candidate registry.

A non-loopback TCP connect is refused. Each scenario runs inside
`unshare --net`. Pass --execute only when the depth venvs already exist
and OFFICE2_STANDALONE_DEPTH=1.
"""
from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "office2" / "standalone-candidate-depth-2026-10-19.md"
HOME = Path(os.environ.get("OFFICE2_DEPTH_HOME", "/tmp/office2-depth"))
TEMPORAL_BIN = Path(os.environ.get("OFFICE2_TEMPORAL_BIN", "/tmp/office2-smoke/bin/temporal"))

PINS = (
    "langgraph==1.2.16",
    "langgraph-checkpoint==4.3.0",
    "langgraph-checkpoint-sqlite==3.1.2",
    "dbos==3.3.0",
    "temporalio==1.32.0",
    "temporal CLI v1.9.1",
    "pydantic-ai==2.57.0",
    "litellm==1.88.6",
)


def _py(name: str) -> Path:
    return HOME / "venvs" / name / "bin" / "python"


def _env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    for key in list(env):
        upper = key.upper()
        if any(part in upper for part in ("KEY", "TOKEN", "SECRET", "PASSWORD")):
            env.pop(key, None)
    env["PYTHONPATH"] = str(HOME / "nethook")
    env["HOME"] = str(HOME / "home")
    env["HF_HUB_OFFLINE"] = "1"
    env["TRANSFORMERS_OFFLINE"] = "1"
    env["DO_NOT_TRACK"] = "1"
    env["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
    env["OFFICE2_NETLOG"] = str(HOME / "recorded" / "net.log")
    if extra:
        env.update(extra)
    return env


def _prepare() -> None:
    hook = HOME / "nethook"
    work = HOME / "recorded"
    hook.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    (HOME / "home").mkdir(parents=True, exist_ok=True)
    (hook / "sitecustomize.py").write_text(
        textwrap.dedent(
            """\
            import os
            import socket

            _connect = socket.socket.connect
            _log = os.environ.get("OFFICE2_NETLOG", "")

            def guarded(self, address):
                if _log:
                    try:
                        with open(_log, "a", encoding="utf-8") as handle:
                            handle.write(repr(address) + "\\n")
                    except OSError:
                        pass
                if isinstance(address, tuple) and address:
                    host = str(address[0])
                    if host not in {"127.0.0.1", "::1", "localhost"}:
                        raise OSError("refused non-loopback connect to " + repr(address))
                return _connect(self, address)

            socket.socket.connect = guarded
            """
        ),
        encoding="utf-8",
    )
    netlog = work / "net.log"
    if netlog.exists():
        netlog.unlink()


def _run(py: Path, script: Path, env: dict[str, str], timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["unshare", "--net", "--map-root-user", "--", str(py), "-u", str(script)],
        env=env,
        timeout=timeout,
        capture_output=True,
        text=True,
        check=False,
    )


def _show(title: str, result: subprocess.CompletedProcess[str]) -> int:
    print("==", title, "rc", result.returncode)
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip())
    netlog = HOME / "recorded" / "net.log"
    print("-- netlog")
    if netlog.exists() and netlog.stat().st_size:
        print(netlog.read_text(encoding="utf-8").rstrip())
    else:
        print("(empty)")
    netlog.write_text("", encoding="utf-8")
    return result.returncode


def _write(name: str, body: str) -> Path:
    path = HOME / "recorded" / name
    path.write_text(textwrap.dedent(body).lstrip("\n"), encoding="utf-8")
    return path


def _join(body: str) -> str:
    return textwrap.dedent(body).lstrip("\n")


LO_UP = """
import fcntl
import socket
import struct

def lo_up() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ifr = struct.pack("16sH14s", b"lo", 0, b"\\x00" * 14)
    flags = struct.unpack("16sH14s", fcntl.ioctl(sock.fileno(), 0x8913, ifr))[1]
    ifr = struct.pack("16sH14s", b"lo", flags | 1, b"\\x00" * 14)
    fcntl.ioctl(sock.fileno(), 0x8914, ifr)
    sock.close()
"""


def langgraph() -> int:
    script = _write(
        "langgraph_depth.py",
        """
        import importlib.metadata as metadata
        from typing import TypedDict

        from langgraph.checkpoint.sqlite import SqliteSaver
        from langgraph.graph import END, START, StateGraph

        print("langgraph", metadata.version("langgraph"))
        print("langgraph-checkpoint", metadata.version("langgraph-checkpoint"))
        print("langgraph-checkpoint-sqlite", metadata.version("langgraph-checkpoint-sqlite"))

        class S(TypedDict):
            n: int
            trace: list[str]

        def step1(state: S) -> dict:
            return {"n": state["n"] + 1, "trace": state["trace"] + ["a"]}

        def step2(state: S) -> dict:
            return {"n": state["n"] + 10, "trace": state["trace"] + ["b"]}

        def step3(state: S) -> dict:
            return {"n": state["n"] + 100, "trace": state["trace"] + ["c"]}

        def build():
            graph = StateGraph(S)
            graph.add_node("step1", step1)
            graph.add_node("step2", step2)
            graph.add_node("step3", step3)
            graph.add_edge(START, "step1")
            graph.add_edge("step1", "step2")
            graph.add_edge("step2", "step3")
            graph.add_edge("step3", END)
            return graph

        cfg = {"configurable": {"thread_id": "office2-depth"}}
        path = "__DB__"

        with SqliteSaver.from_conn_string(path) as saver:
            compiled = build().compile(checkpointer=saver, interrupt_after=["step2"])
            paused = compiled.invoke({"n": 1, "trace": []}, cfg)
            print("PAUSED", paused)
            print("NEXT", list(compiled.get_state(cfg).next))
        with SqliteSaver.from_conn_string(path) as saver:
            compiled = build().compile(checkpointer=saver, interrupt_after=["step2"])
            print("REOPEN_NEXT", list(compiled.get_state(cfg).next))
            print("DONE", compiled.invoke(None, cfg))
        """.replace("__DB__", str(HOME / "recorded" / "langgraph.sqlite")),
    )
    db = HOME / "recorded" / "langgraph.sqlite"
    if db.exists():
        db.unlink()
    return _show("langgraph", _run(_py("langgraph"), script, _env(), 60))


def dbos() -> int:
    job = _write(
        "dbos_job.py",
        """
        import os
        import sys
        import time

        from dbos import DBOS

        MARKER = os.environ["OFFICE2_DBOS_MARKER"]
        ROLE = os.environ["DBOS_ROLE"]

        DBOS(config={"name": "office2-depth", "system_database_url": os.environ["OFFICE2_DBOS_URL"]})

        @DBOS.step()
        def step_one() -> str:
            with open(MARKER, "a", encoding="utf-8") as handle:
                handle.write("step1\\n")
            return "one"

        @DBOS.step()
        def step_two() -> str:
            with open(MARKER, "a", encoding="utf-8") as handle:
                handle.write("step2-start\\n")
            if ROLE == "victim":
                time.sleep(45)
            with open(MARKER, "a", encoding="utf-8") as handle:
                handle.write("step2-done\\n")
            return "two"

        @DBOS.workflow()
        def job() -> str:
            return step_one() + step_two()

        def main() -> int:
            DBOS.launch()
            if sys.argv[1] == "start":
                handle = DBOS.start_workflow(job)
                print("WORKFLOW", handle.workflow_id, flush=True)
                print("RESULT", handle.get_result(), flush=True)
                return 0
            deadline = time.time() + 25
            while time.time() < deadline:
                rows = DBOS.list_workflows()
                if rows:
                    workflow_id = rows[0].workflow_id
                    status = DBOS.get_workflow_status(workflow_id)
                    print("STATUS", status.status, flush=True)
                    if status.status == "SUCCESS":
                        print("RESULT", DBOS.get_result(workflow_id), flush=True)
                        DBOS.destroy()
                        return 0
                time.sleep(0.4)
            print("TIMEOUT", flush=True)
            DBOS.destroy()
            return 1

        if __name__ == "__main__":
            sys.exit(main())
        """,
    )
    driver = _write(
        "dbos_driver.py",
        _join(LO_UP)
        + "\n"
        + _join(
            """
        import os
        import subprocess
        import sys
        import time

        lo_up()
        marker = os.environ["OFFICE2_DBOS_MARKER"]
        py = os.environ["OFFICE2_DBOS_PY"]
        job = os.environ["OFFICE2_DBOS_JOB"]
        env = os.environ.copy()
        env["DBOS_ROLE"] = "victim"
        victim = subprocess.Popen([py, "-u", job, "start"], env=env)
        deadline = time.time() + 20
        while time.time() < deadline:
            if os.path.exists(marker) and "step2-start" in open(marker, encoding="utf-8").read():
                break
            time.sleep(0.1)
        else:
            victim.kill()
            print("NO_STEP2")
            sys.exit(1)
        print("KILL", victim.pid, flush=True)
        victim.kill()
        victim.wait(timeout=5)
        env["DBOS_ROLE"] = "recover"
        recover = subprocess.run([py, "-u", job, "recover"], env=env, check=False)
        print("MARKER")
        print(open(marker, encoding="utf-8").read().rstrip())
        sys.exit(recover.returncode)
            """
        ),
    )
    marker = HOME / "recorded" / "dbos-marker.txt"
    db = HOME / "recorded" / "dbos.sqlite"
    if marker.exists():
        marker.unlink()
    if db.exists():
        db.unlink()
    env = _env(
        {
            "OFFICE2_DBOS_MARKER": str(marker),
            "OFFICE2_DBOS_URL": "sqlite:////" + str(db).lstrip("/"),
            "OFFICE2_DBOS_PY": str(_py("dbos")),
            "OFFICE2_DBOS_JOB": str(job),
            "DBOS_ROLE": "victim",
        }
    )
    # sqlite:////tmp/... is four slashes: scheme, empty host, absolute path.
    env["OFFICE2_DBOS_URL"] = "sqlite:////" + str(db).lstrip("/")
    return _show("dbos", _run(_py("dbos"), driver, env, 60))


def temporal() -> int:
    flow = _write(
        "temporal_flow.py",
        """
        import asyncio
        import os
        from datetime import timedelta

        from temporalio import activity, workflow
        from temporalio.common import RetryPolicy

        RETRY = RetryPolicy(maximum_attempts=3, initial_interval=timedelta(seconds=1))

        @activity.defn
        async def step(name: str) -> str:
            marker = os.environ["OFFICE2_TEMPORAL_MARKER"]
            with open(marker, "a", encoding="utf-8") as handle:
                handle.write(name + "\\n")
                handle.flush()
            if name == "two" and os.environ.get("WORKER_ROLE") == "first":
                await asyncio.sleep(60)
            return name

        @workflow.defn
        class ThreeStep:
            @workflow.run
            async def run(self) -> str:
                one = await workflow.execute_activity(
                    step, "one", start_to_close_timeout=timedelta(seconds=20), retry_policy=RETRY
                )
                two = await workflow.execute_activity(
                    step,
                    "two",
                    start_to_close_timeout=timedelta(seconds=90),
                    heartbeat_timeout=timedelta(seconds=3),
                    retry_policy=RETRY,
                )
                three = await workflow.execute_activity(
                    step, "three", start_to_close_timeout=timedelta(seconds=20), retry_policy=RETRY
                )
                return "|".join([one, two, three])
        """,
    )
    _write(
        "temporal_worker.py",
        """
        import asyncio
        import sys

        from temporalio.client import Client
        from temporalio.worker import Worker

        from temporal_flow import ThreeStep, step

        async def main() -> None:
            client = await Client.connect("127.0.0.1:7233")
            worker = Worker(client, task_queue="office2-depth", workflows=[ThreeStep], activities=[step])
            print("WORKER", sys.argv[1], flush=True)
            await worker.run()

        if __name__ == "__main__":
            asyncio.run(main())
        """,
    )
    _write(
        "temporal_client.py",
        """
        import asyncio

        from temporalio.client import Client

        from temporal_flow import ThreeStep

        async def main() -> None:
            client = await Client.connect("127.0.0.1:7233")
            result = await client.execute_workflow(
                ThreeStep.run, id="office2-depth-1", task_queue="office2-depth"
            )
            print("RESULT", result, flush=True)

        if __name__ == "__main__":
            asyncio.run(main())
        """,
    )
    driver = _write(
        "temporal_driver.py",
        _join(LO_UP)
        + "\n"
        + _join(
            """
        import importlib.metadata as metadata
        import os
        import socket
        import subprocess
        import sys
        import time

        print("temporalio", metadata.version("temporalio"))
        lo_up()
        marker = os.environ["OFFICE2_TEMPORAL_MARKER"]
        temporal = os.environ["OFFICE2_TEMPORAL_BIN"]
        py = os.environ["OFFICE2_TEMPORAL_PY"]
        db = os.environ["OFFICE2_TEMPORAL_DB"]
        log_path = os.environ["OFFICE2_TEMPORAL_LOG"]
        src = os.environ["OFFICE2_TEMPORAL_SRC"]
        log = open(log_path, "w", encoding="utf-8")
        server = subprocess.Popen(
            [temporal, "server", "start-dev", "--ip", "127.0.0.1", "--port", "7233", "--ui-port", "8233", "--db-filename", db],
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        workers = []
        client = None
        worker_log = open(log_path + ".worker", "w", encoding="utf-8")
        client_log = open(log_path + ".client", "w", encoding="utf-8")
        try:
            deadline = time.time() + 25
            while time.time() < deadline:
                probe = socket.socket()
                probe.settimeout(0.3)
                try:
                    probe.connect(("127.0.0.1", 7233))
                    break
                except OSError:
                    time.sleep(0.2)
                finally:
                    probe.close()
            else:
                print("SERVER_DOWN")
                return 1
            print("SERVER_UP", server.pid, flush=True)
            env1 = os.environ.copy()
            env1["WORKER_ROLE"] = "first"
            env1["PYTHONPATH"] = src + os.pathsep + env1.get("PYTHONPATH", "")
            env2 = os.environ.copy()
            env2["WORKER_ROLE"] = "second"
            env2["PYTHONPATH"] = src + os.pathsep + env2.get("PYTHONPATH", "")
            workers.append(subprocess.Popen([py, "-u", os.path.join(src, "temporal_worker.py"), "first"], env=env1, stdout=worker_log, stderr=subprocess.STDOUT))
            time.sleep(0.8)
            client_env = os.environ.copy()
            client_env["PYTHONPATH"] = src + os.pathsep + client_env.get("PYTHONPATH", "")
            client = subprocess.Popen([py, "-u", os.path.join(src, "temporal_client.py")], env=client_env, stdout=client_log, stderr=subprocess.STDOUT)
            deadline = time.time() + 20
            while time.time() < deadline:
                if os.path.exists(marker) and "two" in open(marker, encoding="utf-8").read():
                    break
                time.sleep(0.1)
            else:
                print("NO_TWO_MARKER")
                return 1
            print("KILL_WORKER", workers[0].pid, flush=True)
            workers[0].kill()
            workers[0].wait(timeout=5)
            workers.append(subprocess.Popen([py, "-u", os.path.join(src, "temporal_worker.py"), "second"], env=env2, stdout=worker_log, stderr=subprocess.STDOUT))
            client.wait(timeout=40)
            print("CLIENT_RC", client.returncode, flush=True)
            print("MARKER")
            print(open(marker, encoding="utf-8").read().rstrip())
            print("CLIENT")
            print(open(log_path + ".client", encoding="utf-8").read().rstrip())
            print("SERVER")
            print("\\n".join(open(log_path, encoding="utf-8").read().splitlines()[:8]))
            return 0 if client.returncode == 0 else 1
        finally:
            for proc in workers:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait(timeout=5)
            if client is not None and client.poll() is None:
                client.kill()
                client.wait(timeout=5)
            if server.poll() is None:
                server.kill()
                server.wait(timeout=5)
            log.close()
            worker_log.close()
            client_log.close()

        if False:
            pass
            """
        ),
    )
    # The driver uses return inside main-less script. Wrap it.
    wrapped = _write(
        "temporal_driver_main.py",
        "import runpy\nimport sys\n"
        # Can't return at module level. Rewrite by exec of a main().
        ,
    )
    # Replace the driver body so top-level returns live in main().
    raw = driver.read_text(encoding="utf-8")
    raw = raw.replace("if False:\n    pass\n", "")
    driver.write_text(
        "def main():\n"
        + "\n".join(("    " + line if line else "") for line in raw.splitlines())
        + "\n\nif __name__ == '__main__':\n    sys.exit(main() or 0)\n",
        encoding="utf-8",
    )
    # The indent wrapper does not import sys if the body doesn't. Add it.
    text = driver.read_text(encoding="utf-8")
    if "import sys" not in text.split("def main")[0]:
        driver.write_text("import sys\n" + text, encoding="utf-8")
    marker = HOME / "recorded" / "temporal-marker.txt"
    db = HOME / "recorded" / "temporal.db"
    if marker.exists():
        marker.unlink()
    if db.exists():
        db.unlink()
    env = _env(
        {
            "OFFICE2_TEMPORAL_MARKER": str(marker),
            "OFFICE2_TEMPORAL_BIN": str(TEMPORAL_BIN),
            "OFFICE2_TEMPORAL_PY": str(_py("temporal")),
            "OFFICE2_TEMPORAL_DB": str(db),
            "OFFICE2_TEMPORAL_LOG": str(HOME / "recorded" / "temporal-server.log"),
            "OFFICE2_TEMPORAL_SRC": str(HOME / "recorded"),
            "WORKER_ROLE": "second",
        }
    )
    del wrapped, flow
    return _show("temporal", _run(_py("temporal"), driver, env, 90))


def pydantic_ai() -> int:
    script = _write(
        "pydantic_depth.py",
        """
        import importlib.metadata as metadata

        from pydantic import BaseModel
        from pydantic_ai import Agent
        from pydantic_ai.models.test import TestModel

        print("pydantic-ai", metadata.version("pydantic-ai"))

        class OfferCard(BaseModel):
            sku: str
            ready: bool
            note: str

        seeded = Agent(
            TestModel(custom_output_args={"sku": "shelf-1", "ready": True, "note": "pickup"}),
            output_type=OfferCard,
        )
        print("SEEDED", seeded.run_sync("draft an offer card for shelf-1").output.model_dump())
        plain = Agent(TestModel(), output_type=OfferCard)
        print("PLAIN", plain.run_sync("draft an offer card for shelf-1").output.model_dump())
        """,
    )
    return _show("pydantic-ai", _run(_py("pydantic"), script, _env(), 60))


def litellm() -> int:
    script = _write(
        "litellm_depth.py",
        _join(LO_UP)
        + "\n"
        + _join(
            """
        import importlib.metadata as metadata

        lo_up()
        import litellm
        from litellm import Router

        print("litellm", metadata.version("litellm"))
        litellm.suppress_debug_info = True
        router = Router(
            model_list=[
                {
                    "model_name": "office-primary",
                    "litellm_params": {
                        "model": "openai/primary-down",
                        "api_key": "local",
                        "api_base": "http://127.0.0.1:9/v1",
                    },
                },
                {
                    "model_name": "office-backup",
                    "litellm_params": {
                        "model": "openai/backup-up",
                        "api_key": "local",
                        "mock_response": "pong-from-backup",
                    },
                },
            ],
            fallbacks=[{"office-primary": ["office-backup"]}],
            num_retries=0,
        )
        response = router.completion(
            model="office-primary",
            messages=[{"role": "user", "content": "ping"}],
            timeout=3,
        )
        print("CONTENT", response.choices[0].message.content)
        print("MODEL", response.model)
        hidden = getattr(response, "_hidden_params", {}) or {}
        print("HIDDEN_API_BASE", hidden.get("api_base"))
            """
        ),
    )
    return _show("litellm", _run(_py("litellm"), script, _env(), 60))


def main(argv: list[str]) -> int:
    if os.environ.get("OFFICE2_STANDALONE_DEPTH") != "1" or "--execute" not in argv:
        print("Office 2.0 standalone depth scenarios are recorded in:")
        print(DOC)
        print("Pins:", ", ".join(PINS))
        print("Refusing to run. Set OFFICE2_STANDALONE_DEPTH=1 and pass --execute.")
        return 2
    missing = [str(path) for path in (_py("langgraph"), _py("dbos"), _py("temporal"), _py("pydantic"), _py("litellm"), TEMPORAL_BIN) if not path.is_file()]
    if missing:
        print("missing runtime:", ", ".join(missing))
        return 1
    _prepare()
    codes = [langgraph(), dbos(), temporal(), pydantic_ai(), litellm()]
    print("DEPTH", "PASS" if all(code == 0 for code in codes) else "FAIL", codes)
    return 0 if all(code == 0 for code in codes) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
