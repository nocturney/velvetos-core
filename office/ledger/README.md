# Office ledger

Local CSV is the job book. Google Sheet is a view via Drive `create_file` (CSV → spreadsheet).

Do not invent ₪. Do not put full customer names in git if you can use a short label.

```
python3 scripts/vf_office.py jobs add --channel WhatsApp --what "…" --qty 1
python3 scripts/vf_office.py jobs list
python3 scripts/vf_office.py jobs csv
python3 scripts/vf_office.py jobs stage VF-YYYYMMDD-001 ממתין לסכום
```

Bindings (seeded 2026-08-31): `bindings.json` — folder [VF HQ · משרד](https://drive.google.com/drive/folders/1dFvQBlwzoefZ7OZKHDbMAFjuJ_9kXw8e).
Playbook: `packages/vfbooks/SHEETS.md`.
