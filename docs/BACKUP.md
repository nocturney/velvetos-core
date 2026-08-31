# Grok Bot — HQ backup standing order

**Date:** 2026-08-30  
**From:** Christian  
**Repo:** [nocturney/velvet-factory-headquarters-os](https://github.com/nocturney/velvet-factory-headquarters-os)  
**This HQ agent:** [bc-1ac8b360-69b9-4a1a-954f-19124ea6a227](https://cursor.com/agents/bc-1ac8b360-69b9-4a1a-954f-19124ea6a227)

GitHub HQ is the **constant** backup of Velvet Factory Cursor packs. Do not wait for a weekly dump.

## On every finished VF cloud agent

Reply to **this HQ agent** (follow-up on the run above) with:

```
bcId: bc-…
pack: <packages/name>
origin: <owner/repo or unknown>
```

Include the Origin slug only when you actually have it. Do not invent slugs, prices, or secrets.

Unknown slugs (`vfops`, `vfcovers`, `vfinsights`, `vfbooks`, `vfresearch`, `vfbiz`, `vfcopy`, `vlicense`, `vfseason`, `vfsku`, `vfbriefux`) stay `unknown` until a real copy arrives. Do not guess `tmp-…` from the pack name. HQ overlay is the office. Playbook: [`ORIGIN-SLUGS.md`](ORIGIN-SLUGS.md). Report: `python3 scripts/discover-origin-slugs.py`.

**Quiet if nothing new** — no ping when the finished agent is not a VF pack, or when HQ already has that bcId + name + slug.

HQ sends Instagram via tools (`constitution/SEND.md`). Grok Bot is optional backup. Printers stay on the floor.

## What HQ does the same day

1. Add or update `packages/<name>/ORIGIN.md` and `packages/manifest.json`.
2. Vendor the Origin tree into `packages/<name>/` if Origin is reachable (`origin auth login` or `CURSOR_API_KEY`, then `scripts/vendor-origin-packs.sh`).
3. Append `CHANGELOG.md` **Unreleased** with the date and one Hebrew+English line.
4. Push to `main` (or the open PR branch).

If Origin will not clone, still update the catalog and CHANGELOG so GitHub stays current as a **map**.
