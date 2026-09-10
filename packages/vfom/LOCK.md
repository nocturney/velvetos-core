# vfom locks

נעילות מ־OpenMontage + Velvet Visual Foundry. לא מתקינים את מוצר OpenMontage, לא יוצרים runtime/queue/catalog/memory DB מקביל, ולא ממציאים סצנת רצפה.

## מנוע וידאו — דלג כברירת מחדל

Remotion, HyperFrames, `tools/`, `make setup`, `python -m backlot`, Piper TTS, ורשת ספקי ענן (fal / Veo / Kling / Runway / Seedance / Atlas / HeyGen / Suno / ElevenLabs) אינם runtime קנוני של HQ.

למה: Office Control Plane כבר orchestrator. Media Vault הוא SoT. Canva/כלי המדיה הקיימים הם שכבת production הנוכחית. אין מונורפו שני ואין מפתחות API בגיט.

ספק generation בתשלום יכול להיפתח רק דרך policy/spend gate קיים; פתיחת ספק אינה משנה את חוקי Asset Truth, Content Contract או Claim Provenance.

## VoiceStudio / TTS מקומי — דלג על Cloud · later במק בלבד

[debpalash/VoiceStudio](https://github.com/debpalash/VoiceStudio) (לשעבר OmniVoice-Studio) — שיבוט קול, דיבוב, תמלול, MCP על `localhost:3900`.  
**לא מתקינים** DMG/MSI/Docker/`bun run desktop` מ־HQ Cloud. **לא מחברים** את ה־MCP על Cloud Agent.

למה: ריל Velvet Factory נשען על הוכחת רצפה, לא על קול AI. AGPL + משקלי מודל (לעיתים NC) דורשים שערי `vlicense` לפני שימוש מסחרי. אם ראש צוות פותח VO מקומי — רק Desktop אחרי אישור מותג; ראו `docs/MCP-FIT.md`.

מקור הטמעה: `packages/vfresearch/sources/2026-09-05-voicestudio.md`.

## צינורות מחוץ לסטודיו — דלג

Avatar Spokesperson, Talking Head, Character Animation, Localization & Dub, Podcast Repurpose, Screen Demo, `framework-smoke`.

למה: אין דובר-אווטאר, אין פודקאסט, אין דמו תוכנה, אין תרגום מולטי-שפה כמוצר. הסטודיו מדפיס ומצלם הוכחת רצפה.

## ארכיון / AI במקום הוכחה — דלג

Documentary Montage מ־Archive.org / NASA / Wikimedia / Pexels או generation סינתטי אינם תחליף לטיימלאפס/צילום אמיתי מהסטודיו כאשר התוכן טוען טענה פיזית.

למה: Asset Truth אינו Claim Truth. `synthetic`/`illustrative_ai` יכולים להיות atmosphere/transition/supporting visual בלבד; הם אינם proof למדידה, עומס, כשל, הצלחה, תוצאת לקוח או גאומטריית מוצר.

## שליחה / פרסום — policy, לא איסור HQ גורף

- `vfigos` הוא נתיב הפרסום והאימות הקנוני.
- LOW-risk routine organic Instagram יכול להישלח דרך כלי מחובר כאשר `creativeAutonomy.publish.standingAuthorization=true` וכל Content Contract / PREFLIGHT / policy / rights gates עברו.
- MEDIUM משתמש בשער האישור הקיים כאשר policy דורש.
- HIGH הופך `human_required`.
- Grok הוא backup/failover אופציונלי, לא sender קנוני יחיד.
- אין receipt + live verification אמיתיים -> אין claim שפורסם.

נעילות קבועות: auto-DM, Boost/Ads ללא שער מתאים, customer WhatsApp send, Print from HQ, unsupported claims, ופעולות בלתי הפיכות.

## מחוללי וידאו בתשלום — אחר כך בלבד

Veo, Kling, MiniMax, Runway, Grok video, מוזיקה מ־Suno — רק אם ראש צוות/Policy פותח תקציב. אומרים עלות לפני קריאה. אין המרת דולר ל־₪ מ־HQ ואין generation יקר לפני progressive ranking זול.

## מספרים — נעילה קבועה

אין Insights מומצאים. אין ₪ על הפריים. אין מחיר מכירה בלי מקור/שער מתאים. כתוב `X ₪` / «אין במקור» כשחסר.

## הוכחה — נעילה קבועה

אין סצנת רצפה מומצאת. אין עולם תלת־ממד «כאילו זה ההדפס». חסר קובץ גלם קריטי -> חפש קודם Media Vault; אם עדיין חסר, `shotRequest` מינימלי ו־`waiting_for_media`. אל תייצר את ההוכחה ב־AI.

## איכות — לא owner gate

Hook חלש, crop רע, cover חלש, subject drift, flicker, עברית משובשת או score נמוך חוזרים ל־Artifact Repair Router בתוך bounded repair loop. פנייה לבעלים רק על Human Required אמיתי לפי `CREATIVE-AUTOPILOT.md`.
