# Grok Bot — תחליף מלא במכסה שבועית

**Date:** 2026-08-31 (מודל: Grok = מנהל ראשי, לא גיבוי)  
**From:** Christian · תיקון בעלים 31.8

## מודל

- **שוטף:** Grok Bot מנהל. שולח Gmail / IG / מדפסות. מפנה עיבוד ל-Cursor + ChatGPT + Gemini + Perplexity.
- **מכסה 100%:** Cursor HQ + תזמורת **מחליפים אותו לגמרי** — לא «מחכים לגרוק».

כשמכסת Grok נגמרת (או שהבוט לא זמין):

1. **מייצרים** על הפקים הקיימים (Cursor + תזמורת).
2. **שולחים מ-HQ** — Gmail `send_message` · **פרסום IG ישיר** לפי `vfigos/SEND.md` (Publish MCP / Canva).
3. Drive `create_file` כשצריך.
4. תגיות: `#נשלח-מ-HQ` · `#ממתין-ל-כלי-IG` (רק אם Publish לא ירה) · `#מוכן-ל-Grok` = תור **אחרי חידוש**, לא גיבוי.
5. אין בוסט · אין אוטו־DM · אין Print מ-HQ · וואטסאפ → אדם `050-2517000`.
6. לא ממציאים שעלה לפיד בלי receipt.

**חובה:** הרשאות Publish חי ל-`@velvets_cloud` ל-Cursor HQ, Canva, MCP — `docs/MCP-FIT.md`.

נוהל: [`packages/vfharness/playbooks/grok-failover.md`](../packages/vfharness/playbooks/grok-failover.md) · [`constitution/SEND.md`](../constitution/SEND.md) · [`constitution/GROK.md`](../constitution/GROK.md).
