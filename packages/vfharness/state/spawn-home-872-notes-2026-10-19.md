# Spawn home #872 notes

Goal: close comment 6255812062. Ambient TMPDIR does not hold the home, a gitconfig does not survive into the next spawn, the fsmonitor command creates a marker on this OS, and the process removes the directories it created.

Non-goals: the Windows D: root in #887, and the #889 fold notes already on #891.

Authority: `scripts/vf_spawn.py` on main after #883 (`067a1b9d`). `security_admission` stays RED.

Acceptance:

- `prove_controlled_home()` returns no errors.
- A mkdtemp home, a reused dirty home, a no-op hook, an ambient HOME, a no-op release, and a missing atexit registration are each caught.
- Linux `check-all` is 126/126. Hosted Windows `check-all-windows` is green before QA please.

Evidence: `python3 -c "import vf_spawn; ..."` from `scripts/`, then `python3 scripts/check-all.py`.
