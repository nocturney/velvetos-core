# Instagram failover

Purpose: preserve an owner-approved Instagram delivery window when OpenPost has definitively failed, without creating an unrestricted second publisher.

## Architecture

`grok_client.py` is the unprivileged GrokBot-facing client. It writes a short-lived request into the trusted spool and waits for safe JSON only.

`trusted_dispatch.py` is the single trusted consumer. It accepts manifests only from approved local roots and invokes `grok_instagram_failover.py`.

`grok_instagram_failover.py` performs the failover:

1. load an exact `velvet.instagram_failover.v1` manifest;
2. re-run the canonical Instagram send preflight and require `publishAuthorized=true`;
3. verify the exact package SHA and media CAS SHA;
4. query live Instagram first and stop `duplicate-safe` when the exact caption is already live;
5. query OpenPost through `openpost_failover_state.py`;
6. on `--execute`, require `safe_to_failover=true`: failed publication/rendition, no active primary job, and a provider outcome proven safe for another write;
7. issue a fresh signed `velvet.delivery_approval.v1` receipt;
8. call the canonical Instagram MCP through `openpost-prod`, where the bearer remains server-side;
9. remove the temporary call payload;
10. verify the returned media id with live `get_media` and require the exact approved caption.

`instagram_mcp_remote.py` is installed on `openpost-prod` and exposes only `list-media`, `get-media`, and `publish-call`; its output is whitelisted and never prints bearer tokens or signed receipts.

`prepare_manifest.py` builds the failover manifest at scheduling/staging time from the existing approval request and preflight evidence.

`openpost_failover_state.py` is read-only against the OpenPost SQLite database. It returns only safe delivery state and computes `safe_to_failover`.

## Safety

- No Graph call from GrokBot and no browser publishing.
- No bearer token, Meta token, private key, signature, or signed receipt is returned to GrokBot.
- `--execute` does not bypass owner approval; a fresh signed receipt is issued for the exact pre-approved payload.
- A live duplicate always wins: no second write.
- `processing`, `ambiguous`, `reconcile_only`, `manual_resolution`, or any active primary job blocks failover.
- A timeout/network outcome after the write fence is reconciled before any second write.
- Success means a live verified Instagram `media_id` and permalink, not merely a queued/completed OpenPost job.

## Manifest

Required fields:

```json
{
  "schema": "velvet.instagram_failover.v1",
  "content_id": "EXACT-CONTENT-ID",
  "package_sha256": "64-hex-package-sha",
  "format": "post",
  "repo_root": "C:\\path\\to\\exact-run-checkout",
  "preflight_path": "C:\\path\\to\\preflight.md",
  "approval_request_path": "C:\\path\\to\\approval-request.json",
  "expected_media_sha256": "64-hex-media-sha",
  "publication_id": "OPENPOST-PUBLICATION-ID",
  "rendition_id": "OPENPOST-RENDITION-ID"
}
```

Create it during scheduling with `prepare_manifest.py`; do not fabricate one during an incident.

For an owner-approved production schedule that should recover automatically inside its delivery window, bind the schedule explicitly:

```text
python -X utf8 packages/vfigos/failover/prepare_manifest.py ... \
  --scheduled-at-utc 2026-09-20T10:30:00Z \
  --auto-failover \
  --failover-window-minutes 30
```

`auto_failover` is valid only for an already owner-approved exact package. It never changes media, caption, account, package hash or schedule; it only authorizes the watcher to invoke the already-fenced recovery path after OpenPost proves `safe_to_failover=true`.

## Automatic delivery-window recovery

`failover_watch.py` scans prepared manifests only. Before any automatic write it calls the Grok-facing client in dry-run mode. It proceeds only when the dry-run proves both `duplicate_found=false` and `primary_safe_to_failover=true`.

The watcher writes `execute_attempted=true` atomically **before** the one permitted execute attempt. A process crash or timeout therefore cannot cause a second automatic write after restart. Any unverified execute result becomes `manual_reconcile_required`; it is never automatically replayed.

On the Chris machine the watcher is supervised by the existing S4U `GrokBot Boot Supervisor`, so it starts at boot without login and is restarted if it exits. A singleton file lock prevents two watcher processes from running concurrently. The canonical supervisor copy is `windows/grok_boot_supervisor.py`.

## GrokBot command

Dry-run first:

```text
C:\Python314\python.exe -X utf8 C:\ProgramData\VelvetOS\instagram-failover\grok-instagram-failover.py --manifest <manifest>
```

Then `--execute` only when the primary OpenPost attempt is definitively failed and the trusted state gate authorizes failover. The runner itself enforces this condition.