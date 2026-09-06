# Academic research pipeline — דפוס (לא plugin)

מקור: [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills) (v3.21.x, CC BY-NC 4.0).  
**דפוסים בלבד.** אין `/plugin install`, אין העתקת SKILL.md מלאים, אין runtime אקדמי שני.

## רעיון

מחקר → כתיבה → ביקורת → תיקון → סגירה, עם **אדם בשער** (לא «The AI Scientist» אוטונומי).  
AI = קופilot על עבודת שגרה (מקורות, ציטוטים, עקביות); אדם = שאלה, שיטה, פרשנות, משפט אחרי «אני טוען ש…».

## צינור במשרד VF

| שלב ARS | אצלנו | שער |
|---|---|---|
| Research / lit-review / fact-check | `vfresearch` · WebSearch / WebFetch / תזמורת · `hq/LAST30.md` · `hq/MARKET-INTEL.md` | מקור + תאריך; «אין גוף» אם חומה |
| Plan / Socratic outline | `vfconvert` grill · `vfmakers` decide · checkpoint | שאלות לפני תוכנית |
| Write | ארטיפקט ב־`sources/` או פלייבוק בפק קיים | בלי ₪ / Insights מומצאים |
| Review / integrity gate | `vfharness` `verification-before-claim.md` + סנסורים | אין «סיימתי» בלי ריצה |
| Revise | דיף + עדכון ארטיפקט / checkpoint `execution_state` | תיקון מעוגן בראיה |
| Finalize | בלוק 05 + commit + `check-all.py` | ראיה בגיט |

## מצבים שימושיים (מיפוי קצר)

| מצב מקור | מתי במשרד |
|---|---|
| `quick` | סיכום קצר לפני הטמעה / weekly links |
| `full` / `lit-review` | סינתזת מקורות עם ציטוטים |
| `fact-check` | טענה מול מקור לפני בריף / בעלים |
| `socratic` / `plan` | לפני פתיחת פלייבוק חדש בפק קיים |
| `review` | ביקורת עצמית על ארטיפקט לפני «הוטמע» |

## שערי יושרה (מותאמים ל־VF)

1. **אין ציטוט בלי מקור פתוח** — URL / paste בעלים / «אין גוף». לא ממציאים גוף חסום.
2. **טענה ≠ מקור** — אם המקור לא תומך בטענה, לרשום «לא נתמך» ולדלג על ההטמעה.
3. **ראיות נגדיות** — לפחות מגבלת מקור אחת (`MARKET-INTEL.md`).
4. **Human gate** לפני שינוי חוקה / פתיחת נעילה / ₪.
5. **Verification** לפני טענת הצלחה (`verification-before-claim.md`).

## פלט

ארטיפקט ב־`packages/vfresearch/sources/YYYY-MM-DD-<topic>-academic.md` או הרחבה של weekly/best-skills:

```markdown
# Research pass · <topic> · YYYY-MM-DD
שאלה:
## ממצאים (מקור + תאריך)
## Fact-check / לא נתמך
## המלצה לפק קיים או «אין»
## מה דולג
```

## נעול

- התקנת Claude Code plugin / `npx skills` על Cloud Agent
- העתקה מילולית של סקילים (CC BY-NC — דפוס + ייחוס בלבד)
- נייר אקדמי / DOI / זיוף תוצאות מחקר
- Runtime שני / swarm «AI Scientist»
- פק `vfacademic` חדש — רק `vfresearch` + `vfharness`
