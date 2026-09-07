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

1. Homework first: what is true, what is not claimed. Floor proof only — invent no studio scene.
2. If production handed a `print.done` card (`vfprod/PRINT-DONE.md` + `python3 scripts/vfprod.py print-done`): require media path. Missing → **חסר**. Then `vfom/crews/hybrid-reel.md`. HQ does not watch Bambu/Snapmaker/Elegoo.
3. Draft Hebrew per `vfcopy/VOICE.md`. Funnel CTA from `vfgrowth/hq/PROFILE-TO-WHATSAPP.md` (process-short = follow; product-story = WhatsApp `050-2517000`). Lint against studio voice.
4. Cover brief: size, text on image, no fake metrics on the graphic. Canva first; failover `studio/render.py` then Superdesign. **EDIT-GATE** — no raw JPEG.
5. Written `PREFLIGHT.md` artifact before schedule. Fail-closed = do not book. Morning brief **does not** publish Instagram.
6. HQ **sends Instagram via tools** (`constitution/SEND.md` + `vfigos/SEND.md`):
   - Publish MCP connected → publish and tag `#נשלח-מ-HQ`.
   - No publish MCP → **same turn** Canva + Drive `create_file` + Gmail `send_message`. Tag `#נשלח-מ-HQ` and `#ממתין-ל-כלי-IG` if the feed itself did not go up.
7. Do not idle on `#מוכן-ל-Grok`. Grok Bot is optional backup. Playbook: `packages/vfharness/playbooks/grok-failover.md`.
8. Never claim the feed posted if no publish tool fired. Calendar: Sun/Tue 16:00 reels, Thu 12:00 carousel — not a reel every weekday.

## Done when

A reviewable draft exists on disk **and** the send path ran (tool or failover packet). Send status is honest: posted, or `#ממתין-ל-כלי-IG`.
