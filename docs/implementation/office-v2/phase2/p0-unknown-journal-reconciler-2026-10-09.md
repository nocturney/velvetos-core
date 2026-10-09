# P0 local-model UNKNOWN journal reconciliation — read-only gate (2026-10-09)

Canonical owner: [Office Infrastructure Accelerator #612](https://github.com/nocturney/velvetos-core/issues/612). The separate [#604 fleet placement work](https://github.com/nocturney/velvetos-core/issues/604) is unchanged. This gate follows the actual live-Aider Task Envelope, forced SIGKILL and operator-only new-task proof in merged [PR #629](https://github.com/nocturney/velvetos-core/pull/629).

**What changed:** A pure stdlib read-only observer (scripts/vf_office_v2_p0_unknown_reconcile.py) reads the existing v1 LAB model Task Envelope, exact receipt path and the matching .running journal. No model invocation, code editing, scheduler call, Git operation, subprocess, external host process inspection, network call, auto retry, credentials or production effect. It never marks a claimed success independently verified. The existing Office contract CI runs 33 synthetic positive/negative acceptance cases in a disposable temp folder.

## Usage

Run on the actual machine where the original envelope and receipt paths are available:

~~~sh
python scripts/vf_office_v2_p0_unknown_reconcile.py selftest
python scripts/vf_office_v2_p0_unknown_reconcile.py inspect --envelope /path/to/envelope.json --receipt /path/to/receipt.json
~~~

The second command **only reads** the envelope/receipt and derives /path/to/receipt.json.running; it never touches the worker. File paths must be explicit, not discovered by walking a shared drive. JSON output carries status, task_id, envelope_sha256, host, reason codes, journal/receipt presence, owner_process_state, automatic_retry_allowed=false, verified_success=false and the next operator gate. It does not return raw prompts, model logs or secret contents. Malformed or unsafe input returns FAIL_CLOSED (exit 2).

| Disk evidence | Status | Action |
|---|---|---|
| No final receipt and no journal | NO_EVIDENCE_NOT_PROVEN_UNSTARTED | Operator review; absence is not proof the task never ran |
| RUNNING journal only | UNKNOWN_RUNNING_JOURNAL_NO_BLIND_RETRY | Preserve journal/partials; do not rerun original envelope |
| SUCCEEDED receipt only | SUCCESS_CLAIM_NEEDS_INDEPENDENT_WORKER_VERIFY | Independently run the existing model worker verify command on the same host |
| Non-success receipt only | NON_SUCCESS_RECEIPT_REVIEW_REQUIRED | Manual investigation; do not blindly retry |
| Journal plus final receipt | JOURNAL_RECEIPT_CONFLICT_REVIEW | Review ambiguous crash boundary |
| Mismatched/altered identity or receipt, unknown state, forbidden permissions | CONFLICT_OR_TAMPER_REFUSE or FAIL_CLOSED | Refuse release/retry and examine reason codes |

## Ownership, trust and scope

The existing v1 journal contains a task ID, host label, envelope SHA256, kind, start time and a NO_BLIND_RETRY rule, **but no trustworthy OS worker PID or process creation identity**. Therefore owner_process_state is always UNKNOWN_NOT_ATTESTED. The reconciler does not claim to see live Aider processes, prove a worker died, clean up orphaned descendants, or attest absent external effects. Process-owner proof requires a separate admitted observable contract; mere journal presence or absence cannot authorize a new worker.

Receipt SHA256 self-hashes detect accidental alteration, not a malicious re-seal. Resealed mismatches and false-success evidence are rejected when inconsistent, but a plausible SUCCEEDED remains **unverified** until the original vf_office_v2_p0_local_model_worker.py verify independently checks pinned Git source and allowed diff, Aider log hashes, continuity checkpoint and fresh-clone independent unit/hidden QA. The classifier never invokes that verification automatically and never authorizes retry/new_task/production.

The isolated offline selftest includes 33 cases: missing/partial/concurrent evidence; success claim only; failed receipts; re-sealed wrong task, host, base, branch, model and model digest; forged hidden QA success, bypassed model invocation, paid/production flags; changed receipt directory; fake retry/scheduler authority; bad envelope and journal states; wrong SHA; blocked Codex executor; symlink journal. Each inspect input is byte-for-byte unchanged after classification. Selftest may create temporary synthetic files solely in its own OS temp directory.

**Still open:** independently verified live-process ownership, PID reuse detection, observed orphan handling, operator-mediated safe reissue conditioned on proven ownership, real autonomous cross-host failover under #604 placement authority, repeated throughput/resource peaks, signed external evidence, and production promotion. This PR is a narrow read-only gate, not a new scheduler, agent runtime, authority plane or production writer.
