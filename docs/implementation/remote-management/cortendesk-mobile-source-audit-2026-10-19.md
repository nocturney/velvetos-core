# CortenDesk v1.14.0 — independent mobile-browser source audit

Date: 2026-10-19
Scope: isolated CortenDesk research, NO Fleet Console integration.
Status: STATIC SOURCE VERIFIED / RUNTIME UNAUTHORIZED / SAFARI UNTESTED.

## Provenance and reproducibility

Official upstream: https://github.com/marcpope/cortendesk/tree/v1.14.0
Immutable Git tag commit: 2070d598d30cbaec207060a0fbef539ccf5d5d52.

A fresh, separate, public source-code checkout was created on Windows Chris
at D:\Velvet\Pilots\CortenDeskSourceAudit-20261019 in detached HEAD at the
exact tag commit. This is NOT a container install or a remote service.

From tools/rustdesk-pilot/ in the research worktree:

    python cortendesk_mobile_source_gate.py --source-root D:\Velvet\Pilots\CortenDeskSourceAudit-20261019

Observed state: PINNED_SOURCE_SIGNALS_PRESENT_NOT_RUNTIME.
10/10 selected source files matched the immutable release's Git blob IDs,
and 10/10 source-only feature signals were present. This command makes only
a read-only Git HEAD query and bounded exact-path source-file reads. It never
launches containers, connects to peers, changes users, or alters networks.

A Git source blob SHA-1 is not an OCI image SHA-256. The separately verified
v1.14.0 GHCR OCI digest is pinned in the staging manifest; source matches do
not establish that a runtime image contains the same bytes.

## Static source findings (none has live acceptance)

| Candidate source capability | Upstream file | Runtime result |
|---|---|---|
| Authenticated console/webclient route | routes/web.php | UNTESTED |
| Scoped device:r inventory endpoint | routes/api.php | UNTESTED |
| Web ticket and ws/wss endpoint selection | app/Http/Controllers/WebClientPageController.php | UNTESTED |
| WebSocket bridge to ports 21118 and 21119 | docker/nginx.conf.template | UNTESTED |
| Touch, drag, and long-press input | webclient/src/input/mouse-keyboard.ts | UNTESTED |
| Touch-mode UI and iPhone fullscreen caveat | webclient/src/ui/app.ts | UNTESTED |
| WebCodecs decoding negotiation | webclient/src/media/video.ts | UNTESTED |
| H.264 Media Source fallback | webclient/src/media/mse-video.ts | UNTESTED |
| Browser file picker/download fallback | webclient/src/ui/file-panel.ts | UNTESTED |
| iPhone viewport layout | resources/views/webclient.blade.php | UNTESTED |

## Security and Safari limits

1. The nginx /ws/id and /ws/relay paths are protocol proxies. They do NOT,
   by themselves, demonstrate session authentication. Public HTTPS/WSS access
   would require an independently approved, deny-by-default access boundary
   covering all paths and WebSocket upgrades, with expiry/reconnect tests.
2. Touch UI and H.264 MSE code do not prove usable decoding, gestures,
   keyboard, clipboard, or stability on real iPhone/iPad Safari.
3. Upstream explicitly handles iPhone Safari lacking element fullscreen.
   Windowed control can be accepted; full screen is not assumed available.
4. File-input fallbacks do not prove upload/download reliability on iOS Files.
   Test both directions and byte-for-byte hashes with disposable files.
5. A standalone console will not automatically ingest six live OSS RustDesk
   peers. A disposable 1.5.0 client must be enrolled in staging and observed.
6. The prior remote container-launch safety denial is still binding.
   This audit is not an execution approval and no alternate launch was tried.

## Local verification

- 14 new offline source-gate unit tests: PASS.
- Full RustDesk pilot Python suite: 160 tests, one platform skip, no failures.
- The actual upstream pinned clone: all 10 source blobs and signals PASS.
- No installation, OCI pull, CortenDesk listener, production configuration,
  credential, RustDesk client, Fleet Console, or public endpoint was changed.
- Fresh GitHub CI on the new PR head is a separate required check.

## Next permitted stage

A genuinely authorized, disposable isolated CortenDesk runtime is required
before localhost authentication checks, real relay/browser video and input,
file transfer, and subsequently authenticated HTTPS/WSS Safari tests over
cellular can occur. Existing RustDesk production must remain untouched;
do not merge the research PR on the strength of static evidence alone.
