# ADAPTATION — מקורות חיצוניים → vfcopy native

לא vendoring. רעיונות בלבד, מותאמים לעברית ולחוקת Velvet Factory.  
רישיונות: שני המקורות **MIT** — attribution כאן + ב־`LINKS.json`.

## social-media-skills/skills (MIT · Frank Heijdenrijk)

מקור: https://github.com/social-media-skills/skills

| Skill חיצוני | מה לקחנו | לאן ב־VF | מה דילגנו |
|---|---|---|---|
| **brand-profile** | קראו foundation לפני כתיבה; guardrails; «מי אנחנו / מה לא» | `VOICE.md` + `VOICE-CHART.md` כבר ממלאים; skill מפנה אליהם | קובץ brand-profile.md נפרד / onboarding SaaS |
| **voice-builder** | קול מתוך דגימות אמיתיות בלבד; הפרדת samples איכותיים | `voice/approved/` vs `voice/generated/` | ניתוח 6 שכבות אוטומטי / ghostwriting scale |
| **caption-writer** | שורה ראשונה = כל המשחק; מטרה אחת; לא לתאר את מה שרואים בתמונה; CTA אחד | `SKILL.md` + templates + lint | פלטפורמות שאינן IG; LinkedIn long-form |
| **writing-style-and-tone** | STYLE: substance > detector chasing; burstiness; cluster of tells; לא ממציאים anecdotes | `ai-tells-he.md` + lint cluster + מבחן מאפייה | ציטוטי סטטיסטיקות 2026 כ־Insights; detector scores |
| **hook-writer** | הוק מהאמת של התוכן; לא overpromise; cutoff לפי פורמט | `VOICE.md` הוק · templates | תבניות viral-bait |
| **carousel-writer** | כיסוי = הוק+הבטחה; רעיון אחד לשקופית | PIPELINE + הערת carousel ב־SKILL | image-gen pack / LinkedIn PDF |
| **reels-script** | הוק ~3 שנ׳; muted-first; תהליך או סיפור | `organic-reel.md` + תהליך-קצר | Veo prompts / trending-audio attach מ־HQ |
| **instagram-seo** | SEO כהשבחה; 3–5 תגיות נושא; בלי stuffing | SKILL §SEO | שינוי bio/Name field; fabricated volume |

## thekozugroup/humanizer (MIT · thekozugroup)

מקור: https://github.com/thekozugroup/humanizer

| רעיון | הטמעה native |
|---|---|
| קטלוג AI tells (em dash, rule of three, negative parallelism, AI vocab, significance inflation) | הרחבת `hq/ai-tells-he.md` + דפוסים עבריים ב־lint |
| detect → rewrite ממוקד (לא loop) | `check-vfcopy.py lint --rewrite` — rewrite אחד לסגנון; factual → needs_input |
| burstiness / קצב משפטים | הנחיה ב־SKILL (משפטים קצרים כשמתאים; בלי פאנץ׳ מלאכותי) |
| Rust detector binary | **לא** — Python lint בלבד ב־HQ |

כבר היה אצלנו קו Humanizer מ־write-better + ai-copywriter (`hq/ai-tells-he.md`). השכבה הזו מחזקת ומחברת ל־skill + evals.

## עברית — מה ספציפי ל־VF

- ביטויי AI עבריים («אנו גאים להציג», «נרגשים לשתף», «כל פרט מספר סיפור»…).
- תחביר מתורגם מאנגלית («לקחנו את X לשלב הבא», «זה בדיוק מה שאנחנו אוהבים»).
- מבחן מאפייה (גנריות מול סטודיו שדרות).
- PUBLIC_CURRENT_CTA בעברית · איסוף שדרות · בלי משלוח ארצי · בלי ₪ מומצא.

## מה לא הוטמע (מכוון)

- `npx skills add` / Claude marketplace על Cloud Agent  
- ונדור מלא של הריפואים  
- detector score theater  
- שינוי bio / captions חיים / Meta config  
- auto-DM / boost  
