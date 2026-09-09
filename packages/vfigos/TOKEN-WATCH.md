# Instagram Graph token expiry watch

מושב: תפעול + צמיחה. **אין טוקן בקובץ זה / בגיט / בבריף.**

## מקור אמת

`packages/vfigos/data/token-watch.json`

| שדה | חוק |
|---|---|
| `expiresAt` | ISO `YYYY-MM-DD` **רק** מ־Meta debug_token / App Dashboard — אחרת `null` |
| `expiresAtSource` | `debug_token` / `app_dashboard` / `null` |
| `lastLiveOkAt` | מתעדכן אחרי `healthcheck` עם `live_check.ok=true` (בלי סוד) |
| `warnDaysBefore` | ברירת מחדל 14 |

## התראות

| מצב | watchdog | בריף 01 |
|---|---|---|
| `expiresAt` חסר + MCP `remote_access=ready` | `ig_token_expiry_unverified` (yellow / PREPARED) | «חסר תוקף מאומת לטוקן IG» |
| נשארו ≤ `warnDaysBefore` ימים | `ig_token_expiry_soon` (orange) | «לרענן טוקן IG עד תאריך» |
| `expiresAt` עבר | `ig_token_expired` (red) | חסם — failover `SEND.md` |

## איך מאמתים תוקף (בעלים / מק)

1. במארח ה־MCP בלבד — Meta Access Token Debugger / `debug_token`.
2. מעתיקים **רק** את תאריך הפקיעה ל־`expiresAt`.
3. לא מדביקים את הטוקן לשיחת Cursor / Drive ציבורי / git.

CLI: `python3 scripts/vf_control_plane.py watchdog` · בריף: `python3 scripts/vfops_loop.py brief --write`.
