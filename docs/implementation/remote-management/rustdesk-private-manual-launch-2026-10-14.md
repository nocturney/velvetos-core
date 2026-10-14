# Interim private RustDesk native-launch viewer — acceptance and limits

Date: 2026-10-14
Status: **code verified; real user click untested; CortenDesk runtime still blocked**
Parent: [Draft PR #717](https://github.com/nocturney/velvetos-core/pull/717)

## Why this exists

The full management target remains **CortenDesk** with its bundled server.
A container smoke test of CortenDesk was previously rejected by the remote
execution safety gate. During that gate, the solo operator can still use
existing RustDesk 1.5.0 native clients and the verified stock OSS peer list.
This adds a **manual native-client entrypoint** to the standalone *private*
MacMiniOffice2 registration report rather than cloning CortenDesk or
modifying the approved VelvetOS Control Center architecture.

## User-facing behavior

The operator can open a **local owner-private HTML file**, search six
registered IDs, copy them and optionally click **"פתח ב־RustDesk"**
(Open in RustDesk). Each link has a fixed native URI scheme and a
case-preserving URL-encoded ID path component:

    rustdesk://connection/new/<encoded-registered-device-id>

This source-backed route is recognized by RustDesk 1.5.0
`flutter/lib/common.dart`. Windows registry protocol association was
observed on 3/3 Windows hosts, and the RustDesk macOS app bundles declare
the `rustdesk` protocol on 3/3 Macs; **actual clicking** and macOS
LaunchServices default association remain untested. The browser may ask
permission to open the installed RustDesk app. No credentials are stored in
the HTML and the app's own authentication/connection flows remain unchanged.

## Explicit safety design

- CLI requires both `--registry-db`, `--allow-live-local-read` AND
  `--enable-native-connect`; there is no implicit remote action.
- Fake data, offline snapshots, malformed/unsafe IDs and default private
  registry reports do not expose a native-connect link.
- No browser requests, socket calls, reload timers, hidden iframes,
  automated URI navigation or remote-control APIs are used by the viewer.
- Local report remains under an owner-only directory and is created with
  exclusive `0600` permissions; no overwrites or Git worktree outputs.
  A report contains **real device IDs**; do not commit, host, upload or share.
- The file still reports every device's presence `UNKNOWN` and last-seen
  `null`. Neither a registered ID nor a clickable link is proof the
  device is online.
- This is an opt-in *local client launch shortcut*, not in-browser remote
  control. No change to `hbbs/hbbr`, existing RustDesk client settings,
  Colima, ports, signing keys or CortenDesk runtime.

## Deterministic verification

The additional `tests/test_native_launch_preview.py` exercises:
two independent opt-ins, fixture/snapshot rejection, fail-closed git-root
protection, output privacy, path escaping, script-injection prevention,
no overwrite, and local HTML data. A Node VM
`tests/native_launch_dom_check.js` simulates rendering and verifies
that links are created only in the correct mode; exact mixed-case ID is
preserved in the path; and no automatic navigation is invoked.

Expected total after this addition: **111** existing plus new
unit/localhost/DOM cases. Re-run against the exact resulting PR head and
the existing Core/policy/README sensors.

## Mac production-data trial (separate one-shot step)

Keep all real identifiers exclusively on MacMiniOffice2. Refresh the private
Mac-installed `render_preview.py` and `preview/template.html` using exact
pinned reviewed branch blobs, without moving the live database.
Create **a new** timestamped HTML report under
`~/Library/Application Support/VelvetOS/RustDeskPilot/2026-10-14/private/`
using the documented CLI, not a background timer or autostart mechanism.

Verify *locally* via the embedded report data that there are six registered
IDs, each with unknown presence, `native_connect=true`, and the private
file has `0600` permissions. Do **not** print or export real IDs.
If Node is available, the VM DOM contract can validate link construction
locally without calling the URI handler.

Only after explicit manual interaction may the operator claim actual
OS-level connection support. A successful local UI render is not a
CortenDesk deployment, a live connection, or production readiness.

## Next full CortenDesk integration gate

Wait for an authorized independent runtime (not a workaround to the earlier
denial). Build/use pinned CortenDesk with the already verified deep-link
patch or an upstream-fixed release, enroll a disposable client into the
bundled `hbbs/hbbr`, validate authenticated browser session, file transfer,
and truthful presence, then determine if any live-client migration is
warranted. Retain the original RustDesk server and clients untouched until
these gates are independently completed.

## Verified UI copy gate

The new operator-facing Hebrew action/explanation strings were checked as
`surface=ui-microcopy`, `tier=FINAL_INTERNAL`, `language=he` using the
canonical `scripts/vf_visible_text.py --gate` workflow after truth/context
review, reader-first review and local DOM/UI QA. Result: **PASS**; candidate
`text_sha256=5aa57003b02b73fbbee4878afb084999dcccd9907bdd882055017bdaa1c93069`.
This represents the inspected action and explanation strings, not a general
authorization for runtime changes, auto-connecting or externally published
copy. The `check-visible-text-gate.py` repository sensor passed separately.
