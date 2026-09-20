# VF Project 6.6.3 — current-chat attachment source ingest

## Trigger
Cold-start 6.6.2 saw current-request product images in ChatGPT, but creative execution stopped because the repo preflight required workspace-relative PRODUCT_SOURCE files and hashes. The attachment bytes and repository executor can live on different filesystems.

## Goal
Preserve fail-closed Product Truth evidence while making a normal cold-start request with current-chat product images executable without arbitrary folder searches or unhashed fallback.

## Architecture
1. `vf_source_ingest.py` accepts an explicitly named platform-local attachment file, verifies it is within the current-request intake root, decodes it as media, copies exact bytes into the chat execution workspace, hashes it and writes an ingest receipt.
2. When attachment bytes and repo execution share a filesystem, the ordinary project preflight can use the ingested sources.
3. When they do not share a filesystem, `vf_chat_cold_start_preflight.py` runs beside the attachment bytes using the hash-verified Project bundle + ingest receipts + inspected plan. It can authorize creative production only and can never authorize publication.
4. Every PRODUCT_SOURCE in publication evidence must be backed by an exact source_ingest receipt bound into source_lock.
5. 6.6.2 creative-master materialization remains required after source-grounded editing.

## Safety / fail-closed rules
- No arbitrary user-folder scanning.
- External paths require an explicit intake root scoped to the current request.
- No URL download in the source-ingest bridge.
- No creative transformation during source ingest.
- No unhashed visual-memory fallback.
- Do not pass chat-local paths to a remote preflight that cannot read them.
- If exact attachment bytes are genuinely unavailable after the platform-local path and one supported explicit handoff are exhausted, return ATTACHMENT_BYTES_UNAVAILABLE.
- Chat-local preflight never authorizes publication or Instagram mutation.

## Acceptance
- Contract 6 / Revision 6.6.3 / VF-PROJECT-6.6.3-CHAT-ATTACHMENT-SOURCE-INGEST.
- Two current-chat product images can be exact-byte ingested and represented as one source set.
- A plan using SAME_FRAME_CROP + ALTERNATE_VERIFIED_SOURCE passes the chat-local creative gate.
- Source identity drift, missing receipts, unbounded external intake and tampering fail closed.
- Project preflight/router recognize the chat-local gate without weakening delivery authorization.
- Existing 6.6.2 master-materialization and all prior Product Truth/reference/CTA/brand rules remain active.
- Full VelvetOS Core Sensors pass before merge.
