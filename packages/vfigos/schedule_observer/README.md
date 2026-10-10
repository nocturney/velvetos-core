# VelvetOS Instagram — Multi-source read-only observer (candidate)

## Purpose

One user question should make the assistant inspect every **known and connected** read source without asking the owner whether to check Meta, Cloudflare or Google Calendar first. An inaccessible source is **UNKNOWN / UNAVAILABLE**, never a zero schedule. No publication or scheduling permission is added.

**This is a read projection.** Cloudflare Publisher D1 remains the one VelvetOS production schedule *writer*. Meta Business Suite can have a separate native queue. Google Calendar `אינסטגרם` is only a Cloudflare mirror and is not authoritative for Meta-native schedules. Instagram Graph is an evidence provider for *published* media, not native Meta scheduling. Instagram-app-only schedules are explicitly marked unsupported until an approved read path exists.

## Registry and coverage

`source-registry.json` is an instance-scoped provider inventory. Every configured source receives one of: AVAILABLE / EMPTY / STALE / INVALID / UNAVAILABLE / UNSUPPORTED / DISABLED. Future provider adapters must be registered and evaluated; there is no legitimate way to silently claim all imaginable third-party accounts have been searched.

- **Meta Business Suite**: reads only the Scheduled tab, under an owner-authorized dedicated local Chrome profile, using visible DOM rows and user-interface scrolling. It does **not** capture or export cookies, tokens, private API payloads or localStorage; and it never creates or edits posts. The reader stores visible text only under the restricted Windows user-state directory; screenshot and raw text are local artifacts, never committed.
- **Cloudflare Publisher**: delegates to the existing `Resolve-Phase3B-ProductionSnapshot.ps1 -Mode Production` (trusted interactive `Chris` context), preserving the cp017 GREEN production-read grant. No old `CONTROL_TOKEN` fallback, no publishing rights.
- **Google Calendar**: connector-supplied bounded event snapshot. Derivative mirror; a discrepancy is mirror drift only relative to an actually available Cloudflare snapshot.
- **Instagram Graph**: connector-supplied published media snapshot for readback. Never used to infer an empty scheduled queue.
- **Native Instagram app**: no authenticated, verified scheduled-list reader configured; report explicitly UNSUPPORTED.
- **OpenPost**: legacy frozen since Sept 24; disabled, not a production writer.

Meta's virtualized DOM can repeat the same row as it loads more. Reconciliation deduplicates by scheduled datetime, media kind, and exact normalized caption. Never merge by time alone. If the UI scroll range cannot prove it exhausted all records, the result is a **lower bound**, not a total-certified count.

## Files

- `reader-v3.cjs`: Chrome UI reader, flags `--once --headless` for unattended local refresh. Uses `puppeteer-core` and an owner-created browser profile. UI-only browser automation is susceptible to Meta markup changes or re-authentication.
- `source-reconciler.py`: pure deterministic registry-driven reconciliation; Python standard library, no credentials or HTTP requests.
- `source-registry.json`: complete explicit known-source inventory and source TTLs.
- `run-on-demand.ps1`: Windows interactive-user orchestrator, calls local Meta reader + the existing Office v2 production read, and includes independently supplied calendar/Graph snapshots if fresh.
- `test-source-reconciler.py`: regression tests for fail-closed, dedup, DST, wrong account/tab, publisher heartbeat, calendar drift and true on-disk Meta fixture.
- `package.json`: pinned `puppeteer-core`, no Chrome download.

## Local deployment (Velvet Factory Windows Chris)

Staged installation:
- Code: `D:\Velvet\Projects\MetaPlannerReader`
- Restricted private browser profile: `D:\Velvet\State\MetaPlannerReader\chrome-profile`
- Read-only evidence artifacts: `D:\Velvet\Artifacts\MetaPlannerReader`
- Existing secure resolver: `D:\Velvet\Runtime\OfficeV2Lab\Resolve-Phase3B-ProductionSnapshot.ps1`

**Owner login** is completed once in the dedicated Chrome profile. Run `npm ci --omit=dev --ignore-scripts` when deploying from repo with lockfile; the deployed copy may use `npm install --omit=dev --ignore-scripts` if no lockfile yet.

An **on-demand only** Windows Scheduled Task named `VelvetOS Instagram Sources Read` runs as `CHRIS\Chris`, `InteractiveToken`, with **no trigger**. The connected Remote Desktop Commander service can request `Start-ScheduledTask`; Windows starts it under the authorized desktop user without copying or revealing session credentials. The action is `run-on-demand.ps1` and the task returns in minutes, not continuously.

The assistant should, **without asking the user which source to check**:

1. Start that one read-only task (unless an equivalent verified fresh run exists).
2. Fetch the Google Calendar `אינסטגרם` future events and Instagram Graph published media via the already connected plugins; normalize and atomically write their **whitelisted** connector snapshots into the restricted artifact directory. They can also be refreshed before starting the task to include all four sources.
3. Wait for the task completion and inspect `on-demand-read-receipt.json` and `all-sources-latest.json`.
4. Present merged per-source records with timestamps, explicit gaps, coverage and cross-source conflicts. Do not say there are zero schedules if any active schedule source is unavailable. Do not add Meta-native schedules to Cloudflare or modify existing postings without the separate publication-authority process.

Example owner-context interactive read:

```powershell
Start-ScheduledTask -TaskName 'VelvetOS Instagram Sources Read'
Get-Content -Raw 'D:\Velvet\Artifacts\MetaPlannerReader\on-demand-read-receipt.json'
```

Python verifier:

```powershell
C:\Python311\python.exe D:\Velvet\Projects\MetaPlannerReader\test-source-reconciler.py
```

## Safety and scope

- This is a source discovery/reading component, **not** a new scheduler, marketing writer, automation engine, source of truth, autonomous cloud account inspector, or Office 2.0 P0 agent. Never run it with publisher control credentials.
- `headless` Meta reader is only an alternative *UI rendering mode* for an already owner-authenticated browser profile; it never bypasses authentication or session boundaries.
- When Windows is logged out, Meta authentication expires, the Meta UI changes or the browser is in active use, fail visibly and preserve the last valid time-stamped snapshot without treating it as current. The assistant should not ask for login unless this genuinely blocks an authorized read.
- The read-on-demand task has no recurrence and does not interfere with existing Office 2.0 ownership, lease or authority. No production promotion until protected PR/CI and direct production readback.
- Need a separate, supported **MCP/connector endpoint** to make this callable in chats that do not have Remote Desktop Commander. The existing Instagram MCP connector alone does **not** expose Meta's native Scheduled list. Never claim otherwise.
