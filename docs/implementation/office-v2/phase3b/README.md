# Office v2 Phase 3B — Identity / Authorization / Credential Broker

Status: **CONTRACT V0 FROZEN / CROSS-ROLE COMPOSITION PASS / PRIMARY: ZITADEL + OPA + OPENBAO / INTEGRATION WIRING PASS / PERSISTENCE RESTORE PASS / RUNTIME READINESS PASS NOT ACTIVATED / EXACT REGRESSION PENDING / NOT SHADOW / NO PRODUCTION AUTHORITY CHANGE**

Phase 3B treats security as three explicit roles rather than forcing one product to own identity, authorization and secrets:

1. **Identity provider** — authenticates service/workload principals and emits verifiable claims.
2. **Authorization/policy engine** — makes the canonical ALLOW/DENY decision and emits a correlated decision receipt.
3. **Credential broker** — returns only exact-scope credential material after identity and policy gates pass.

Authentication never implies authorization. Secret existence never implies authorization. A policy engine may not become a secret store. Evidence may contain IDs/hashes/metadata but never raw secrets, bearer tokens or private keys.

## Frozen gate

Before any production-adjacent PILOT, the selected composition must prove:

- deny-by-default;
- explicit service identity;
- exact scoped credentials;
- effective revocation;
- policy-decision receipts;
- no unrelated secret exposure;
- no raw secret material in evidence;
- cross-scope isolation;
- fail-closed dependency outage;
- operator inspection;
- acceptable backup/upgrade/rollback.

## Benchmark strategy

Each sublane is benchmarked independently using neutral LAB stubs for the other two roles. Only the lane winner/fallback combinations proceed to the shared 20-step composition fixture. This avoids a brute-force Cartesian bake-off while still proving the selected products interoperate safely.

The shortlist has now completed admission, per-lane destructive validation and the shared Stage B composition gate. Exact pins and lane verdicts remain frozen; production credentials and production authority remain forbidden in LAB.

## Shared Stage B composition

The frozen 20-step fixture passed in four selected compositions, without Cartesian exhaustion:

- **Primary:** ZITADEL + OPA + OpenBao — PASS 20/20.
- **Identity fallback swap:** Keycloak + OPA + OpenBao — PASS 20/20.
- **Authorization fallback swap:** ZITADEL + Cedar + OpenBao — PASS 20/20.
- **Credential fallback swap:** ZITADEL + OPA + Infisical — PASS 20/20.

All four receipts are LAB-only, use synthetic credentials/material, expose no host ports, record no raw bearer/secret material, and prove fail-closed dependency behavior. The primary composition is selected for integration because it preserves the already selected lane winners while each one-at-a-time fallback has independently proven interoperability under the same fixture.

`composition-gate-verdict-v0.json` is the canonical Phase 3B composition receipt. This closes the architecture/composition gate only. It does **not** grant SHADOW, PILOT or production authority, and `CURRENT.json` remains at the Phase 3A closed / Phase 3B ready checkpoint pending a separate project-state promotion.

## Integration wiring — non-authoritative

`integration-wiring-v0.json` now freezes the normalized integration order as request intake → identity verification → claim normalization → authorization → exact credential-scope check → credential-resolution decision → effect gate → sanitized evidence. The selected component mapping is ZITADEL → OPA → OpenBao, with Keycloak, Cedar and Infisical retained only as explicit one-at-a-time rewires. Automatic fallback is disabled; a canonical DENY may never be retried against a fallback merely to seek ALLOW.

`scripts/vf_office_v2_security_wiring.py` is the executable reference for this contract. It is standard-library-only, imports no provider/network client, embeds no runtime endpoint, accepts only synthetic request metadata, rejects raw token/secret/private-key fields, and supports `validate`, `simulate` and `selftest`. Even the fully passing path returns `ALLOW_SIMULATION_ONLY`; `external_effect_allowed` is always `false`, and the script never resolves or emits credential material.

`promotion-gates-v0.json` keeps SHADOW explicitly blocked pending a separate promotion receipt plus persistence backup/restore drills, health/fail-closed probes, sanitized correlated evidence, service/rollback planning and an exact regression gate. PILOT and production are separately blocked after that. No production endpoint, credential class, writer, canonical store or external-effect authority is bound by the current wiring.

A wiring PASS therefore proves only **LAB_SIMULATION_ONLY integration semantics**. It does not change the Phase 0 authority map or credential trust classes, does not advance `CURRENT.json`, and does not grant SHADOW, PILOT or production authority.

## Persistence restore readiness

The selected primary composition has now also passed an isolated persistence/restore drill using only synthetic LAB state. OPA was backed up, replaced by a deny-only policy, restored and returned the expected ALLOW again. OpenBao used persistent integrated Raft storage: an offline backup was taken, a fresh empty volume returned the expected uninitialized state, the backup was restored into a new volume, the restored node returned sealed state, then unsealed and read back the synthetic secret successfully. ZITADEL used its pinned PostgreSQL substrate: a custom-format `pg_dump` was restored into a fresh empty Postgres instance and the same synthetic machine identity could issue a token again after restore.

Canonical evidence is `D:/Velvet/Artifacts/OfficeV2/phase3b/evidence/2026-10-06/persistence-readiness.json` with SHA256 `c8093f463c293d851109de73d1c60a688efc918ea719d782916bbfda2c752da7`. The final drill run `20261007T042934Z-218776` passed OPA policy restore, OpenBao Raft fresh-storage/restore/unseal/read, and ZITADEL PostgreSQL fresh-DB/restore/token issuance. All host-port bindings remained empty, no production credentials or secret material were used, and no raw key/token/secret material appears in the receipt. `shadow-readiness-v0.json` records this as a completed precondition only. SHADOW remains blocked on the exact regression/negative-control suite and a separate explicit project-state promotion receipt.

## Admission research

Immutable NODE-A pins are frozen in runtime-pins-v0.json. Eight challengers pass the Phase 2 CANDIDATE→ADMITTED research gate and may proceed to isolated LAB smoke: ZITADEL, Keycloak, authentik, OpenFGA, OPA, Cedar, Infisical and OpenBao.

Owner decision 2026-10-06 resolves the prior ZITADEL licensing defer: AGPL obligations are accepted for the separate-service/API architecture, and modifications to ZITADEL itself may be open-sourced if required. ZITADEL completed isolated LAB smoke successfully; this does not grant production authority or select a winner.

Admission is not LAB validation, winner selection, SHADOW, PILOT or production promotion.

## LAB admission smokes

Authorization lane admission smoke is PASS for OPA, OpenFGA and Cedar. The run used only synthetic inputs; OPA/OpenFGA had no host-port bindings, Cedar used the checksum-verified official 4.13.0 CLI asset, and teardown removed candidate containers/network before lifecycle promotion to LAB.

Identity lane admission smoke is PASS for ZITADEL, Keycloak and authentik. All used synthetic service identities only, no production credentials, and no raw token/secret material in receipts. The frozen 20-step destructive fixture is also complete for all three challengers: each proved identity issuance/verification, revocation, replacement identity recovery and dependency-outage fail-closed behavior. ZITADEL is selected as the identity winner for composition, Keycloak as fallback, and authentik as specialized reserve. This lane selection does not grant SHADOW, PILOT or production authority.

Credential-broker LAB smoke is PASS for both Infisical's core/community path and OpenBao. Infisical used only synthetic machine identity and secret material on an internal-only network with no host-port bindings; it proved scoped read, unrelated-project denial, viewer write denial, client-secret rotation, revocation of the old secret and its issued token, survival of the rotated credential, and full denial after identity deletion. Agent Vault / Enterprise-only features were not assumed. OpenBao used synthetic AppRole credentials on an internal-only network with no host-port bindings and proved scoped read, unrelated-secret denial and token revocation. No LAB smoke selects a winner or grants SHADOW/PILOT/production authority.
