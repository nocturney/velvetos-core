# Best Skills · 2026-09-12

מקור: https://github.com/LinklyAI/best-skills  
dataDate: **2026-09-11** — זה ה-dataset החדש ביותר שקיים בזמן הריצה; `data/2026-09-12` לא היה קיים.  
מושב: מחקר/אורקסטרציה · Asia/Jerusalem

## קבצים שנקראו

- https://github.com/LinklyAI/best-skills/blob/main/data/2026-09-11/rankings/best-100.csv
- https://github.com/LinklyAI/best-skills/blob/main/data/2026-09-11/rankings/trending-7d.csv
- https://github.com/LinklyAI/best-skills/blob/main/data/2026-09-11/rankings/social-buzz.csv
- https://github.com/LinklyAI/best-skills/blob/main/data/2026-09-11/rankings/top-repos.csv

## Movers רלוונטיים ל-VF

| אות | מצב | פעולה |
|---|---|---|
| `find-skills` #1 best-100 | כבר מכוסה ב-`vfresearch/BEST-SKILLS.md` | אין כפילות |
| `grill-me` #4 best-100 | כבר מוטמע ב-`vfconvert/hq/GRILL.md` | אין שינוי |
| `improve-codebase-architecture` #26 best-100 | watch קיים תחת `mattpocock-skills` | ממשיך watch; לא pack חדש |
| `hyperframes` family #12/#17/#19+ trending | רלוונטי למדיה, אבל כבר נמצא במסלול media/video הקיים | אין runtime/pack נוסף במעבר הזה |
| Google Agents CLI ~+230% trending | vendor CLI / runtime מקביל | דולג לפי נעילות |
| `earthtojake/text-to-cad` #64 top-repos | חדש ורלוונטי ל-CAD/DfAM | watch בלבד; לבדוק pattern אם יתגלה פער ב-`vfprod` |
| `archify` #21 top-repos | watch קיים; DIAGRAM-MAKER כבר מכסה צורך | אין כפילות |
| `self-improving` #1 social-buzz | runtime עצמי מקביל | דולג; office-learning/vfops כבר מכסים reflection |

## בדיקת `earthtojake/text-to-cad`

מקורות:
- https://github.com/earthtojake/text-to-cad/blob/main/skills/cad/SKILL.md
- https://github.com/earthtojake/text-to-cad/blob/main/skills/dfam-check/SKILL.md

הדפוס השימושי: CAD כ-source code עם STEP/STL/3MF, inspection/snapshot/validation ו-DfAM check לפני slicing. זה יכול להיות שימושי בעתיד כבדיקת mesh/printability, אבל אין כרגע הוכחה שחסר לנו gate כזה שמצדיק dependency/runtime נוסף.

**החלטה:** watch. אם יתועד פער אמיתי ב-`vfprod`, מטמיעים את עקרון ה-validation בתוך הפק הקיים; לא מתקינים מערכת CAD מקבילה ולא מקצרים `vlicense`/slice/Print gates.

## מה הוטמע

**אין embed חדש במעבר הזה.** הדירוג לא חשף pattern חדש שמצדיק שינוי קנוני בלי ליצור כפילות.

## Watchlist addition

- `earthtojake/text-to-cad` — source-controlled CAD + DfAM validation pattern; watch only.

## מה דולג

| מה | למה |
|---|---|
| Google Agents CLI | vendor CLI/runtime מקביל; לא נחוץ ל-VF |
| self-improving / proactive runtimes | runtime שני; office-learning/vfops קיימים |
| reddit/twitter automation | growth/social automation מחוץ למנדט |
| AI-video/image skill packs | לא מחליפים את Visual OS / media authority בגלל leaderboard |

## Timer

`standingForever=true` ו-lastPass הקודם היה 2026-09-10, לכן המעבר היה due ובוצע בתוך Research Seat.  
`timer: UNPROVEN` — `cursor-subscriptions/list_subscriptions` אינו כלי זמין בריצה הנוכחית, ולכן לא נטען `timer: ok` ולא `timer: renewed`. לא נוצרה automation נפרדת, בהתאם להוראת הבעלים לשלב את refresh במחקר היומי.

## בלוק 05

`best-skills — מעבר 48h בוצע; אין embed חדש. earthtojake/text-to-cad נכנס ל-watch בלבד; legacy timer verification חסום בכלי הנוכחי.`
