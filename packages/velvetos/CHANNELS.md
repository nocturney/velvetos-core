# ערוצי סושיאל — multi-account

VelvetOS תומך ב־**יותר מחשבון Instagram אחד** לכל tenant. כל פוסט/סטורי/ריל חייב לציין `channelId`.

## מבנה

```json
"channels": {
  "instagram": [
    {
      "id": "ig-primary",
      "handle": "@velvets_cloud",
      "purpose": "studio",
      "primary": true,
      "language": "he"
    }
  ]
}
```

## חוקים

1. `primary: true` בדיוק על חשבון אחד.
2. תוכן לחשבון A לא עובר ל־B בלי החלטת ראש צוות.
3. Canva / `vfigos` / `vfcanva` עובדים מול `handle` של הערוץ שנבחר בבריף.
4. בלי Publish MCP — אותו failover (`SEND.md`) לכל ערוץ; לא לטעון שפורסם.
5. אוטו־DM ובוסט אסורים בכל הערוצים.
6. CTA מגיע מה־tenant — לא «שלחו DM».

## דוגמת יופי (טיוטה)

| id | handle | purpose |
|---|---|---|
| `ig-nails` | (חסר עד הפעלה) | ציפורניים |
| `ig-tattoos` | (חסר עד הפעלה) | קעקועים |

שני מותגים = שני ערוצים באותו tenant, לא שני משרדים.

## דוגמת פסיכיאטר (טיוטה)

ערוץ אחד או אפס (שיווק שקט). תוכן רק לפי `compliance.contentAllowed`. אין פרטי מטופל בפוסט.
