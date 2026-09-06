# SKILLSTATE embed · 2026-09-05

מושב: ייצור (`@research-synthesist`) → ראש צוות (`@workflow-architect` / vfharness)  
מקור: https://arxiv.org/abs/2608.26263 · HTML https://arxiv.org/html/2608.26263  
כותרת: *SKILLSTATE: Scalable Long-Horizon Agent Skills* (Badhe, Tiwari, Chung)

## תקציר (מה שקראנו)

ראנטיים של כישורי סוכן ארוכים נכשלים כשממשיכים לצרף reasoning + actions + observations להיסטוריית שיחה (\(O(T^2)\) טוקנים).  
SKILLSTATE מחליף את זה במצב ביצוע מפורש: בכל צעד המודל מקבל רק \(A_t=(P,\Sigma_t,O_t)\) — מפרט כישור קבוע, מצב מובנה נוכחי, ותצפית אחרונה. אחרי עדכון מצב מאומת זורקים את ה-reasoning. תוצאה מדווחת: דיוק דומה/טוב יותר + צריכת טוקנים נמוכה בהרבה.

## פסיקה

`embed` על `vfharness` (Memory + Loop). **לא** runtime שני. **לא** LangGraph / SkillExecBench.

## מה הוטמע

| קובץ | שינוי |
|---|---|
| `vfharness/playbooks/skillstate.md` | פלייבוק מיפוי |
| `vfharness/EMBED.md` · `LOOP.md` · `LAYERS.md` · `SKILL.md` | מחזור \(P,\Sigma,O\) |
| `templates/checkpoint.schema.json` | שדות אופציונליים `execution_state` · `latest_observation` |
| `scripts/check-vfharness.py` | קיום הפלייבוק + מחטים |
| `AGENTS.md` MEMORY | חוק הצגת מצב במקום replay |
| `docs/HARNESS.md` | שורת מקור |
| `vfresearch/LINKS.json` | רישום arxiv-skillstate |
| `layers.json` | קובץ בפלייבוק בשכבת memory |

## מה דולג

| מה | למה |
|---|---|
| SkillExecBench / InterCode CTF harness | לא מנדט משרד; אין CTF ממשרד |
| LangGraph / stateful agent framework | נעילת runtime שני |
| Schema לכל משימה | אצלנו schema אחד לדומיין (`checkpoint.schema.json`) |

## קשר לדפוסים קיימים

- `context-thrift.md` — דחיסת פלט כלי  
- `skillstate.md` — מצע הביצוע הוא Σ, לא הצ'אט  
- `oma-patterns.md` + DeerFlow compaction — gate / planned_steps / resume מ-checkpoint

## בלוק 05

שבועי קישורים — הוטמע SKILLSTATE ב־`vfharness`
