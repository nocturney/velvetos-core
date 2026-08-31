# פריפלייט קובץ הדפסה

מושב: **ייצור**. לא מדפיסים מ־HQ. לא CMYK / PDF נייר — הסטודיו הוא תלת־ממד.

```
python3 scripts/vf_office.py print preflight path/to/model.stl
```

מה הבדיקה עושה:

- STL בינארי / ASCII — מספר משולשים + תיבת גבול (מ״מ, בהנחה)
- STEP / 3MF — «הקובץ קיים; ממשיכים בסלייסר / 3DAI»
- `price` ו־`print_hours` תמיד ריקים
- `hq_prints: false`

ארבע הווי ב־`CHECKLIST.md` נשארות חובה על הרצפה.  
תיקון רשת / Image-to-3D: `3DAISTUDIO.md` (OAuth). אתר אם MCP `needsAuth`.  
Studio MCP Hub בליבה (`vfmcp/CONNECT-STUDIOHUB.md`) — VF מדלג `print_ready`/CMYK.  
רישיון: `vlicense`. אין ₪ מכאן.
