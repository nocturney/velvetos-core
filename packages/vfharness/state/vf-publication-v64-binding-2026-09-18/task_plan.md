# VF publication v6.4 binding repair

Route: Bounded system/engineering bugfix in the existing publication preflight.

## Outcome
Current creative/publication validators resolve Contract 6 / Revision 6.4 / VF-PROJECT-6.4-AESTHETIC-TRUTH-SEPARATION and no longer consume the superseded v6.2 Product Truth visual reference set.

## Authority / SoT
- packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json
- packages/velvetos/chatgpt-project/LATEST.json
- packages/velvetos/chatgpt-project/ASSET-MANIFEST-v6.4.json
- packages/velvetos/chatgpt-project/PROJECT-AUTHORITY-v6.4.txt
- packages/vfom/PUBLICATION-PREP-EXECUTION.md

## Smallest credible change
1. Make the active preflight + evidence validator bind to v6.4.
2. Keep byte/hash verification fail-closed while tolerating Git CRLF checkout normalization for text authority files.
3. Add repository attributes so future Windows checkouts preserve canonical bytes.
4. Update regression fixtures/sensors to assert the current bundle pointer and v6.4 reference set.

## Acceptance criteria
- Targeted request-gate sensor proves active binding is v6.4.
- Publication evidence tests pass with v6.4 fixtures.
- A CRLF checkout of canonical text authority files does not create a false hash failure.
- v6.2 remains historical only and is not referenced by active publication validator/preflight code.
- python scripts/check-all.py passes.

## Out of scope
No publication, no Instagram action, no creative generation, no business-fact changes, no historical checkpoint rewrite.

## Base
origin/main f4fbbf8832575da0bf68f1a6c26a1e56f85ada6b
