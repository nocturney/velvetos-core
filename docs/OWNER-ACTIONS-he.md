# פעולות בעלים — מה Cloud Agent לא יכול לסגור לבד

עודכן 2026-09-10 אחרי סגירת פערים תפעוליים (Sheet jobs adapter, IG MCP Insights, Media Auto Intake OIDC).

## מצב נוכחי — אין פעולת בעלים נדרשת לסגירת הפערים התפעוליים האלה

| נושא | סטטוס נוכחי |
|------|-------------|
| Instagram MCP (`instagram`) | **ready** — profile / media / insights / publish tools חיים |
| Media Auto Intake (GHA OIDC/WIF) | **commissioned** — `packages/vfmedia/state/intake-runner.json` · `auth.ready=true` · `activation.proven=true` |
| Jobs ledger | **Google Sheet קנוני** (`VF HQ · jobs`) + cache מקומי דרך `vf_office.py jobs pull` |
| Insights | MCP מאומת → `vf_insights_ingest.py` → `posts.csv` / LEARNINGS |

אם אין חוסם חיצוני אמיתי:

**No owner action required.**

---

## היסטורי / לא חוסם את המשרד כרגע (superseded או אופציונלי)

### Origin vendor (6 פקים `tmp-*`) — היסטורי 2026-09-01

`origin auth login` נשאר אופציונלי לפקים `tmp-*`. העץ החי ב-Core הוא hq-native — לא חוסם תפעול יומי.

### Push ל-`velvetos-velvet-factory` — אופציונלי

נדרש רק כשמפרסמים instance frontend. לא חוסם Core HQ.

### Mobbin MCP על Cloud — אופציונלי

Failover: `vfbriefux` templates / Superdesign. לא חוסם בריף.

### ~~Instagram Publish MCP~~ — SUPERSEDED 2026-09-09/10

~~אין namespace~~ → **שגוי.** Namespace `instagram` מחובר ומוכן. ראו `packages/vfigos/CAPABILITIES.json`.

### ~~VFMEDIA_DRIVE_CREDENTIALS_JSON~~ — SUPERSEDED 2026-09-10

~~בעלים חייב להוסיף JSON credentials ל-runner~~ → **שגוי.** Media Auto Intake רץ עם GitHub OIDC/WIF (`GOOGLE_TOKEN`). ראיות: `intake-runner.json`.

---

## מה כבר תוקן בקוד

| נושא | סטטוס |
|------|--------|
| 3D AI Studio על Cloud | ready |
| פקים בלי Origin slug | hq-native |
| Instagram Insights live | verified via MCP |
| Creative Autopilot / autonomy composition | על main |
| Jobs Sheet adapter | `jobs pull` / `push` / `reconcile` |
