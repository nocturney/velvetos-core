# Crew: research

Source patterns: GPT Researcher, Aomni, Private GPT, Local GPT, GPT Runner, MemGPT.
Orchestrator overlay: Dex (human-gated plan, stop at a dead end) + ralphex (fresh context on retry).
Packs: `vfresearch`, `vlicense`, `vfsku`, `vfbiz`.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Planner | `vfresearch` | Writes 5–8 research questions. | Answers them from memory |
| Gatherer | `vfresearch` | One source per question (URL or HQ path). | Invent citations |
| Verifier | `vfresearch` | Re-opens the source or writes **חסר**. | Invent a blocked body |
| Memory | HQ catalog | Recalls existing packs / CHANGELOG. | Invent prices or Insights |
| License | `vlicense` | Flags new models / fonts / STL. | Auto-add to catalog |
| Human | — | Accepts or rejects the note. | — |

## Run

1. Restate the topic in one Hebrew line.
2. Planner: numbered questions only.
3. Gatherer: for each question, `{question, source, excerpt-or-חסר}`.
4. Verifier: if a live page is a wall, write «דולג — חומה» / «אין גוף». Do not invent. Retry re-reads the source; it does not guess.
5. If the topic is a new printable / SKU / weight, stop for `vlicense` before `vfsku`.
6. Write the note under `vfresearch/sources/` (or say the tree is not vendored yet and keep the note in the chat).

## Done when

Every question has a source or an explicit **חסר**. Artifact path is named. No invented metrics.
