# כספת מדיה משותפת — VelvetOS

**נעול על ידי Christian · 8.9.2026**  
ריפו: `nocturney/velvetos-core` בלבד. אין ריפו מדיה שני. אין שינוי הרשאות שיתוף ב־Drive מ־HQ.

שורש Drive (נקרא בפועל `Velvet Media`):  
https://drive.google.com/drive/folders/1Yg3Rj0hKWTa86EXjaeu-f7CQXswSRMCv

קטלוג יחיד: [`packages/vfmedia/catalog.json`](../packages/vfmedia/catalog.json) · סכמה: [`packages/vfmedia/catalog.schema.json`](../packages/vfmedia/catalog.schema.json) · נוהל קטלוג: [`packages/vfmedia/CATALOG.md`](../packages/vfmedia/CATALOG.md)

---

## תיקיות נעולות (מזהים חובה)

| שלב | שם ב־Drive | Folder ID | תפקיד |
|---|---|---|---|
| שורש | Velvet Media | `1Yg3Rj0hKWTa86EXjaeu-f7CQXswSRMCv` | כספת אחת. אין עץ מקביל |
| נכנס | `01 - נכנס` | `1IG4zNTOuGgvPyhEbKQEKwjRjFD6BuUDJ` | העלאה ראשונה בלבד. עדיין לא מקור |
| מקור | `02 - מקור` | `1M0WY3iIKYOlqMPcBx5xctx8sr8xidnY6` | אחרי קליטת תפעול. הקובץ המקורי החי |
| בעבודה | `03 - בעבודה` | `13H42Kpif3GPNaHlnI24YiHn-m1IS1k5a` | נגזרות / עריכה / Canva / ריל. לא מאשר פרסום |
| מאושר לפרסום | `04 - מאושר לפרסום` | `1LitaCUDgVk7njkWAvC-MX-noQOkyr-ib` | מיקום קובץ אחרי אישור גרסה. **לא** הוכחת אישור לבד |

מזהים אלה חיים גם ב־[`packages/vfmedia/FOLDERS.json`](../packages/vfmedia/FOLDERS.json). לא ממציאים תיקייה חמישית. לא מוחקים קבצים.

---

## מי עושה מה

| גורם | בעלות |
|---|---|
| **תפעול** | קליטה: נכנס → מקור. בעל ה־intake. לא מאשר פרסום מההעלאה |
| **Cursor** | סכמת הקטלוג היחיד + חיישן. לא ממציא שורות / מק״ט / ₪ |
| **GrokBot (משרד)** | עובד על הקבצים דרך **Drive MCP** (העברה בין ארבע התיקיות, תיאור לפי צפייה). לא פותח קטלוג שני |
| **צמיחה / סטודיו** | נגזרות ב־בעבודה. שיבוץ רק אחרי `versionApproval` בקטלוג + `PREFLIGHT.md` |
| **ראש צוות** | אישור גרסה לפרסום. תיקיית «מאושר לפרסום» לבד לא מספיקה |

לוח תיאום: [`docs/SHARED-WORK-COORDINATION.md`](SHARED-WORK-COORDINATION.md).

---

## נוהל (קליטה → מקור → עבודה → אישור)

1. **העלאה** לקובץ נכנס (`01 - נכנס`) בלבד. ההעלאה ≠ אישור. אין שורת קטלוג בלי `sourceFileId` אמיתי.
2. **תפעול קולט:** פותח את הקובץ, כותב תיאור **לפי מה שנראה** (לא סצנה מומצאת), תאריך העלאה, קישור מוצר רק אם ידוע, סטטוס `inbox` → מעביר ל־`02 - מקור` ומשנה סטטוס ל־`source`. אין מק״ט חדש מהכותרת.
3. **עבודה:** עותק / נגזרת ב־`03 - בעבודה`. רושמים `derivativeIds` + `sourceLinks`. המקור נשאר ב־מקור. סטטוס `in_progress`.
4. **אישור גרסה:** ראש צוות ממלא `versionApproval` בקטלוג (`approved` + מי + מתי). רק אז מעבירים את הנגזרת המאושרת ל־`04 - מאושר לפרסום`. שיבוץ IG עדיין עובר `vfgrowth/PREFLIGHT.md` + `vfigos/SEND.md`.
5. **פרסום** הוא צעד נפרד. מיזוג קוד ≠ אישור פרסום. תיקיית מאושר ≠ הוכחת אישור.

---

## חוקים נעולים

1. **קטלוג אחד** — `packages/vfmedia/catalog.json`. אין גיליון מקביל, אין JSON שני, אין רשימת INSTA כקטלוג רשמי.
2. **תפעול = בעל קליטה** — נכנס → מקור. סוכן לא מדלג על תפעול.
3. **אין קטלוגים מקבילים** — לא ב־`vfsku` (מדף מק״ט, לא מדיה), לא ב־Canva בלבד, לא בתיבת Grok.
4. **העלאה ≠ אישור.** קובץ בנכנס הוא גלם.
5. **תיקיית «מאושר לפרסום» לבד ≠ הוכחת אישור.** חייב `versionApproval` בקטלוג.
6. **לא ממציאים ₪** ולא Insights. כותבים `X ₪` / «אין ספירה» כשחסר מקור.
7. **לא ממציאים מק״ט.** קישור מוצר רק אם כבר ידוע (שם עבודה / כרטיס `vfsku` קיים). אחרת `productLink: null`.
8. **אין שינוי הרשאות שיתוף ציבורי** מ־HQ. לא `anyone with the link`, לא העברת בעלות, לא מחיקה.
9. **לא מוחקים קבצים** מהכספת. העברה בין ארבע התיקיות בלבד.
10. CTA נשאר וואטסאפ `050-2517000` / איסוף שדרות. לא «שלחו DM».

---

## כלי

```bash
python3 scripts/vfmedia.py validate
python3 scripts/vfmem.py who "כספת מדיה"
```

GrokBot / משרד: Drive MCP על ארבע התיקיות למעלה. Cursor: סכמה + חיישן `scripts/check-vfmedia.py`. לא משנים sharing.
