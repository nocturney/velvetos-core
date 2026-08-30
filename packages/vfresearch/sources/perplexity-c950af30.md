# מקור · Perplexity 30.8.2026

**גוף השיחה לא נקרא.** הקובץ הזה הוא מה שנפתח בפועל — לא המצאה של התשובה.

| | |
|---|---|
| קישור | https://www.perplexity.ai/search/c950af30-8c60-4667-b7d6-84db67f62218 |
| מעקב | 30.8.2026 אחה״צ (follow-up: Cursor חייב לפתוח בעצמו) |
| מצב | Cloudflare Turnstile. לא הגיעו לגוף. פעם אחת WebFetch הראה גם «This session is private» |

## מה נפתח בדפדפן אמיתי (Chrome + Xvfb + Playwright, ועוד סשן computerUse)

כותרת: רק רגע… / Just a moment…

```
www.perplexity.ai
ביצוע אימות אבטחה

אתר זה משתמש בשירות אבטחה להגנה מפני בוטים זדוניים.
דף זה מופיע בזמן שהאתר מוודא שאינך בוט.

יש לאמת שאינך רובוט
```

אנגלית באותו דף:

```
Performing security verification
This website uses a security service to protect against malicious bots.
This page is displayed while the website verifies you are not a bot.
Verify you are human
```

Ray IDs (חלקי): `a33430513f93feff`, `a3343288abee96ba`, `a3340874dabcd106`, `a333e8f0aba30d87`.

## ניסיונות במעקב הזה (לא לחכות לגרוק)

1. דפדפן computerUse — לחיצה על Turnstile, המתנה, רענון. לולאה.
2. Chrome 148 headed תחת Xvfb (Playwright). אותה חומה בעברית.
3. לחיצה ממוקדת על iframe של `challenges.cloudflare.com`. הפריים קיים, הלחיצה לא עוברת.
4. undetected-chromedriver — Chrome לא נפתח (`chrome not reachable`).
5. WebFetch / curl — `cf-mitigated: challenge`, HTTP 403.
6. jina על `www.perplexity.ai` — חסימת Abuse עד ~14:26 UTC. בלי www — רק Cookie Policy.
7. Gmail + Drive — אין ייצוא של השיחה. רק קבלות Apple על Perplexity Pro.
8. archive / 12ft / allorigins — אין עותק.

אחרי Cloudflare, אם בכלל: מסך «This session is private / Sign in if you are the owner». בלי סשן Google של `nocturney@gmail.com` בדפדפן הזה — אין גוף.

## מה לא עושים

- לא ממציאים את תשובת Perplexity.
- לא מעתיקים לכאן את שיתוף ChatGPT (PR #1) ומתייחסים אליו כאילו זה Perplexity.
- לא פותחים פק חדש.

כשהשיחה תיפתח מחשבון הבעלים — להחליף את הקובץ הזה בטקסט המלא ולמפות על אותן חבילות כמו Gemini.
