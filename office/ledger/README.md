# Office ledger

**Canonical authority (option A):** Google Sheet **VF HQ · jobs** bound in `office/ledger/bindings.json`.

**Local cache (not a second SoT):** `office/ledger/live/jobs.csv` — gitignored; empty/header-only on clean checkout until pull.

Adapter CLI:

```bash
# After Drive MCP export (download_file_content fileId=<spreadsheetId> exportMimeType=text/csv):
python3 scripts/vf_office.py jobs pull --from-csv /path/to/export.csv
python3 scripts/vf_office.py jobs status
python3 scripts/vf_office.py jobs list
python3 scripts/vf_office.py jobs reconcile --against /path/to/export.csv
python3 scripts/vf_office.py jobs push          # emit pending CSV for Drive upload
```

When `GOOGLE_TOKEN` / Drive API credentials exist (same as vfmedia), `jobs pull` without `--from-csv` exports the Sheet directly.

Write path: mutate cache (`jobs add` / `jobs stage`) → dirty receipt → `jobs push` → Drive update → `jobs pull --force` to confirm.

Conflict: dirty local + differing Sheet without `--force` → refuse overwrite (receipt `status=conflict`).

Do not invent ₪. Do not put full customer names in git if you can use a short label.

See `office/control-plane.json` sourcesOfTruth.jobs for the Sheet-canonical declaration.

Bindings (seeded 2026-08-31): folder [VF HQ · משרד](https://drive.google.com/drive/folders/1dFvQBlwzoefZ7OZKHDbMAFjuJ_9kXw8e).
Playbook: `packages/vfbooks/SHEETS.md`.

## GitHub OIDC/WIF write-through

The canonical background writer is `.github/workflows/jobs-write-through.yml`. It mints a short-lived Google token with Drive + Sheets scopes, runs `jobs pull --force` before commissioning writes, runs `jobs push`, requires post-write read-back evidence, and persists `sync-receipt.json`. No long-lived Google JSON key is stored in the repository. Production commissioning is LIVE_PROVEN: the committed receipt proves `status=written`, `verifiedFrom=sheets_values_get`, `canonical_changed=true`, and `dirty=false`. Adapter CSV files remain gitignored caches; price changes remain human-authorized.
