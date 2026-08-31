# vfharness — רתמת המשרד

מושב: ראש צוות (תשתית לכל המושבים). לא שולח אינסטגרם / ג׳ימייל / DM.

הפק הזה הוא ה-outer harness — לא סוכן מוצר חדש ולא ראנטיים שני. Cursor כבר המשרד.

## מתי

כשל שחוזר, משימה רב-שלבית, בדיקת מוכנות, כשהמשתמש אומר רתמה / harness / AGENTS.md, או **מכסת Grok נגמרה** (failover + פרסום חי דחוף).

## שרשרת

1. קרא `AGENTS.md` (המדריך מנצח את השיחה).
2. תכנן צעדים קצרים על **פק קיים**.
3. בצע. אחרי כל שינוי קטלוג/כלל — `python3 scripts/check-all.py`.
4. כשל סנסור → תקן פעם אחת → אם נכשל שוב, הסלם עם `templates/escalation.md`.
5. כתוב נקודת ביקורת ב-`state/<task-id>.json` לפני סגירת סשן ארוך.
6. מכסת Grok ריקה + צריך IG חי → `playbooks/grok-failover.md` + `vfigos/LIVE-PACKET.md` לאדם.
7. הקשר כבד (thread, JSON, Drive dump) → `playbooks/context-thrift.md` — סיכום בשיחה, מקור ב-checkpoint.

צינור יחיד נשאר: פנייה · שיחה · הצעה · הדפסה · איסוף.

## אסור

סוכן HQ לא לוחץ Publish / Send / Boost / DM. אדם כן יכול לפרסם חי בזמן failover עם LIVE-PACKET. אין להמציא ₪ / Insights, אין CrewAI/AutoGPT, אין פק כפול, אין להסתיר סנסור אדום.

ראה `hq/PLAYBOOK.md` ו-`EMBED.md`.
