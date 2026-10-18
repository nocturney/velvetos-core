# CrewAI pilot dependency findings (2026-10-18)

Status of the reviewed runner in `scripts/office_v2_crewai/`: preflight refuses.
No package was installed from this change. No model call was made. E3 stays
`BLOCKED_SECURITY` until a recorded security decision exists for this lock.
E6 stays `NOT_VERIFIED` because the public repo has 12 open issues, and the
runbook minimum is 20.

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
remove it: `import crewai` loads `crewai.crew`, which imports
`crewai.knowledge.knowledge`, which imports `KnowledgeStorage`, which imports
`crewai.rag.chromadb.config`, which executes `from chromadb.config import Settings`
at module level. Omitting the chromadb wheel breaks `import crewai`. chromadb
1.5.9 carries PYSEC-2026-311, PYSEC-2026-3813, PYSEC-2026-3814 and
PYSEC-2026-3815, and no fix is recorded.

## Lock identity

The Chris lock file is `requirements-locked.txt`, sha256
`121c1bd04eee730b51eb71e49da503b0d0236cdd06d8687a5df792234f78a669`, with 154
hash-pinned wheels. The recorded scan is RED. The committed evidence file is
`scripts/office_v2_crewai/evidence/e3-supply-chain.json` and it sets
`security_decision_present` to false. No `e3-security-decision.json` is
committed. Preflight treats E3 as failing until a decision file names
`ACCEPTED_RISK`, the same lock sha256, and all five advisory ids.

## Open-issue fixture

`gh issue list` for open issues on `nocturney/velvetos-core` returned 12
issues, including 612 and 595. The frozen export is those 12 issues, an answer
sheet of 20 facts, and one adversarial fixture. It does not pad with closed
issues or pull requests, and it contains no title, SHA, or URL from
`velvetos-velvet-factory`. The manifest stores sha256 of those three files.
