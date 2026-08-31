# Grok Bot — failover כשמכסה שבועית נגמרת

**Date:** 2026-08-31 (עודכן — HQ שולח דרך כלים)  
**From:** Christian (בקשת בעלים: פיילאובר אוטונומי, לא אדם ולא Grok כשער)

כשמכסת השימוש השבועית של **Grok Bot** נגמרת (או שהבוט לא זמין):

1. **מייצרים תוצרים** על הפקים הקיימים.
2. **שולחים מ־HQ דרך כלים** — ג׳ימייל `send_message` / `reply` · אינסטגרם לפי `vfigos/SEND.md`. בריף 07:00 = `htmlBody` תצוגה 3 (`vfbriefux/MAIL.html`).
3. Drive `create_file` למסמך משרד כשצריך.
4. תזמורת ChatGPT + Gemini + Perplexity. **Treg לא רלוונטי.**
5. תגיות: `#נשלח-מ-HQ` · `#ממתין-ל-כלי-IG` · `#מוכן-ל-Grok` רק כגיבוי אופציונלי.
6. אין בוסט. אין אוטו־DM. אין Print מ־HQ. שיחת לקוח → אדם `050-2517000`.
7. לא ממציאים שעלה לפיד אם לא עלה.

נוהל: [`packages/vfharness/playbooks/grok-failover.md`](../packages/vfharness/playbooks/grok-failover.md) · [`constitution/SEND.md`](../constitution/SEND.md).
