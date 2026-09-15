# לולאות תפעול · LOOPS

שעון קנוני לאוטומציות בעלים: **`packages/vfops/ROUTINE.md`**.  
`packages/vfops/LOOP.json` הוא מפת **צריכה** של פקים, לא שעון. תוויות היסטוריות `daily-07:00` / `daily-06:15` **אינן** דוחפות את ה־cron החי.

אזור זמן: `Asia/Jerusalem`.

## מתח מתועד: 07:00 מול 09:00

| מקור | מה הוא אומר |
|---|---|
| `ROUTINE.md` | Velvet Morning Brief ב־**09:00**; Research Seat 02:00 עם cutoff 07:00 למוכנות |
| `AGENTS.md` / `CONSTITUTION.md` / `GATES.md` | בריף **07:00**, תצוגה 3 `htmlBody` |
| `ORCHESTRA.md` | תזמורת מחקר **06:15** (Cursor) |

ראש צוות: לא להמציא איחוד. בריף לבעלים רץ לפי **ROUTINE.md** (09:00) אלא אם HANDOFF חי או הבעלים שינה במפורש. חוקת 07:00 נשארת כחוזה תוכן/HTML (`vfbriefux/MAIL.html`) וצריכת פקים. סטטוס ההרצה בפועל בסשן = `UNPROVEN` בלי `gmail-send-request` receipt.

## יום — אוטומציות מוגנות (ROUTINE.md)

| שעה | משטח | מה | מה לא |
|---|---|---|---|
| 01:45 | Automation Integrity Guard | תיקון סט האוטומציות המוגן | לא בונה מערכת שנייה |
| 02:00 | Velvet Research Seat | מחקר חי עד cutoff 07:00 → `vfops/data/research.md` | GHA לא מחליף את גוף המחקר |
| 07:15 | OpenPost Release Watch | מעקב שינוי upstream; שקט אם אין שינוי | OpenPost עדיין `shadow` |
| **09:00** | Velvet Morning Brief | בריף V10.3 לבעלים | קובץ שנוצר ≠ נשלח; דרוש Gmail evidence |
| 10:00 | Morning Delivery Guard | וידוא שנשלח הבריף של היום | |
| 10:30 | VelvetOS Office Loop | blockers, production→content, drift | לא scheduler לכל היכולות |
| 18:30 | VelvetOS Office Loop | סגירת יום, למידה, HANDOFF | |

שבועי: Weekly Research Accountability שישי 12:00 (ROUTINE).  
Deck: `.github/workflows/velvetos-weekly-deck.yml` שישי 06:00 UTC.

## GitHub Actions (קיום workflow ≠ LIVE ספק)

| Workflow | תפקיד | קצב מתועד |
|---|---|---|
| `check-all.yml` | סנסורי `check-*.py` על push/PR ל־`main` | כל PR/push |
| `vfmedia-intake.yml` | קליטת Drive נכנס→קטלוג | `*/5` (best-effort) |
| `office-control-plane.yml` | activation sweep + watchdog + hygiene + gaps + handoff | כל 6 שעות |
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
  → נגזרת 03 בעבודה (Canva / vfom)
  → versionApproval בקטלוג → 04 מאושר לפרסום
  → PREFLIGHT + SEND (פרסום צעד נפרד)
```

- Upload ≠ approval. Folder 04 ≠ proof.
- אין מחיקה. אין שינוי share על מקור/נכנס/עבודה.
- HTTPS ציבורי זמני רק לנגזרת מאושרת (Publish Bridge / Canva CDN).

## מפעל תוכן / Organic Growth

סמכות: `constitution/ORGANIC_GROWTH.md`.

```
print.done + מדיה אמיתית
  → vfom concept/hook/EDL + vfcopy + vfcanva
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
| יומי (02:00 seat / 06:15 ORCHESTRA) | `vfresearch/DAILY.md` | failover ל־WebSearch; אין גוף מומצא |
| כל ~יומיים לעד | `BEST-SKILLS.md` + `TIMER.md` | `standingForever` עד שהבעלים עוצר |
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
