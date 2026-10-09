# P0 live Aider child OS-birth pin — optional LAB gate (2026-10-09)

Canonical owner #612. Depends on merged two-host native process birth identity proof [PR #634](https://github.com/nocturney/velvetos-core/pull/634).

## Code and safety

The existing model-aware local-only synthetic worker is unchanged by default. A NEW versioned opt-in string `kernel_birth_capture=REQUIRE_OS_BIRTH_BEFORE_QA_V1` may be placed by `vf_office_v2_p0_local_model_fixture.py --kernel-birth-pin` only in a unique `AgentEnvelopeLab` fixture. Worker preflight refuses invalid opt-in values. After an actual Aider subprocess is launched from the pre-pinned Aider binary and the fsynced `receipt.json.running` journal exists, it captures both worker and child OS kernel process birth identities and their real parent relation, writes the externally bound `kernel-pin.json` with create-exclusive semantics, and immediately re-reads both PIDs to guard reuse. The result is not a new Task Envelope schema, queue, scheduler or authority provider.

Any failed OS birth capture prevents a successful receipt even if the model later edits source successfully. An opt-in success must pass the existing independent 3+12 QA and an additional **pure pin readback** that reconstructs the original RUNNING journal from the receipt started-at, verifies pin selfhash, source directory hash, task/envelope/host binding, creation-time data and parent/session relation. The journal remains on errors. No worker can auto-requeue. A previous killed worker lacking such birth pin cannot be retro-certified.

## Experimental evidence and promotion

This PR initially adds the optional source code, offline selftests and no additional claims of a completed real-model run. Next acceptance must explicitly launch this updated worker on both actual connected hosts in exclusive new fixtures, verify real model source edit+pin+QA receipts, SIGKILL a *separate uniquely owned* opt-in Aider worker while alive, confirm surviving UNKNOWN journal and pinned PID/start readback, then independently ensure no blind retry. Record all results in issue #612 and a protected subsequent evidence update before concluding acceptance. #604 alone owns placement/host leases; no production writer, paid APIs or Codex CLI.

