# Superpowers v6.3 harness delta — תוכנית יישום

**Goal:** להטמיע ב־vfharness את דפוסי Superpowers v6.3 שמוסיפים אוטונומיה/איכות בלי runtime, pack או control-plane נוסף.
**Architecture:** שינוי כירורגי ב־playbooks ובסולם ההסלמה הקיים. `vf_graceful_escalation.py` נשאר מנגנון הביצוע; playbooks מגדירים preflight, safe rulings, test-first, fresh review ו־parallel fan-out; sensors מוכיחים wiring והתנהגות.
**Spec / אישור:** שיחת המשתמש 2026-09-13 — לאחר סקירת `obra/superpowers`, המשתמש אישר: "תעשה את זה" עבור safe rulings, evidence-bearing preflight, test-first behavioral changes, fresh review ו־parallel dispatch.
**Constraints:** אין runtime שני · אין pack חדש · אין `npx skills` · אין worktree חובה ב־Cloud · אין עקיפה של sensor/receipt/human/constitutional gate · אין merge ל־main מתוך משימה זו ללא מדיניות git הקיימת.

## קבצים (מפת מבנה)

| קובץ | Create / Modify | אחריות |
|---|---|---|
| `packages/vfharness/scripts/vf_graceful_escalation.py` | Modify | rung אופציונלי fail-closed של `safe_ruling` |
| `packages/vfharness/playbooks/executing-plans.md` | Modify | preflight matrix, rulings, parallel dispatch, review |
| `packages/vfharness/playbooks/writing-plans.md` | Modify | Spec כסמכות + producer/consumer metadata |
| `packages/vfharness/playbooks/implementation-discipline.md` | Modify | RED→GREEN→REFACTOR לשינוי התנהגות |
| `packages/vfharness/playbooks/critique-review.md` | Modify | fresh-context light review |
| `packages/vfharness/LOOP.md` | Modify | ladder/ruling semantics במקום binary stop |
| `packages/vfharness/EMBED.md` | Modify | loop wiring מעודכן |
| `packages/vfharness/SKILL.md` | Modify | route/wiring קנוני |
| `docs/AUTONOMY-TOOLS.md` | Modify | תיעוד ladder 5-rung |
| `scripts/check-vfharness-execution-discipline.py` | Create | behavioral proof ל־safe_ruling |
| `scripts/check-skill-pattern-embeds.py` | Modify | structural wiring ל־Superpowers v6.3 delta |
| `packages/vfresearch/sources/2026-09-13-superpowers-v63.md` | Create | provenance + accepted/rejected patterns |
| `CHANGELOG.md` | Modify | Unreleased record |

## Preflight inputs

- Binding authority: ה־Spec/אישור לעיל + `AGENTS.md`/constitution.
- Shared surfaces: `vfharness` execution semantics, `state/`, escalation ladder, skill routing, sensor suite.
- Required final proof: behavioral checker + `python3 scripts/check-all.py` via CI/available runner; no completion claim from docs-only wiring.

### Task 1: Safe ruling rung

**Files:** escalation script + behavioral checker.
**Depends on:** existing ladder API.
**Produces/Consumes:** produces structured ruling receipt consumed by state/loop semantics.
**Verify:** safe ruling succeeds only when explicitly allowed; blocked/malformed ruling escalates.

### Task 2: Plan execution semantics

**Files:** executing-plans, writing-plans, LOOP, EMBED, SKILL.
**Depends on:** Task 1 names/semantics.
**Produces/Consumes:** producer/consumer preflight table, authority-preserving rulings, parallel fan-out/fan-in.
**Verify:** structural sensor requires all canonical phrases/wiring.

### Task 3: Test-first + fresh review

**Files:** implementation-discipline, critique-review, SKILL.
**Depends on:** existing deterministic sensors/review convergence.
**Produces/Consumes:** RED evidence and fresh reviewer packet; high-risk mode unchanged.
**Verify:** structural sensor + full suite.

### Task 4: Provenance + changelog + full verification

**Files:** source note, AUTONOMY-TOOLS, CHANGELOG, checkpoint/progress.
**Verify:** `python3 scripts/check-all.py`; PR CI green before completion claim.
