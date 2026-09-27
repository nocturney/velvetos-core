# scripts/archive

One-shot migrations kept for history only. Nothing in the repo invokes them, and
their entry points refuse to run.

| Script | Origin | Why archived |
|---|---|---|
| `vf_close_runtime_corners.py` | #9913d57a / #6ce09920, 2026-09-14 runtime closeout | Unreferenced one-shot migration that edits REGISTRY.json, BEST-SKILLS.json and OWNER-ACTIONS-he.md. Re-running it would overwrite current authorities, and after the move its paths resolve from `scripts/`. |

Not archived: `scripts/vf_project669_transport.py`. It is the only producer of the
`velvet.project669.transport_qa.v1` receipts that `scripts/vf_project669_publication.py`
requires when a transport derivative is bound, so it is a live tool.
