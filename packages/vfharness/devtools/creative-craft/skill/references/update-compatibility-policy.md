# Update and compatibility policy

This policy applies to Creative Craft automatic routing. It supplements, and does not replace, the existing DCC/Adobe Update Sentinel and per-tool acceptance receipts.

## Default rule

A tool update is never assumed compatible merely because the application launches. Automatic routing is enabled only when the tool's configured authority gate is healthy.

## Gate types

- **DCC Update Sentinel:** app fingerprint and compatibility probe must resolve to `available`.
- **Accepted candidate adapter:** candidate matrix entry must remain `PASS`; the deployed runtime adapter must exist and, where recorded, match the accepted SHA-256.
- **Verified runtime state:** HyperFrames, VoiceStudio, Manim and similar local runtimes require their stored doctor/smoke state to remain passing.
- **Authority files:** Fabrication authority files must exist under the configured source root and match the accepted SHA-256 baseline.
- **Support CLI:** deterministic support executables must remain discoverable; their use is still bounded by policy.

Any missing, stale, failed, or hash-mismatched gate fails closed for that tool without disabling unrelated tools.

## Post-update sequence

1. Detect version/fingerprint change.
2. Preserve the previous accepted config/state for rollback.
3. Run the tool-specific compatibility probe or accepted smoke through the correct execution context.
4. Verify exact output/readback where the tool creates artifacts.
5. Confirm ownership/cleanup: do not attach to or close a pre-existing user GUI session.
6. Record the new receipt and only then mark the route available.
7. Re-run affected Creative Craft `status` / `plan` checks. Do not globally re-baseline unrelated tools.

## Tool-specific notes

- **Maya:** available. Automatic Maya routing uses the managed hidden `mayapy` host, requires endpoint ownership by the managed host PID, probes the registered `discovery_mcp_url`, and validates current 0.9.31 read-only tools. Latest accepted compatibility receipt: `D:\Velvet\Logs\DCC-Adobe-Update-Sentinel\receipts\20261003T053432Z-maya.json`.
- **OpenSCAD Nightly:** track latest compatible Nightly, but do not auto-update. After update, run CLI conversion smoke and Sentinel compatibility probe before routing.
- **PrusaSlicer:** discovery is healthy, but OrcaSlicer remains canonical for the accepted Fabrication path. Do not promote Prusa to automatic fallback until profile parity is explicitly accepted.
- **HyperFrames:** runtime version and doctor/render smoke state must agree; a state file alone cannot stand in for an installed runtime.
- **InteractiveToken candidates:** InDesign, Media Encoder, XVL/Corel and similar GUI/COM automation must be validated through the accepted InteractiveToken Scheduled Task/host path. Session-0 failure or apparent success is not production evidence.
- **Media Encoder:** only named accepted presets are routable; currently `h264-high`. Add presets by receipt, not arbitrary encoder argument exposure.
- **Topaz Gigapixel:** retired for this phase; updates must not recreate config, baseline, or routing entries.
- **ElegooSlicer / Flash Studio:** reference/profile candidates only; an update does not make them routing authorities.
- **gcloud / gh / 7-Zip:** keep support roles least-authority. Version updates require command/probe compatibility but do not grant new cloud, repository, or packaging permissions.

## Security and authority invariants

Compatibility repair must not weaken signature/integrity/security controls, broaden IAM, expose secrets, enable arbitrary script/eval surfaces, auto-publish, send email, incur unapproved cloud spend, or enable printer upload/start/heating/motion.

A successful compatibility probe restores only the previously approved surface. New operations require separate typed acceptance.
