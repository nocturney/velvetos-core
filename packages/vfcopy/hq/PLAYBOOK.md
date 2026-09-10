# לינט וכתיבה — Visible Text Playbook

Authority: `constitution/VISIBLE_TEXT.md` + `packages/vfcopy/SOFT-TOOLS-CONTRACT.md`.

לפני כל prose/microcopy שנכתב ב־AI ואדם עתיד לקרוא: `hq/reader-first-he.md`.  
שכבת עברית: `skills/velvet-hebrew-copy/SKILL.md` + `PIPELINE.md`.  
Humanizer/anti-AI: `hq/ai-tells-he.md`.  
Executable candidate gate: `python3 scripts/vf_visible_text.py --surface <surface> ...`.  
Public legacy lint: `python3 scripts/check-vfcopy.py lint [--rewrite]`.  
Evals: `python3 scripts/check-vfcopy.py eval` — בודקים את המנוע, לא מוכיחים שטקסט מסוים עבר.

## קודם בוחרים surface

| Surface | מי קורא | מה מתווסף |
|---|---|---|
| `public-social` | קהל Instagram | VOICE + VOICE-CHART + PUBLIC_CTA + vfgrowth; vfmskill aids כששיווקי |
| `visual-microcopy` | קהל על cover/overlay/slide | public context + 3–5 candidates + `NO_TEXT` + Creative Director/Brand Guardian |
| `customer-message` | לקוח בפרטי | vfconvert; vfsales/vfcost/vlicense לפי הצורך; private CTA מהשיחה |
| `sales-proposal` | ליד/לקוח | vfsales + verified price/facts + vfmskill copywriting/copy-editing כשישים |
| `owner-brief` | כריסטיאן | office truth + reader-first; preserve IDs/status/numbers; בלי public CTA |
| `human-document` | קורא מסמך/HTML/מצגת | domain pack + vfcopy; format QA אחר כך |
| `ui-microcopy` | משתמש בממשק | reader-first + literal technical labels |
| `desk` | אדם במשרד | domain context הרלוונטי |

## אנטומיית פרומפט / טיוטה

לפני טיוטה בנה מהרכיבים, לא מ־“act as X” גנרי:

| רכיב | במשרד |
|---|---|
| **תפקיד** | לפי surface/domain, לא פרסונה שיווקית מומצאת |
| **הקשר** | facts מהשיחה/רצפה/Calendar/Drive/order/slicer; חסר נשאר חסר |
| **קורא** | הרגע/הצורך מ־`reader-first-he.md` |
| **משימה** | פעולה אחת: תשובה / מעקב / החלטה / כיתוב / הסבר |
| **אילוצים** | domain truth + constitution + surface rules |
| **פורמט** | chat/email/caption/brief/document/UI/visual microcopy |
| **דוגמה** | approved example מתאים למשטח; לא טיוטת AI לא מאושרת |

תבניות מוכנות: `hq/templates/README.md`. מקור מתודולוגיה: `packages/vfresearch/sources/2026-08-31-prompts-chat-embed.md`.

## שרשרת חובה

`verified context → surface/intent → reader-first → relevant domain/writing tools → velvet-hebrew-copy → Humanizer/AI-tells → surface-aware lint על הטקסט המדויק → factual/constraint gate → surface QA → visible_text_gate`

- marketing/public/sales: `vfmskill` `copywriting` / `copy-editing` / `marketing-psychology` כשהם רלוונטיים; `N/A` צריך להיות אמיתי ולא קיצור דרך.
- visual: `NO_TEXT` baseline חובה.
- owner: אין שיווקיות/CTA ציבורי; blocker/ID/status נשארים מדויקים.
- customer: אין public Instagram CTA בכוח; מחיר/מועד רק ממקור.

## בודקים

- האם השורה הראשונה נותנת לקורא את הדבר שהוא צריך עכשיו?
- האם כל משפט מרוויח מקום?
- האם הטון טבעי לאותו surface, לא “ChatGPT Hebrew”?
- האם כל עובדה, ₪, זמן, סטטוס, לקוח או claim מגיעים ממקור?
- האם Humanizer שינה רק סגנון ולא אמת?
- האם `vf_visible_text.py` רץ על **הטקסט הסופי** עם surface נכון?
- האם יש `visible_text_gate: PASS` רק אחרי ביצוע אמיתי של השלבים?
- אם זה visual copy: האם text באמת מנצח `NO_TEXT`?
- אם זה public: CTA לפי `PUBLIC_CTA.md`, עד 5 hashtags, no WhatsApp public.
- אם זה owner: preserve literal IDs/hashes/status/numbers; אין “הכול תקין” כשהחיישן אדום.
- אם זה customer/sales: thread/card ראשון; verified amount לפני price; CTA/ערוץ מתוך השיחה.

## Fail closed

- עובדה חסרה → `needs_input` / `חסר`, לא rewrite יצירתי.
- lint pass לבדו ≠ Visible Text PASS.
- CI/eval pass ≠ candidate receipt.
- טקסט שנכתב מחוץ ל־vfcopy הוא raw candidate עד שעבר gate.
- rewrite אחרי gate מבטל hash/PASS; אם יש render/preflight תלוי — גם הוא invalidated.
- approved static copy ניתן למחזור רק כשהטקסט זהה והעובדות עדיין תקפות.

## Public/social notes

קול public נמצא ב־`VOICE.md` + `VOICE-CHART.md`; `PUBLIC_CTA.md` קובע CTA. האשטאגים עד 5. visual copy עובר NO_TEXT + creative QA. `#vfigos` מטפל review/send אחרי gates.

## Customer/owner notes

Customer private: `vfconvert`/`vfsales`/`vfcost`/`vlicense` לפי הצורך; WhatsApp send נשאר אדם. Gmail יכול להישלח מ־HQ אחרי gate.  
Owner brief: `vfops`/מקורות אמת → owner-brief gate → `vfbriefux` render → Gmail. אין public CTA ואין שינוי נתונים כדי “לזרום”.
