# Fabrication verification

- Require evidence-before-done: a successful command, slice or mesh export proves only that stage completed.
- Check numeric facts directly where possible: units, bounding dimensions, wall/interface dimensions, part count, mesh status, estimated material/time from the actual slice, and selected printer/profile identity.
- Separate digital printability evidence from physical-print proof. Only an observed/measured print can establish physical fit, surface, strength or process success.
- Bind verification to the exact input/output artifact and profile/version so a later file cannot inherit an old pass.
- Use preview/G-code checks to inspect first layer, unsupported regions, travel/retraction risks, thin features, support contact and unexpected toolpaths as applicable.
- Record unresolved uncertainty instead of filling it with a familiar slicer number.
- Re-run the relevant check after any geometry, orientation, profile or material change that could invalidate prior evidence.
