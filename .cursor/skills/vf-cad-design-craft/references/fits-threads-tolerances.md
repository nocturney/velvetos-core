# Fits, threads and tolerances

Use this reference whenever two parts must mate, slide, snap, screw, press, seal or align.

## Evidence first

Resolve the manufacturing process, material, machine/profile, orientation, mating geometry and desired fit behavior before assigning compensation. If any of these materially affect the interface and are unknown, keep the value unresolved or request a calibration artifact instead of guessing.

## Fits

- Describe the intent first: free-running, locating, sliding, transition, interference, snap or retained fit.
- Prefer standards or measured process capability when they apply.
- For additive manufacturing, use coupons or prior measured evidence from the relevant machine/material/profile when possible.
- Apply compensation at the interface feature, not by globally scaling the whole model unless scale error is the evidenced problem.

## Threads

- Record thread system, nominal size, pitch, handedness, engagement length and manufacturing route.
- Use cosmetic/thread metadata only when physical helical geometry is not required by the downstream process.
- For printed threads, verify wall thickness, root/crest survivability, lead-in and mating clearance against the intended process; do not assume nominal CAD threads will print and mate correctly.
- Re-check both male and female parts after any compensation change.

## Tolerances

- Distinguish nominal dimension, manufacturing tolerance and assembly clearance.
- Use tolerance stack analysis for chained interfaces where multiple dimensions contribute to final fit.
- Do not promise a physical fit from CAD inspection alone.
