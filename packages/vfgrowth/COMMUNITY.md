# Community Print Engine

מושב: צמיחה + ייצור. לא פק חדש.  
סקרים: `data/poll-library.json`. חוקה: `constitution/ORGANIC_GROWTH.md`.

## מחזור

1. 07:00 — Core מציע סקר לערב (מלאי / מדפסות / חור בפיד) מתוך הספרייה בלבד.
2. ראש צוות מאשר ומעלה Story **ידנית**.
3. תוצאה: הדבקה ידנית או Insights מיובא — לא ניחוש.
4. `vfgrowth` כותב Work Order `pending_ops` (לא Print).
5. מפעיל רצפה מבצע אחרי אישור ops.
6. Reel המשך: «אתם בחרתם—בדקנו» (בלי תיוג אוטומטי).

## Work Order (דיסק)

```json
{
  "name": "community.work_order",
  "work_order_id": "community_test_YYYY-MM-DD_<slug>",
  "source": "instagram_story_poll",
  "poll_question": "",
  "winning_option": "",
  "required_action": "print_and_test",
  "test_protocol": "",
  "deadline": "",
  "content_followup": "reel_result",
  "approval_state": "pending_ops"
}
```

## נעול

- אין סקר→Print מ־HQ. `pending_ops` ≠ הדפסה.
- אין תיוג משתמשים בלי opt-in כתוב + אישור אדם.
- משפט ברירת מחדל: **«אתם בחרתם—הנה התוצאה.»**
- ספריית הסקרים רק מיכולות סטודיו אמיתיות (חומר במלאי / מדפסת פנויה). חסר מלאי = לא מציעים את האופציה.
