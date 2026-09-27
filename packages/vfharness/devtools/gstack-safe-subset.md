# gstack safe subset — pattern embed only

Canonical source: https://github.com/garrytan/gstack
Pinned source: `01593aa67c94780528e8f5121e47362502410ced`

VelvetOS does **not** run the gstack runtime. The upstream package contains its own onboarding,
telemetry, memory/GBrain and release machinery, so installing it wholesale would violate the
single-authority and minimum-complexity rules.

## Allowed subset

| gstack surface | VelvetOS mapping |
|---|---|
| review | `packages/vfharness/playbooks/critique-review.md` + deterministic diff/sensors |
| qa | existing package sensors + `verification-before-claim.md` |
| investigate | `systematic-debugging.md` |
| careful | `implementation-discipline.md` |
| freeze | stop scope expansion; preserve branch/diff while investigating |
| guard | existing authority/security/cost gates |
| document-generate | existing docs/templates; no alternate document authority |

Use the upstream material as development guidance only. Existing VelvetOS playbooks and
sensors remain authoritative.
## Explicitly disabled

- GBrain and any brain-sync/memory path.
- `ship`, `land-and-deploy`, `setup-deploy` and any independent release flow.
- gstack telemetry/onboarding runtime.
- browser/session orchestration as a replacement for existing tools.
- any model/provider call that can create incremental cost.

## Acceptance rule

A gstack-derived change is acceptable only when it:
1. maps into an existing VelvetOS pack/playbook;
2. keeps existing approvals, receipts, schemas and fail-closed behavior;
3. does not become a required runtime dependency;
4. remains removable without disabling VelvetOS;
5. passes the normal deterministic sensor for the changed surface.

The deterministic Phase 4 sensor checks both the allowlist and forbidden-capability denylist.
