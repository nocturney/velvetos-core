# Office 2.0 P0 — Windows Sandbox guest-receipt origin gate (#604)

**2026-10-11 | Scope:** public synthetic Windows Sandbox fixture only. No actual Windows Sandbox guest has been launched or independently witnessed by this work. No model-generated source, credential, production writer, account, ACL, firewall, Defender, UAC, reboot, printer, customer or publishing action was performed.

## Canonical reason for the gate

A guest receipt written to a directory mapped as writable from the host is **untrusted evidence**, even if the receipt includes the expected nonce, public source hash and claimed input/network denials. A host process can write the same JSON without creating a guest. The inherited verifier returned `PASS_SYNTHETIC_ATTENDED_GUEST_SMOKE_NOT_GENERAL_CODE_ADMISSION` with exit 0 for this forged output. A `PASS` that describes static configuration or syntactically correct guest fields **must not** be interpreted as VM execution or OS isolation.

See [#604 receipt-origin security-negative comment](https://github.com/nocturney/velvetos-core/issues/604#issuecomment-6106561927) for the exact original negative evidence. This is a real **verification-origin false acceptance**, not a VM escape.

## Windows observations (each clone is separate)

| Probe | Result |
| --- | --- |
| Original trusted LAB `p0-604-wsb-attended-smoke-20261011-a1` | Config SHA256 `781c82ac2f426196c847ba32e0da9170985c7877953f144ddc992623200411ff`; human-written script SHA256 `f216aa189f54900b4ba412508de69193d591a648611e1d862da1d067f22eb056`; output empty; guest **NOT** launched |
| Negative clone `p0-604-wsb-untrusted-receipt-negative-20261011-b1` | An explicitly host-forged guest JSON (SHA256 `6c3e80bb61d8d07994dacfae964acc53fabf88510b0373991781fbbb877d75a0`) caused the old path-adjusted verifier to report attended-guest PASS, rc0 |
| Hardened clone `p0-604-wsb-receipt-gate-hardening-20261011-c1` | Original public input source remains byte-identical; hardened PowerShell verifier with empty output reported **STATIC ONLY**, rc0; with the same forged guest JSON it reported `BLOCKED_UNTRUSTED_GUEST_RECEIPT_ORIGIN_NO_HOST_WITNESS`, rc2 |

All three paths are beneath `D:\Velvet\Pilots\OfficeAccelerator\AgentEnvelopeLab`, with unique directories. The original LAB and the previous negative evidence were **not** modified. Chris Remote Desktop Commander executes as `NT AUTHORITY\SYSTEM` in Session 0; interactive Chris Session 1 is separate. The live guest was not started through SYSTEM.

## New portable negative-admission check

`scripts/vf_office_v2_604_wsb_receipt_origin_gate.py` is a **trusted human-authored**, standalone, cross-platform read-only verifier for this fixed *public* challenge shape. It deliberately has no success path for guest admission. It accepts:

- `selftest`: 18 bounded in-memory offline controls: empty receipt, six false-witness/host-forgery shapes, ten malformed/scope violation cases, and one privileged challenge denial.
- `inspect --root <explicit disposable AgentEnvelopeLab/p0-604-wsb-... path>`: read-only challenge/source SHA and output inventory checks; any presence of a syntactically valid guest report yields `BLOCKED_UNTRUSTED_GUEST_RECEIPT_ORIGIN_NO_HOST_WITNESS` and exit 2. Missing output also exits 2 for lack of guest proof. Invalid receipts fail closed.

The gate **never** creates a VM, executes received code, reads repository credentials, opens a listener, runs a model, emits an external effect, or promotes a worker. If the guest JSON claims an "attested" launch, the gate still rejects the claim because host-writable JSON is not an independent witness.

The existing local PowerShell verifier was modified **only in the separate hardened clone** for the negative test; its original trusted LAB copy remains unmodified. Until the local consumer is explicitly routed through a trusted witness adapter, **the old PowerShell PASS must not be used for VM admission**. The new repo gate and contract selftest establish a regression barrier but do not silently reconfigure a deployed consumer.

## Admission still required

1. A genuine attended Windows Sandbox launch under the authorized Chris **interactive Session 1**, using a public synthetic challenge with pinned config/script and no production mounts/credentials. Do not use SYSTEM Session 0 token/session delegation.
2. An **independent, trusted host-side launch witness**, correctly scoped in time and identity to the fresh guest, separate from the guest-writable public-output directory. Even a host process observation alone is not cryptographic VM/kernel attestation.
3. Independent readback of actual guest results, nonce, source bytes, readonly mount denial and bounded no-network behavior; explicit uncertainty after lost/ambiguous launch ACK.
4. A separate low-trust generated-code execution admission path and independent QA; keep #612 local untrusted Worker entrypoints fail closed until proven.
5. **Separate #604 Git Sink authority proof**: credential holder must be isolated from Worker and daemon-owner; current GitHub stale-epoch write admission, crash/lost ACK reconciliation and exactly-once recovery remain RED.

**Security verdict:** #604 stays OPEN / RED; #612 remains PARTIAL. Offline refusal tests are **not** Windows Sandbox acceptance.
