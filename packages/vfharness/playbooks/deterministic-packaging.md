# Deterministic packaging — stage, archive, test, prove

Use the installed 7-Zip CLI for repeatable handoff, release or deployment bundles when an archive is the requested artifact. This is packaging, not source control or release authority.

## Workflow

1. Stage only intended files into a clean temporary/staging directory.
2. Produce a manifest containing expected relative paths and, when useful, SHA-256 hashes.
3. Create the archive with explicit format/options and stable relative paths.
4. Run `7z t <archive>` to test archive integrity.
5. Extract the finished archive into a fresh temporary directory and compare expected paths/hashes when the handoff is important.
6. Record archive hash, size and creation inputs in the existing handoff/release evidence.
7. Delete staging/extraction temp only after verification; keep the source untouched.

## Rules

- Prefer ordinary .7z or .zip according to the receiving workflow.
- Do not use `-sdel` or another source-deleting option in normal packaging.
- Do not include caches, secrets, credentials, logs or machine-specific temp data unless explicitly required and reviewed.
- Do not build self-extracting executables unless the user/workflow explicitly requires an executable package.
- Do not call an archive complete merely because creation returned exit 0; integrity test plus expected-content check is the proof.
- Preserve timestamps/metadata only when the receiving workflow needs them; deterministic content and provenance matter more than accidental workstation state.
