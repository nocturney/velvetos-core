# vffcc

Free Claude Code fit — map [Alishahryar1/free-claude-code](https://github.com/Alishahryar1/free-claude-code) onto Velvet Factory HQ. Playbooks and locks only; this HQ does **not** install `fcc-server`, vendor the FCC tree, or send.

Write-up: [`docs/FCC-FIT.md`](../../docs/FCC-FIT.md).

| | |
|---|---|
| Agent | https://cursor.com/agents/bc-5abae8de-a5da-455e-b71c-3db25e3d029c |
| bcId | `bc-5abae8de-a5da-455e-b71c-3db25e3d029c` |
| Origin slug | `unknown` |
| Codebase | (this HQ repo; not an Origin tree) |
| Clone | `(none)` |
| vendor | `hq-native` |
| Source | https://github.com/Alishahryar1/free-claude-code (MIT; v6.4.4 / 37c77262 reviewed 2026-09-27) |

FCC is a **local** Anthropic/OpenAI-compatible proxy. It does not reduce Cursor Cloud Agent usage on this run.

Do not commit secrets. Do not invent prices. Do not send Instagram from this pack.
Gmail and Instagram send through canonical HQ tools/policy; Grok Bot is optional backup. Printers stay on the floor. The canonical team has 6 seats.

Reviewed update: `v6.4.3` (`9fe194ed`) fixes the Windows Hermes installer by dropping unsupported `-SkipSetup`. VelvetOS keeps Hermes/FCC second-office runtime skipped; no live FCC service was installed.

Reviewed update: `v6.4.4` (`37c77262`) preserves provider admission/rate/concurrency/recovery state across settings changes. VelvetOS still uses FCC only as a pattern/policy source; no live FCC runtime or Hermes client is installed.
