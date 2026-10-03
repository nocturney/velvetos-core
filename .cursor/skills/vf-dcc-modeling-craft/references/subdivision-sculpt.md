# Subdivision and sculpt craft

- Establish primary and secondary forms before spending detail on tertiary surface noise.
- Keep subdivision support geometry proportional to the intended edge character; avoid dense support loops where a cleaner construction can express the same form.
- Check the unsubdivided cage and subdivided result together to detect pinching or hidden shape dependency.
- Keep sculpt masters separate from retopologized production meshes when the workflows have different requirements.
- Preserve a recoverable high-resolution source before destructive decimation, remesh or projection operations.
- For hard-surface work, inspect highlight flow; a technically manifold surface can still have poor curvature continuity.
- For functional printed geometry, do not let smoothing/subdivision alter protected interfaces or nominal dimensions.
