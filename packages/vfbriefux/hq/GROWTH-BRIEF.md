# GROWTH-BRIEF.md

מושב: בריף UX בלבד. התוכן מגיע מ־`python3 scripts/vf_organic_growth.py brief --write` → `vfgrowth/data/growth-brief.json`.  
חריצי המייל נשארים 01–07 (`MAIL.html`). זה **מסך פעולה** לחריץ 01/07 — לא דוח ארוך ולא Publish.

```
VELVET ORGANIC GROWTH BRIEF — 07:00

יעד היום:
{goal}

1. REEL למשבצת 16:00 הבאה בלוח (א׳/ג׳ — אין ריל כל יום חול)
נושא: {reel_topic}
Asset: {asset_or_חסר}
Hook: {hook_or_חסר}
CTA: לפרטים והזמנות — שלחו לנו הודעה כאן באינסטגרם
גיאוטג: {geotag_or_חסר}
סט האשטגים: {hashtag_set_id}
פעולה: [אישור] [עריכה] [דחייה]
{no_media_line}
{candidate_lines_או_ריק}

2. STORY מוכן ל־20:30 (א׳–ה׳)
סקר: {poll_question}
אפשרויות: {options}
פעולה: [אישור] [עריכה] [דחייה]

3. תוצאת אתמול
Insights: {imported_or_אין_ספירה}
WhatsApp: {orders_or_אין_ספירה}
המלצה: {recommendation_or_אין}

4. משימות סטודיו
{studio_tasks}
```

הפעולה האנושית כאן היא קלט ל־`policy_id: instagram.publish`; היא אינה בעצמה טענת פרסום. רק evaluator `ALLOW` יכול להוביל ל־tool publish, ו־`approved_for_manual_posting` נשאר מסלול legacy ידני.
אין מספר Reach/Saves בלי סנאפשוט מיובא.
כש־`reel.gate=candidates_ready`, `{no_media_line}` הוא שורת «מועמדי Reel מהקטלוג» ו־`reel.candidate_lines` מפרט 2–3 מועמדים (קובץ · סוג · תאריך · מזהה, למה, מתכון). מועמד ≠ ריל ≠ אישור ≠ פרסום.
