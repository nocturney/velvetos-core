# Office #604 — Docker daemon synthetic signer execution-authority negative control

**2026-10-11. LAB only; #604 Git Sink P0 RED.** Extends the actual two-container #686 same-UID synthetic-key denial experiment instead of adding another workflow, daemon, token or authority.

## Threat-boundary question

The uncredentialed worker and signer containers can both run UID65534 and have separate mount namespaces. #686 already observed the worker cannot read /sink. That proves **worker-mount denial**, not secrecy or policy enforcement against the administrator of the Docker daemon that created the signer.

This new negative probe runs only inside the existing zero-GitHub-write-permission hosted PR workflow. While the original signer remains live and worker direct/hardlink/symlink/HMAC/egress attacks are independently denied, the existing synthetic Docker administrator client uses `docker exec <exact-CID> python -B -c <fixed-script>` to request a fresh signing operation inside the **signer** mount namespace. The fixed script reads only the already-created *disposable* `/sink/signer-only.key` and *public* intent, recomputes a SHA256 HMAC, and prints **only that synthetic MAC** into the parent Python's captured stdout. The parent compares its digest against the original reported signer HMAC using constant-time comparison; neither the key bytes nor the digest are intentionally written into GitHub logs or repository files.

If it succeeds, the precise result is **daemon can invoke the synthetic signer's signing authority despite ordinary worker denial**. That is a security NEGATIVE, not an authorization success. The outcome must not imply that the daemon has been denied key/memory access or that actual GitHub credentials are safe. The probe has no access to any real credential, service-account token, Keychain, certificate, production Git API, business data or printed model output.

## Current acceptance gates

- Historical #686 actual two-container worker **denial** remains required before the new daemon probe. No relaxation of flags, UID, read-only mount or network is permitted.
- Static `selftest` increased from 19 to **21 model-free tests**, adding a fixed probe-source guard and refusal for malformed/unowned container IDs. Local `run` on Mac and Windows must refuse non-hosted context with exit2.
- Actual hosted job must show both the original worker denial and `docker_daemon_can_command_live_signer_observed=true`, `daemon_injected_synthetic_signature_matches=true`, while `host_daemon_cannot_read_key_proven=false`, `exclusive_native_git_sink_authority_proven=false` and `provider_epoch_and_github_commit_fenced=false` remain explicitly false.
- Every result is tied to the exact source SHA, protected GitHub PR head, and expected-head merge. Current source digest: `20cce6a09dec25de74d624361806a8ec2d758856217dd048123cdac8fc7281bd`.

**At authoring:** Mac static 21/21 PASS; Mac local run refused. Protected live CI and independent Windows static recheck remain REQUIRED. Do not claim a real hosted daemon negative outcome until that job completes. Existing real production writers remain untouched. No Codex CLI, paid model/API, system security settings, OS accounts, local Docker installation, scheduler or physical output was changed.
