# שליחה מ־HQ · כלים, לא אדם ולא Grok Bot

נעילה 31.8.2026 (Asia/Jerusalem) — הבעלים.  
Human-visible text lock נוסף 11.9.2026: `VISIBLE_TEXT.md`.  
Treg לא רלוונטי. Drive יוצר מסמכים לפי צורך.  
**ג׳ימייל ואינסטגרם יוצאים מ־HQ דרך כלים** — לא דרך כריסטיאן ולא דרך Grok Bot.  
פיילאובר מלא: כלי נפל → כלי גיבוי באותו תור. אסור להישאר בלי תוצאה.

לא פק חדש. לא מושב שישי.

## חוק לפני Send / Publish

**Transport readiness ≠ text readiness ≠ publish approval.**

כל גוף/subject/CTA/כותרת או prose שנכתב או שוכתב ב־AI ושאדם יקרא חייב לעבור קודם `constitution/VISIBLE_TEXT.md` דרך `vfcopy` על **הטקסט המדויק**. מקור literal — IDs, hashes, URLs, raw logs, source values — נשאר literal.

- Gmail ללקוח: `customer-message` / `sales-proposal` Visible Text Gate.
- בריף/מייל לכריסטיאן: `owner-brief` Visible Text Gate.
- Instagram public copy/visual text: `public-social` / `visual-microcopy` Visible Text Gate + יתר שערי vfgrowth/Brand Guardian.
- WhatsApp: HQ לא שולח; הטיוטה שהאדם מקבל להדבקה חייבת `customer-message` gate.
- נוסח קבוע מאושר ניתן לשימוש כ־`approved_static_copy` רק ללא שינוי וכשהעובדות שבו עדיין תקפות.

אין `PASS` על סמך קיום הקובץ/ה־skill. אם השרשרת לא הופעלה בפועל: `UNPROVEN`/`BLOCKED`, ולא שולחים/מפרסמים.

## מי שולח

| ערוץ | מי | כלי | תנאי טקסט | לא |
|---|---|---|---|---|
| ג׳ימייל | **סוכן HQ** | `send_message` / `reply` / `forward` על `nocturney@gmail.com` | Visible Text Gate לפי הקורא + facts | לא מחכים לגרוק. לא מחכים לאדם ללחוץ Send |
| אינסטגרם `@velvets_cloud` | **סוכן HQ** דרך כלי מחובר | `publish_image` / `publish_carousel` / `publish_reel` / `publish_story` אחרי creative+Canva+vault+PREFLIGHT v2 | `public-social` + `visual-microcopy` כשיש טקסט על הוויזואל | לא LIVE-PACKET לאדם כברירת מחדל. לא אוטו־DM. לא Metricool כתלות |
| וואטסאפ לקוח | אדם `050-2517000` | Core: MCP חיפוש/טיוטה. VF `send=false` | gated draft לפני handoff | HQ לא ממציא בוט |
| מדפסות | רצפה | `vfprod` | — | HQ לא לוחץ Print |
| בוסט / אוטו־DM | — | נעול | — | נעול תמיד |

Grok Bot הוא **גיבוי אופציונלי**, לא השולח היחיד ולא שער חובה.

## לפני Instagram publish — שלושה היבטים נפרדים

### 1. Transport readiness

אבחון חיבור בלבד:

```bash
python3 scripts/vf_send_preflight.py --gate instagram --transport-only
```

הצלחה כאן אומרת רק שהכלי/transport זמינים. **היא אינה הרשאת publish.**

### 2. Human-visible copy approval

הכיתוב וכל cover/overlay/slide text שנכתבו ב־AI עוברים `VISIBLE_TEXT.md`. ל־visual microcopy: 3–5 candidates + `NO_TEXT`; אם הטקסט אינו מוסיף פואנטה מול התמונה הנקייה → `NO_TEXT`.

ה־PREFLIGHT חייב לשמור `visible_text_gate: PASS`, `text_sha256`/copy digest, `vfcopy_lint`, `humanizer_ai_tells` ו־surface QA על הגרסה הסופית. שינוי קופי מבטל את ה־PASS.

### 3. Exact-package creative approval

לפני כל `publish_*` חובה להריץ:

```bash
python3 scripts/vf_send_preflight.py --gate instagram \
  --content-id <GID> \
  --format <story|reel|carousel|post> \
  --approval-ref packages/vfgrowth/preflight/<GID>.md \
  --package-sha256 <SHA256-OF-EXACT-FINAL-PACKAGE>
```

רק exit `0` ובפלט `publication_quality.publishAuthorized=true` מאפשרים Publish.  
exit `1/2` = **לא מפרסמים**. מתקנים את התוצר או את ה־transport לפי הסיבה.

PREFLIGHT לפרסום חדש חייב להיות schema v2. `brand_guardian`, `copy_qa`, `readability`, `contrast` + Visible Text Gate חייבים להתאים לפורמט ולגרסה הסופית; Rubric ≥20/25; `artifact_digest`; `final_package_sha256`. אין waiver ל״רכה אבל קריאה״ / ״לא חוסם״. שינוי מהותי אחרי QA מבטל approval.

## פריפלייט כללי לכלי HQ

```bash
python3 scripts/vf_send_preflight.py
python3 scripts/vf_send_preflight.py --gate gmail
```

בדיקות כלי אינן מחליפות Visible Text Gate או `vfgrowth/PREFLIGHT.md`.

## ג׳ימייל — מותר עכשיו, אחרי text gate

מותר:
- בריף 07:00 ל־`nocturney@gmail.com` — `owner-brief` gate לפני render/send.
- תשובה בשרשור פנייה שכבר נקרא — `customer-message` gate; בלי ₪ מומצא.
- הצעה — `sales-proposal` gate + מחיר/עובדות מאומתים.
- חבילת LIVE / כיתוב / קישור Canva / קישור Drive — prose שנכתב ב־AI עובר surface המתאים; הקישורים/IDs עצמם literal.
- `reply` / `forward` כשזה מקדם את הצינור ואחרי gate מתאים לגוף החדש שנוסף.

אסור: דיוור המוני, חוב בלי ראש צוות, סודות, אוטו־DM / `send_dm`, או Send של AI body עם `visible_text_gate != PASS`.

## בריף 07:00 — לולאה לפני שליחה

`python3 scripts/vfops_loop.py brief --write` מרכיב עובדות/חריצים מפקים חיים. אחר כך: `owner-brief` reader-first → `vf-hebrew-copy` → Humanizer/AI-tells → surface-aware lint → fact/status validation → `visible_text_gate: PASS` → ורק אז `render_mail.py` ו־Gmail. המעבר הזה לא מפרסם IG.

## נעילת כריסטיאן — לפני שיבוץ / חי

משטח: **החלטה** · **חסם קשיח** · **פרסום חי שדורש אותו בלבד**.  
אסור: מדדים חלשים · «רמה נמוכה» · נתיחת איכות אחרי פרסום · דוח בושה על כלי שלא נצרך.

לפני שיבוץ או Publish: ארטיפקט `vfgrowth/preflight/<id>.md` לפי [`PREFLIGHT.md`](../packages/vfgrowth/PREFLIGHT.md). נכשל-סגור → **לא משבצים ולא מפרסמים**.

## אינסטגרם — מותר דרך כלי

1. **Visible Text + creative QA + שער עריכה** — copy chain, VOICE/Brand Guardian/רובריקה, Canva/vfcovers/vfcanva, ואז בדיקת final render.
2. **PREFLIGHT v2** — קשור ל־hash של הקופי והחבילה המדויקת. approval ישן/חסר digest אינו תקף לפרסום חדש.
3. `vfcopy` נותן public copy לפי `PUBLIC_CURRENT_CTA`; לא וואטסאפ בכיתוב ציבורי. Showcase יכול לבחור CTA ניטרלי/ללא CTA לפי המדיניות הפעילה.
4. אם Instagram MCP מחובר — מריצים exact-package gate, ורק אחרי PASS מפרסמים ב־`publish_*`.
5. אחרי publish מאמתים ב־`list_media`/`get_media`; רק אז `liveVerified`.
6. אם אין Publish MCP חי — failover Drive+Gmail באותו תור; לא טוענים שעלה.
7. לא סרק. לא ממציאים שנשלח לפיד אם לא עלה.

## Drive — יוצרים לפי צורך

`create_file`: מסמך / גיליון / מצגת למשרד. אם AI כתב prose שאדם אמור לקרוא במסמך — `human-document`/`owner-brief` Visible Text Gate לפני שמכנים אותו final. נתוני source literal אינם עוברים rewrite. לא פותחים תיקיות אישיות/רפואיות/משפטיות. לא ממציאים שורות מחיר.

## Organic Growth Control Plane — לא מפרסם

[`ORGANIC_GROWTH.md`](ORGANIC_GROWTH.md): מפעל טיוטות + Decision Pack 07:00. אישור אדם ≠ פרסום. שליחת IG חיה נשארת פעולה נפרדת אחרי שערי האיכות וה־publish.

## עדיין אסור

אוטו־DM, בוסט בלי ראש צוות, ₪ / Insights מומצאים, גוף חסום מומצא, משלוח ארצי, סוד בגיט, `fcc-server` ב־Cloud Agent, Send/Publish עם Visible Text Gate חסר, או Publish על בסיס transport readiness בלבד.
