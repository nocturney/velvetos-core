# Verified RustDesk hostnames for the private Mac viewer

Date: 2026-10-14
Scope: MacMiniOffice2 private registered-machines report
Status: **6/6 IDs matched with evidence; not a live online/offline monitor**

## Result

Six names can be attached to RustDesk's original registered IDs without
using row ordering or guessing:

| Friendly display name | Local matching evidence |
|---|---|
| Chris | Native RustDesk `--get-id` hash matches registered ID |
| Chris-Mini-PC | Hostname+ID cached in main PC's RustDesk peers, hash matches registered ID; Windows hostname verified |
| Chris-3DPC | Hostname+ID cached in main PC's RustDesk peers, hash matches registered ID; Windows hostname verified |
| MacMiniOffice2 | Native RustDesk `--get-id` hash matches registered ID |
| MacMiniOffice | Native RustDesk `--get-id` hash matches registered ID |
| Mac-Bedroom | Native RustDesk `--get-id` hash matches registered ID |

Cross-check used the already existing private HTML inventory on
MacMiniOffice2, not a production database export. All six hashed IDs were
unique and matched exactly one of the six registered entries. Two Windows
RustDesk `--get-id` calls from the remote service account produced no ID;
their associations were established instead from the main PC's RustDesk
cached peer metadata and corroborated Windows hostnames.

## Implementation

`tools/rustdesk-pilot/local_aliases.py` accepts a separate
`velvetos.rustdesk.local_aliases.v1` JSON file. Entries contain
`id_sha256`, `display_name` and a constrained evidence source only.
The **owner-private Mac file**, never uploaded to the repository, is:

`~/Library/Application Support/VelvetOS/RustDeskPilot/2026-10-14/private/friendly-names-verified-20261014.json`

The generator must explicitly opt into `--aliases-file`. The display name
and original ID occupy separate UI fields. The existing
`rustdesk://connection/new/<encoded-original-ID>` URL is unchanged:
aliases have no influence on the target of a connection. An unmatched ID
shows an explicit unknown-name label rather than guessing.

The alias file is owner-only (`0600`) and outside Git. The HTML output
is likewise private; do not share either artifact or log raw RustDesk IDs.

## Scope boundaries

- Registered IDs and OS hostnames are not proof of live availability;
  every row still has `presence=UNKNOWN`, `last_seen_at=null`.
- No client was reconfigured, service restarted, CortenDesk container
  launched, privileged setting bypassed, or PR merged.
- The user previously confirmed that the manual native-RustDesk link
  successfully opened the intended machine. This new feature changes
  only human-visible names, not connection behavior.
- Full CortenDesk browser management remains a separate permitted staging
  acceptance task.

## Acceptance

Tests must show exactly six verified names, zero unmatched IDs, six manual
links referencing their original IDs, no auto-launch, no network access from
the HTML, owner-private file permissions, and no raw ID or mapping committed.
The existing original private HTML files are intentionally not overwritten.
