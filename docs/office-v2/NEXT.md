# Office 2.0 desk — next step

The working desk is plain Python: `scripts/office_v2_mvp.py`. It only GETs GitHub and writes `docs/office-v2/board/latest.md` plus `latest.json`.

CrewAI and LangGraph are **not** in `requirements-sensors.txt` or the hashed lockfiles (`requirements-sensors.py311.lock`, `requirements-sensors.py312.lock`). They are not imported. A protected admission has to add them to the lockfile before this desk may call either framework.

The verified research for that decision is the auditor's read-only check of the 2026-10-18 Perplexity scan:

https://github.com/nocturney/velvetos-core/issues/595#issuecomment-6249011608

That comment (id `6249011608`) records CrewAI as MIT and Windows-native, with critical CVEs that must be pinned, and LangGraph as the pure-Python no-Docker fallback whose listed CVEs have fixed versions. Microsoft UFO is Windows-native and is not a fit for this read-only board. No install, no listener, and no scheduler belongs to this desk. Recurring runs stay with ChatGPT automations; the GitHub workflow is manual dispatch only.
