# ציר לקוח (Customer Timeline)

דפוסים מ־Monica (PRM), Twenty People/Companies, Krayin activities, forum thread history.

מטרה: לזכור אינטראקציות אמיתיות עם לקוח/פנייה — בלי CRM שני ובלי סודות בגיט.

## מתי

אחרי שיחה משמעותית, שליחת הצעה, אישור תשלום, איסוף, או מעקב לאחר־מכירה.

## רשומה (Markdown בתיקיית job / Drive)

```markdown
# timeline · <כינוי-קצר>
- opened: YYYY-MM-DD
- channel: Gmail | WhatsApp-human | IG-comment
- stage_now: פנייה|שיחה|הצעה|הדפסה|איסוף

## events
| when | kind | note | source |
|---|---|---|---|
| 2026-08-31 | inquiry | רוצה X | Gmail thread … |
| 2026-08-31 | quote_drafted | X ₪ עד אימות | vfsales |
| … | payment_verified | … | vfbooks |
| … | picked_up | איסוף שדרות | human |
| … | followup_draft | … | vfsales |
```

## סוגי אירוע מותרים

`inquiry` · `call_note` · `quote_drafted` · `quote_sent` · `payment_verified` · `print_queued` · `picked_up` · `followup_draft` · `followup_sent` · `blocked` · `license_check`

## אסור

- המצאת שיחה / סכום / Insights.
- שמירת ת״ז, כרטיס אשראי, תיק רפואי.
- אוטו־DM כאירוע «נשלח».
- סנכרון ל־Monica/Twenty חי מ־HQ.

## קישור לצינור

כל `stage_now` חייב להתאים ל־`vfops/hq/PIPELINE-BOARD.md`.  
מעבר שלב = שורת event חדשה, לא מחיקת היסטוריה (כמו forum thread / Monica activity).
