# Office 2.0: local source-import commit handoff (#612)

- Admit a previously imported, hash-verified Claude source patch to one isolated Role A **local topic commit** after exact source/branch/index/postimage verification. Run without Git hooks or inherited Git configuration; refuse changed scope or tampered evidence.
- Persist a one-use journal before any Git/index mutation. After a crash, allow read-only reconciliation only when the exact single-parent commit and Git tree are present; never auto-retry a commit with uncertain effects.
- Preserve the exact receipt-bound file bytes when Git stages a local commit, independently of `core.autocrlf` on the target machine; isolate temporary Git test fixtures from host-wide CRLF defaults without changing user Git settings.
- Keep source-stage, Git commit and quality/authority separate: the resulting receipt explicitly denies independent QA, protected CI, PR, merge, distributed lease/fencing and production admission. No remote push or model execution is performed by this command.
