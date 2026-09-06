# Mastery + memory layers — דפוס למידה (DeepTutor)

מקור: [HKUDS/DeepTutor](https://github.com/HKUDS/DeepTutor) (Apache-2.0 · Lifelong Personalized Tutoring).  
**דפוסים בלבד.** אין Docker/Compose של DeepTutor, אין EduHub skill install, אין runtime חונכות שני.

## רעיון

מערכת למידה אחת עם הקשר משותף: שליטה (mastery) לפני «עברתי», זיכרון בשכבות שאפשר לבדוק, ושאלון מכישלונות מדורגים.

## מיפוי למשרד

| DeepTutor | VelvetOS / VF |
|---|---|
| Mastery gate לפני מעבר נושא | `verification-before-claim.md` + סנסור ירוק לפני «הוטמע / סיימתי» |
| Question bank מכישלונות | `AGENTS.md` ANTI-PATTERN + `LEARNING-RECORDS.md` אחרי חזרה |
| L1 traces | `vfharness/state/*.json` · לוג כלים / תצפית אחרונה |
| L2 surface summaries | שורת יום ב־`owner-memory.md` · סיכום checkpoint |
| L3 synthesis | מדריך עמיד: `AGENTS.md` / פלייבוק פק / ADR |
| Recoverable sessions | resume מ־checkpoint + `skillstate` \(P,\Sigma,O\) |
| Shared books + private learning state | Core guides משותפים · instance / task state פרטי |
| Cost estimate before approve spine | לא ממציאים ₪; לפני עבודה יקרה — שער ראש צוות |

## טריגרים (נוסף ל־DAILY-RETRO)

| מתי | מה |
|---|---|
| טענת הצלחה בלי אימות | חסום — mastery gate = verification |
| אותה טעות פעמיים | Question-bank → ANTI-PATTERN או learning-record |
| סוף job ארוך | L1→L2: checkpoint + שורה ב־owner-memory אם עמיד |
| דפוס שחזר 3+ פעמים | L3: עדכון פלייבוק / חוקה (אדם מאשר נעילה/פתיחה) |

## שלוש שכבות זיכרון (קיצור)

כבר ממופה ב־`vfmem/MEMORY-UPDATE.md`. DeepTutor מחזק:

1. **L1** — מה קרה עכשיו (לא לשמור שיחה שלמה).
2. **L2** — מה חשוב למחר (שורה אחת / עובדה אחת).
3. **L3** — מה הופך לחוק משרד (רק אחרי חזרתיות / ADR).

Evidence ≠ Policy נשאר בעינו.

## ExamFul.ai (קישור נלווה)

אתר הכנה לבחינות AP/IB/A-level + AI tutor. **לא** מנדט סטודיו הדפסה.  
רישום: `LINKS.json` → `examful-ai` · `verdict: watch`.  
שימושי רק אם בעתיד קם **frontend instance** לחינוך (`expert-instance-onboard`) — לא מטמיעים צינור בחינות ב־VF desk.

## נעול

- התקנת DeepTutor / PocketBase / GraphRAG stack על HQ
- ClawHub `deeptutor skill install`
- אוטו־DM / בוסט / Print מ־HQ
- המצאת ציוני תלמיד / Insights למידה
- פק `vftutor` חדש — רק `office-learning` + packs קיימים
