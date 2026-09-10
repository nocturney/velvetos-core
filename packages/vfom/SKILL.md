# vfom — Velvet Visual Foundry על צינור התוכן הקיים

מושב: צמיחה. לא סטודיו וידאו שני ולא orchestrator שני.

דפוסי OpenMontage על הפקים שכבר רצים: `vfgrowth`, `vfcopy`, `vfcovers`, `vfcanva`, `vfigos`, `vfmedia`, `vfinsights`. אין Remotion runtime נוסף. אין Veo/Kling מ־HQ בלי שער spend מתאים.

## Visual Foundry

ברירת העבודה ל־Velvet Factory כאשר ה־instance מפעיל `creativeAutonomy`:

- `FOUNDRY.json` — machine-readable policy: layers, specialists, state machine, truth, variants, evaluation, novelty, learning, budget and human surface.
- `CONTENT-CONTRACT.schema.json` — חוזה objective + Claim Provenance + synthetic policy + Subject Pack + success thresholds לכל content job.
- `CREATIVE-MANIFEST.schema.json` — coordination artifact יחיד לכל content job: concept, hooks, shots, EDL, overlays, cover, QA, feed and derivative refs. אינו state machine/Media Vault/Claim authority נוסף.
- `VISUAL-DNA.json` — projection machine-readable של חוקי המותג; `VISUAL-OS.md` נשאר authority.
- `CREATIVE-AUTOPILOT.md` — orchestration + Exception Queue + Human Intervention Policy.
- `VISUAL-OS.md` — Visual Constitution + proof-first + first frame + cover + QA + Subject Lock + fatigue guard.
- `EDIT-DIRECTOR.md` — EDL אופרטיבי + shot-gap handling.
- `MOTION-PRESETS.md` — motion vocabulary מצומצם וקנוני.
- `FORMAT-GENOMES.md` — מבני סיפור חוזרים; mechanics ולא זהות מועתקת.
- `experts/MEDIA-DIRECTOR.md` — Creative/Edit/Publishing Director מאוחד.

הפעלה ישירה ב־Cursor: `.cursor/skills/vf-content-sprint/SKILL.md`.

## Specialists

`vf-content-sprint` הוא ה־orchestrator היחיד ומאציל עבודה לשלושה specialists, לא לשלושה runtimes:

- `.cursor/skills/velvet-creative-director/SKILL.md` — concept + First-Frame Hunter + shot list/gaps + timeline + overlay + cover direction.
- `.cursor/skills/velvet-media-librarian/SKILL.md` — canonical Media Vault intake/search/tagging/rights/truth; אין קטלוג שני.
- `.cursor/skills/velvet-brand-guardian/SKILL.md` — Brand Compliance Visual QA + originality/fatigue + feed continuity + targeted repair.

## Architecture law

Creative intelligence יכולה לחשוב: Creative Director, Brand Guardian, Media Librarian, Storyboarder, Evaluation/Repair Planner, Experiment Director.

Orchestration ו־deterministic services נשארים במערכת הקיימת: state/control plane, Media Vault, validation, composition/render, Drive, publish verification, Insights ingest. אל תהפוך כל שירות ל־Agent ואל תיצור queue/catalog/memory DB מקביל.

## Truth law

Asset Truth חי באותה שורת `vfmedia/catalog.json` דרך `catalog.schema.json`. חסר `truth` = `unverified` לצורכי טענה ציבורית. Asset Truth אינו Claim Truth: טענה עובדתית נדרשת ל־evidence-linked Content Contract. `synthetic`/`illustrative_ai` אינם הוכחה למדידה, עומס, כשל, הצלחה או גאומטריית מוצר.

## Variant/quality law

עבוד progressive: הרבה concepts זולים → פחות storyboards/rough cuts → עד שני final renders כברירת מחדל. Evaluation מפריד deterministic/perceptual/reference/artifact checks. כשל איכות רגיל מתוקן אוטונומית ב־bounded repair loop; הוא לא owner gate.

## Memory law

Novelty/fatigue ו־performance learning משתמשים ב־office-learning + `vfinsights`; אין Creative Memory DB נוסף. recipe נשמר רק לצד evidence אמיתי, ו־success pattern נשאר preference עם exploration budget — לא חוק שכפול.

## Crews existing

`reference-plan` · `clip-factory` · `hybrid-reel` · `scene-gate` · `self-review` נשארים patterns פנימיים שה־Foundry מפעיל לפי צורך. אין צורך שהבעלים יבחר crew או שלב.

## Human surface

פנייה לבעלים רק על צילום/סטייג'ינג פיזי, זכויות/פרטיות, unsupported high-stakes claim שלא ניתן להסיר/למסגר מחדש, כסף/Boost, customer WhatsApp, Print, פעולה הרסנית או חסם קשיח אחרי failover/repair limit. LOW-risk routine organic Instagram יכול להתקדם לפי standing authorization של ה־instance אחרי כל gates ועם receipt/live verification אמיתיים.
