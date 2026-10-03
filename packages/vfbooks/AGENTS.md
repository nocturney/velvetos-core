# vfbooks — local finance/books guide

Scope: payments, invoices, bookkeeping projections and finance evidence.

- Read `SKILL.md` and only the authoritative finance source needed for the request.
- Missing amounts/statuses remain unknown; never infer payment, debt, invoice state or revenue from memory.
- Cost/spend authorization belongs to `policy_id: cost.recurring.new`; bookkeeping evidence cannot authorize spend.
- Sale-price/commitment authority stays separate from bookkeeping records.
- External provider mutation requires the canonical effect policy + provider receipt/readback before claiming success.
- Keep provenance and timestamps on financial observations.

Verification: `python3 scripts/check-vfbooks.py` when present and the routed finance sensor set.
