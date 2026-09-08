# Office Control — מצב בקרת משרד

לא מערכת משרד שנייה. מאחד ומקשיח מקורות אמת קיימים.

מפת מקורות: [`../control-plane.json`](../control-plane.json)  
CLI: `python3 scripts/vf_control_plane.py`  
סנסור: `python3 scripts/check-office-control-plane.py`

## קבצים

| קובץ | תפקיד |
|---|---|
| `inbox.json` | תיבת משרד אחת (content / production / sales / admin / approvals / blocked / unknown) |
| `dead-letter.json` | כשלונות אחרי failover — לא נזרקים בשקט |
| `followups.json` | גשר WIP→finished, ממתין ל־print.done / מדיה / preflight / אימות פרסום |
| `HANDOFF.json` | מסירת מנהל חיה לכל AI |
| `HANDOFF-he.md` | אותה מסירה בעברית לקריאה |
| `decisions.jsonl` | יומן החלטות append-only (supersede, לא מחיקה) |
| `POLICY.md` | Don't Bother Christian — ירוק/צהוב/כתום/אדום (canonical; `constitution/RISK.md` + `vfops/risk-policy.json` are mirrors) |

## מצביעי תאימות (לא SoT)

- `packages/vfharness/dead-letter/queue.json` → `dead-letter.json`
- `packages/vfgrowth/data/production-content-followups.json` → `followups.json`

## נעול

אין המצאת ₪ / Insights / סיפור לקוח. אין אוטו־DM. אין Meta Suite.  
שיבוץ ≠ פרסום חי. העלאה ≠ אישור. תיקיית מאושר ≠ הוכחת אישור.  
אין תור dead-letter / followups כפול. live דורש `verification_evidence`.
