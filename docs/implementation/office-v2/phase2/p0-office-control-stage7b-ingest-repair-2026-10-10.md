# Office Control Plane — Stage 7B dynamic learning-candidate ingestion failure (2026-10-10)

## Live failure, bounded owner scope

Scheduled [Office Control Plane run #38036479932](https://github.com/nocturney/velvetos-core/actions/runs/38036479932) completed its Living Studio, watchdog, memory hygiene, gaps, handoff and sensor steps successfully, but **failed during "Learning candidates from failed main runs"** after `vf_learning.py ingest-ci` appended candidates:

```text
OK ingest-ci workflows_failed=5 candidates_written=3 window_days=7
FAIL Stage 7B acceptance receipt is not reproducible
```

That is a **repeatability-contract error after a legitimate learning-candidate mutation**, not evidence that workers, customer actions, or the Control API stopped. The Stage 7B acceptance receipt was captured as a historical observation (frozen candidate snapshot **4 accepted**, revised Oct 5) while the live `packages/vfharness/state/learning-candidates/*.json` set is intentionally mutable and status/evidence may change after each scheduled CI ingest.

## Root cause and repair

`scripts/check-learning-lifecycle.py` previously ran `generate-stage7b-memory-learning-lifecycle.py` on the *currently mutated* candidate store and required the whole regenerated JSON to be **byte-identical** to the *frozen* acceptance receipt. Any added candidate or changed lifecycle status updated `candidate_state.count/status_counts` and caused a false failure, blocking the later protected machine-writer persistence.

The repaired check:
1. Still checks **every live candidate** for schema, unique identity, status, evidence, confidence, valid supersedes target and explicit accepted/promoted policy.
2. Pins Stage 7B's **historical** `candidate_state` exactly (`count=4`, `accepted=4`, `automatic_promotion=false`) and verifies *every other byte* of regenerated static acceptance against the original historical receipt after replacing only the two dynamic count/status fields via the bounded `candidate_state` projection.
3. Independently verifies the regenerated *live* candidate count and status counts against candidates already validated on disk; rejects malformed counts/types, altered paths, extra fields and any automatic promotion.
4. Runs **17 offline positive/adversarial controls** including legitimate new/rejected/promoted candidates and refusals for historical rewrites, forged static acceptance, policy drift, invalid dynamic schema/count, authority drift and mismatch with validated records.
5. Retains the original Stage 7B report **unchanged** and does not regenerate it as a substitute for acceptance.

In parallel, `scripts/vf_learning.py` now reads/writes explicit UTF-8 across Windows/macOS/Linux (instead of Windows process-default CP1252); its selftest actually persists a workflow name containing en dash and Hebrew UTF-8 bytes and verifies raw-byte roundtrip, idempotency and preserved status.

## Actual independent regression readback

On Chris Windows, a clean LF/full-history checkout at `main 889545fd2d767f82be8500fd25880f2dc41e1812` was used to replay *read-only GitHub Actions metadata* from the last 7 days into its own isolated candidate directory. **Before repair**, CI ingestion created a new candidate / updated one and the receipt comparison failed; on Windows the prior `write_text()` additionally wrote invalid legacy bytes. **After repair** using the same run set:

- `ingest-ci`: 2 failed workflows, 2 candidate files changed; current live set **5** (`accepted=4, candidate=1`).
- `check-learning-lifecycle.py`: **PASS**, 17/17 projection adversarial controls.
- Frozen Stage 7B report SHA-256 **identical before/after**.
- Re-ingesting identical runs wrote **0** candidates, raw file hashes identical.
- A synthetic invalid `status=promoted` candidate without `promote_to` was correctly rejected, original file bytes restored, lifecycle verifier PASS.
- `vf_learning.py selftest`: deterministic/idempotent/status preservation and raw UTF-8 roundtrip PASS.

All tests used isolated, disposable checkout/candidate files; no Office production writes, real task retries, paid APIs, scheduler changes or credentials. The live scheduled workflow is **not** yet confirmed green by these local checks alone. Mandatory next evidence: protected PR exact-head `check-all` PASS, merged-main full sensors, then actual Office Control Plane run through ingestion and machine-writer path (without broadening its authorization).

## Reproduce

```sh
python scripts/vf_learning.py selftest
python scripts/check-learning-lifecycle.py --selftest
python scripts/check-learning-lifecycle.py
```

For the dynamic-state test, use a disposable checkout with complete Git history (the generator's pinned `git show 7c1725f...` requires the historical commit), and inject **only synthetic or metadata-derived learning candidates** before invoking `check-learning-lifecycle.py`. A shallow checkout without the Stage7B baseline is not evidence that the lifecycle test has failed on substantive grounds; fetch the required Git history or use the CI full-history checkout.
