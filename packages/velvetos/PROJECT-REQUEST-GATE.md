# VelvetOS — Project Request Gate

Status: **MANDATORY · FAIL-CLOSED · ALL REQUESTS**

This is the single front door for any Velvet Factory / VelvetOS request. It does not replace the Constitution, packs, skills or tools; it forces the request to be routed through them before work begins.

## Core law

**No substantive work starts before `project_preflight: PASS`.**

The preflight is not permission to dump the whole warehouse into context. It is a dispatcher:

1. load the small baseline authority set;
2. classify the request;
3. resolve the relevant packs / skills / sources from the authority manifest;
4. verify hard constraints and current evidence;
5. only then execute;
6. run exact-final / action postflight before claiming completion.

If a mandatory authority is unavailable, stale, contradictory or cannot be verified, the branch is `BLOCKED` / `needs_sync`; never silently fall back to model defaults.
## Preflight sequence

### 1. Baseline authority

Always resolve the authority manifest: `packages/velvetos/PROJECT-AUTHORITY-MANIFEST.json`.

Baseline law is always higher priority than task-local preference:
- `constitution/CONSTITUTION.md`
- `constitution/STUDIO.md`
- `constitution/RISK.md`
- `constitution/PUBLIC_CTA.md`
- `constitution/VISIBLE_TEXT.md`
- `constitution/ORCHESTRA.md`
- instance / frontend policy when operating a specific tenant

### 2. Classify the request

Choose one or more domains from the manifest. Do not guess a new pack or invent a parallel workflow. If classification is uncertain, use the office graph / router (`vfmem`) and Living Studio registry before choosing handlers.

### 3. Load only relevant authorities

For every selected domain, load the named pack instructions, relevant skills and canonical Sources of Truth before drafting or acting. A tool being available does not make it authoritative; the manifest and Constitution decide whether it may be used.
### 4. Build an internal preflight receipt

Before execution, resolve these fields internally:
- `request_domain`
- `authority_manifest_version`
- `baseline_authority: PASS|FAIL`
- `routed_packs`
- `required_skills`
- `required_sources`
- `required_tools`
- `hard_gates`
- `current_evidence_state`
- `project_preflight: PASS|BLOCKED`

Do not expose this receipt to the owner unless useful or requested. But do not proceed when it is incomplete.

### 5. Execute through the real pipeline

Execution must use the routed skills/tools rather than reproducing their intended behavior from memory. When a matching specialist, lint, editor, source or provider exists, actually use it when the task requires it.

### 6. Postflight

Before claiming `done`, `ready`, `prepared`, `published`, `synced`, `sent`, or equivalent, run the domain's output/action gates on the exact final artifact or provider result. Evidence beats intention.
## Mandatory creative/publication path

Any request involving product media, social content, copy, image/video editing, post/carousel/Story/Reel/cover/grid or `prepare for publication` must route through the complete creative stack named in the authority manifest.

This path is especially fail-closed because observed failures came from skipping layers:
- visual language / owner-approved reference;
- Product Truth / source-subject lock;
- publication-prep execution contract;
- meaningful creative transformation (no raw-photo fallback);
- Brand Asset + Public CTA lock;
- copy/voice + Visible Text gate;
- exact-final visual QA / publish preflight.

A beautiful artifact that violates Product Truth, branding, CTA or facts fails. A truthful raw photo carousel that skipped meaningful treatment also fails when the request was publication prep.

## Conflict order

When authorities disagree, resolve in this order:

`system / safety / rights` → `Constitution + Product Truth + verified facts` → `tenant/instance policy` → `domain authority / pack` → `owner-approved visual/copy standards` → `local creative preference`.

Never use memory of an old chat to override a newer canonical authority.
## ChatGPT Project binding

For the Velvet Factory ChatGPT Project, resolve `packages/velvetos/chatgpt-project/PROJECT-CONTRACT-v6.json` before substantive work. The always-on Project Instructions must be the v6 bootstrap and Project Sources must contain `Velvet-Factory-Project-Authority-v6.txt`. Visual branches must also resolve `Velvet-Factory-APPROVED-Visual-Reference-v2.jpg` and match Canva asset `MAHVL7PKpvE` / SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897`.

A missing/mismatched version, stale source set, unresolved visual reference, or ambiguous authority version is `needs_sync` / BLOCKED. Do not merge old and new project-source rules. v6 is the current contract.

Project memory is helpful context, not governance. Do not rely on a previous chat to remember the pipeline. The always-on Project Instructions are the bootstrap; v6 authority + this gate + manifest are the router; domain files/skills are the authority.

## What this gate is not

- not a second runtime;
- not a new office or pack;
- not permission to load all 273 specialists every turn;
- not a replacement for provider receipts, file evidence or current operational Sources of Truth;
- not a promise that a tool exists when the current environment does not expose it.

The desired behavior is simple: **route first, verify authority, execute, verify the exact result.**