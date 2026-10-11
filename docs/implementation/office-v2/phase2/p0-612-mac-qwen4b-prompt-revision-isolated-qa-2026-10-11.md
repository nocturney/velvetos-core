# Office 2.0 #612 — Mac Qwen3.5:4B prompt-revision source quality, hosted-only QA

**2026-10-11, isolated P0 research LAB.** Explicit follow-up to protected PR #695, whose *new* Chris Qwen9B merge-windows candidate passed independent hosted Docker visible 3/3 + hidden 12/12 tests while Mac Qwen4B canonical-tag candidate failed both. No actual model-generated Python was executed on either connected physical host. The purpose here is one bounded prompt-feedback experiment, NOT a new autonomous coding Worker, Git Sink signer, lease holder or production effect.

## Actual NEW Mac model calls (not a blind same-envelope retry)

MacMiniOffice.local owner user **chris**, loopback Ollama **qwen3.5:4b**, observed model digest `7f3251fa6878a78a606bcb3c074283306e5ad2ea411a7774a9dd98a4bc7f2d13`, port 11556, temperature 0, response-text only. Each fresh task had its own immutable directory, written STARTED.json before its **one** HTTP model request, then separate raw request/response, candidate.py.txt and receipt. Raw API responses and receipts stay on the Mac LAB host, while the sanitized two-attempt JSON manifest and exact candidate bytes are archived in Git. No model retry inside an UNKNOWN journal, no production credentials and no model output execution on Mac.

| Fresh Mac Qwen4B attempt | Task ID suffix | Source SHA256 | Seconds | Output tokens | Review |
| --- | --- | --- | ---: | ---: | --- |
| Public-criteria feedback A1 | `feedback-20261011-a1` | `27ee28702c88e1d84a2409c63337228693186e8802a1115faeace86a543f6b23` | 11.651 | 175 | AST rejected — `DYNAMIC_CALL_TARGET_REFUSED` |
| Explicit state-machine guidance B1 | `explicit-algorithm-20261011-b1` | `47c4a82129f7ca5ad034144c2301b029e6beb4e5578a4f6a7f4a0492de3c439c` | 10.606 | 132 | AST admitted, behavioral QA **NOT YET OBSERVED** |

A1 preserved the incorrect behavior class (lost first valid character after a separator, missing lowercase) and attempted an unreviewed dynamic method call `pop()`. Never submit A1 for execution. B1 instead used an explicit finite-state specification of *public rules*, not a hidden-test transcript or reference implementation; Qwen generated a 536-byte source whose AST statically adheres to the reviewed source policy. Static inspection **is not** proof that the algorithm works. The two new local request rounds cost $0 in extra paid API usage.

## Narrow isolated QA acceptance

A new separate PR-only GitHub Actions workflow with `permissions: {}` and `actions/checkout@v7` + `persist-credentials:false` runs `vf_office_v2_p0_hosted_mac4b_feedback_qa_lab.py selftest` first (15 bounded static checks, including A1 rejection, B1 exact SHA, and six unsafe Docker plan mutations). This offline selftest was run on Mac and `run` refused locally with `GH_HOSTED_LAB_CONTEXT_NOT_PRESENT`, code 2 and **zero Docker/model calls**. The standalone hosted `run` mode creates **one temporary** ephemeral Ubuntu Docker guest with pinned Python OCI RepoDigest, UID 65534, network none, root/read-only source mounts, cap-drop ALL, no new privileges, CPU/memory/PID/FD limits and no mounted writer key or Docker socket. The guest must independently verify **3 visible and 12 hidden tests**, deny host-canary/network/root escalation and return exact-source receipt. A1 never executes.

## Operational honesty

Original #695 already provides ONE different accepted Windows algorithm in hosted Docker; a **passing B1 hosted receipt**, IF observed, would establish a second distinct independently tested fixed algorithm from another physical model host, not two complete autonomous PR-authoring agents. One original Mac fail + A1 static reject + B1 potential success cannot establish broad prompt success rate, causal inference or general model reliability. The Mac code was **not run locally**; Aider/Job worker run and verification remain blocked by #691/#683. Docker daemon host control is trusted within this narrow synthetic LAB; #604 exclusive Git Sink custody and provider epoch cross-store fencing remain RED. No Codex CLI, paid API, social/publishing/customer/printer/CAD effects, new scheduler or system configuration changes.

Original single-shot requests and response hashes and distinct Task Envelopes: `docs/implementation/office-v2/phase2/p0-612-mac-qwen4b-prompt-revision-2026-10-11.json`. **Admission requires** independent Windows native static source/Office contracts, Mac Office contracts, protected exact-head hosted Docker and 120/120 CI, guarded normal PR merge and postmerge full 118/118 main CI.
