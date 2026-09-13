# שער מצבי תוכן — Organic Growth

מושב: צמיחה. חוקה: `constitution/ORGANIC_GROWTH.md`.  
פריפלייט איכות נשאר `PREFLIGHT.md` (נכשל-סגור לפני שיבוץ).  
חוזה קופי ציבורי חובה: `../vfcopy/SOFT-TOOLS-CONTRACT.md`.  
השער הזה מוסיף **מדיניות + הרשאת פרסום** לפני מסירה ל־`vfigos`.

## מצבים

| מצב | מי מעביר | הערה |
|---|---|---|
| `draft` | מפעל תוכן | טיוטה פנימית |
| `quality_checked` | משרד אחרי copy chain + Rubric + מדיה | דורש `vfcopy_lint=pass` על גרסת הקופי הנוכחית + fact gate; בלי גלם = `blocked_no_media` |
| `policy_checked` | `vf_organic_growth.py policy` | אסור/מותר מ־ORGANIC_GROWTH |
| `pending_publish_authorization` | אחרי policy | דורש human approval נקודתי או standing authorization תקף |
| `pending_human_approval` | legacy alias | תאימות ל־queue/CLI הישן; מפורש כ־`pending_publish_authorization` |
| `approved_for_manual_posting` | אדם: אישור נקודתי | תאימות legacy; לא טענת פרסום |
| `authorized_for_tool_publish` | instance standing authorization | רק תוכן שגרתי שעבר SOFT-TOOLS-CONTRACT + exact-final PREFLIGHT + Visual Finishing/Product Truth + rights + Visual OS QA |
| `rejected` | אדם: דחייה | נשאר במשרד |
| `edit` | אדם או QA | חוזר ל־draft; שינוי קופי מבטל copy lint קודם |
| `published_verified` | `vfigos` אחרי tool receipt + verification evidence | לא מסמנים בלי ראיה |
| `posted_manually` | אדם במסלול legacy | רק אחרי העלאה ידנית אמיתית עם `human_marked=true` + `marked_by` |
| `performance_imported` | סנאפשוט / CSV | חסר = אין ספירה |
| `attributed` | ייחוס הסתברותי | לא «וודאי» |
| `learned` | רטרו / brief מחר | בלי בושה לבעלים |
| `blocked_no_media` | מפעל | אין Reel מומצא; צור shotRequest מדויק |
| `blocked_policy` | policy | נכשל-סגור |
| `human_required` | משרד | רק חסר פיזי/זכויות/כסף/WhatsApp/Print/חסם קשיח |

## הרשאה

ברירת המחדל הכללית נשארת human approval. Instance יכול להפעיל:

`creativeAutonomy.publish.standingAuthorization=true`

במצב זה, `pending_publish_authorization` יכול לעבור ל־`authorized_for_tool_publish` ללא אישור לכל נכס, **רק** אם:

1. הקופי הסופי עבר `packages/vfcopy/SOFT-TOOLS-CONTRACT.md`: reader-first + Voice + velvet-hebrew-copy + Humanizer/AI-tells + `check-vfcopy.py lint` על הטקסט הסופי + fact gate, ויש digest/version תואם.
2. `VISUAL-OS.md` brandScore >=80.
3. `CONTENT-RUBRIC >=20/25`.
4. policy pass + written PREFLIGHT על אותה גרסת טקסט/ויזואל.
5. ה־PREFLIGHT של ה־exact-final artifact מציג `publish_gate: PASS` ולא רק marker כללי של “עבור”.
6. Visual Finishing Protocol עבר על התוצר המדויק: `photo_retouch -> brand_content_styling -> text_layout_qa -> final_visual_qa`, עם evidence ב־Creative Manifest. שלב שאינו רלוונטי מסומן `N/A` מפורש, לא חסר.
7. למוצר פיזי אמיתי Product Truth עבר fail-closed: `product_truth_gate: PASS`, `subject_identity_integrity: PASS`, `synthetic_subject_change: NONE`, `source_subject_match: PASS`. הכלל: **Retouch the photo, not the product.**
8. אם יש טקסט ויזואלי: `readability: PASS`, `contrast: PASS`, safe zones/RTL/mobile preview עברו, וה־visual-copy gate תואם לגרסת הטקסט הסופית.
9. rights/privacy ברורים.
10. אין ₪/Boost/Ads/customer WhatsApp/Print או claim לא מאומת.
11. קיים publish tool אמיתי.

חסר evidence של אחד מהשערים = לא `authorized_for_tool_publish`. כשל איכות שגרתי חוזר אוטונומית ל־targeted repair ולבדיקה מחדש; הוא אינו אישור לעקוף את השער ואינו סיבה להסלים לבעלים.

## מעברים אסורים

- `draft` ישירות ל־publish.
- `draft`/`quality_checked` בלי copy lint אמיתי על ה־candidate הנוכחי.
- `authorized_for_tool_publish` כאשר ה־exact-final PREFLIGHT חסר `publish_gate: PASS` או Product Truth רלוונטי לא הוכח.
- שימוש ב־Brand Guardian, VOICE, Rubric או CI/eval כהוכחה חלופית לכך שהקופי הספציפי עבר lint.
- שימוש ב־edit URL / brief / rough preview כהוכחה חלופית ל־QA של ה־exact-final render.
- publish claim בלי tool receipt + verification evidence.
- standing authorization על כסף, Boost/Ads, customer WhatsApp, Print from HQ, auto-DM, user tag בלי opt-in או זכויות לא ברורות.

## invalidation

כל שינוי מהותי בקופי אחרי lint מבטל את `vfcopy_lint=pass`. שינוי מהותי בוויזואל, בטקסט שעל הוויזואל, במוצר, ב־crop, בתאורה, ברקע או באודיו אחרי finishing/Brand Guardian/Rubric/PREFLIGHT מבטל את ה־PASS הרלוונטי ומחייב בדיקה מחדש על ה־exact-final artifact.

## פעולות בעלים

כאשר אין standing authorization או שיש `human_required`: **אישור** · **עריכה** · **דחייה**.  
כשלי Hook/cover/crop/caption/contrast/readability/retouch/QA רגילים אינם פעולת בעלים — מתקנים אוטונומית.
