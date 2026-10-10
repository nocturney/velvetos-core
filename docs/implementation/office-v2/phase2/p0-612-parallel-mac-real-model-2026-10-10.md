# #612: Mac Qwen 4B model-generated code during real two-host parallel trial (2026-10-10)

**Observed:** SUCCEEDED on real MacMiniOffice.local, local Qwen3.5:4b, already installed Aider v0.86.2. This is a new real model invocation and quarantined source, not an autonomous native GitHub writer.

- Mac model digest 7f3251fa6878a78a606bcb3c074283306e5ad2ea411a7774a9dd98a4bc7f2d13; existing Aider venv Python provided psutil 7.2.2; no install, no paid API, no Codex CLI.
- New prepared-only fixture p0-diverse-speed-mac-tag-20261010-c, Git base c4e9417e7a2a4303260e5f08253be4cd5cbe2529; new task p0-diverse-run-mac-speed-tag-20261010-c with publicly approved state-separator-v2 prompt and hidden QA not supplied to model.
- External wrapper start 2026-10-10T17:16:17Z, finish 17:17:18Z; real receipt start 17:16:18.622275Z, worker elapsed 59.187 s. Only canonical_tag.py modified; model_invocations_min=1; exact token count UNKNOWN.
- Real Worker SUCCEEDED exit0, independently verified 3/3 public tests and 12/12 hidden tests. Separate later Worker verify returned PASS, unchanged original receipt. Model code SHA256 b2ec92fed514a5e0e37aeca31155fe0d04cdfde70a3d46fafeeb9a09b0ef1ccb.
- Exact quarantined copy: docs/implementation/office-v2/phase2/quarantined-agent-sources-2026-10-10/parallel-mac-tag-20261010.py. This code is BYTE-IDENTICAL to an earlier independently generated quarantined source canonical_tag.py; this is a new successful model RUN, not a novel algorithm or production code change.
- Receipt selfhash 34affcc60ecd9754eed79a00dbdb4371fe437660212650daa0f99b7ddf0fcdc7; raw original file SHA256 60e1f9fa016418e882d874dc9d483ab81df5ab5760318e8a2d1db7936f6c7a23. Original logs, task envelope, source history, kernel birth pins and checkpoint stay on Mac; selfhash does not provide externally signed attestation.

**Transparent failed predecessor:** Mac Task p0-diverse-run-mac-speed-merge-20261010-a refused BEFORE any model call because macOS system Python had no psutil (PSUTIL_REQUIRED_NO_FALLBACK_TO_UNPINNED_PS). The original RUNNING journal was preserved, never replayed. A DIFFERENT newly admitted task -b using preexisting Aider venv succeeded on merge-windows in 64.084 seconds with QA PASS. The current Task -c is a separate fresh task run concurrently with Windows merge.

**True different-host overlap:** Windows Qwen9B Task p0-diverse-run-win-speed-merge-20261010-c wrapper 17:16:08.296Z–17:17:03.983Z, duration 54.985 s, exact source SHA e625ea816531000df82d15144f3155ebd59a868a2dd89c81c1f254115bafb2b9, independent 3+12 QA PASS. Mac and Windows model workers overlapped about 46.98 s. First start–last end ~69.70 s; worker elapsed sum 114.172 s. Do not infer general p50/p95 or automatic provider coordination from one paired sample.

Protected-PR source gate scripts/vf_office_v2_p0_parallel_mac_model_gate.py pins exact model output SHA, replays 3+12 real synthetic tests independently with no model or network effect, and proves deliberately broken seed fails. All source paths are quarantined; no native agent Git credential.

**Not authorized/proven:** source is not a live runtime module; no autonomous PR push/merge, canonical #604 provider lease, dedicated OS credential owner, globally exactly-once, automatic recovery, business/Instagram/CAD/printer effect or additional paid inference. #612 and #604 remain OPEN/P0 PARTIAL.
