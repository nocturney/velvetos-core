# Office 2.0 #612 — portable exact-byte Git source/evidence (all tracked Python/JSON/Markdown)

**2026-10-11, isolated LAB.** Existing Windows system Git setting is core.autocrlf=true and remains unchanged. This follow-up to PR #689 fixes the next observed failure in the full *native Windows default* check-all suite, not a source-level algorithm or policy-authority change.

## Direct evidence from canonical main 091fef76

Native Chris Windows Git checkout, independently scanned with git ls-files --eol: 3456 total tracked paths; 554 Python (551 Git-index LF, one historical CRLF original, two empty), 874 JSON (868 Git-index LF, five CRLF originals, one mixed original) and 1280 Markdown (all Git-index LF). After the narrower PR #689, all 502 Office Phase2/Python paths retained LF, but the full check-all still failed the unrelated Stage 6B Creative FOUNDRY/schema *byte-hash* guard: packages/vfom/FOUNDRY.json and CREATIVE-MANIFEST.schema.json were Git-index LF yet checkout CRLF.

## Fix and immutable exceptions

Add repository-local Git .gitattributes rules *.py, *.json, *.md with text eol=lf. These operate on existing Git-index LF sources; they do not rewrite the blobs committed to Git or change the machine-wide Git config. Explicit -text !eol exceptions protect **all six original non-LF JSON blobs** (five i/crlf, one i/mixed), and the pre-existing quarantined generated-code source archive remains -text !eol (five Python fixtures, one i/crlf and four i/lf). No original CRLF/mixed-index evidence may silently normalize.

The read-only verifier scripts/vf_office_v2_p0_repo_text_byte_gate.py uses native git ls-files --eol -z to check original Git-index vs working-tree end-of-line classification without reading a secret, running generated code, changing Git index/refs, or making network/model calls. Selftest has 13 bounded positive/negative cases: LF-to-CRLF drift, unregistered non-LF blobs, historical normalized evidence, historical attr policy drift and empty files. Verified on Mac local *before* PR: PASS 13/13 plus 2708 tracked Python/JSON/Markdown, 2695 LF exact, two empty and 11 historical raw preserved. Source SHA-256 pin: 0c8a98519803158f0944abc6ace592526e75f457bacc37ce4846d2712167cf86. The existing Office contracts gate requires both selftest and read-only Git index verification and will FAIL_CLOSED if scope or source drifts.

## Acceptance and boundaries

1. Native Chris Windows fresh clone, with the existing system core.autocrlf=true, must pass verifier 13 static cases + full indexed/worktree comparison and full check-all suite. Test declared exceptions with native git readback as well as normal files. No changed global config.
2. Mac independent clean current PR head Office contracts/README and read-only integrity checker PASS.
3. Protected PR full CI + expected-head squash merge + independent post-merge main CI PASS before any claim of closure.

**Nonclaims:** Git index/worktree byte equality for three trusted text families is not general binary/codec normalization, OS-level generated-code isolation, token custody, independent Git Sink identity, provable model output quality, or distributed provider epoch safety. #604 and #612 P0 remain RED/PARTIAL. Existing active business writers, local unisolated Aider and production auth are not modified.
