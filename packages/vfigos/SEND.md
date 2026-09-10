# שליחת אינסטגרם מ־HQ

מושב: **צמיחה**. לא מחכים לגרוק. לא מחכים לכריסטיאן.

פרוטוקול מלא: `constitution/SEND.md`.  
MCP קנוני: [`CONNECT-IG.md`](CONNECT-IG.md) (`adelaidasofia/instagram-mcp`).  
Transport קנוני למדיה פרטית: [`PUBLISH-BRIDGE.md`](PUBLISH-BRIDGE.md) + [`PUBLISH-BRIDGE.json`](PUBLISH-BRIDGE.json).

## סדר

1. כיתוב סופי ב־`vfcopy` — **PUBLIC_CURRENT_CTA** = הודעת Instagram / «הזמנות» / איסוף שדרות (`constitution/PUBLIC_CTA.md`). לא «שלחו DM». לא וואטסאפ בכיתוב. מקסימום 5 האשטגים. לא אוטו־DM. לא ₪ מומצא.
2. מדיה: גרסה מאושרת במאגר (`docs/MEDIA-VAULT.md` · `packages/vfmedia/catalog.json`) עם `versionApproval` לגרסה המדויקת; תיקיית מאושר לבד אינה הוכחה. יצירה/עריכה ב־Canva או `studio/render.py` חוזרת למסלול נגזרת→אישור.
3. **QA final render + PREFLIGHT v2** — לפני transport/publish, בודקים את הייצוא הסופי עצמו. לסטורי: Brand Guardian + copy QA + readability + contrast = `PASS`; Rubric ≥20/25; `artifact_digest`; ו־`final_package_sha256` של חבילת הפריימים המדויקת. אין waiver ל״ניגודיות רכה״. שינוי ויזואל/קופי אחרי אישור מבטל את האישור.
4. **Publish Bridge** — כאשר הנגזרת אינה כבר ב־HTTPS ציבורי מתאים, מעבירים **רק את הנגזרת שאושרה לפרסום** דרך `PUBLISH-BRIDGE.md`: normalize → strip metadata → content hash → stage בענף `publish-bridge` → external fetch verify. אסור לשנות שיתוף של המקור ב־Drive. `staged`/`fetch_verified` ≠ published.
5. **פריפלייט שליחה** — בדיקת transport בלבד מותרת לאבחון:
   ```bash
   python3 scripts/vf_send_preflight.py --gate instagram --transport-only
   ```
   אבל היא **לעולם אינה הרשאת publish**. לפני `publish_*` חובה:
   ```bash
   python3 scripts/vf_send_preflight.py --gate instagram \
     --content-id <GID> --format <story|reel|carousel|post> \
     --approval-ref packages/vfgrowth/preflight/<GID>.md \
     --package-sha256 <SHA256-OF-EXACT-FINAL-PACKAGE>
   ```
   רק exit `0` + `publication_quality.publishAuthorized=true` מאפשרים מעבר ל־apply. exit `1/2` = **לא מפרסמים**; מתקנים איכות או מבצעים failover transport לפי הסיבה.
6. **Instagram MCP מחובר** → HQ מפרסם לפי פורמט: תמונה `publish_image`; קרוסלה `publish_carousel`; ריל/וידאו `publish_reel`/`publish_video`; סטורי `publish_story`.
7. **אימות אחרי שליחה** — `list_media` / `get_media` מאשרים שהמדיה חיה. רק אז `#נשלח-מ-HQ` ו־`liveVerified`. success בלי אימות חי → `publish_pending_verification`.
8. **אין Publish MCP חי** → failover באותו תור: Drive create_file + Gmail עם אותה חבילה; `#ממתין-ל-כלי-IG` אם הפיד עצמו עוד לא עלה.
9. אסור לכתוב שעלה לפיד אם לא עלה. Calendar / upload / bridge staging / publishRequested ≠ live. אסור בוסט. אסור אוטו־DM.

## חוזה איכות → פרסום

`transport-ready` ≠ `creative-approved` ≠ `published_verified`.

האישור חייב להתייחס **לאותו hash** שמגיע ל־Publish Bridge/Instagram. אסור למחזר PREFLIGHT ישן אחרי שינוי תוצר או אחרי שינוי במדיניות האיכות. PREFLIGHT ללא `publish_gate_schema: 2` אינו מקור הרשאה לפרסום חדש.

## Publish Bridge — כללי בטיחות

- source of truth למדיה נשאר Drive/Media Vault; ה־bridge הוא transport בלבד ואינו קטלוג שני.
- `approved_for_public_release` הוא שער קשיח. upload או folder placement לא מספיקים.
- correlation בנתיב חייב להיות non-PII; לא שם לקוח.
- metadata ציבורי שומר hash של source reference, לא URL פרטי של Drive/Canva.
- cleanup יומי מסיר נכסים ישנים מראש הענף אחרי חלון retention; הוא **לא** secure erase מהיסטוריית Git.
- לכן בענף מותרת רק נגזרת שממילא מותר לפרסם לציבור.

## דפוס validate → transport → apply → verify

| שלב | כאן |
|---|---|
| validate | PREFLIGHT v2 + exact final-package hash + Brand/Copy/Readability/Contrast + rights/privacy |
| transport | Publish Bridge רק לנגזרת המאושרת; HTTPS fetch verified |
| apply | `publish_*` **או** Drive+Gmail באותו תור |
| verify | `list_media` / `get_media` · לא «פורסם» בלי ראיה |

## אסור

- לפרסם על בסיס `--transport-only`
- למחזר approval ישן שלא קשור ל־final package המדויק
- waiver לניגודיות/קריאות חלשות
- סרק / «תעלה ידנית» כברירת מחדל
- להפוך מקור/תיקיית Drive לציבוריים כדי לפתור transport
- לשים publish binaries על `main`
- להכניס ל־`publish-bridge` חומר שלא עבר `approved_for_public_release`
- להמציא Insights אחרי «שליחה»
- לטעון live מ־publish tool בלי verify
- Treg · אוטו־DM · `INSTAGRAM_MCP_DM_ENABLED`
