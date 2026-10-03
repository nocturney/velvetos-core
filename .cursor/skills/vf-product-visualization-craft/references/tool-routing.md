# Tool routing

- Use Creative Craft and the accepted registry to select the execution surface; this Skill never creates a second renderer route.
- Blender is the current primary bounded turntable/render surface when the registered pipeline selects it.
- Substance Painter/Designer or another accepted material surface remains subordinate to `vf-material-lookdev` for material truth.
- Maya/3ds Max may contribute modeling or scene work only through their accepted DCC surfaces and the existing routing gates.
- Preserve user sessions and use only named/bounded operations exposed by the accepted adapter.
- If camera/light/render authoring is not exposed on the selected tool, report the typed gap instead of falling back to arbitrary Python, COM, eval or raw MCP execution.
