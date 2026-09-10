# vfcopy — שולחן קופי

מושב: סטודיו (+ מגיש לצמיחה). לא סוכן חדש.

עבודה: שיעורי בית, טיוטה, לינט.  
רף סוכנות: עברית חזקה, מדוברת, בלי מילוי. הקורא מרגיש משרד יקר — לא חצי-טיוטה.  

**חוזה חובה לכל קופי ציבורי:** `SOFT-TOOLS-CONTRACT.md`. הוא גובר על קיצורי דרך מקומיים ומחייב את כל השרשרת על גרסת הטקסט הסופית.  
**קול פיד (חוק):** `VOICE.md` — תהליך-קצר או סיפור-מוצר; מחקר: `VOICE-RESEARCH.md`.  
**שכבת עברית:** `skills/velvet-hebrew-copy/` — סמכות סגנון + pipeline + מבחן מאפייה + `needs_input`.  
קורפוס קול: `voice/approved/` בלבד (לא `voice/generated/`).  
תבניות פרומפט משרד: `hq/templates/` (מתודולוגיה מ־prompts.chat; לא ייבוא CSV).  
לפני טיוטה: `hq/reader-first-he.md` (ai-copywriter — קורא/תחושה/סיפור, בלי skill נפרד).  
כלי marketing soft skills לקופי שיווקי: `vfmskill` — `copywriting` + `copy-editing` + `marketing-psychology`; עובדים בתוך `SOFT-TOOLS-CONTRACT.md`, לא כאלטרנטיבה אליו.  
לינט anti-AI בעברית: `hq/ai-tells-he.md` + `python3 scripts/check-vfcopy.py lint` על **הטקסט הסופי בפועל** עם context מאומת (מ־write-better + Humanizer + velvet-hebrew-copy).  
Evals: `python3 scripts/check-vfcopy.py eval` — בודקים את המנוע, לא מוכיחים שקופי מסוים עבר.  

סדר חובה בקופי ציבורי: verified context → reader-first → VOICE/VOICE-CHART/approved corpus → vfmskill writing aids כשיווקי → template → velvet-hebrew-copy → ai-tells/Humanizer → actual-copy lint → factual gate → visual TEXT_WINS/NO_TEXT אם רלוונטי → CONTENT-RUBRIC → PREFLIGHT.  
שינוי קופי אחרי lint מבטל את ה־pass. שינוי מהותי אחרי Rubric/PREFLIGHT מחייב גם אותם מחדש.  

מגישים ל־`#vfsales` ו־`#vfgrowth`. HQ שולח דרך כלים רק לאחר gates הקנוניים (`constitution/SEND.md`).  
לוח קבוע: `vfgrowth/CALENDAR.md`. G003 נעול ב־`G003.md`. G004 מחזיק-קטלבל ב־`G004.md` (סיפור-מוצר). סטוריז חי: `G004-STORIES-FIX.md` + `vfgrowth/STORIES.md`. תבנית: `hq/templates/ig-stories.md`. CTA תמיד לפי `constitution/PUBLIC_CTA.md`, לא לפי טקסט legacy בתבנית/דוגמה. ריל אורגני: `hq/templates/organic-reel.md`. בלי Canva/vfcovers = לא משבצים. רואים `hq/PLAYBOOK.md`.
