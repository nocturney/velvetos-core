# Crew: studio brain

Source pattern: [makerskills `company-brain`](https://github.com/coreyhaines31/makerskills/blob/main/skills/company-brain/SKILL.md) — capture / query / review with trust tags. **No second vault.**
Packs: `vfcopy`, `vfsales`, `vfconvert`, `vfbiz`, `vfresearch`. Memory = this repo.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Capture | existing `hq/` | Append + stamp trust | Open unnamed personal Drive folders |
| Query | HQ + CHANGELOG | Answer with paths | Invent citations |
| Review | lead seat | verify / deprecate / supersede | Delete history |

## Where things live (do not invent a parallel wiki)

| Content | File |
|---|---|
| Verbatim customer phrases | `packages/vfcopy/hq/customer-language.md` |
| Sales objections + replies | `packages/vfsales/hq/objections.md` |
| Recurring intake questions | `packages/vfconvert/hq/PLAYBOOK.md` (append a FAQ block) |
| Lead-seat calls | `packages/vfbiz/hq/decisions/` via `crews/decide.md` |
| Walls we already broke | `packages/vfops/hq/walls/` via `crews/unstuck.md` |
| External gaps | `vfresearch` — source or **חסר** |

Reserved: do not rewrite `constitution/` from this crew. Do not create `people/` dossiers of private contacts in git.

## Capture stamp

Every new block starts:

```markdown
source: <thread / call / floor / URL>
author: <seat or handle>
captured: YYYY-MM-DD
trust: unreviewed
sensitivity: internal
```

`sensitivity: confidential` — do not commit. Keep it in the chat and tell the human.

## Modes

| Ask | Mode |
|---|---|
| brain capture / תפוס | **capture** |
| brain query / מה אנחנו יודעים | **query** |
| brain review / נקה | **review** — walk `trust: unreviewed` |

## Query rules

1. Prefer `verified` over `unreviewed`. Never use `deprecated` as fact.
2. If the answer leans on unreviewed notes, say **ביטחון נמוך** first.
3. Missing source → **חסר**. Do not fill from training data.
4. ₪ and Insights stay locked unless the cited file already has them.

## Review dispositions

- **verify**
- **deprecate** (keep the file, drop from context)
- **supersede** + pointer
- **skip**

## Done when

The capture has a path, or the query lists the files it used, or the review queue moved. No secrets in git.
