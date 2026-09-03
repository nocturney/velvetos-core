# Origin slugs — איך מטפלים בחסר

לא פק חדש. נוהל קטלוג על `docs/BACKUP.md` + `packages/manifest.json`.

**חוק:** לא ממציאים Origin slug. כותבים `unknown` / `origin-slug-unknown` וממשיכים. ה-HQ overlay (`SKILL.md` + `hq/`) הוא המשרד.

## מה השורה ב-README אומרת

אחת-עשרה חבילות היו עם `bcId` בלי `christian-velvet/tmp-…`. **מ-2026-09-01** הן מסווגות **`hq-native`** — העץ חי ב-Core; ה-bcId הוא שורש היסטורי בלבד, לא מחכים ל-vendor.

`vfops` · `vfcovers` · `vfinsights` · `vfbooks` · `vfresearch` · `vfbiz` · `vfcopy` · `vlicense` · `vfseason` · `vfsku` · `vfbriefux`

שישה פקים עם slug ידוע (`vfigos`, `vfcost`, `vfconvert`, `vfgrowth`, `vfprod`, `vfsales`) — vendor דורש `origin auth login` (ראה `docs/OWNER-ACTIONS-he.md`).

## מה עושים עכשיו (סוכן HQ)

1. **לא ממציאים** `christian-velvet/tmp-…`. אין slug = `unknown`.
2. **לא עוצרים את המשרד.** `SKILL.md` + `hq/` כבר על הדיסק. בריף, פנייה, כריכות, עלות — רצים בלי עץ Origin.
3. `scripts/vendor-origin-packs.sh` מדלג על slug ריק (`SKIP … no Origin slug`). זה מצב תקין.
4. מריצים דיווח, לא השלמה:

```bash
python3 scripts/discover-origin-slugs.py
```

5. אם `origin repo list` מחזיר רק את HQ — רושמים «רשימה מצומצמת» וממשיכים. Failover ≠ המצאת slug.

## למה הגילוי נכשל גם אחרי login

בדיקה 2026-08-31 על Cloud Agent עם Origin CLI מחובר:

| ניסיון | תוצאה |
|---|---|
| `origin repo list --namespace christian-velvet` | רק `christian-velvet/velvet-factory-headquarters-os` |
| `origin repo view` על slug **ידוע** (`tmp-20e9908caebda9d0` / vfigos) | `token is not scoped` — מגבלה על הטוקן, לא על החשבון |
| `batch-fetch-details` ל-11 bcId של החבילות | לא נגישים מסביבת HQ הזו |
| רשימת סוכני Cloud בסביבה | 69 ריצות על HQ; אין את סוכני ה-tmp |

כלומר: login ל-Origin **לא** פותח את רשימת עצי ה-tmp. צריך טוקן עם scope ל-`christian-velvet/tmp-*`, או העתקה מדף הסוכן.

**2026-09-01:** ריפוז GitHub פומביים (`velvetos-core`, `velvetos-velvet-factory`) **לא** פותחים את זה — `origin.cursor.com` עדיין דורש `origin auth login` / `CURSOR_API_KEY`; vendor נכשל בלי auth. ראה `docs/OWNER-ACTIONS-he.md`.

## איך ממלאים slug (ראש צוות / Grok / אדם עם דף הסוכן)

רק כשיש slug אמיתי ביד. לא מנחשים.

1. פותחים את קישור הסוכן מ-`packages/<name>/ORIGIN.md` (או טבלת README).
2. מעתיקים Origin slug / codebase URL מדף הסוכן.
3. שולחים ל-HQ לפי [`BACKUP.md`](BACKUP.md):

```
bcId: bc-…
pack: <packages/name>
origin: <owner/repo>
```

4. באותו יום: מעדכנים `ORIGIN.md` + `packages/manifest.json` (`originSlug`, `codebaseUrl`, `cloneUrl`, `vendorStatus`).
5. שורת `CHANGELOG.md` Unreleased (עברית+אנגלית).
6. Vendor רק אם הטוקן באמת משכפל את ה-tmp:

```bash
./scripts/vendor-origin-packs.sh
```

`vendorStatus` אחרי מילוי slug בלי clone: `origin-unreachable` (כמו vfigos). אחרי clone מוצלח: מעדכנים את ה-ORIGIN עם commit.

## מה לא

- לא ממציאים slug «כדי לסגור את הרשימה».
- לא טוענים שהעץ הועתק אם vendor לא הצליח.
- לא יושבים בסרק כי Origin list ריק.
- לא פק חדש לכל slug חסר.
- לא פותחים Treg בשביל זה.

## מי מטפל

```bash
python3 scripts/vfmem.py who origin slug
```

`@workflow-architect` על `vfharness`. המפה נשארת ב-GitHub HQ גם בלי עצים.

## סנסור

```bash
python3 scripts/check-origin-slugs.py
```

תופס: slug מומצא, manifest מול ORIGIN לא תואם, פלייבוק חסר, vendor שלא מדלג על ריק.
