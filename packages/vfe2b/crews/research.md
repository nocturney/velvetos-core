# Crew: research

Source patterns: GPT Researcher, Aomni, Private GPT, Local GPT, GPT Runner, MemGPT.
Packs: `vfresearch`, `vlicense`, `vfsku`, `vfbiz`.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Planner | `vfresearch` | Writes 5–8 research questions. | Answers them from memory |
| Gatherer | `vfresearch` | One source per question (URL or HQ path). | Invent citations |
| Memory | HQ catalog | Recalls existing packs / CHANGELOG. | Invent prices or Insights |
| License | `vlicense` | Flags new models / fonts / STL. | Auto-add to catalog |
| Human | — | Accepts or rejects the note. | — |

## Run

1. Restate the topic in one Hebrew line.
2. Planner: numbered questions only.
3. Gatherer: for each question, `{question, source, excerpt-or-חסר}`.
4. If the topic is a new printable / SKU / weight, stop for `vlicense` before `vfsku`.
5. Write the note under `vfresearch` (or say the tree is not vendored yet and keep the note in the chat).

## Done when

Every question has a source or an explicit **חסר**. No invented metrics.
