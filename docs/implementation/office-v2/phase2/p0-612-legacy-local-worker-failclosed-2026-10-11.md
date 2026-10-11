# Office 2.0 #612 — Legacy v1 Worker direct-model/QA admission fail-closed

**2026-10-11. LAB / no new execution authority.** This closes the unisolated direct entrypoint left by the newer Diverse Worker guard in PR #683, without claiming that either connected host is now a valid low-trust executor.

## Demonstrated risk before this change

The old `scripts/vf_office_v2_p0_local_model_worker.py` originally used `subprocess.Popen` for local Aider and `qa_fresh()` to execute `slug.py` and blind tests in an ordinary local Git clone. `run` persisted a RUNNING journal before launching; `verify` loaded receipt inputs then independently replayed generated-source QA. The old `selftest` also locally executed fixed replacement Python source, which was not a model call but still ran Python without a separate guest.

Chris's Remote Desktop Commander runs as `NT AUTHORITY\\SYSTEM` in Session 0. Mac's Remote Desktop Commander runs as user `chris`/UID501. Neither user or PATH/temp separation provides an OS-isolated credential-free generated-code runtime. The historical v1 positive model receipts and independent QA remain historical evidence, NOT authorization for fresh privileged replay.

## Narrow implementation

Add code-locked constant `P0_GENERATED_SOURCE_OS_ISOLATION_NOT_ADMITTED` and unconditional rejection via `require_isolated_generated_code_executor()` as the very first operation in **`run`, `check_run`, and `qa_fresh`**. The `verify` CLI also refuses *before reading* envelope or receipt paths. No task-, model-, environment-, system-user-, receipt- or caller-controlled opt-in exists. Both direct CLI commands `run` and `verify` return `FAIL_CLOSED`, exit 2 with the exact shared guard reason, before spawning Aider, running Python QA, or writing journals and receipts.

Retain existing offline fixture preflight, policy/hash/dirty-worktree negatives, continuity checks and the historical proof verification in `vf_office_v2_p0_local_model_evidence.py`. The historical birth-pin receipt's original `worker_git_commit` is `030eccbe98e5165115faa37253ad82208fc59614` with SHA-256 `7b4cb176c9c66351f9658c08589f45ec94d50c2a8b6450fe8e5cb1d8f09d86f7`. Its EXACT historical bytes are now archived as a non-executable `.txt` source witness at `p0-612-historical-v1-worker-source-030eccbe.txt`, preserved via `-text !eol`. The existing independent birth-pin evidence verifier reads this immutable archive, **not** the new guarded current Worker. Neither the historical model receipts nor their claimed QA results have been rewritten or relabeled. The v1 `selftest` removes the former two local generated-source QA replays and instead proves that all three direct function paths reject *even missing inputs* before access, and that spoofing `VF_OFFICE_GENERATED_EXECUTION_ISOLATED=true` does not bypass the code lock. It continues to run only trusted selftest logic, git fixture setup and pure contract tests; no local model calls or generated candidate Python.

Pin the exact modified v1 source SHA-256 in the full Office contracts and add actual CLI regression checks for `run` and `verify`. The initial changed worker source SHA-256 is `eff2a82e37d40fb90c1746ddcc3adf4e7be28ddfc0f1677106e9796b47275161`. Source-locked static `selftest` expected **21/21** including four new refusals; historical Task Envelope records are not rewritten.

## Verification gates and limitations

- Mac on a clean new LAB checkout: **21/21** `selftest`, actual `run` and `verify` **exit 2 / FAIL_CLOSED** with expected guard reason, all before a candidate/model launch. No changed task data.
- Required before merge: fresh exact-PR-head native Chris Windows with unchanged system Git `core.autocrlf=true`, same local 21/21, both CLI denials; independent Mac Office contracts; protected GitHub PR CI 120/120, then exact-head merge and postmerge 118/118.
- **Not a new OS sandbox.** Neither this nor the Diverse Worker can execute untrusted locally. Hosted Docker #685/#688 demonstrated narrow synthetic isolation/trust-boundary negatives for already known sources, not arbitrary unknown model code.
- No Codex CLI, paid inference, new scheduler, production Github writer, credential, actual certificate, host OS setting, social media, customer, printer, CAD or unrelated project operations. #604 is still the sole authority for actual credential custody and fleet fencing. #612 remains P0 PARTIAL.

