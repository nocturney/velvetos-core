# Instagram Graph token expiry watch

מושב: תפעול + צמיחה. **אין טוקן בקובץ זה / בגיט / בבריף.**

## מקור אמת

`packages/vfigos/data/token-watch.json`

### מצבי תוקף (`expiryMode`)

| מצב | משמעות | ראיה חובה |
|---|---|---|
| `unknown` | תוקף לא ידוע | — |
| `limited` | תוקף מוגבל עם timestamp + אזור זמן | `expiresAt` ISO + `expiryEvidence.source` (`debug_token` / `app_dashboard` / …) |
| `none` | ללא תפוגה לפי דיווח בעלים על Meta | `expiryEvidence.source=owner-reported-meta` + `reportedAt` |

**`expiresAt=null` לבדו אינו מספיק** להבחין בין unknown ל־none.

מקור הראיה נשמר בכנות: `owner-reported-meta` = דיווח בעלים מ־Meta UI/Debugger — **לא** אימות API שביצע הסוכן.

## התראות

| מצב | watchdog | בריף 01 |
|---|---|---|
| `unknown` + MCP `remote_access=ready` | `ig_token_expiry_unverified` | תוקף לא ידוע — לא ממציאים תאריך |
| `none` + `owner-reported-meta` | **אין** התראת «חסר מועד פקיעה» | שורת מצב: ללא תפוגה (דיווח בעלים) · healthcheck חי נמשך |
| `limited` עם תאריך בלבד (בלי שעה מאומתת) | `ig_token_expiry_partial` | תוקף חלקי — לא מציגים תוקף מדויק / לא קובעים תקינות ודאית |
| אזור זמן / `warnDaysBefore` / טיפוס פגום | `ig_token_expiry_unverified` או `ig_token_watch_invalid` | התראה מסוננת — לא מפילים watchdog |

השוואת תוקף מוגבל היא **datetime מול עכשיו** עם אזורי זמן — לא «יום אחרי».

ללא תפוגה **אינו** מבטיח שהטוקן לא יבוטל או שהרשאותיו לא ישתנו — ממשיכים `healthcheck` חי.

## איך מעדכנים (בעלים / מק)

1. במארח ה־MCP בלבד — Meta Access Token Debugger / App Dashboard.
2. אם יש תאריך פקיעה → `expiryMode=limited` + ISO datetime בלבד.
3. אם Meta מציג שאין תפוגה → `expiryMode=none` + `owner-reported-meta` (בלי להמציא תאריך).
4. לא מדביקים את הטוקן לשיחת Cursor / Drive ציבורי / git.

CLI: `python3 scripts/vf_control_plane.py watchdog` · בדיקות התנהגות: `simulate` · בריף: `python3 scripts/vfops_loop.py brief --write`.
