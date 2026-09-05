# מארח המנויים · המק בשדרות

לא פק חדש. פק `vfmcp`.  
חוק: **מנוי Plus/Pro חי רק על מכונה אחת עם IP ביתי קבוע.**  
Cloud Agent ו־Grok Bot **לא** מתחברים ל־`chatgpt.com` / `gemini.google.com` / `perplexity.ai`.

בלי חיוב API נפרד (בעלים 5.9.2026). Hub: [`SUBSCRIPTIONS.md`](SUBSCRIPTIONS.md).

## מה «מלא וקבוע» אומר כאן

| שכבה | מה מקבלים | איפה |
|---|---|---|
| אפליקציות הדפדפן | Gems, GPTs, Canvas, Deep Research, Perplexity Pro / Collections | Chrome במק — פרופיל אחד שנשאר מחובר |
| CLI רשמי בלי מפתח API | Gemini CLI = Login with Google (מנוי Google AI). Codex CLI = `codex login` (ChatGPT Plus) | טרמינל במק בלבד |
| Perplexity לסוכן | אין CLI רשמי למנוי. כרום, או `perplexity-user-mcp` **רק במק** אחרי ראש צוות | לא Cloud |
| Cloud Agent | Gmail / Drive / Canva / git / `WebSearch` | לא אתרי מנוי |

Gemini CLI ו־Codex **לא** מחליפים את Gems/GPTs/Canvas של האתר. «מלא» לאפליקציה = כרום. «קבוע» לסוכן מקומי = OAuth על המק, לא העתקת טוקן לענן.

## אחרי שהתקנת Chrome במק

Cloud Agent על VM של Cursor **לא** מקבל גישה לכרום שלך. אין שיתוף מרחוק, אין remote-debugging, אין העתקת עוגיות.  
כדי שסוכן עתידי ייכנס לאתרים **מזוהה במנוי, מ־IP ביתי**: הכלים רצים **על המק** (`agent worker --computer-use`).

### א. כרום — שלושה לוגין, פרופיל אחד

1. פתח Chrome. אופציונלי: פרופיל בשם `VF-research` (תמונה → Add).
2. הישאר מחובר באתרים (לא מספיק «התקנתי כרום»):
   - https://chatgpt.com — חשבון Plus
   - https://gemini.google.com — אותו Google של המנוי
   - https://www.perplexity.ai — Pro
3. בדוק תג Plus/Pro בכל טאב. סגור בלי Log out.
4. אל תפתח את שלושת האתרים מדפדפן Cloud / Grok Bot.

### ב. CLI רשמי (בלי מפתח API) — אותו מק

```bash
gemini          # Login with Google
codex login     # ChatGPT Plus
```

### ג. Worker — כדי שסוכן Cloud יריץ כלים אצלך

המק דולק, התהליך רץ. אין פורט נכנס, אין ngrok.

```bash
curl https://cursor.com/install -fsS | bash
agent login
cd /path/to/velvetos-core   # הקלונים המקומי
agent worker --computer-use --name "sderot-mac" start
```

בפעם הראשונה ב־macOS: System Settings → Privacy & Security → Accessibility **ו־** Screen Recording ל־**Cursor Computer Use**.

ב־cursor.com/agents: בחר את המכונה `sderot-mac` (לא VM הענן).  
אין worker מחובר עכשיו — עד שזה רץ, השיחה הזו נשארת על VM בלי הכרום שלך.

### ד. מה לא לעשות

- Chrome remote debugging / שיתוף מסך / מנהרה לכרום
- להעתיק עוגיות או `~/.codex` / `~/.gemini` ל־Cloud
- `npx perplexity-user-mcp` בענן

## כל בוקר 06:15
| מי רץ | מה עושים |
|---|---|
| **Cursor Desktop במק** | שלושת השולחנות במנוי (כרום ו/או Codex + Gemini CLI). תבנית `vfresearch/DAILY.md`. מטמיעים בפק קיים. |
| **Cloud Agent** | לא פותח אתרי מנוי. קורא `sources/` אם יש. אחרת `WebSearch` / `WebFetch`. בלי מפתח: «חסר מפתח Gemini» / «חסר מפתח ChatGPT» — לא ממציאים גוף. |

`constitution/ORCHESTRA.md`.

## אופציונלי — worker בלי computer-use

`agent worker start` בלי `--computer-use`: טרמינל + קבצים במק, בלי לחיצות בכרום. עדיין Codex / Gemini CLI בטרמינל המקומי.

## אסור

- לוגין מ־Cloud / Grok לאתרי המנוי
- עוגיות / patchright / העתקת vault
- `npx perplexity-user-mcp` ב־Cloud
- Gemini CLI / Codex headless בענן (שם בדרך כלל דורשים מפתח API או לוגין זר)
