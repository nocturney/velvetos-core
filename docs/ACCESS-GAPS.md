# פערי גישה — מצב אחרי ריפוז פומביים

עודכן: 2026-09-01. הריפוז `nocturney/velvetos-core` ו־`nocturney/velvetos-velvet-factory` **פומביים**.

## מה השתנה

| לפני (private) | אחרי (public) |
|---|---|
| Cloud Agent צריך token מיוחד ל־`repositoryDependencies` | `attach-core.sh` עובד בלי token ייעודי ל-core |
| README: «צור ריפו ריק **פרטי**» | clone / fork חופשי |
| Cloud Agent לא יכול `createRepository` | **עדיין לא יכול** — מגבלת הרשאות סוכן, לא visibility |

## צ'קליסט בעלים (פעם אחת)

סמן ✓ כשסיימת. פירוט מלא בקישורים.

### 1. GitHub Integration ל-Cursor

→ [`GITHUB-INTEGRATION.md`](GITHUB-INTEGRATION.md)

- [ ] GitHub → Settings → Applications → **Cursor** → Configure
- [ ] גישה ל־`nocturney/velvetos-core` ו־`nocturney/velvetos-velvet-factory`
- [ ] הרשאות: Contents (read/write), Pull requests (read/write)
- [ ] אימות: Cloud Agent פותח PR על core בלי «integration failed»

### 2. 3D AI Studio (Cloud + Desktop)

→ [`packages/vfprod/CONNECT-3DAI.md`](../packages/vfprod/CONNECT-3DAI.md)

- [ ] **Desktop:** deeplink או `.cursor/mcp.json` → Connect → OAuth
- [ ] **Cloud:** Dashboard → Integrations & MCP → HTTP `threedaistudio` → `https://mcp.3daistudio.com/mcp`
- [ ] **Cloud:** cursor.com/agents → MCP dropdown → Connect (OAuth נפרד מ-Desktop)
- [ ] אימות: «בדוק יתרת קרדיטים ב-3D AI Studio»

### 3. Canva (אם לא מחובר)

→ [`docs/CANVA.md`](CANVA.md) · [`packages/vfcanva/CONNECT.md`](../packages/vfcanva/CONNECT.md)

- [ ] Team MCP: `https://mcp.canva.com/mcp` (כמו 3DAI)
- [ ] OAuth ב־cursor.com/agents

### 4. Instagram Publish

→ [`packages/vfigos/CONNECT-IG.md`](../packages/vfigos/CONNECT-IG.md)

**אין MCP Publish מובנה ב-Cursor נכון לעכשיו.**

- [ ] בדוק Dashboard → Integrations & MCP — אם הופיע Meta/Instagram, חבר
- [ ] עד אז: failover `vfigos/SEND.md` (Canva + Drive + Gmail) — **כבר מוגדר**
- [ ] פרסום חי דחוף: אדם + `LIVE-PACKET.md` או Grok כגיבוי

### 5. Origin packs (vendor tmp trees)

→ [`ORIGIN-SLUGS.md`](ORIGIN-SLUGS.md)

6 חבילות עם slug ידוע אבל `origin-unreachable` (טוקן לא scoped ל־`tmp-*`):

`vfigos` · `vfcost` · `vfconvert` · `vfgrowth` · `vfprod` · `vfsales`

11 חבילות עדיין `origin-slug-unknown` — צריך slug מדף הסוכן.

```bash
# על מכונה עם חשבון christian-velvet / Origin scoped
origin auth login
python3 scripts/discover-origin-slugs.py
./scripts/vendor-origin-packs.sh
python3 scripts/check-origin-slugs.py
```

- [ ] `origin auth login` (או `export CURSOR_API_KEY=…` עם scope ל־tmp)
- [ ] `vendor-origin-packs.sh` מצליח לפחות ל־6 ה-slugs הידועים
- [ ] מילוי slug ל־11 הנותרות מדפי הסוכן (`packages/*/ORIGIN.md`)

### 6. מה **לא** נפתח בפומבי

| חסימה | סיבה | פתרון |
|---|---|---|
| Grok / X | חומת התחברות | failover כלים כאן + `ORCHESTRA.md` |
| Perplexity שיתוף | Cloudflare / סשן פרטי | PDF מהבעלים או ChatGPT+Gemini |
| iCloud / קבצים מקומיים | אין mount לענן | העלה ל-Drive או צרף בצ'אט |
| Mobbin | פלאגין דסקטופ | `brief-email.html` / Superdesign |
| FCC (free-claude-code) | Mac בלבד | `vffcc` — לא על Cloud Agent |
| `createRepository` | token סוכן | צור ריפו ידנית ב-GitHub |

## אימות אחרי setup

```bash
./scripts/attach-core.sh   # או START-VF.bat
python3 vendor/velvetos-core/scripts/check-all.py
```

Cloud Agent: הרץ «בדוק MCP — Canva, 3DAI, Gmail» ודווח `needsAuth` שנשאר.
