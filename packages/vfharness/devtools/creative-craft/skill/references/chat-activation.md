# Natural chat activation

Use this reference when a user asks in ordinary language for work that belongs to the local Creative Craft stack.

## Expected conversational behavior

The user should be able to say things such as:
- "תכין לי מודל כזה ב-Maya"
- "תבדוק אם ה-STL הזה מוכן להדפסה"
- "תכין ריל קצר מהמוצרים האלה"
- "תייצר שרטוט טכני ותוציא PDF"
- "תעשה לי BOM באקסל"

Do not require the user to mention Creative Craft, a Skill name, MCP, a router command, a local path, or a particular adapter.

## Execution sequence

1. Infer the high-level intent from the request and run Creative Craft `route --request`.
2. If the user explicitly named a tool, keep that preference when the selected authority allows it and its live gate is healthy. An explicit app preference does not override Product Truth, Fabrication authority, publish authority, or a failed compatibility gate.
3. Run `status --tool <id>` for every required local capability before execution.
4. For DCC hosts, use `host --tool <id> --action start` only when needed. Hidden/headless accepted automation routes take precedence over opening a visible GUI.
5. Load only the specialist Skills returned by the plan.
6. Execute the accepted typed operation through the existing adapter/authority.
7. Verify the exact output/readback/receipt.
8. Stop only agent-owned hosts when cleanup is appropriate. Preserve user-opened sessions.

## Chat-to-workstation transport

ChatGPT cannot treat `D:\Velvet` as its own filesystem. Use the connected Remote Desktop Commander workstation to invoke the router and local adapters. If that connector is unavailable, local execution is unavailable; do not simulate success.

## Current execution coverage

Creative Craft already provides direct bounded execution surfaces for Fabrication, Fusion, Meshmixer, Corel, Topaz Video, host lifecycle, routing, and planning. Accepted Phase 2 adapters provide bounded operations for InDesign, PHOTO-PAINT, Fusion Studio, Office, Acrobat, SketchUp/LayOut, Media Encoder, XVL, and OpenSCAD.

Some DCCs such as Maya, Blender, 3ds Max, AutoCAD, Inventor, ZBrush, Substance, Photoshop, Illustrator, After Effects, and Premiere are routable and compatibility-gated, but not every useful authoring action is yet exposed through one uniform Creative Craft execution command. When a requested action exceeds the accepted typed surface, report the typed gap. Do not fall back to arbitrary scripting.

## Target end state

For fully uniform "just ask" execution, expose a thin Creative Craft chat bridge with allowlisted verbs only:
- route
- status
- plan
- host_start / host_stop
- execute_typed
- artifact_verify
- cleanup

The bridge must delegate to existing authorities/adapters rather than duplicate them. It must never expose arbitrary shell, Python, Lua, COM, eval, unrestricted MCP tool calls, printer control, or publish authorization.
