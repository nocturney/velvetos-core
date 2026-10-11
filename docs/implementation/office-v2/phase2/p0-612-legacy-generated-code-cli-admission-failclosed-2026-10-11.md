# Office #612 — block legacy local generated-source execution; preserve original source bytes

**2026-10-11, LAB only, P0 NOT GREEN.** Extends the existing post-PR683 diverse-worker `P0_GENERATED_SOURCE_OS_ISOLATION_NOT_ADMITTED` policy to the original v1 Local Model Worker and its separate Windows Job Object supervised entrypoint. Chris Remote Desktop Commander is SYSTEM Session 0, MacMiniOffice DCC is UID501, neither has an admitted low-trust generated-code OS executor. A Windows Job Object bounds process lifetime, not runtime/file-system/network authority.

## New live entrypoint denial

The current scripts/vf_office_v2_p0_local_model_worker.py now unconditionally refuses run and verify immediately after argument parsing, prior to envelope/receipt reads, writes/journals, network/model preflight, Aider Popen or fresh code QA. Defense in depth also blocks direct calls to `run`, `check_run`, and `qa_fresh` before Python subprocess execution. Existing selftest retains all 19 offline fixture/path/identity cases but deliberately stops executing even synthetic known-good and known-bad generated Python: now both QA attempts MUST raise the same denial. Return codes are exactly 2 and reason `P0_GENERATED_SOURCE_OS_ISOLATION_NOT_ADMITTED`. Source SHA256: `299dbfba2909790d66dba261ffc98bf308956f687136145e475473a2e439bbf2`.

The current scripts/vf_office_v2_p0_supervised_aider_lab.py now unconditionally refuses both run and _helper immediately after CLI parsing, plus directly imported `controller`, `_helper`, and `check_inputs` methods. Existing 20 offline path/binary/trust pin tests remain operable. A Job object alone cannot admit locally executed generated code. Source SHA256: `7d104cb55a7d2d87f2022f65bb4ff15c0e5aca6eb210b6bd4081df4cfd641586`.

## Historical evidence truth retention

Two original sources are copied byte-for-byte to non-executable `.py.txt` paths under `quarantined-worker-sources-2026-10-11/`: Local Model Worker original SHA256 `7b4cb176c9c66351f9658c08589f45ec94d50c2a8b6450fe8e5cb1d8f09d86f7`; Windows supervisor original SHA256 `505dc727d8dc539ebf4b2c43e309ec6e7723393aff0899938efdea595e85d461`. The archive is protected by `.gitattributes -text !eol` to prevent Windows checkout from modifying evidence. These are historical evidence snapshots, NOT runnable alternative worker entrypoints.

Historical real Qwen/Aider receipts and `vf_office_v2_p0_live_birth_evidence.py` deliberately compare against the archived ORIGINAL Worker path, never re-label current guarded Worker as a historical execution source. Supervised Job's existing pinned old SHA and old synthetic Git commit remain historical record, not admitted worker. No receipt seal, expected source SHA or historical journal is rewritten.

## Independent acceptance

Mac local initial check: Worker selftest 19/19 PASS, supervisor selftest 20/20 PASS; CLI worker run and verify and supervisor run and _helper returned FAIL_CLOSED reason P0_GENERATED_SOURCE_OS_ISOLATION_NOT_ADMITTED, code 2. No model/Aider or generated-source QA executed. New Office contracts pin both new facades and both original archives and assert 4 CLI denials. Independent native Chris Windows fresh exact-head tests, Mac clean recheck, protected GitHub PR CI and normal expected-head merge plus postmerge full CI remain required.

**Nonclaims:** CLI-scoped disallow protects the named code paths, not untrusted host scripts outside these entrypoints, global OS/Docker trust, all legacy experimental scripts, or arbitrary processes. The already approved hosted Docker negative/source QA still uses public SHA-pinned historical files in a separate low-permission GitHub runner. #604 privileged Git Sink custody/lease/epoch and #612 autonomous two-host model-generated PR acceptance stay RED. No Codex CLI, paid model API, changed system config, production writer, email, Instagram, printer, CAD or customer effect.
