# Scenario: content-live

Existing office orchestrator pattern only — no second runtime. Crew: [`../crews/content.md`](../crews/content.md). Creative control: `packages/vfom/CREATIVE-AUTOPILOT.md`.

## Graph

```mermaid
flowchart LR
  P[real opportunity / print.done / media.verified] --> A[creative.plan]
  A --> G{critical media present?}
  G -->|no| SR[shotRequest / waiting_for_media]
  G -->|yes| EDL[edit.plan]
  EDL --> C[cover + copy]
  C --> QA[Visual OS + Rubric + policy + PREFLIGHT]
  QA -->|fail quality| FIX[auto-fix]
  FIX --> QA
  QA -->|pass| AU{standing authorization?}
  AU -->|yes| AP[authorized_for_tool_publish]
  AU -->|no| HA[pending human authorization]
  AP --> PUB[vfigos publish tool]
  HA --> PUB
  PUB --> V{receipt + live evidence?}
  V -->|yes| DONE[published_verified]
  V -->|no| D[Degraded + failover packet]
```

## Laws

- Missing physical media = one precise shot request; no invented bed/product scene.
- Routine hook/cover/cut/caption choices are autonomous.
- Quality failure loops internally; it does not become an owner task.
- Standing authorization is instance-scoped and never covers ₪, Boost/Ads, auto-DM, customer WhatsApp, Print, unclear rights or private customer/CAD material.
- Feed cadence remains `vfgrowth/CALENDAR.md`; no invented schedule.
- No publish claim without tool receipt and verification evidence.

## Outcomes

- `published_verified` — tool receipt + live evidence.
- `ready_for_publish` — gates pass but publish tool unavailable; failover packet exists.
- `waiting_for_media` — exact shotRequest exists.
- `human_required` — named constitutional/business gate only.
