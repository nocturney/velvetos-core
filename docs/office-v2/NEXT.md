# Office 2.0 desk — next step

The working desk is plain Python: `scripts/office_v2_mvp.py`. It only GETs GitHub. A local `--write` lands in gitignored `docs/office-v2/board/latest.md` and `latest.json`. Those files are not committed. The committed sample is `docs/office-v2/board/SAMPLE.md` (and `SAMPLE.json`), built from the offline fixture with private rows removed.

`nocturney/velvetos-core` is public. `nocturney/velvetos-velvet-factory` is private. The generator will not write private-repo rows, URLs, or titles into a tracked path or any path outside this repo. `.github/workflows/office-v2-board.yml` is manual dispatch only, passes `--omit-private`, and uploads the board as an artifact. It does not commit the board. On GitHub Actions, `github.token` cannot read the private factory repo, so that artifact shows the factory repo as denied and invents no rows.

CrewAI and LangGraph are **not** in `requirements-sensors.txt` or the hashed lockfiles (`requirements-sensors.py311.lock`, `requirements-sensors.py312.lock`). They are not imported. A protected admission has to add them to the lockfile before this desk may call either framework.

The verified research for that decision is the auditor's read-only check of the 2026-10-18 Perplexity scan:

https://github.com/nocturney/velvetos-core/issues/595#issuecomment-6249011608

That comment (id `6249011608`) records CrewAI as MIT and Windows-native, with critical CVEs that must be pinned, and LangGraph as the pure-Python no-Docker fallback whose listed CVEs have fixed versions. Microsoft UFO is Windows-native and is not a fit for this read-only board. No install, no listener, and no scheduler belongs to this desk. Recurring runs stay with ChatGPT automations; the GitHub workflow is manual dispatch only.
