# P0 historical live-model worker PID snapshot — scoped LAB 2026-10-09

Owner: https://github.com/nocturney/velvetos-core/issues/612; host scheduling and leases remain exclusively https://github.com/nocturney/velvetos-core/issues/604.

## Actual outcome

After existing real Aider SIGKILL in PR #629, new read-only scripts/vf_office_v2_p0_owner_snapshot.py validates the original Task Envelope and the external historical force-kill observation. It requires exact original task, host, envelope hash, model and digest, worker/Aider PID and process group, and already recorded refusal of the blind retry. It reads only the historical PID numbers from a current OS process snapshot and rechecks that the original UNKNOWN journal still exists unchanged. No model, retry, scheduler, signal, authorization or business effect.

Historical Mac attempt p0-mac-kill-1 used worker PID 40456, Aider PID/group 40465, and envelope hash e55ce10ae527094029b37084b616c6338d3c17af90262dd5c4df4172102f9b40. A real Mac snapshot at 2026-10-09T10:56:32.614814+00:00 found neither historical PID. The original RUNNING journal stayed present; the original success receipt remained absent. The observer now checks that the exact journal file SHA-256 still equals the external historical SIGKILL receipt before AND after the process snapshot; a mismatched journal hash fails closed. NO_PID_AT_SNAPSHOT is NOT proof that all descendants are absent, and explicitly does NOT authorize any rerun or process cleanup.

## Reproduction

Run selftest in a Python 3.11+ checkout: python scripts/vf_office_v2_p0_owner_snapshot.py selftest

To inspect the existing on-host historical attempt, an operator can call:

python scripts/vf_office_v2_p0_owner_snapshot.py observe --envelope /absolute/envelope.json --kill-observation /absolute/forced-live-model-kill.json --receipt /absolute/output/receipt.json

On macOS/Unix the tool uses ps for a bounded process snapshot; on Windows it uses Get-CimInstance through a bounded noninteractive PowerShell read. Only observed PID existence, relationship metadata and hashes of matching process command/start text appear in results; unrelated full command lines are never emitted. 16/16 offline mock selftests PASS on both Mac and Windows and CI only runs selftest, never observe. Negative controls reject wrong task/host/model/hash, forged kill flags and requeue permission, invalid PID, duplicate process IDs, wrong parent and misleading command text. Original evidence and journal are left untouched.

## Safety and remaining acceptance

The v1 model RUNNING journal lacks trustworthy OS process creation identity, so PID reuse remains possible; possible match is NOT start-time attestation. No claim of worker live-ownership, all-descendant absence, automatic recovery, safe restart, worker-fleet authority or production promotion follows. This gate has zero model invocations, process kills, additional paid APIs or Codex CLI. Next #612 capability needs durable PID plus process-start identity, negative ownership tests and fail-closed reconciliation; #604 owns any actual cross-host lease/scheduling work.
