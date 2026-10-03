# Shot setup, plate and lens

- Record source path/hash, frame range, resolution, pixel aspect, frame rate, color-management context and camera/lens evidence before mutation.
- Keep plate preparation reversible and separate from integration.
- Resolve lens distortion before committing tracking or CG alignment. A common coherent pattern is undistort for analysis/CG, composite in the chosen working geometry, then redistort for delivery.
- Treat STMap/lens data as versioned source evidence; do not silently regenerate or swap it mid-shot.
- Validate that the generated/read-back comp opens with the intended color configuration; correct node counts and file paths do not prove color setup is valid.
- Preserve overscan/crop assumptions across plate, CG and delivery.
