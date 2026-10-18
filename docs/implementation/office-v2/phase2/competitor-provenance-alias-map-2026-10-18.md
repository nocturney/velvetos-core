# Competitor provenance and alias map (read-only), 2026-10-18

Issue: `nocturney/velvetos-core#595`, acceptance criterion 1. Read-only map. It makes no triage decisions and changes no registry rows. Machine-readable data: `competitor-provenance-alias-map-2026-10-18.json` (schema v2).

## Inputs

| Path | Rows | Role |
|---|---:|---|
| `packages/vfresearch/LINKS.json` | 109 | research_link |
| `packages/vfe2b/catalog.json` | 47 | catalog_pick |
| `packages/vfe2b/orchestrators.json` | 30 | orchestrator_pick |
| `docs/implementation/office-v2/phase2/candidate-registry-v0.json` | 213 | registry_items |

## Counts

| Source | Total | Status counts |
|---|---:|---|
| research_link | 109 | MATCHED_BY_URL 7, MATCHED_STRONG 4, NON_GITHUB_ORIGIN 36, NOT_FOUND_IN_REGISTRY 49, WEAK_ONLY_REVIEW 13 |
| catalog_pick | 47 | AMBIGUOUS_URL 1, MATCHED_BY_URL 2, MATCHED_STRONG 2, NON_GITHUB_ORIGIN 38, NOT_FOUND_IN_REGISTRY 3, WEAK_ONLY_REVIEW 1 |
| orchestrator_pick | 30 | MATCHED_BY_URL 2, MATCHED_STRONG 2, NON_GITHUB_ORIGIN 1, NOT_FOUND_IN_REGISTRY 22, WEAK_ONLY_REVIEW 3 |

## How to read this

- `NOT_FOUND_IN_REGISTRY` and `WEAK_ONLY_REVIEW` mean unlinked, needs review. They do **not** mean lost or rejected.
- `NON_GITHUB_ORIGIN` rows have no owner/repo key and need a hand-written alias.
- `AMBIGUOUS_URL` rows point at several registry items and need a manual choice.
- The registry has no canonical URL field, so recall is limited. Treat the lists as a queue.

## Unlinked or ambiguous GitHub origins

| Source | Label | Origin | Status | Weak hints |
|---|---|---|---|---|
| research_link | awesome-mcp-servers | `punkpeye/awesome-mcp-servers` | NOT_FOUND_IN_REGISTRY |  |
| research_link | trailhq-graft | `trailhq/graft` | NOT_FOUND_IN_REGISTRY |  |
| research_link | free-claude-code | `alishahryar1/free-claude-code` | NOT_FOUND_IN_REGISTRY |  |
| research_link | 500-ai-agents | `ashishpatel26/500-ai-agents-projects` | NOT_FOUND_IN_REGISTRY |  |
| research_link | agency-agents | `msitarzewski/agency-agents` | NOT_FOUND_IN_REGISTRY |  |
| research_link | awesome-ai-agents | `e2b-dev/awesome-ai-agents` | NOT_FOUND_IN_REGISTRY |  |
| research_link | awesome-agent-orchestrators | `andyrewlee/awesome-agent-orchestrators` | NOT_FOUND_IN_REGISTRY |  |
| research_link | effective-html | `plannotator/effective-html` | NOT_FOUND_IN_REGISTRY |  |
| research_link | plannotator-write-better | `plannotator/write-better` | WEAK_ONLY_REVIEW | live-google-drive-connector, candidate-infisical-agent-vault |
| research_link | awesome-design-md | `voltagent/awesome-design-md` | NOT_FOUND_IN_REGISTRY |  |
| research_link | planning-with-files | `othmanadi/planning-with-files` | WEAK_ONLY_REVIEW | candidate-opencode-cli, candidate-robbietilton-compositor, candidate-flashml-freevideo |
| research_link | genai-agents-nirdiamant | `nirdiamant/genai_agents` | NOT_FOUND_IN_REGISTRY |  |
| research_link | oh-my-claudecode | `yeachan-heo/oh-my-claudecode` | NOT_FOUND_IN_REGISTRY |  |
| research_link | prompts-chat | `f/prompts.chat` | NOT_FOUND_IN_REGISTRY |  |
| research_link | taste-skill | `leonxlnx/taste-skill` | NOT_FOUND_IN_REGISTRY |  |
| research_link | huly-platform | `hcengineering/platform` | NOT_FOUND_IN_REGISTRY |  |
| research_link | monica-prm | `monicahq/monica` | NOT_FOUND_IN_REGISTRY |  |
| research_link | nocobase | `nocobase/nocobase` | NOT_FOUND_IN_REGISTRY |  |
| research_link | krayin-laravel-crm | `krayin/laravel-crm` | NOT_FOUND_IN_REGISTRY |  |
| research_link | idurar-erp-crm | `idurar/idurar-erp-crm` | NOT_FOUND_IN_REGISTRY |  |
| research_link | dolibarr | `dolibarr/dolibarr` | NOT_FOUND_IN_REGISTRY |  |
| research_link | linklyai-best-skills | `linklyai/best-skills` | NOT_FOUND_IN_REGISTRY |  |
| research_link | mcpmarket-blender-mcp | `ahujasid/mcp-for-blender` | WEAK_ONLY_REVIEW | live-creativecraft, live-blender |
| research_link | mcpmarket-blender-ai | `ahujasid/mcp-for-blender` | WEAK_ONLY_REVIEW | live-creativecraft, live-blender |
| research_link | mikiarlo3-ai-copywriter | `mikiarlo3/ai-copywriter` | NOT_FOUND_IN_REGISTRY |  |
| research_link | social-media-skills | `social-media-skills/skills` | NOT_FOUND_IN_REGISTRY |  |
| research_link | thekozugroup-humanizer | `thekozugroup/humanizer` | NOT_FOUND_IN_REGISTRY |  |
| research_link | hkuds-deeptutor | `hkuds/deeptutor` | NOT_FOUND_IN_REGISTRY |  |
| research_link | lieflat-charts | `larashero3-dotcom/lieflat-charts` | NOT_FOUND_IN_REGISTRY |  |
| research_link | academic-research-skills | `imbad0202/academic-research-skills` | NOT_FOUND_IN_REGISTRY |  |
| research_link | mvanhorn-last30days-skill | `mvanhorn/last30days-skill` | NOT_FOUND_IN_REGISTRY |  |
| research_link | ig-mcp-jlbadano | `jlbadano/ig-mcp` | NOT_FOUND_IN_REGISTRY |  |
| research_link | instagram-mcp-adelaidasofia | `adelaidasofia/instagram-mcp` | WEAK_ONLY_REVIEW | live-cloudflare-instagram-publisher, live-instagram-mcp, candidate-robbietilton-compositor |
| research_link | cporter202-automate-for-growth | `cporter202/automate-for-growth` | NOT_FOUND_IN_REGISTRY |  |
| research_link | cporter202-social-media-scraping-apis | `cporter202/social-media-scraping-apis` | WEAK_ONLY_REVIEW | candidate-flashml-freevideo, candidate-nexu-io-html-video, candidate-intake-charlie947-social-media-skills |
| research_link | cporter202-social-growth-apis-for-creators | `cporter202/social-growth-apis-for-creators` | WEAK_ONLY_REVIEW | candidate-flashml-freevideo, candidate-nexu-io-html-video, candidate-intake-charlie947-social-media-skills |
| research_link | cporter202-api-mega-list | `cporter202/api-mega-list` | NOT_FOUND_IN_REGISTRY |  |
| research_link | awesome-cad | `mlightcad/awesome-cad` | NOT_FOUND_IN_REGISTRY |  |
| research_link | scenario-labs-skills | `scenario-labs/skills` | NOT_FOUND_IN_REGISTRY |  |
| research_link | no-ai-slop | `petergyang/no-ai-slop` | NOT_FOUND_IN_REGISTRY |  |
| research_link | roble3-cc-blender-skill | `roble3/cc-blender-skill` | WEAK_ONLY_REVIEW | live-creativecraft, live-blender |
| research_link | arjun988-blender-skills | `arjun988/blender-skills` | WEAK_ONLY_REVIEW | live-creativecraft, live-blender |
| research_link | kajisho5-ffmpeg-skill | `kajisho5/ffmpeg-skill` | WEAK_ONLY_REVIEW | candidate-flashml-freevideo |
| research_link | samuelgursky-davinci-resolve-mcp | `samuelgursky/davinci-resolve-mcp` | WEAK_ONLY_REVIEW | candidate-flashml-freevideo |
| research_link | aedev-tools-adobe-agent-skills | `aedev-tools/adobe-agent-skills` | NOT_FOUND_IN_REGISTRY |  |
| research_link | jablonkai-skills | `jablonkai/skills` | NOT_FOUND_IN_REGISTRY |  |
| research_link | cua | `trycua/cua` | NOT_FOUND_IN_REGISTRY |  |
| research_link | acu | `trycua/acu` | NOT_FOUND_IN_REGISTRY |  |
| research_link | awesome-n8n-templates | `enescingoz/awesome-n8n-templates` | NOT_FOUND_IN_REGISTRY |  |
| research_link | dashy | `lissy93/dashy` | NOT_FOUND_IN_REGISTRY |  |
| research_link | awesome-cli-apps | `agarrharr/awesome-cli-apps` | NOT_FOUND_IN_REGISTRY |  |
| research_link | awesome-shell | `alebcay/awesome-shell` | NOT_FOUND_IN_REGISTRY |  |
| research_link | awesome-agent-skills-voltagent | `voltagent/awesome-agent-skills` | NOT_FOUND_IN_REGISTRY |  |
| research_link | awesome-openclaw-skills | `voltagent/awesome-openclaw-skills` | WEAK_ONLY_REVIEW | deferred-openclaw |
| research_link | awesome-claude-code | `hesreallyhim/awesome-claude-code` | NOT_FOUND_IN_REGISTRY |  |
| research_link | awesome-generative-ai-guide | `aishwaryanr/awesome-generative-ai-guide` | NOT_FOUND_IN_REGISTRY |  |
| research_link | awesome-python | `vinta/awesome-python` | NOT_FOUND_IN_REGISTRY |  |
| research_link | awesome-cpp | `fffaraz/awesome-cpp` | NOT_FOUND_IN_REGISTRY |  |
| research_link | awesome-java | `akullpp/awesome-java` | NOT_FOUND_IN_REGISTRY |  |
| research_link | awesome-design-patterns | `dovamir/awesome-design-patterns` | WEAK_ONLY_REVIEW | deferred-crewai, candidate-deerflow, candidate-lobehub |
| research_link | awesome-design-tools | `goabstract/awesome-design-tools` | NOT_FOUND_IN_REGISTRY |  |
| research_link | magictools | `ellisonleao/magictools` | NOT_FOUND_IN_REGISTRY |  |
| catalog_pick | AutoGen | `microsoft/autogen` | AMBIGUOUS_URL | candidate-microsoft-agent-framework |
| catalog_pick | GPT Researcher | `assafelovic/gpt-researcher` | NOT_FOUND_IN_REGISTRY |  |
| catalog_pick | MemGPT | `cpacker/memgpt` | NOT_FOUND_IN_REGISTRY |  |
| catalog_pick | Local GPT | `promtengineer/localgpt` | NOT_FOUND_IN_REGISTRY |  |
| catalog_pick | GPT Runner | `nicepkg/gpt-runner` | WEAK_ONLY_REVIEW | candidate-deerflow, candidate-opencode-cli |
| orchestrator_pick | Fusion | `runfusion/fusion` | NOT_FOUND_IN_REGISTRY |  |
| orchestrator_pick | kodo | `ikamensh/kodo` | NOT_FOUND_IN_REGISTRY |  |
| orchestrator_pick | tutti | `nutthouse/tutti` | NOT_FOUND_IN_REGISTRY |  |
| orchestrator_pick | 5dive | `5dive-ai/5dive` | NOT_FOUND_IN_REGISTRY |  |
| orchestrator_pick | paperclip | `paperclipai/paperclip` | NOT_FOUND_IN_REGISTRY |  |
| orchestrator_pick | fractal | `plasma-ai/fractal` | NOT_FOUND_IN_REGISTRY |  |
| orchestrator_pick | MartinLoop | `keesan12/martin-loop` | NOT_FOUND_IN_REGISTRY |  |
| orchestrator_pick | ralph-claude-code | `frankbria/ralph-claude-code` | NOT_FOUND_IN_REGISTRY |  |
| orchestrator_pick | ralphex | `umputun/ralphex` | NOT_FOUND_IN_REGISTRY |  |
| orchestrator_pick | Taskuary | `ldbumble/taskuary` | NOT_FOUND_IN_REGISTRY |  |
| orchestrator_pick | NEEDLE | `jedarden/needle` | WEAK_ONLY_REVIEW | candidate-intake-cactus-compute-needle |
| orchestrator_pick | Crewplane | `crewplaneai/crewplane` | NOT_FOUND_IN_REGISTRY |  |
| orchestrator_pick | LionClaw | `moshthepitt/lionclaw` | NOT_FOUND_IN_REGISTRY |  |
| orchestrator_pick | Open Multi-Agent | `open-multi-agent/open-multi-agent` | WEAK_ONLY_REVIEW | deferred-crewai, deferred-orca, candidate-selenium-grid-browser-pool |
| orchestrator_pick | Claudexor | `razzant/claudexor` | NOT_FOUND_IN_REGISTRY |  |
| orchestrator_pick | humanlayer | `humanlayer/humanlayer` | NOT_FOUND_IN_REGISTRY |  |
| orchestrator_pick | ivy-tendril | `ivy-interactive/ivy-tendril` | NOT_FOUND_IN_REGISTRY |  |
| orchestrator_pick | Dex | `francescoalemanno/dex` | NOT_FOUND_IN_REGISTRY |  |
| orchestrator_pick | amux | `andyrewlee/amux` | NOT_FOUND_IN_REGISTRY |  |
| orchestrator_pick | loki-mode | `asklokesh/loki-mode` | NOT_FOUND_IN_REGISTRY |  |
| orchestrator_pick | bernstein | `sipyourdrink-ltd/bernstein` | NOT_FOUND_IN_REGISTRY |  |
| orchestrator_pick | takopi | `banteg/takopi` | NOT_FOUND_IN_REGISTRY |  |
| orchestrator_pick | claude-code-action | `anthropics/claude-code-action` | WEAK_ONLY_REVIEW | live-adobepy, incumbent-current-authorization, candidate-dagu-worker-fleet |
| orchestrator_pick | denchclaw | `denchhq/denchclaw` | NOT_FOUND_IN_REGISTRY |  |
| orchestrator_pick | Archon | `coleam00/archon` | NOT_FOUND_IN_REGISTRY |  |

## Matched rows

| Source | Label | Origin | Status | Registry ids | URL hit |
|---|---|---|---|---|---|
| research_link | codebase-memory-mcp | `deusdata/codebase-memory-mcp` | MATCHED_BY_URL | candidate-intake-deusdata-codebase-memory-mcp | yes |
| research_link | ruflo | `ruvnet/ruflo` | MATCHED_STRONG | deferred-ruflo | yes |
| research_link | getbindu-bindu | `getbindu/bindu` | MATCHED_BY_URL | candidate-bindu | yes |
| research_link | lobehub-operator | `lobehub/lobehub` | MATCHED_BY_URL | candidate-lobehub | yes |
| research_link | huginn | `huginn/huginn` | MATCHED_BY_URL | candidate-intake-huginn-huginn | yes |
| research_link | superset-sh-superset | `superset-sh/superset` | MATCHED_BY_URL | candidate-intake-superset-sh-superset | yes |
| research_link | twentyhq-twenty | `twentyhq/twenty` | MATCHED_STRONG | candidate-twenty | no |
| research_link | frappe-erpnext | `frappe/erpnext` | MATCHED_STRONG | candidate-erpnext | no |
| research_link | akaunting | `akaunting/akaunting` | MATCHED_STRONG | candidate-akaunting | no |
| research_link | debpalash-voicestudio | `debpalash/voicestudio` | MATCHED_BY_URL | candidate-intake-debpalash-voicestudio | yes |
| research_link | charlie947-social-media-skills | `charlie947/social-media-skills` | MATCHED_BY_URL | candidate-intake-charlie947-social-media-skills | yes |
| catalog_pick | CrewAI | `joaomdmoura/crewai` | MATCHED_STRONG | deferred-crewai | no |
| catalog_pick | UFO | `microsoft/ufo` | MATCHED_BY_URL | candidate-intake-microsoft-ufo | yes |
| catalog_pick | Huginn | `huginn/huginn` | MATCHED_BY_URL | candidate-intake-huginn-huginn | yes |
| catalog_pick | Orca | `stablyai/orca` | MATCHED_STRONG | deferred-orca | yes |
| orchestrator_pick | Orca | `stablyai/orca` | MATCHED_STRONG | deferred-orca | yes |
| orchestrator_pick | herdr | `herdrdev/herdr` | MATCHED_STRONG | candidate-herdr | no |
| orchestrator_pick | gastown | `gastownhall/gastown` | MATCHED_BY_URL | candidate-intake-gastownhall-gastown | yes |
| orchestrator_pick | OpenClaw | `openclaw/openclaw` | MATCHED_BY_URL | deferred-openclaw | yes |

## Next steps (not done here)

1. Owner or triage decides the unlinked GitHub rows (CLQ-2 covers the non-GitHub rows).
2. Ambiguous rows need a manual choice of candidate id.
3. A canonical URL field in the registry would remove most name matching. That is a schema change and needs owner approval.
