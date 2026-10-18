# Office 2.0 P0 — Cross-guest Windows Host Compute event identity negative (#604 / #612)

**2026-10-11 | LAB-only, read-only real host observation.** This is NOT Windows Sandbox guest acceptance and NOT host/OS/credential security attestation. No guest was launched by the probes and the original public-only WSB fixture was not edited.

## Why this additional gate exists

PR [#696](https://github.com/nocturney/velvetos-core/pull/696), merged to main `73047a7c58c3c7c192ca7337068e13a784f1ab3e`, already established a clear negative: a host-writable JSON guest receipt, even when shaped like a successful Sandbox outcome, is *not* trusted evidence that a VM ran. A second confusion risk remains: **another Windows Sandbox/Hyper-V compute system can run while the Office P0 guest is absent**. A global "Hyper-V VM was created" event is not evidence that Office's exact `.wsb` was launched, and does not prove networking/mount denial or prevent host-admin forgeries.

The Office P0 pinned public WSB specifically maps **only** `C:\vf-public-input\run-public-smoke.ps1` as an executable script and specifies memory 2048 MB. Original WSB SHA256 `781c82ac2f426196c847ba32e0da9170985c7877953f144ddc992623200411ff`; original human-authored public guest script SHA256 `f216aa189f54900b4ba412508de69193d591a648611e1d862da1d067f22eb056`. Other guest activity using a path such as `C:\StudioInput\guest-runner.ps1` is not a substitute. Microsoft [Windows Sandbox configuration](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-configure-using-wsb-file) confirms mapped shares and logon command can be configured; that specification is not proof of live enforcement.

## New bounded read-only diagnostic pair

- `scripts/vf_office_v2_604_wsb_host_compute_probe.ps1` reads **only** `Microsoft-Windows-Hyper-V-Compute-Operational` IDs 2014 (VM create), 2007 (compute modification) and 2500 (compute-process creation) in a maximum 180-minute local host clock window. It reads the exact original *public* config/script SHA, and emits only sanitized UUID, record number, UTC timestamp and booleans for exact public logon path / 2048 MB modification. No event `Message`, other process command line, VM user secret or raw other-guest file is serialized. A complete-record max of 400 is explicitly flagged as truncated and denied. It never starts, stops or modifies Windows Sandbox, the original output, service, log, account, OS setting or Git. **It always exits 2** so calling it is not an admission signal.
- `scripts/vf_office_v2_604_wsb_etw_identity_gate.py` reads **only an explicit disposable AgentEnvelopeLab/p0-604-wsb-... JSON snapshot** with an exact allowlist of fields and required original WSB/script digests; `selftest` exercises 30 in-memory negative/overclaim controls. It requires any *observational* match to correlate (same compute UUID, increasing record IDs, 20-minute window) the VM-create event, 2048 MB change and expected public-command process. Even such a complete match returns **BLOCKED**, not attested; events can be copied, host SYSTEM controls the observation, and no authenticated interactive-user launch witness exists.

**PowerShell timezone failure preserved:** The initial disposable A1 collector incorrectly passed `UtcNow` to a `Get-WinEvent -FilterHashtable` query, which selected against Windows local time (Chris UTC+03). Original snapshot in `p0-604-wsb-host-etw-capture-20261011-a1/host-compute-public-metadata.json` SHA256 `4a5a701a091cd8687bc87ca800aa667a11e94d8f13d1462f21177f25d00e244b` included 21 apparent events but FAILED the new parser with `EVENT_TIMESTAMP_OUTSIDE_CAPTURE_WINDOW` / rc2. **This failure is authentic and retained, not rewritten.** The new collector uses `[DateTime]::Now` for `Get-WinEvent` filtering, and converts the start/end to ISO UTC only for durable output. See Microsoft's [Get-WinEvent reference](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.diagnostics/get-winevent).

## Real Chris Windows OS event observation

Fresh new **B1** capture, held only in a disposable local directory:
`D:\Velvet\Pilots\OfficeAccelerator\AgentEnvelopeLab\p0-604-wsb-host-etw-capture-20261011-b1/host-compute-public-metadata.json`

- Window UTC `2026-10-11T04:47:50.8890402Z` through `2026-10-11T07:47:50.8890402Z`, original WSB and script SHAs rechecked, original output count **0**.
- Actual host event channel: **227** sanitized records; **16** separate compute-system UUIDs; **16** VM-create events, **134** process-create observations, with the remainder settings updates; not truncated.
- Exactly **0** process observations invoking the Office public guest path; exactly **0** observations matching Office's specified 2048 MB change. Other environments' Hyper-V activity is not mapped onto Office's expected guest.
- Collector status `UNTRUSTED_READ_ONLY_HOST_COMPUTE_METADATA`, deliberately exit2; unique B1 capture SHA256 `42f405735207dec0a81aa866792af7b54c602d845e3f13824f324f577761d822`.
- New independent Python gate on the exact B1 bytes: `BLOCKED_ONLY_UNRELATED_VM_COMPUTE_EVENTS`, exit2, **0** observational matches, guest admission FALSE, guest session proof FALSE.
- Portable selftest **30/30 PASS** independently on Chris Windows Python 3.11 and MacMiniOffice Python 3, same Git branch source hashes; test PASS means the 30 malicious/synthetic cases were refused as designed, *not* VM admission.
- Snapshot remains host-owned, synthetic/public scoped, and therefore **is not a signing-key-independent origin proof** even when host events appear consistent.

The existing original public-only WSB remains the sole eligible Office fixture. Remote Desktop Commander runs as `NT AUTHORITY\SYSTEM` **Session0**, while Chris interactive console is Session1; no Session0 impersonation, token/ACL/security changes, new scheduler or user-session launch attempted.

## P0 security conclusion and exact next gate

This addition closes one **false-positive class**: rejecting someone else's VM events as a witness for Office. It does *not* turn a host event log into a trusted, independently correlated User-Session1 launch receipt, does not show guest filesystem/network denials, and provides no hypervisor/kernel attestation. A real interactive attended run of the exact pinned Office public WSB must be authorized and observed independently, with bounded response/exit/readback and an explicit unknown status on lost ACK. #612 generated-source execution remains refused. #604 exclusive Git Sink (host/daemon principal, real provider epoch/CAS, native GitHub effect fencing and UNKNOWN reconciliation) remains RED.

**Disallowed remains disallowed:** no Codex CLI, paid model API, source-model execution on unisolated hosts, Git writer/production secret in a worker, Windows security weakening, reboots, printers, publishing, customer files or production effects.
