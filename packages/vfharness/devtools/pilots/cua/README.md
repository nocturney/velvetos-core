# Cua Windows bounded pilot (Chris, 2026-10-08)

This is a **closed, evidence-backed pilot**, not an active business execution provider. The canonical execution-provider registry retains `runtimeAuthority: false` and `activationAllowed: false`. **Capability is not authority:** future design, isolated testing and integration for printers, social publishing, customer sends, purchases, credential-mediated workflows and other GUI operations are permitted in principle. They cannot execute in the current pilot. Any business action or executable allowlist expansion needs separately reviewed promotion, task-specific owner instruction or explicit bounded owner approval, the existing effect-specific policy gate, verified runtime safety and post-action readback. This clarification grants no new runtime permission.

## Supply chain and staging

- Pin: `trycua/cua`, `cua-driver-rs-v0.34.0` (Cua Driver 0.34.0).
- Standalone Windows asset: `cua-driver-rs-0.34.0-windows-x86_64.zip`.
- Expected SHA-256: `f96cc1632bc88e6f268eab745277c1fc302bb0f7d123e04373e35afecad6439f`.
- Runtime executable observed SHA-256: `77f5cac754b42b6a8bae126414fc8f7487432ace93466967965188e24e9e53fb`. Authenticode: valid, Cua AI, Inc.
- Repository license MIT; native Windows package declares `MIT AND MPL-2.0`. Perception / OmniParser were not installed.
- No pipe-to-shell remote installer. No global package, PATH edit, service, or autostart.

## Bounded test

The scripts are **host-specific evidence/reproduction sources**, not standalone production authorizations. Review the Office Phase 3B main-line gate and ensure there is no concurrent Office GUI mutation before any later repro. On the authorized Windows session, compile `CuaSmokeFixture.cs` with the .NET Framework C# compiler as a Windows app, place it in the isolated fixture path, and use only `pilot-capabilities.yaml` with an executable allowlist for that app. The pilot launched in `CHRIS\\Chris` Session 1, never in SYSTEM Session 0. Telemetry was disabled.

`Start-CuaPilot.ps1` is a historical, opt-in bounded launcher: it must not be installed as a production service. `Run-CuaSmoke.ps1` uses an accessibility-targeted background click on `Compute 6 times 7`, then verifies `Result: 42` and the window title in a fresh UIA snapshot. Negative general desktop enumeration was refused.

The pilot processes and one-time tasks were cleaned up; only isolated reversible files and evidence remain. Source receipt: `packages/vfharness/state/cua-pilot-complete-2026-10-08.json`. The real Windows Calculator 6x7 acceptance is **not yet passed** (UIA tree loss and native click errors; no verified 42). All pilot processes were closed. Microsoft UFO is **uninstalled** and is now a read-only research candidate only if the material Calculator gap persists after root-cause diagnosis and a separate scope review.
