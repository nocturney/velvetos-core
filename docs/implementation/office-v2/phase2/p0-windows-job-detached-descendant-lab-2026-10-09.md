# P0 Windows native Job Object detached-descendant proof — 2026-10-09

Issue: https://github.com/nocturney/velvetos-core/issues/612
Scope: synthetic, bounded, owner-only Windows process experiment; **not** Office runtime/scheduler admission.

## Experiment

- Authorized host: Chris (Windows). Python direct interpreter: `C:\Python311\python.exe`.
- Source base: `main` `0984e19edec023553f8e47a8eaf73812742e5fe7`; exclusive test branch `office-v2/p0-detached-job-descendant-gpt6-20261009`.
- Executed source checkpoint: `32610da5846ae0dfab0fa5f0b56936adf2a80157`; script Git blob `56d7d4ab6294c3900c14adcd2814a0bf1043f2e4`; Windows source-file SHA256 `82573feb68c95af73609fa3e3bc2e9cf443c00ceff0469695056826ee3e543a0`.
- Script: `scripts/vf_office_v2_p0_detached_descendant_lab.py`. It reuses the existing Win32 Job API adapter, makes a new unnamed `KILL_ON_JOB_CLOSE` Job, and assigns a temporary owner **before** allowing its child to spawn.
- Owner creates a real detached grandchild with `CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS`, not a simple inherited-console child. The controller checks both OS handles with native `IsProcessInJob`, observes them alive, closes **only its new owned Job handle**, and waits for both to exit.
- Original raw receipt: `p0-windows-job-detached-descendant-lab-2026-10-09.json`; receipt self-hash `13272458fa66476b71a4a025e197fa6888dde168adc16612bc23089b0667737f` (self-hash, not an external digital signature).

## Actual readback

- Owner PID `50368`, kernel birth `1791569961539676` microseconds; detached descendant PID `16376`, birth `1791569961595445` microseconds.
- Both were OS-verified Job members and alive before close; both completed the wait after owned Job closure. A subsequent independent Windows CIM PID readback returned no records for either PID.
- Bounded temporary fixture directory was removed; historical lab attempts and their UNKNOWN journals were not touched.
- Local pure admission/receipt selftests: **14/14 PASS** (one shape-only positive, twelve re-sealed false-safety negatives, one raw-hash tamper).
- Model invocations: **0**; cloud/API spend: **0**. No WSL, VM, scheduler, production endpoint, credentials, social, customer or printer action.

## Limits and interpretation

This verifies **one specific DETACHED_PROCESS grandchild inherited this specific Windows Job** and exited on close. It does not establish global process-tree/orphan absence, withstand arbitrary Job breakaway/elevation/injected code, certify a network sandbox, or grant automatic UNKNOWN recovery, host failover, scheduler placement, production authority, or repeatable p50/p95/resource metrics. The Mac detached-session escape demonstrated in PR #636 remains a separate negative case. Do **not** use this as a replacement for #604's fleet ownership or a production safety certification.

CI integration reruns only `selftest` and historical receipt `verify`, not `live`; the pinned historic receipt hash guards against an unreviewed re-seal.
