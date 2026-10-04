# Best Skills · 2026-10-05

מקור: https://github.com/LinklyAI/best-skills · README Last updated **2026-10-04** (UTC) · commit `fcdab075666a2332fcfc6ff6fd70584d2fa7eddf` (`data: 2026-10-04`, 2026-10-04T01:00:47Z)  
דף חי: https://linkly.ai/skills  
CSVs: `data/2026-10-04/rankings/`  
מושב: ייצור · Asia/Jerusalem  
Cadence: `lastPass` על main = 2026-10-02 (~72h, stale מעל 52h) → בוצע בתוך Velvet Research Seat. בלי טיימר שני. בלי `npx skills`.

## Research metadata

- **as_of:** dataDate 2026-10-04 (UTC); נקרא 2026-10-05 ~02:40 Asia/Jerusalem.
- **provenance:** `gh api repos/LinklyAI/best-skills/contents/data/2026-10-04/rankings/*.csv` + README + WebFetch של https://linkly.ai/skills (Top 100 תואם ל־best-100.csv).
- **uncertainty:** הדירוג משקף ספירות של skills.sh / ClawHub / SkillHub CN וסיגנלים חברתיים; לא נמדד שימוש אצלנו. מעבר 4.10 (PR #488) לא מוזג, ולכן `lastPass` על main נשאר 2.10 עד המעבר הזה.
- **refresh_target:** Research Seat הבא שבו `lastPass` בן 44h לפחות (≈ 2026-10-07).

נקרא:
- https://github.com/LinklyAI/best-skills/blob/main/data/2026-10-04/rankings/best-100.csv
- https://github.com/LinklyAI/best-skills/blob/main/data/2026-10-04/rankings/trending-7d.csv
- https://github.com/LinklyAI/best-skills/blob/main/data/2026-10-04/rankings/social-buzz.csv
- https://github.com/LinklyAI/best-skills/blob/main/data/2026-10-04/rankings/top-repos.csv
- https://github.com/LinklyAI/best-skills/blob/main/data/2026-10-04/rankings/rising-stars.csv

## Movers (VF-relevant)

| # / signal | list | פעולה |
|---|---|---|
| agent-browser #1 WIS 81 · find-skills #2 · frontend-design #3 · grill-me #4 | best-100 | כיסוי קיים; אין embed כפול |
| vercel-react-best-practices #5 · web-design-guidelines #6 | best-100 | **דולג** — לא משרד הדפסה |
| remotion-best-practices #7 | best-100 | **watch/דולג** — `vfom` ממפה; אין ספק Remotion מ־HQ |
| code-review #8 · skill-creator #9 | best-100 | כיסוי ב־`vfharness` (critique-review, skill-authoring) |
| nano-banana-pro #10 (ClawHub, חדש בעשירייה) | best-100 | **watch מדיה בלבד** — עריכת תמונה ב־AI נשארת מאחורי Product Truth («Retouch the photo, not the product») ו־expert-media-director; אין התקנה |
| grill-with-docs #11 | best-100 | grill כבר מוטמע (`vfconvert/hq/GRILL.md`) |
| ui-taste #1 · ai-image/video/avatar #2–#4 | trending-7d | watch קיים מ־4.10; בלי npx |
| twitter-automation #5 · reddit-automation #7 | trending-7d | **דולג** — אוטו־פוסט מחוץ ל־CTA |
| design-mobile-apps #6 | trending-7d | **דולג** — אין אפליקציה |
| media-use (heygen hyperframes) #12 | trending-7d | **דולג** — hyperframes נשאר `ignore` ב־upstream |
| agent-browser #1 · grill-me #2 · code-review #4 · skill-creator #5 | social-buzz | כבר מוטמע / כיסוי |
| self-improving #3 · proactive-agent #9 · self-improving-agent #10 | social-buzz | office-learning; **runtime שני נעול** |
| openai-whisper #12 | social-buzz | **watch** — תמלול מקומי בלי מפתח; אין צורך פעיל |
| obra/superpowers #1 · mattpocock/skills #2 · anthropics/skills #4 | top-repos | partial+ קיים; mattpocock נשאר `review` ב־upstream (v1.3.1) |
| affaan-m/ECC #3 · ponytail #5 · ui-ux-pro-max-skill #7 | top-repos | watch קיים מ־4.10 |
| JuliusBrussee/caveman #10 · addyosmani/agent-skills #11 · Leonxlnx/taste-skill #12 | top-repos | **דולג** — אין פער משרדי |
| rising-stars #1–#12 (SkillHub CN, סינית: הורות, כתיבת מאמרים, חותמת דיגיטלית, כרזות) | rising-stars | **דולג** — לא תחום VF |

## מה הוטמע

- אין embed חדש. מול grill / verification / triage / brainstorm / systematic-debugging / writing-plans / executing-plans / anti-ui-slop / last30 / skill-first לא נמצא פער חדש על snapshot `data/2026-10-04` (`no-embed-existing-coverage`).
- watchlist: הערה ל־`nano-banana-pro` (best-100 #10) ול־`openai-whisper` (social-buzz #12).

## Watchlist

- `steipete/nano-banana-pro` — best-100 #10, dataDate 2026-10-04. עריכת תמונה ב־AI; מותר רק כ־retouch ולא כהחלפת מוצר.
- `steipete/openai-whisper` — social-buzz #12. תמלול מקומי.
- ממשיכים מ־4.10: `uizze.sh/ui-taste`, `nextlevelbuilder/ui-ux-pro-max-skill`, `affaan-m/ECC`.

## מה דולג

| מה | למה |
|---|---|
| npx skills / ClawHub installs | אין התקנה; דפוסים בגיט בלבד |
| vercel / prisma / azure / supabase skills | לא משרד הדפסה |
| twitter-automation / reddit-automation | אוטו־פוסט |
| self-improving / proactive-agent | runtime שני נעול; office-learning מכסה |
| rising-stars SkillHub CN | לא תחום VF |

## בלוק 05

best-skills — מעבר 5.10 על דירוג `data/2026-10-04`; `no-embed-existing-coverage`; stale מ־2.10 על main, בוצע בתוך Research Seat.
