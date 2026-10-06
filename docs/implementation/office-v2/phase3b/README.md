# Office v2 Phase 3B — Identity / Authorization / Credential Broker

Status: **CONTRACT V0 FROZEN / RESEARCH SHORTLIST ONLY / NO WINNER / NO PRODUCTION AUTHORITY CHANGE**

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
