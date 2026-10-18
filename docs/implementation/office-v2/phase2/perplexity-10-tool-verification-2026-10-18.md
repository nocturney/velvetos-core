# Perplexity 10-tool scan, auditor verification (2026-10-18)

Issue: `nocturney/velvetos-core#595`. This is the repo copy of the auditor's read-only check of the owner's Perplexity Office 2.0 scan (10 candidates). Report only: no registry edits, no install, no promotion.

Source: [auditor comment](https://github.com/nocturney/velvetos-core/issues/595#issuecomment-6249011608). The auditor checked on 2026-10-18, around 13:55 IDT. Machine-readable data: `perplexity-10-tool-verification-2026-10-18.json`.

Claim: [#612 comment](https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6249230356).

## Check time

License and archived status were re-read from the GitHub REST API at write time.

| Check | Time (UTC) | Call |
|---|---|---|
| Archived flag, SPDX `license.spdx_id`, default branch, `pushed_at` | 2026-10-18T11:16:07Z | `GET /repos/{owner}/{repo}` |
| License file text and the AutoGen README | same pass, before the UFO advisory read | contents API |
| UFO published security advisories | 2026-10-18T11:18:22Z | `GET /repos/microsoft/UFO/security-advisories?state=published` |

Windows-without-Docker ratings, release names, and CVE rows other than the UFO advisory list are the auditor's verified facts. A value this record did not re-check, and that the source comment does not state, is `UNVERIFIABLE`.

Policy #632: a license does not block selling. These ten rows are software, not 3D-print models. Licenses are recorded as the API and license files state them.

Auditor totals, not re-counted here: **87 VERIFIED, 6 WRONG, 2 UNVERIFIABLE.** All 51 CVE IDs the auditor checked exist in GHSA or NVD. Five "last commit" cells Perplexity left empty were filled by the auditor and do not count as WRONG.

## GitHub license and archived status

`GET /repos/{owner}/{repo}` at 2026-10-18T11:16:07Z. Every `archived` field is `false`.

| # | Repo | SPDX at check | License as recorded | Archived | Maintenance |
|---|---|---|---|---|---|
| 1 | `crewAIInc/crewAI` | MIT | MIT (`LICENSE`) | false | GitHub archived false. Auditor: release 1.15.28 (2026-10-14), commit `40bb2d3` 2026-10-16. API `pushed_at` 2026-10-18T06:35:12Z. HEAD SHA at this check: UNVERIFIABLE |
| 2 | `microsoft/autogen` | CC-BY-4.0 | `LICENSE` is CC-BY-4.0 (docs). `LICENSE-CODE` is MIT (code). Both files read | false | README says the project is archived and no longer maintained, and points new work to [microsoft/agent-framework](https://github.com/microsoft/agent-framework). GitHub `archived` is still false |
| 3 | `langchain-ai/langgraph` | MIT | MIT | false | GitHub archived false. Auditor: 1.2.16 (2026-10-16 22:11Z), commit `0870f5e` 2026-10-18. API `pushed_at` 2026-10-18T01:27:12Z |
| 4 | `coleam00/Archon` | MIT | MIT. Default branch `dev` | false | GitHub archived false. Auditor: v0.12.1 (2026-10-17); commit `c7b358f` at 2026-10-18 10:34Z, with a newer commit `7ab8a9b` already noted. API `pushed_at` 2026-10-18T11:11:04Z. HEAD SHA at this check: UNVERIFIABLE |
| 5 | `microsoft/UFO` | MIT | MIT | false | GitHub archived false. Auditor: v3.0.10 (2026-09-22), commit `eae3c0a` 2026-10-14. API `pushed_at` 2026-10-17T13:15:14Z |
| 6 | `OpenHands/OpenHands` | MIT | MIT (root `LICENSE`). An enterprise-licence note is UNVERIFIABLE: the repo root listing has no `enterprise/` directory | false | GitHub archived false. Auditor: v1.27.1 (2026-10-12), commit `852132d` 2026-10-17. API `pushed_at` 2026-10-17T22:11:14Z |
| 7 | `n8n-io/n8n` | NOASSERTION | Sustainable Use License 1.0 (`LICENSE.md`). `.ee.` files need an n8n Enterprise licence. Source-available. Internal business, non-commercial, or personal use | false | GitHub archived false. Auditor: n8n@2.43.7 (2026-10-16), commit `d2dc2f9` 2026-10-18. API `pushed_at` 2026-10-18T10:07:12Z. Default branch `master` |
| 8 | `activepieces/activepieces` | NOASSERTION | MIT Expat, except `packages/ee/` and `packages/server/api/src/app/ee`, which use the Activepieces Enterprise licence (`packages/ee/LICENSE`). Both files read | false | GitHub archived false. Auditor: 0.92.3 (2026-10-12), commit `ec79605` 2026-10-18. API `pushed_at` 2026-10-18T11:14:28Z |
| 9 | `windmill-labs/windmill` | NOASSERTION | AGPLv3 by default. Apache-2.0 for the named clients and OpenAPI. Proprietary for enterprise snippets. Community Edition binaries and images: free use, no sell, resell, managed service, modify, or wrap. `LICENSE` read | false | GitHub archived false. Auditor: v1.840.0 (2026-10-17), commit `19ec5d3` 2026-10-18. API `pushed_at` 2026-10-18T10:33:02Z |
| 10 | `temporalio/temporal` | MIT | MIT | false | GitHub archived false. Auditor: GitHub latest v1.32.1 (2026-10-08); v1.31.4 and v1.30.8 published 2026-10-12; commit `d934169` 2026-10-18. API `pushed_at` 2026-10-18T06:46:32Z |

## Windows without Docker, and CVEs

Windows column: `yes` / `partial` / `no`, as the auditor recorded it. This pass did not re-fetch the vendor docs.

| # | Tool | Windows without Docker | CVEs (auditor, except UFO which was re-read) | Auditor row |
|---|---|---|---|---|
| 1 | CrewAI | yes. Official PowerShell `uv` install | CVE-2026-2275 critical, fix UNVERIFIABLE. CVE-2026-2286 critical, fix UNVERIFIABLE. CVE-2026-37008 high, fix UNVERIFIABLE. CVE-2026-37009 medium, fix UNVERIFIABLE. CVE-2026-62240 high, fix crewai-tools 1.15.1 | VERIFIED |
| 2 | AutoGen | yes. Windows venv; Docker is optional and only for the code executor | None in GHSA for the named packages, and none in repo advisories | WRONG: activity status |
| 3 | LangGraph | yes. Pure-Python wheel (`py3-none-any`) | CVE-2025-64104 and CVE-2025-64439: a fix exists, version number not stated (UNVERIFIABLE as a version). CVE-2026-48776 fix sdk 0.3.15. CVE-2026-48775 fix checkpoint 4.1.1. CVE-2026-104873 fix sdk 0.4.4. CVE-2026-28277 fix langgraph 1.0.10 (`GHSA-g48c-2wqr-h844`) | WRONG: one CVE detail |
| 4 | Archon | yes. `install.ps1` in the README | CVE-2025-69443 (`GHSA-9w6r-hr5j-2g2p`, medium, Archon 0.1.0, fix UNVERIFIABLE). CVE-2026-111322 (`GHSA-3q7p-hhhj-qh4p`, critical 9.3, unauthenticated `/api/*` on 0.0.0.0, affected 0.2.13–0.11.1, published 2026-10-15). v0.12.1 is outside that affected range. A patch version number is not named | WRONG: CVEs |
| 5 | UFO | yes. Windows is the target. `pip install -r requirements.txt`, Python ≥3.10 | 18 published repo advisories at 2026-10-18T11:18:22Z. `patched_versions` is an empty string or null on every advisory. IDs below | WRONG: CVE completeness |
| 6 | OpenHands | partial. Native PowerShell with Docker Desktop. WSL 2 is only for the multi-sandbox option | CVE-2026-33718 high, fix 1.5.0. CVE-2026-19022 medium, path removed in 1.7.0 per NVD | WRONG: Windows detail |
| 7 | n8n | partial. From 3.0, distributed only via Docker. On Windows the docs say WSL plus Docker Desktop | CVE-2025-52478, CVE-2025-62726, CVE-2025-65964, CVE-2025-68613, CVE-2025-68668, CVE-2025-68697, CVE-2026-21858, CVE-2026-65597, CVE-2026-72749. All exist. 4 are critical; which 4, and every fixed version: UNVERIFIABLE | VERIFIED |
| 8 | Activepieces | partial. Recommended self-host is Docker Compose plus Postgres and Redis. No documented native Windows path | CVE-2026-12813 (GHSA, low; GHSA id UNVERIFIABLE), CVE-2026-48499, CVE-2026-53535, CVE-2026-53536, CVE-2026-73081, CVE-2026-73082, CVE-2026-73083, CVE-2026-73084. Fixed versions UNVERIFIABLE | VERIFIED |
| 9 | Windmill | partial. Native Windows workers need no Docker or WSL, and they are a Self-Hosted Enterprise feature | CVE-2026-23696 critical (SQLi to admin token to RCE), CVE-2026-22683, CVE-2026-29059, CVE-2026-33881, CVE-2026-47107, CVE-2026-54136, CVE-2026-26964, CVE-2026-72539, CVE-2026-72541, CVE-2026-72542. Fixed versions other than the critical description: UNVERIFIABLE | VERIFIED |
| 10 | Temporal | yes. Temporal CLI Windows binary. `temporal server start-dev` is one process with SQLite | CVE-2025-8396, CVE-2025-14986, CVE-2025-14987, CVE-2026-5199, CVE-2026-5724, CVE-2026-65655, CVE-2026-87858, CVE-2026-89139, CVE-2026-89140, CVE-2026-104355. All exist in GHSA. Fixed versions UNVERIFIABLE. "Upgrade to ≥1.32.1/1.31.4/1.30.8" is UNVERIFIABLE | WRONG: release date |

### UFO advisories (API, 2026-10-18T11:18:22Z)

18 published advisories. `patched_versions` is empty on each one. CVSS score is the API `cvss.score`. A null score is UNVERIFIABLE.

| CVE | GHSA | Severity | Score | Affected range from the API | Fixed version |
|---|---|---|---|---|---|
| CVE-2026-105788 | GHSA-6ppj-5886-4f26 | high | 8.8 | `<= be75a7d` | no patched version listed |
| CVE-2026-105789 | GHSA-85w2-wggf-rw49 | medium | 5.4 | `<= 3.0.8` | no patched version listed |
| CVE-2026-105790 | GHSA-3pgm-xw75-hq27 | medium | 6.4 | Current `main` at commit `364eb7969d392e857299ceaf14bd6057e5b00078` | no patched version listed |
| CVE-2026-105791 | GHSA-cmq9-vqjf-4q2q | high | 7.5 | `<= 3.0.8` | no patched version listed |
| CVE-2026-105792 | GHSA-3hwr-qx8m-9xxx | medium | 6.5 | Current `main` at commit `364eb7969d392e857299ceaf14bd6057e5b00078` | no patched version listed |
| CVE-2026-105793 | GHSA-5cjx-4375-4877 | critical | 9.1 | Current `main` at commit `364eb7969d392e857299ceaf14bd6057e5b00078` | no patched version listed |
| CVE-2026-45322 | GHSA-wj72-7w8h-695f | high | 7.8 | `<= v3.0.0` | no patched version listed |
| CVE-2026-46402 | GHSA-whcg-fgpx-76f2 | high | 8.1 | `v3.0.1-4-ge2626659` | no patched version listed |
| CVE-2026-46414 | GHSA-qgx6-cvhg-jw7p | high | 8.8 | `v3.0.1-4-ge2626659` | no patched version listed |
| CVE-2026-46416 | GHSA-cwwh-p9rv-4pj4 | medium | 6.3 | `v3.0.1-4-ge2626659` | no patched version listed |
| CVE-2026-46538 | GHSA-wmq2-74rj-7pjc | medium | 5.9 | `v3.0.1-4-ge2626659` | no patched version listed |
| CVE-2026-46544 | GHSA-29gc-vqjp-7fqf | medium | 5.3 | `v3.0.1-4-ge2626659` | no patched version listed |
| CVE-2026-54568 | GHSA-hc27-j4p9-qm2x | medium | 4.3 | `>= 3.0.0` | no patched version listed |
| CVE-2026-55440 | GHSA-hxjv-fmjf-wmjf | medium | 6.5 | `<= 3.0.1` | no patched version listed |
| CVE-2026-62316 | GHSA-vf4c-mf32-gf2h | high | 8.8 | `<=3.0.7` | no patched version listed |
| CVE-2026-73296 | GHSA-24fq-m9rr-g3mm | critical | 9.4 | `<= v3.0.7` | no patched version listed |
| CVE-2026-73297 | GHSA-7hrg-r8xr-p8gr | high | UNVERIFIABLE | `<= v3.0.7` | no patched version listed |
| (no CVE id) | GHSA-2jff-h3r3-59qm | medium | UNVERIFIABLE | `<= v3.0.0` | no patched version listed |

The auditor's named UFO facts match this list: CVE-2026-46544 is 5.3 with no patched version; CVE-2026-73296 is critical 9.4 and `<= v3.0.7`; CVE-2026-105793 is critical 9.1; CVE-2026-62316 is high 8.8 and `<=3.0.7`; CVE-2026-105791 is high 7.5 and `<= 3.0.8`; CVE-2026-46414 is high 8.8.

## Six Perplexity corrections

1. **AutoGen is not "active in maintenance mode".** The README says the project is archived and no longer maintained by Microsoft, and it points new projects to Microsoft Agent Framework. GitHub `archived` is still `false` (API at 2026-10-18T11:16:07Z).
2. **Archon is not "no CVE found".** Two exist: CVE-2025-69443 and CVE-2026-111322 (critical 9.3, unauthenticated control API on 0.0.0.0, affected through 0.11.1). Current v0.12.1 is outside that stated range.
3. **The UFO CVE list was incomplete.** One of 18 published repo advisories was listed. Both critical IDs, CVE-2026-73296 and CVE-2026-105793, were missing. The API re-read at 2026-10-18T11:18:22Z is 18 advisories. `patched_versions` is an empty string or null on each one.
4. **LangGraph CVE-2026-28277 is not "no public fix".** `GHSA-g48c-2wqr-h844` lists `langgraph` patched in 1.0.10.
5. **OpenHands is not "Windows officially via WSL" as the whole story.** The docs give a native PowerShell plus Docker Desktop path. WSL 2 applies only to the multi-sandbox option. The partial rating stands. The enterprise-licence note stays UNVERIFIABLE.
6. **Temporal is not "v1.31.4, 09.10.2026".** v1.31.4 was published 2026-10-12. The GitHub latest release is v1.32.1 (2026-10-08). Guidance to upgrade to ≥1.32.1 / 1.31.4 / 1.30.8 is UNVERIFIABLE. The v1.31.4 notes only say "Bump dependencies to address CVEs".

n8n's own row is VERIFIED. From 3.0 it is Docker-only, so a new Windows install is WSL plus Docker Desktop. That is `partial`, not a Windows-without-Docker yes.

## Verified top 3

Perplexity's top 3 was CrewAI, n8n, and UFO. The verified top 3 is CrewAI, LangGraph, and UFO localhost-only.

1. **CrewAI.** Supported. MIT, GitHub archived false, Windows-native via `uv`. Caveat from the auditor: 5 CVEs, 2 critical, so pin a current version and do not run CodeInterpreter or untrusted-input tools unsandboxed.
2. **LangGraph.** The pure-OSS, no-Docker fallback in place of n8n. MIT, pure-Python wheel, GitHub archived false. The auditor says the 6 checkpoint/SDK CVEs all have fixed versions. Two of those version numbers are not written in the source comment and stay UNVERIFIABLE here.
3. **UFO, localhost-only.** Supported for fit. Windows-native, MIT, GitHub archived false. Not supported for the security caveat as first written: 18 advisories, 2 critical, and no patched version listed on any of them. Run it only as a single-user, loopback-only setup, with no Galaxy, MCP, or WebSocket servers exposed. Re-check the advisory list before any adoption.

n8n stays active, and its integrations are strong. The licence is Sustainable Use License 1.0, which #632 does not treat as a sale block. It fails Windows-without-Docker for new installs because v3 is Docker-only, and it has 9 CVEs, 4 critical.

## UNVERIFIABLE

- OpenHands enterprise-licence note. No `enterprise/` directory in the repo root listing at this check.
- Temporal upgrade guidance "≥1.32.1 / 1.31.4 / 1.30.8". The auditor records that v1.31.4 notes only say "Bump dependencies to address CVEs".
- Fixed-version strings the source comment does not give, and that this pass did not look up, are marked UNVERIFIABLE on the rows above.
- Default-branch HEAD SHAs were not re-fetched. Auditor commit SHAs stay as recorded in the source comment. API `pushed_at` is a separate field.
