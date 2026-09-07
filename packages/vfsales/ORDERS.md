# הזמנות / פניות — orders.json

מושב: סטודיו (`vfsales`). לא CRM מלא. לא ₪ מומצא.  
קובץ: `data/orders.json`. ייחוס: `vfinsights/ATTRIBUTION.md`.

## מינימום שדות

```json
{
  "order_id": "lead_YYYY-MM-DD_NNN",
  "created_at": "ISO-8601+03:00",
  "channel": "whatsapp",
  "source_declared": "instagram|walkin|repeat|unknown",
  "source_content_id": null,
  "source_code": "REEL|STORY|MATERIAL|B2B|null",
  "lead_type": "B2B|consumer|unknown",
  "interest": "",
  "status": "new",
  "estimated_value_ils": null,
  "closed_value_ils": null,
  "human_owner": "christian",
  "conversion_certainty": "declared|window_24h|wa_me|unknown"
}
```

`estimated_value_ils` / `closed_value_ils` נשארים `null` עד סכום מראש צוות.  
אין לסמן המרה ודאית רק כי הגיעה הודעת וואטסאפ אחרי פוסט.
