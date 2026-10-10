# Office 2.0 / #612 — Fail-closed local generated-code admission, 2026-10-10

**Status: DIRECT_LOCAL_MODEL_AND_GENERATED_SOURCE_QA_BLOCKED; P0 STILL PARTIAL.**

## Why this safety gate exists

The fresh two-host Qwen/Aider experiment in [PR #682](https://github.com/nocturney/velvetos-core/pull/682) proved that model-generated Python was subjected to native independent QA from Chris Windows Remote Desktop Commander, whose command process is **NT AUTHORITY\\SYSTEM, Session 0**. The independent synthetic QA is a functional correctness checker, **not** an OS privilege boundary. MacMiniOffice.local ran as a regular but admin-capable existing user `chris`, UID501, not a demonstrated isolated account. The existing `vf_office_v2_p0_diverse_local_worker.py` created cloned code worktrees, scrubbed environment variables and pinned process-birth identities, but none of those safeguards creates a trustworthy privilege boundary for executing generated Python.

Separately, #604's real same-UID Sink-key impersonation negative [PR #675](https://github.com/nocturney/velvetos-core/pull/675) and sandbox hardlink-alias bypass [PR #676](https://github.com/nocturney/velvetos-core/pull/676) mean filesystem mode 0600, 0700 subdirectories and a pathname-based macOS Seatbelt deny are **not verified substitutes** for a separate trust principal. Neither Windows USER Session 1 nor Windows Sandbox/WSL is established as a safe replacement simply because a feature or UI automation library exists.

## Code-locked scope and exact effect

The previously committed direct local Worker source SHA256 was `9ed3f0b495008c44249867c87b664aa7b75178049b1c7d53f37d557bd12cfafb`, preserved in the dated #682 **historical experiment receipt**, which must not be falsified by retroactive rewriting. This change creates a new source SHA `5a4fadfca6f8e33724f851b5723f9952a4676013a290a7ed46fa19db3b953cbb`.

The new `require_isolated_generated_code_executor()` has an intentionally unconditional **Refused(`P0_GENERATED_SOURCE_OS_ISOLATION_NOT_ADMITTED`)** result, invoked before any model process, generated-code subprocess, candidate clone/journal or source replay in three direct entrypoints:

- `admit`: refuses creation of new run envelopes, even though preparing an envelope itself does not request paid models
- `run / execute`: refuses before `Popen`, after no effect, for any argument including an existing envelope
- `independent_qa`: refuses generated-code execution used by `verify_receipt` and `audit_failed_qa`, including historical attempts; already completed offline audit records remain available through `verify-failed-audit` and pure evidence validators

There is **no** environment, CLI, JSON, user, host or unsigned token bypass. Future re-admission must be a separate protected source change reviewed with #604/#612: independently established OS-level guest/dedicated unprivileged identity, executable+input hashing, no host/customer credentials/secrets/Git write token, bounded CPU/memory/IO/network, kill/reap, independently reproducible QA, immutable receipt, and replay/UNKNOWN semantics. An ephemeral GitHub-hosted runner with minimal permissions is a candidate for **synthetic-code QA only**, not proven to isolate the Git credential-owning Sink or make GitHub and etcd atomic. No install or new scheduler is authorized by this note.

## Verified negatives / regression boundary

`python3 -B scripts/vf_office_v2_p0_diverse_local_worker.py selftest` now has **48/48 model-free tests**, including direct `admit`, `run`, `independent_qa` and spoofed environment denial, while preserving the 44 previous safety checks. A real command invocation `run --envelope /DOES-NOT-EXIST/envelope.json --receipt /DOES-NOT-EXIST/receipt.json` on Mac returned `FAIL_CLOSED`, exact isolation-denial reason, and **exit 2 before reading path or starting a model**. Independent Windows behavior and protected GitHub CI must be verified on this exact code head prior to merge.

Office contracts pin the replacement source byte digest and 48-test result. The historical two-host #682 report remains a negative **real observation**, not a recommendation to repeat model execution. The closure **does not** grant new executor authority, prove Git credential custody, fix other legacy worker entrypoints, add a global OS sandbox, promote production, or authorize model/generated-code runs in SYSTEM/Mac-admin contexts. Critical capability remains P0 **RED** until a verified isolated ready-made executor or controlled VM/guest boundary passes a new admission gate.

No model or new paid API calls, no system privilege, OS account, firewall, Keychain, WSL, service, UI, scheduler, customer, publication, printer or production file mutation was used to implement this change.
