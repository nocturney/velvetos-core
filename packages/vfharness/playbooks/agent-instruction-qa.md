# Agent instruction QA — write for agents, not about agents

Pattern source: [mattpocock/skills `writing-for-agents`](https://github.com/mattpocock/skills).

Use when creating or materially editing `AGENTS.md`, `SKILL.md`, agent/rule prompts, routing playbooks, automation prompts, or other instructions that will be consumed primarily by an agent.

## Core rule

Every durable instruction should earn its context cost by changing at least one of:

- **trigger / route** — when this instruction applies;
- **authority** — which source wins;
- **action** — what the agent must do;
- **constraint** — what it must not do;
- **evidence** — what proves the task is complete;
- **escalation** — when control moves to another tool/person/path.

If a paragraph only explains a general concept the model already knows, remove it or move it to human documentation.

## Placement

Put a rule at the narrowest durable authority that still covers every consumer:

| Rule kind | Canonical home |
|---|---|
| Cross-office law / authority | `AGENTS.md` / `constitution/` |
| Pack/domain behavior | that pack’s `SKILL.md` / playbook |
| Cursor trigger/router | thin `.cursor/skills/<name>/SKILL.md` |
| Background/reference detail | one-level reference/playbook |
| Runtime/provider truth | state/receipt/capability source, not prose memory |

**Point to the source; do not paste the same policy into five prompts.** A router should route, not become another handbook.

## Authoring checks

### 1. Trigger test

The skill/rule description must make it clear **when it should activate and when it should not**. Avoid descriptions such as “helps with workflows” that could match everything.

### 2. Necessity test

For each paragraph ask: “Would removing this materially change an agent’s behavior?” If not, cut it.

### 3. Authority test

Separate:

- **authority** — binding rule / source of truth;
- **context** — useful background;
- **example** — illustration only;
- **evidence** — observed proof.

Never let an example or historical note silently become policy.

### 4. Single-source test

Do not restate long route tables, business laws, credentials policy, or product truth in multiple skills. Link to the canonical file and keep only the local delta.

If two instructions disagree, resolve the conflict at the sources; do not add a third paragraph explaining both.

### 5. Actionability test

Prefer concrete imperatives:

- “Run `python3 scripts/check-all.py` after catalog/rule edits.”
- “If provider receipt is absent, state `UNPROVEN`.”

Avoid vague prose such as “be careful”, “ensure quality”, or “use best practices” unless the file names the actual gate/checklist.

### 6. Context-budget test

`SKILL.md` is a control plane, not a knowledge dump. Keep it compact; when it approaches roughly **500 lines**, move detailed variants/reference material into directly linked one-level playbooks/references.

Do not create deep chains where `SKILL.md` links to A → B → C before the agent can act.

### 7. Verification test

An instruction that claims a workflow is complete must name a deterministic check, provider receipt, human gate, or explicit `UNPROVEN/BLOCKED` state. Fluent prose is not evidence.

## Deterministic health pass

Run:

```bash
python3 scripts/check-skill-health.py
```

The sensor covers package skills **and active `.cursor/skills` routers**. It checks structural issues such as empty/thin skills, weak trigger metadata, context-heavy skills, missing verification language, broken symlinks, and possible duplicate names.

Warnings are review prompts, not invented quality scores. Fix evidence-backed problems; do not rewrite a working skill just to reduce a warning count.

## Review output

For a material instruction edit, report findings in this order:

1. contradiction / authority risk;
2. trigger too broad or too narrow;
3. duplicated policy / competing SoT;
4. missing action/evidence/escalation;
5. context bloat / navigability;
6. optional wording cleanup.

## Do not

- copy an upstream skill wholesale when an existing VelvetOS pack already owns the behavior;
- add a new runtime or orchestrator to solve prompt quality;
- duplicate secrets, tokens, provider state, or customer data into instructions;
- turn transient chat context into durable policy without an authority decision;
- optimize for “more instructions” instead of fewer, sharper instructions.

## Related

- `skill-first.md`
- `skill-authoring.md`
- `agent-architecture-audit.md`
- `context-thrift.md`
- `engineering-delivery-chain.md`
