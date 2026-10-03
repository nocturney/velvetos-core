# CAD verification contract

Before delivery, verify what can be verified digitally and label what remains physical.

1. Re-open or independently inspect the engineering master when possible.
2. Check units, global bounds and orientation.
3. Measure every protected functional interface against the source requirement.
4. Confirm holes, bosses, wall sections, engagement lengths and clearances that affect assembly.
5. Regenerate after final parameter changes and inspect downstream features for breakage or topology flips.
6. Export the required downstream format and re-open/inspect that exact export.
7. Run the existing DfAM and slicer/g-code checks when the output is intended for additive manufacturing.
8. Distinguish: digital geometry pass, manufacturing-prep pass and physical fit proof.

A green feature tree, successful save, or visually plausible render is not sufficient evidence by itself.
