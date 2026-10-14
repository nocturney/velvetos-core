# Awesome AI Motion → Velvet Factory Reels · שילוב מקומי

**סטטוס:** 3 מסלולי Motion זמינים כתבניות מועמד ב־Core, לפני רינדור, ללא פרסום וללא התקנת מנוע נוסף. **מקור:** [gongnyang/awesome-ai-motion](https://github.com/gongnyang/awesome-ai-motion), commit `1e3c249073c61b42ceb556d7800f628d565d9312` (2026-09-30). הסקירה נערכה 2026-10-14.

## מיקום מדויק במסלול הקיים

`Asset Truth + Claim Provenance → Content Contract → Creative Director / EDL → Motion Library selector (אופציונלי) → HyperFrames rough render → Brand/Copy/RTL/Audio/Product Truth QA → HyperFrames final + ffprobe receipt → existing EDIT-GATE/PREFLIGHT → current instagram.publish policy → vfigos live verification`.

השכבה אינה מחליפה את `vf_hyperframes.py`, DaVinci Resolve, Topaz, OpenPost, Media Vault, ה־Creative Manifest או ה־publisher. אין API נוסף, אין מנוי חדש, אין תהליך startup, אין מצב אישור עצמאי. ברירת מחדל: להמשיך Hard Cut וריאליזם מוצר, ולהוסיף תנועה רק אם משפרת את הסיפור.

## בחירת מסלול

| `motionStyle` | מתי | תנועה | תנאי קדם |
|---|---|---|---|
| `product_reveal` | השקת/הצגת פריט אמיתי | Mask Reveal + sheen על אותיות בלבד | צילום מוצר אמיתי, ref מאומת, copy+audio מאושרים |
| `before_after` | השוואת שלבי ייצור/גימור *אמיתיים* | Split Compare + title | שני refs שונים ומאומתים של אותו פריט, יישור וצילום תואם, ראיות להשוואה, copy+audio |
| `shorts_hook` | פתיח Reel שלוש פעימות | kinetic beats + Mask Reveal | שלוש מילים/ביטויים קצרים מאושרים, פריט מצולם בפריים הראשון, audio |

המתכונים שהוטמעו הם **התאמת דפוסים**. לא שולבו קוד, תמונות, פונטים, MP4 או ספריות חיצוניים מתוך המאגר. ה־GSAP הקיים הוא הפלטפורמה. הבסיס ברישיון MIT; רכיבי צד שלישי במאגר המקורי עשויים להיות ברישיונות אחרים, ולכן **אסור לייבא אותם ללא בדיקת ATTRIBUTIONS ורישיון פרטני**.

## הרצה, ללא עקיפת פייפליין

1. סטודיו/צמיחה מסיימים את EDL והבריף עם ה־Content Contract, vfcopy, רפרנסים מאומתים מ־Media Vault וסאונד מאושר. לשלב ראשוני, חייבים media source עם `truth.truthLevel=verified_real|derived_real`. אסור להפוך תמונת הדגמה לנכס מכירה.
2. בתוך **אותו projectDir של HyperFrames**, יוצרים `jobs/<job-id>/motion-variables.json` עם **כל** שדות `MOTION-STORY-VARIABLES.schema.json` כמחרוזות. `variablesStatus=ready` רק אחרי שיש נתיבים ו־refs אמיתיים. כל נתיבי media הם יחסיים לשורש הפרויקט. אין רנדר אוטומטי עבור `needs_input`.
3. יוצרים בקשת rough מתוך selector, ללא שליחת מידע לרשת:

```bash
python3 scripts/vf_motion_plan.py plan jobs/<job-id>/motion-variables.json \
  --project-dir . --job-id <job-id> --output jobs/<job-id>/rough-motion.mp4 \
  --request-out jobs/<job-id>/rough-motion-request.json
python3 scripts/vf_hyperframes.py plan jobs/<job-id>/rough-motion-request.json
```

4. רק Edge/Office host שנמצא ב־RENDER-HOSTS ועבר `doctor` מרנדר עם `python3 scripts/vf_hyperframes.py run <request>`. תוצאת rough היא דגימה פנימית לבדיקה — לא master מאושר.
5. למעבר ל־final חייבים את **כל** השערים הקיימים: בדיקת Rights, ביטחון זהות/גאומטריית המוצר מול מקור, יישור והשוואת before/after, RTL עם Rubik, contrast + Instagram safe zones, copy lint, audio loudness/rights, השוואת רפרנס, בדיקת נגזרת יצירתית, FINAL quality+strict-all, ffprobe receipt ושערי פרסום. כל שינוי בטקסט מחייב lint חדש. `publicationAuthorized=false` בכל תוצר של selector.
6. רק אחרי אישור בהתאם ל־`instagram.publish` ממשיכים ל־OpenPost/vfigos; לא נוצרו פעולות publish, DM או spend בעקבות הטמעת ספריית התנועה.

## QA פנימי

```bash
python3 scripts/vf_motion_plan.py --self-test
python3 scripts/check-video-toolchain.py
python3 scripts/check-reel-templates.py
python3 scripts/check-reel-route-sync.py
python3 scripts/vf_hyperframes.py doctor
```

בדיקת smoke אמיתית של התבנית נדרשת עם *נכסי בדיקה מבודדים* והרצת HyperFrames על המארח הנכון; בדיקות מבניות ואמת־נתיבים לא מהוות אישור עיצוב או פרסום. אין ליצור או לעקוף פרסום בזמן הבדיקה. תיעוד מקור: `MOTION-LIBRARY.json`. `FOUNDRY.json`, `REEL-ROUTE-CONTRACT.json` וה־instance business facts נשארים סמכותיים וללא מסלול מקביל.
