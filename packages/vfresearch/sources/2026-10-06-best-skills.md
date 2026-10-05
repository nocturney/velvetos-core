# Best Skills · 2026-10-06

מקור: https://github.com/LinklyAI/best-skills · commit `32cd4d1733e9651bff52a27e8976751e4f1ee39b` (`data: 2026-10-05`, 2026-10-05T00:58:07Z)  
CSVs: `data/2026-10-05/rankings/`  
מושב: ייצור · Asia/Jerusalem  
Cadence: `lastPass` על main = 2026-10-02 (~96h, stale מעל 52h) → בוצע בתוך Velvet Research Seat. בלי טיימר שני. בלי `npx skills`.

## Research metadata

- **as_of:** dataDate 2026-10-05 (UTC); נקרא 2026-10-06 ~02:10 Asia/Jerusalem.
- **provenance:** `gh api repos/LinklyAI/best-skills/contents/data/2026-10-05/rankings/*.csv` (best-100, trending-7d, social-buzz, top-repos, rising-stars), בהשוואה ל־`data/2026-10-04` (commit `fcdab075`).
- **uncertainty:** הדירוג משקף ספירות של skills.sh / ClawHub / SkillHub CN וסיגנלים חברתיים; לא נמדד שימוש אצלנו. מעברי 4.10 ו־5.10 (PR #488, #535) לא מוזגו, ולכן `lastPass` על main נשאר 2.10 עד המעבר הזה. ב־top-repos נכנסו כמה repos חדשים בבת אחת (למשל firecrawl, claude-mem); ייתכן שזה שינוי ברשימת המעקב של LinklyAI ולא קפיצה אמיתית.
- **refresh_target:** Research Seat הבא שבו `lastPass` בן 44h לפחות (≈ 2026-10-08).

נקרא:
- https://github.com/LinklyAI/best-skills/blob/main/data/2026-10-05/rankings/best-100.csv
- https://github.com/LinklyAI/best-skills/blob/main/data/2026-10-05/rankings/trending-7d.csv
- https://github.com/LinklyAI/best-skills/blob/main/data/2026-10-05/rankings/social-buzz.csv
- https://github.com/LinklyAI/best-skills/blob/main/data/2026-10-05/rankings/top-repos.csv
- https://github.com/LinklyAI/best-skills/blob/main/data/2026-10-05/rankings/rising-stars.csv

## Movers (VF-relevant)

| # / signal | list | פעולה |
|---|---|---|
| agent-browser #1 · find-skills #2 · frontend-design #3 · grill-me #4 | best-100 | כיסוי קיים; אין embed כפול |
| self-improving-agent #10 (ClawHub, עלה מ־#75) | best-100 | **דולג** — runtime שני נעול; office-learning מכסה |
| setup-matt-pocock-skills #14 (עלה מ־#51) | best-100 | **דולג** — מתקין סקילים; אין npx |
| nano-banana-pro #12 | best-100 | watch קיים מ־5.10; Product Truth קודם |
| ios-design #8 (עלה מ־#15) · ui-taste #1 | trending-7d | **דולג/watch** — אין אפליקציה; ui-taste כבר ב־watch |
| hyperframes-studio / registry / keyframes / audio #20–#23 | trending-7d | **דולג** — hyperframes נשאר `ignore` ב־upstream |
| twitter/reddit-automation | trending-7d | **דולג** — אוטו־פוסט |
| proactive-agent #4 (עלה מ־#9) | social-buzz | **דולג** — runtime שני נעול |
| firecrawl/firecrawl #4 (חדש ברשימה) | top-repos | **watch** — WebFetch/WebSearch מכסים מחקר; אין שירות scraping בתשלום |
| thedotmack/claude-mem #13 (חדש ברשימה) | top-repos | **דולג** — `vfmem` + Cognee מכסים זיכרון |
| ChromeDevTools/chrome-devtools-mcp #26 · HKUDS/CLI-Anything #27 | top-repos | **דולג** — אין פער משרדי |
| obra/superpowers #1 · mattpocock/skills #2 · anthropics/skills #5 | top-repos | partial+ קיים; mattpocock נשאר `review` ב־upstream |
| rising-stars #1–#13 (SkillHub CN, סינית) | rising-stars | **דולג** — לא תחום VF |

## מה הוטמע

- אין embed חדש. מול grill / verification / triage / brainstorm / systematic-debugging / writing-plans / executing-plans / anti-ui-slop / last30 / skill-first לא נמצא פער חדש על snapshot `data/2026-10-05` (`no-embed-existing-coverage`).

## Watchlist

- `firecrawl/firecrawl` — top-repos #4, dataDate 2026-10-05. רק אם WebFetch ייחסם באופן קבוע; לא שירות בתשלום.
- ממשיכים: `steipete/nano-banana-pro`, `steipete/openai-whisper`, `uizze.sh/ui-taste`, `nextlevelbuilder/ui-ux-pro-max-skill`, `affaan-m/ECC`.

## מה דולג

| מה | למה |
|---|---|
| npx skills / ClawHub installs / setup-matt-pocock-skills | אין התקנה; דפוסים בגיט בלבד |
| self-improving-agent / proactive-agent | runtime שני נעול; office-learning מכסה |
| claude-mem | `vfmem` + Cognee קיימים |
| twitter-automation / reddit-automation | אוטו־פוסט |
| ios-design / vercel / prisma skills | לא משרד הדפסה |
| rising-stars SkillHub CN | לא תחום VF |

## בלוק 05

best-skills — מעבר 6.10 על דירוג `data/2026-10-05`; `no-embed-existing-coverage`; stale מ־2.10 על main, בוצע בתוך Research Seat.
