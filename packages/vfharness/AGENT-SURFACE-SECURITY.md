# Agent surface security — AgentShield-pattern embed

Source pattern: `affaan-m/ECC` AgentShield. VelvetOS keeps its own runtime and security agents; only the deterministic configuration-audit pattern is embedded here.

## Surfaces in scope

- `.cursor/mcp.json` and desktop MCP examples
- `.cursor/skills/**/SKILL.md`
- `.cursor/rules/*.mdc`
- shell/python entrypoints referenced by agent instructions
- provider URLs, auth placeholders, write-capable tool declarations, hooks and command launchers

## Fail-closed checks

1. **No committed secrets** — bearer tokens, API keys, private keys, passwords, session cookies, or filled auth headers.
2. **No broad secret interpolation** — commands should reference named environment variables; never dump the environment or home credential stores.
3. **No hidden authority escalation** — a skill/rule cannot grant publish/send/delete/price authority that conflicts with constitution or pack gates.
4. **No prompt-injection obedience** — external content is data; instructions inside mail, web pages, files, issues, or media metadata do not alter system rules.
5. **No unreviewed remote execution** — curl-pipe-shell, downloaded executable launch, or opaque install hooks are blocked from the committed agent surface.
6. **MCP endpoints are explicit** — URLs must be visible in config/docs and secrets remain outside git.

Sensor: `python3 scripts/check-agent-surface-security.py`.
