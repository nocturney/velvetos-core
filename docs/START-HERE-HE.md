# התחלה — Velvet Factory (הדרך הכי פשוטה)

**לא צריך** ריפו שני · **לא צריך** `gh` · **לא צריך** PAT (ברוב המקרים)

---

## שלושה צעדים

### 1. התקן Git (פעם אחת)

הורד והתקן: https://git-scm.com/download/win  
(Next → Next → סיום — ברירות מחדל בסדר)

### 2. הרץ קובץ אחד

1. שכפל את הריפo:
   ```text
   git clone https://github.com/nocturney/velvetos-core.git
   ```
2. ב-Explorer, היכנס ל:
   ```text
   velvetos-core\instances\velvet-factory\
   ```
3. **לחיצה כפולה** על **`START-VF.bat`**

הסקריפט ימשוך את הליבה ויציג לך את הנתיב לפתיחה ב-Cursor.

### 3. פתח ב-Cursor

**File → Open Folder** → בחר את התיקייה:
```text
...\velvetos-core\instances\velvet-factory
```

**זהו.** זה ה-workspace היומיומי של VF.

---

## מה קורה מאחורי הקלעים

```
velvetos-core/                    ← ריפo אחד ב-GitHub
  instances/velvet-factory/       ← **כאן** אתה עובד ב-Cursor
    vendor/velvetos-core/         ← נוצר אוטומטית ע"י START-VF.bat
```

הריפo `velvetos-velvet-factory` **אופציונלי** — רק אם תרצה בעתיד לפצל לגמרי.  
**עכשיו אפשר לדלג עליו.**

---

## אם BAT נכשל

פתח **Git Bash** (מתפריט Start אחרי התקנת Git), הדבק:

```bash
cd ~/velvetos-core/instances/velvet-factory
./scripts/attach-core.sh
```

ואז פתח את אותה תיקייה ב-Cursor.

---

## VF (קבוע)

WhatsApp `050-2517000` · איסוף שדרות · IG `@velvets_cloud`
