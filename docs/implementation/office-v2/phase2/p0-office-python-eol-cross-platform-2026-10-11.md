# Office 2.0 — Git-index LF vs Windows checkout CRLF source-byte regression

**2026-10-11.** Source-byte portability only; no system, model, credential or business effect.

## Real Windows baseline

On Chris Windows, existing core.autocrlf=true was left unchanged. A clean clone of the repo contained **389 Python files under scripts/**. Native git ls-files --eol reported **389/389 index LF**, zero index CRLF/mixed, but **383/389 working-tree CRLF**. Therefore the existing raw SHA-256 Office contract does not match actual worktree bytes.

The 51 tracked Phase2 JSON receipt files likewise all have Git-index LF but all 51 became CRLF on Windows; two Dagu receipt SHA pins subsequently failed after correcting Python LF. The canonical pre-change main itself failed Office contracts at the historical fresh-attempt lineage source byte pin. A narrow eol=lf override restored its expected SHA256 00882aa96d6e22e785b4c3c6ba30ff1048f655284256b455f760a366c437bddc, and then Office contracts exposed another identical CRLF mismatch in the SHA-pinned Aider display usage script. Neither is new model failure.

## Minimal proposed repository rule

Set three .gitattributes entries: /scripts/*.py text eol=lf; /scripts/**/*.py text eol=lf; /docs/implementation/office-v2/phase2/*.json text eol=lf. On Mac, native git check-attr confirms both top-level and nested scripts receive eol=lf. No source blobs need to be rewritten because all 389 Git index Python blobs are already LF. This does not apply to non-Python files or to quarantined model outputs under docs/, whose intentional LF/CRLF bytes remain protected by -text.

## Admission / nonclaims

Before merge: verify a new Windows checkout with native autocrlf=true shows all 389 files as i/lf w/lf; rerun Office contracts and the 118-sensor full suite; check clean Mac Office contracts and README; pass protected PR CI; guarded merge and postmerge main CI. Do not claim these outcomes before they are observed.

This is NOT a new scheduler, OS sandbox, signer key-custody proof, worker or GitHub writer authority, model execution, hidden-QA promotion or permission to retry an UNKNOWN effect. #604 and #612 P0 remain PARTIAL/RED.
