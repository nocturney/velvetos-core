# ChatGPT Scheduler Contract

Current owner-facing scheduling authority is ChatGPT automations in Asia/Jerusalem.

Only three recurring jobs are active: Cognee Memory Sync once daily around 11:30 (flexible), VelvetOS Office Loop at 18:30, and Runtime Receipts Refresh at 19:15. Velvet Morning Brief is manual/event-driven only.

Grokbot is not a scheduler, routine manager, guard, retry layer, or receipt-maintenance authority. Its known routines are paused and it remains available only on demand.

Research is not a standing broad recurring job. Research starts from a concrete decision or an Office v2 gate that still needs evidence.

Retry, health, observability, and evidence generation should be behavior of the workflow/runtime that needs them, not separate owner-facing cron jobs.

Runtime proof must never fabricate a ChatGPT provider receipt. The historical Grok readbacks remain immutable historical evidence. Current runtime proof is dependency-scoped and does not require grok-production-scheduler.
