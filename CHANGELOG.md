# Changelog

All notable changes to Velvet Factory Headquarters & OS.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-08-30

- Initial GitHub backup of Cursor office packs.

### Added

- Headquarters catalog on GitHub (`packages/manifest.json`, `packages/<name>/ORIGIN.md`).
- `scripts/vendor-origin-packs.sh` to clone Origin trees when `origin auth login` or `CURSOR_API_KEY` is available.
- Pack list (one line each). Origin source trees were **not** copied in this environment (Origin CLI not logged in; GitHub token rejected by `origin.cursor.com`; pack agent transcripts not readable from this HQ).

#### Packs

- **vfigos** — VF Instagram OS: Instagram office pack (review and schedule; this HQ does not send). Origin `christian-velvet/tmp-20e9908caebda9d0`, [bc-c4a53ee3](https://cursor.com/agents/bc-c4a53ee3).
- **vfcost** — Studio cost pack: unit economics and spend, without invented prices. Origin `christian-velvet/tmp-8a55585f5a73bd06`, [bc-a4dc99c9](https://cursor.com/agents/bc-a4dc99c9).
- **vfconvert** — Conversion pack: inquiry-to-order path. Origin `christian-velvet/tmp-4460086f23171633`, [bc-9644a175](https://cursor.com/agents/bc-9644a175).
- **vfgrowth** — Growth pack: content sprints and acquisition work. Origin `christian-velvet/tmp-0093db8b6deea44f`, [bc-e68393a0](https://cursor.com/agents/bc-e68393a0).
- **vfprod** — Production pack: print-floor and job tracking. Origin `christian-velvet/tmp-c9ca74be9225ac7d`, [bc-cd4a5cde](https://cursor.com/agents/bc-cd4a5cde).
- **vfsales** — Sales pack: quotes and follow-up. Origin `christian-velvet/tmp-b467d4882113eabd`, [bc-28017566](https://cursor.com/agents/bc-28017566).
- **vfops** — Operations pack: run-the-studio procedures. [bc-93fbfca6](https://cursor.com/agents/bc-93fbfca6). Origin slug not found in this dump.
- **vfcovers** — Covers pack: brief and post cover art. [bc-390e0de1](https://cursor.com/agents/bc-390e0de1). Origin slug not found in this dump.
- **vfinsights** — Insights pack: performance reads; does not invent metrics. [bc-02df9e72](https://cursor.com/agents/bc-02df9e72). Origin slug not found in this dump.
- **vfbooks** — Books pack: receivables and studio ledger work. [bc-280dd241](https://cursor.com/agents/bc-280dd241). Origin slug not found in this dump.
- **vfresearch** — Research pack: source gathering and notes. [bc-01278e9b](https://cursor.com/agents/bc-01278e9b). Origin slug not found in this dump.
- **vfbiz** — Business pack: studio strategy and decisions. [bc-3921041e](https://cursor.com/agents/bc-3921041e). Origin slug not found in this dump.
- **vfcopy** — Copy desk: homework, draft, and lint. [bc-b6bc8b8c-136d-4d95-812e-177991534e42](https://cursor.com/agents/bc-b6bc8b8c-136d-4d95-812e-177991534e42). Origin slug not found in this dump.

[Unreleased]: https://github.com/nocturney/velvet-factory-headquarters-os/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/nocturney/velvet-factory-headquarters-os/releases/tag/v0.1.0
