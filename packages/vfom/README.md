# vfom — OpenMontage desk

מפה של [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage) אל משרד Velvet Factory.

OpenMontage הוא סטודיו וידאו סוכני: 12 צינורות, 100+ כלים, שערי איכות. אצלנו **לא** מתקינים אותו. מטמיעים **דפוסי הפקה** על הפקים שכבר מכינים ריל מהמיטה.

## מה כן אצלנו

| דפוס מ-OpenMontage | פק | מה עושים |
|---|---|---|
| Clip Factory | `vfgrowth`, `vfprod` | טיימלאפס ארוך → כרטיסי קליפ מדורגים |
| Hybrid | `vfcanva`, `vfcovers` | גלם מהמיטה + שכבת Canva. הגלם ראשי |
| Cinematic / reference video | `vfgrowth`, `vfresearch` | ריל שאוהבים → מה נשמר / מה משתנה / מסלול כלים ישר |
| Backlot approval gate | `vfigos` | דף סצנות לאישור אדם לפני «מוכן ל-Grok» |
| Self-review / slideshow risk | `vfigos`, `vfcopy` | רשימת איכות לפני מסירה. אין שליחה |
| Instagram Reels 1080×1920 | `vfcanva` | כבר ב-`FORMATS.json` (`ig_reel_cover` / `ig_story`) |

## מה לא

ראה [`LOCK.md`](LOCK.md): מנוע Remotion/HyperFrames, ספקי וידאו בתשלום, אווטאר/פודקאסט/דמו מסך, מונטאז' ארכיון במקום הוכחת רצפה, פרסום חי.

## קבצים

| קובץ | תפקיד |
|---|---|
| [`catalog.json`](catalog.json) | 12 צינורות + דפוסים, קריא למכונה |
| [`EMBED.md`](EMBED.md) | איך מריצים את חמשת הצוותים |
| [`LOCK.md`](LOCK.md) | מה דולג ולמה |
| [`crews/`](crews/) | נהלי צוות להרצה ב-Cursor |
| [`scripts/check-vfom.py`](../../scripts/check-vfom.py) | בדיקת עקביות מול `packages/manifest.json` |
| [`docs/OPENMONTAGE.md`](../../docs/OPENMONTAGE.md) | דוח בעברית לראש צוות |

## איך מפעילים

ב-Cursor:

```
@vfom reference-plan <קישור ריל>
@vfom clip-factory <שם עבודה / טיימלאפס>
@vfom hybrid-reel <שם עבודה>
@vfom scene-gate <בריף ריל>
@vfom self-review <בריף ריל>
```

או פותחים את הקובץ ב-`crews/` ומריצים לפי הסדר.

`python3 scripts/check-vfom.py` — צפי: `OK vfom`.
