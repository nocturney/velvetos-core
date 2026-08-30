# Crew: catalog memory

Source patterns: Engramory, MemSearch, Co-Engram, dsh-project-memory, WeKnora (user-managed KB only).
Packs: `vfresearch`, `vfsku`, `vfops`.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Librarian | `vfresearch` | Answer from HQ files with a path citation. | Invent a source |
| SKU clerk | `vfsku` | Recall a card that already exists. | Mint a new SKU |
| Ops memory | `vfops` | Point at a written procedure / CHANGELOG line. | Stand up a memory server |
| Human | — | Approves any new catalog line. | — |

## Run

1. Search this repo first: packs, `CHANGELOG.md`, `constitution/`. Drive only if the user names the job/SKU.
2. Each claim needs a file path or a mail/calendar id. No hit → **חסר**.
3. Do not install OpenViking, WeKnora, EverOS, or MemOS.
4. Write-back (new SKU note, new procedure) only when the user or head of desk asks. One fact per note, Markdown.
5. Stop. Do not upload studio files to a third-party memory API.

## Done when

The answer is a cited list. Uncited lines are removed.
