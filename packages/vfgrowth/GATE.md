# שער מצבי תוכן — Organic Growth

מושב: צמיחה. חוקה: `constitution/ORGANIC_GROWTH.md`.  
פריפלייט איכות נשאר `PREFLIGHT.md` (נכשל-סגור לפני שיבוץ).  
השער הזה מוסיף **מדיניות + הרשאת פרסום** לפני מסירה ל־`vfigos`.

## מצבים

| מצב | מי מעביר | הערה |
|---|---|---|
| `draft` | מפעל תוכן | טיוטה פנימית |
| `quality_checked` | משרד אחרי Rubric + מדיה | בלי גלם = `blocked_no_media` |
| `policy_checked` | `vf_organic_growth.py policy` | אסור/מותר מ־ORGANIC_GROWTH |
| `pending_publish_authorization` | אחרי policy | דורש human approval נקודתי או standing authorization תקף |
| `pending_human_approval` | legacy alias | תאימות ל־queue/CLI הישן; מפורש כ־`pending_publish_authorization` |
| `approved_for_manual_posting` | אדם: אישור נקודתי | תאימות legacy; לא טענת פרסום |
| `authorized_for_tool_publish` | instance standing authorization | רק תוכן שגרתי שעבר PREFLIGHT + rights + Visual OS QA |
| `rejected` | אדם: דחייה | נשאר במשרד |
| `edit` | אדם או QA | חוזר ל־draft |
| `published_verified` | `vfigos` אחרי tool receipt + verification evidence | לא מסמנים בלי ראיה |
| `posted_manually` | אדם במסלול legacy | רק אחרי העלאה ידנית אמיתית עם `human_marked=true` + `marked_by` |
| `performance_imported` | סנאפשוט / CSV | חסר = אין ספירה |
| `attributed` | ייחוס הסתברותי | לא «וודאי» |
| `learned` | רטרו / brief מחר | בלי בושה לבעלים |
| `blocked_no_media` | מפעל | אין Reel מומצא; צור shotRequest מדויק |
| `blocked_policy` | policy | נכשל-סגור |
| `human_required` | משרד | רק חסר פיזי/זכויות/כסף/WhatsApp/Print/חסם קשיח |

## הרשאה

ברירת המחדל הכללית נשארת human approval. Instance יכול להפעיל:

`creativeAutonomy.publish.standingAuthorization=true`

במצב זה, `pending_publish_authorization` יכול לעבור ל־`authorized_for_tool_publish` ללא אישור לכל נכס, **רק** אם:

1. `VISUAL-OS.md` brandScore >=80.
2. `CONTENT-RUBRIC >=20/25`.
3. policy pass + written PREFLIGHT.
4. rights/privacy ברורים.
5. אין ₪/Boost/Ads/customer WhatsApp/Print.
6. קיים publish tool אמיתי.

## מעברים אסורים

- `draft` ישירות ל־publish.
- publish claim בלי tool receipt + verification evidence.
- standing authorization על כסף, Boost/Ads, customer WhatsApp, Print from HQ, auto-DM, user tag בלי opt-in או זכויות לא ברורות.

## פעולות בעלים

כאשר אין standing authorization או שיש `human_required`: **אישור** · **עריכה** · **דחייה**.  
כשלי Hook/cover/crop/caption/QA רגילים אינם פעולת בעלים — מתקנים אוטונומית.
