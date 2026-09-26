# VF Project 6.6.1 — first-pass completion and creative continuity

## Trigger
Cold-start behavioral test from 2026-09-20. The new Project correctly loaded multi-source/Product Truth concepts and produced a strong source-faithful styled base visual, but it stopped after an intermediate visual and, after the owner asked "זהו..?", rebuilt the final post from a weaker raw-source composition. The finalization step therefore regressed the successful creative direction instead of preserving it.

## Goal
Make publication-prep complete on the first response when tools/sources permit, and make finalization preserve the strongest already-approved creative master instead of restarting from raw media or another weaker direction.

## Scoped corrections
1. **No premature handoff:** "תכין פוסט", "תכין לפרסום", post/carousel/Story/Reel-cover/grid and equivalent requests remain execution tasks. A base/staging/hero visual is an internal stage, not a completed response, unless it is deliberately selected as the final NO_TEXT artifact and passes all final gates.
2. **Creative-master continuity:** once a source-faithful base visual passes Product Truth + reference match and is selected as the best direction, freeze it as `creative_master`. Final copy, deterministic typography, icons, logo, dividers and insets are composed onto that exact master. Do not silently restart from the raw source, swap scene/background or regenerate the hero during finalization.
3. **No-regression finalization:** finalization must preserve or improve the selected master on product fidelity, atmosphere, hierarchy, depth, reference match and editorial richness. A final artifact that is materially weaker than its selected master is FAIL -> targeted repair.
4. **Restart only for cause:** replacing the selected master is allowed only for a recorded reason such as Product Truth failure, unsupported claim/asset, unreadable composition, owner-directed change or an objectively blocking artifact defect. Record `creative_master_replaced=true`, reason and replacement evidence.
5. **Source-set continuity:** alternate verified sources remain available for truthful distinct details. They do not justify replacing a strong hero/master unless the creative plan explicitly chooses a new master before final overlay.
6. **TEXT_WINS / NO_TEXT:** text is not mandatory. If NO_TEXT wins, the selected clean visual may itself be the final artifact, but that is a deliberate final decision, not an accidental stop after the generation/edit stage.

## Non-goals

## Acceptance
- Contract 6 / Revision 6.6.1 / `VF-PROJECT-6.6.1-FIRST-PASS-CREATIVE-CONTINUITY`.
- Active pointers/validators bind only 6.6.1.
- Machine policy contains fail-closed no-premature-handoff and creative-master-continuity rules.
- Project Instructions encode the same behavior compactly.
- Structural sensor proves the rules are present and Project Instructions bytes are bound.
- Full CI passes.
- Complete install bundle generated and SHA-verified.
