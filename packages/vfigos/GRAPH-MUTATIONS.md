# GRAPH-MUTATIONS · Instagram official Graph support matrix

Updated: 2026-09-09. Research against Meta Instagram Graph API docs (IG User / IG Media).  
VelvetOS law: if Meta does **not** expose an operation, status stays `unsupported_by_official_graph` and we do **not** register an MCP write tool.  
Capability discovery SoT: MCP tool `graph_mutation_matrix` (and this file).  
No browser automation, private APIs, credential scraping, or unofficial workarounds.

## Matrix

| Desired operation | Official Graph? | `supported` | Endpoint | Permissions | Allowed fields | Limitations | MCP tool exposed? |
|---|---|---|---|---|---|---|---|
| Update biography (`update_biography`) | **No** | `false` | — | — | — | IG User **Updating** unsupported | **No** |
| Update website (`update_website`) | **No** | `false` | — | — | — | same | **No** |
| Update display name (`update_name`) | **No** | `false` | — | — | — | same | **No** |
| Update profile bundle (`update_profile`) | **No** | `false` | — | — | — | same | **No** (removed — was misleading) |
| Update caption feed/Reel (`update_media_caption`) | **No** | `false` | `POST /{ig-media-id}` | (comments only) | `comment_enabled` only | Caption ignored | **No** (removed — was misleading) |
| Delete media (`delete_media`) | **Yes** | `true` (gated) | `DELETE /{ig-media-id}` | `instagram_manage_contents` | — | Irreversible | **Yes** — `delete_media` requires `confirm_irreversible` + explicit account; **no live delete in hardening** |
| Archive media (`archive_media`) | **No** | `false` | — | — | — | No archive API ≠ delete | **No** |

App `1748471159829574` (אינסטה מנג'ר) is in **dev_mode** / not live (Meta DevTools `basic_settings` 2026-09-09). Production MCP tokens remain server-side only — do not paste into docs.

## MCP tools (VelvetOS remote overlay)

| Tool | Behavior |
|---|---|
| `graph_mutation_matrix` | **Source of truth** — read-only matrix with `supported` bool per op |
| `delete_media` | Official delete when `confirm_irreversible=true` + explicit account |

**Not exposed** (agents must not see these as write capabilities): `update_profile`, `update_media_caption`, `update_biography`, `update_website`, `update_name`, `archive_media`.

## Bio discrepancy (live vs law)

Live Graph profile (ChatGPT verify 2026-09-09):

- Name: `Velvet Factory | הדפסות תלת־ממד`
- Bio includes `WhatsApp 050-2517000` → conflicts with `PUBLIC_CURRENT_CTA`

Compliant replacement: [`PROFILE-DESIRED.json`](PROFILE-DESIRED.json) — human / Instagram-app edit (Graph cannot write profile).

## Related

- [`CONNECT-IG.md`](CONNECT-IG.md)
- [`CAPABILITIES.json`](CAPABILITIES.json)
- [`constitution/PUBLIC_CTA.md`](../../constitution/PUBLIC_CTA.md)
- Remote overlays: `remote/mutations.py` · `remote/insights_v21.py` · `remote/cta_tools.py`
