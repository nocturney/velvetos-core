# Office map

Token-budgeted first look. Open this, then **two or three** nodes. Do not grep the 273-specialist warehouse from zero.

```
HQ — 5 seats · 28 desk specialists · 1 pipeline · Grok sends

laws            constraint   no send, no invented ₪, pickup Sderot
pipeline        flow         פנייה → שיחה → הצעה → הדפסה → איסוף
desk            system       five seats; warehouse stays off
tools           system       Gmail read · Calendar · Drive-by-job · Canva
skills          system       morning / inquiry / content / Canva / this map
packs           system       packages/<name>/ — no duplicate job
grok-bot        boundary     live Instagram, Gmail send, printers
morning-job     job          בריף בוקר
inquiry-job     job          פנייה → טיוטת הצעה
content-job     job          חבילת תוכן + כריכות
blast           impact       what breaks if a law or tool mode moves
maps            system       vfe2b · vfagents · vfmcp · vfgraft
```

## Ask → nodes

| Job | Open |
|---|---|
| בריף בוקר / what is open | [[morning-job]] → [[tools]] → [[skills]] |
| פנייה / quote this | [[inquiry-job]] → [[pipeline]] → [[packs]] |
| חבילת תוכן / covers / Canva | [[content-job]] → [[grok-bot]] → [[tools]] |
| how is HQ wired | this file → [[desk]] → [[packs]] |
| what breaks if I change X | [[blast]] |
| embed an outside repo | [[maps]] → [[laws]] |

## Hubs

- `laws` — every job depends on it
- `grok-bot` — send boundary for Gmail, Instagram, printers
- `desk` — seat → pack → `@slug` → tool

## Do not

- Install `@nanonets/graft` from this pack
- Open the Agency warehouse unless the user names a slug
- Invent ₪ or Insights to fill a missing source

Nodes: [`graph/`](graph/). Machine list: [`graph.json`](graph.json). How to run: [`EMBED.md`](EMBED.md).
