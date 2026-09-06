# איך מחברים את Instagram MCP (ig-mcp) ל-Cursor

מקור: [jlbadano/ig-mcp](https://github.com/jlbadano/ig-mcp) — MCP על Instagram Graph API.  
פרוטוקול שליחה: [`SEND.md`](SEND.md) + [`constitution/SEND.md`](../../constitution/SEND.md).  
קטלוג ליבה: [`packages/vfmcp/CORE-MCP.md`](../vfmcp/CORE-MCP.md) · [`core-mcp.json`](../vfmcp/core-mcp.json).  
אין סודות בגיט. אין אוטו־DM. אין בוסט.

## מה זה סוגר

| פער היום | אחרי חיבור |
|---|---|
| Publish לפיד — `#ממתין-ל-כלי-IG` | `publish_media` → `#נשלח-מ-HQ` |
| Insights — «אין ספירה» / הדבקת בעלים | `get_media_insights` + resources מאומתים |
| סקירת פיד / פוסטים אחרונים | `get_media_posts` · `get_profile_info` |
| Failover Canva+Drive+Gmail | נשאר — רק כש־MCP down או `needsAuth` |

## מה זה **לא** סוגר

| נושא | למה |
|---|---|
| **Stories** | ig-mcp מפרסם פוסט/קרוסלה/וידאו לפיד — לא Story API |
| **אוטו־DM / follow-back** | נעול בחוקה. `send_dm` / `get_conversations` דורשים Meta App Review — **לא מפעילים** |
| **בוסט / Ads** | [`meta-ads-mcp`](../../docs/MCP-FIT.md) — lead gate בלבד |
| **וואטסאפ לקוח** | אדם `050-2517000` — אין MCP שליחה |
| **Canva** | עדיין מקור המדיה. ig-mcp מקבל URL לתמונה/וידאו (export מ־Canva) |

## דרישות מוקדמות

1. **`@velvets_cloud` = Business Account** מקושר ל־Facebook Page
2. **Facebook Developer App** עם Instagram Graph API
3. **Long-lived Page Access Token** (מתחדש ~כל 60 יום)
4. **Python 3.10+** על המחשב שמריץ את שרת ה־MCP

הרשאות Standard (מיד): `instagram_basic`, `instagram_content_publish`, `instagram_manage_insights`, `pages_show_list`, `pages_read_engagement`.

מדריך מהיר: [AUTHENTICATION_GUIDE.md](https://github.com/jlbadano/ig-mcp/blob/main/AUTHENTICATION_GUIDE.md).

## A) Desktop — Cursor Agent מקומי

לא שמים את השרת ב־`.cursor/mcp.json` של הריפו (טוקן + נתיב מקומי). כמו Sheets/WhatsApp — רק ב־`~/.cursor/mcp.json`.

### 1. התקנת השרת (פעם אחת)

```bash
git clone https://github.com/jlbadano/ig-mcp.git ~/ig-mcp
cd ~/ig-mcp
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp env.example .env
# ערוך .env — אין commit
python scripts/setup.py      # בדיקת credentials
```

### 2. הוספה ל־`~/.cursor/mcp.json`

`Ctrl+Shift+P` → **View: Open MCP Settings** → הוסף ל־`mcpServers` (או העתק מ־[`mcp.desktop.example.json`](../vfmcp/mcp.desktop.example.json)):

```json
"instagram": {
  "command": "/ABS/PATH/ig-mcp/.venv/bin/python",
  "args": ["/ABS/PATH/ig-mcp/src/instagram_mcp_server.py"],
  "env": {
    "INSTAGRAM_ACCESS_TOKEN": "${env:INSTAGRAM_ACCESS_TOKEN}",
    "INSTAGRAM_BUSINESS_ACCOUNT_ID": "${env:INSTAGRAM_BUSINESS_ACCOUNT_ID}",
    "FACEBOOK_APP_ID": "${env:FACEBOOK_APP_ID}",
    "FACEBOOK_APP_SECRET": "${env:FACEBOOK_APP_SECRET}"
  }
}
```

**אל תדביק טוקנים בגיט** — רק ב־mcp.json המקומי או ב־env vars של המערכת.

### 3. Reload + בדיקה

1. **Developer: Reload Window**
2. MCP Settings → `instagram` אמור להיות ירוק
3. בצ'אט Agent מקומי: «הצג פרופיל @velvets_cloud» או «5 פוסטים אחרונים עם insights»

## B) Cloud Agent

ig-mcp הוא **stdio Python** — לא HTTP כמו Canva. שני מסלולים:

### מסלול 1 (מומלץ): Team MCP + secrets בדשבורד

1. [cursor.com/dashboard](https://cursor.com/dashboard) → **Cloud Agents** → **Integrations & MCP**
2. **Add MCP server** → **stdio** (או Custom command)
3. Command: נתיב ל־python + `instagram_mcp_server.py` (או image מ־[`docker-compose.yml`](https://github.com/jlbadano/ig-mcp/blob/main/docker-compose.yml))
4. Secrets: `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_BUSINESS_ACCOUNT_ID`, `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET` — **בדשבורד בלבד**

### מסלול 2: environment build

אם צריך ig-mcp על כל ריצת Cloud Agent — הוסף install ב־environment (לא בגיט עם סודות) + Team MCP עם env vars.

עד שסודות מוגדרים: סטטוס השולחן נשאר `needsAuth` → failover Canva+Drive+Gmail.

## C) זרימת פרסום (vfigos)

```
vfcopy (כיתוב + CTA WhatsApp)
  → Canva export-design (URL לתמונה/וידאו)
  → instagram publish_media (caption + media_url)
  → #נשלח-מ-HQ ב־QUEUE.md
```

אם `instagram` = `needsAuth` / down:

```
Canva export → Drive create_file → Gmail send_message
→ #נשלח-מ-HQ + #ממתין-ל-כלי-IG
```

## D) Insights מאומתים (vfinsights)

אחרי חיבור: `get_media_insights` / resources — מספרים מ־Graph API בלבד.  
בלי חיבור: הדבקת בעלים או «אין ספירה» — לא ממציאים.

## E) תחזוקת טוקן

Long-lived token פג תוקף ~60 יום. לפני תפוגה:

```bash
curl -G "https://graph.facebook.com/v19.0/oauth/access_token" \
  --data-urlencode "grant_type=fb_exchange_token" \
  --data-urlencode "client_id=APP_ID" \
  --data-urlencode "client_secret=APP_SECRET" \
  --data-urlencode "fb_exchange_token=CURRENT_TOKEN"
```

עדכן את ה־secret בדשבורד / mcp.json המקומי — לא בגיט.

## F) VF `mcpBind`

```
instagram.enabled = true
instagram.when = desktop-or-team-mcp
instagram.publish = true
instagram.dm = false
```

## G) חוקים (לא משתנים)

- **מותר:** publish פוסט/קרוסלה/ריל (וידאו) אחרי סקירה; insights; קריאת פיד
- **אסור:** auto-DM, boost, follow-back, story hacks, ₪/Insights מומצאים
- **לא טוענים** שעלה לפיד אם `publish_media` לא החזיר success

מפת פערים: [`packages/vfmcp/GAP.md`](../vfmcp/GAP.md).
