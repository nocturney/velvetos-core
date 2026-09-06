# סנכרון iCloud → Google Drive (ל-Cloud Agent)

מטרה: קבצים שנשארים ב-iCloud על Mac **מגיעים ל-HQ בענן** דרך **Google Drive MCP** (`Google-drive` — `search_files`, `create_file`).

זה **לא** MCP iCloud בענן. זה **מראה (mirror)** בתיקיית Drive שהסוכן כבר מחובר אליה.

## עקרון

```
Mac: iCloud …/Velvet Factory/  ──rsync──►  Google Drive …/Velvet Factory/iCloud mirror/
                                                      │
Cloud Agent ◄─────────────────────────────────────────┘  search_files / read
```

## 1. Google Drive for Desktop (Mac)

1. התקן [Google Drive for desktop](https://www.google.com/drive/download/)
2. התחבר עם `nocturney@gmail.com` (אותו חשבון כמו MCP HQ)
3. ודא ש-**My Drive** מסונכרן מקומית (לא Streaming-only אם rsync איטי — Prefer mirror לתיקיית הסטודיו)

נתיב טיפוסי (2026):

`/Users/YOU/Library/CloudStorage/GoogleDrive-nocturney@gmail.com/My Drive/`

(ייתכן גם `GoogleDrive-…@gmail.com` — בדוק ב-Finder.)

## 2. תיקיית יעד ב-Drive

צור:

`My Drive/Velvet Factory/iCloud mirror/`

מבנה מirror (זהה ל-iCloud):

| תת-תיקייה | HQ מחפש |
|---|---|
| `floor/` | תוכן / ריל / רצפה |
| `stl/` | `vfprod`, `vfsku` |
| `jobs/<שם-עבודה>/` | חיפוש לפי שם job |
| `office/` | `vfbooks` — חשבונות בלבד |

**אל** תסנכרן תיקיות אישיות, רפואיות, או משפטיות.

## 3. סקריפט סנכרון (Mac)

מהשורש של הריפו:

```bash
chmod +x scripts/sync-icloud-to-drive.sh
./scripts/sync-icloud-to-drive.sh
```

משתני סביבה (אופציונלי):

```bash
export VF_ICLOUD_ROOT="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Velvet Factory"
export VF_GDRIVE_MIRROR="$HOME/Library/CloudStorage/GoogleDrive-nocturney@gmail.com/My Drive/Velvet Factory/iCloud mirror"
./scripts/sync-icloud-to-drive.sh
```

הסקריפט:

- מוריד placeholders של iCloud (`brctl download`) לפני העתקה
- מריץ `rsync` (ללא `--delete` כברירת מחדל — בטוח יותר)
- כותב לוג ל-`~/Library/Logs/velvet-factory-icloud-sync.log`

## 4. אוטומציה (launchd, אופציונלי)

כל 30 דקות בזמן שעות סטודיו:

1. העתק את [`examples/com.velvetfactory.icloud-sync.plist`](examples/com.velvetfactory.icloud-sync.plist) ל-`~/Library/LaunchAgents/`
2. ערוך נתיבים (`YOU`, נתיב Drive)
3. `launchctl load ~/Library/LaunchAgents/com.velvetfactory.icloud-sync.plist`

או **Shortcuts** / **Automator** שמריץ את הסקריפט אחרי שמירה בתיקיית `jobs/`.

## 5. איך Cloud Agent משתמש

אחרי סנכרון, בצ'אט Cloud:

- «חפש ב-Drive את הקובץ `<שם>` תחת Velvet Factory iCloud mirror»
- «קרא את ה-STL של job `<שם>` מ-iCloud mirror»

סוכן HQ **לא** טוען שהקובץ ב-iCloud — הוא קורא את **העותק ב-Drive**.

אם אין עותק: «אין ב-Drive — הרץ sync על Mac או העלה ידנית».

## 6. Failover

| מצב | פעולה |
|---|---|
| sync לא רץ / Mac כבוי | העלאה ידנית ל-Drive · או קובץ בצ'אט |
| Drive MCP down | שם קובץ שהמשתמש נתן בצ'אט · `ORCHESTRA.md` |
| קובץ רק ב-iCloud Desktop | Agent מקומי + MCP iCloud — [`CONNECT-ICLOUD.md`](CONNECT-ICLOUD.md) |

## 7. rclone (מתקדם, אופצional)

אם **אין** Google Drive for Desktop — `rclone sync` מ-iCloud path ל-`drive:Velvet Factory/iCloud mirror`.  
דורש הגדרת OAuth rclone נפרדת. לא בגיט. lead seat מחליט.

---

**קישורים:** Desktop MCP — [`CONNECT-ICLOUD.md`](CONNECT-ICLOUD.md) · שולחן — `.cursor/vf-desk.json` (`tools.icloud`, `tools.drive`).
