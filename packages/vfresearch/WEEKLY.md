# סקירת קישורי השראה — שבועי

מושב: **מחקר/אורקסטרציה** (`@research-synthesist`) + ראש צוות קורא בבריף.  
לא פק חדש. לא clock נוסף. כאן חוזרים על **קישורים שנשלחו** ועל ריפוזי השראה שכבר הוטמעו, בתוך Research Seat / Weekly Research Accountability או משימה מפורשת.

רישום: `packages/vfresearch/LINKS.json`  
מפת ChatGPT: `packages/chatgpt-embed-map.json`  
חוקה: `constitution/ORCHESTRA.md` · שגרה: `vfops/ROUTINE.md`

## מתי

ה־clock הקבוע הוא **Weekly Research Accountability — Friday 12:00 Asia/Jerusalem** בתוך protected Grok routine inventory. סקירת הקישורים היא capability של אותו Research Seat ויכולה לרוץ גם במשימה מפורשת; אין Sunday timer / ChatGPT / Cursor cron נוסף.

אירוע לוח שנה: רק אם ראש צוות מבקש יצירה; אירוע כזה אינו scheduler authority. HQ לא יוצר אירוע בלי אישור.

## צעדים (Research Seat; Cursor/Cloud הם execution tools, לא clock authority)

1. לקרוא את `LINKS.json` מלמעלה למטה.
2. לכל קישור:
   - לפתוח את ה-URL (או את `openUrl` / PDF / `sourceNote` אם החי חסום).
   - להשוות לגוף שכבר ב־`sources/` / `docs/` / המפה.
   - **יש עדכון שימושי** → להטמיע **במקום** על פק קיים (טבלת מיפוי ב־`constitution/ORCHESTRA.md`). לעדכן `lastReviewed`.
   - **אין שינוי** → לרשום «ללא שינוי» ולעדכן רק `lastReviewed`.
   - **חומה / סשן פרטי / מנוי** → «דולג — חומה». **לא ממציאים גוף.**
3. לשאול במפורש: *מה חדש לחקור ולנצל לטובתנו?* — רק ממצאים עם מקור אמיתי. בלי ₪, בלי Insights מומצאים, בלי פק חדש.
4. **באותו מעבר שבועי:** דופק Print · Demand · Sound — `hq/PRINT-DEMAND.md` → ארטיפקט `sources/YYYY-MM-DD-print-demand.md` (טרנדים ויזואליים 3D + ביקוש IL + סאונד מ־`MUSIC.md`). בלי אוטו־DM / בלי שעות חמות מומצאות.
5. לכתוב ארטיפקט קישורים: `packages/vfresearch/sources/YYYY-MM-DD-weekly-links.md`
6. שורת בלוק `05-משרד` בבריף הבא (`vfops/BRIEF.md`):
   - יש הטמעה: «שבועי קישורים — הוטמע X ב־`<pack>`» · «print-demand — N אותות»
   - אין: **«שבועי קישורים — אין חדש במשרד»** / «print-demand — אין חדש»
7. אחרי שינוי קטלוג/כלל/פק: `python3 scripts/check-all.py`
8. קישור חדש שהבעלים שלח באמצע השבוע: להוסיף ל־`LINKS.json` **באותו יום** (לא לחכות ל־Friday accountability).

## תבנית ארטיפקט

```markdown
# סקירת קישורים שבועית · YYYY-MM-DD

Research metadata:
- as_of: YYYY-MM-DD / source observation time
- provenance: LINKS.json + URLs/provider refs actually read
- uncertainty: walls/missing reads/none_known
- refresh_target: next Friday 12:00 accountability or explicit task

מושב: ייצור · Asia/Jerusalem
רישום: packages/vfresearch/LINKS.json

## מה נבדק

| id | סטטוס | הערה |
|---|---|---|
| chatgpt-building-agents | ללא שינוי / הוטמע / דולג | … |

## מה הוטמע

- (פק + קובץ) או «אין»

## מה חדש לחקור

- (רק עם מקור) או «אין»

## מה דולג

| מה | למה |
|---|---|
| … | חומה / מנדט / בלי מקור |

## בלוק 05

…
```

## חומות (זהות לתזמורת + failover)

| מצב | מה עושים |
|---|---|
| Cloudflare / רובוט / סשן פרטי | דולגים על הגוף. לא ממציאים. ממשיכים בקישור הבא ברשימה **מיד**. |
| מנוי נדרש | לא אורח. רושמים לראש צוות. עוברים לקישור/מקור פתוח אחר עכשיו. |
| כלי אחד הצליח ואחר לא | מטמיעים רק מגוף אמיתי. |
| הצעת אוטו־DM / שליחה / ₪ / אתר מ־HQ | דולגים — מנדט. |
| כל הקישורים חסומים | ארטיפקט עם «אין גוף» + «אין חדש במשרד» — לא ממציאים. |

## לא כאן

- Research Seat יומי 02:00 (`DAILY.md`) — גוף מחקר יומי, לא רישום קישורים שבועי.
- גיבוי GitHub (`docs/BACKUP.md`) — אותו יום לכל פק; לא מחליף את הסקירה השבועית.
- שליחת אינסטגרם / ג׳ימייל / וואטסאפ מ־HQ.
- **אין timer כפול:** `BEST-SKILLS.json` עם `standingForever:true` הוא due-check בתוך Research Seat; `TIMER.md` מתאר cadence ולא יוצר scheduler/provider נוסף.

## Discovery catalogue rule — API mega lists

`cporter202/API-mega-list` and `cporter202/social-growth-apis-for-creators` are reviewed as discovery catalogues only. Catalogue presence, featured placement, sponsored placement, or provider copy is not approval. Weekly review should look for a concrete VelvetOS capability gap, independently verify the strongest provider candidate, and embed only through an existing pack/contract. Never vendor/import the catalogue or create an API-mega runtime.
