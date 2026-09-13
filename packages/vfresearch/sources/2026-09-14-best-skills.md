# Best Skills · 2026-09-14

מקור: https://github.com/LinklyAI/best-skills  
dataDate: **2026-09-13** — זהו ה-dataset החדש ביותר שאומת בזמן הריצה; `data/2026-09-14/rankings` עדיין לא היה קיים.  
מושב: מחקר/אורקסטרציה · Asia/Jerusalem

## קבצים שנקראו

- https://github.com/LinklyAI/best-skills/blob/main/data/2026-09-13/rankings/best-100.csv
- https://github.com/LinklyAI/best-skills/blob/main/data/2026-09-13/rankings/trending-7d.csv
- https://github.com/LinklyAI/best-skills/blob/main/data/2026-09-13/rankings/social-buzz.csv
- https://github.com/LinklyAI/best-skills/blob/main/data/2026-09-13/rankings/top-repos.csv

## Movers רלוונטיים ל-VF

| signal | מצב | החלטה |
|---|---|---|
| `mattpocock/skills` | #2 ב-top-repos | נשאר מקור דפוסים חזק; אין התקנה |
| `improve-codebase-architecture` | #36 ב-best-100; #39 ב-trending-7d; מופיע גם ב-social-buzz | כבר מכוסה בפועל ב-`vfharness/playbooks/agent-architecture-audit.md`; אין embed כפול |
| `codebase-design` | #37 ב-trending-7d | watch בלבד; חופף ל-codebase navigability / ownership שכבר הוטמעו |
| `domain-modeling` | #47 ב-best-100; #31 ב-trending-7d | watch בלבד; אין פער תפעולי שמצדיק שכבה חדשה |
| `archify` | #21 ב-top-repos | watch נשאר; `vfbriefux` כבר מחזיק נתיב diagram קנוני |
| `heygen-com/hyperframes` | #24 ב-top-repos; כמה skills ב-trending-7d | רלוונטי רק בתוך media pipeline שכבר אושר; אין runtime/publisher נוסף |
| Google Agents CLI | #11–17 ב-trending-7d עם קפיצה חדה | דולג — vendor CLI/deploy path נוסף שלא נדרש למשרד |

## בדיקת כיסוי לפני embed

`packages/vfharness/playbooks/agent-architecture-audit.md` כבר מציין במפורש את `mattpocock/skills improve-codebase-architecture` כמקור דפוס ומיישם:

- evidence-first לפני refactor;
- זיהוי ownership/entrypoint עמום, duplicate concepts ו-wide fan-out;
- smallest structural change במקום refactor אסתטי;
- seam/test לפני תזוזה מסוכנת;
- איסור על runtime / report ritual כפול.

לכן האות החזק של היום מאשר כיוון שכבר מוטמע — הוא לא מצדיק מערכת נוספת.

## תוצאה

**`no-embed-existing-coverage`**.

לא נמצא דפוס חדש שמוסיף יכולת מהותית מעבר לפקים הקיימים. `mattpocock` architecture/design נשאר watch פעיל; נפתח embed רק אם יימדד פער אמיתי שה-playbook הקיים לא מכסה.

`earthtojake/text-to-cad` נשאר watch בלבד מהמעבר הקודם. הוא לא שימש היום סיבה להרחבת `vfprod`; אין הוכחה לפער geometry/pre-slice שמצדיק CAD runtime נוסף.

## מה דולג

- self-improving / proactive-agent runtimes — שכבת runtime/cron נוספת; office-learning + vfops כבר מכסים learning.
- Google Agents CLI — vendor scaffold/deploy/observability path נוסף.
- reddit/twitter/social automation — מחוץ למנדט; אין auto-DM/blast.
- duplicate agent orchestration (`stablyai/orca`, Herdr וכדומה) — `vfe2b` lock; אין runtime שני.
- generic image/video generators — לא עוקפים את `expert-media-director`/Canva/Hyperframes pipeline הקיים.

## Validation

- Daily research freshness check: **PASS** on a fresh Windows fallback checkout.
- `scripts/check-all.py`: **BLOCKED/FAIL on fallback checkout**, not PASS. The case-insensitive Windows checkout collides `constitution/TAGS.md` with `constitution/tags.md`; `check-hq-overlay.py` therefore reports missing `#צמיחה-חברתית`, and the broader sensor run did not complete. No claim is made that this Best Skills pass made `check-all` green.

## Timer

`standingForever=true`; `lastPass` הקודם היה 2026-09-12 ולכן refresh היה due ובוצע היום.

`timer: UNPROVEN` — `cursor-subscriptions/list_subscriptions` ו-`subscribe_timer` אינם חשופים בריצה הנוכחית. לא נטען `timer: ok` או `timer: renewed`, ולא נוצרה automation חלופית/כפולה.

## בלוק 05

`best-skills — מעבר 48h בוצע על dataDate 2026-09-13; אין embed חדש כי architecture/design כבר מכוסים ב-agent-architecture-audit. timer verification נשאר UNPROVEN בכלי הנוכחי.`
