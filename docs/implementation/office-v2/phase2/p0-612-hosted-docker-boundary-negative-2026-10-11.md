# Office 2.0 P0 / #612 — hosted Docker boundary negative LAB (2026-10-11)

**Pre-admission state: LAB / not autonomous P0 GREEN.** This is a **new experiment** beyond the previous read-only GitHub-hosted synthetic QA [#684](https://github.com/nocturney/velvetos-core/pull/684). It does not alter, unlock or replace the fail-closed local Diverse Worker `admit`, `run`, or `independent_qa` from [#683](https://github.com/nocturney/velvetos-core/pull/683). Chris Windows Remote Desktop Commander remains SYSTEM Session 0; macOS remote user is UID501, and neither is an admitted generated-code executor.

## Narrow hypothesis and real negative probes

Use **one existing standard `ubuntu-24.04` GitHub-hosted ephemeral VM** in a PR-triggered workflow, with `permissions: {}` and `actions/checkout@v7 persist-credentials: false`. No scheduled jobs, GitHub writer token, production environment or cloud/model API is supplied to the test. The VM host itself can access Docker and the public container registry, but generated-source Python is **never** executed on the host.

The workflow `.github/workflows/office-p0-hosted-docker-boundary-lab.yml` invokes `scripts/vf_office_v2_p0_hosted_container_boundary_lab.py`. Before any generated code, it validates host runner identity markers, no exported credential environment, absent persisted checkout auth, source SHA-256, trusted public fixture SHA-256, and the OCI image content hash. Each of three disposable Docker containers receives only an exact **read-only bind mount of temporary public synthetic code/QA**; every container is created with:

- `--network=none`; `--read-only`; `--cap-drop=ALL`; `--security-opt=no-new-privileges:true`
- `--user=65534:65534`; private PID and no IPC; `--pids-limit=32`
- `--memory=256m`, `--cpus=1`, bounded file and descriptor limits, and 32MiB `/tmp` tmpfs with `noexec,nosuid`
- No Docker socket bind, no host home/repository mount, no Git credentials, no host-only disposable canary bind and no model/network access.

The parent inspects the **actual native Docker HostConfig and mounts before starting each guest**, not only the intended CLI arguments. Inside each guest, real Python negative controls attempt outbound TCP, discovery of non-loopback NICs, access to an outside synthetic canary file, writing into read-only fixture/root, acquiring UID0, and access to Docker socket/GitHub token variables. A third **public broken canonical-tag seed** must fail both visible and hidden QA rather than create a false green. The **two positive inputs are previously observed pinned source files**, never unknown arbitrary new code:

| Pinned archive source | SHA-256 | Expected independent QA |
| --- | --- | --- |
| Existing Mac Qwen4B canonical-tag | `b2ec92fed514a5e0e37aeca31155fe0d04cdfde70a3d46fafeeb9a09b0ef1ccb` | Visible 3/3 and hidden 12/12 |
| Existing Windows Qwen9B merge-windows | `e625ea816531000df82d15144f3155ebd59a868a2dd89c81c1f254115bafb2b9` | Visible 3/3 and hidden 12/12 |

## Safety, cost, failure and image provenance

The initial experiment pulls the public official `python:3.11-slim-bookworm` image; the first live run is **digest discovery only**, using the pulled SHA-256 image ID for that run and recording the registry's RepoDigest. Before a final production-independent proof, pin the exact OCI registry digest into source, re-run fresh protected CI on the new exact head and preserve both receipts. A mutable tag alone is **not** cross-run reproducible. If Docker is absent, credential preflight fails, the OCI digest drifts, any security configuration differs, any expected negative probe succeeds unexpectedly, QA fails, the child times out or cleanup fails, return **FAIL_CLOSED**, not a fallback to local/system execution.

Local `selftest` never invokes Docker, the model, generated code or a Git write. It validates source/fixture pins and synthetic attack mutations of container flags. Local `run` on macOS or Windows must fail before Docker subprocess or generated-source QA. Native GitHub job results will be linked here only after actual provider readback.

**Explicit nonclaims:** Docker is not a proof against a hostile kernel exploit, unbounded arbitrary adversarial code, runtime escape by unknown malware, host admin compromise, full egress/metadata access in every configuration, deterministic billing, or a hardened guest/VM for commercial secrets. Since the generated source is already known and source-pinned, this pilot tests a *bounded concrete workload*. It does **not** mint a model worker, prove 1-vs-2 accepted *new* algorithms, do autonomous PR writes, own #604 Git credentials, implement cross-store exactly-once or re-enable unconfined local Aider. If the negative checks pass, admit only the narrow disposable source/QA surface and leave broader P0 RED/PARTIAL.

References: [#604](https://github.com/nocturney/velvetos-core/issues/604) is the exclusive fleet/credential custody owner; [#612](https://github.com/nocturney/velvetos-core/issues/612) owns coding agents/QA. Existing production scheduled writer workflows are untouched. No Codex CLI, paid model API, local Windows Sandbox/WSL settings, macOS security changes, publication, CAD, printer, customer or key access.
