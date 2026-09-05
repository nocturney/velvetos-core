# Owner memory — זיכרון משותף

שורות קצרות שכל המושבים קוראים בבוקר (בריף / פתיחת שיחה).  
עדכון: `MEMORY-UPDATE.md` · רטרו יומי: `hq/DAILY-RETRO.md` · רטרו ראשוני: `hq/INITIAL-RETRO.md` · אינדקס תוצרים: `ARTIFACT-INDEX.md`.

---

## רטרו ראשוני (catch-up) — 2026-09-01

סיכום ממה שנשמר בגיט **לפני** שהרוטינה היומית הייתה קיימת. מקורות: CHANGELOG, checkpoints, חוקה, בקשות בעלים.

### בעלים — העדפות שחוזרות

- **משרד חי:** סוכנים מומחים שלומדים ומשתפרים — לא פרומפטים סטטיים גנריים.
- **רטרו:** כל סוף יום על שיחות; עכשיו גם catch-up על כל מה שלפני.
- **ארבעה תחומי מומחה:** Social Booster · 3D model · Trend explorer · Media director (תמונות/וידאו).
- **שפה:** עברית לקופי מוצר; מסמכי משרד עברית+אנגלית.
- **CTA:** וואטסאפ `050-2517000` / איסוף שדרות — לא «שלחו DM».

### ראש צוות (lead)

- **למדנו:** Core = backend; VF frontend = `instances/velvet-factory` → `velvetos-velvet-factory` עם `attach-core.sh`.
- **למדנו:** HQ **שולח** Gmail ו-IG דרך כלים (`SEND.md`) — לא מחכים ל-Grok/כריסטיאן; Grok גיבוי אופציונלי.
- **למדנו:** בריף 07:00 **לא** קורא תיבת דואר — לוח + vfops בלבד; שליחה ב-`htmlBody` תצוגה 3.
- **למדנו:** Treg לא רלוונטי; כלי נפל → failover מיד (`ORCHESTRA.md`).
- **פתוח:** `grok-failover` checkpoint עדיין `running` — בריף יומי + LIVE-PACKET לפרסום חי דחוף.
- **פתוח:** פרסום ריפו `velvetos-velvet-factory` — הריפו קיים אצל הבעלים; טוקן Cloud Agent חסום → `PUSH=1` מקומי או הרשאה לאינטגרציה.
- **מקור:** checkpoints 2026-08-30..31, CHANGELOG, AGENTS.md.

### סטודיו (inquiry / quote)

- **למדנו:** צינור אחד: פנייה → שיחה → הצעה → הדפסה → איסוף; אין משלוח ארצי מ-HQ.
- **למדנו:** ₪ רק ממקור מאומת — אחרת `X ₪` / «אין ספירה».
- **למדנו:** dedup פניות — `vfconvert/hq/DEDUP.md` (דפוס Huginn).
- **מקור:** constitution, vfconvert, checkpoint huginn-embed.

### צמיחה (content / IG)

- **למדנו:** תוכן מרצפת הוכחה — לא סצנות מומצאות; Canva ראשון ל-IG.
- **למדנו:** מוזיקה לריל מ-HeyOrca / IG paste — לא שמות שירים מומצאים (`MUSIC.md`).
- **למדנו:** אין בוסט / אוטו-DM / TikTok בלי ראש צוות.
- **למדנו (חדש):** Social Booster = `expert-social-booster` + `@carousel-growth-engine`; Media director = `vfom/experts/MEDIA-DIRECTOR.md`.
- **מקור:** vfgrowth PLAYBOOK, vfcanva, expert modules 2026-09-01.

### תפעול (ops / books)

- **למדנו:** חשבונות מ-Gmail label חשבונות; לא לרדוף חוב בלי ראש צוות.
- **למדנו:** קונסולת משרד פנימית מותרת; אתר שיווקי ציבורי מ-HQ נשאר נעול (`OFFICE-OS-EMBED-he.md`).
- **מקור:** vfbooks, office-os checkpoint.

### ייצור (print / 3D)

- **למדנו:** אין הדפסה מ-HQ; תור ושעות מסלייסר — לא מניחוש.
- **למדנו:** 3D AI Studio אחרי אישור lead; MCP `threedaistudio` — OAuth בדסקטופ/Cloud נפרד (`CONNECT-3DAI.md`).
- **למדנו (חדש):** מומחה mesh = `expert-3d-model` + `@technical-artist`; רישיון לפני reprint (`#vlicense`).
- **מקור:** vfprod, checkpoint 3daistudio-embed.

### מחקר / מגמות

- **למדנו:** סקירת קישורים שבועית — `WEEKLY.md` + `LINKS.json` (47 רשומות).
- **למדנו (חדש):** Trend explorer = `expert-trend-explorer`; WebSearch בלבד.
- **מקור:** vfresearch checkpoints weekly-links, ig-music.

### אנטי-דפוסים שלא חוזרים (מ-AGENTS.md)

- המצאת ₪ / Insights · המתנה לשליחה כשיש כלי · פק חדש לכל רעיון · orchestrator שני · Treg · auto-DM · boost בלי lead.

---

### 2026-09-01 (revenue loop)
- **מושב:** lead + growth
- **למדנו:** IG כפרנסה = לולאה סגורה (Offer → פנייה → הצעה → איסוף → retention → snapshot).
- **מחר:** כל פוסט מסחרי עם כרטיס Offer; שבועי `WEEKLY-REVENUE-PULSE.md`.
- **מקור:** expert-revenue-loop embed.
- **מושב:** lead
- **למדנו:** המשרד הוא צוות חי — כל מומחה (`expert-*`) עושה רטרו יומי ומעדכן זיכרון משותף; לא פרומפט סטטי.
- **למדנו:** רטרו ראשוני הושלם מ-CHANGELOG + checkpoints — מחרתיים רק DAILY-RETRO.
- **מחר:** רטרו קצר בסוף כל יום עבודה; בריף קורא בלוק זיכרון (חריץ 05a).
- **מקור:** בקשת בעלים + INITIAL-RETRO 2026-09-01.

### 2026-09-01 (ops — publish + snapshot + pulse)
- **מושב:** lead + ops
- **למדנו:** snapshot ראשון ב־`vfinsights/sources/2026-09-01-ig-snapshot.md` — רק refs מאומתים; מטריקות עדיין «אין ספירה».
- **למדנו:** דופק W35 ב־`vfops/hq/revenue-pulse-2026-W35.md` — צינור 0, G005 מתוכנן 3.9.
- **פתוח:** push ל־`velvetos-velvet-factory` — טוקן Cloud Agent לא רואה הריפו; להריץ מקומית `PUSH=1 ./scripts/publish-instance.sh velvet-factory nocturney/velvetos-velvet-factory` או לתת גישה לאינטגרציה.
- **מחר:** אחרי G005 — הדבקת מטריקות ל־`snapshot-ingest.md`.
- **מקור:** ops run 2026-09-01.

### 2026-09-02 (מחקר יומי — מדף מק״ט)
- **מושב:** ייצור
- **למדנו:** מדף 5 מק״ט חי ב־`vfsku/SHELF.json`. כרטיס רק אחרי רישיון בדף + סלייס + הדפסת ניסיון (`FIRST-PRINT.md`). הורדה ≠ רישיון מסחרי.
- **מחר:** בעלים נותן קישור לדגם אחד → שעה למשבצת 1. בלי שם מהאוויר.
- **מקור:** תזמורת 2026-09-02.

### 2026-09-03 (best-skills bi-daily)
- **מושב:** ייצור + lead
- **למדנו:** בעלים רוצה סריקת [LinklyAI/best-skills](https://github.com/LinklyAI/best-skills) **כל יומיים** + ראש פתוח לעדכון חוקה כשדפוס עמיד מנצח.
- **למדנו:** grill לפני הצעה מורכבת; אין טענת הצלחה בלי סנסור/ראיה; אין `npx skills` על Cloud.
- **למדנו:** דופק **קבוע לנצח** עד הודעה מפורשת לעצור — `standingForever: true` + חידוש טיימר בכל מעבר (`TIMER.md`).
- **מחר:** טיימר bi-daily רץ ומתחדש; watchlist (superpowers, anti-ui-slop, media-gen).
- **מקור:** בקשת בעלים + `sources/2026-09-03-best-skills.md` + `TIMER.md`.

### 2026-09-04 (best-skills pulse)
- **מושב:** ייצור
- **למדנו:** skill-first לפני פעולה; שיעורים עמוקים → `LEARNING-RECORDS.md`. Upstream יכול להישאר על dataDate אתמול — עדיין רצים ומחדשים טיימר.
- **מחר:** לעקוב archify / OpenSpec; לא להעתיק impeccable palette.
- **מקור:** `sources/2026-09-04-best-skills.md`.

### 2026-09-05 (לוח פרסום קבוע)
- **מושב:** צמיחה
- **למדנו:** קצב נעול — ריל א׳/ג׳ 16:00, קרוסלה ה׳ 12:00, סטוריז א׳–ה׳ 20:30, אין פיד ו׳–ש׳, ≥36ש בין פיד. שיבוץ ב־instagram.com לא סוויט. G001+G002+G005 חיים. G003 = SoccerBall ריל #3 (חסום מדיה).
- **מחר:** לא לשאול «מה לפרסם?» — למלא לדג׳ר ואז לשבץ לפי `vfgrowth/CALENDAR.md`.
- **מקור:** כריסטיאן 5.9 ~11:10 + `LEDGER.md`.

### 2026-09-05 (G003 עצירה)
- **מושב:** צמיחה
- **למדנו:** מועמד G003 = `media/SoccerBall final_PLA_9h55m_20260715143622.mp4` + הוק «מכדור דיגיטלי למוצר שאפשר להחזיק». הקובץ לא נגיש מ־Cloud HQ (אין מראת iCloud ב־Drive). לא מחליפים ב־G001 king / G002 RoboLotl. בלי mp4 — אין שיבוץ.
- **מחר:** סטודיו על המק מוצא את הקובץ ב־`media/` או מעלה ל־Drive, ואז משבץ א׳ 7.9 16:00 / נפילה ג׳ 9.9 16:00.
- **מקור:** כריסטיאן 5.9 ~11:21 + חיפוש Drive/Canva/3DAI.

### 2026-09-05 (G003 שיבוץ + G003-alt)
- **מושב:** צמיחה
- **למדנו:** SoccerBall לא בעץ GitHub HQ. על מחשב Grok הגלם היחיד תחת `/workspace/INSTA/media` הוא `vf-user-2026-08-30.mp4` + `vf-user-2026-08-30-9x16.mp4` (+ stills). שני מסלולים: A SoccerBall אם iCloud מצא; B ריל מדפסת בלי לטעון «כדור». משבצת א׳ 7.9 16:00 משוחררת **כשיש mp4**. HQ לא חותך.
- **מחר:** סטודיו מרכיב, מדביק כיתוב תואם, משבץ instagram.com. בלי Meta Suite.
- **מקור:** עדכון כריסטיאן/סטודיו 5.9 — SoccerBall לא בגיט; הרכבה מהגלם שאושר.

### 2026-09-05 (ספריית תהליך על Grok)
- **מושב:** צמיחה
- **למדנו:** אחרי סנכרון, SoccerBall `…9h55m_20260715143622.mp4` זמין מקומית תחת `/workspace/INSTA/media/` — לא בגיט. G003 נשאר משובץ עם ריל המדפסת וכיתוב «מה יוצא מהמדפסת?» עד שכריסטיאן מאשר חיתוך מחדש. king שסונכרן הוא `22h32m` (18–19.8), לא השם `22h10m` שתועד ל־G001.
- **מחר:** לא להעלות mp4 לריפו. RoboLotl/king לא לריל חדש. Octopus/SeaTurtle = מועמדים אחרי G003.
- **מקור:** סנכרון מדיה כריסטיאן 5.9.

### 2026-09-05 (G003-alt כיתוב)
- **מושב:** סטודיו / צמיחה
- **למדנו:** פתיחה «מהמיטה יוצא משהו» נפסלה: «מיטה» סלנג רצפה, «משהו» לא פרימיום. כיתוב ריל תהליך = מה שעל המסך / שאלת הסדרה, CTA כמו G005 (`להזמנה וואטסאפ` + איסוף). בלי מגבלות בפתיחה.
- **מחר:** להדביק את בלוק `vfcopy/G003-alt.md` ולהחליף `VF-G003-caption.txt` על מחשב Grok. לא לגעת ב־mp4.
- **מקור:** החלטת כריסטיאן 5.9 + reader-first / ai-tells + קול G005.

### 2026-09-05 (G003-alt חבילה חתוכה)
- **מושב:** צמיחה
- **למדנו:** סטודיו חתך G003-alt: `VF-G003-reel.mp4` + `VF-G003-cover.jpg` + `VF-G003-caption.txt` תחת `/workspace/INSTA/content/2026-09-07/`. 1080×1920 ~9.6ש מקליפ מדפסת. SoccerBall / king / RoboLotl מקורות לא על פרוסת הדיסק. #משובץ א׳ 7.9 16:00. לא עלה לפיד.
- **מחר:** לשבץ ב־instagram.com מהחבילה. SoccerBall רק אם מופיע + ראש צוות.
- **מקור:** כריסטיאן — ספרייה מקומית iCloud Drive/INSTA על מחשב Grok.

### 2026-09-05 (קישורי בעלים ×4)
- **מושב:** ייצור
- **למדנו:** DeepTutor/lieflat/academic → דפוסים על packs קיימים; ExamFul = watch לאנכי חינוך עתידי, לא צינור VF.
- **מחר:** להשתמש ב־`ACADEMIC-PIPELINE` / `CHARTS` / `MASTERY-MEMORY` במחקר ובריף; בלי להתקין vendor.
- **מקור:** `sources/2026-09-05-weekly-links-owner-four.md`.
