# Crew: content draft

Source patterns: Wordware, GoCharlie, Wispy, Diagram, v0 (layout only).
Packs: `vfcopy`, `vfcovers`, `vfigos`, `vfgrowth`.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Homework | `vfcopy` | Voice, facts, banned claims. | Invent Insights |
| Draft | `vfcopy` | Caption / carousel text. | Post |
| Cover | `vfcovers` | Brief the cover. Superdesign/Canva if asked. | Publish |
| Scheduler | `vfigos` | Review slot. Native schedule via Grok. | Send from HQ |
| Sprint | `vfgrowth` | Batch the week. | Boost / DM |
| Human | — | Approves. Grok sends. | — |

## Run

1. Homework first: what is true, what is not claimed.
2. Draft Hebrew (and English if the brief says so). Lint against studio voice.
3. Cover brief: size, text on image, no fake metrics on the graphic.
4. Hand the approved draft to Grok Bot. This HQ does not send Instagram.
5. If Grok weekly quota is exhausted:
   - Not urgent → `#מוכן-ל-Grok` in `packages/vfigos/QUEUE.md`.
   - **Needs live post now** → `#פרסום-חי-דחוף` + complete `packages/vfigos/LIVE-PACKET.md`; a **human** posts. HQ agent does not press Publish.
6. Keep producing. Do not idle. Playbook: `packages/vfharness/playbooks/grok-failover.md`.

## Done when

A reviewable draft exists. Send status is **not sent from HQ agent**. During Grok failover, «done» means `#מוכן-ל-Grok` **or** a complete LIVE-PACKET handed to a human for `#פרסום-חי-דחוף`.
