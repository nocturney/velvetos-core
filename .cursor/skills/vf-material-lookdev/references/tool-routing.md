# Tool routing notes

Execution stays on the existing VelvetOS adapters.

- Substance Painter: primary for mesh baking, texture-set painting, masks and asset-level material authoring. Current Painter baking supports per-map inspection, bake logs, cage modes, mesh-name matching, skew correction and OpenPBR workflows.
- Substance Designer: primary for procedural graph authoring, reusable material logic and deterministic texture generation where already connected.
- Substance Sampler/Modeler: craft guidance may be used, but the current local handoff does not establish an accepted official automation adapter. Treat execution as unavailable/manual until a later integration accepts one.
- Blender/Maya/3ds Max: use for UV, mesh normals/tangents, source geometry and destination look checks when routed by the existing DCC stack.