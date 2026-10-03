# Meshmixer mesh surgery

Use Meshmixer only as a bounded legacy utility when its accepted integration is available and it offers a faster repair/surgery path than the primary DCC/CAD tools.

- Always operate on a disposable copy, never the only source mesh.
- Inspect scale, bounds, shells, holes, normals and obvious self/intersection defects before editing.
- Use repair, remesh, reduce, plane-cut, boolean, separate/combine and hollow/split operations only when the live accepted surface exposes them reliably.
- Preserve critical dimensions before remeshing or solidification; compare measured values afterward.
- Use reduction based on silhouette/error needs, not an arbitrary triangle target.
- After booleans or cuts, recheck manifoldness, normals, thin regions and disconnected shells.
- Hollowing, drains and splits are print-prep operations only when the actual process requires them and must still pass the canonical DfAM checks.
- Export to a new path and independently verify the exported STL/OBJ/3MF before delivery.
- If the legacy Meshmixer API is unavailable or unstable for the installed build, fail closed and route equivalent mesh work to Blender/Fusion rather than weakening the host.
