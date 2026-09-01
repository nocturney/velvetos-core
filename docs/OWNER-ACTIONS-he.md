# פעולות בעלים — מה Cloud Agent לא יכול לסגור לבד

עודכן 2026-09-01 אחרי ריצת `discover-origin-slugs.py` + `vendor-origin-packs.sh` + בדיקת הרשאות GitHub.

## 1. Origin vendor (6 פקים `tmp-*`)

**סטטוס:** `origin auth login` לא מחובר; clone ל-`origin.cursor.com` נכשל.

**אצלך (פעם אחת):**

```bash
origin auth login
# או: export CURSOR_API_KEY=...   # טוקן עם scope ל-christian-velvet/tmp-*
./scripts/vendor-origin-packs.sh
```

**לא נפתח מפומבי ב-GitHub** — זה Cursor Origin, לא GitHub.

---

## 2. Push ל-`velvetos-velvet-factory`

**סטטוס:** קריאה OK (ריפוזים פומביים). אחרי **Uninstall + חיבור מחדש** ל-Cursor ב-GitHub — **Agent שכבר רץ** עדיין מחזיק טוקן **מבוטל** (`gh`: invalid token; `git push`: Authentication failed). **חובה Agent חדש** כדי לקבל טוקן טרי.

**אחרי חיבור מחדש:**

1. **פתח Cloud Agent חדש** על `velvetos-core` (לא להמשיך ריצה ישנה)  
2. אימות: `gh api repos/nocturney/velvetos-velvet-factory --jq .permissions.push` → `true`  
3. `PUSH=1 ./scripts/publish-instance.sh velvet-factory nocturney/velvetos-velvet-factory`  

**או מקומית** (מיד, בלי Agent חדש):

```bash
PUSH=1 ./scripts/publish-instance.sh velvet-factory nocturney/velvetos-velvet-factory
```

**אימות מהיר אחרי Agent חדש:**

```bash
gh api repos/nocturney/velvetos-velvet-factory --jq .permissions.push
# צריך: true
```

**מקומית (תמיד עובד עם PAT שלך):**

```bash
PUSH=1 ./scripts/publish-instance.sh velvet-factory nocturney/velvetos-velvet-factory
```

**לפני push — מה השתנה:**

```bash
./scripts/sync-instance-scaffold.sh
```

---

## 3. Mobbin MCP על Cloud

**סטטוס:** פלאגין על הדיסק; namespace **לא** מופיע ב-Cloud Agent הזה.

**אצלך:** Dashboard → Cloud Agents → Environment → Integrations & MCP → הפעל Mobbin.

**עד אז:** `vfbriefux` templates / Superdesign (`tools.mobbin.failover`).

---

## 4. Instagram Publish MCP

**סטטוס:** אין namespace — לא קיים ב-Cursor MCP catalog.

**משרד:** `packages/vfigos/SEND.md` — Canva + Drive + Gmail; `#ממתין-ל-כלי-IG` עד שיופיע כלי Publish.

---

## 5. מה כבר תוקן בקוד (2026-09-01)

| נושא | סטטוס |
|------|--------|
| 3D AI Studio על Cloud | **ready** — namespace `3DAIStudio` מאומת |
| 11 פקים בלי Origin slug | **hq-native** — העץ חי ב-Core, לא מחכים ל-tmp |
| ריפוז פומביים | קריאה מ-Cloud Agent |
| `.cursor/environment.json` (Core) | `repositoryDependencies` כולל instance repo |
