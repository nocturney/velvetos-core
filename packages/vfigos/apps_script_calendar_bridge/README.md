# VelvetOS Instagram Calendar Bridge

One-way operational mirror from Cloudflare Publisher to the owner's Google Calendar.

## Contract
- Source of truth: Cloudflare Publisher D1.
- Target calendar: secondary calendar named `אינסטגרם` owned by `nocturney@gmail.com`.
- Timezone: `Asia/Jerusalem`.
- Calendar edits never mutate a publication job.
- Sync cadence: every 5 minutes.
- Events are transparent and have reminders disabled.
- `cancelled` removes the mirror event; other terminal/active states update the same event.
- The publisher control token is stored only in Apps Script Properties after bootstrap.

## Bootstrap security
The script source stores only SHA-256 of the random Publisher control token. Bootstrap accepts the real token only when its SHA-256 matches, then stores the token in Script Properties. The token itself must never be committed.

## One-time owner authorization
The Apps Script project requires:
- Google Calendar
- external request (read-only fetch from Publisher)
- Apps Script trigger management

Run `authorizeCalendarBridge` once as the owner, review the requested scopes, then bootstrap. After bootstrap, the time-driven trigger runs without ChatGPT or the local PC.

## Health
The web app GET response exposes only non-secret operational fields: calendar name/id, last sync, and authorization state. Morning Green may use those fields to report mirror drift, but Calendar health never overrides Publisher schedule truth.
