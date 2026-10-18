# Changelog fragments

Normal pull requests do not edit `CHANGELOG.md`. Each one adds a single file:

```text
changelog.d/<slug>.md
```

`<slug>` is the branch or PR name in lowercase words separated by hyphens, for example `changelog.d/changelog-fragments.md`. The file is UTF-8 with LF newlines. Blank lines are allowed. Every other line is one Keep a Changelog bullet:

```markdown
- 2026-10-18 - **Short title:** what changed, in one paragraph.
```

A change under `packages/`, `office/`, `scripts/`, `.github/workflows/` or `constitution/` must include that fragment or a direct `CHANGELOG.md` edit. `scripts/check-changelog-fragments.py` accepts the fragment and rejects a capability diff that has neither. A docs-only diff outside those roots is not gated.

Only an added or modified fragment with a valid non-empty bullet counts. Deleting a fragment (status `D`) or emptying it does not. Deleting a fragment that already exists is refused unless the pull request is the compile step: the diff is only `CHANGELOG.md` plus those deletions, and each deleted bullet is already in `CHANGELOG.md`.

## Compile

Fold the fragments into `## [Unreleased]` when a person wants one changelog file:

```bash
python3 scripts/changelog-compile.py
```

The command is manual. Do not put it on a schedule and do not add a workflow that runs it. It appends missing bullets, leaves released sections byte for byte, consumes the fragment files it folded, and does nothing on a second run.

## `merge=union` fallback

`.gitattributes` sets `CHANGELOG.md merge=union`. That is Git's built-in union merge driver, not a custom script.

Use it only as a fallback for a pull request that still edits `CHANGELOG.md` directly. Union keeps added lines from both parents, so two new Unreleased bullets no longer conflict.

The tradeoff: union does not understand the changelog. A line deleted or rewritten on one side stays if the other side still has the old line. Near-duplicate bullets can both remain. Order follows the line merge, not "newest first". A fragment does not touch `CHANGELOG.md`, so the fallback is not needed for new work.
