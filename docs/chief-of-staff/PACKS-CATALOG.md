# קטלוג פקים · PACKS-CATALOG

מקור מכונה: `packages/manifest.json` (`catalogRefreshedAt`: 2026-09-09, 31 פקים).  
תיקיות תחת `packages/`: **32** (כולל `vfbrand`, שאינו ברשימת `packs` של המניפסט).

כל פק: תפקיד בשורה + מצביעי סמכות שקיימים בריפו.  
`vendorStatus` מ־מניפסט. Origin trees ל־tmp-*: `origin-unreachable` — לא ממציאים slug חדש.

מושבים: `constitution/TEAM.md` + `.cursor/vf-desk.json` → `seats` (אריזת פקים בין שני הקבצים **לא זהה** — ראה SYSTEM-MAP).

## פקי ליבה / משרד

| פק | תפקיד | סמכות / כניסה | CLI / sensor |
|---|---|---|---|
| `velvetos` | Kernel: שכבות, מודולים, מופעים, Living Studio, שער בקשה | `CORE.json` · `LAYERS.md` · `REPOS.md` · `PROJECT-REQUEST-GATE.md` · `living-studio/` | `velvetos.py` · `vf_living_studio.py` · `vf_autonomy.py` · `check-velvetos.py` · `check-living-studio.py` |
| `vfops` | מנהל הסטודיו: בריף, לולאה, שערי 01, רטרו | `LOOP.json` · `ROUTINE.md` · `hq/GATES.md` · `hq/DAILY-RETRO.md` · `BRIEF.md` | `vfops_loop.py` · `gmail_brief_send.py` · `check-vfops-loop.py` |
| `vfharness` | רתמה חיצונית (6 שכבות) על פקים קיימים | `EMBED.md` · `playbooks/` · `AGENTS.md` | `check-all.py` · `check-vfharness.py` · `packages/vfharness/scripts/vf_graceful_escalation.py` |
| `vfmem` | שאילתות גרף משרד + זיכרון בעלים | `MEMORY-UPDATE.md` · `docs/VFMEM.md` | `vfmem.py` · `vf_semantic_search.py` · `check-vfmem.py` |
| `vfgraft` | מפת משרד (Graft markdown) | `MAP.md` · `graph/` | `check-vfgraft.py` |
| `vfbiz` | החלטות מסחריות + מבנה הצעה | `OFFERING.md` · `LOCK.md` · `CHAIN.md` | `check-vf-offering.py` |
| `vfbriefux` | פורמט בריף 07:00/09:00 HTML | `MAIL.html` · `hq/PACKET.md` | `render_mail.py` |
| `vfbrand` | SoT ויזואלי למותג (נעול 2026-09-13) | `BRAND-SOURCE-OF-TRUTH.md` בלבד | נצרך ב־`LOOP.json`; **חסר** מ־`manifest.json` packs |

## צינור לקוח → כסף

| פק | תפקיד | סמכות / כניסה | CLI / sensor |
|---|---|---|---|
| `vfconvert` | פנייה → בריף הזמנה | `PATH.md` · `CARD.md` · `WHATSAPP.md` · `hq/GRILL.md` | `vf_office.py convert draft` |
| `vfsales` | הצעות, מעקב, הזמנות | `QUOTE.md` · `ORDERS.md` · `SLA.md` | `vf_quote_ladder.py` (תחת vfsales/scripts) |
| `vfcost` | עלות חומר בלבד (גרמים × ₪/ק״ג) | `CLI.md` · `FILAMENTS.json` · `CARDS.json` | `vfcost.py` · `check-vfcost.py` |
| `vfbooks` | ספר / חוב / איסוף מול תשלום | `INTEGRITY.md` · `LEDGER.md` · `PICKUP.md` · `SHEETS.md` | `vfbooks.py brief` |
| `vfsku` | מדף מק״ט + הדפסה ראשונה | `SHELF.json` · `FIRST-PRINT.md` · `GATE.md` · `TAG.md` | `vfsku.py scan` · `check-vfsku.py` |
| `vlicense` | שער רישיון קובץ/מודל | `GATE.md` | לפני 3DAI/Meshy/Tripo |

## ייצור

| פק | תפקיד | סמכות / כניסה | CLI / sensor |
|---|---|---|---|
| `vfprod` | רצפה: ניתוב מיטות, print.done, תחזוקה | `FLEET.json` · `ROUTING.md` · `PRINT-DONE.md` · `WATCHTOWER.md` · `3DAISTUDIO.md` | `vfprod.py` · `check-vfprod.py` |

HQ **ממליץ** מיטה; לא מדפיס. Watchtower = Edge.

## תוכן / יצירה / פרסום

| פק | תפקיד | סמכות / כניסה | CLI / sensor |
|---|---|---|---|
| `vfgrowth` | לוח, PREFLIGHT, מפעל תוכן אורגני | `CALENDAR.md` · `PREFLIGHT.md` · `EDIT-GATE.md` · `ORGANIC-GROWTH.md` · `HANDOFF-he.md` | `vf_organic_growth.py` · `check-vfgrowth.py` · `check-organic-growth.py` |
| `vfcopy` | כיתוב + Visible Text + עברית טבעית | `VOICE.md` · `skills/velvet-hebrew-copy/` | `check-vfcopy.py` · `vf_visible_text.py` |
| `vfcovers` | כריכות בריף/פיד | `DRAFT.md` · `g005/` | |
| `vfcanva` | ויזואל Instagram ב־Canva | `WORKFLOW.md` · `FORMATS.json` · `CONNECT.md` · `docs/CANVA.md` | `studio/render.py` · `check-vf-canva.py` |
| `vfigos` | סקירה / שיבוץ / שליחה דרך כלים | `SEND.md` · `CAPABILITIES.json` · `PUBLICATION-STATES.json` · `CONNECT-IG.md` | `vf_send_preflight.py` · `vf_publish_bridge.py` |
| `vfom` | Visual Foundry / ריל / toolchain וידאו | `VISUAL-OS.md` · `CREATIVE-AUTOPILOT.md` · `VIDEO-TOOLCHAIN.md` · `HYPERFRAMES-BACKEND.json` | `vf_hyperframes.py` · `vf_video_edit.py` · `vf_speech.py` |
| `vfinsights` | מדידה אחרי פרסום — בלי המצאה | `data/` · loop scripts | `vf_insights_ingest.py` · `vf_insights_loop.py` |
| `vfmedia` | קטלוג כספת מדיה יחיד | `CATALOG.md` · `INTAKE.md` · `FOLDERS.json` · `docs/MEDIA-VAULT.md` | `vfmedia.py` · `check-vfmedia.py` |
| `vfseason` | סימוני עונה ללוח | `SKILL.md` | |
| `vfmskill` | כישורי שיווק (Haines) על פקים קיימים | `docs/MARKETING-SKILLS.md` · `.agents/product-marketing.md` | `check-vfmskill.py` |

## מחקר / הטמעות דפוס (לא runtime שני)

| פק | תפקיד | סמכות / כניסה | CLI / sensor |
|---|---|---|---|
| `vfresearch` | תזמורת 06:15, קישורים, best-skills, last30, print-demand, מוזיקה | `DAILY.md` · `WEEKLY.md` · `LINKS.json` · `BEST-SKILLS.md` · `MUSIC.md` · `hq/LAST30.md` · `hq/PRINT-DEMAND.md` | `vfresearch_cadence.py` · `check-vfresearch.py` |
| `vfe2b` | דפוסי awesome-ai-agents + orchestrators overlay | `ORCHESTRATORS.md` · `LOCK.md` · `crews/run.md` | `check-vfe2b.py` |
| `vfdsh` | דפוסי awesome-dsh-plugin | `docs/DSH-FIT.md` · `LOCK.md` | `check-vfdsh.py` |
| `vfagents` | התאמת 500-AI-Agents לפקי VF | `docs/500-AGENTS.md` · `playbooks/` | `check-vfagents.py` |
| `vfmakers` | decide / unstuck / cash pulse / IG rotation | `docs/MAKERSKILLS-EMBED-he.md` | `check-vfmakers.py` |
| `vfmcp` | מפת MCP + Gemini/ChatGPT API desks | `CORE-MCP.md` · `SUBSCRIPTIONS.md` · `HOST.md` · `docs/MCP-FIT.md` | `vf_gemini.py` · `vf_chatgpt.py` · `check-vfmcp.py` |
| `vffcc` | Free Claude Code — מפה בלבד, לא proxy על Cloud | `docs/FCC-FIT.md` · `LOCK.md` | `check-vffcc.py` |

## Skills ב־`.cursor/skills/` (נתבים דקים, לא פקים)

ראו גם `packages/vfops/LOOP.json` (skill-* consume steps) ו־`.cursor/skills/*/SKILL.md`.

| Skill | מתי |
|---|---|
| `vf-morning-brief` | בריף בוקר |
| `vf-inquiry-chain` | פנייה → convert/prod/cost/sales |
| `vf-canva-instagram` | ויזואל IG ב־Canva |
| `vf-hebrew-copy` | כיתוב עברי |
| `vf-organic-growth` | Decision Pack / מפעל תוכן |
| `vf-content-sprint` | ספרינט תוכן מוצדק |
| `vf-daily-learning` | רטרו סוף יום |
| `vf-hq-memory` / `vf-graft-map` | מי מטפל / מפת משרד |
| `vf-harness` | רתמה, הסלמה, failover Grok |
| `vf-velvetos` | Core מול instance |
| `vf-living-studio` | World Model / Pulse / Intake |
| `vf-revenue-loop` | IG→פרנסה |
| `vf-best-skills` / `vf-weekly-links` / `vf-last30` / `vf-ig-music` | מחקר |
| `vf-openmontage` / `velvet-creative-director` / `velvet-brand-guardian` / `velvet-media-librarian` | יצירה/QA/מדיה |
| `vf-run` / `vf-makers` / `vf-marketing-skills` / `vf-fcc-offload` | משמרת / makers / שיווק / FCC |

Canva plugin skills (`canva-*`) הם כלי עריכה; מסלול VF נשאר `vf-canva-instagram`.

## מחסן Agency

273 כללים ב־`.cursor/rules/` עם `alwaysApply: false`.  
שולחן חי: `.cursor/vf-desk.json` + `docs/AGENCY-TOOLS.md`.  
**לא מפעילים את כל הרוסטר.** `@chief-of-staff` כבר על שולחן ראש צוות.

## הערות קטלוג (fail-closed)

- README System Pulse סופר **31 packs** — תואם `manifest.json`, לא את תיקיית `vfbrand`.
- כמה `ORIGIN.md` עדיין כותבים «Live send stays on Grok Bot» — **סופרסד** ב־`constitution/SEND.md` (HQ שולח דרך כלים). לא להעתיק את המשפט הישן כחוק.
- פקים `origin-unreachable` עדיין משרתים דרך HQ overlay (`SKILL.md` + `hq/`) שחי בליבה.
