# שערים והסלמה · GATES-AND-ESCALATION

סמכות צבעים: **`office/control/POLICY.md`** (Don't Bother Christian).  
`constitution/RISK.md` ו־`office/control-plane.json` → `dontBotherChristian` הם אותו מפה.  
משטח כריסטיאן (נעילה 7.9.2026): **החלטה · חסם קשיח · פרסום חי שדורש אותו בלבד.**  
אסור להעלות מדדים חלשים, «רמה נמוכה», נתיחת איכות אחרי פרסום, או בושת כלים.

## מתי לפעול / להכין / להסלים

| צבע | משמעות | דוגמאות מ־POLICY.md | מה ראש צוות עושה |
|---|---|---|---|
| **GREEN** | לבצע אוטונומית | סיווג מדיה, ארכיון, מצב פנימי, טיוטת קופי פנימית, קריאה/חיפוש, תחזוקת HANDOFF, תיקוני איכות שגרתיים | לבצע; לא להעיר את כריסטיאן |
| **YELLOW** | לבצע + לדווח בבריף | הכנת תוכן, ארגון Drive/מדיה, עדכון לוח, מעקב production→content, watchdog דטרמיניסטי | לבצע; שורה בבריף/HANDOFF |
| **ORANGE** | להכין בלבד, לא לבצע | הודעה חיצונית חדשה, טענה ציבורית שדורשת אימות, שינוי מדיניות, פרסום חריג, חסר שער חובה | חבילת הכנה + המתנה לאישור |
| **RED** | אישור כריסטיאן | רכישה/תשלום, שינוי מחיר, פעולה חיצונית הרסנית, הרשאת פרסום שדורשת בעלים, חסם קשיח בלי failover, מחיקה בלתי הפיכה, התחייבות עסקית לא מכוסה | לא לבצע; פקטת הסלמה |

משטח בעלים (read model): Control Plane מציג **אדום** ו־**כתום אמיתי** בלבד. תור האישורים הקנוני נשאר `packages/vfgrowth/data/approval-queue.json`.

Autonomy: `vf_autonomy.py execute` מותר ל־green/yellow בלבד (`office/control-plane.json` + `AUTONOMY.json`).  
`quiet-plan` = פעולות פנימיות הפיכות. Destructive autonomy = false.

## שערי אדם שתמיד נשארים (Kernel events)

מ־`packages/velvetos/schema/events.catalog.json` → `humanGates` + `LAYERS.md`:

| שער | מי | אסור ל־HQ |
|---|---|---|
| מחיר מכירה / שינוי ₪ | ראש צוות / כריסטיאן | להמציא או לסגור בלי סכום מאומת (`X ₪`) |
| WhatsApp ללקוח | אדם `050-2517000` | `send=false` ב־VF; טיוטה בלבד אחרי Visible Text |
| Boost / Ads | ראש צוות אחרי הוכחה אורגנית | `@paid-social-strategist` לא פותח קמפיין לבד |
| Print מ־HQ | רצפה / Edge | `vfprod.py` ממליץ מיטה; לא לוחץ Print |
| Auto-DM / `send_dm` | נעול תמיד | גם כש־Instagram MCP חי |
| תיוג משתמש בלי opt-in | נעול | |
| IG autopost כ־Control Plane | נעול | Organic Growth מייצר טיוטות; publish דרך `vfigos` + שערים |

## שער בקשת פרויקט (לפני כל עבודה מהותית)

`packages/velvetos/PROJECT-REQUEST-GATE.md` — **MANDATORY · FAIL-CLOSED**.

1. Baseline: חוקה + `PUBLIC_CTA` + `VISIBLE_TEXT` + `ORCHESTRA` + control-plane + `OFFERING.md`.
2. סיווג דומיין מ־`PROJECT-AUTHORITY-MANIFEST.json`.
3. טעינת פקים/skills/SoT רלוונטיים בלבד — לא 273 specialists.
4. `project_preflight: PASS|BLOCKED`. חסר/סותר/לא ניתן לאימות = `BLOCKED` / `needs_sync`.
5. ביצוע דרך הכלים האמיתיים, לא «כאילו».
6. Postflight על הארטיפקט הסופי לפני `done` / `published` / `sent`.

סדר סתירות:  
`system/safety/rights` → `Constitution + Product Truth + verified facts` → `tenant/instance` → `domain pack` → `owner-approved visual/copy` → `local creative preference`.

## Visible Text Gate

`constitution/VISIBLE_TEXT.md` · יישום: `packages/vfcopy`.

כל prose ש־AI כתב ושעין אדם תקרא — כריסטיאן, לקוח, קהל, שותף — חייב `visible_text_gate: PASS` על **הטקסט המדויק** לפני final/send/publish/render.

- אין `PASS` כי הקובץ/ה־skill קיימים.
- IDs / hashes / URLs / לוגים / ערכים ממקור נשארים literal.
- בריף לבעלים = `owner-brief` (לא קול Instagram).
- כיתוב ציבורי = `public-social` + `PUBLIC_CTA.md`.
- כשל כלי כתיבה = `UNPROVEN`/`BLOCKED`, לא סימון ידני.

## שרשרת פרסום Instagram (שלושה היבטים נפרדים)

מ־`constitution/SEND.md` + `packages/vfigos/SEND.md` + `PUBLICATION-STATES.json`:

| היבט | מה זה מוכיח | מה זה לא |
|---|---|---|
| Transport readiness | `vf_send_preflight.py --gate instagram --transport-only` | לא הרשאת publish |
| Human-visible copy | Visible Text + `vfcopy` + digest | לא creative QA |
| Exact-package creative | PREFLIGHT v2 + Brand Guardian + Rubric ≥20/25 + `final_package_sha256` | שינוי אחרי QA מבטל |

רק `publishAuthorized=true` + exit 0 מאפשרים `publish_*`.  
אחרי כלי: `list_media` / `get_media` → `published_verified` / `liveVerified`.  
בלי אימות: `publish_pending_verification`. **אסור לכתוב «עלה לפיד»**.

מצבים (לא לערבב): `prepared` · `approved` · `scheduled` · `staged` · `fetch_verified` · `publishRequested` · `published_verified`.

Creative Autopilot (`constitution/ORGANIC_GROWTH.md`): standing authorization ב־instance יכול לאפשר tool publish אחרי כל השערים. בלי standing authorization — `approved_for_manual_posting` / הכנה בלבד. מצב ה־instance החי **לא אומת במסמך זה** — ראה `instances/velvet-factory/instance/velvet-factory.json` לפני טענת standing auth.

OpenPost: `packages/vfigos/OPENPOST.json` `integrationMode: shadow`. SEND.md מזכיר גם `shadow_pending_runtime_deploy`. **לא primary.** Failover: Instagram MCP → Canva+Drive+Gmail.

## שערי תוכן נוספים (fail-closed)

| שער | סמכות | נכשל = |
|---|---|---|
| Product Truth | `packages/vfbrand/BRAND-SOURCE-OF-TRUTH.md` | אסור מוצר סינתטי כ־showcase/מכירה |
| Brand asset / CTA lock | `vfom/BRAND-ASSET-LOCK.md` · `PUBLIC_CTA.md` | אין וואטסאפ בכיתוב/פריים |
| EDIT-GATE | `packages/vfgrowth/EDIT-GATE.md` | אין שיבוץ JPEG גולמי |
| Rights / לקוח / CAD פרטי | ORGANIC_GROWTH Human Required | לא מפרסמים |
| Media `versionApproval` | `docs/MEDIA-VAULT.md` | תיקיית מאושר לבד ≠ הוכחה |
| `offering_shape` | `vfbiz/OFFERING.md` | אין קו שירות שלישי לפי סוג לקוח/כמות |
| חומר / גרמים | `vfcost.py` | חסר גרמים = סירוב, לא ניחוש ₪ |

## שערי בריף 01 (כן / לא / דחה)

`packages/vfops/hq/GATES.md` + `GATES.json`  
CLI: `python3 scripts/vfops_loop.py gate --id G-001 --decision yes|no|defer`

- לחיצת אדם במייל או CLI. **לא** סגירת WhatsApp. **לא** Print.
- `quote` אחרי `yes` → תור רצפה רק אם יש סכום מראש צוות; אחרת `ממתין לסכום`.
- `content` אחרי `yes` → `vfigos` רק אחרי PREFLIGHT. לא Publish מכאן.
- `GATES.json.items` היה ריק בקריאה לתיעוד זה (2026-09-15) — אין להמציא שערי בריף פתוחים.

Organic Growth באותו חריץ: `python3 scripts/vf_organic_growth.py brief` — אישור ≠ פרסום.

## הסלמת רתמה (לא כריסטיאן)

מ־`packages/vfharness/EMBED.md` + `packages/vfharness/scripts/vf_graceful_escalation.py`:

1. retry תחום (מקסימום לפי AGENTS: 2 לשלב).
2. fallback כלי (`ORCHESTRA.md`).
3. downgrade scope בטוח.
4. `safe_ruling` רק אם מקומי+הפיך וללא security/authority/external-side-effect; ברירת מחדל `safe_to_rule=False`.
5. עדיין חסום / sensor אדום → `packages/vfharness/templates/escalation.md`. לא לעקוף gate.

חסם אנושי אמיתי (לא «תעביר לבעלים את כל המשימה»): `packages/vfharness/playbooks/human-step-wizard.md` — מסיימים הכל, מבקשים פעולה אחת, מוודאים, ממשיכים.

Thrash: אותו sensor נכשל שלוש פעמים → עוצרים, מחזירים ארטיפקט + בעיות פתוחות.

## מתי כן להעיר את כריסטיאן

| כן | לא |
|---|---|
| החלטת מחיר / רכישה / שינוי הצעה | מדד חלש / «הרמה נמוכה» |
| חסם קשיח אחרי failover מתועד | כשל MCP עם גיבוי שעובד |
| פרסום חי שדורש בעלים במפורש | ליטוש Canva / תיקון כיתוב |
| מחיקה בלתי הפיכה / הרשאות Drive גלובליות | שיבוץ פנימי על CALENDAR.md |
| קו B2B / אתר שיווקי / TikTok / ads | «לא השתמשתם בכלים» |
| זכויות לקוח לא ברורות לפרסום | אין ספירה (רושמים «אין ספירה» פנימית) |

טלפון עסק פנימי: `050-2517000` — **לא** בקופי ציבורי.

## פקטת הסלמה

תבנית: `packages/vfharness/templates/escalation.md`.  
Dead-letter אם הפעולה נכשלה אחרי failover: `office/control/dead-letter.json` (לא לאבד בשקט).

## לעולם לא מ־HQ

- Print / G-code / חיבור למצלמת מדפסת.
- Auto-DM, follow-back, story hacks, רכישת עוקבים.
- משלוח ארצי.
- המצאת ₪, Insights, גוף חסום, Origin slug, סצנת רצפה.
- טענת LIVE בלי verification evidence.
- פתיחת `gemini.google.com` / `chatgpt.com` מ־Cloud Agent.
- התקנת fcc-server / DeepSeek Harness / orchestrator שני (Orca, CrewAI, amux…).
- שינוי הרשאות שיתוף על כספת המדיה.
- מחיקת קבצי vault.
- פתיחת תיקיות Drive אישיות/רפואיות/משפטיות בלי שהמשתמש נקב בהן.
