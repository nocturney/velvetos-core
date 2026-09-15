# אינדקס מקורות אמת · SOT-INDEX

כל שורה מצביעה ל**סמכות קנונית אחת**. תצוגות, CLI, HANDOFF ו־Living Studio הם נגזרות — לא SoT מתחרה.

כלל: `office/control-plane.json` → `sourcesOfTruth` + `locks`.  
אם שני קבצים טוענים סמכות על אותו דומיין — החיישן חייב ליפול (`scripts/check-office-control-plane.py`).

סטטוס LIVE/IMPLEMENTED בטבלה הוא **כפי שמתועד בריפו** (README pulse / capability files). אין כאן אימות ספק חי.

## ליבה / שכבות / מופע

| דומיין | סמכות קנונית | מצביעים / נגזרות | הערה |
|---|---|---|---|
| זהות Core | `packages/velvetos/CORE.json` | `KERNEL.md` · `docs/VELVETOS.md` | backend kernel, לא frontend עסק |
| שלוש שכבות | `packages/velvetos/ADR-THREE-LAYERS.md` + `LAYERS.md` | `CORE.json.layers` | Edge / Kernel / Office. לא broker |
| ריפואים | `packages/velvetos/REPOS.md` | `CORE.json.repos` · `INSTANCE.md` | VF scaffold: `instances/velvet-factory/` |
| חוזי אירועים (דיסק) | `packages/velvetos/schema/events.catalog.json` | `event-envelope.schema.json` | לא message bus |
| מודולים | `packages/velvetos/modules/catalog.json` | `python3 scripts/velvetos.py modules` | תמיד בליבה; מופע בוחר subset |
| שער בקשה | `packages/velvetos/PROJECT-REQUEST-GATE.md` | `PROJECT-AUTHORITY-MANIFEST.json` · `scripts/vf_project_preflight.py` | אין עבודה מהותית לפני `project_preflight: PASS` |
| קטלוג פקים (מכונה) | `packages/manifest.json` | `packages/README.md` | `vfbrand` חי ב־`packages/vfbrand/` אבל **לא** ברשימת `packs` של המניפסט — ראה UNKNOWN |
| מפה טוקן-חסכונית | `packages/vfgraft/MAP.md` | `graph/` · `graph.json` | לפני grep למחסן 273 |
| שאילתת משרד | `scripts/vfmem.py` | `docs/VFMEM.md` · `packages/vfmem/` | לא מתקינים binary של codebase-memory-mcp |
| מדריך סוכן | `AGENTS.md` | `packages/vfharness/EMBED.md` | המדריך מנצח את השיחה |

## חוקה / זהות VF

| דומיין | סמכות קנונית | מצביעים | הערה |
|---|---|---|---|
| חוקת משרד | `constitution/CONSTITUTION.md` | `constitution/README.md` | |
| עובדות סטודיו VF | `constitution/STUDIO.md` | `.cursor/vf-desk.json` → `studio` | איסוף שדרות בלבד |
| מושבים | `constitution/TEAM.md` | `.cursor/vf-desk.json` → `seats` | TEAM=6; STUDIO/MAP עדיין כותבים 5 — ראה מתח מתועד |
| CTA ציבורי | `constitution/PUBLIC_CTA.md` | `PUBLIC_CURRENT_CTA` / `BUSINESS_CONTACT_RECORD` | WhatsApp לא CTA ציבורי |
| שליחה | `constitution/SEND.md` | `packages/vfigos/SEND.md` · `scripts/vf_send_preflight.py` | HQ שולח Gmail/IG דרך כלים |
| טקסט לעין אדם | `constitution/VISIBLE_TEXT.md` | `packages/vfcopy` | אין `PASS` בלי ביצוע בפועל |
| תזמורת כלים | `constitution/ORCHESTRA.md` | `docs/FAILOVER.md` · `degraded-mode.md` | failover ≠ המצאה |
| צמיחה אורגנית (חוק) | `constitution/ORGANIC_GROWTH.md` | `packages/vfgrowth/ORGANIC-GROWTH.md` | לא בוט פרסום |
| סיכון (מצביע) | `constitution/RISK.md` | **SoT:** `office/control/POLICY.md` | RISK הוא mirror |
| הצעה לציבור | `packages/vfbiz/OFFERING.md` | `vfbiz/LOCK.md` | מוצרים מוכנים + בהתאמה; כמות≠קו שירות |
| מותג ויזואלי | `packages/vfbrand/BRAND-SOURCE-OF-TRUTH.md` | `vfom/BRAND-ASSET-LOCK.md` · EDIT-GATE | לא במניפסט הפקים |
| Origin slugs | `docs/ORIGIN-SLUGS.md` | `unknown` / `origin-slug-unknown` | לא ממציאים `tmp-…` |
| תגיות | `constitution/TAGS.md` + `tags.md` | | שני שמות קבצים חיים — לא לאחד מכאן |

## בקרת משרד

| דומיין | סמכות קנונית | CLI / sensor | הערה |
|---|---|---|---|
| מפת Control Plane | `office/control-plane.json` | `scripts/vf_control_plane.py` · `check-office-control-plane.py` | unify, לא מערכת שנייה |
| Don't Bother Christian | `office/control/POLICY.md` | `dontBotherChristian` ב־control-plane | GREEN/YELLOW/ORANGE/RED |
| Jobs | Google Sheet `VF HQ · jobs` דרך `office/ledger/bindings.json` | `vf_office.py jobs` · `vf_jobs_adapter.py` · `jobs-write-through.yml` | cache מקומי `office/ledger/live/jobs.csv` (gitignore) **אינו** SoT |
| קבלת סנכרון Jobs | `office/ledger/live/sync-receipt.json` | | כתיבה חיה דורשת WIF write + Sheets read-back |
| Inbox משרד | `office/control/inbox.json` | Universal Intake | לא inbox מקביל |
| Dead-letter | `office/control/dead-letter.json` | `vf_dead_letter.py` | מצביע תאימות: `packages/vfharness/dead-letter/queue.json` **לא** SoT |
| Followups / WIP→finished | `office/control/followups.json` | `vf_control_plane.py followups` | מצביע: `packages/vfgrowth/data/production-content-followups.json` |
| HANDOFF מנהל | `office/control/HANDOFF.json` | `HANDOFF-he.md` | מסירה חיה לכל AI |
| יומן החלטות | `office/control/decisions.jsonl` | append-only / supersede | |
| לולאת צריכת פקים | `packages/vfops/LOOP.json` | `vfops_loop.py` · `check-vfops-loop.py` | consume map, **לא** שעון (ראה ROUTINE.md) |
| שעון אוטומציות בעלים | `packages/vfops/ROUTINE.md` | ChatGPT protected inventory | 09:00 brief; לא 07:00 כשעון חי |
| זיכרון בעלים | `packages/vfops/data/owner-memory.md` | `vfmem/MEMORY-UPDATE.md` · `DAILY-RETRO.md` | |
| תבניות לקוח | `office/clients/` | INTAKE / CLIENT-RECORD templates | אין PII מיותר בגיט |
| תיאום משותף | `docs/SHARED-WORK-COORDINATION.md` | | לוח בעלות, לא task runtime |

## מדיה / תוכן / פרסום

| דומיין | סמכות קנונית | CLI / sensor | הערה |
|---|---|---|---|
| כספת מדיה | `docs/MEDIA-VAULT.md` | `packages/vfmedia/FOLDERS.json` | 4 תיקיות נעולות; אין תיקייה חמישית |
| קטלוג מדיה | `packages/vfmedia/catalog.json` | `catalog.schema.json` · `vfmedia.py` · `check-vfmedia.py` | העלאה ≠ אישור |
| לוח תוכן | `packages/vfgrowth/CALENDAR.md` | `CALENDAR-OPS.md` | שיבוץ ≠ פרסום |
| תור אישור תוכן | `packages/vfgrowth/data/approval-queue.json` | `vf_organic_growth.py queue` | תור קנוני יחיד |
| PREFLIGHT | `packages/vfgrowth/PREFLIGHT.md` | `preflight/<id>.md` | נכשל-סגור חוסם שיבוץ |
| EDIT-GATE | `packages/vfgrowth/EDIT-GATE.md` | Canva / vfcovers / vfcanva | אין JPEG גולמי |
| קול כיתוב | `packages/vfcopy/VOICE.md` | `VOICE-CHART.md` · `VOICE-RESEARCH.md` | תהליך-קצר / סיפור-מוצר |
| מצבי פרסום | `packages/vfigos/PUBLICATION-STATES.json` | `check-publication-states.py` | `liveVerified` רק אחרי אימות |
| יכולות Instagram | `packages/vfigos/CAPABILITIES.json` | `CONNECT-IG.md` | MCP קנוני: `adelaidasofia/instagram-mcp` |
| פרופיל רצוי | `packages/vfigos/PROFILE-DESIRED.json` | | |
| ביקורת פיד | `packages/vfgrowth/data/feed-audit.json` | | |
| Insights | `packages/vfinsights/data/` | `vf_insights_ingest.py` | חסר = «אין ספירה». לא ממציאים |
| OpenPost | `packages/vfigos/OPENPOST.json` | `OPENPOST.md` | `integrationMode: shadow` — לא עוקף MCP/שערים |
| Publish Bridge | `packages/vfigos/PUBLISH-BRIDGE.md` + `PUBLISH-BRIDGE.json` | `vf_publish_bridge.py` | transport בלבד, לא קטלוג שני |

## ייצור / עלות / מק״ט

| דומיין | סמכות קנונית | CLI / sensor | הערה |
|---|---|---|---|
| צי רצפה | `packages/vfprod/FLEET.json` | `vfprod.py route` · `ROUTING.md` | HQ לא מדפיס |
| print.done | `packages/vfprod/PRINT-DONE.md` | `vfprod/hq/cards/` · אירוע `print.done` | חסר גלם = חסר, לא סצנה מומצאת |
| Watchtower | `packages/vfprod/WATCHTOWER.md` | | Edge/LAN שדרות — לא דמון בליבה |
| מדף מק״ט | `packages/vfsku/SHELF.json` | `vfsku.py scan` · `FIRST-PRINT.md` | לא ממציאים שמות/₪ |
| עלות חומר | `packages/vfcost/FILAMENTS.json` + `CARDS.json` | `scripts/vfcost.py` | גרמים חסרים = סירוב; לא מחיר מכירה |
| רישיון קובץ | `packages/vlicense/GATE.md` | | Meshy/Tripo/3DAI צריכים אישור ראש צוות |
| הזמנות (מכירה) | `packages/vfsales/data/orders.json` | `ORDERS.md` · `QUOTE.md` | `orders.json` ריק ≠ הוכחה שאין הזמנות |

## Living Studio / אוטונומיה / רתמה

| דומיין | סמכות קנונית | CLI / sensor | הערה |
|---|---|---|---|
| Living Studio | `packages/velvetos/living-studio/` | `vf_living_studio.py` · `check-living-studio.py` | projection/router בלבד |
| Skills registry | `packages/velvetos/living-studio/REGISTRY.json` | | 22 operational skills ב־README pulse |
| Autonomy composition | `packages/velvetos/living-studio/AUTONOMY.json` | `vf_autonomy.py` · `check-vf-autonomy.py` | לא runtime שני |
| רתמה | `AGENTS.md` + `packages/vfharness/` | `check-all.py` · `check-vfharness.py` | שש שכבות על פקים קיימים |
| Checkpoints | `packages/vfharness/state/` | `checkpoint.schema.json` · `skillstate.md` | `component_state`: Idle/Processing/Degraded/Syncing/Blocked |
| מסירת הנדסה | `packages/vfharness/playbooks/engineering-delivery-chain.md` | | decision→spec→tickets→proof→PR |
| QA להוראות סוכן | `packages/vfharness/playbooks/agent-instruction-qa.md` | `check-skill-health.py` | סמכות אחת לכל כלל |

## כלים / failover / שיתוף עבודה

| דומיין | סמכות קנונית | הערה |
|---|---|---|
| Failover מנהל משרד | `docs/FAILOVER.md` | ChatGPT → Perplexity → Gemini → Grok → Cursor |
| Failover מכסת Grok | `docs/GROK-FAILOVER.md` + `vfharness/playbooks/grok-failover.md` | HQ ממשיך לשלוח דרך כלים |
| Degraded Mode | `vfharness/playbooks/degraded-mode.md` | שם רשמי ל־failover רכיב |
| MCP / מנויים | `packages/vfmcp/` · `docs/MCP-FIT.md` · `SUBSCRIPTIONS.md` · `HOST.md` | Cloud לא פותח `gemini.google.com` / `chatgpt.com` |
| שולחן כלי | `.cursor/vf-desk.json` | מצבי `ready` הם רשומת desk — לא smoke חי בסשן |
| Canva | `docs/CANVA.md` · `packages/vfcanva/` | `needsAuth` → `studio/render.py` |
| קונסולת משרד פנימית | `docs/OFFICE-OS-EMBED-he.md` · `vfops/hq/COMMAND-SURFACE.md` | אתר שיווקי ציבורי נעול |

## מה לעולם לא SoT

| פריט | למה |
|---|---|
| World Model / Studio Pulse JSON | projection (`living-studio/data/`) |
| `office/ledger/live/jobs.csv` | cache; Sheet הוא הקנוני |
| תיקיית Drive «מאושר לפרסום» לבד | חסר `versionApproval` בקטלוג |
| Calendar event | שיבוץ ≠ live |
| `publish_*` בלי `list_media` | `publishRequested` בלבד |
| שיחת צ'אט / זיכרון מודל | Project memory ≠ governance |
| מחסן `.cursor/rules/` (273) | desk overlay בלבד; לא להפעיל את כולם |
| `packages/vfbrand` כשורה ב־`manifest.json` packs | הקובץ קיים; המניפסט לא מציג אותו כפק |
