# Office 2.0 / #604 — HOST Docker daemon can access guest signer key: synthetic expected NEGATIVE

**Date 2026-10-11. Status at authoring: LIVE experiment pending; only 11 local, model-free, Docker-free static tests PASS.** This is a deliberately adversarial proof scoped to a single disposable GitHub-hosted VM, not a production key-management feature.

## Why this matters

[PR #686](https://github.com/nocturney/velvetos-core/pull/686) established twice that two simultaneous isolated Docker guests sharing **the same Linux UID65534** had separate mount namespaces: the worker could not read, hardlink, symlink or derive the signer's **fake temporary HMAC key** even with the same Unix UID. That narrowly disproved treating the UID alone as an admission/denial condition within separate guest mount namespaces. It does **not** show the **host Docker daemon or VM administrator** lacks access to the signer's key. #604 cannot promote an “exclusive Git Sink credential owner” until the threat model covers the authority of the host controlling the runner.

## Expected destructive *simulation* (synthetic only)

A new GitHub Actions **PR-change-only**, Ubuntu24.04 hosted workflow with `permissions: {}`, `actions/checkout@v7 persist-credentials:false`, and no exported Git tokens, no production environment or external service runs `scripts/vf_office_v2_604_host_docker_daemon_key_negative.py`. It uses the exact immutable OCI image `python@sha256:0a310eeecf4e1f5a0743f9a6520c90c88d089c903ca5fd283f501e3a805f5f89` validated in [#685](https://github.com/nocturney/velvetos-core/pull/685).

A fresh temporary public synthetic intent and trusted reference `signer.py` are placed on exactly **one read-only bind mount**. A non-root (`uid65534`) signer container with no network or capabilities generates an unpredictable **synthetic** 32-byte HMAC key inside its **signer-only ephemeral tmpfs /sink**; it emits only a MAC of a public test string, not the key. While the container stays alive, **the privileged GitHub-hosted VM process, using its existing authorized Docker daemon access**, attempts `docker cp <owned-container-id>:/sink/signer-only.key -`. The private key exists only in the signer guest, but the host daemon is privileged relative to guest mount isolation.

The Docker CLI output is captured as a small TAR archive **only in parent RAM**; it is parsed with strict exactly-one-file, exact 32-byte key controls. The parent calculates HMAC in memory and must match the signer's public MAC. **No key, TAR archive or MAC is printed, written to files or uploaded**. Exact running container identity and Docker HostConfig/mounts are attested before attempt, and the signer must still be live after the attempt. The container is removed in a `finally` clause, deleting its ephemeral key. A positive probe deliberately means **host Docker daemon could access the guest secret**—a SECURITY NEGATIVE, not a secured signer.

## Boundaries, operator policy and acceptance

Local `selftest` checks 11 immutable-OCI/synthetic-only/argument-contract negative cases, no Docker or model calls. Direct `run` on Chris SYSTEM or Mac UID501 refuses before any container is created. Live GH hosted runner must **actually** demonstrate privileged daemon access without leaking even synthetic bytes, while the published receipt maintains `production_git_secret_custody_safe=false` and `kernel_escape_resistance_proven=false`.

This is NOT a request to steal, read, search or log real credentials. It uses only an owned temporary guest and freshly generated random bytes, and does not access any existing user account, Keychain, token, cloud, SSH credential, customer file, Instagram, printer or CAD process.

**Correct conclusion if the expected negative occurs:** A signer key kept only in a private Docker guest tmpfs is hidden from an unprivileged sibling container, **but not from an administrator of the shared Docker daemon/host**. Future #604 Git Sink admission requires a stronger separately administered trust root or strictly verified external signer custody, combined with explicit provider lease/epoch/ref freshness, durable intent and cancellation/crash reconciliation. Do not grant local workers Git credentials, do not treat a GitHub-hosted QA runner as a globally sole Git writer, and do not alter existing production writers. #604 P0 remains RED; #612 remains PARTIAL regardless of result.
