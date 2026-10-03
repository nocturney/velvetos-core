# Slice and G-code QA

Before handoff, inspect the exact generated artifact.

1. Confirm printer/profile/nozzle/material selection.
2. Check model bounds, placement, orientation and part count.
3. Review layer preview for missing regions, unexpected gaps, thin-wall loss, support/contact issues and unintended seams.
4. Inspect estimated material/time as planning information only, not proof.
5. Check configured temperatures, flow limits and tool/material changes against the resolved profile.
6. Review start/end/custom G-code provenance when present; do not accept unknown arbitrary commands.
7. Run the existing deterministic G-code validation path.
8. Keep digital G-code approval separate from human printer-operation approval and physical-print evidence.