# Story publish overlay

Patches upstream `publish_story` so **image** Stories poll `status_code=FINISHED` before `media_publish`.

Wired from `http_server.py` via `apply_story_publish_patch`. Redeploy Cloud Run (`./packages/vfigos/remote/deploy.sh`) for the live Team MCP to pick this up.

Until redeployed, image Stories may return Graph 9007; video Stories already wait upstream.
