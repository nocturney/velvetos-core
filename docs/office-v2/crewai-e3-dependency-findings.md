# CrewAI pilot dependency findings (2026-10-18)

Status of the reviewed runner in `scripts/office_v2_crewai/`: the committed
tree still refuses before any model call. No package was installed from this
change. No model call was made. E6 stays `NOT_VERIFIED` because the public
repo has 12 open issues, and the runbook minimum is 20.

E3 is no longer an unconditional fail. Christian accepted the RED lock at
2026-10-18 16:02 Asia/Jerusalem (issue 612 comment 6250234075), on the basis
of comment 6250224612. The decision is
`scripts/office_v2_crewai/evidence/e3-security-decision.json` and it matches
lock sha256 `121c1bd04eee730b51eb71e49da503b0d0236cdd06d8687a5df792234f78a669`.
Preflight passes E3 only when that file is present and every condition below
is enforced. E1, E2, E4, E5, E6 and E7 are unchanged, so this tree does not
start a pilot.

## Approved local model

Owner approval at 2026-10-18 15:28 IDT, recorded in issue 612 comment
6250120048. The approved endpoint is `http://127.0.0.1:11435` with model
`qwen3.5:9b`, digest
`56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90`.
Port 11434 is not the pilot listener. The provider sends `think: false`.
It refuses any non-loopback host, any digest other than the approved digest,
and any process that does not have `OLLAMA_NO_CLOUD` set to `1` or `true`.
Remote and paid APIs stay refused.

## Pins that block the CVE fixes

CrewAI 1.15.28 (`lib/crewai/pyproject.toml` at tag 1.15.28) declares:

- `chromadb~=1.5.9` in the required `dependencies` list (PEP 440: `>=1.5.9`, `==1.5.*`)
- `mcp~=1.28.1` in the same required list (`>=1.28.1`, `==1.28.*`)
- optional extra `tools = ["crewai-tools==1.15.28"]`

`mcp~=1.28.1` does not allow `mcp` 1.30.0. The installed lock pin is
`mcp==1.28.1`, which carries CVE-2026-59951. The fix version 1.30.0 is outside
the pin. A future CrewAI release would have to widen the pin. This runner does
not override it and does not install with `--no-deps`.

`chromadb~=1.5.9` is not an extra. The tools extra is `crewai-tools`, and
excluding that extra does not remove chromadb. `memory=False` also does not
remove it. Comment 6250224612 verified the eager chain: `crewai/__init__.py`
imports `memory/unified_memory.py`, which imports
`rag/embeddings/providers/openai/openai_provider.py`, which imports chromadb.
Omitting the chromadb wheel breaks `import crewai`. chromadb 1.5.9 carries
PYSEC-2026-311, PYSEC-2026-3813, PYSEC-2026-3814 and PYSEC-2026-3815, and no
fix is recorded. Those four advisories are server-side. The post-run check
therefore fails closed on `chromadb.server`, `fastapi`, `uvicorn` and `mcp`
in `sys.modules`. It does not treat the `chromadb` package itself as a
violation, because `import crewai` loads that package. The runner also
refuses the `chroma` CLI and any pilot listening port.

## Lock identity

The Chris lock file is `requirements-locked.txt`, sha256
`121c1bd04eee730b51eb71e49da503b0d0236cdd06d8687a5df792234f78a669`, with 154
hash-pinned wheels. The recorded scan is still RED. The owner decision accepts
that residual risk only with the conditions above. The committed files are
`scripts/office_v2_crewai/evidence/e3-supply-chain.json` and
`e3-security-decision.json`. A different lock sha, a missing condition, or a
guard that accepts a violation keeps E3 at `BLOCKED_SECURITY`.

## Open-issue fixture

`gh issue list` for open issues on `nocturney/velvetos-core` returned 12
issues, including 612 and 595. The frozen export is those 12 issues, an answer
sheet of 20 facts, and one adversarial fixture. It does not pad with closed
issues or pull requests, and it contains no title, SHA, or URL from
`velvetos-velvet-factory`. The manifest stores sha256 of those three files.
