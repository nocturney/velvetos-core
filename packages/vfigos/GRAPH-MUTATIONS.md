# GRAPH-MUTATIONS · Instagram official Graph support matrix

Updated: 2026-09-09. Research against Meta Instagram Graph API docs (IG User / IG Media).  
VelvetOS law: if Meta does **not** expose an operation, MCP returns `unsupported_by_official_graph`.  
No browser automation, private APIs, credential scraping, or unofficial workarounds.

## Matrix

| Desired operation | Official Graph? | Endpoint | Permissions | Allowed fields | Limitations | Our Meta app scope (אינסטה מנג'ר `1748471159829574`) |
|---|---|---|---|---|---|---|
| Update biography (`update_biography`) | **No** | — | — | — | IG User **Updating** unsupported | N/A — cannot grant |
| Update website / profile link (`update_website`) | **No** | — | — | — | same | N/A |
| Update display name (`update_name`) | **No** | — | — | — | same | N/A |
| Update caption (feed post) (`update_media_caption`) | **No** | `POST /{ig-media-id}` | (comments only) | `comment_enabled` only | Caption param ignored | N/A for caption |
| Update caption (Reel) (`update_media_caption`) | **No** | same | same | same | same | N/A |
| Delete media (`delete_media`) | **Yes** | `DELETE /{ig-media-id}` | `instagram_manage_contents` | — | Irreversible; posts/carousels/reels/stories; not carousel children | **Not verified** on token this session — tool gated behind `confirm_irreversible` + explicit `account`; **no live delete exercised** |
| Archive media (`archive_media`) | **No** | — | — | — | No archive API distinct from delete | N/A |

App `1748471159829574` is in **dev_mode** / not live (Meta DevTools `basic_settings` 2026-09-09). Production MCP tokens remain server-side only — do not paste into docs.

## MCP tools (VelvetOS remote overlay)

| Tool | Behavior |
|---|---|
| `graph_mutation_matrix` | Read-only matrix dump |
| `update_profile` | Always `unsupported_by_official_graph` · `mutated=false` |
| `update_media_caption` | Always `unsupported_by_official_graph` · `mutated=false` |
| `delete_media` | Official delete when `confirm_irreversible=true` + explicit account — **do not** use for CTA cleanup automation |

## Bio discrepancy (live vs law)

Live Graph profile (ChatGPT verify 2026-09-09):

- Name: `Velvet Factory | הדפסות תלת־ממד`
- Bio includes `WhatsApp 050-2517000` → conflicts with `PUBLIC_CURRENT_CTA`

Compliant replacement: [`PROFILE-DESIRED.json`](PROFILE-DESIRED.json) — human / Instagram-app edit until Graph supports profile write (it does not).

## Related

- [`CONNECT-IG.md`](CONNECT-IG.md)
- [`CAPABILITIES.json`](CAPABILITIES.json)
- [`constitution/PUBLIC_CTA.md`](../../constitution/PUBLIC_CTA.md)
- Remote overlays: `remote/mutations.py` · `remote/insights_v21.py` · `remote/cta_tools.py`
