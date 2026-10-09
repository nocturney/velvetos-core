# P0 live Aider child OS-birth pin — optional LAB gate (2026-10-09)

Canonical owner #612. Depends on merged two-host native process birth identity proof [PR #634](https://github.com/nocturney/velvetos-core/pull/634).

## Code and safety

The existing model-aware local-only synthetic worker is unchanged by default. A NEW versioned opt-in string `kernel_birth_capture=REQUIRE_OS_BIRTH_BEFORE_QA_V1` may be placed by `vf_office_v2_p0_local_model_fixture.py --kernel-birth-pin` only in a unique `AgentEnvelopeLab` fixture. Worker preflight refuses invalid opt-in values. After an actual Aider subprocess is launched from the pre-pinned Aider binary and the fsynced `receipt.json.running` journal exists, it captures both worker and child OS kernel process birth identities and their real parent relation, writes the externally bound `kernel-pin.json` with create-exclusive semantics, and immediately re-reads both PIDs to guard reuse. The result is not a new Task Envelope schema, queue, scheduler or authority provider.

Any failed OS birth capture prevents a successful receipt even if the model later edits source successfully. An opt-in success must pass the existing independent 3+12 QA and an additional **pure pin readback** that reconstructs the original RUNNING journal from the receipt started-at, verifies pin selfhash, source directory hash, task/envelope/host binding, creation-time data and parent/session relation. The journal remains on errors. No worker can auto-requeue. A previous killed worker lacking such birth pin cannot be retro-certified.

## Actual execution and independently verified evidence

The initial design gate has now been exercised with actual Aider 0.86.2 processes and local Ollama/Qwen on **both connected physical hosts**, pinned at exact PR code commit `030eccbe98e5165115faa37253ad82208fc59614` and worker source SHA-256 `7b4cb176c9c66351f9658c08589f45ec94d50c2a8b6450fe8e5cb1d8f09d86f7`. Both hosts passed 19/19 model-worker offline selftests. Existing P0 model-aware envelopes and fixture source hashes were retained; the new OS-birth capture is an explicit opt-in only.

Three different fresh, exclusive LAB Task Envelopes actually invoked locally pinned Aider+Qwen. Each edited exactly synthetic `slug.py`, passed independent fresh-clone **3 visible +12 hidden** regressions, produced an OS-birth `kernel-pin.json` during inference, and subsequently passed **separate-process `worker verify`**:

| Task | Host | Local model | Elapsed | Host-local Worker Receipt SHA-256 |
| --- | --- | --- | ---: | --- |
| `p0-mac-birth-live-20261009-a` | MacMiniOffice.local | Qwen3.5:4B | 46.494s | `f88f212815a7ff35295211dcfd5e0a26e9041b9c99bf5bd15c81f0e6bddd222f` |
| `p0-win-birth-live-20261009-a` | Chris Windows | Qwen3.5:9B | 33.062s | `b1a4ec3541a202946f1f62cd61d1192624dd96c1fa50852b9e0d2dfe7a7ef50d` |
| `p0-mac-birth-afterloss-20261009-c` | MacMiniOffice.local | Qwen3.5:4B | 44.400s | `0b479e0f73560238ae6a36de0798004d4db8935530fdd179125074703b9646d5` |

A separate uniquely owned Mac LAB `p0-mac-birth-kill-20261009-b` actually launched an Aider model-worker with the same opt-in. A native OS birth observer confirmed both expected worker and child as `SAME_KERNEL_INSTANCE_AT_SNAPSHOT` while active, with one possible POSIX-group member. The exact worker and child were force-terminated in this isolated experiment. A new native readback showed both historical PIDs absent and zero observed group members **at that instant**, not complete orphan exclusion. The original RUNNING journal SHA-256 `66c53c987b3ddd0e26359f486b9e1de861cb3a9df20d0fd70fb985606858e1a7` and kernel pin file SHA-256 `149ab11989e4c39db9c286e40820996b8d1c45da375a1d48d4f71d20c22bb845` survived unchanged. No original success receipt was produced; executing the original envelope a second time was explicitly **REFUSED** with `DUPLICATE_OR_UNKNOWN_OUTCOME_NO_RETRY` (exit 2). The third, freshly prepared Mac Task Envelope was started by an operator *after* reconciliation and independently verified; it did **not** resume or retry the unknown original task.

The canonical sanitized evidence JSON `docs/implementation/office-v2/phase2/p0-real-aider-kernel-birth-2026-10-09.json` contains exact model-worker receipt hashes, pinned source/revisions, native before/after OS snapshots, and limitations; host-local detailed Aider logs and original Worker Receipts remain outside Git. The new pure verifier `scripts/vf_office_v2_p0_live_birth_evidence.py` passed independently on **both Mac and Windows**, checking the three positive model receipt references and **11 malicious evidence mutations**. It is wired into the canonical Office v2 contracts sensor; it launches no LLM, reads no live OS processes, and schedules nothing in CI.

## What these results do NOT authorize

This is a **synthetic model-worker LAB milestone**, not autonomous crash restart, resumption of a failed model attempt, proof that every orphan descendant has exited, Windows Job Object isolation, cross-host failover, #604 host placement or task lease, OS/network sandbox, production writer authority, or statistical p50/p95. Mac/Windows used differently sized local models; exact token usage and full cost of the owner's existing machine were not recorded. A self-hashed receipt is an integrity check, **not an externally signed OS/process attestation**. No Codex CLI, new paid API, customer/social/printer effect or recurring automation was introduced. P0 remains PARTIAL. Next acceptance work belongs to the existing #612 gate and must coordinate scheduling and placement solely through #604.
