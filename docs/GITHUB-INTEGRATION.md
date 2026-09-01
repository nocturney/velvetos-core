# GitHub Integration — PR אוטומטי מ-Cloud Agent

Cloud Agents דוחפים ענפים (`git push`) אבל **פתיחת PR** דורשת הרשאות GitHub App של Cursor.

## בעיה שנראתה

- ענף נדחף ל־`nocturney/velvetos-core` ✓
- `ManagePullRequest` / `gh pr create` נכשל — «אין הרשאת integration»
- **לא קשור** ל-private/public — זה הרשאות האפליקציה

## תיקון (בעלים, ~2 דקות)

1. פתח https://github.com/settings/installations
2. מצא **Cursor** → **Configure**
3. **Repository access:**
   - בחר **All repositories**, או
   - **Only select** → סמן:
     - `nocturney/velvetos-core`
     - `nocturney/velvetos-velvet-factory`
4. ודא שההרשאות כוללות (לפחות):
   - **Contents:** Read and write
   - **Pull requests:** Read and write
   - **Metadata:** Read-only (ברירת מחדל)
5. שמור

## אימות

הרץ Cloud Agent על ענף בדיקה:

```
עשה שינוי קטן ב-README, commit, push, ופתח PR ל-main
```

אם עדיין נכשל — בדוק גם:

- https://cursor.com/dashboard → הגדרות צוות / GitHub connection
- שה-repo לא חסום ב-org policy

## מה עדיין לא יעבוד

| פעולה | מי עושה |
|---|---|
| `createRepository` (ריפו חדש ריק) | בעלים ידנית ב-GitHub |
| מחיקת ריפו | בעלים |
| שינוי visibility | בעלים (כבר public ✓) |

`scripts/publish-instance.sh` ממשיך לדרוש ריפו קיים מראש.
