# Crew: content draft

Source patterns: Wordware, GoCharlie, Wispy, Diagram, v0 (layout only).
Orchestrator overlay: Claudexor — if Grok quota is empty, rotate to HQ tools the same turn.
Packs: `vfcopy`, `vfcovers`, `vfigos`, `vfgrowth`.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Homework | `vfcopy` | Voice, facts, banned claims. | Invent Insights |
| Draft | `vfcopy` | Caption / carousel text. | Claim the feed posted |
| Cover | `vfcovers` | Brief the cover. Superdesign/Canva if asked. | Invent a Canva URL |
| Sender | `vfigos` | Send via tools (`vfigos/SEND.md`). | Auto-DM. Boost. Fake publish |
| Sprint | `vfgrowth` | Batch the week. | Boost / DM |
| Human | — | Approves ₪ or a boost. Customer WhatsApp. | — |

## Run

1. Homework first: what is true, what is not claimed.
2. Draft Hebrew (and English if the brief says so). Lint against studio voice.
3. Cover brief: size, text on image, no fake metrics on the graphic. Canva first; failover `studio/render.py` then Superdesign.
4. HQ **sends Instagram via tools** (`constitution/SEND.md` + `vfigos/SEND.md`):
   - Publish MCP connected → publish and tag `#נשלח-מ-HQ`.
   - No publish MCP → **same turn** Canva + Drive `create_file` + Gmail `send_message`. Tag `#נשלח-מ-HQ` and `#ממתין-ל-כלי-IG` if the feed itself did not go up.
5. Do not idle on `#מוכן-ל-Grok`. Grok Bot is optional backup. Playbook: `packages/vfharness/playbooks/grok-failover.md`.
6. Never claim the feed posted if no publish tool fired.

## Done when

A reviewable draft exists on disk **and** the send path ran (tool or failover packet). Send status is honest: posted, or `#ממתין-ל-כלי-IG`.
