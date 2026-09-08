# Inventory · Instagram integration (pre-edit · 2026-09-08)

Audit before making `adelaidasofia/instagram-mcp` canonical. No secrets.

## Hot paths (canonical today → must change)

| Path | Old claim |
|---|---|
| `.cursor/vf-desk.json` · `tools.instagram` | `needsAuth` · `jlbadano/ig-mcp` · no Stories · `publish_media` only |
| `instances/velvet-factory/.cursor/vf-desk.json` | same |
| `packages/vfmcp/core-mcp.json` | source `jlbadano/ig-mcp` · `needsAuth until token` |
| `packages/vfmcp/CORE-MCP.md` | «Instagram ig-mcp» |
| `packages/vfmcp/mcp.desktop.example.json` | local `ig-mcp` python path + old env names |
| `packages/vfigos/CONNECT-IG.md` | full jlbadano install + «Stories unsupported» + human token steps as current |
| `packages/vfigos/SEND.md` · `SKILL.md` | `publish_media` / ig-mcp |
| `packages/vfigos/CAPABILITIES.json` | `currentStatus: needsAuth` |
| `constitution/SEND.md` | ig-mcp `publish_media` |
| `docs/MCP-FIT.md` · `packages/vfmcp/GAP.md` | ig-mcp needsAuth; Publish gap open |
| `packages/vfgrowth/STORIES.md` | «ig-mcp ≠ stories» · no Publish from HQ |
| `packages/vfinsights/SKILL.md` · `READ.md` | ig-mcp / Metricool as Insights path |
| `scripts/check-vfmcp.py` · `vf_send_preflight.py` | expect jlbadano needles + `needsAuth` |

## Legacy / historical (keep, mark deprecated)

| Path | Note |
|---|---|
| `packages/vfresearch/LINKS.json` · `ig-mcp-jlbadano` | keep URL; mark legacy |
| `packages/vfresearch/sources/*` | weekly notes mentioning jlbadano / Metricool |
| `packages/vfharness/state/*` | historical checkpoints — do not rewrite |
| `packages/vfops/hq/brief-2026-09-0*.json` | historical briefs |

## Already correct (retain)

| Path | Note |
|---|---|
| `CAPABILITIES.json` capability ids (incl. Stories) | keep; flip status |
| `PUBLICATION-STATES.*` | liveVerified law — extend with pending verification |
| `docs/MEDIA-VAULT.md` · `packages/vfmedia/` | one catalog; no share-permission changes |
| Metricool in `notRequired` | already listed; reinforce as optional/legacy |
| DM / boost forbidden | keep forever |

## Verified facts (owner / Codespace · do not re-ask)

- `@velvets_cloud` linked to Facebook Page
- IG Business Account ID `17841407772120429`
- `add_account` label `velvets_cloud`, default true
- `healthcheck` / `get_profile` / `list_media` OK in Codespace
- Transport: **stdio** · secrets in Codespace env only
- Remote always-on MCP for Cloud Agent: **pending**
