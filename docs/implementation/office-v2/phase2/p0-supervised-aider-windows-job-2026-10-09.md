# Office 2.0 P0: real Windows Job-supervised Aider completion and interruption (2026-10-09)

Canonical owner: https://github.com/nocturney/velvetos-core/issues/612 . LAB only. No production writer, customer/Instagram/printer effect, paid model API, Codex CLI or new fleet scheduler (#604 exclusively owns placement).

## Source and isolation

The exact executed manual Windows supervisor is scripts/vf_office_v2_p0_supervised_aider_lab.py, Git blob 605ca7d82a8b461d8a34043305bad8c671561ea0, byte-comparison matched the authorized Windows source via git hash-object. It drives the accepted existing local Aider task-envelope Worker from source pin 030eccbe98e5165115faa37253ad82208fc59614; Aider 0.86.2, Ollama qwen3.5:9b on loopback 11555, no extra API spend, one attempt, bounded 170s and explicit REQUIRE_OS_BIRTH_BEFORE_QA_V1 mode.

Two fresh, completely DISTINCT Git fixture repos, task IDs, base SHAs, source/worktree owners and receipt paths were prepared under Windows AgentEnvelopeLab/win-native-job-model-20261009. The original interrupted task was NEVER restarted, including after its RUNNING journal was retained. The Windows native Job Object was unnamed, created exclusively for its new helper, set KILL_ON_JOB_CLOSE, assigned helper BEFORE releasing the helper to launch Worker and Aider, checked all three as members by native handles and kernel birth time, then either closed the job during the attempt or waited for successful independent QA.

## Actual real local-model trials

| Mode | Isolated task suffix | Git baseline | Observed owned helper / worker / Aider | Native supervisor self-hash |
|---|---|---|---|---|
| Interrupt | gpt6-interrupt-20261009-c | 3b5e11d277fba0a085befa432bd0bebacd17dbd3 | 60132 / 53808 / 46500 | 7546dc7ef85808b578ef61f15ebe499a34abadbf8ecc2e13f22f0ff48309c309 |
| Success | gpt6-success-20261009-d | 1a65f37c897e28df7b2855fe624c64d454772bd1 | 57316 / 47608 / 46304 | 02b41e9e86bb7dc1e2413f4bd235bbbc71b3095030daf1093b9da41d617d336b |

INTERRUPT: after the observed Job membership and kernel creation-time checks, closing exactly the sole owned Job handle signaled all three original process handles. Subsequent Windows CIM readback found all three PIDs absent. Original receipt.json.running persisted, final receipt.json was ABSENT, source worktree remained clean, and an attempted same-envelope run returned DUPLICATE_OR_UNKNOWN_OUTCOME_NO_RETRY. Existing UNKNOWN reconciler independently returned UNKNOWN_RUNNING_JOURNAL_NO_BLIND_RETRY with retry=false. The original task remains quarantined. Historical original kernel pin file bytes SHA256: abba0e79ae2c9f9a290c6d1cb12e5b6ad396d1dba5e85d225c1a6a1dc7304b05, RUNNING journal raw file SHA256: 86155bfeabbe717c5c1441a47bce449a1af1c563dc284a80308d9160f401023c.

SUCCESS: entirely NEW task/source Git base, real Qwen Aider model invocation, changed exactly slug.py, completed in 30.172s. Independent fresh Git replay passed 3 visible unittest and 12 hidden regression cases. Separate OS process ran canonical Worker verify on the original envelope/receipt and returned status=PASS, checking source SHA, model log hashes, continuity checkpoint, kernel pin file and actual QA. Original worker receipt SHA256 self-hash: 4424b020ead05e6d30bd4467f105792f98fc37f0aca039144f0413432a5eec02; success kernel pin raw file SHA256 dec8e1eeb74c3d7d16f1ca7fbaad9a6b800c45ed04fa137ba0719e4accc6ba81. All three owned post-run old PIDs were absent by readback.

## CI and negative controls

The checked-in JSON contains the exact two task envelopes, original job process receipts and raw historical kernel-pin file bytes encoded as base64 with independently recorded SHA256 hashes. It also retains the old journal bytes and the full successful model-worker receipt. No credentials or customer data. The portable pure-stdlib+canonical-kernel-identity verifier scripts/vf_office_v2_p0_supervised_aider_evidence.py validates immutable bindings, canonical self-hashes, native process lineage, born-before ordering, exact-pinned model, original UNKNOWN journal, positive independent QA, and explicit fail-closed authority booleans. It runs 19 counterexample modifications, some re-sealed, rejecting forged success/QA/ownership/orphan/paid/production/retry claims. The existing Office contracts CI invokes only this offline verifier; it NEVER starts the manual supervisor, model, Windows processes or a scheduler. The source receipt self-hashes are NOT independent digital signatures and Linux CI cannot re-observe historical Windows process handles.

## Boundary and P0 exit debt

This proves native Job inheritance and kill-on-close for the THREE exact owned and observed real-model processes, not that arbitrary breakaway, detached or escaped descendants cannot survive (Mac negative #636 remains material), nor a Windows OS/network sandbox, restart of the old unknown task, zero-touch failover, reboot recovery, cross-host lease or production writer. p50/p95 needs separate repeated task-family measurements. Do not activate manual code as service, create a second scheduler, claim broad orphan closure or bypass protected PR CI. Next owner step: new explicit unique-envelope admission/reconciliation after demonstrably bounded job-tree postcondition, plus #604 placement acceptance; old UNKNOWN remains NEVER blindly retryable.
