# VF Research - GitHub repository source recheck - 2026-10-17

Scope: precisely 16 records from LINK.json last reviewed 2026-10-07. Rechecked live authenticated GitHub repository metadata and README existence/size/sha for each on 2026-10-17 (Asia/Jerusalem).
Limits: no README body, diff or full code review. A recent push does NOT prove maintained or safe; an archived repository is historical-only. No installs, secrets, licensing conclusions, new capabilities, runtime approval or customer actions.

| ID | Repo | Archive | Last upstream push (UTC) | README | Verification |
|---|---|---|---|---|---|
| `cua` | [source](https://github.com/trycua/cua) | NO (maintenance not proven) | 2026-10-17 | 21071 B / `239b8df28b49` | GitHub API 200 |
| `acu` | [source](https://github.com/trycua/acu) | NO (maintenance not proven) | 2025-09-26 | 26363 B / `70b89477dde2` | GitHub API 200 |
| `awesome-n8n-templates` | [source](https://github.com/enescingoz/awesome-n8n-templates) | NO (maintenance not proven) | 2026-09-12 | 115134 B / `358bb3a191c8` | GitHub API 200 |
| `dashy` | [source](https://github.com/lissy93/dashy) | NO (maintenance not proven) | 2026-10-16 | 36175 B / `1be51b6b62d2` | GitHub API 200 |
| `awesome-cli-apps` | [source](https://github.com/agarrharr/awesome-cli-apps) | YES - historical-only | 2026-10-12 | 56551 B / `4989f8135b44` | GitHub API 200 |
| `awesome-shell` | [source](https://github.com/alebcay/awesome-shell) | NO (maintenance not proven) | 2025-08-28 | 44296 B / `75f75693a1ba` | GitHub API 200 |
| `awesome-agent-skills-voltagent` | [source](https://github.com/VoltAgent/awesome-agent-skills) | NO (maintenance not proven) | 2026-10-15 | 226330 B / `dbb9ef83bc5a` | GitHub API 200 |
| `awesome-openclaw-skills` | [source](https://github.com/VoltAgent/awesome-openclaw-skills) | NO (maintenance not proven) | 2026-10-11 | 136235 B / `03b47369adef` | GitHub API 200 |
| `awesome-claude-code` | [source](https://github.com/hesreallyhim/awesome-claude-code) | NO (maintenance not proven) | 2026-10-17 | 238876 B / `bb0d6dcdc138` | GitHub API 200 |
| `awesome-generative-ai-guide` | [source](https://github.com/aishwaryanr/awesome-generative-ai-guide) | NO (maintenance not proven) | 2026-10-15 | 9076 B / `4abc4995ff2c` | GitHub API 200 |
| `awesome-python` | [source](https://github.com/vinta/awesome-python) | NO (maintenance not proven) | 2026-10-17 | 81398 B / `408f65f0085e` | GitHub API 200 |
| `awesome-cpp` | [source](https://github.com/fffaraz/awesome-cpp) | NO (maintenance not proven) | 2026-10-11 | 198767 B / `538ac69b08fd` | GitHub API 200 |
| `awesome-java` | [source](https://github.com/akullpp/awesome-java) | NO (maintenance not proven) | 2026-09-23 | 183540 B / `7678928926ed` | GitHub API 200 |
| `awesome-design-patterns` | [source](https://github.com/DovAmir/awesome-design-patterns) | NO (maintenance not proven) | 2024-10-25 | 17202 B / `6c6285915bd3` | GitHub API 200 |
| `awesome-design-tools` | [source](https://github.com/goabstract/Awesome-Design-Tools) | NO (maintenance not proven) | 2024-07-28 | 144976 B / `f6c4d1aefd29` | GitHub API 200 |
| `magictools` | [source](https://github.com/ellisonleao/magictools) | NO (maintenance not proven) | 2026-10-16 | 56188 B / `2a592d2e71dd` | GitHub API 200 |

Existing original intake/source notes and scope restrictions remain canonical; only the lastReviewed metadata is refreshed.
Review of archived sources should not recommend live deployment; maintainers, supply chain and feature fitness remain independent admission decisions.
No automatic change to the eight-day staleness policy is made in this PR. Recommend a separate owner-reviewed policy change to keep source freshness visible without masking meaningful code safety failures.

Verification method: GitHub REST GET /repos/{owner}/{repo} plus GET /repos/{owner}/{repo}/readme (metadata only); each response parsed and validated before updating any file.
