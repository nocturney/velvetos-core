# CONNECT-IG · Instagram MCP קנוני (adelaidasofia)

סטטוס שולחן: **`ready`** — Cloud Run Streamable HTTP מאומת (`remote_access: ready`).  
`auth: ready` · `transport: streamable-http` · `remote_access: ready`.  
Fallback מקומי: Codespace/Desktop **stdio** (`DEPLOY-CODESPACE.md`) — לא מחליף אוטונומיית Cloud.

**נתיב אוטונומיה (ייצור):** Streamable HTTP + bearer — [`REMOTE.md`](REMOTE.md) · `packages/vfigos/remote/` · `scripts/vf_instagram_mcp_remote_health.py`.  
מצב בריאות מרוחק (בלי סודות): [`live/remote-health.json`](live/remote-health.json).

MCP קנוני: [`adelaidasofia/instagram-mcp`](https://github.com/adelaidasofia/instagram-mcp) · חבילה `adelaidasofia-instagram-mcp` · שם שרת `instagram`.  
**לגאסי:** [`jlbadano/ig-mcp`](https://github.com/jlbadano/ig-mcp) — לא ראשי יותר. ראו [`LEGACY-IG-MCP.md`](LEGACY-IG-MCP.md).

אין סודות בגיט. אין אוטו־DM. אין בוסט. אין Metricool כתלות תפעול.  
Capability contract: [`CAPABILITIES.json`](CAPABILITIES.json).  
מצבי פרסום: [`PUBLICATION-STATES.md`](PUBLICATION-STATES.md) — upload/schedule/publish tool ≠ `liveVerified`.  
פריסת Codespace (stdio): [`DEPLOY-CODESPACE.md`](DEPLOY-CODESPACE.md).  
**פריסה מרוחקת (Cloud autonomy):** [`REMOTE.md`](REMOTE.md).  
מדיה ציבורית לפרסום: [`docs/MEDIA-VAULT.md`](../../docs/MEDIA-VAULT.md) § «URL ציבורי לפרסום» — נפרד מ־MCP transport.

## מצב מאומת (לא לבקש שוב מכריסטיאן)

| עובדה | ערך |
|---|---|
| חשבון | `@velvets_cloud` |
| Instagram Business Account ID | `17841407772120429` |
| קישור לעמוד Facebook | מאומת |
| `add_account` | label `velvets_cloud` · default `true` |
| כלים שעבדו ב־Codespace | `healthcheck` · `get_profile` · `list_media` |
| סודות | Secret Manager / Cloud Run + Codespaces Secrets / runtime env — **לא בגיט** |

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

שמות סודות נוספים לנתיב המרוחק (ערכים רק ב־host / Team MCP — לא בגיט):

| שם | תפקיד |
|---|---|
| `VELVET_INSTAGRAM_MCP_BEARER_TOKEN` | שער MCP (≠ Meta token; ≥24 תווים) |
| `INSTAGRAM_MCP_REMOTE_URL` | `https://…/mcp` אחרי deploy |
| `INSTAGRAM_MCP_APP_SECRET` | אופציונלי |
| `INSTAGRAM_MCP_DEFAULT_ACCOUNT` | `velvets_cloud` |
| `INSTAGRAM_MCP_DM_ENABLED` | חייב להישאר כבוי |

התקנה:

```bash
pip install adelaidasofia-instagram-mcp
# או מ־source:
# git clone https://github.com/adelaidasofia/instagram-mcp
# cd instagram-mcp && python3 -m venv .venv && .venv/bin/pip install -e .
```

## B) Cloud Agent / אוטונומיה מלאה (Streamable HTTP)

stdio בתוך Codespace ישן/כבוי **אינו** מספיק למשרד תמיד-דלוק.  
נתיב ייצור: [`REMOTE.md`](REMOTE.md) · עטיפה `packages/vfigos/remote/` · **Google Cloud Run** (`me-west1`, scale-to-zero).

| שדה | ערך נוכחי (אמת) |
|---|---|
| ארכיטקטורה | Cloud Run Streamable HTTP + bearer gate |
| Host / region / service | `instamcp` · `me-west1` · `velvet-instagram-mcp` |
| URL | נשמר ב־`live/remote-health.json` אחרי healthcheck (אין סודות) · client: `INSTAGRAM_MCP_REMOTE_URL` |
| Auth ל־MCP | `VELVET_INSTAGRAM_MCP_BEARER_TOKEN` |
| Meta token | רק על השרת המארח (`INSTAGRAM_MCP_ACCESS_TOKEN` ב־Secret Manager) |
| `remote_access` | **ready** — `python3 scripts/vf_instagram_mcp_remote_health.py --write` יצא 0 (2026-09-09) |
| קובץ אמת | [`live/remote-health.json`](live/remote-health.json) |

כש־`remote-health.json` degraded: failover [`SEND.md`](SEND.md). אין לפרסם דרך MCP בלי health ok.  
Codespace/dev fallback: [`DEPLOY-CODESPACE.md`](DEPLOY-CODESPACE.md).

## C) Insights (vfinsights)

מקור מועדף: `get_account_insights` / `get_media_insights` / `get_audience_insights`.  
מדד ש־Meta לא מחזירה → «אין ספירה» / unavailable. לא ממציאים.  
הדבקת בעלים נשארת גיבוי כשאין MCP. Metricool = אופציונלי לגאסי, לא קנוני.

## D) VF `mcpBind`

```
instagram.enabled = true
instagram.when = remote-streamable-http-when-ready-or-codespace-stdio-fallback
instagram.publish = true
instagram.dm = false
instagram.connect = packages/vfigos/CONNECT-IG.md
instagram.remote = packages/vfigos/REMOTE.md
```

## E) חוקים שלא משתנים

- מותר: publish אחרי שערים + verify חי; Insights מאומתים; קריאת פיד/סטורי דרך אותו MCP
- אסור: auto-DM, boost, follow-back, ₪/Insights/SKU מומצאים, לטעון live בלי אימות
- אין סוד בגיט

קטלוג ליבה: [`packages/vfmcp/CORE-MCP.md`](../vfmcp/CORE-MCP.md). מפת פערים: [`GAP.md`](../vfmcp/GAP.md).
