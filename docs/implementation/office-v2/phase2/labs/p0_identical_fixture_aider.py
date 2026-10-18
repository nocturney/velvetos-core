#!/usr/bin/env python3
"""Office #612: identical, bounded LAB coding fixture on two separate hosts.
No repo authority, no external effects, no paid model. NOT an OS/network sandbox.
"""
from __future__ import annotations
import argparse, datetime, hashlib, json, os, pathlib, platform, shutil, subprocess, sys, tempfile, time, urllib.request

SOURCE = '''import re

def slugify(value: str) -> str:
    """Lowercase ASCII; collapse punctuation/whitespace to hyphens, strip, default untitled."""
    return value.lower().replace(" ", "-")
'''
TEST = '''import unittest
from slug import slugify

class SlugTests(unittest.TestCase):
    def test_basic(self): self.assertEqual(slugify("Hello   World!!"), "hello-world")
    def test_edges(self): self.assertEqual(slugify(" _ABC_ 42_ "), "abc-42")
    def test_empty(self): self.assertEqual(slugify("!?"), "untitled")
'''
EXTRA = """from slug import slugify
cases = [
("a  b","a-b"),("HELLO","hello"),("!_A_-B!","a-b"),
("2026/Oct/08","2026-oct-08"),("  ","untitled"),("A..B","a-b"),
("A_B","a-b"),("a---b","a-b"),("mixed Case","mixed-case"),
("!?","untitled"),("Hi!","hi"),("42","42")]
for inp, expected in cases:
    actual = slugify(inp)
    assert actual == expected, (inp, expected, actual)
print("EDGE_CASES_PASS=12")
"""

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
def utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
def run(argv, *, cwd=None, env=None, timeout=20):
    return subprocess.run(argv,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        timeout=timeout,encoding="utf-8",errors="replace")
def git(root,*args):
    p=run(["git","-C",str(root),*args])
    if p.returncode: raise RuntimeError("GIT_FAILURE:"+p.stderr[:120])
    return p.stdout.rstrip("\n")
def prepare(root):
    if root.exists(): raise RuntimeError("PATH_ALREADY_EXISTS")
    root.mkdir(parents=True)
    (root/"tests").mkdir()
    (root/"slug.py").write_bytes(SOURCE.encode())
    (root/"tests"/"test_slug.py").write_bytes(TEST.encode())
    p=run(["git","init","-b","main",str(root)])
    if p.returncode: raise RuntimeError(p.stderr[:200])
    git(root,"config","core.autocrlf","false")
    git(root,"add","--","slug.py","tests/test_slug.py")
    git(root,"-c","user.name=P0 Fixture","-c","user.email=fixture@example.invalid",
        "commit","-qm","P0 identical coding fixture")
    print(json.dumps({"state":"PREPARED","base":git(root,"rev-parse","HEAD"),
        "source_blob":git(root,"hash-object","slug.py"),
        "source_sha256":sha((root/"slug.py").read_bytes()),
        "tests_sha256":sha((root/"tests"/"test_slug.py").read_bytes()),
        "clean":not bool(git(root,"status","--porcelain","--untracked-files=all"))}))
def check(root):
    return run([sys.executable,"-B","-m","unittest","discover","-s","tests","-q"],
        cwd=root,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"},timeout=20)
def qa(original,after):
    with tempfile.TemporaryDirectory(prefix="p0-independent-qa-") as td:
        target=pathlib.Path(td)/"replay"
        p=run(["git","clone","--local","--no-hardlinks",str(original),str(target)],timeout=25)
        if p.returncode: return {"pass":False,"step":"clone","diagnostic":p.stderr[:180]}
        (target/"slug.py").write_bytes(after)
        unit=check(target)
        edge=run([sys.executable,"-B","-c",EXTRA],cwd=target,
            env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"},timeout=15)
        changed=git(target,"status","--porcelain","--untracked-files=all").splitlines()
        return {"pass":unit.returncode==0 and edge.returncode==0 and changed==[" M slug.py"],
            "unit_exit":unit.returncode,"unit_summary":[x for x in unit.stderr.splitlines() if x.startswith("Ran ")],
            "edge_exit":edge.returncode,"edge_ok":"EDGE_CASES_PASS=12" in edge.stdout,
            "changed_paths":changed,"replayed_sha256":sha((target/"slug.py").read_bytes())}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=["prepare","run"])
    p.add_argument("--repo",required=True)
    p.add_argument("--out")
    p.add_argument("--aider")
    p.add_argument("--model",choices=["qwen3.5:4b","qwen3.5:9b"])
    p.add_argument("--port",type=int,choices=[11555,11556])
    p.add_argument("--timeout",type=int,default=170)
    p.add_argument("--trial",default="p0-lab")
    a=p.parse_args()
    root=pathlib.Path(a.repo).resolve()
    if a.action=="prepare":
        prepare(root);return 0
    assert a.out and a.aider and a.port and a.model and 30<=a.timeout<=240
    out=pathlib.Path(a.out).resolve()
    executable=pathlib.Path(a.aider).resolve()
    if out.exists() or out.is_relative_to(root): raise RuntimeError("OUTPUT_COLLISION")
    if not executable.is_file() or not (root/".git").exists(): raise RuntimeError("EXECUTOR_OR_GIT_MISSING")
    if git(root,"branch","--show-current")!="main": raise RuntimeError("BRANCH_MISMATCH")
    if git(root,"status","--porcelain","--untracked-files=all"):raise RuntimeError("DIRTY_INPUT")
    if (root/"slug.py").read_bytes()!=SOURCE.encode():raise RuntimeError("UNPINNED_SOURCE")
    baseline=check(root)
    if baseline.returncode==0:raise RuntimeError("BASELINE_UNEXPECTED_GREEN")
    url="http://127.0.0.1:%s/api/tags"%a.port
    models=json.load(urllib.request.urlopen(url,timeout=4))
    if a.model not in [m.get("name") for m in models.get("models",[])]:raise RuntimeError("MODEL_NOT_AVAILABLE")
    out.mkdir(parents=True)
    for label in ["home","config","data","cache","tmp","local","roaming","programdata"]:(out/label).mkdir()
    (out/"empty.env").write_bytes(b"")
    (out/"empty.yml").write_bytes(b"{}\n")
    env={k:os.environ[k] for k in ("PATH","SYSTEMROOT","WINDIR","COMSPEC","PATHEXT","TEMP","TMP","TMPDIR","LANG","LC_ALL") if k in os.environ}
    env.update({"HOME":str(out/"home"),"USERPROFILE":str(out/"home"),"XDG_CONFIG_HOME":str(out/"config"),
        "XDG_DATA_HOME":str(out/"data"),"XDG_CACHE_HOME":str(out/"cache"),"TMPDIR":str(out/"tmp"),
        "PROGRAMDATA":str(out/"programdata"),"APPDATA":str(out/"roaming"),"LOCALAPPDATA":str(out/"local"),
        "PYTHONIOENCODING":"utf-8","PYTHONUTF8":"1","TERM":"dumb","NO_COLOR":"1",
        "OLLAMA_API_BASE":"http://127.0.0.1:%s"%a.port,"NO_PROXY":"127.0.0.1,localhost,::1",
        "PYTHONDONTWRITEBYTECODE":"1","GIT_TERMINAL_PROMPT":"0","AIDER_ANALYTICS":"false"})
    prompt=("In this disposable, offline, synthetic Python fixture, fix slug.py according to the "
        "function docstring and the read-only tests so all unittest cases pass. "
        "Modify ONLY slug.py; preserve signature; do not run shell commands or edit test files.")
    cmd=[str(executable),"--model","ollama_chat/"+a.model,"--edit-format","whole",
        "--file","slug.py","--read","tests/test_slug.py","--message",prompt,
        "--no-auto-commits","--no-dirty-commits","--no-auto-lint","--no-auto-test",
        "--no-gitignore","--no-analytics","--no-check-update","--no-show-model-warnings",
        "--no-suggest-shell-commands","--no-browser","--no-pretty","--no-stream",
        "--no-fancy-input","--no-multiline","--no-detect-urls","--no-restore-chat-history",
        "--no-watch-files","--disable-playwright","--yes-always","--map-tokens","0",
        "--env-file",str(out/"empty.env"),"--config",str(out/"empty.yml"),
        "--input-history-file",str(out/"input.history"),
        "--chat-history-file",str(out/"chat.history.md"),
        "--llm-history-file",str(out/"llm.history.log")]
    started=utc(); start=time.monotonic();state="UNKNOWN_OUTCOME";ex=None
    stdout=stderr=""
    try:
        result=run(cmd,cwd=root,env=env,timeout=a.timeout)
        ex=result.returncode;stdout=result.stdout;stderr=result.stderr
        state="FINISHED" if ex==0 else "EXECUTOR_ERROR"
    except subprocess.TimeoutExpired as e:
        state="TIMEOUT_UNKNOWN"
        stdout=(e.stdout or b"").decode("utf-8","replace") if isinstance(e.stdout,bytes) else (e.stdout or "")
        stderr=(e.stderr or b"").decode("utf-8","replace") if isinstance(e.stderr,bytes) else (e.stderr or "")
    elapsed=round(time.monotonic()-start,3);finished=utc()
    (out/"stdout.log").write_bytes(stdout.encode())
    (out/"stderr.log").write_bytes(stderr.encode())
    paths=git(root,"status","--porcelain","--untracked-files=all").splitlines()
    after=(root/"slug.py").read_bytes()
    verified=qa(root,after) if state=="FINISHED" and paths==[" M slug.py"] else {"pass":False,"reason":"non-success or changed paths"}
    success=state=="FINISHED" and paths==[" M slug.py"] and verified["pass"]
    receipt={"schema":"vf.office-v2.same-fixture-two-host-lab.v0","trial":a.trial,
        "host":platform.node(),"platform":platform.platform(),"model":a.model,"executor":"Aider 0.86.2",
        "source_sha256":sha(SOURCE.encode()),"source_blob":git(root,"rev-parse","HEAD:slug.py"),
        "base_sha":git(root,"rev-parse","HEAD"),"started_utc":started,"finished_utc":finished,
        "elapsed_seconds":elapsed,"exit_code":ex,"state":state,"changed_paths":paths,
        "after_sha256":sha(after),"stdout_sha256":sha(stdout.encode()),"stderr_sha256":sha(stderr.encode()),
        "independent_qa":verified,"verified_success":success,"external_spend_usd":0,
        "model_invoked_locally":True,"codex_cli":False,"scheduler_or_os_sandbox_proven":False}
    receipt["receipt_sha256"]=sha(json.dumps(receipt,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode())
    (out/"receipt.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"trial":a.trial,"host":receipt["host"],"elapsed_seconds":elapsed,
        "state":state,"exit_code":ex,"verified_success":success,"changed_paths":paths,
        "edge_pass":verified.get("edge_ok"),"receipt_sha256":receipt["receipt_sha256"]}))
    return 0 if success else 2
if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as e:
        print(json.dumps({"status":"FAIL_CLOSED","reason":str(e)[:160]}))
        raise SystemExit(2)
