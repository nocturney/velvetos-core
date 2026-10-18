# Office #604: typed desktop capability eligibility — synthetic-only contract v0

**Status:** LAB DESIGN ONLY. Not an app bridge, controller, scheduler, lease issuer, authorizer, production service or permission to act. Office Phase 0/2 #604 owns comparative Desktop Runtime design. #612 P0 has precedence, #602 owns Cua-only diagnostics, and VelvetOS Core is the sole canonical task/lease and authorization authority.

## Purpose
A provider may advertise an operation through `native_api`, `named_accessibility` or `visual_replay`. That is NOT permission to execute it. A real runtime provider must authenticate and independently recheck app/version, OS principal/session, host/session lease, PID plus process-start identity and exact window, observation freshness, operation/effect scope, uncertain-effect state, and a verifiable postcondition.

The adjacent JSON has an imaginary Notes app, synthetic OS principal, fixed test clock, dummy lease and no customer content. The no-side-effects checker can only return `ELIGIBLE_SIMULATION_ONLY`; it never calls a model or application. A future real provider must acquire a genuine authoritative Core lease; it cannot trust a fixture's `lease.granted=true` claim.

## Negative contract
- Native application API/CLI/MCP is normally preferred, named UIA/macOS AX second, visual/replay fallback third; benchmark task-specific outcomes, not an assumed universal winner.
- Reject wrong app/version, wrong host or session, stale UI observation, foreign/reused PID, wrong process-start nonce and wrong window identity.
- Host SYSTEM Session 0 never stands in for an ordinary Windows interactive user session. Never run model-sourced code as host SYSTEM.
- Missing/wrong-owner/stale-epoch lease and unsupported operation or route deny eligibility. No competing scheduler or lease owner.
- Do not automatically replay UNKNOWN external effects; reconcile via independent evidence first.
- A named independent verifier plus expected target is necessary even for synthetic eligibility. Issued clicks or a positive route match are not success evidence.
- Customer sends, publishing, money, physical/printing, credentials, paid models, new apps/services and real computer-use effects remain separately authorized gates.

## Deterministic no-effect QA
Run `python3 docs/implementation/office-v2/phase2/desktop-runtime-eligibility-check-v0.py` from the repo root. The pure stdlib test checks 69 positive/negative cases (31 original plus 38 additional denials); no desktop, browser, WSB, provider, network, account, model, service or scheduler is invoked. Do not count a synthetic PASS as real UIA/AX/Windows SID proof. `scripts/check-desktop-runtime-eligibility.py` is the check-all guard for this synthetic matrix, including a duplicate-id negative control (`DUPLICATE_CASE_ID`). It is not a production adapter and does not replace established Phase 2 sensors.


## Malformed-input negatives added after independent review

This synthetic-only checker now rejects malformed nested objects and scope arrays, missing/blank or wrong-type host/session/app/task identities, nonpositive/bool lease epochs, invalid process PID/start/window identity, boolean/negative UI timestamps, unsupported session kinds, and blank postcondition fields. Equality of two missing, false or blank values must **never** count as verification. The original 31 deterministic cases remain unchanged; 38 new denial fixtures extend the matrix to 69. Tests also run under `python -O`, and five separate source mutation probes must be caught. All results remain simulated and do not attest a genuine Core-issued lease, independent window/SID identity, signed provider code, verified postcondition, nor runtime authorization.

## Future separate pilot
Require independently verified idle user-session host/GUI lease and #612 noninterference; compare native, named accessibility and visual/replay on the same fixture across at least two real harmless apps including a non-editor. Measure exact postconditions, false-success, UI drift, crash/UNKNOWN recovery, p50/p95 latency and rollback. Reuse #602 evidence; retain all external effect and production gates.
