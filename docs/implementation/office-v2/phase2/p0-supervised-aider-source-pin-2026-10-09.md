# Office P0 manual Windows Aider supervisor — source/path fail-closed trust hardening (2026-10-09)

This is an incremental safety change to the existing #612 synthetic manual Windows Lab supervisor. It is NOT new scheduler, host selector, token/credential manager, task promotion authority, or a claim of automatic crash recovery. Preserve #604 fleet placement and the historic real successful #638 evidence unchanged.

## Discovered input-contract weakness

The exact live-proven supervisor source (historical Git blob 605ca7d82a8b461d8a34043305bad8c671561ea0) verified only the supplied Worker filename before using sys.path/import. A file with the correct basename could originate from an unapproved checkout, and its sibling dependency files could drift without the manual supervisor noticing. The original code also only checked a scratch-name prefix and fresh directory, not that the reporting path is inside the dedicated Job LAB.

These issues do not invalidate the already-observed #638 owned-job process outcome because that run passed exact-source readback against the original pinned Worker checkout. They DO block confidence in arbitrary FUTURE executions and are fixed here before further LAB promotion.

## New explicit gate, before any Python Worker import or process launch

- Worker root must be scripts/vf_office_v2_p0_local_model_worker.py directly beneath a named source Git checkout under AgentEnvelopeLab/kernel-birth-*/source.
- The Git checkout MUST have the exact approved SHA1 HEAD 030eccbe98e5165115faa37253ad82208fc59614 and no modified OR untracked paths (git status porcelain v1).
- Exact SHA-256 pins: Worker 7b4cb176c9c66351f9658c08589f45ec94d50c2a8b6450fe8e5cb1d8f09d86f7; kernel identity 2268091d9129eb504fc17ce7e7374367deb5ae23cb1327872796f353a16043ce; Project State continuity fba96dd7e1a398c393bf3c4237aed062d11369d62bf907a42f25810b04872ec2.
- Only fresh sibling scratch names job-model-* and new report names job-guard-*.json, both inside a unique immediate child of the dedicated D:/Velvet/Pilots/OfficeAccelerator/WindowsJobObjectLab. Symlink and existing-collision denial; manual reports are exclusive-create.
- Canonical model Task Envelope/Worker preflight, local qwen pin, allowlisted source, bounded timeout/attempts and zero API spend remain separately mandatory and unchanged.

## Model-free repeatable verification

Run python -B scripts/vf_office_v2_p0_supervised_aider_lab.py selftest on Windows, Mac or CI. It creates an OS-temp git repo ONLY (not a real model task), exercises 15 deterministic source/path negative and positive assertions, and reports status PASS_OFFLINE with model_invocations=0, native_job_objects_created=0, production_effects=0 and retries_authorized=0. Independently re-run the read-only gate on Chris against the EXISTING clean pinned Worker checkout and a non-existent allowed scratch/report: PINNED_REAL_WORKER_TRUST_CHAIN_PASS + SCOPED_SCRATCH_REPORT_PASS, without launching a model or creating those destination files. GitHub Office contracts CI invokes only this selftest.

## Limits and next acceptance

This hardens the manual lab launcher and creates no automated worker. The historical two actual Aider Job trials under merged PR #638 were executed using the previous source Git blob, not the new hardened blob. Before claiming the hardened producer can run real models safely, repeat a NEW unique disposable Task Envelope under this exact new source and require the same native three-member observation, independent Worker verify, 3/3 +12/12 QA, no leaked original UNKNOWN and protected CI. No arbitrary escaped-descendant closure, automatic retry/failover, distributed scheduler, production writer or operating-system sandbox has been demonstrated.
