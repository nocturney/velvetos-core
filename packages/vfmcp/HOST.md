# מארח המנויים · המק בשדרות

לא פק חדש. פק `vfmcp`.  
חוק: **מנוי Plus/Pro חי רק על מכונה אחת עם IP ביתי קבוע.**  
Cloud Agent **על VM מנוהל** ו־Grok Bot **לא** מתחברים ל־`chatgpt.com` / `gemini.google.com` / `perplexity.ai`.  
סוכן שכליו רצים על המק (`agent worker --computer-use`) נכנס בכרום המקומי — זה ה־IP הביתי, לא חווה.

בלי חיוב API נפרד (בעלים 5.9.2026). Hub: [`SUBSCRIPTIONS.md`](SUBSCRIPTIONS.md).

## מק ייעודי — לא ה-PC ווינדוס

בעלים 5.9.2026: יש מחשב ווינדוס ליום-יום, ו**מק ייעודי** למנויים + worker. המארח הוא המק בשדרות — לא הווינדוס.

לוגין בכרום בווינדוס **לא** עובר למק. לא מעתיקים עוגיות / פרופיל בין המחשבים. מתחברים מחדש בכרום **על המק**.

`--computer-use` רשמי של Cursor: **macOS ו-Linux בלבד**. ווינדוס native לא מפעיל לחיצות בכרום — לכן המק הייעודי הוא הבחירה הנכונה.

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

### א. כרום — שלושה לוגין **על המק הייעודי**

לוגין שעשית בווינדוס לא נספר. פתח Chrome **במק**. אופציונלי: פרופיל בשם `VF-research` (תמונה → Add).

1. הישאר מחובר באתרים (לא מספיק «התקנתי כרום»):
   - https://chatgpt.com — חשבון Plus
   - https://gemini.google.com — אותו Google של המנוי
   - https://www.perplexity.ai — Pro
2. בדוק תג Plus/Pro בכל טאב. סגור בלי Log out.
3. אל תפתח את שלושת האתרים מדפדפן Cloud / Grok Bot.

### ב. CLI רשמי (בלי מפתח API) — אותו מק

```bash
gemini          # Login with Google
codex login     # ChatGPT Plus
```

### ג. Worker — כדי שסוכן Cloud יריץ כלים אצלך

המק דולק, התהליך רץ. אין פורט נכנס, אין ngrok.

```bash
curl https://cursor.com/install -fsS | bash

# zsh במק לא רואה ~/.local/bin עד שמוסיפים ל-PATH:
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

which agent          # אמור להדפיס .../.local/bin/agent
agent --version
agent login
```

חלון דפדפן = לוגין ל־**חשבון Cursor** (לא ChatGPT/Gemini). אחרי הצלחה בחלון, חזור לטרמינל.

```bash
agent status          # Logged in + האימייל של Cursor
agent about
```

זה רק CLI מחובר. worker עדיין לא רץ עד:

```bash
cd /path/to/velvetos-core   # הקלונים המקומי
agent worker --computer-use --name "sderot-mac" start
```

הטרמינל **נשאר פתוח**. מחובר = השורה לא נסגרת חזרה ל־`$`, ויש שם `sderot-mac` / connected. בדיקת מוקדמת: `agent worker debug`.

אם עדיין `command not found: agent`:

```bash
ls -l ~/.local/bin/agent
```

- הקובץ **חסר** → ההתקנה לא רצה; חזור על `curl https://cursor.com/install -fsS | bash` באותו טרמינל.
- הקובץ **קיים** → הרץ `export PATH="$HOME/.local/bin:$PATH"` ואז `agent --version`. אפשר גם `~/.local/bin/agent login` בלי PATH.

בפעם הראשונה ב־macOS: System Settings → Privacy & Security → Accessibility **ו־** Screen Recording ל־**Cursor Computer Use**.

ב־cursor.com/agents: בחר את המכונה `sderot-mac` (לא VM הענן).  
אין worker מחובר עכשיו — עד שזה רץ, השיחה הזו נשארת על VM בלי הכרום שלך.

### ד. מה לא לעשות

- להעתיק עוגיות מווינדוס למק, או `~/.codex` / `~/.gemini` ל־Cloud
- Chrome remote debugging / שיתוף מסך / מנהרה לכרום
- `npx perplexity-user-mcp` בענן

## 06:15 — מק בשדרות
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
