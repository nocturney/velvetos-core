# שער מצבי תוכן — Organic Growth

מושב: צמיחה. חוקה: `constitution/ORGANIC_GROWTH.md`.  
פריפלייט איכות נשאר `PREFLIGHT.md` (נכשל-סגור לפני שיבוץ).  
השער הזה מוסיף **מדיניות + אישור אדם** לפני «מוכן להעלאה ידנית».

## מצבים

| מצב | מי מעביר | הערה |
|---|---|---|
| `draft` | מפעל תוכן | טיוטה פנימית |
| `quality_checked` | משרד אחרי Rubric + מדיה | בלי גלם = `blocked_no_media` |
| `policy_checked` | `vf_organic_growth.py policy` | אסור/מותר מ־ORGANIC_GROWTH |
| `pending_human_approval` | אחרי policy | מופיע בבריף 07:00 |
| `approved_for_manual_posting` | אדם: אישור | **לא** פרסום |
| `rejected` | אדם: דחייה | נשאר במשרד |
| `edit` | אדם: עריכה | חוזר ל־draft |
| `posted_manually` | אדם אחרי העלאה ב־instagram.com | Core לא מעביר לכאן |
| `performance_imported` | סנאפשוט / CSV | חסר = אין ספירה |
| `attributed` | ייחוס הסתברותי | לא «וודאי» |
| `learned` | רטרו / brief מחר | בלי בושה לבעלים |
| `blocked_no_media` | מפעל | אין Reel מומצא |
| `blocked_policy` | policy | נכשל-סגור |

## מעברים אסורים ל־Core

- כל מעבר אל `posted_manually` בלי `"human_marked": true` **ו** `"marked_by"` אדם.
- קפיצה מ־`draft` ל־`approved_for_manual_posting`.
- `pending_human_approval` → Publish API.

שדה חובה בכל פריט תור: `content_id`, `gate`, `format` (`reel`|`story`|`card`|`poll`).

## פעולות בריף

לכל נכס רק: **אישור** · **עריכה** · **דחייה**.
