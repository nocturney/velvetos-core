# לולאות תפעול · LOOPS

שעון קנוני לאוטומציות בעלים: **`automation/chatgpt/manifest.json` + `packages/vfops/ROUTINE.md`**.
`packages/vfops/LOOP.json` הוא מפת צריכה, לא שעון. Grokbot אינו scheduler.

אזור זמן: `Asia/Jerusalem`.

## קדנס נוכחי — מינימום הכרחי

| שעה | משטח | מה | מה לא |
|---|---|---|---|
| ~11:30 | Cognee Memory Sync | סנכרון derived-memory יומי גמיש | לא authority ולא cloud model |
| 18:30 | VelvetOS Office Loop | sweep תפעולי אחד, handoff ופעולות אמיתיות | לא research רחב ולא self-health bureaucracy |
| 19:15 | Runtime Receipts Refresh | ראיות runtime dependency-scoped מתצפיות אמיתיות | לא Grok receipt ולא refresh מלאכותי |

Morning Brief הוא manual/event-driven בלבד. Delivery Guard, Research Seat, Weekly Research Accountability, Cognee Stable Updates, Integrity Guard ו-PC Offline Retry אינם clocks פעילים.

Deck: `.github/workflows/velvetos-weekly-deck.yml` נשאר workflow מכונה נפרד ואינו authority לשעון הבעלים.

## GitHub Actions (קיום workflow ≠ LIVE ספק)

| Workflow | תפקיד | קצב מתועד |
|---|---|---|
| `check-all.yml` | סנסורי `check-*.py` על push/PR ל־`main` | כל PR/push |
| `vfmedia-intake.yml` | קליטת Drive נכנס→קטלוג | `23 */3 * * *` — 8 ריצות ביום (#357, מיושר לקצב ש־GitHub באמת מריץ) |
| `jobs-write-through.yml` | write-through לגיליון העבודות | `53 1-23/3 * * *` — 8 ביום + push ל־sync-receipt |
| `instagram-read-smoke.yml` | smoke קריאה-בלבד ל־Instagram MCP (401 בלי טוקן, profile, media, insights, בלי כלי כתיבה) | 04:41 UTC יומי; secret `VELVET_INSTAGRAM_MCP_BEARER_TOKEN` |
| `office-control-plane.yml` | activation sweep + watchdog + hygiene + gaps + handoff | `0 2,8,14,20 * * *` UTC = 05:00/11:00/17:00/23:00 IDT (לא מתנגש ב־Office Loop 10:30/18:30 גם עם עיכוב GitHub של ~40 דק׳) |
| `jobs-write-through.yml` | Sheet jobs WIF pull/push/read-back | `:07,:22,:37,:52` כל שעה |
| `velvetos-research.yml` | verifier/index/sensors למחקר שכבר הופק | workflow_dispatch בלבד; אין cron |
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

| טריגר | מקור | הערה |
|---|---|---|
| שאלה/החלטה/צורך תוכן/gate פתוח | `vfresearch/DAILY.md` | on-demand; אין Research Seat יומי ואין cutoff קבוע |
| החלטת skill/tool | `BEST-SKILLS.md` + `BEST-SKILLS.json` | on-demand; גיל `lastPass` הוא provenance בלבד |
| inspiration / print-demand | `WEEKLY.md` + `LINKS.json` + `PRINT-DEMAND.md` | playbook לפי צורך; “weekly” אינו clock |
| MakerWorld / Printables | `vfresearch/hq/MAKERWORLD-SCAN.md` + `vfsku.py scan` | לפי צורך מאומת; license/slice/test לפני promotion |
| Last-30 | `hq/LAST30.md` · skill `vf-last30` | לפי דרישה בלבד |
| Revenue pulse | `vfops/playbooks/WEEKLY-REVENUE-PULSE.md` | מופעל רק כשיש צורך עסקי/סקירה; Insights רק מסנאפשוט מאומת |

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
