# CP057 - native Windows Calculator acceptance packet (2026-10-18)

**Gate: `RED_UNVERIFIED` (unchanged).** One real, bounded Windows Calculator
run reported `PASS_NATIVE_UIA_CALCULATOR_42_ONLY` on PC Chris; it does **not**
complete independent receipt QA, a repeat run, or acceptance promotion. This
native PowerShell/UIA result is **not** a Cua Driver 0.34.0 acceptance pass and
grants no general computer-use authority. Source of record:
[#602](https://github.com/nocturney/velvetos-core/issues/602);
coordination: [#612](https://github.com/nocturney/velvetos-core/issues/612).

The CP057 attempt numbers below refer to the owner-authorized native one-shot
series on 2026-10-18, **not** the three earlier Cua Driver Calculator attempts
documented in #602 (2026-10-08). The 2026-10-14 pilot preflight refused while
the user was active and performed zero UI steps; it is not numbered as a
successful Calculator run.

## Attempts 1-8 (PC Chris)

| Attempt | Evidence and result | Failure explanation / progress |
| --- | --- | --- |
| **1**, 13:02 IDT | [#602 receipt](https://github.com/nocturney/velvetos-core/issues/602#issuecomment-6248545046): `FAIL_CLOSED_REAL_APP`, exit 2, no Calculator launch or UI steps. | Windows PowerShell 5.1 `Set-StrictMode`: an empty `Calcs` pipeline became `$null`; `$prior.Count` threw `PropertyNotFoundException`. Fixed via `@(...)` in [#763](https://github.com/nocturney/velvetos-core/pull/763). |
| **2**, 13:23 IDT | [#602 receipt](https://github.com/nocturney/velvetos-core/issues/602#issuecomment-6248719930): `FAIL_CLOSED_REAL_APP`, exit 2; launched and closed Calculator, zero UI steps. | First `CalculatorResults` read was empty after binding the outer `ApplicationFrameHost`; exact refusal was absent from this receipt. A missing content-ready wait was a **hypothesis**, not independently established as the sole cause. |
| **3**, about 13:45 IDT | [#602 receipt](https://github.com/nocturney/velvetos-core/issues/602#issuecomment-6248875426): `CALCULATOR_ELEMENT_UNAVAILABLE_CalculatorResults`, exit 2, zero UI steps. | Even with the bounded 10-second poll, `CalculatorResults` was not found under the outer UWP frame. Needed a content-window binding. |
| **4**, after [#772](https://github.com/nocturney/velvetos-core/pull/772) | [#602 receipt](https://github.com/nocturney/velvetos-core/issues/602#issuecomment-6249007457): `CALCULATOR_CONTENT_WINDOW_UNAVAILABLE`, exit 2, zero UI steps, `calc_closed=false`. | The selection matched a shared `ApplicationFrameHost` showing Settings, not the Calculator-owned content. The following fix constrained selection/cleanup to this attempt's Calculator process. |
| **5**, 15:04 IDT | [#602 receipt and read-only probes](https://github.com/nocturney/velvetos-core/issues/602#issuecomment-6249714629): `CALCULATOR_CONTENT_WINDOW_UNAVAILABLE`, exit 2, zero UI steps; cleanup succeeded. | The CalculatorApp `Windows.UI.Core.CoreWindow` was **top-level**, not an `ApplicationFrameWindow` child on that build. An `EnumWindows`/owned-process binding was added. |
| **6**, 15:23 IDT | [#602 receipt and probes](https://github.com/nocturney/velvetos-core/issues/602#issuecomment-6249903313): `CALCULATOR_ELEMENT_UNAVAILABLE_CalculatorResults`, exit 2, zero UI steps. | Owned top-level CoreWindow binding now worked; read-only probes observed **23/23 suspended** CalculatorApp threads and DWM cloak value 2, consistent with Windows PLM. [#786](https://github.com/nocturney/velvetos-core/pull/786) added a fail-closed PLM diagnostic, not a Windows PLM repair. |
| **7**, 16:17:57 IDT | [#602 receipt](https://github.com/nocturney/velvetos-core/issues/602#issuecomment-6250391790): `NOT_INTERACTIVE_LIMITED_USER`, followed by controller `CHILD_RECEIPT_IDENTITY_MISMATCH`, no Calculator launch/UI steps. | Console logon moved to **session 2** after sign-out/in; Child, `Calcs` and Controller hardcoded **session 1**. [#794](https://github.com/nocturney/velvetos-core/pull/794), merged as [`4593b8a1`](https://github.com/nocturney/velvetos-core/commit/4593b8a1), resolves and cross-checks the active console session; idle gate is 120 s. |
| **8**, 16:49:30 IDT | [#602 receipt](https://github.com/nocturney/velvetos-core/issues/602#issuecomment-6250697930): **`PASS_NATIVE_UIA_CALCULATOR_42_ONLY`**, exit 0, real fresh display readback `Display is 42`. | First run of the post-#794 pin. No retry was made. **Evidence of one successful bounded native attempt, not `ACCEPTED`.** |

## Attempt 8 - exact receipt and scope

- Host: **CHRIS**, 2026-10-18 **16:49:30 IDT**; source main after
  [#794 merge `4593b8a1`](https://github.com/nocturney/velvetos-core/commit/4593b8a1).
  Script `calc.ps1` SHA-256:
  `2f70a3c26fe3cd8b75f06e60a6d1c220a41a979aeaffa97f6547177256e18eed`;
  it matched `cp057/PIN.json` at execution time.
- Receipt: `receipt-36abe219c4cf4995b8ce95078e568ee3.json`;
  **receipt SHA-256**:
  `0E0AE55B1EC00EE26A116BE172EDA17E3C7A917FFBA4F3102C73BDBE4DA6BB5C`.
  Canonical report: [#602 comment 6250697930](https://github.com/nocturney/velvetos-core/issues/602#issuecomment-6250697930).
  This document quotes the reported hash; it does not independently hash the
  off-repository local receipt.
- Preflight: interactive, non-SYSTEM and non-elevated, `session=2`,
  `console_session=2`, about 3000 s idle (120 s gate); no Calculator process
  or suspended UWP thread before the run.
- Fresh native UIA readings: `first_result="Display is 0"`, then
  `num6=6`, `multiply=6`, `num7=7`, `equal=42`,
  `last_result="Display is 42"`. Window host `ApplicationFrameHost`,
  bound process `CalculatorApp`, `bound_via=frame_child`, title `Calculator`.
- Reported cleanup: `calc_created=true`, `calc_closed=true`,
  `suspended_threads=0`, `model_called=false`,
  controller `TASK_REMOVED=true`; no Calculator process/CP057 task/pending file
  left, no C: write reported. These remain **report claims** pending receipt QA.

## Requirements to change `RED_UNVERIFIED` to `ACCEPTED`

- [x] One source-pinned, bounded, read-after-each-action native Calculator
  attempt with explicit `42` readback and hashed receipt **reported** on #602.
- [ ] **Independent receipt QA**: obtain actual receipt bytes and recompute the
  SHA-256; compare `source_sha256` with the pinned file; verify
  identity/console/idle, Calculator-only window ownership, every UI step and
  fresh final read, exit code, refusals (if any), teardown, and lack of
  unrelated GUI effects. Publish a separate signed-off QA result tied to
  specific bytes and #602. A comment alone is not cryptographic verification.
- [ ] **Second separately admitted native run** with the same safety boundaries
  and a *new* nonce/receipt/hash; independently verify a second final `42`
  readback and teardown. Stop on any new failure, mismatch, or scope deviation;
  do not silently reclassify the first success.
- [ ] **Independent comparison and scoped owner decision** on both receipts,
  including the continuing difference between a native UIA Calculator result
  and the earlier Cua 0.34.0 Driver failure. No broader Cua/production admission
  follows from these two runs.
- [ ] **Separate, reviewed status-change PR only after those gates**: in
  `packages/vfharness/devtools/pilots/cua/cp057/PIN.json`, change the single
  `acceptance` field from `RED_UNVERIFIED` to `ACCEPTED`; update `note` with
  the exact two receipt IDs/hashes, QA verdict and decision links. Keep
  `runtimeAuthority=false` and `activationAllowed=false`; do **not** rotate
  `sha256`/`supersedes_sha256` without a source revision, and keep
  `algorithm` and `line_ending` unchanged. The current
  `scripts/vf_cp057_calc_strictmode.py` enforces `RED_UNVERIFIED` and will
  need a separately reviewed acceptance-contract change at that future time.
  This PR does **not** make any of these changes.

## Next in the recorded roadmap (not a new authorization)

[Office v2 NEXT.md](../../../../../../docs/office-v2/NEXT.md) is a dated
**2026-10-18 snapshot** written before attempt 8; its CP057 attempt-6 row
should not supersede #602's newer receipt. It defines **no CP058 milestone**.
The explicit surrounding work remains **CrewAI E1-E7** under
[#612](https://github.com/nocturney/velvetos-core/issues/612), the
read-only Office board's separately reviewed event-trigger work, and
**CP083 security evidence** under [#604](https://github.com/nocturney/velvetos-core/issues/604)
(which remains SECURITY RED). No operator action, machine run, activation,
or acceptance promotion is authorized by this documentation packet.
