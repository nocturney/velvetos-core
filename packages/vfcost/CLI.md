# vfcost — שורת עלות חומר

מושב: **תפעול**. CLI חומר בלבד. לא מחיר מכירה. לא שולחים מייל/IG מכאן.

## נוסחה

`גרם × ILS/kg ÷ 1000 = ILS/unit`

נתיב דוגמה (קלט מפורש, לא מחירון שמור):

`20.29g × 250 ILS/kg → 5.07 ILS/unit`

חסר גרמים = סירוב. אין אפס שקט. חסר ILS/kg מאומת = סירוב. לא ממציאים.

## פקודות

```
python3 scripts/vfcost.py material --grams 20.29 --ils-per-kg 250
python3 scripts/vfcost.py material --grams 20.29 --ils-per-kg 250 --filament Ella
python3 scripts/vfcost.py filaments
python3 scripts/vfcost.py cards
python3 scripts/vfcost.py brief
```

גלילי רצפה בשמות: Ella / Rachel / Gefen (`FILAMENTS.json`).  
`ilsPerKg` ריק עד מלאי/חשבונית מאומתים. `--filament Ella` בלי ILS/kg לא ממציא 250.

## איך תפעול / בריף מושכים שורה

חריץ **02** (כסף בעבודה) ב־`packages/vfops/BRIEF.md` + `hq/BRIEF-SLOTS.md`.

1. תפעול מריץ `python3 scripts/vfcost.py brief`.
2. מדביקים **את שורת הפלט כמו שהיא** לחבילת הבריף (`vfbriefux` תצוגה 3).
3. אין כרטיס עם גרמים → השורה היא `עלות חומר: אין כרטיס עם גרמים · בלי ₪ מכירה`.
4. יש כרטיס ב־`CARDS.json` עם גרמים + ILS/kg מאומת → שורת סכום חומר בלבד.
5. לא ממלאים ₪ מכירה בחריץ 02 מכאן. מחיר מכירה נשאר `X ₪` עד ראש צוות.

כרטיס חדש אחרי סלייס: גרמים מהסלייסר + ILS/kg ממקור מאומת. בלי גרמים — לא נכנס לבריף כמספר.
