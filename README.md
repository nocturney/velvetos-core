<p align="center">
  <img src="docs/assets/velvetos-readme-hero.svg" alt="VelvetOS — Headquarters & Operating System" width="100%">
</p>

<p align="center">
  <strong>Velvet Factory Headquarters & OS</strong><br>
  מערכת הפעלה עסקית חיה ל־Velvet Factory · A living operational OS for Velvet Factory
</p>

<p align="center">
  <a href="#עברית">עברית</a> · <a href="#english">English</a> · <a href="CHANGELOG.md">Changelog</a> · <a href="docs/START-HERE-HE.md">Start Here</a>
</p>

---

## System Pulse · דופק המערכת

<!-- OPERATIONAL-SNAPSHOT:START -->
<table>
<tr>
<td align="center"><strong>HEALTHY</strong><br><sub><span dir="ltr">System Health</span><br><span dir="rtl">בריאות מערכת</span></sub></td>
<td align="center"><strong>4</strong><br><sub><span dir="ltr">Live / Bound Paths</span><br><span dir="rtl">נתיבים חיים / מחוברים</span></sub></td>
<td align="center"><strong>2</strong><br><sub><span dir="ltr">Gated Actions</span><br><span dir="rtl">פעולות מבוקרות</span></sub></td>
<td align="center"><strong>0</strong><br><sub><span dir="ltr">Needs Attention</span><br><span dir="rtl">דורש טיפול</span></sub></td>
</tr>
<tr>
<td align="center"><strong>22</strong><br><sub><span dir="ltr">Living Studio Skills</span><br><span dir="rtl">יכולות</span></sub></td>
<td align="center"><strong>46</strong><br><sub><span dir="ltr">Sensors</span><br><span dir="rtl">חיישנים</span></sub></td>
<td align="center"><strong>8</strong><br><sub><span dir="ltr">Workflows</span><br><span dir="rtl">אוטומציות</span></sub></td>
<td align="center"><strong>31</strong><br><sub><span dir="ltr">Packs</span><br><span dir="rtl">חבילות</span></sub></td>
</tr>
</table>

| Pulse | Current committed evidence |
|---|---|
| **Instagram MCP** | LIVE / VERIFIED |
| **Instagram Insights** | LIVE / VERIFIED |
| **Media Intake / Drive** | LIVE / VERIFIED |
| **Jobs source of truth** | Google Sheet bound |
| **Waiting work** | 1 |
| **Owner blocked** | 0 |
| **Degraded tools** | 0 |
| **Last verified / refreshed evidence** | `2026-09-12T17:00:30Z` |

<div dir="rtl"><strong>מה השתנה:</strong> Office Control Plane מוטמע · followups=1 · dead_letters=0</div>
<div dir="ltr"><strong>What changed:</strong> Office Control Plane מוטמע · followups=1 · dead_letters=0</div>

<div dir="rtl"><strong>שינוי הטמעה אחרון:</strong> 2026-09-10 — **Jobs Sheet write-through harden:** bindings `sheetName=Untitled` (fail-closed, no guessed `jobs` tab); pre-write remote digest concurrency guard → conflict without mutation; behavioral tests in `…</div>
<div dir="ltr"><strong>Latest implementation change:</strong> 2026-09-10 — **Jobs Sheet write-through harden:** bindings `sheetName=Untitled` (fail-closed, no guessed `jobs` tab); pre-write remote digest concurrency guard → conflict without mutation; behavioral tests in `…</div>

<div dir="rtl"><strong>חוזה הפולס:</strong> הבלוק מציג את הראיות האחרונות שנשמרו בריפו. הוא לא מבצע קריאת ספק חיה בזמן טעינת GitHub ולא הופך “מוגדר” ל“מאומת”.</div>
<div dir="ltr"><strong>Pulse contract:</strong> this block reports the latest evidence committed to the repository. It never performs a live provider call while rendering GitHub, and never turns “configured” into “verified”.</div>
<!-- OPERATIONAL-SNAPSHOT:END -->

<p align="center">
  <strong>LIVE / VERIFIED</strong> · <strong>IMPLEMENTED</strong> · <strong>GATED</strong> · <strong>OPTIONAL</strong> · <strong>PLANNED</strong>
</p>

---

# ‏עברית

## ‏מה זה VelvetOS — בפשטות

‏**VelvetOS היא שכבת ניהול והפעלה לעסק שמחברת בין אנשים, AI, מידע, כלים ותהליכים — והופכת אותם למערכת אחת שיודעת להבין מה קורה, להחליט מה השלב הבא, לבצע מה שמותר לה לבצע, ולבקש אישור כשצריך.**

‏במקום שהעסק יתפזר בין שיחות, גיליונות, קבצים, אינסטגרם, תזכורות, כלי AI והרבה ידע שנשאר בראש של אנשים, VelvetOS נותנת לכל אלה מבנה משותף. פנייה יכולה להפוך לעבודה; עבודה יכולה לעבור לתכנון ייצור; תמונה מהשטח יכולה להיכנס למאגר המדיה ולהפוך לחומר לתוכן; נתוני ביצועים יכולים לחזור למערכת כלמידה; והכול נשען על מקורות אמת ברורים ועל היסטוריה שאפשר לבדוק.

‏המטרה אינה להחליף בני אדם באוטומציה עיוורת. המטרה היא **להוריד עבודה מכנית, למנוע טעויות, לשמור הקשר, לחבר בין חלקי העסק ולהשאיר החלטות רגישות בידיים הנכונות**. לכן כל כלי ויכולת מקבלים גבולות: מה מותר לבצע לבד, מה דורש אישור, מה רק מציע, ומה אסור למערכת להמציא או להניח.

### ‏איך זה עובד

‏VelvetOS פועלת כמו משרד דיגיטלי עם כמה שכבות שעובדות יחד: היא קולטת מידע ואירועים, מעדכנת מקורות אמת, בונה תמונת מצב, מפעילה Skills ו־handlers ייעודיים, מריצה חיישנים שבודקים שהחוזים נשמרים, ומייצרת תוצרים או פעולות בהתאם לרמת הסיכון. מעל הכול נמצא Control Plane שמוודא שהעבודה מתקדמת בלי ליצור מערכות כפולות ובלי לאבד את ההקשר העסקי.

‏המערכת בנויה כך ש־**אוטומציה אינה שווה סמכות מלאה**. קריאה, ניתוח, סיווג, הכנת טיוטה או סנכרון בטוח יכולים להיות אוטונומיים; מחיר, פרסום, מחיקה או פעולה בלתי הפיכה יכולים להישאר מאחורי gate. אם ספק חיצוני לא זמין או שאין הוכחה שהפעולה הצליחה, VelvetOS אמורה לדווח על זה כפי שהוא — לא להעמיד פנים שהכול עבד.

### ‏למה היא בנויה כך

- ‏**מקור אמת אחד לכל תחום** — כדי שאותו לקוח, job או asset לא יקבל כמה גרסאות סותרות.
- ‏**Evidence before confidence** — יכולת נחשבת חיה רק כשהיא מגובה בראיה, sensor או אימות provider.
- ‏**Fail-closed במקום ניחוש** — כשלא יודעים, עוצרים או מסמנים `needs_sync` / `needs_input`; לא ממציאים.
- ‏**Human-in-the-loop איפה שיש משמעות אמיתית** — מערכת טובה חוסכת החלטות קטנות, לא גונבת החלטות גדולות.
- ‏**למידה מהעבודה עצמה** — אירועים, תוצאות, תוכן, failures ו־Insights חוזרים למערכת ומשפרים את ההחלטה הבאה.
- ‏**יכולת להתרחב בלי לבנות הכול מחדש** — ה־Core, החוקים וה־patterns נועדו לאפשר בעתיד Offices/עסקים נוספים עם זהות ותהליכים משלהם, בלי לשכפל את הליבה.

### ‏כמוצר

‏אפשר לחשוב על VelvetOS כעל **Business Operating System עם AI מובנה**: לא עוד chatbot שעונה על שאלות, ולא רק אוסף אוטומציות. זו שכבה מתמשכת שיושבת מעל כלי העסק הקיימים, זוכרת את המבנה והחוקים, מחברת בין אירועים, מפעילה מומחים לפי צורך, שומרת על גבולות סמכות ומספקת תמונת מצב אמינה לבעלים ולצוות.

‏היום המופע הפעיל הוא **Velvet Factory**, סטודיו להדפסות תלת־ממד בשדרות. הכיוון קדימה הוא מערכת שניתן יהיה להצמיד לעסקים נוספים: אותו מנוע עקרונות, בקרה ואוטומציה — עם tenant, workflows, integrations ו־policies שמתאימים לכל עסק.

‏**Tenant פעיל:** Velvet Factory · שדרות  
‏**ערוצים פעילים:** Instagram `@velvets_cloud` · WhatsApp `050-2517000` · איסוף עצמי בשדרות

## ‏המבנה הטכני בקצרה

|‏ שכבה | תפקיד |
|---|---|
|‏ **Core / Kernel** | חוקים, schemas, modules, packs, sensors וחוזי אירועים משותפים |
|‏ **Office / Control Plane** | Intake, jobs, approvals, follow-ups, briefs, memory, content ומעקב ביצוע |
|‏ **Edge** | ביצוע מקומי/פיזי כשצריך לגעת במכונות או runtime מקומי |

‏ארכיטקטורה קנונית: [`docs/VELVETOS.md`](docs/VELVETOS.md) · [`packages/velvetos/LAYERS.md`](packages/velvetos/LAYERS.md) · [`packages/velvetos/ADR-THREE-LAYERS.md`](packages/velvetos/ADR-THREE-LAYERS.md)

> ‏**עיקרון:** מקור אמת אחד, הרבה תצוגות ואוטומציות. לא בונים מערכת מקבילה רק כי עלה רעיון חדש.

## ‏מפת היכולות

<table>
<tr><td><strong>Office Control Plane</strong></td><td><strong>IMPLEMENTED</strong></td><td dir="rtl" align="right">סטטוס משרד, watchdog, gaps, follow-ups, dead-letter, handoff, review, memory hygiene ו־WIP→finished.</td></tr>
<tr><td><strong>Living Studio</strong></td><td><strong>IMPLEMENTED</strong></td><td dir="rtl" align="right">שכבת חיבור על מקורות האמת הקיימים עם 22 Skills תפעוליים.</td></tr>
<tr><td><strong>Universal Intake</strong></td><td><strong>IMPLEMENTED</strong></td><td dir="rtl" align="right">נרמול וניתוב פניות/מסמכים/פגישות/מדיה ל־handlers קיימים, בלי Inbox מקביל.</td></tr>
<tr><td><strong>Jobs + Google Sheet bridge</strong></td><td><strong>IMPLEMENTED / FAIL-CLOSED</strong></td><td dir="rtl" align="right">pull/push/reconcile, הגנת concurrency וללא ניחוש tab.</td></tr>
<tr><td><strong>vfmem</strong></td><td><strong>IMPLEMENTED</strong></td><td dir="rtl" align="right">זיכרון עסקי והקשר לפני הפיכת notes/meetings/documents למצב תפעולי.</td></tr>
<tr><td><strong>Autonomy + Risk Gates</strong></td><td><strong>IMPLEMENTED</strong></td><td dir="rtl" align="right">הפרדה בין פעולות בסיכון נמוך לבין פעולות שדורשות gate/approval.</td></tr>
<tr><td><strong>Instagram MCP + Insights</strong></td><td><strong>LIVE / VERIFIED</strong></td><td dir="rtl" align="right">נתיבי Insights נתמכים ו־CTA audit מאומתים; mutations לא נתמכים לא מוצגים כאילו הם עובדים.</td></tr>
<tr><td><strong>Media Vault + vfmedia</strong></td><td><strong>IMPLEMENTED</strong></td><td dir="rtl" align="right">incoming → source → WIP → approved, עם checksum ו־persist-before-move.</td></tr>
<tr><td><strong>Hebrew Copy QA</strong></td><td><strong>IMPLEMENTED</strong></td><td dir="rtl" align="right">עברית טבעית, anti-AI QA ושער FACT vs INVENTED.</td></tr>
<tr><td><strong>Organic Growth / Content Factory</strong></td><td><strong>IMPLEMENTED / HUMAN-GATED</strong></td><td dir="rtl" align="right">עבודה אמיתית → רעיונות/טיוטות/approval queue; בלי autopost ובלי auto-DM.</td></tr>
<tr><td><strong>HyperFrames Video Backend</strong></td><td><strong>IMPLEMENTED / HOST ROUTE CONFIGURED</strong></td><td dir="rtl" align="right">`Mac-Office` / `sderot-mac` רשום כ־render host קנוני דרך ה־Cursor Edge worker הקיים, ללא tunnel/port חדש. HyperFrames 0.8.34, bootstrap ורינדור smoke מוכנים; LIVE ייקבע רק אחרי שה־bootstrap ירוץ בהצלחה על המק האמיתי.</td></tr>
<tr><td><strong>Production Support</strong></td><td><strong>IMPLEMENTED</strong></td><td dir="rtl" align="right">routing, חומר, spool/slice, maintenance signals ותכנון ייצור מבוקר.</td></tr>
<tr><td><strong>Gmail Operating Brief</strong></td><td><strong>IMPLEMENTED</strong></td><td dir="rtl" align="right">בריף HTML עם מדיה inline ושליחה כאשר קיימים credentials תקפים.</td></tr>
<tr><td><strong>Office-manager Failover</strong></td><td><strong>OPTIONAL / GOVERNED</strong></td><td dir="rtl" align="right">מעבר מבוקר לכלי חלופי בלי לייצר SoT נוסף.</td></tr>
<tr><td><strong>Agents / Skills catalog</strong></td><td><strong>AVAILABLE TOOLING</strong></td><td dir="rtl" align="right">קטלוג specialists גדול; עצם קיום prompt/rule לא נחשב הוכחת capability פעילה.</td></tr>
<tr><td><strong>Sensors + CI</strong></td><td><strong>ACTIVE</strong></td><td dir="rtl" align="right">חיישני `check-*.py` ו־GitHub Actions כראיית חוזה executable.</td></tr>
</table>

## ‏אוטומציות פעילות בריפו

- full sensor suite
- Gmail brief send
- Office Control Plane loop
- publish-bridge cleanup
- VelvetOS research
- weekly deck generation
- vfmedia intake

‏קובץ workflow מוכיח שהאוטומציה קיימת; פעולה חיצונית נחשבת **LIVE** רק אחרי אימות אמיתי מול provider/runtime.

## ‏מקורות אמת

|‏ תחום | מיקום קנוני |
|---|---|
|‏ זהות Core | `packages/velvetos/CORE.json` |
|‏ שכבות | `packages/velvetos/LAYERS.md` |
| Event contracts | `packages/velvetos/schema/events.catalog.json` |
| Office control | `office/control-plane.json` + `office/control/` |
| Living Studio | `packages/velvetos/living-studio/` |
| Media catalog | `packages/vfmedia/` |
|‏ חוקי מערכת | `constitution/` |
| Sensors | `scripts/check-*.py` |
| Workflows | `.github/workflows/` |
|‏ היסטוריית שינויים | [`CHANGELOG.md`](CHANGELOG.md) |
|‏ הנחיות agents | [`AGENTS.md`](AGENTS.md) |

## ‏חוקי אמת עסקית

- ‏לא ממציאים מחירי ₪.
- ‏לא ממציאים לקוחות, הזמנות או זמני ביצוע.
- ‏לא טוענים שפעולת provider הצליחה בלי ראיה.
- ‏לא ממציאים Origin slugs; אם לא ידוע — `unknown` ([`docs/ORIGIN-SLUGS.md`](docs/ORIGIN-SLUGS.md)).
- ‏לא יוצרים source of truth מקביל בשקט.
- ‏פרסום ותקשורת חיצונית כפופים ל־approval/capability gates.
- ‏איסוף נשאר בשדרות כל עוד הרשומה הקנונית לא שונתה.

## ‏README חי

‏ה־README הוא חלק מהמוצר. שינוי מהותי ב־`packages/`, `office/`, `scripts/`, `.github/workflows/` או `constitution/` מחייב עדכון README באותו PR, אלא אם מדובר בשינוי פנימי שאינו משנה capability.

‏ה־System Pulse למעלה **נוצר מנתוני הריפו עצמו**. להרצה ידנית:

```bash
python3 scripts/update-readme-snapshot.py
python3 scripts/update-readme-snapshot.py --check
```

**Definition of Done:** implementation + evidence/sensor + changelog + README capability/status update.

---

# English

## What VelvetOS is — in plain language

**VelvetOS is a business operating layer that connects people, AI, information, tools and workflows into one system that can understand what is happening, determine the next step, execute what it is allowed to execute, and ask for approval when human judgment matters.**

Instead of letting the business fragment across chats, spreadsheets, files, Instagram, reminders, AI tools and knowledge trapped in people's heads, VelvetOS gives those parts a shared operating model. An inquiry can become a job; a job can move into production planning; media from real work can enter the media vault and become content material; performance data can return as learning; and every important transition can remain tied to a canonical source and auditable evidence.

The goal is not blind automation or replacing people. It is to **remove mechanical work, reduce mistakes, preserve context, connect the business end-to-end and keep consequential decisions with the right person**. Every capability therefore has an authority boundary: what can run autonomously, what requires approval, what may only recommend, and what the system is never allowed to invent or assume.

### How it works

VelvetOS behaves like a digital office made of cooperating layers. It ingests information and events, updates canonical sources, builds an operational picture, routes work to specialized skills and handlers, runs sensors that verify contracts, and produces outputs or actions according to risk. A Control Plane sits across those workflows so new automation extends the existing operating model instead of creating disconnected mini-systems.

The system deliberately separates **automation from authority**. Reading, classification, analysis, safe synchronization and draft generation can be autonomous; pricing, publishing, deletion or irreversible actions can remain gated. When a provider is unavailable or success cannot be proven, VelvetOS is expected to say so rather than report fictional completion.

### Why it is designed this way

- **One canonical source per domain** — customers, jobs and assets should not develop competing versions of truth.
- **Evidence before confidence** — a capability is treated as live only when backed by a sensor, receipt or provider verification.
- **Fail closed instead of guessing** — unknown state becomes `needs_sync` / `needs_input`, not fabricated certainty.
- **Human-in-the-loop where consequences matter** — remove repetitive decisions without stealing important ones.
- **Learn from real work** — outcomes, failures, content performance and operational signals feed the next decision.
- **Scale without rebuilding the system** — Core laws and patterns are intended to support additional business Offices with their own tenants, workflows, integrations and policies.

### As a product

VelvetOS can be understood as a **Business Operating System with AI built into the operating model**. It is not merely a chatbot and not merely a collection of automations. It is a persistent layer above the tools a business already uses: it understands the structure and rules, connects events across systems, invokes specialists when needed, preserves authority boundaries and gives owners and teams a reliable operational picture.

The active deployment today is **Velvet Factory**, a 3D-printing studio in Sderot. The direction forward is a reusable operating layer that can support additional businesses: the same Core principles, governance and automation patterns, with each business receiving its own tenant identity, workflows, integrations and policy boundaries.

**Active tenant:** Velvet Factory · Sderot  
**Active channels:** Instagram `@velvets_cloud` · WhatsApp `050-2517000` · local pickup in Sderot

## Technical shape at a glance

| Layer | Role |
|---|---|
| **Core / Kernel** | Shared laws, schemas, modules, packs, sensors and event contracts |
| **Office / Control Plane** | Intake, jobs, approvals, follow-ups, briefs, memory, content and completion tracking |
| **Edge** | Local/physical execution when work must reach machines or a local runtime |

Canonical architecture: [`docs/VELVETOS.md`](docs/VELVETOS.md) · [`packages/velvetos/LAYERS.md`](packages/velvetos/LAYERS.md) · [`packages/velvetos/ADR-THREE-LAYERS.md`](packages/velvetos/ADR-THREE-LAYERS.md)

> **Principle:** one source of truth, many projections and automations. New ideas extend existing SoTs instead of creating parallel systems.

## Capability map

<table>
<tr><td><strong>Office Control Plane</strong></td><td><strong>IMPLEMENTED</strong></td><td>Status, watchdog, gaps, follow-ups, dead-letter, handoff, review, memory hygiene and WIP→finished.</td></tr>
<tr><td><strong>Living Studio</strong></td><td><strong>IMPLEMENTED</strong></td><td>Connective layer over canonical SoTs with 22 operational skills.</td></tr>
<tr><td><strong>Universal Intake</strong></td><td><strong>IMPLEMENTED</strong></td><td>Normalizes and routes inquiries, documents, meetings and media into existing handlers.</td></tr>
<tr><td><strong>Jobs + Google Sheet bridge</strong></td><td><strong>IMPLEMENTED / FAIL-CLOSED</strong></td><td>Pull/push/reconcile with concurrency guards and no guessed tab names.</td></tr>
<tr><td><strong>vfmem</strong></td><td><strong>IMPLEMENTED</strong></td><td>Business context before notes, meetings and documents become operational state.</td></tr>
<tr><td><strong>Autonomy + Risk Gates</strong></td><td><strong>IMPLEMENTED</strong></td><td>Separates low-risk execution from actions that require explicit approval.</td></tr>
<tr><td><strong>Instagram MCP + Insights</strong></td><td><strong>LIVE / VERIFIED</strong></td><td>Supported Insights reads and CTA audit are verified; unsupported mutations are not presented as working writes.</td></tr>
<tr><td><strong>Media Vault + vfmedia</strong></td><td><strong>IMPLEMENTED</strong></td><td>Incoming → source → WIP → approved with checksums and persist-before-move.</td></tr>
<tr><td><strong>Hebrew Copy QA</strong></td><td><strong>IMPLEMENTED</strong></td><td>Natural Hebrew, anti-AI QA and FACT vs INVENTED gates.</td></tr>
<tr><td><strong>Organic Growth / Content Factory</strong></td><td><strong>IMPLEMENTED / HUMAN-GATED</strong></td><td>Real work becomes drafts and approval candidates; no default autopost or auto-DM.</td></tr>
<tr><td><strong>HyperFrames Video Backend</strong></td><td><strong>IMPLEMENTED / HOST ROUTE CONFIGURED</strong></td><td>`Mac-Office` / `sderot-mac` is registered as the canonical render host through the existing Cursor Edge worker, with no extra tunnel or inbound port. HyperFrames 0.8.34, bootstrap and smoke render are ready; LIVE requires the bootstrap to pass on the real Mac.</td></tr>
<tr><td><strong>Production Support</strong></td><td><strong>IMPLEMENTED</strong></td><td>Routing, material/spool planning and maintenance signals.</td></tr>
<tr><td><strong>Gmail Operating Brief</strong></td><td><strong>IMPLEMENTED</strong></td><td>HTML + inline media brief path when valid credentials exist.</td></tr>
<tr><td><strong>Office-manager Failover</strong></td><td><strong>OPTIONAL / GOVERNED</strong></td><td>Controlled takeover without creating another source of truth.</td></tr>
<tr><td><strong>Agents / Skills catalog</strong></td><td><strong>AVAILABLE TOOLING</strong></td><td>Large specialist catalog; a prompt/rule file alone is not proof of active capability.</td></tr>
<tr><td><strong>Sensors + CI</strong></td><td><strong>ACTIVE</strong></td><td>`check-*.py` sensors and GitHub Actions provide executable contract evidence.</td></tr>
</table>

## Operational workflows

The repository currently carries workflows for the sensor suite, Gmail brief, Office Control Plane, publish-bridge cleanup, VelvetOS research, weekly deck generation and vfmedia intake.

A workflow file proves automation exists; provider-dependent behavior is **LIVE** only after real provider/runtime verification.

## Canonical sources

| Area | Canonical location |
|---|---|
| Core identity | `packages/velvetos/CORE.json` |
| Layer model | `packages/velvetos/LAYERS.md` |
| Event contracts | `packages/velvetos/schema/events.catalog.json` |
| Office control | `office/control-plane.json` + `office/control/` |
| Living Studio | `packages/velvetos/living-studio/` |
| Media catalog | `packages/vfmedia/` |
| Constitution | `constitution/` |
| Sensors | `scripts/check-*.py` |
| Workflows | `.github/workflows/` |
| Change history | [`CHANGELOG.md`](CHANGELOG.md) |
| Agent guidance | [`AGENTS.md`](AGENTS.md) |

## Living README contract

This README is part of the product. Material capability/runtime changes must update it in the same PR.

The System Pulse above is generated from repository sources:

```bash
python3 scripts/update-readme-snapshot.py
python3 scripts/update-readme-snapshot.py --check
```

**Definition of Done:** implementation + evidence/sensor + changelog + README capability/status update.

---

## Quick health check · בדיקת בריאות מהירה

```bash
python3 scripts/velvetos.py core
python3 scripts/velvetos.py modules
python3 scripts/velvetos.py instances
python3 scripts/check-all.py
python3 scripts/check-commission-isolation.py
python3 scripts/update-readme-snapshot.py --check
```

## Read next · המשך קריאה

[`CHANGELOG.md`](CHANGELOG.md) · [`AGENTS.md`](AGENTS.md) · [`docs/HARNESS.md`](docs/HARNESS.md) · [`docs/FAILOVER.md`](docs/FAILOVER.md) · [`docs/MEDIA-VAULT.md`](docs/MEDIA-VAULT.md) · [`constitution/`](constitution/) · [`packages/velvetos/`](packages/velvetos/)

---

<p align="center"><strong>If VelvetOS can really do it, the README should say so.<br>אם VelvetOS באמת יודע לעשות את זה — ה־README צריך להגיד את זה.</strong></p>