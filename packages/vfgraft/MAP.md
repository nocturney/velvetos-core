# Office map

Token-budgeted first look. Open this, then **two or three** nodes. Do not grep the 273-specialist warehouse from zero.

```
HQ — VelvetOS Core (backend) · reference bind Velvet Factory · 5 seats · HQ sends via tools

laws            constraint   HQ-send-via-tools; no auto-DM/boost; no invented ₪; pickup Sderot; public site locked; internal console OK
pipeline        flow         פנייה → שיחה → הצעה → הדפסה → איסוף (= lead→talk→offer→fulfill→close)
desk            system       five seats; warehouse stays off
tools           system       Gmail · Calendar · Drive · Canva · WebSearch · GenerateImage · 3DAI site
skills          system       morning / inquiry / content / Canva / velvetos / this map
packs           system       packages/<name>/ — shared backend capabilities
velvetos        system       CORE backend; modules always loaded; instances/* = frontend scaffolds
grok-bot        boundary     optional backup; printers on floor
morning-job     job          בריף בוקר
inquiry-job     job          פנייה → טיוטת הצעה
content-job     job          חבילת תוכן + כריכות
blast           impact       what breaks if a law or tool mode moves
maps            system       vfe2b (+ orchestrators) · vfmakers · vfagents · vfmcp · vfgraft · velvetos
command-surface system       capabilities + pipeline board + portlets (future UI view)
```

## Ask → nodes

| Job | Open |
|---|---|
| VelvetOS / modules / instance repo | `packages/velvetos/KERNEL.md` + `REPOS.md` → [[packs]] → [[pipeline]] |
| בריף בוקר / what is open | [[morning-job]] → [[tools]] → [[skills]] |
| פנייה / quote this | [[inquiry-job]] → [[pipeline]] → [[packs]] |
| חבילת תוכן / covers / Canva | [[content-job]] → [[grok-bot]] → [[tools]] |
| מוזיקה / סאונד לריל | `vfresearch/MUSIC.md` → `@trend-researcher` → [[content-job]] → [[grok-bot]] |
| Social Booster / 3D model / trends / media director | `packages/velvetos/modules/expert-*.md` → [[desk]] → [[packs]] |
| סוף יום / זיכרון משותף / למידה | [[morning-job]] → `vfops/hq/DAILY-RETRO.md` → `vfops/data/owner-memory.md` → [[skills]] |
| how is HQ wired | this file → [[desk]] → [[packs]] |
| what breaks if I change X | [[blast]] |
| embed an outside repo | [[maps]] → [[laws]] |
| orchestrator / משמרת | [[maps]] → `vfe2b/ORCHESTRATORS.md` → [[laws]] |
| weekly inspiration links / share refresh | [[packs]] → `vfresearch/WEEKLY.md` + `LINKS.json` → [[laws]] |
| office console / CRM-ERP inspiration / command surface | [[blast]] → `vfops/hq/COMMAND-SURFACE.md` → `docs/OFFICE-OS-EMBED-he.md` → [[laws]] |

## Hubs

- `laws` — every job depends on it
- `grok-bot` — send boundary for Gmail, Instagram, printers
- `desk` — seat → pack → `@slug` → tool

## Do not

- Install `@nanonets/graft` from this pack
- Open the Agency warehouse unless the user names a slug
- Invent ₪ or Insights to fill a missing source

Nodes: [`graph/`](graph/). Machine list: [`graph.json`](graph.json). How to run: [`EMBED.md`](EMBED.md).
