# CONNECT-IG · Instagram MCP קנוני (adelaidasofia)

סטטוס שולחן: **`ready-codespace`** — auth מאומת ב־GitHub Codespace (stdio).  
`auth: ready` · `transport: stdio` (+ Cloud Team MCP Streamable HTTP) · `remote_access: pending` עד `live_check.ok=true`.

**אימות Cloud 2026-09-09:** namespace `instagram` זמין בסוכן · שרת מרוחק `…a.run.app/mcp` עונה · `list_accounts` מחזיר IG user id `17841407772120429` · **`live_check.ok=false`** — טוקן Meta long-lived **פג** (oauth). עד רענון טוקן ב־host vault של השרת: אין Publish / אין claim ready מרוחק.

MCP קנוני: [`adelaidasofia/instagram-mcp`](https://github.com/adelaidasofia/instagram-mcp) · חבילה `adelaidasofia-instagram-mcp` · שם שרת `instagram`.  
**לגאסי:** [`jlbadano/ig-mcp`](https://github.com/jlbadano/ig-mcp) — לא ראשי יותר. ראו [`LEGACY-IG-MCP.md`](LEGACY-IG-MCP.md).

אין סודות בגיט. אין אוטו־DM. אין בוסט. אין Metricool כתלות תפעול.  
Capability contract: [`CAPABILITIES.json`](CAPABILITIES.json).  
מצבי פרסום: [`PUBLICATION-STATES.md`](PUBLICATION-STATES.md) — upload/schedule/publish tool ≠ `liveVerified`.  
פריסת Codespace / פער remote: [`DEPLOY-CODESPACE.md`](DEPLOY-CODESPACE.md).  
מדיה ציבורית לפרסום: [`docs/MEDIA-VAULT.md`](../../docs/MEDIA-VAULT.md) § «URL ציבורי לפרסום».

## מצב מאומת (לא לבקש שוב מכריסטיאן)

| עובדה | ערך |
|---|---|
| חשבון | `@velvets_cloud` |
| Instagram Business Account ID | `17841407772120429` |
| קישור לעמוד Facebook | מאומת |
| `add_account` | label `velvets_cloud` · default `true` |
| כלים שעבדו ב־Codespace | `healthcheck` · `get_profile` · `list_media` |
| סודות | Codespaces Secrets / runtime env בלבד — **לא בגיט** |

## מה סוגר עכשיו (כשה־MCP חי בסביבה)

| יכולת | כלי MCP |
|---|---|
| בריאות / חשבונות | `healthcheck` · `list_accounts` · `account_info` |
| פרופיל / מדיה | `get_profile` · `list_media` · `get_media` |
| Insights | `get_account_insights` · `get_media_insights` · `get_audience_insights` |
| פרסום פיד | `publish_image` · `publish_carousel` · `publish_video` |
| ריל | `publish_reel` |
| **סטורי** | `publish_story` (אותו MCP — לא מערכת נפרדת) |
| תגובות | `get_comments` · `reply_to_comment` · hide/delete לפי מדיניות מודרציה |
| מחקר | `get_mentions` · `publishing_limit` · `business_discovery` לפי צורך |
| Failover כש־MCP down / remote pending | Canva + Drive + Gmail — [`SEND.md`](SEND.md) |

## מדיניות הרשאות (VelvetOS)

### מותר — קריאה

`healthcheck` · `list_accounts` · `account_info` · `get_profile` · `list_media` · `get_media` · `get_account_insights` · `get_media_insights` · `get_audience_insights` · `get_comments` · `get_mentions` · `publishing_limit` · `business_discovery` (מחקר)

### מותר — כתיבה רק אחרי שערי אישור קיימים

`publish_image` · `publish_video` · `publish_reel` · `publish_carousel` · `publish_story` · `reply_to_comment` · `hide_comment` / `delete_comment` רק כשמדיניות מודרציה מחייבת

שערים לפני publish: מאגר מדיה + `versionApproval` · Canva/vfcovers · `vfgrowth/PREFLIGHT.md` · `vf_send_preflight.py --gate instagram` · אז כלי `publish_*`.

### אסור תמיד

`send_message` · `list_conversations` · `get_messages` · אוטו־DM · follow/unfollow · boost · Ads · API פרטי/scraping · username/password · עקיפת מגבלות Meta  
**`INSTAGRAM_MCP_DM_ENABLED` לא מופעל** במשרד.

Metricool / Publer / Postly / SimplePost / Meta Business Suite = **לא נדרשים** (אופציונלי/לגאסי בלבד).

## זרימת פרסום קנונית

```
Drive Media Vault (מקור פרטי)
  → נגזרת Canva / vfcovers (בעבודה)
  → שער אישור (versionApproval + PREFLIGHT)
  → URL HTTPS ציבורי לנגזרת המאושרת בלבד (לא כל הכספת)
  → Instagram MCP publish_image | publish_carousel | publish_reel | publish_story
  → אימות חי: list_media / get_media (media id / permalink)
  → רק אז liveVerified + ledger/catalog
  → Insights מאוחר יותר (get_*_insights)
```

| פורמט | כלי |
|---|---|
| תמונה / פוסט | `publish_image` |
| קרוסלה | `publish_carousel` |
| ריל / וידאו | `publish_reel` / `publish_video` |
| סטורי | `publish_story` |

**חוק אימות:** תשובת publish מוצלחת ≠ «פורסם». בלי `list_media`/`get_media` שמאשרים פריט חי → מסמנים `publish_pending_verification` — לא `liveVerified`.  
JPEG גולמי מהמיטה **אסור** לסטורי. מקסימום 5 האשטגים. CTA: `PUBLIC_CURRENT_CTA` (הודעת Instagram / «הזמנות») — לא «שלחו DM», לא טלפון וואטסאפ בכיתוב ציבורי.

## משתני ריצה (שמות בלבד — בלי ערכים בגיט)

חובה:

- `INSTAGRAM_MCP_ACCESS_TOKEN`
- `INSTAGRAM_MCP_IG_USER_ID` (= `17841407772120429` לסטודיו)

אופציונלי:

- `INSTAGRAM_MCP_APP_SECRET`

אסור להפעיל:

- `INSTAGRAM_MCP_DM_ENABLED`

## A) Desktop / Codespace — stdio

לא שמים טוקן ב־`.cursor/mcp.json` של הריפו. העתק מ־[`mcp.desktop.example.json`](../vfmcp/mcp.desktop.example.json) ל־`~/.cursor/mcp.json` או ל־Codespaces secrets:

```json
"instagram": {
  "command": "instagram-mcp",
  "env": {
    "INSTAGRAM_MCP_ACCESS_TOKEN": "${env:INSTAGRAM_MCP_ACCESS_TOKEN}",
    "INSTAGRAM_MCP_IG_USER_ID": "${env:INSTAGRAM_MCP_IG_USER_ID}"
  }
}
```

התקנה:

```bash
pip install adelaidasofia-instagram-mcp
# או מ־source:
# git clone https://github.com/adelaidasofia/instagram-mcp
# cd instagram-mcp && python3 -m venv .venv && .venv/bin/pip install -e .
```

## B) Cloud Agent / אוטונומיה מלאה

stdio בתוך Codespace ישן/כבוי **אינו** מספיק למשרד תמיד-דלוק.  
Endpoint מרוחק (Cloud Run / Team MCP, שם שרת `instagram`) **קיים** — ראו [`DEPLOY-CODESPACE.md`](DEPLOY-CODESPACE.md).  
`remote_access: pending` נשאר עד `healthcheck.live_check.ok=true` על `@velvets_cloud` (לא מספיק שה־MCP namespace ירוק אם Graph oauth נכשל).  
כש־oauth / remote לא מוכנים: failover [`SEND.md`](SEND.md).

## C) Insights (vfinsights)

מקור מועדף: `get_account_insights` / `get_media_insights` / `get_audience_insights`.  
מדד ש־Meta לא מחזירה → «אין ספירה» / unavailable. לא ממציאים.  
הדבקת בעלים נשארת גיבוי כשאין MCP. Metricool = אופציונלי לגאסי, לא קנוני.

## D) VF `mcpBind`

```
instagram.enabled = true
instagram.when = codespace-stdio-or-remote-when-ready
instagram.publish = true
instagram.dm = false
instagram.connect = packages/vfigos/CONNECT-IG.md
```

## E) חוקים שלא משתנים

- מותר: publish אחרי שערים + verify חי; Insights מאומתים; קריאת פיד/סטורי דרך אותו MCP
- אסור: auto-DM, boost, follow-back, ₪/Insights/SKU מומצאים, לטעון live בלי אימות
- אין סוד בגיט

קטלוג ליבה: [`packages/vfmcp/CORE-MCP.md`](../vfmcp/CORE-MCP.md). מפת פערים: [`GAP.md`](../vfmcp/GAP.md).
