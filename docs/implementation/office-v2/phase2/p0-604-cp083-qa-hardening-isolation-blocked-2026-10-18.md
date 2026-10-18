# CP083 QA hardening + Worker isolation BLOCKED (2026-10-18)

**SECURITY RED · Draft only · no merge/deploy**

## CLAIM

Cursor Cloud Agent `bc-01a14e53` (title: בידוד סביבת Worker) claimed the **isolation / limited My Machines** lane on #604/#612. This is **not** the independent security reviewer of Draft #749 (that agent already posted PASS WITH NOTES @ `85de7e7e…`).

## Worker isolation — BLOCKED (OS-enforced least privilege not available)

| Probe | Result |
|---|---|
| Desktop Commander devices online | 6 (Chris, Chris-3DPC, Chris-Mini-PC, MacMiniOffice, MacMiniOffice2, Mac-Bedroom) |
| Cursor self-hosted My Machines workers | 1 — `Chris` Windows, repo `velvetos-velvet-factory`, **host user credentials** |
| Start least-privilege worker on that machine | **Denied by policy** — must not run Worker under primary user / secrets / write GitHub / Computer Use / high-privilege MCP |
| Cloud `useradd` dedicated UID | `Permission denied` (cannot lock `/etc/passwd`) |
| Cloud `unshare --user` | Succeeds but **does not** hide `HOME` or `CLOUD_AGENT_*` secrets — not an OS security boundary for workers |
| Colima `vf-cp083-quarantine` guest | STOPPED; prior `Operation not permitted` for guest user NS; guest-root provisioning blocked by safety control — **not bypassed** |

**Pilot Worker not started.** Isolation remains BLOCKED until a verified dedicated OS identity exists without weakening security controls.

## Fallback code task (executed)

Independent stacked work on Draft #749 head `85de7e7e…` implementing Cursor QA fix requests without modifying ChatGPT's occupied branch tip in-place (new branch / new Draft PR):

1. Linux/`SO_PEERCRED` platform gate **before** `connect`
2. Reply allow-list: `status`, `head`, `record`, `frozen` only
3. Client negatives expanded with positive matching-UID control, slow-ACK **lower** bound (`>2.5s`), malformed/symlink/extra-field/partial-late cases
4. New static reconcile negatives pinning Option A labels, UNKNOWN-after-ACK, no blind retry

Option A contract unchanged: revoke-first → DENY; admit-first → DRAINING; uncertain external effect → `UNKNOWN_EFFECT_RECONCILE`; no blind retry; no early reservation release.

## Not claimed

- Full joined distinct guest UIDs + live etcd/Git Option A replay of this candidate
- Two autonomous coding workers
- Security admission GREEN
- Merge / deploy / ports / admin / paid APIs / Codex / Work
