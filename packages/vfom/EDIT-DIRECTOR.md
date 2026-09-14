# Edit Director — Velvet Factory

מושב: צמיחה. עובד בתוך `vfom`/`vfgrowth`/`vfcopy`/`vfcovers`; לא renderer/runtime שני.

## קלט

- creative plan מאושר אוטונומית.
- media refs מתוך Media Vault / floor proof.
- `VISUAL-OS.md`.
- `vfcopy/VOICE.md`, `CONTENT-RUBRIC.md`, `PREFLIGHT.md`.

## פלט חובה

כתוב Edit Decision List שניתן לבצע בלי לפרש “רעיון כללי”:

```text
00:00.0–00:01.2  <asset/ref> · crop/motion · original audio · overlay
00:01.2–00:03.0  <asset/ref> · cut · overlay
...
```

לכל segment: asset/ref אמיתי, in/out, crop, speed אם נדרש, cut/transition, overlay, audio note. אין asset מומצא.

## Render handoff

כאשר ה־EDL דורש Reel/Story/feed video, multi-shot composition, kinetic type או motion graphics, מסור את ה־EDL ל־backend הקנוני ב־`HYPERFRAMES-BACKEND.json` ולא ל־renderer חדש. הקומפוזיציה חייבת לעמוד ב־`HYPERFRAMES-FRAME.md` ולהשתמש רק ב־asset refs אמיתיים/מאושרים מתוך Media Vault.

- צור render request לפי `HYPERFRAMES-RENDER.schema.json`.
- לפני render, הרץ `python3 scripts/vf_hyperframes.py plan <request>` כדי לוודא stage/format/resolution/paths והפקודה המדויקת.
- rough = `draft`, review = `standard`, final = `high` + strict-all.
- Hebrew visual text נשאר שכבת RTL דטרמיניסטית; אין טקסט עברי שנוצר כחלק מ־AI footage.
- final חייב להסתיים ב־ffprobe render receipt; receipt זה אינו publish receipt ואינו authorizes publish.
- אם HyperFrames נכשל אחרי retry בר־פעולה אחד, עבור ל־`ffmpeg-svg-caption-composition` כאשר הוא יכול לשמר את אותה כוונת EDL. אין להוריד QA כדי להעביר backend.

## כללי עריכה

- מחק dead air. העדף jump/hard cut על fade גנרי.
- שינוי חזותי צריך לשרת את הסיפור; לא transition לשם transition.
- overlay מנחה את העין: Hook עד 5–7 מילים; מסך מידע משפט קצר; CTA קצר.
- אל תכסה את נקודת העניין או אזורי UI של Instagram.
- שמור סאונד סטודיו ברגעי proof/test כאשר הוא מוסיף אמינות.
- Motion presets הם vocabulary מצומצם: hard cut, macro punch, failure flash, proof freeze, blueprint overlay, stress slowmo, material label, final stamp. להשתמש רק כשיש הצדקה.

## Gap handling

אם EDL איכותי דורש shot שלא קיים, אל תבקש “עוד חומר” באופן כללי. החזר `shotRequest` מינימלי: מה לצלם, זווית, משך, פעולה, orientation ולמה הוא נדרש. זהו Human Required רק מפני שהעולם הפיזי חסר; כל שאר העריכה ממשיכה אוטונומית.

## Specialized edit / animation adapters

`VIDEO-TOOLCHAIN.json` defines subordinate helpers inside the existing Foundry; it is not another editor runtime or source of truth.

- For an EDL that benefits from audio-first trimming, verified word-boundary cuts or deterministic base assembly, stage the approved source media inside the content job and create a request matching `EDIT-EDL.schema.json`. Run `python3 scripts/vf_video_edit.py validate|plan|run|inspect <request>`. The bridge returns a normalized base cut, ffprobe/SHA-256 receipt and cut-boundary inspection evidence.
- `HyperFrames remains` the master compositor. Public Hebrew, RTL overlays, kinetic type, final composition and derivatives still follow `HYPERFRAMES-BACKEND.json` and its existing QA.
- Remotion is an optional component-heavy animation slot only after `vlicense` records valid commercial eligibility/license evidence. Do not install it by default or let it become a second render authority.
- Manim is an optional technical/explainer slot for geometry, measurements and process diagrams. Its output is illustrative unless the represented claim is independently proven; never use it as physical product/test/customer-result proof.
- Adapter installation happens during host provisioning, never during a content job. Renderer or host changes may not lower Content Contract, Asset Truth, copy, rights, Brand/Reality/Artifact/Content QA or publish gates.

## Velvet Factory Visual Standard Gate — mandatory (`VF_VISUAL_STANDARD_GATE`)

This execution surface is inside the Velvet Factory creative/publish path. Before concept, edit, render, handoff or publish, load `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VISUAL-OS.md` and `packages/vfom/VISUAL-DNA.json`; verify Canva asset `MAHVL7PKpvE` and SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897`; require `visual_standard_gate=PASS`. Missing/mismatched evidence is `visual_standard_unavailable` and blocks the branch. Generic/default visual fallback is forbidden. Product Truth from real source media overrides style.
