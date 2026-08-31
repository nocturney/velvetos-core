# איפה ה־MCP של 3D AI Studio (לא NCP)

אתה מחפש במקום הלא נכון אם אתה ב־**Cursor Settings / Marketplace / Plugins**.  
3D AI Studio **לא** מופיע שם. גם לא ב־`docs.3daistudio.com` (הדוקס עודכנו מאי 2026; המחבר יצא ב־4.8.2026).

המתג יושב **באתר שלהם, אחרי Login**, לא במחשב של Cursor.

מקור: [Updates v6.5](https://www.3daistudio.com/Updates) · [MCP](https://www.3daistudio.com/MCP)  
«Available on all paid plans.»

## 1. דפדפן — לא Cursor

1. פתח [www.3daistudio.com](https://www.3daistudio.com) והתחבר (אותו מנוי).
2. אתה בדשבורד (Files / Projects). זה לא מסך ההגדרות.
3. חפש **גלגל שיניים** / האווטאר / **Settings** / **Manage** — בפינה (בדרך כלל ימין־למעלה).
4. בלשוניות של Settings חפש בדיוק: **AI Assistants (MCP)**.
5. Add / Connect → בחר **Cursor**.
6. ייפתח Login של 3DAI → Allow.
7. אם מופיע כפתור **Add to Cursor** או שדה URL — לחץ / העתק **רק מה שמופיע שם**. לא ממציאים כתובת.

אחרי זה, ב־**Cursor Desktop** (חלון העורך, לא `cursor.com/agents`):

1. Customize בסרגל → **MCPs**, או `Ctrl+Shift+P` → `View: Open MCP Settings`.
2. אמור להופיע שרת 3D AI Studio. לחץ **Connect** אם הוא אפור.
3. צ׳אט חדש, מצב **Agent** מקומי: «ייצא את המודל האחרון ל־STL».

## מה לא לעשות

| חיפוש | למה זה ריק |
|---|---|
| Cursor Marketplace / Plugins / «3D AI Studio» | אין תוסף חנות. זה מחבר מהאתר שלהם |
| הצ׳אט הזה / Cloud Agent | אין כאן OAuth של 3DAI |
| `.cursor/mcp.json` עם URL מהראש | אין URL רשמי מפורסם. Canva נשאר ה־HTTP היחיד בגיט |
| Flow → **Bob** | זה עוזר פנימי לקנבס, לא MCP ל־Cursor |
| API Dashboard / מפתח | שכבה אחרת. לא נחוץ למחבר הרשמי |
| ChatGPT Settings → Connectors | זה ל־ChatGPT, לא ל־Cursor |

## הלשונית לא שם

1. לוודא שאתה **Logged In** (לא Guest).
2. מנוי **בתשלום** — ב־v6.5 כתוב במפורש: רק תוכניות בתשלום.
3. רענון קשיח / חלון פרטי אחרי Login.
4. שמות אחרים באותו Settings: Connectors / Integrations / MCP / AI Assistants.
5. עדיין אין? מייל ל־`support@3daistudio.com`: «Where is Settings → AI Assistants (MCP) for Cursor? Paid plan, logged in, tab missing.»

עד שהלשונית מופיעה: עובדים מהאתר. `3DAISTUDIO.md`. אין המתנה בסרק.

## אחרי שהחיבור חי

להגיד ל־HQ «3DAI מחובר ב־Desktop». אז מעדכנים `threedaistudio.status` בריצה שרואה את הכלים.
