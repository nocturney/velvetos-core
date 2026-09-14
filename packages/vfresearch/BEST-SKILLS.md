# Best Skills — סקירת דירוג כל יומיים

מושב: **מחקר/אורקסטרציה** (`@research-synthesist`) + ראש צוות קורא בבריף.  
מקור חי: [LinklyAI/best-skills](https://github.com/LinklyAI/best-skills) (Top 100, מתעדכן יומית).  
לא פק חדש. לא `npx skills add` על Cloud Agent. דפוסים בלבד על פקים קיימים.

מיומנות: `.cursor/skills/vf-best-skills/SKILL.md`  
מצב: `packages/vfresearch/BEST-SKILLS.json`  
רישום: `LINKS.json` → `linklyai-best-skills`

## למה כל יומיים

הדירוגים זזים כל יום (WIS, trending, social buzz, top repos). מעבר שבועי בלבד מפספס קפיצות.  
**כל ~48 שעות** (Asia/Jerusalem) — **דופק קבוע לנצח** עד שהבעלים מעדכן אחרת (standing order 2026-09-03).

סמכות cadence: **Velvet Research Seat** לפי `packages/vfresearch/TIMER.md`. `lastPass` + artifact הם הראיה; אין תלות במנוי timer חיצוני. חלון grace הוא 4 שעות, כלומר מעל 52h המצב stale.

אירוע Calendar: רק אם ראש צוות מבקש יצירה.

## צעדים (Cursor / Research Seat)

1. לפתוח את הריפו / `data/latest` / README של היום (`gh api` או WebFetch).
2. לקרוא לפחות: `best-100.csv`, `trending-7d.csv`, `social-buzz.csv`, `top-repos.csv`.
3. לסנן ל־**VF-relevant** (משרד סוכנים, מחקר, עיצוב/בריף, למידה, אימות, תוכן/מדיה, גילוי סקילים) — לדלג על Azure/Prisma/SaaS שלא נוגע.
4. להשוות ל־`BEST-SKILLS.json` (`lastPass`, `watchlist`, `embedded`).
5. לכל מועמד חדש / שעלה חזק:
   - **שימושי מיד** → להטמיע **דפוס** על פק קיים. לעדכן `lastReviewed`.
   - **מעניין אבל לא עכשיו** → `watchlist` + שורה בארטיפקט.
   - **מנדט נעול / runtime שני / אוטו־DM / בוסט / Print מ־HQ** → דולג עם סיבה.
6. לכתוב ארטיפקט: `packages/vfresearch/sources/YYYY-MM-DD-best-skills.md`.
7. לעדכן `BEST-SKILLS.json` (`lastPass`, `dataDate`, `lastArtifact`, `lastResult`).
8. שורת בלוק `05-משרד`: «best-skills — הוטמע X» או «best-skills — אין חדש במשרד».
9. אחרי שינוי קטלוג/כלל/פק: `python3 scripts/check-all.py`.
10. לאמת שה־artifact וה־state תואמים. אם `lastPass` ישן מ־52 שעות, Research Seat חייב לבצע מעבר או לרשום blocker אמיתי. אין timer receipt מומצא.

## מיפוי — לא פק כפול

| סוג סקיל / ריפו | נופל ל־ | לא |
|---|---|---|
| גילוי סקילים / leaderboard | `vfresearch` + skill זה | התקנת `npx skills` על Cloud |
| grill / שאלות לפני תוכנית | `vfconvert` · `vfmakers` decide | שליחה ללקוח |
| handoff בין סשנים | `vfharness` templates | מסמך זמני מחוץ לגיט בלבד |
| verification לפני «סיימתי» | `vfharness` playbooks + סנסורים | LLM-as-judge |
| skill-creator / writing-skills | `vfharness` · skills ב־`.cursor/skills/` | פק סקילים חדש |
| self-improving / learning | `office-learning` · `vfops` retro · `owner-memory` | `~/self-improving/` runtime |
| last30days / מחקר רשת | `vfresearch` · `hq/LAST30.md` · skill `vf-last30` · WebSearch / `gh` / תזמורת | TikTok/X keys · auto-DM · `npx skills` / CLI על Cloud |
| market-research / intel gates | `vfresearch` · `hq/MARKET-INTEL.md` | npx install · תיקיית משקיע כברירת מחדל · ₪ מומצא |
| academic research / lit-review / fact-check | `vfresearch` · `hq/ACADEMIC-PIPELINE.md` | Claude plugin · AI Scientist runtime · פק אקדמי חדש |
| data viz / HTML charts | `vfbriefux` · `hq/CHARTS.md` | npx lieflat · Insights מומצאים · החלפת MAIL.html |
| tutor / mastery / lifelong memory | `office-learning` · `vfops/hq/MASTERY-MEMORY.md` | DeepTutor install · EduHub |
| frontend-design / anti-slop | `vfbriefux` · `vfcovers` · קונסולה פנימית | אתר שיווקי ציבורי מ־HQ |
| proposal-drafter / no-fabricate quote | `vfsales` · `vfconvert` · inquiry chain | ₪ מומצא · cold email |
| agent-browser / browser-use | computerUse / בדיקות ידניות | בוט לקוח |
| Remotion / video gen vendor | `vfom` · `expert-media-director` | Veo/Kling מ־HQ · Remotion vendor |
| orchestrator / swarm / OpenClaw | `vfe2b` LOCK | runtime שני |
| social-media-publisher / SocialClaw | `vfigos` SEND + `vfmcp` GAP (דפוס validate→verify) | `npx socialclaw` · blast רב-פלטפורמי · API key בגיט |

## מה מותר לפתוח (חוקה)

הבעלים אישר: אפשר **לעדכן חוקה** ולפתוח מגבלות כשהדירוג חושף דפוס עמיד שמשפר את המשרד — כל עוד:

- אין אוטו־DM / בוסט בלי ראש צוות / Print מ־HQ / ₪ או Insights מומצאים.
- אין התקנת runtime שני / `npx skills` על Cloud Agent; מטמיעים דפוס בגיט.
- CTA ציבורי תמיד נגזר מהסמכות הנוכחית `constitution/PUBLIC_CTA.md`; אין להעתיק CTA היסטורי מארטיפקטים ישנים.
- אתר שיווקי ציבורי נשאר נעול; קונסולה פנימית מותרת.

## חומות

| מצב | מה עושים |
|---|---|
| CSV / GitHub down | WebFetch README · «אין גוף» · failover לתזמורת · לא ממציאים דירוג |
| סקיל דורש API key / vendor lock | watchlist או דפוס בלי המפתח |
| הצעת אוטו־DM / בוסט / אתר מ־HQ | דולג — מנדט |
| אין שינוי מול `lastPass` | ארטיפקט קצר + «אין חדש במשרד» |

## תבנית ארטיפקט

```markdown
# Best Skills · YYYY-MM-DD

מקור: LinklyAI/best-skills · dataDate: YYYY-MM-DD
מושב: ייצור · Asia/Jerusalem

## Movers (VF-relevant)

| # | skill/repo | list | פעולה |
|---|---|---|---|
| … | … | best-100 / trending / buzz / repos | הוטמע / watch / דולג |

## מה הוטמע

- …

## Watchlist

- …

## מה דולג

| מה | למה |
|---|---|

## בלוק 05

…
```

## לא כאן

- סקירת `LINKS.json` השבועית (`WEEKLY.md`) — נשארת; זה מעבר נוסף לדירוג החי.
- Research Seat הוא הסמכות הקבועה; אין automation/timer שני עבור Best Skills.
- שליחת IG/Gmail/WhatsApp אינה חלק מהמעבר, למעט delivery paths שכבר מורשים בנפרד.
