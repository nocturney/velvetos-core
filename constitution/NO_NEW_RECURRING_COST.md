# NO_NEW_RECURRING_COST

Status: CANONICAL COST AUTHORITY

VelvetOS defaults to zero new recurring cost. A useful capability is not permission to create a new subscription, paid plan, billing account, usage-based workload, auto-renewing trial, paid resource, or other recurring charge.

## 1. Objective and default

The default target is zero new recurring cost. Prefer capabilities already available locally, self-hosted, or already paid for with proven zero incremental cost. Cost is a hard execution gate, not a post-hoc reporting field.

## 2. Scope

This law applies before installing, connecting, authenticating, provisioning, enabling, upgrading, calling, scheduling, or routing work through any component that can create recurring or usage-based cost. It applies to tools, APIs, models, SaaS plans, cloud resources, storage, databases, workers, queues, automation products, trials, hosted inference, and equivalent external capabilities.

## 3. Definitions

"New recurring cost" means a charge that can repeat because a capability remains enabled or because the workload continues. "Incremental cost" means extra spend attributable to the proposed workload even when the provider or plan already exists. "Explicit owner approval" means a specific approval for the concrete provider, plan/workload, billing model, scope, and expected recurring exposure; generic approval to use a tool is not cost approval.

## 4. Cost classifications

Every cost-sensitive component must be classified as exactly one of:

- FREE_LOCAL — runs on already-owned local resources without a new paid service.
- FREE_SELF_HOSTED — self-hosted without a new recurring vendor charge.
- EXISTING_PAID_CAPABILITY — already paid for and the proposed workload is proven not to increase the bill.
- FREE_TIER_LIMITED — no charge only while a quota or allowance is respected.
- PAID_OPTIONAL — the required path can remain free, while optional paid features exist.
- PAID_REQUIRED — the required path creates a paid or recurring charge.
- COST_UNKNOWN — billing behavior or incremental cost is not proven.

## 5. Fail closed

PAID_REQUIRED and COST_UNKNOWN are blocked by default. Unclear pricing, missing quota information, unclear overage behavior, ambiguous account ownership, or unknown billing linkage must be treated as COST_UNKNOWN. Do not infer "probably free" from a marketing page, an existing login, a successful API response, or the absence of an immediate charge.

## 6. Explicit owner approval contract

A cost exception is valid only when the owner explicitly approves the concrete action and the evidence records: provider, product or plan/workload, billing model, expected recurring cost or exposure, billing period or usage basis, scope, any hard cap or quota control, and an approval note tied to this action. Approval for one provider, plan, workload, or limit does not transfer to another.

## 7. Cost preflight timing

Run cost preflight before any install, connection, credential setup, billing-capable authentication, first paid-capable API call, production deployment, scheduled workload, resource provisioning, or change that can alter billing. A preflight result is evidence for a specific action; it does not permanently bless the provider.

## 8. Installation and connection

Do not install or connect a component merely because installation itself is free. Determine whether normal use, required plugins, hosted control planes, storage, egress, model calls, or later activation can create recurring cost. If the cost path is not proven safe, block before connection.

## 9. Credentials and billing accounts

Creating or attaching a billing account, payment method, paid API key, metered project, credit commitment, or equivalent billing-capable credential is a cost-sensitive action. It requires a passing preflight and, when paid or uncertain, explicit owner approval.

## 10. Paid-capable API calls

The first call to an API that can bill by request, token, image, minute, compute, storage, bandwidth, or another usage unit is a cost gate. Existing credentials do not authorize paid usage. Prefer a local, self-hosted, or already-paid zero-incremental-cost route when it can satisfy the task.

## 11. Free-tier limited services

FREE_TIER_LIMITED is acceptable only when quota evidence is current and automatic paid overage is impossible or a meaningful hard cap prevents charge. If overage can bill automatically and no hard cap is enforced, explicit owner approval is required before production use.

## 12. Trials

A trial that can auto-renew, convert to paid, require a payment method, or create a paid resource is not treated as free. Prefer a non-renewing free path. Any auto-renewing or conversion-capable trial is blocked without explicit owner approval and a recorded cancellation/expiry control.

## 13. Usage-based workloads

Metered workloads must have a known billing unit, a bounded workload, and a hard or operational cap where the provider supports one. "Low expected usage" is not a cost control. Scheduled or autonomous workloads require stricter bounds because repetition can multiply spend.

## 14. Existing paid capability

EXISTING_PAID_CAPABILITY is allowed without a new cost exception only when incremental_cost_possible is explicitly false and supported by evidence. If the workload can raise the bill, consume paid credits that replenish for money, trigger a higher tier, or create overage, it is not zero-incremental-cost and requires explicit approval.

## 15. Paid optional features

PAID_OPTIONAL may proceed only with paid_features_enabled=false for the proposed path. If a paid feature is needed or enabled, reclassify the action and run the corresponding approval gate. Do not silently turn on premium features to improve quality or convenience.

## 16. Local and self-hosted resources

Ordinary use of already-owned CPU, GPU, RAM, disk, and network is not treated as a new recurring vendor cost. Prefer this route when quality, reliability, and operational simplicity are acceptable. Unusually resource-intensive workloads should still record expected local resource impact and storage growth so "free" does not hide material operational burden.

## 17. Tool and model routing preference

When multiple routes can satisfy the task, prefer in this order: FREE_LOCAL; FREE_SELF_HOSTED; EXISTING_PAID_CAPABILITY with proven zero incremental cost; FREE_TIER_LIMITED with effective hard controls; PAID_OPTIONAL with paid features disabled. PAID_REQUIRED and COST_UNKNOWN are last-resort blocked states until explicit approval exists.

## 18. Failover and fallback

Failover must preserve the cost boundary. A local/free failure does not authorize a hosted or paid replacement. First seek another zero-new-recurring-cost route, reduce scope safely, or return a concrete blocker. A paid fallback may be used only after its own preflight and required approval.

## 19. No silent cost escalation

Never change model tier, provider, hosting mode, storage class, database plan, retention, concurrency, polling cadence, scheduled frequency, or another billing-relevant setting in a way that can increase recurring cost without a fresh cost decision. Quality or reliability improvements do not override this law.

## 20. Evidence, logging, and monthly drift review

Record classification, evidence source, date checked, recurring-cost assessment, quota/overage controls, approval reference when required, and the resulting decision. External or cloud-connected components require a monthly cost-drift review: confirm the plan, free-tier rules, overage behavior, workload, and incremental-cost assumption still match the recorded preflight.

## 21. Emergency exceptions, forbidden assumptions, and enforcement

An emergency does not create automatic cost authority. If a paid action is genuinely necessary, obtain the same explicit owner approval and record the exception. Forbidden assumptions include: "we already have an account, so it is free"; "the first call is probably free"; "credits are available, so spend is authorized"; "the free tier will be enough"; "a trial is free"; and "failover may use any provider". Enforcement is fail-closed through packages/vfharness/cost-policy.json, scripts/vf_cost_preflight.py, scripts/check-no-new-recurring-cost.py, office/control/POLICY.md, and the harness sensor registry.
