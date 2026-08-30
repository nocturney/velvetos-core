# 500 AI Agents — מה נכנס למשרד

מקור: [ashishpatel26/500-AI-Agents-Projects](https://github.com/ashishpatel26/500-AI-Agents-Projects) (נקרא 2026-08-30).  
הרשימה היא קטלוג של מאות דוגמאות CrewAI / LangGraph / AutoGen / Agno. רובה קוד פייתון, רפואה, מסחר, או סתם דמו.

כאן זה **מפה + נהלי משרד** על החבילות הקיימות. אין התקנת LangGraph בריפו. אין שליחת אינסטגרם או ג׳ימייל מ־HQ. אין ₪ מומצא. אין Insights מומצא.

פק הקטלוג: [`packages/vfagents/`](../packages/vfagents/).  
מפה מכונה: [`packages/vfagents/fit.json`](../packages/vfagents/fit.json).  
בדיקה: `python3 scripts/check-vfagents.py`.

## כבר יש אצלנו — לא לשכפל

| רעיון מהרשימה | חבילה אצלנו | למה לא פק חדש |
|---|---|---|
| Web Research / Research Scholar / DeepKnowledge | `vfresearch` | מחקר 06:15 כבר נופל לבריף. Treg במקום Tavily |
| Instagram Post / Social Media Content | `vfigos`, `vfcopy`, `vfcovers` | טיוטה וסקירה. Grok שולח |
| Marketing Strategy / Content Personalization | `vfgrowth` | ספרינט תוכן, לא אסטרטגיה מומצאת |
| Product / SKU recommendation / RecAI | `vfsku` | כרטיסים וחוזרים. בלי מק״ט חדש |
| Factory Process Monitoring | `vfprod` | רשימת רצפה. לא דמון חי |
| Inquiry → order / Customer Support | `vfconvert` | ארבעה־שנים־עשר שדות בוואטסאפ אנושי |
| Quotes + follow-up / Lead Score | `vfsales` | טיוטה. ₪ רק אחרי ראש צוות |
| Unit economics / cost | `vfcost` | סלייס ובדיקה. בלי מחיר מכירה |
| Performance reads | `vfinsights` | קריאה ממקור. לא ממציאים מספר |
| Receivables / ledger | `vfbooks` | Invoice4U. לא Bookipi |
| Studio calendar | `vfseason` | סימוני עונה. לא יומן נסיעות |
| License / legal clause | `vlicense` | שער רישיון. לא מעתיקים מותג ישראלי |
| Brief UX / meeting packet | `vfbriefux`, `vfops` | בריף בוקר 07:00 |
| Copy lint / reflection | `vfcopy` | שיעורי בית. לא פוסט אוטומטי |
| Strategy / plan-and-execute | `vfbiz` | החלטות. לא שרשרת סוכנים חיה |

## להטמיע עכשיו (נהלים, לא בוט)

שתים־עשרה תבניות מהרשימה שחסרות כצעד משרדי ברור. כל אחת היא קובץ ב־`packages/vfagents/playbooks/`.

| # | רעיון | מקור | נוהל | חבילות |
|---|---|---|---|---|
| 1 | טיוטת מייל (אנליסט → כותב) | `agents/05-email-drafting-agent`, CrewAI Email Auto Responder | [email-draft](../packages/vfagents/playbooks/email-draft.md) | `vfsales`, `vfconvert`, `vfops` |
| 2 | תמיכת פנייה + הסלמה | `agents/13-customer-support-agent`, LangGraph Customer Support | [inquiry-support](../packages/vfagents/playbooks/inquiry-support.md) | `vfconvert`, `vfcopy` |
| 3 | כיתוב לפיד | `agents/14-social-media-agent`, CrewAI Instagram Post | [caption-draft](../packages/vfagents/playbooks/caption-draft.md) | `vfigos`, `vfcopy`, `vfcovers` |
| 4 | סיכום פגישה / הכנה | `agents/10-meeting-notes-agent`, CrewAI Meeting Assistant | [meeting-notes](../packages/vfagents/playbooks/meeting-notes.md) | `vfops`, `vfbriefux` |
| 5 | ניקוד ליד (בלי ₪) | CrewAI Lead Score Flow | [lead-score](../packages/vfagents/playbooks/lead-score.md) | `vfsales`, `vfconvert` |
| 6 | ניקוי PII לפני מודל | `agents/21-pii-sanitization-agent` | [pii-gate](../packages/vfagents/playbooks/pii-gate.md) | `vlicense`, `vfops` |
| 7 | ביקורת רצפה / שכבה ראשונה | Factory Process Monitoring | [floor-qc](../packages/vfagents/playbooks/floor-qc.md) | `vfprod` |
| 8 | המלצת חוזר מקטלוג קיים | RecAI / Shopping Partner | [sku-repeat](../packages/vfagents/playbooks/sku-repeat.md) | `vfsku`, `vfsales` |
| 9 | סריקת מתחרים ציבורית | `agents/19-competitive-analysis-agent` | [competitor-scan](../packages/vfagents/playbooks/competitor-scan.md) | `vfbiz`, `vfresearch` |
| 10 | שאלות על PDF בריף / הצעה / רישיון | `agents/03-pdf-qa-agent`, Legal Document Review | [brief-pdf](../packages/vfagents/playbooks/brief-pdf.md) | `vfresearch`, `vlicense`, `vfsales` |
| 11 | מחקר יומי מובנה | `agents/01-web-research-agent`, Agno Research | [daily-research](../packages/vfagents/playbooks/daily-research.md) | `vfresearch` |
| 12 | טיוטה → ביקורת → תיקון | LangGraph Reflection / vfcopy lint | [copy-reflect](../packages/vfagents/playbooks/copy-reflect.md) | `vfcopy`, `vfgrowth` |

## אחר כך — רק אם ראש צוות פותח

| רעיון | למה מחכים |
|---|---|
| Landing Page Generator | אתר רק אם `vfbiz` נפתח. לא Wix מ־HQ |
| Media Trend Analysis (Agno) + Treg | אחרי התחברות Treg; בלי Insights מומצא |
| YouTube / Whisper תמלול שיחת לקוח | רק אם יש הקלטה שהלקוח אישר |
| Multimodal proof (GPT-4V) | תמונת מיטה אמיתית מ־`vfprod`, לא דמון מצלמה |
| SQL / Sheets על יומן | אחרי MCP של Sheets (`vfmcp`). לא ממציאים טבלה |
| Inbox Zero מעל Gmail | קריאה בלבד; כבר מופה ב־`docs/MCP-FIT.md` אם אותו PR נכנס |

## דולג — לא אצלנו

בריאות, ביטוח, מסחר במניות, ארנק קריפטו, נהיגה אוטונומית, חקלאות, אנרגיה, גיימינג, תיירות, מתכונים, גיוס/קורות חיים, צוות אדום / Vibe Hacking, צ׳אטבוט 24/7, אוטו־DM, ווידג׳ט מחיר, שליחת מייל ללקוח, פרסום אינסטגרם מ־HQ.

פירוט: [`packages/vfagents/SKIP.md`](../packages/vfagents/SKIP.md).

## איך משתמשים

1. בשיחת Cursor: «תריץ את נוהל `email-draft` על המייל הזה» / «`lead-score` על הפנייה».
2. הסוכן ממלא את התבנית מהנוהל. לא שולח. לא ממציא ₪.
3. אדם או Grok Bot סוגרים את השליחה (וואטסאפ `050-2517000`, אינסטגרם, ג׳ימייל חי).
4. PII: קודם `pii-gate` אם הטקסט הולך למודל חיצוני.

## סדר מומלץ לשבוע הראשון

1. `pii-gate` — הרגל לפני כל הדבקה.
2. `inquiry-support` + `lead-score` — פניות בוואטסאפ.
3. `email-draft` — תיבת Gmail לקריאה.
4. `caption-draft` + `copy-reflect` — פיד ל־Grok.
5. `floor-qc` — משמרת הדפסה.
6. `daily-research` ב־06:15, `meeting-notes` כשיש שיחה.

עצירה שם. השאר רק כשפק תקוע בלי תבנית.
