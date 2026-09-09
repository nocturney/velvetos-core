# CONNECT-IG · Instagram MCP קנוני (adelaidasofia)

סטטוס שולחן: **`ready`** — Cloud Team MCP namespace `instagram` מאומת ב־2026-09-09.  
`auth: ready` · `transport: streamable-http` · **`remote_access: ready`** (`live_check.ok=true` · `get_profile`=`velvets_cloud` · `list_media` ok).  
Codespace stdio נשאר נתיב גיבוי מקומי (ראה [`DEPLOY-CODESPACE.md`](DEPLOY-CODESPACE.md)).

MCP קנוני: [`adelaidasofia/instagram-mcp`](https://github.com/adelaidasofia/instagram-mcp) · חבילה `adelaidasofia-instagram-mcp` · שם שרת `instagram`.  
**לגאסי:** [`jlbadano/ig-mcp`](https://github.com/jlbadano/ig-mcp) — לא ראשי יותר. ראו [`LEGACY-IG-MCP.md`](LEGACY-IG-MCP.md).

אין סודות בגיט. אין אוטו־DM. אין בוסט. אין Metricool כתלות תפעול.  
Capability contract: [`CAPABILITIES.json`](CAPABILITIES.json).  
ChatGPT Business connect: [`CHATGPT-MCP.md`](CHATGPT-MCP.md) — **CONNECTED + VERIFIED 2026-09-09** (API key).  
Graph mutations honesty: [`GRAPH-MUTATIONS.md`](GRAPH-MUTATIONS.md).  
Insights Graph v21 overlay: [`remote/insights_v21.py`](remote/insights_v21.py) (deploy required).  
CTA live audit: `audit_public_cta` / [`cta_audit.py`](cta_audit.py).  
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
| Insights (Graph v21 overlay) | `get_account_insights` · `get_media_insights` · `get_audience_insights` — splits `metric_type=total_value`; no invented metrics |
| CTA audit (read-only) | `audit_public_cta` · `audit_profile_cta` |
| Mutation honesty | `graph_mutation_matrix` (SoT) · profile/caption writes **not exposed** · `delete_media` gated |
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

Endpoint מרוחק (Cloud Run / Team MCP, שם שרת `instagram`) **מאומת** ב־2026-09-09:  
`healthcheck.live_check.ok=true` · `get_profile.username=velvets_cloud` · `list_media` ok.  
שולחן: `remote_access: ready`. סודות רק ב־host vault — לא בגיט.  
אם MCP/oauth נכשל בזמן אמת: failover [`SEND.md`](SEND.md) אותו תור.

Public URL (streamable-http): `https://velvet-instagram-mcp-1016876126699.me-west1.run.app/mcp`  
Connector auth: `VELVET_INSTAGRAM_MCP_BEARER_TOKEN` (Bearer) — **לא** הטוקן של Meta.  
Remote entry source: [`remote/`](remote/README.md). ChatGPT Business: [`CHATGPT-MCP.md`](CHATGPT-MCP.md).

### ChatGPT Business · Custom MCP

| Authentication ב־ChatGPT | תוצאה |
|---|---|
| OAuth | נכשל — השרת לא מממש OAuth discovery (צפוי) |
| No Auth | נכשל — `initialize` מחזיר **401 Bearer** (השרת דורש מפתח מחבר) |
| **API key** | הנכון — להדביק `VELVET_INSTAGRAM_MCP_BEARER_TOKEN` |

אין להשאיר endpoint עם publish כ־No Auth ציבורי. אין להדביק `INSTAGRAM_MCP_ACCESS_TOKEN` ב־ChatGPT.

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

## E) מעקב פקיעת טוקן

קובץ: [`data/token-watch.json`](data/token-watch.json) · מדריך: [`TOKEN-WATCH.md`](TOKEN-WATCH.md).  
Watchdog + בריף 01 מתריעים כש־`expiresAt` חסר / קרוב / פג — **רק מתאריך Meta מאומת**.  
אסור לשמור את הטוקן עצמו בדוחות, בגיט או בבריף.

## F) חוקים שלא משתנים

- מותר: publish אחרי שערים + verify חי; Insights מאומתים; קריאת פיד/סטורי דרך אותו MCP
- אסור: auto-DM, boost, follow-back, ₪/Insights/SKU מומצאים, לטעון live בלי אימות
- אין סוד בגיט

קטלוג ליבה: [`packages/vfmcp/CORE-MCP.md`](../vfmcp/CORE-MCP.md). מפת פערים: [`GAP.md`](../vfmcp/GAP.md).
