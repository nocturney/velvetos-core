# VelvetOS — Velvet Factory: הגדרה ב-Windows (בלי `gh`)

אם `git push` מחזיר **Repository not found** — זו כמעט תמיד **הרשאה / התחברות**, לא שגיאת כתיב.

## למה זה קורה

| מי | מה קורה |
|---|---|
| Cloud Agent (Cursor) | רואה רק `nocturney/velvetos-core`. **לא** רואה ריפו פרטי `velvetos-velvet-factory`. |
| המחשב שלך | צריך להתחבר ל-GitHub כ-**nocturney** עם PAT או Git Credential Manager. |
| `gh` | לא חובה. אפשר בלי. |

---

## דרך 1 — הכי פשוטה: ZIP + Git Bash (מומלץ)

### שלב א — הורד את החבילה

1. ב-GitHub: `nocturney/velvetos-core` → תיקייה `instances/velvet-factory`
2. או: הורד את `velvetos-velvet-factory-scaffold.zip` מה-artifacts של Cloud Agent / מה-release

### שלב ב — PAT (פעם אחת)

1. https://github.com/settings/tokens → **Generate new token (classic)**
2. סימון: **`repo`** (Full control of private repositories)
3. העתק את הטוקן — לא תראה שוב

### שלב ג — דחיפה לריפו הפרטי

פתח **Git Bash** (לא PowerShell רגיל):

```bash
# 1. שכפל את הריפו הפרטי (יצור תיקייה ריקה אם עדיין אין קבצים)
git clone https://github.com/nocturney/velvetos-velvet-factory.git
cd velvetos-velvet-factory

# 2. העתק את כל הקבצים מה-scaffold (לאחר חילוץ ה-ZIP)
#    לדוגמה אם חילצת ל-C:\Users\YOU\Downloads\velvet-factory:
cp -r /c/Users/YOU/Downloads/velvet-factory/* .
cp -r /c/Users/YOU/Downloads/velvet-factory/.cursor .
cp -r /c/Users/YOU/Downloads/velvet-factory/.gitignore .

# 3. commit + push
git add -A
git commit -m "VelvetOS instance scaffold: velvet-factory"
git push -u origin main
```

כשGit שואל **Username**: `nocturney`  
כשGit שואל **Password**: הדבק את ה-**PAT** (לא סיסמת GitHub)

> אם עדיין «Repository not found» — ודא שהריפו `nocturney/velvetos-velvet-factory` **קיים** תחת החשבון nocturney (Settings → Repositories).

---

## דרך 2 — PowerShell (בלי Bash)

```powershell
git clone https://github.com/nocturney/velvetos-velvet-factory.git
cd velvetos-velvet-factory

# העתק ידנית את תוכן instances/velvet-factory מה-core לכאן
# (Explorer: Ctrl+A מהתיקייה המקור → Ctrl+V)

git add -A
git commit -m "VelvetOS instance scaffold: velvet-factory"
git push -u origin main
```

אותו PAT כ-password.

---

## דרך 3 — מה-core (אם כבר שכפלת velvetos-core)

**Git Bash בלבד** (הסקריפט bash):

```bash
cd velvetos-core
git checkout main
git pull
PUSH=1 ./scripts/publish-instance.sh velvet-factory nocturney/velvetos-velvet-factory
```

---

## אחרי שה-push הצליח

```bash
cd velvetos-velvet-factory
./scripts/attach-core.sh    # Git Bash — מושך את velvetos-core ל-vendor/
```

פתח את **`velvetos-velvet-factory`** ב-Cursor כ-workspace יומיומי.

---

## עדכון remote ב-core המקומי (אם עדיין שם ישן)

```bash
cd velvetos-core
git remote set-url origin https://github.com/nocturney/velvetos-core.git
git remote -v
```

---

## שגיאות נפוצות

| הודעה | פתרון |
|---|---|
| `Repository not found` | PAT עם `repo`, או שם ריפו/owner שגוי, או לא מחובר כ-nocturney |
| `gh: command not found` | התעלם — לא צריך `gh` |
| `./scripts/...` ב-PowerShell | השתמש ב-**Git Bash** או בדרך 2 |
| Cloud Agent לא דוחף | נורמלי לריפו פרטי — דחוף **אתה** מהמחשב |

---

## CTA / VF (לא משתנה)

WhatsApp `050-2517000` · איסוף שדרות · IG `@velvets_cloud`
