# מפת הפעלה · VelvetOS Core

חבילת ידע לראש צוות. **לא SoT.** אם יש סתירה — `AGENTS.md` / `constitution/` / `office/control-plane.json` מנצחים.

נקרא מהריפו ב־2026-09-15 על `main` (אחרי fetch). סטטוסי LIVE להלן הם **כפי שמתועדים בקבצי הריפו**, לא כבדיקת ספק בסשן הזה.

---

## 1. מה זה

**VelvetOS Core** (`nocturney/velvetos-core`) הוא **Kernel / backend**: חוקים, מושבים, פקים, מודולים, חוזי אירועים על דיסק, סנסורים חישוביים.

כל עסק = **frontend instance** נפרד ששואב מודולים מהליבה (`packages/velvetos/REPOS.md`).

Tenant ייחוס פעיל בליבה: **Velvet Factory** — סטודיו הדפסת תלת־ממד בשדרות, איסוף עצמי, Instagram `@velvets_cloud`, WhatsApp `050-2517000` כרשומת עסק פנימית בלבד.

המטרה אינה אוטומציה עיוורת: להוריד עבודה מכנית, לשמור הקשר, לחבר אירועים — ולהשאיר החלטות רגישות אצל אדם.

נוסחה: Agent = Model + Harness (`AGENTS.md`).

---

## 2. שלוש שכבות (SoC)

סמכות: `packages/velvetos/LAYERS.md` · `ADR-THREE-LAYERS.md`.

| שכבה | עושה | לא עושה |
|---|---|---|
| **Office / HQ** | desk, בריף, CRM, החלטות, Gmail/IG דרך כלים, retro→signal | Print מ־HQ, אוטו־DM, בוסט בלי ראש צוות |
| **Kernel** (הריפו) | חוזים, פקים, מודולים, `check-*.py`, `component_state` | HTTP API חי, IoT daemon, broker |
| **Edge** (אופציונלי) | buffer מקומי, רצפה, Watchtower LAN, Mac/Windows host | מחיר, WhatsApp ללקוח, החלפת חוקה |

אירועים: JSON על דיסק (`schema/events.catalog.json`). אין תלות קוד Edge↔Office.

`component_state`: `Idle` · `Processing` · `Degraded` · `Syncing` · `Blocked`.

---

## 3. מופע VF מול הליבה

| פריט | מצב מתועד |
|---|---|
| Scaffold | `instances/velvet-factory/` |
| GitHub יעד | `nocturney/velvetos-velvet-factory` — `CORE.json` status **`scaffold-ready`** |
| Attach | `instances/velvet-factory/scripts/attach-core.sh` → `vendor/velvetos-core/` |
| Start מקומי | `START-VF.bat` · `docs/START-HERE-HE.md` |
| Workspace יומיומי מומלץ (START-HERE) | לפתוח את תיקיית ה־scaffold; ריפו נפרד **אופציונלי** |
| Bind תאימות בליבה | desk/STUDIO נשארים כאן עד cutover |

`constitution/TENANT.md` עדיין אומר «הריפו = VelvetOS — Velvet Factory» — ניסוח ישן מול `CORE.json`. **לא לאחד במסמך זה.** סמכות זהות: `CORE.json`.

Presets נוספים (`beauty-multi-ig`, `clinical-legal-opinions`) = **preset-only**, לא משרדים חיים.

---

## 4. שישה מושבים (desk + TEAM)

`.cursor/vf-desk.json` `seats` ו־`constitution/TEAM.md` מגדירים **שישה** תפקידים על פקים קיימים — לא שישה פקים חדשים.

| id | עברית | מחליט (desk) |
|---|---|---|
| `research` | מחקר/אורקסטרציה | הטמעת דפוסים לפקים; אין פק לרעיון; אין גוף מומצא |
| `lead` | ראש צוות | ₪, מה זז בלוח, מה נדחה, רטרו |
| `studio` | סטודיו | בריף פנייה, טיוטת הצעה, קופי. לא שולח WhatsApp |
| `growth` | צמיחה | חבילת תוכן; HQ מפרסם דרך כלי או failover |
| `ops` | תפעול | עלות, ספר, החלטות עסק. אין ₪ מומצא |
| `production` | ייצור | היתכנות, תור, מק״ט, רישיון קובץ |

`@chief-of-staff` יושב על מושב `lead` יחד עם `@studio-operations`.  
עבודה: החלטות פתוחות, מסירות מושבים, מה מחכה לכריסטיאן, לולאת למידה (`owner-memory.md`).

**מתח מתועד:** `constitution/STUDIO.md` ו־`packages/vfgraft/MAP.md` עדיין כותבים «5 מושבים». אריזת הפקים בין TEAM ל־desk אינה זהה (למשל `vfcovers` אצל צמיחה ב־desk ואצל סטודיו ב־TEAM). בניתוב יומיומי: **desk.json** לכלי/`@slug`; **TEAM.md** לחוקה. לא «לתקן» כאן.

Grok Bot «5 seats» = גבול שליחה היסטורי (IG/Gmail/מדפסות). **סופרסד חלקית:** HQ שולח Gmail/IG דרך כלים; מדפסות נשארות ברצפה; Grok = גיבוי אופציונלי (`SEND.md`).

---

## 5. צינור אחד

`פנייה → שיחה → הצעה → הדפסה → איסוף`  
= lead → talk → offer → fulfill → close.

אין משלוח ארצי מ־HQ.  
הצעה לציבור (`vfbiz/OFFERING.md`): **מוצרים מוכנים** + **הדפסה/מודל בהתאמה**. כמות וסוג לקוח הם מאפייני הזמנה, לא קו שירות שלישי. קו B2B נעול (`vfbiz/LOCK.md` · extraLock `b2b-line-locked`) — לוגו/QR/מפיות היו **דוגמאות**, לא שלושה מק״ט.

CTA ציבורי: הודעת Instagram.  
סגירה אנושית: הודעות IG / רשומת וואטסאפ פנימית + Invoice4U (STUDIO.md). HQ לא שולח WhatsApp ללקוח.

---

## 6. מערכות משנה

### 6.1 Office Control Plane — IMPLEMENTED

**תפקיד:** לאחד ולהקשיח SoTs קיימים. לא מערכת משרד שנייה.

- מפה: `office/control-plane.json`
- מדיניות: `office/control/POLICY.md`
- CLI: `python3 scripts/vf_control_plane.py` — `status` `watchdog` `gaps` `handoff` `followups` `review` `memory-hygiene` `simulate` `selftest` `brief-summary`
- Sensor: `scripts/check-office-control-plane.py` · `check-office-watchdog.py`
- Workflow: `.github/workflows/office-control-plane.yml` (כל 6ש)

חיבור: בולע משימות מכניות מ־ChatGPT (intake, sprint, insights review, memory hygiene, WIP→finished, dead-letter) ומשאיר ל־ChatGPT בריף + Research Seat + Publish Watch אופציונלי.

### 6.2 Jobs Sheet — IMPLEMENTED / FAIL-CLOSED · LIVE מתועד ב־README pulse

קנוני: Google Sheet `VF HQ · jobs` (`bindings.json` spreadsheetId `13jTA9FJLNWMEc2zEpdmXL5kNWYYguQHXeOdOPpDNgao`, `sheetName=Untitled` — לא מנחשים tab בשם `jobs`).

- Adapter: `vf_office.py jobs` + `vf_jobs_adapter.py`
- Workflow: `jobs-write-through.yml` (OIDC/WIF, בלי מפתח JSON בגיט)
- ראיה: `office/ledger/live/sync-receipt.json` — כתיבה חיה דורשת `status=written` + `verifiedFrom=sheets_values_get`
- Sheets נוספים ב־bindings (sku/quotes/books): **IDs קיימים**; האם write-through חי לכל אחד = **UNPROVEN** במסמך זה (רק jobs מוצהר canonical)

### 6.3 Living Studio — IMPLEMENTED (connective tissue)

`packages/velvetos/living-studio/` · `REGISTRY.json` (22 skills תפעוליים ב־README pulse; הקובץ כולל גם יכולות overlay).

CLI: `vf_living_studio.py` world-model / pulse / signal-room / intake / invisible-work / failure-museum / lab / opportunity / commercial-qa / content-universe / work-to-story / commission / selftest.

**חוק:** projection/router. World Model לקריאה בלבד. Signal Room מנרמל אירועים קיימים — לא bus.

### 6.4 Autonomy + Risk — IMPLEMENTED

`AUTONOMY.json` · `vf_autonomy.py` · `check-vf-autonomy.py` · `docs/AUTONOMY-COMPOSITION.md`.

מרכיב routing, waiting, approvals (projection), reliability, quiet hours מעל SoTs קיימים. לא queue שני. `execute` = GREEN/YELLOW.

### 6.5 Media Vault — IMPLEMENTED · intake LIVE מתועד

`docs/MEDIA-VAULT.md` + `packages/vfmedia/`.  
שורש Drive `Velvet Media` `1Yg3Rj0hKWTa86EXjaeu-f7CQXswSRMCv`. ארבע תיקיות נעולות ב־`FOLDERS.json`.

תפעול = intake נכנס→מקור. Cursor = schema. GrokBot = Drive MCP על הקבצים.  
Workflow `vfmedia-intake.yml` כל ~5 דקות (GHA best-effort).

### 6.6 Organic Growth / Content Factory — IMPLEMENTED / HUMAN-GATED

חוקה: `constitution/ORGANIC_GROWTH.md`.  
לא Publish API. שליחה = `vfigos`. אין autopost, אין auto-DM, אין poll→Print, אין המרה ודאית מוואטסאפ.

### 6.7 Instagram MCP + Insights — LIVE / VERIFIED (כפי ש־CAPABILITIES.json ו־README pulse)

MCP קנוני: `adelaidasofia/instagram-mcp`.  
`CAPABILITIES.json`: `currentStatus=ready`, `remote_access=ready`, Insights Graph v21 `deployed=true` (2026-09-09).  
`chatgptSmoke.publish`: **`available_not_live_tested`**.  
Desk note: `publish_story` מוצהר; live story publish **לא נבדק** באותו מעבר.  
מוטציות bio/caption: `supported=false` (`graph_mutation_matrix`).  
Team MCP scope: **not-verified**.  
DM כבוי תמיד.

Failover פרסום: Canva export + Drive `create_file` + Gmail אותו תור. לא לטעון שעלה לפיד.

### 6.8 Visible Text + Hebrew copy — IMPLEMENTED

`constitution/VISIBLE_TEXT.md` · `vfcopy` · `velvet-hebrew-copy` · FACT vs INVENTED (`needs_input` בלי אימות).

### 6.9 Production support — IMPLEMENTED

ארבע מיטות ב־`FLEET.json`. `vfprod.py route` לפי חומר.  
print.done → כרטיס → טיוטת תוכן.  
Watchtower = Edge מתוכנן/LAN — לא דמון בליבה.  
3D AI Studio: אתר + MCP OAuth; אין מפתח בגיט; אותו שער `vlicense`.

### 6.10 Video / Speech backends — IMPLEMENTED / host-verified לפי README

HyperFrames: Mac מועדף; Windows `host_smoke_verified` כגיבוי.  
Video adapters: EDL/Manim smoke ב־Windows; Remotion **license-gated**.  
Speech: VoiceStudio על `sderot-windows` LIVE/VERIFIED לפי README. Receipt דיבור ≠ אישור פרסום.  
סטטוס host **עכשיו** = UNPROVEN בלי doctor חי בסשן.

### 6.11 Gmail brief — IMPLEMENTED

`vfbriefux/MAIL.html` תצוגה 3.  
`python -m vfops.gmail_brief_send` / workflow `gmail-brief-send.yml`.  
שליחה ל־`nocturney@gmail.com`. Inbox **לא** ממלא את הבריף.  
Transport ≠ text readiness (`VISIBLE_TEXT` למסלול `owner-brief`).

### 6.12 Harness + engineering delivery + instruction QA — IMPLEMENTED

שש שכבות: guides, sensors, loop, memory, permissions, observability (`docs/HARNESS.md`).  
Sensors: כל `scripts/check-*.py` דרך `check-all.py` (README pulse: 69).  
Engineering chain + agent-instruction-qa + human-step-wizard + execution-discipline (RED→GREEN→REFACTOR, `safe_ruling` fail-closed).

### 6.13 Office-manager failover — OPTIONAL / GOVERNED

`docs/FAILOVER.md`. סדר: ChatGPT → Perplexity → Gemini → Grok → Cursor (טכני).  
קוראים SoT קיים + דוח השתלטות. לא בונים מחדש.  
**סתירה מתועדת:** FAILOVER.md עדיין כותב CTA וואטסאפ כציבורי. **סמכות CTA: `PUBLIC_CTA.md`.**

### 6.14 Project Request Gate — MANDATORY

כל בקשה מהותית עוברת `PROJECT-REQUEST-GATE.md`.  
Manifest דומיינים: creative_publication, copywriting, operations, production, sales_conversion, finance, research, system_engineering, instagram_action, general_business.

### 6.15 Social intelligence — IMPLEMENTED / EVIDENCE-GATED

`vfresearch/SOCIAL-INTELLIGENCE.md` · `check-social-intelligence.py`.  
Insights עצמיים קנוניים ב־Instagram MCP. Scraping פרטי אסור. ≥3 פוסטים מדודים לפני קידום pattern.

---

## 7. כלי HQ (desk) — מצבי חיבור מתועדים

מ־`.cursor/vf-desk.json` + ORCHESTRA. סטטוס desk ≠ smoke חי.

| כלי | מצב מתועד | Failover |
|---|---|---|
| Gmail `nocturney@gmail.com` | ready, read-and-send | Drive `create_file` + המשך; לא ממציאים פנייה |
| Calendar | ready, read; create לפי CALENDAR-OPS לרשת IG | «חסר לוח» + המשך |
| Drive | ready, search-and-create | לא תיקיות אישיות; לא שינוי share לכספת |
| Canva | ready (חוק desk) | `studio/render.py` → Superdesign |
| Instagram MCP | LIVE/VERIFIED לפי pulse | Canva+Drive+Gmail |
| WebSearch | desk | תזמורת ChatGPT+Gemini+Perplexity |
| GenerateImage | desk | Canva generate-design |
| 3DAI | OAuth / site | Drive + 3DAISTUDIO.md; לא Print |
| Sheets | Desktop / WIF ל־jobs | Drive CSV (`vfbooks/SHEETS.md`) |
| WhatsApp MCP | draft/search; VF `send=false` | `vf_office.py convert draft` |
| Gemini/ChatGPT API | מפתחות, לא אתרי מנוי | «חסר מפתח …» + שולחן אחר |
| Treg | **לא רלוונטי** | Web + orchestra |
| FCC | לא על Cloud Agent | מחקר desks |
| Mobbin | אופציונלי | תבניות vfbriefux / Superdesign |

---

## 8. סנסורים ו־CI

`python3 scripts/check-all.py` מריץ כל `scripts/check-*.py` (בלי רשת, בלי send).  
`check-all.yml` על push/PR ל־`main`.  
PR שנוגע ב־`packages/` `office/` `scripts/` `.github/workflows/` `constitution/` **חייב** עדכון README (חוזה living README).

אין LLM-as-judge לשערי ₪ / send / שמות פקים.

כישלון סנסור: לא להסתיר מאחורי עברית שוטפת. Retry פעם אחת, אז הסלמה.

---

## 9. מה אסור תמיד (קצר)

פירוט מלא: `GATES-AND-ESCALATION.md`.

- המצאת ₪, Insights, לקוחות, זמני ביצוע, Origin slugs, גוף חסום, סצנת רצפה
- SoT מקביל (קטלוג מדיה שני, תור dead-letter שני, Control Plane שני, runtime שני)
- Print מ־HQ, אוטו־DM, בוסט בלי lead, משלוח ארצי, Meta Business Suite כתלות
- טענת LIVE בלי verification
- Cloud login ל־chatgpt.com / gemini.google.com
- סודות בגיט

---

## 10. OPTIONAL / PLANNED / UNVERIFIED / UNKNOWN

סמן כך בכוונה. לא «כנראה עובד».

| נושא | סיווג | ראיה |
|---|---|---|
| ריפו frontend `velvetos-velvet-factory` כ־workspace יומי | scaffold-ready / אופציונלי | `CORE.json` · START-HERE |
| OpenPost כ־control plane פרסום | shadow / לא primary | `OPENPOST.json` |
| Live `publish_*` / `publish_story` בסשן זה | UNVERIFIED | CAPABILITIES `available_not_live_tested` |
| Team MCP scope | not-verified | CAPABILITIES |
| Standing publish authorization ב־instance החי | UNPROVEN עד קריאת פרופיל המופע | ORGANIC_GROWTH + instance json |
| Watchtower כדשבורד חי על LAN | planned/Edge playbook | `WATCHTOWER.md` |
| Origin vendor ל־tmp-* | origin-unreachable | `manifest.json` |
| `vfbrand` כפק במניפסט | חסר מהקטלוג המכונה | תיקייה קיימת; LOOP צורך אותה |
| מספר מושבים 5 מול 6 | סתירת מסמכים | TEAM/desk=6; STUDIO/MAP=5 |
| שעון בריף 07:00 מול 09:00 | סתירת מסמכים | ROUTINE=09:00; חוקה=07:00 |
| FAILOVER.md CTA וואטסאפ | מסמך מיושן בנקודה זו | PUBLIC_CTA מנצח |
| TENANT.md «הריפו=VF» | ניסוח מיושן | CORE.json מנצח |
| ORIGIN.md «Grok שולח» | סופרסד | SEND.md |
| SWC SHAs של GrokBot/Codex | עלולים להיות מאחור | `SHARED-WORK-COORDINATION.md` עצמו מזהיר `main` ≠ מה שרץ על המכונה |
| Sheets sku/quotes/books write-through | IDs קיימים; LIVE כתיבה UNPROVEN כאן | רק jobs מוצהר עם receipt |
| `GATES.json` items | ריק בקריאה | אין להמציא שערי בריף פתוחים |
| Insights «עכשיו» | אין ספירה בלי snapshot/MCP בסשן | לעולם לא למלא מספר |
| Host Mac/Windows כרגע online | UNPROVEN בלי doctor | README מתעד smoke היסטורי |
| ChatGPT protected automations כ־clock חי בסשן | מתועד ב־ROUTINE; חיבור ChatGPT **לא אומת כאן** | |

---

## 11. איך ראש צוות רץ את היום (תמצית)

1. `PROJECT-REQUEST-GATE` אם זו בקשה חדשה.
2. `vfmem.py who` / `vfgraft/MAP.md` — אל תפתח 273 rules.
3. `vf_control_plane.py status|watchdog|followups|handoff` — תמונת מצב.
4. צבע POLICY: לבצע / לדווח / להכין / להסלים.
5. Jobs רק דרך Sheet adapter; מדיה רק דרך vault; תוכן רק דרך PREFLIGHT+SEND.
6. כלי נפל → failover אותו תור.
7. סוף יום: DAILY-RETRO + owner-memory.
8. כל טענת הצלחה = sensor או receipt על הארטיפקט הסופי.

קריאה הבאה: `SOT-INDEX.md` · `GATES-AND-ESCALATION.md` · `LOOPS.md` · `PACKS-CATALOG.md`.
