# פעולות בעלים — מה Cloud Agent לא יכול לסגור לבד

עודכן 2026-09-10 אחרי תיקון חוסמי מיזוג ב־PR #160 (בידוד commission, Sheet write-through honesty, intake idempotency).

## מצב נוכחי — אין פעולת בעלים (Christian) נדרשת

| נושא | סטטוס נוכחי |
|------|-------------|
| Instagram MCP (`instagram`) | **ready** — Insights verified; אין צורך ב־Professional Dashboard ידני כש־MCP חי |
| Media Auto Intake (GHA OIDC/WIF) | **commissioned** — `intake-runner.json` · `auth.ready=true` · `activation.proven=true` · **לא** דורש `VFMEDIA_DRIVE_CREDENTIALS_JSON` |
| Jobs **read** | Google Sheet קנוני + `jobs pull` (Drive MCP CSV או API) — cache לא = אפס הזמנות |
| Jobs **write-through** | **PARTIAL** על Cloud: `push_write_through` → `write_pending_provider` בלי Sheets API auth/libs. Cache נשאר dirty עד כתיבה אמיתית לגיליון (Desktop `mcp-gsheets` / GOOGLE_TOKEN+spreadsheets). לא ממציאים COMPLETE |
| Approval queue | `pending_human_approval` ישן **לא** הופך אוטומטית לכתום אצל כריסטיאן תחת standing authorization; פריט 2026-09-07 → `stale_orphan` |
| Insights learning | MCP ingest חי; מדגם קטן → «insufficient evidence» — בלי המלצת סגנון כוזבת |

**No owner action required.**

(אופציונלי לולאת כתיבה מלאה לגיליון: חיבור Sheets write על Desktop או מפתח Cloud — לא חוסם קריאה/תפעול יומי ולא משטח כריסטיאן.)

---

## היסטורי / לא חוסם (superseded)

### ~~VFMEDIA_DRIVE_CREDENTIALS_JSON~~ — SUPERSEDED 2026-09-10

~~בעלים חייב להוסיף JSON credentials~~ → **שגוי.** OIDC/WIF על GHA.

### ~~Instagram Publish MCP חסר~~ — SUPERSEDED 2026-09-09/10

Namespace `instagram` מחובר. ראו `packages/vfigos/CAPABILITIES.json`.

### Origin vendor / Push instance / Mobbin — אופציונלי

לא חוסמים תפעול יומי של Core HQ.
