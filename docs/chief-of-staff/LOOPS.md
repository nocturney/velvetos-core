# לולאות תפעול · LOOPS

שעון קנוני לאוטומציות בעלים: **`packages/vfops/ROUTINE.md`**.  
`packages/vfops/LOOP.json` הוא מפת **צריכה** של פקים, לא שעון. תוויות היסטוריות `daily-07:00` / `daily-06:15` **אינן** דוחפות את ה־cron החי.

אזור זמן: `Asia/Jerusalem`.

## קדנס קנוני: 07:00 cutoff, 09:00 Morning Brief

- `packages/vfops/ROUTINE.md` הוא שעון האוטומציות לבעלים.
- **07:00** הוא cutoff/readiness פנימי למחקר ול-Decision Pack; הוא אינו Morning Brief נוסף.
- **09:00** הוא Morning Brief היחיד לבעלים, במסלול Morning Green v3.1.
- סטטוס delivery נשאר `UNPROVEN` בלי Gmail/provider evidence.

## יום — אוטומציות מוגנות (ROUTINE.md)

| שעה | משטח | מה | מה לא |
|---|---|---|---|
| 01:45 | Automation Integrity Guard | תיקון סט האוטומציות המוגן | לא בונה מערכת שנייה |
| 02:00 | Velvet Research Seat | מחקר חי עד cutoff 07:00 → `vfops/data/research.md` | GHA לא מחליף את גוף המחקר |
| 07:15 | Runtime Receipts Refresh | רענון קבלות runtime מתצפיות חיות כדי להכין dependency-scoped live proofs; PR אחד, מיזוג רק על ירוק | freshness אינו gate אוניברסלי לקוד; לא ממציא תצפית |
| **09:00** | Velvet Morning Brief | Morning Green v3.1 לבעלים | קובץ שנוצר ≠ נשלח; דרוש Gmail evidence |
| 10:00 | Morning Delivery Guard | וידוא שנשלח הבריף של היום | |
| 10:30 | VelvetOS Office Loop | blockers, production→content, drift | לא scheduler לכל היכולות |
| 18:30 | VelvetOS Office Loop | סגירת יום, למידה, HANDOFF | |
| 19:15 | Runtime Receipts Refresh | רענון שני של ראיות runtime כדי ש־deployment/runtime claims יוכלו להוכיח dependencies בשם | stale receipt לא קשור אינו חוסם `CODE_VALID` |

שבועי: Weekly Research Accountability שישי 12:00 (ROUTINE).  
Deck: `.github/workflows/velvetos-weekly-deck.yml` שישי 06:00 UTC.

## GitHub Actions (קיום workflow ≠ LIVE ספק)

| Workflow | תפקיד | קצב מתועד |
|---|---|---|
| `check-all.yml` | סנסורי `check-*.py` על push/PR ל־`main` | כל PR/push |
| `vfmedia-intake.yml` | קליטת Drive נכנס→קטלוג | `23 */3 * * *` — 8 ריצות ביום (#357, מיושר לקצב ש־GitHub באמת מריץ) |
| `jobs-write-through.yml` | write-through לגיליון העבודות | `53 1-23/3 * * *` — 8 ביום + push ל־sync-receipt |
| `instagram-read-smoke.yml` | smoke קריאה-בלבד ל־Instagram MCP (401 בלי טוקן, profile, media, insights, בלי כלי כתיבה) | 04:41 UTC יומי; secret `VELVET_INSTAGRAM_MCP_BEARER_TOKEN` |
| `office-control-plane.yml` | activation sweep + watchdog + hygiene + gaps + handoff | `0 2,8,14,20 * * *` UTC = 05:00/11:00/17:00/23:00 IDT (לא מתנגש ב־Office Loop 10:30/18:30 גם עם עיכוב GitHub של ~40 דק׳) |
| `jobs-write-through.yml` | Sheet jobs WIF pull/push/read-back | `:07,:22,:37,:52` כל שעה |
| `velvetos-research.yml` | freshness/index/sensors אחרי Research Seat | 04:30 UTC |
| `readme-system-pulse.yml` | רענון README pulse | שעתי + שינוי קבצי ראיה |
| `gmail-brief-send.yml` | שליחת בריף כש־`gmail-send-request.json` enabled | workflow_dispatch / push לקובץ |
| `velvetos-weekly-deck.yml` | דק שבועי מנתוני ריפו | שישי |
| `publish-bridge-cleanup.yml` | ארכיון transport | יומי |

## צינור עסקי: פנייה → איסוף

קנוני: `פנייה → שיחה → הצעה → הדפסה → איסוף`  
(`constitution/STUDIO.md` · desk `pipeline` · module `pipeline-canonical`).

```
פנייה (Gmail/IG/הודעה)
  → vfconvert grill/card + office/clients
  → vfmem לפני note/meeting/document
  → Universal Intake (`vf_living_studio.py intake`) → inbox.json / job
  → שיחה אנושית (WhatsApp אדם; HQ לא שולח)
  → vfcost material (או סירוב) + vfsales quote עם X ₪ עד אישור
  → שער GATES quote = yes רק עם סכום ראש צוות
  → vfprod route (המלצת מיטה) — Print ברצפה
  → print.done card + מדיה לכספת
  → vfbooks pickup מול תשלום מאומת
  → איסוף שדרות בלבד
```

Jobs SoT: Google Sheet `VF HQ · jobs`.  
`python3 scripts/vf_office.py jobs pull|push|reconcile|status`  
כתיבה חיה מתועדת ב־`office/ledger/live/sync-receipt.json`. Dirty local + Sheet שונה בלי `--force` = conflict.

## כספת מדיה

סמכות: `docs/MEDIA-VAULT.md`.

```
העלאה → 01 נכנס
  → vfmedia.py intake run (תפעול) → catalog registered → 02 מקור verified
  → נגזרת 03 בעבודה (vfom / כלי עריכה מאושר)
  → versionApproval בקטלוג → 04 מאושר לפרסום
  → PREFLIGHT + SEND (פרסום צעד נפרד)
```

- Upload ≠ approval. Folder 04 ≠ proof.
- אין מחיקה. אין שינוי share על מקור/נכנס/עבודה.
- HTTPS ציבורי זמני רק לנגזרת מאושרת דרך Publish Bridge.

## מפעל תוכן / Organic Growth

סמכות: `constitution/ORGANIC_GROWTH.md`.

```
print.done + מדיה אמיתית
  → vfom concept/hook/EDL + vfcopy
  → quality_checked → policy_checked
  → pending_publish_authorization
      → authorized_for_tool_publish (אם standing auth ב־instance)
      → approved_for_manual_posting (legacy)
  → vfigos SEND (tool או failover)
  → published_verified + insights import
  → attributed (הסתברותי) → learned
```

CLI: `python3 scripts/vf_organic_growth.py brief|policy|queue|score`  
חסר צילום = `waiting_for_media` + `shotRequest`. לא ממציאים רצפה.  
קהילה: Work Order `pending_ops` — לא poll→Print.

## Control Plane יומיומי

```
vf_control_plane.py watchdog
vf_control_plane.py followups
vf_control_plane.py gaps
vf_control_plane.py memory-hygiene
vf_control_plane.py handoff
vf_control_plane.py brief-summary
```

עדיפות ספרינט תוכן (`contentSprintPriority`):  
`ready_for_finished_content` → `print.done_with_usable_media` → `approved_waiting_for_slot` → `new_media_from_intake` → `general_new_content_ideas`.

WIP→finished: `office/control/followups.json`.  
בקריאה לתיעוד: פריט אחד `fu-G003-soccerball` ב־`waiting_for_print_done` (תהליך G003 חי; finished thread ממתין ל־print.done אמיתי). `orders.json` ריק ≠ אפס הזמנות.

Dead-letter: `office/control/dead-letter.json` (ריק בקריאה). לא לאבד כשל אחרי failover.

## אוטונומיה + סיכון

```
vf_autonomy.py status|next-action|blockers|approvals|context|quiet-plan|snapshot|execute|selftest
```

הרצה ירוקה/צהובה בלבד. לפני retry: reconcile מצב אמיתי.  
Idempotency: `run_id` / `idempotency_key` / `correlation_id`. לא ממציאים `correlation_id`.

## לולאת למידה

ערב: `packages/vfops/hq/DAILY-RETRO.md` + skill `vf-daily-learning`.  
ראש צוות מבקש מכל מושב שורה ל־`vfops/data/owner-memory.md`.  
בוקר: בריף קורא את הבלוק — לא את תיבת הדואר (`briefSources.inboxRead=false`).

Signals: `scripts/vf_retro_signals.py` → בריף. לא בושת בעלים.

## מחקר

| קצב | מקור | הערה |
|---|---|---|
| יומי (02:00 Research Seat; 07:00 readiness cutoff) | `vfresearch/DAILY.md` | failover ל־WebSearch; אין גוף מומצא |
| Research Seat הוא סמכות התזמון (`packages/vfresearch/BEST-SKILLS.json`) | due ב־44h, stale מעל 52h | **אין טיימר חיצוני** — `TIMER.md` היסטורי בלבד |
| שבועי | `WEEKLY.md` + `LINKS.json` + `PRINT-DEMAND.md` | |
| MakerWorld א׳+ד׳ | `vfresearch/hq/MAKERWORLD-SCAN.md` + `vfsku.py scan` | |
| Last-30 | `hq/LAST30.md` · skill `vf-last30` | |
| דופק פרנסה שבועי | `vfops/playbooks/WEEKLY-REVENUE-PULSE.md` | Insights רק מסנאפשוט מאומת |

## הנדסה / הוראות סוכן

שינוי מהותי בקוד/מדיניות/אינטגרציה:

`engineering-delivery-chain.md`: decision → spec → vertical tickets → branch → proof → review → PR/CI.

הוראות סוכן חדשות: `agent-instruction-qa.md` + `check-skill-health.py`.  
DoD ריפו (README): implementation + evidence/sensor + CHANGELOG + README אם נגע ב־packages/office/scripts/workflows/constitution.

## משמרת (`@vf-run` / vfe2b)

תיקיית עבודה אחת. סיום: `worker_done` / `escalation` / `decision_gate`.  
לא מתקינים Orca. כרטיס: דופק / אימות / ארטיפקט.

## Failover בתוך לולאה

כלי נפל → גיבוי **באותו תור** (`ORCHESTRA.md`).  
מנהל משרד נפל → `docs/FAILOVER.md` (דוח השתלטות, לא בנייה מחדש).  
Grok quota → ממשיכים לייצר ולשלוח; תגיות `#נשלח-מ-HQ` / `#ממתין-ל-כלי-IG`.  
`component_state: Degraded` ב־checkpoint אם יש משימה פתוחה.
