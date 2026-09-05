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

## פעם אחת על המק (אתה)

1. Chrome: פרופיל ייעודי (למשל `VF-research`). התחבר פעם אחת ל־ChatGPT Plus, Gemini, Perplexity Pro. אל תתנתק. אל תפתח את אותם חשבונות מדפדפן Cloud/Grok.
2. Cursor **Desktop** על אותו מק — זה משרד התזמורת 06:15 כשצריך את המנויים.
3. Gemini בלי מפתח API:

```bash
# על המק בלבד — Login with Google, החשבון של המנוי
gemini
```

4. ChatGPT Plus בלי מפתח API:

```bash
# על המק בלבד
codex login
```

5. Perplexity: אותה שאלת `DAILY.md` בטאב כרום (או Codex/Gemini ואז ציטוטים מ־WebSearch ב־Cloud). לא מתקינים `perplexity-user-mcp` עד שאישור ראש צוות + סיכון ToS.
6. שמור תוצר ל־`packages/vfresearch/sources/YYYY-MM-DD-orchestra.md` ו־push / Drive. Cloud קורא את הקובץ — לא את האתר.

אל תעתיקו `~/.gemini`, `~/.codex`, עוגיות, או `ANTIGRAVITY_TOKEN` ל־Cloud Agent.

## כל בוקר 06:15

| מי רץ | מה עושים |
|---|---|
| **Cursor Desktop במק** | שלושת השולחנות במנוי (כרום ו/או Codex + Gemini CLI). תבנית `vfresearch/DAILY.md`. מטמיעים בפק קיים. |
| **Cloud Agent** | לא פותח אתרי מנוי. קורא `sources/` אם יש. אחרת `WebSearch` / `WebFetch`. בלי מפתח: «חסר מפתח Gemini» / «חסר מפתח ChatGPT» — לא ממציאים גוף. |

`constitution/ORCHESTRA.md`.

## אופציונלי אחר כך

`cursor worker start` על המק — סוכן שרץ **בשדרות** (IP ביתי). אין worker מחובר עכשיו. לא מנהרה / ngrok לסשן הדפדפן.

## אסור

- לוגין מ־Cloud / Grok לאתרי המנוי
- עוגיות / patchright / העתקת vault
- `npx perplexity-user-mcp` ב־Cloud
- Gemini CLI / Codex headless בענן (שם בדרך כלל דורשים מפתח API או לוגין זר)
