# Instagram failover

Purpose: preserve a scheduled Instagram delivery window when OpenPost has failed
or cannot be repaired quickly, without creating a second unrestricted publishing
path.

## Boundary

`grok_instagram_failover.py` accepts only a prepared
`velvet.instagram_failover.v1` manifest. It:

1. re-runs the exact Instagram send preflight;
2. checks Instagram for an identical live caption before issuing a receipt;
3. defaults to dry-run unless `--execute` is supplied;
4. obtains a fresh signed delivery approval through the owner-invoker;
5. sends the approved `publish_image` call through `openpost-prod`, where the
   Instagram MCP bearer remains server-side;
6. removes the temporary call file;
7. verifies the returned media id with `get_media`.

A media-publish timeout/network failure is never blindly repeated. The MCP marks
that outcome `retry_safety=reconcile_only`; live Instagram state must be
reconciled before another write.

## Manifest

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
  "publication_id": "optional-openpost-publication-id",
  "rendition_id": "optional-openpost-rendition-id"
}
```

## GrokBot

The GrokBot automation manager may invoke only the installed failover runner:

```
python -X utf8 C:\ProgramData\VelvetOS\instagram-failover\grok-instagram-failover.py --manifest <manifest>
```

Use `--execute` only after the scheduled OpenPost attempt is failed/missed or
the delivery window is at risk, and only for the exact owner-approved package.
Do not call Instagram Graph directly, do not publish from browser automation,
and do not retry an ambiguous media-publish outcome without reconciliation.

The server helper lives at:

`/opt/velvetos/instagram-failover-mcp.py`

It requires root/openpost access to the existing bearer file and prints only
whitelisted non-secret fields.
