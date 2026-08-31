# הסלמה

לא כישלון. אדם מחליט. HQ לא שולח בינתיים.

```
task_id: grok-failover-2026-08-31
pack: vfharness
decision_needed: האם לשנות את Deny הקבוע (Gmail send / Instagram Publish מ־HQ) ב־AGENTS.md — כרגע השיחה ביקשה שליחה אוטונומית; המדריך מנצח את השיחה
recommended: להשאיר Deny. אדם מדביק MAIL-PACK ומעלה G005 מ־LIVE-PACKET. אחרי ~5.9 — Grok
already_tried: תוצרים מלאים על פקים קיימים (OUTAGE-5D, MAIL-PACK, G005-LIVE-PACKET). לא נקרא send_message. אין MCP Publish לאינסטגרם. ChatGPT/Gemini/Perplexity אין להם כלי שליחה כאן
sensor_or_guide: AGENTS.md (guide wins) · DENY send_message/reply/forward · playbooks/grok-failover.md · check-vfharness.py
artifact: packages/vfops/human-send/MAIL-PACK.md · packages/vfigos/live/G005-LIVE-PACKET.md
safest_default: לא לשלוח / לא להמציא ₪ / לחכות לאדם
cost_of_waiting: אין ספירה (G005 משובץ חמישי 12:00 — אם אדם לא מעלה, המועד מתפספס; HQ לא ממלא את הלחיצה)
```
