# Office v2 Phase 3B — Identity / Authorization / Credential Broker

Status: **CONTRACT V0 FROZEN / ALL THREE LANES LAB SMOKES PASS / DESTRUCTIVE FIXTURES PENDING / NO WINNER / NO PRODUCTION AUTHORITY CHANGE**

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

Current shortlist is research-only. Exact versions, immutable pins, license/maintenance/security review, resource plans and teardown/rollback evidence are required before ADMITTED-to-LAB promotion.

Production credentials and production authority remain forbidden in LAB.

## Admission research

Immutable NODE-A pins are frozen in runtime-pins-v0.json. Eight challengers pass the Phase 2 CANDIDATE→ADMITTED research gate and may proceed to isolated LAB smoke: ZITADEL, Keycloak, authentik, OpenFGA, OPA, Cedar, Infisical and OpenBao.

Owner decision 2026-10-06 resolves the prior ZITADEL licensing defer: AGPL obligations are accepted for the separate-service/API architecture, and modifications to ZITADEL itself may be open-sourced if required. ZITADEL completed isolated LAB smoke successfully; this does not grant production authority or select a winner.

Admission is not LAB validation, winner selection, SHADOW, PILOT or production promotion.

## LAB admission smokes

Authorization lane admission smoke is PASS for OPA, OpenFGA and Cedar. The run used only synthetic inputs; OPA/OpenFGA had no host-port bindings, Cedar used the checksum-verified official 4.13.0 CLI asset, and teardown removed candidate containers/network before lifecycle promotion to LAB.

Identity lane admission smoke is PASS for ZITADEL, Keycloak and authentik. All used synthetic service identities only, no production credentials, and no raw token/secret material in receipts. ZITADEL used an internal-only network with no host-port bindings and proved bootstrap identity, service-account creation, client-credentials issuance, wrong-secret denial, deletion and deleted-identity denial. Keycloak proved client-credentials issuance plus wrong-secret and deleted-client denial; authentik proved client-credentials issuance plus wrong-secret denial and token revocation.

Credential-broker LAB smoke is PASS for both Infisical's core/community path and OpenBao. Infisical used only synthetic machine identity and secret material on an internal-only network with no host-port bindings; it proved scoped read, unrelated-project denial, viewer write denial, client-secret rotation, revocation of the old secret and its issued token, survival of the rotated credential, and full denial after identity deletion. Agent Vault / Enterprise-only features were not assumed. OpenBao used synthetic AppRole credentials on an internal-only network with no host-port bindings and proved scoped read, unrelated-secret denial and token revocation. No LAB smoke selects a winner or grants SHADOW/PILOT/production authority.
