# סקירת velvet-hebrew-copy · 2026-09-09

מושב: סטודיו / `@content-creator` · Asia/Jerusalem  
רישום: `packages/vfresearch/LINKS.json`  
מקורות:  
- https://github.com/social-media-skills/skills (MIT)  
- https://github.com/thekozugroup/humanizer (MIT)  
סטודיו: Velvet Factory · שדרות · איסוף · IG `@velvets_cloud`  
לא פק חדש. לא vendoring. לא `npx skills`.

## מה הוטמע

| מקור | רעיון | לאן |
|---|---|---|
| brand-profile / voice-builder | foundation לפני כתיבה; קול מדגימות אמיתיות | `VOICE*` + `voice/approved/` vs `generated/` |
| caption-writer / hook-writer | שורה ראשונה; לא לתאר תמונה; CTA אחד | skill + templates + lint |
| writing-style-and-tone | cluster of tells; substance; no invented anecdotes | `ai-tells-he.md` + מבחן מאפייה |
| carousel-writer / reels-script | כיסוי=הוק; muted-first | PIPELINE + הערות פורמט |
| instagram-seo | SEO כהשבחה בלבד | SKILL §SEO |
| humanizer | AI tells + rewrite ממוקד | `lint_he.py` + `--rewrite` |

## מה לא

- Rust detector / marketplace install  
- שינוי bio / captions חיים / Meta config  
- PR #141/#142 (Instagram MCP) — לא ננגעו  

## בדיקות

`python3 scripts/check-vfcopy.py` (behavioral + evals + live lint)  
`python3 scripts/check-all.py` אחרי מיזוג הקבצים.
