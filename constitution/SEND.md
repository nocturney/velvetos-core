# שליחה מ־HQ · כלים, לא אדם ולא Grok Bot

## VF_PUBLICATION_ROUTE_V1 - current publication scope

Run `scripts/vf_publication_evidence.py --phase production` before production and `--phase delivery` before review delivery, with the exact manifest/content ID. A file-path or static wiring pass is not creative approval. Preserve source pixels, purposeful editorial richness and independent source/reference/copy/brand/final review evidence.

נעילה 31.8.2026 (Asia/Jerusalem) — הבעלים.  
Human-visible text lock נוסף 11.9.2026: `VISIBLE_TEXT.md`.  
Treg לא רלוונטי. Drive יוצר מסמכים לפי צורך.  
**ג׳ימייל ואינסטגרם יוצאים מ־HQ דרך כלים** — לא דרך כריסטיאן ולא דרך Grok Bot.  
פיילאובר מלא: כלי נפל → כלי גיבוי באותו תור. אסור להישאר בלי תוצאה.

לא פק חדש. לא מושב נוסף.

**יכולת/סמכות (2026-10-08):** האיסורים הנוכחיים על WhatsApp send דרך HQ, על הדפסה מהמטה ועל ביצוע עסקי דרך Computer Use אינם איסור קבוע על *פיתוח* יכולות כאלה. הפעלה אמיתית תדרוש החלטת קידום נפרדת, הנחיית בעלים או אישור מפורש ותחום ושער פעולה קנוני; עד אז send=false, גבולות המדפסות וגבולות הפרסום הקיימים נשארים פעילים. ראו CAPABILITY_NOT_AUTHORITY_V1 ב־constitution/CONSTITUTION.md. מסלולי Gmail/Instagram שכבר אושרו פועלים רק תחת הסמכויות העצמאיות שלהם, לא דרך הרשאה חדשה ל־GUI.

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
| וואטסאפ לקוח | אדם `050-2517000` | Core: MCP חיפוש/טיוטה. VF `send=false` | gated draft לפני handoff | HQ לא ממציא בוט |
| מדפסות | רצפה | `vfprod` | — | HQ לא לוחץ Print |
| בוסט / אוטו־DM | — | נעול | — | נעול תמיד |

Grok Bot הוא **גיבוי אופציונלי**, לא השולח היחיד ולא שער חובה.

## לפני Instagram publish — שלושה היבטים נפרדים

`policy_id: instagram.publish` הוא מקור ההחלטה המכונתית הסופי ל־`ALLOW` / `DENY` / `REQUIRE_OWNER_APPROVAL`. שלושת ההיבטים להלן מספקים evidence לקונטקסט ההחלטה; הם אינם evaluator נוסף.

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

PREFLIGHT לפרסום חדש חייב להיות schema `3` במסלול legacy publicationEvidence או schema `4` במסלול VF Project Revision `6.6.9`. במסלול 6.6.9 צורכים ישירות את `.vf-run.json`, `release.json`, ביקורות ה־route/final, transport-QA ו־caption receipt דרך `scripts/vf_project669_publication.py`; לא מייצרים ראיות legacy בדיעבד. בכל מסלול `artifact_digest` ו־`final_package_sha256` חייבים להיות קשורים לגרסה הסופית המדויקת, ושינוי מהותי אחרי QA מבטל approval.

## פריפלייט כללי לכלי HQ

```bash
python3 scripts/vf_send_preflight.py
python3 scripts/vf_send_preflight.py --gate gmail
```

בדיקות כלי אינן מחליפות Visible Text Gate או `vfgrowth/PREFLIGHT.md`.

## ג׳ימייל — Routine send בלי ceremony מיותר

`policy_id: gmail.send` הוא מקור ההחלטה המכונתית ל־Gmail external send. `scripts/vf_send_preflight.py --gate gmail` בודק **transport בלבד**; הוא אינו authorization. החלטת ה־send נעשית ב־`scripts/vf_gmail_send_policy.py` מול `packages/velvetos/policy/gmail.send.json`.

Routine path — **לא דורש owner approval נוסף** כאשר אין trigger רגיש:
- בריף בעלים (`owner_brief`) ל־`nocturney@gmail.com`: facts + `owner-brief` text readiness + target/transport verified.
- תשובה לשרשור שכבר נקרא (`known_thread_reply`): facts + `customer-message` readiness + target/transport verified.
- forward רוטיני ליעד מאומת (`routine_forward`) באותם תנאים.

Text readiness יכול להיות אחד משניים:
- `visible_text_gate: PASS` קשור ל־`body_sha256` המדויק; או
- `approved_static_copy` ללא שינוי, עם אותו `body_sha256` ועם הוכחה שהעובדות עדיין עדכניות. אין סיבה להריץ rewrite/Humanizer מלא מחדש על נוסח סטטי זהה.

נשאר gated:
- יעד חדש (`new_outbound`) שאינו routine מוכר;
- התחייבות מסחרית חדשה;
- מחיר / spend;
- ambiguity של rights/privacy.

במקרים האלה evaluator מחזיר `REQUIRE_OWNER_APPROVAL`; אישור תקף חייב להיות קשור ל־`body_sha256` המדויק, עם reviewer/timestamps/blockers תקינים, ואז ההחלטה ניתנת מחדש כ־`ALLOW`. כאשר יש commitment, `velvetos.action-receipt.v1` נדרש עם exact-body binding (`receipt_mode: EXACT_ACTION_ON_COMMITMENT`).

Fail-closed:
- עובדה לא מאומתת, יעד לא מאומת, transport לא מוכן, body/text digest mismatch, static copy ששונה/התיישן, או blast → `DENY`.
- דיוור המוני נשאר אסור; owner approval לא הופך blast למותר.
- provider receipt נדרש לפני טענה `sent`; transport failure הוא failover/unsynced state, לא הצלחה מדומיינת.

מותר בפועל:
- Morning Brief ידני/אירועי ל־`nocturney@gmail.com` — routine owner-brief class; אין standing 09:00 clock.
- תשובה בשרשור פנייה שכבר נקרא — routine known-thread reply; בלי ₪ מומצא.
- הצעה/מחיר/התחייבות — רק אחרי gate המתאים + exact-body owner approval כאשר נדרש.
- `reply` / `forward` כשזה מקדם את הצינור ואחרי body readiness מתאים.

אסור: blast, סודות, אוטו־DM / `send_dm`, או Send של AI body ללא text readiness תקף.

## Morning Brief ידני/אירועי — לולאה לפני שליחה

`python3 scripts/vfops_loop.py brief --write` מרכיב עובדות/חריצים מפקים חיים. אחר כך: `owner-brief` reader-first → `vf-hebrew-copy` → Humanizer/AI-tells → surface-aware lint → fact/status validation → `visible_text_gate: PASS` → ורק אז `render_mail.py` ו־Gmail. המעבר הזה לא מפרסם IG.

## נעילת כריסטיאן — לפני שיבוץ / חי

משטח: **החלטה** · **חסם קשיח** · **פרסום חי שדורש אותו בלבד**.  
אסור: מדדים חלשים · «רמה נמוכה» · נתיחת איכות אחרי פרסום · דוח בושה על כלי שלא נצרך.

לפני שיבוץ או Publish: ארטיפקט `vfgrowth/preflight/<id>.md` לפי [`PREFLIGHT.md`](../packages/vfgrowth/PREFLIGHT.md). נכשל-סגור → **לא משבצים ולא מפרסמים**.

## אינסטגרם — מותר דרך כלי

2. **PREFLIGHT v2** — קשור ל־hash של הקופי והחבילה המדויקת. approval ישן/חסר digest אינו תקף לפרסום חדש.
3. `vfcopy` נותן public copy לפי `PUBLIC_CURRENT_CTA`; לא וואטסאפ בכיתוב ציבורי. Showcase יכול לבחור CTA ניטרלי/ללא CTA לפי המדיניות הפעילה.
4. אם Instagram MCP מחובר — מריצים exact-package gate, ורק אחרי PASS מפרסמים ב־`publish_*`.
5. אחרי publish מאמתים ב־`list_media`/`get_media`; רק אז `liveVerified`.
6. אם אין Publish MCP חי — failover Drive+Gmail באותו תור; לא טוענים שעלה.
7. לא סרק. לא ממציאים שנשלח לפיד אם לא עלה.

## Drive — יוצרים לפי צורך

`create_file`: מסמך / גיליון / מצגת למשרד. אם AI כתב prose שאדם אמור לקרוא במסמך — `human-document`/`owner-brief` Visible Text Gate לפני שמכנים אותו final. נתוני source literal אינם עוברים rewrite. לא פותחים תיקיות אישיות/רפואיות/משפטיות. לא ממציאים שורות מחיר.

## Organic Growth Control Plane — לא מפרסם ישירות

[`ORGANIC_GROWTH.md`](ORGANIC_GROWTH.md): מפעל טיוטות + readiness Decision Pack לפי צורך/אירוע. ה־Control Plane עצמו אינו קורא Publish API; הוא מוסר ל־`vfigos`. `policy_id: instagram.publish` רשאי לאשר LOW-risk routine publication מכוח standing authorization כשה־instance וכל השערים המדויקים תקפים. אין direct/bypass autopost; אישור אדם נדרש רק כשה־policy מחזיר `REQUIRE_OWNER_APPROVAL` או כשיש חריג אנושי אמיתי.

## עדיין אסור

אוטו־DM, בוסט בלי ראש צוות, ₪ / Insights מומצאים, גוף חסום מומצא, משלוח ארצי, סוד בגיט, `fcc-server` ב־Cloud Agent, Send/Publish עם Visible Text Gate חסר, או Publish על בסיס transport readiness בלבד.
