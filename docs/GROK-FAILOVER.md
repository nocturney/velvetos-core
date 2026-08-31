# Grok Bot — failover כשמכסה שבועית נגמרת

**Date:** 2026-08-30  
**From:** Christian (בקשת בעלים)  
**Repo:** nocturney/velvet-factory-headquarters-os

כשמכסת השימוש השבועית של **Grok Bot** נגמרת (או שהבוט לא זמין), HQ נכנס למצב failover:

1. **מייצרים תוצרים** על הפקים הקיימים (כיתוב, כריכות, בריף, פניות, מחקר, תכנון ריל).
2. **נעזרים** ב־Cursor + ChatGPT + Gemini + Perplexity לפי `constitution/ORCHESTRA.md`.
3. **שני מסלולי פרסום:**
   - לא דחוף → תור `#מוכן-ל-Grok` עד חידוש המכסה.
   - **פרסום חי במידת הצורך** → `#פרסום-חי-דחוף` + חבילת [`LIVE-PACKET.md`](../packages/vfigos/LIVE-PACKET.md): HQ מכין מדיה+כיתוב; **האדם** מעלה ב־`@velvets_cloud`.
4. בריף 07:00: HQ שולח אל `nocturney@gmail.com` (`send_message` — אותו תפקיד כמו Grok). Instagram Publish / Boost / DM / וואטסאפ — אין כלי או Deny. LIVE-PACKET לאדם. מפה: `packages/vfharness/playbooks/grok-outage-tools.md`.
5. דחוף ללקוח (שיחה) → אדם בוואטסאפ `050-2517000`.

נוהל מלא: [`packages/vfharness/playbooks/grok-failover.md`](../packages/vfharness/playbooks/grok-failover.md).

זה **לא** מחליף את `docs/BACKUP.md` (גיבוי GitHub של פקים). כאן מדובר בגיבוי **תפעולי** כש־Grok לא זמין.

## הפעלה במילים

```
@vfharness grok-failover
נגמרה מכסת Grok — תמשיכו לייצר
צריך פרסום חי עכשיו על <נושא>
```
